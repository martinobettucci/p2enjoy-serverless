# @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md#api-de-la-console
"""Bounded, admin-only real HTTP requests to this installation's public gateway."""
import asyncio
import base64
import binascii
import json
import logging
import re
import time
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter,HTTPException,Request
from fastapi.exceptions import RequestValidationError
import httpx
from pydantic import Field,ValidationError,field_validator,model_validator

from .db import audit
from .function_versions import live_function
from .instances import HEADER_NAME,WITHHELD,joined
from .invocation_http import canonical_origin
from .invocation_urls import read_routes
from .models import Strict,TokenCreate
from .service_tokens import create_token

REQUEST_LIMIT=1024**2
RESPONSE_LIMIT=6*1024**2
ENVELOPE_LIMIT=2*1024**2
RESERVED=WITHHELD|{'cookie','cookie2','x-csrf-token','x-serverless-token','x-request-id',
                    'x-serverless-code-hash','accept-encoding','forwarded','x-real-ip','x-forwarded-for',
                    'x-forwarded-host','x-forwarded-proto','access-control-request-method','access-control-request-headers'}


class Pair(Strict):
    name:str=Field(max_length=8192)
    value:str=Field(max_length=8192)


class TestInvocation(Strict):
    origin:str=Field(min_length=1,max_length=280)
    version:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    path:str|None=Field(default=None,max_length=256)
    query:list[Pair]=Field(default_factory=list,max_length=128)
    method:str=Field(pattern=r'^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$')
    headers:list[Pair]=Field(default_factory=list,max_length=64)
    token:str=Field(min_length=1,max_length=512)
    body_base64:str=Field(default='',max_length=ENVELOPE_LIMIT)
    max_response_wait_seconds:float=Field(default=30,ge=1,le=900)

    @field_validator('origin')
    @classmethod
    def exact_origin(cls,value):
        if canonical_origin(value)!=value:raise ValueError('Choisissez une origine exacte du catalogue.')
        return value

    @field_validator('path')
    @classmethod
    def relative_path(cls,value):
        if value is not None and (not re.fullmatch(r'[A-Za-z0-9_/-]+',value) or any(p in ('','.','..') for p in value.split('/'))):
            raise ValueError('Le chemin doit être relatif et exact, sans segment vide.')
        return value

    @model_validator(mode='after')
    def bounded_parameters(self):
        if sum(len(p.name.encode('utf8'))+len(p.value.encode('utf8')) for p in self.query)>8192:
            raise ValueError('Les paramètres de requête sont limités à 8 Kio.')
        names=set();size=0
        for pair in self.headers:
            name=pair.name.lower()
            if (len(name)>128 or not pair.name.isascii() or not HEADER_NAME.fullmatch(pair.name) or name in RESERVED or
                    name.startswith(('proxy-','sec-','x-forwarded-'))):
                raise ValueError('Un en-tête est invalide ou réservé au transport.')
            if name in names:raise ValueError('Un en-tête ne peut pas être présent deux fois.')
            names.add(name)
            if pair.value!=pair.value.strip() or any(ord(c)<32 or ord(c)==127 or ord(c)>255 for c in pair.value):
                raise ValueError('Une valeur d’en-tête contient un caractère interdit ou des espaces de bordure.')
            size+=len(pair.name)+len(pair.value)
            if name=='origin':canonical_origin(pair.value)
        if size>16384:raise ValueError('Les en-têtes sont limités à 16 Kio.')
        if any(ord(c)<33 or ord(c)>126 for c in self.token):raise ValueError('Le jeton doit être une valeur ASCII sans espace.')
        try:body=base64.b64decode(self.body_base64,validate=True)
        except (binascii.Error,ValueError):raise ValueError('Le corps doit être encodé en base64 valide.') from None
        if body and self.method in ('GET','HEAD'):raise ValueError('GET et HEAD ne portent pas de corps.')
        return self


