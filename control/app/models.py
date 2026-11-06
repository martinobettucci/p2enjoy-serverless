# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#gestion | docs/PLATFORM.md
# Explicit management DTOs; unknown fields and invalid resource contracts fail.
import ipaddress
import re
import time
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)


class Named(Strict):
    name:str=Field(min_length=1,max_length=63,pattern=r'^[a-z0-9][a-z0-9_-]*$')
    description:str=Field(default='',max_length=2000)


class NetworkPolicy(Strict):
    origins:list[str]=Field(default_factory=list,max_length=64)
    ips:list[str]=Field(default_factory=list,max_length=64)
    combination:Literal['and','or']='and'

    @field_validator('origins')
    @classmethod
    def exact_origins(cls,values):
        result=[]
        for value in values:
            url=urlsplit(value)
            if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.path or url.query or url.fragment or '*' in value:
                raise ValueError('Une origine contient uniquement protocole, hôte et port.')
            # Reading port validates its syntax and range, including IPv6.
            port=url.port
            host=url.hostname.lower()
            if ':' in host:host='['+host+']'
            default=443 if url.scheme=='https' else 80
            result.append(f'{url.scheme}://{host}'+(f':{port}' if port and port!=default else ''))
        return sorted(set(result))

    @field_validator('ips')
    @classmethod
    def networks(cls,values):
        try:return sorted({str(ipaddress.ip_network(value,strict=False)) for value in values})
        except ValueError:raise ValueError('Adresse IP ou réseau CIDR invalide.') from None


class ServiceCreate(Named):
    policy:NetworkPolicy=Field(default_factory=NetworkPolicy)


class Configuration(Strict):
    environment:dict[str,str]=Field(default_factory=dict,max_length=128)
    secrets:dict[str,str|None]=Field(default_factory=dict,max_length=128)

    @model_validator(mode='after')
    def names_and_sizes(self):
        for mapping in (self.environment,self.secrets):
            for key,value in mapping.items():
                if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}',key):raise ValueError('Nom de variable invalide.')
                if value is not None and ('\x00' in value or len(value.encode())>16384):raise ValueError('Valeur de variable trop longue ou contenant NUL.')
        if set(self.environment)&{k for k,v in self.secrets.items() if v is not None}:
            raise ValueError('Une variable ne peut pas être aussi un secret.')
        return self


class StorageVolume(Strict):
    enabled:bool=False
    quota_mib:int=Field(default=64,ge=1,le=65536)


class Storage(Strict):
    data:StorageVolume=Field(default_factory=StorageVolume)
    cache:StorageVolume=Field(default_factory=StorageVolume)
    concurrency:Literal['exclusive','shared']='exclusive'


class FunctionConfig(Strict):
    handler:str=Field(default='handler.handler',min_length=3,max_length=256)
    runtime:Literal['node24']='node24'
    memory_mib:int=Field(default=256,ge=128,le=8192)
    cpu:float=Field(default=.25,ge=.05,le=1)
    timeout_seconds:float=Field(default=30,ge=.1,le=86400)
    idle_seconds:float=Field(default=60,ge=0,le=86400)
    min_instances:int=Field(default=0,ge=0,le=32)
    max_instances:int=Field(default=1,ge=1,le=32)
    concurrency:int=Field(default=1,ge=1,le=32)
    queue_timeout_seconds:float=Field(default=10,ge=0,le=300)
    storage:Storage=Field(default_factory=Storage)

    @field_validator('handler')
    @classmethod
    def handler_path(cls,value):
        if not re.fullmatch(r'[A-Za-z0-9_./-]+\.[A-Za-z_$][A-Za-z0-9_$]*',value):raise ValueError('Handler attendu : chemin/module.export.')
        module=value.rsplit('.',1)[0]
        if module.startswith('/') or any(p in ('','..','.') for p in module.split('/')):raise ValueError('Le handler doit rester dans l’archive.')
        return value

    @model_validator(mode='after')
    def bounds(self):
        if self.min_instances>self.max_instances:raise ValueError('Le minimum ne peut pas dépasser le maximum d’instances.')
        if self.concurrency>self.max_instances:raise ValueError('Une instance accepte une invocation active.')
        if self.storage.data.enabled and self.storage.concurrency=='exclusive' and self.concurrency!=1:
            raise ValueError('Le mode données exclusives exige une concurrence de 1.')
        return self


class FunctionCreate(Strict):
    name:str=Field(min_length=1,max_length=63,pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]*$')
    config:FunctionConfig=Field(default_factory=FunctionConfig)
    configuration:Configuration=Field(default_factory=Configuration)


class TokenCreate(Strict):
    name:str=Field(min_length=1,max_length=100)
    rights:list[Literal['create','read','update','delete']]=Field(min_length=1,max_length=4)
    function_ids:list[UUID]|None=Field(default=None,min_length=1,max_length=256)
    expires_at:float|None=None

    @model_validator(mode='after')
    def scope(self):
        if len(self.rights)!=len(set(self.rights)):raise ValueError('Les droits doivent être distincts.')
        if self.function_ids is not None and 'create' in self.rights:raise ValueError('Create exige une portée sur toutes les fonctions du service.')
        if self.expires_at is not None and self.expires_at<=time.time():raise ValueError('L’expiration doit être future.')
        return self


# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
class HttpEvent(Strict):
    path:str=Field(min_length=1,max_length=256,pattern=r'^[A-Za-z0-9_/-]+$')
    methods:list[Literal['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS']]=Field(min_length=1,max_length=7)
    implicit:bool=False

    @model_validator(mode='after')
    def exact(self):
        if any(part in ('','.','..') for part in self.path.split('/')):raise ValueError('Chemin HTTP relatif exact requis.')
        if len(self.methods)!=len(set(self.methods)):raise ValueError('Les méthodes HTTP doivent être distinctes.')
        return self


class ScheduleEvent(Strict):
    cron:str=Field(min_length=9,max_length=256)
    enabled:bool=True
    timezone:Literal['UTC']='UTC'

    @field_validator('cron')
    @classmethod
    def schedule(cls,value):
        parts=value.split()
        if len(parts)!=5:raise ValueError('Cron attendu : cinq champs numériques.')
        for part,(low,high) in zip(parts,[(0,59),(0,23),(1,31),(1,12),(0,7)]):
            for item in part.split(','):
                match=re.fullmatch(r'(\*|\d+(?:-\d+)?)(?:/(\d+))?',item)
                if not match:raise ValueError('Champ cron invalide.')
                base,step=match.groups()
                if step is not None and not 1<=int(step)<=high-low+1:raise ValueError('Pas cron hors limites.')
                if base!='*':
                    numbers=[int(n) for n in base.split('-')]
                    if not all(low<=n<=high for n in numbers) or numbers[0]>numbers[-1]:raise ValueError('Plage cron invalide.')
        return ' '.join(parts)


class Events(Strict):
    http:list[HttpEvent]=Field(default_factory=list,max_length=16)
    schedules:list[ScheduleEvent]=Field(default_factory=list,max_length=16)

    @model_validator(mode='after')
    def unique(self):
        routes=set()
        for event in self.http:
            for method in event.methods:
                key=(event.path,method)
                if key in routes:raise ValueError('Route HTTP dupliquée.')
                routes.add(key)
        return self


class DeploymentCreate(Strict):
    config:FunctionConfig
    configuration:Configuration=Field(default_factory=Configuration)
    events:Events=Field(default_factory=Events)


class Rollback(Strict):
    revision_id:UUID
