# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#configuration
# All declarations validate the cell configuration and protect persisted data.
from dataclasses import dataclass
import ipaddress
import json
import os
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
        return cls(*values,trusted_proxies=trusted)


class Vault:
    def __init__(self,key):
        self.cipher=Fernet(key.encode())

    def seal(self,value):
        return self.cipher.encrypt(json.dumps(value,separators=(',',':')).encode()).decode()

    def open(self,value):
        return json.loads(self.cipher.decrypt(value.encode()))
