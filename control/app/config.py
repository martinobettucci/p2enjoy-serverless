# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#configuration
# All declarations validate the cell configuration and protect persisted data.
from dataclasses import dataclass
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
        return cls(*values,trusted_proxies=trusted,host_state_dir=paths[0],runtime_image=image,artifact_budget=int(budget)*1024**2)


class Vault:
    def __init__(self,key):
        self.cipher=Fernet(key.encode())

    def seal(self,value):
        return self.cipher.encrypt(json.dumps(value,separators=(',',':')).encode()).decode()

    def open(self,value):
        return json.loads(self.cipher.decrypt(value.encode()))
