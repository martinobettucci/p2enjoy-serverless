# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#configuration
# All declarations validate the cell configuration and protect persisted data.
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation,ROUND_CEILING
import ipaddress
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.fernet import Fernet


@dataclass(frozen=True)
class Settings:
    public_url: str
    issuer: str
    client_id: str
    client_secret: str
    master_key: str
    state_dir: Path = Path('/state')
    trusted_proxies: tuple = ()
    host_state_dir: Path | None = None
    runtime_image: str = ''
    artifact_budget: int = 4096*1024**2
    storage_root_host: Path | None = None
    storage_socket_dir_host: Path | None = None
    function_cpu_nanos: int = 1000000000
    function_memory_mib: int = 8192
    function_instance_limit: int = 32
    waiting_call_limit: int = 128
    function_waiting_call_limit: int = 16

    @classmethod
    def load(cls):
        keys=('SERVERLESS_PUBLIC_URL','OIDC_ISSUER','OIDC_CLIENT_ID',
              'OIDC_CLIENT_SECRET','SERVERLESS_MASTER_KEY')
        missing=[key for key in keys if not os.environ.get(key)]
        if missing:
            raise RuntimeError('Missing cell configuration: '+', '.join(missing))
        values=[os.environ[key] for key in keys]
        for value in values[:2]:
            url=urlsplit(value)
            if url.scheme!='https' or not url.netloc or url.username or url.password or url.query or url.fragment:
                raise RuntimeError('Public URL and issuer must be absolute HTTPS URLs')
        if urlsplit(values[0]).path not in ('','/'):
            raise RuntimeError('Public URL must use the root path')
        values[0]=values[0].rstrip('/');values[1]=values[1].rstrip('/')
        if values[1]!='https://oauth.lelabs.tech/realms/lelabs':
            raise RuntimeError('OIDC_ISSUER doit désigner le realm lelabs autorisé.')
        Fernet(values[4].encode())
        try:
            trusted=tuple(ipaddress.ip_network(value.strip(),strict=False)
                          for value in os.environ.get('SERVERLESS_TRUSTED_PROXIES','').split(',') if value.strip())
        except ValueError:raise RuntimeError('SERVERLESS_TRUSTED_PROXIES doit contenir des CIDR valides.') from None
        # @spec docs/BACKLOG.md#sls-030 | docs/CONTROL.md#configuration
        paths=[]
        for key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST'):
            raw=os.environ.get(key,'');path=Path(raw)
            if not raw or not path.is_absolute() or '..' in path.parts or path==Path('/') or '\0' in raw:
                raise RuntimeError(key+' doit être un chemin absolu de cellule.')
            paths.append(path)
        image=os.environ.get('SERVERLESS_RUNTIME_IMAGE','')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}',image):raise RuntimeError('SERVERLESS_RUNTIME_IMAGE exige une empreinte Docker immuable.')
        budget=os.environ.get('SERVERLESS_ARTIFACT_BUDGET_MIB','4096')
        if not re.fullmatch(r'[0-9]{3,5}',budget) or not 512<=int(budget)<=65536:
            raise RuntimeError('SERVERLESS_ARTIFACT_BUDGET_MIB doit être compris entre 512 et 65536.')
        storage_paths=[]
        for key in ('SERVERLESS_STORAGE_ROOT_HOST','SERVERLESS_STORAGE_SOCKET_DIR_HOST'):
            raw=os.environ.get(key,'');path=Path(raw)
            if not raw or not path.is_absolute() or '..' in path.parts or path==Path('/') or '\0' in raw:
                raise RuntimeError(key+' doit être un chemin absolu de cellule.')
            storage_paths.append(path)
        if (storage_paths[1].is_relative_to('/run') or storage_paths[1].is_relative_to(storage_paths[0])
                or storage_paths[0].is_relative_to(storage_paths[1])):
            raise RuntimeError('Le canal de stockage doit être distinct des données et hors de /run.')
        # @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
        try:
            cpu=Decimal(os.environ.get('SERVERLESS_FUNCTION_CPU_BUDGET','1'))
            if not cpu.is_finite() or not Decimal('.05')<=cpu<=64:raise ValueError
            limits=[]
            for key,default,low,high in (
                ('SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB',8192,128,1048576),
                ('SERVERLESS_FUNCTION_INSTANCE_LIMIT',32,1,256),
                ('SERVERLESS_WAITING_CALL_LIMIT',128,1,4096),
                ('SERVERLESS_FUNCTION_WAITING_CALL_LIMIT',16,1,256)):
                raw=os.environ.get(key,str(default))
                if not re.fullmatch('[0-9]{1,7}',raw) or not low<=int(raw)<=high:raise ValueError
                limits.append(int(raw))
            if limits[3]>limits[2]:raise ValueError
        except (ValueError,InvalidOperation):raise RuntimeError('Budgets d’exécution de cellule invalides.') from None
        return cls(*values,trusted_proxies=trusted,host_state_dir=paths[0],runtime_image=image,artifact_budget=int(budget)*1024**2,
                   storage_root_host=storage_paths[0],storage_socket_dir_host=storage_paths[1],
                   function_cpu_nanos=int((cpu*1000000000).to_integral_value(rounding=ROUND_CEILING)),
                   function_memory_mib=limits[0],function_instance_limit=limits[1],waiting_call_limit=limits[2],function_waiting_call_limit=limits[3])


class Vault:
    def __init__(self,key):
        self.cipher=Fernet(key.encode())

    def seal(self,value):
        return self.cipher.encrypt(json.dumps(value,separators=(',',':')).encode()).decode()

    def open(self,value):
        return json.loads(self.cipher.decrypt(value.encode()))
