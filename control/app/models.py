# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#gestion | docs/PLATFORM.md
# Explicit management DTOs; unknown fields and invalid resource contracts fail.
import ipaddress
import re
import time
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .invocation_http import canonical_origin,canonical_network


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
        return sorted({canonical_origin(value) for value in values})

    @field_validator('ips')
    @classmethod
    def networks(cls,values):
        try:return sorted({canonical_network(value) for value in values})
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


# @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#configuration-de-service-et-surcharges
class ServiceConfiguration(Configuration):
    replace_secrets:bool=False

    @model_validator(mode='after')
    def explicit_replacement(self):
        if self.replace_secrets and 'secrets' not in self.model_fields_set:
            raise ValueError('Le remplacement des secrets exige un mapping secrets explicite.')
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
        # @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009
        from .schedule_calendar import compile_cron
        return compile_cron(value).expression


class Events(Strict):
    http:list[HttpEvent]=Field(default_factory=list,max_length=16)
    schedules:list[ScheduleEvent]=Field(default_factory=list,max_length=16)

    @model_validator(mode='after')
    def unique(self):
        routes=set();implicit=set()
        for event in self.http:
            for method in event.methods:
                key=(event.path,method)
                if key in routes:raise ValueError('Route HTTP dupliquée.')
                routes.add(key)
                if event.implicit:
                    if method in implicit:raise ValueError('Endpoint implicite dupliqué pour cette méthode.')
                    implicit.add(method)
        return self


class DeploymentCreate(Strict):
    config:FunctionConfig
    configuration:Configuration=Field(default_factory=Configuration)
    events:Events=Field(default_factory=Events)
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication
    restore_code_hash:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')


# @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md
class CodeDeploymentCreate(Strict):
    handler:str=Field(min_length=3,max_length=256)
    deployment_id:UUID
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication
    events:Events|None=None
    restore_code_hash:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')

    @field_validator('handler')
    @classmethod
    def handler_path(cls,value):
        return FunctionConfig.handler_path(value)


class Rollback(Strict):
    revision_id:UUID


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#archivage-restauration-et-suppression
class VersionDisposition(Strict):
    replacement_code_hash:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    disable_default:bool=False

    @model_validator(mode='after')
    def exclusive_target(self):
        if self.replacement_code_hash is not None and self.disable_default:
            raise ValueError('Choisissez une version de remplacement ou la désactivation de la cible.')
        return self