class FunctionHttpClient:
    def __init__(self,database,identity):
        self.db,self.identity=database,identity
        self.active=0
        # HTTPX INFO includes query strings, and httpcore DEBUG includes headers.
        # The application owns its structured, metadata-only request logging.
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)

    async def read_json(self,request,limit):
        body=bytearray()
        try:
            async with asyncio.timeout(30):
                async for chunk in request.stream():
                    if len(body)+len(chunk)>limit:raise HTTPException(413,'Le corps dépasse sa limite autorisée.')
                    body.extend(chunk)
        except TimeoutError:raise HTTPException(408,'Le délai de réception est dépassé.') from None
        try:return json.loads(body)
        except (UnicodeError,ValueError):raise HTTPException(422,'Un objet JSON valide est requis.') from None

    def destination(self,request,key,data):
        server=request.scope.get('server')
        if not server or not isinstance(server[1],int):raise HTTPException(503,'Le port de la passerelle est indisponible.')
        source,domains=read_routes(server[1])
        if source['state']!='available':raise HTTPException(503,'Le catalogue des domaines est indisponible. Actualisez avant de réessayer.')
        if data.origin not in {v['origin'] for v in domains if not v['domain'].startswith('*.')}:
            raise HTTPException(422,'La destination ne fait pas partie des domaines d’appel de cette installation.')
        url=data.origin+'/invoke/'+str(key)+('@'+data.version if data.version is not None else '')
        if data.path is not None:url+='/'+data.path
        if data.query:url+='?'+urlencode([(p.name,p.value) for p in data.query])
        return url

    async def forward(self,url,data):
        headers=[(p.name.encode('ascii'),p.value.encode('latin1')) for p in data.headers]
        headers.extend([(b'X-Serverless-Token',data.token.encode('ascii')),(b'Accept-Encoding',b'identity')])
        async with httpx.AsyncClient(trust_env=False,follow_redirects=False,
                                     timeout=httpx.Timeout(None,connect=10,write=10,pool=10)) as client:
            async with client.stream(data.method,url,headers=headers,content=base64.b64decode(data.body_base64)) as response:
                body=bytearray();truncated=False
                async for block in response.aiter_raw(chunk_size=65536):
                    available=RESPONSE_LIMIT-len(body)
                    body.extend(block[:available])
                    if len(block)>available:truncated=True;break
                received=[];size=0;header_truncated=False
                for name,value in response.headers.raw:
                    if len(received)>=128 or size+len(name)+len(value)>32768:header_truncated=True;break
                    received.append({'name':name.decode('latin1'),'value':value.decode('latin1')});size+=len(name)+len(value)
                identifier=response.headers.get('x-serverless-request-id')
                try:identifier=str(UUID(identifier)) if identifier else None
                except ValueError:identifier=None
                code_hash=response.headers.get('x-serverless-code-hash')
                if not code_hash or not re.fullmatch('[0-9a-f]{64}',code_hash):code_hash=None
                return {'state':'response','status':response.status_code,'headers':received,
                        'body_base64':base64.b64encode(body).decode('ascii'),'body_bytes':len(body),
                        'body_truncated':truncated,'headers_truncated':header_truncated,
                        'request_id':identifier,'code_hash':code_hash,'body_representation':'wire'}

    async def invoke(self,request,key):
        actor=await self.identity.admin(request,True)
        with self.db.transaction() as db:live_function(db,key)
        if self.active>=4:raise HTTPException(429,'Quatre appels de test sont déjà en cours. Attendez leur fin.')
        self.active+=1;outgoing=watcher=None
        try:
            request.state.test_request_authorized=True
            raw=await self.read_json(request,ENVELOPE_LIMIT)
            try:data=TestInvocation.model_validate(raw)
            except ValidationError as error:raise RequestValidationError(error.errors()) from None
            if len(base64.b64decode(data.body_base64))>REQUEST_LIMIT:
                raise HTTPException(413,'Le corps envoyé à la fonction est limité à 1 Mio.')
            actor=await self.identity.admin(request,True)
            with self.db.transaction() as db:
                function=live_function(db,key)
                audit(db,actor,'function.test',str(key),function['service_id'])
            url=self.destination(request,key,data);started=time.monotonic()
            async def disconnected():
                while True:
                    if (await request.receive())['type']=='http.disconnect':return
            outgoing=asyncio.create_task(self.forward(url,data));watcher=asyncio.create_task(disconnected())
            try:
                async with asyncio.timeout(data.max_response_wait_seconds):
                    await asyncio.wait((outgoing,watcher),return_when=asyncio.FIRST_COMPLETED)
                    if not outgoing.done():raise HTTPException(499,'Attente interrompue ; l’issue de l’invocation peut rester inconnue.')
                    result=outgoing.result()
            except (TimeoutError,httpx.HTTPError):
                result={'state':'unconfirmed','error':'response_wait_expired' if not outgoing.done() else 'transport_unavailable',
                        'status':None,'request_id':None,'code_hash':None}
            return result|{'duration_ms':round((time.monotonic()-started)*1000,3)}
        finally:
            tasks=[task for task in (outgoing,watcher) if task is not None]
            for task in tasks:task.cancel()
            try:
                if tasks:await joined(asyncio.gather(*tasks,return_exceptions=True))
            finally:self.active-=1

    def routes(self):
        api=APIRouter(prefix='/api/functions')

        @api.post('/{key}/test-token',status_code=201)
        async def temporary_token(request:Request,key:UUID):
            actor=await self.identity.admin(request,True)
            if await self.read_json(request,256*1024)!={}:raise HTTPException(422,'Cette création ne prend aucun paramètre.')
            actor=await self.identity.admin(request,True)
            with self.db.transaction() as db:
                function=live_function(db,key)
                data=TokenCreate(name='console-invocation-'+function['name'],rights=['read'],
                                 function_ids=[key],expires_at=time.time()+900)
                return create_token(db,function['service_id'],data,actor)

        @api.post('/{key}/test-invocation')
        async def invoke(request:Request,key:UUID):return await self.invoke(request,key)

        return api
