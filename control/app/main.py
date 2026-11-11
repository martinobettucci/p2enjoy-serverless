# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md | docs/SCHEMA.md
# Application lifecycle, bounded input, safe errors and canonical auth routes.
from contextlib import asynccontextmanager
import html
import json
import logging
from pathlib import Path
import sqlite3
from urllib.parse import parse_qsl,urlencode,urlsplit
from uuid import UUID,uuid4

from cryptography.fernet import InvalidToken
from fastapi import FastAPI,HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse,HTMLResponse,JSONResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import router
from .auth import Identity,SESSION_COOKIE,FLOW_COOKIE,AccessPending
from .config import Settings,Vault
from .db import Database,audit
from .deployments import Deployments
from .function_operations import FunctionOperations
from .storage_management import StorageManagement
from .execution import Execution
# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009
from .schedules import Schedules
from .invocation_routes import routes as invocation_routes,gateway_error
from .network import forwarded_addresses
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md
from .invocation_urls import routes as invocation_url_routes
# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md
from .catalogue import catalogue_query, routes as catalogue_routes

logger=logging.getLogger('p2enjoy.control')


class BodyLimit:
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        total=0
        async def limited():
            nonlocal total
            message=await receive()
            if message['type']=='http.request':
                total+=len(message.get('body',b''))
                state=scope.get('state',{})
                limit=64*1024**2 if state.get('artifact_upload_authorized') is True else 1024**2 if state.get('invocation_authorized') is True else 256*1024
                if total>limit:raise HTTPException(413,'Le corps de requête dépasse sa limite autorisée.')
            return message
        await self.app(scope,limited,send)


settings=Settings.load()
database=Database(settings.state_dir)
vault=Vault(settings.master_key)
identity=Identity(settings,database,vault)
operations=FunctionOperations(settings,database)
deployments=Deployments(settings,database,identity,vault,operations)
execution=Execution(settings,database,identity,vault,operations,deployments)
operations.execution=execution
schedules=Schedules(execution)
# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md
storage_management=StorageManagement(database,identity,vault,operations,deployments)
operations.discards=storage_management


@asynccontextmanager
async def lifespan(app):
    await deployments.start()
    try:
        database.migrate()
        marker={'purpose':'p2enjoy-serverless-control','version':1}
        with database.transaction() as db:
            row=db.execute("SELECT value FROM security_metadata WHERE name='master-key'").fetchone()
            if row:
                try:valid=vault.open(row['value'])==marker
                except (InvalidToken,ValueError):valid=False
                if not valid:raise RuntimeError('La clé maîtresse ne correspond pas à cette base.')
            else:db.execute('INSERT INTO security_metadata VALUES (?,?)',('master-key',vault.seal(marker)))
        await deployments.ready()
        await operations.ready(deployments.installation)
        await execution.ready(deployments.installation)
        await schedules.ready()
        yield
    finally:
        try:
            try:await schedules.close()
            finally:
                try:await operations.close()
                finally:await execution.close()
        finally:
            await deployments.close()
            await identity.close()


app=FastAPI(title='P2Enjoy Serverless',lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(BodyLimit)
app.include_router(router(database,identity,vault,operations))
app.include_router(deployments.routes())
app.include_router(invocation_routes(execution))
app.include_router(schedules.routes())
app.include_router(storage_management.routes())
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#api-et-calcul-commun
app.include_router(invocation_url_routes(database,identity,settings))
# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#lecture-et-périmètre
app.include_router(catalogue_routes(database,identity))
web_root=Path(__file__).parent.parent/'web'
app.mount('/assets',StaticFiles(directory=web_root/'assets'),name='assets')


@app.middleware('http')
async def response_headers(request:Request,call_next):
    request.state.request_id=str(uuid4())
    response=await call_next(request)
    if request.url.path.startswith('/invoke/'):
        if 'X-Request-ID' not in response.headers:response.headers['X-Request-ID']=request.state.request_id
        return response
    response.headers['X-Request-ID']=request.state.request_id
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    return response


@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_error(request:Request,error:HTTPException):
    if request.url.path.startswith('/invoke/'):return gateway_error(execution,request,error.status_code)
    # No query string: OAuth codes and state must never enter access logs.
    if error.status_code>=400:
        route=getattr(request.scope.get('route'),'path','unmatched')
        forwarded=forwarded_addresses(request)
        logger.warning(json.dumps({'event':'request.refused','status':error.status_code,
                                   'route':route,'request_id':getattr(request.state,'request_id',None),
                                   'transport_peer':request.client.host if request.client else None,
                                   'untrusted_forwarded_for':[str(ip) for ip in forwarded] if forwarded is not None else 'invalid'}))
        actor=getattr(request.state,'actor',None)
        if actor:
            key=request.path_params.get('key')
            try:key=str(UUID(str(key))) if key else None
            except ValueError:key=None
            service_id=actor.service_id
            try:
                if actor.kind=='admin' and key:
                    if route.startswith('/api/services/'):service_id=key
                    elif route.startswith(('/api/functions/','/api/archives/','/api/tokens/')):
                        table='service_tokens' if '/tokens/' in route else 'functions'
                        row=database.one(f'SELECT service_id FROM {table} WHERE id=?',(key,))
                        if row:service_id=row['service_id']
                    elif route.startswith('/api/deployments/'):
                        row=database.one('SELECT service_id,function_id FROM deployments WHERE id=?',(key,))
                        if row:service_id=row['service_id'];key=row['function_id']
                    elif route.startswith('/api/storage-operations/'):
                        row=database.one('SELECT service_id,function_id FROM storage_commands WHERE id=?',(key,))
                        if row:service_id=row['service_id'];key=row['function_id']
                with database.transaction() as db:
                    audit(db,actor,'request.denied',key,service_id,{'status':error.status_code,'route':route})
            except sqlite3.Error:
                logger.error(json.dumps({'event':'audit.unavailable','request_id':getattr(request.state,'request_id',None)}))
    # @spec docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#attente-de-droits
    payload={'error':error.detail}
    if isinstance(error,AccessPending):payload['access_requirement']=error.access_requirement
    response=JSONResponse(payload,status_code=error.status_code,headers=error.headers)
    if request.url.path=='/auth/login' and 'text/html' in request.headers.get('accept',''):
        document=(web_root/'index.html').read_text().replace('<body>',
            '<body data-auth-error="'+html.escape(str(error.detail),quote=True)+'">',1)
        response=HTMLResponse(document,status_code=error.status_code,headers=error.headers)
    if request.url.path=='/auth/retour' and 'text/html' in request.headers.get('accept',''):
        destination=('/auth/attente?'+urlencode({'reason':error.access_requirement}) if isinstance(error,AccessPending)
                     else '/#'+urlencode({'auth-error':str(error.detail)}))
        response=RedirectResponse(settings.public_url+destination,status_code=303)
    if request.url.path=='/auth/retour':response.delete_cookie(FLOW_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
    if isinstance(error,AccessPending):response.delete_cookie(SESSION_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,error:RequestValidationError):
    logger.warning(json.dumps({'event':'request.refused','status':422,
        'route':getattr(request.scope.get('route'),'path','unmatched'),
        'request_id':getattr(request.state,'request_id',None)}))
    errors=[{'field':list(item['loc']),'message':item['msg'],'type':item['type']} for item in error.errors()]
    return JSONResponse({'error':'Données invalides.','details':errors},status_code=422)


@app.exception_handler(sqlite3.IntegrityError)
async def conflict(request:Request,error:sqlite3.IntegrityError):
    return JSONResponse({'error':'Ce nom existe déjà ou la référence est invalide.'},status_code=409)


@app.exception_handler(sqlite3.OperationalError)
async def database_error(request:Request,error:sqlite3.OperationalError):
    trace=error.__traceback__
    while trace and trace.tb_next:trace=trace.tb_next
    logger.error(json.dumps({'event':'database.unavailable','request_id':getattr(request.state,'request_id',None),
        'sqlite_errorname':getattr(error,'sqlite_errorname',None),
        'source':{'file':Path(trace.tb_frame.f_code.co_filename).name,'function':trace.tb_frame.f_code.co_name,
                  'line':trace.tb_lineno} if trace else None}))
    return JSONResponse({'error':'Le stockage du contrôle est temporairement indisponible.'},status_code=503)


@app.get('/healthz')
async def health():
    database.one('SELECT 1')
    if deployments.cleanup_error:raise HTTPException(503,'Le nettoyage des artefacts doit être repris.')
    if operations.cleanup_error or not operations.agent_ready:raise HTTPException(503,'Le stockage des fonctions doit être rétabli ou réconcilié.')
    if schedules.maintenance_error:raise HTTPException(503,'Les planifications doivent être réconciliées.')
    if not execution.healthy():raise HTTPException(503,'Les instances doivent être réconciliées avant la reprise.')
    return {'status':'ok','component':'control','version':'0.1.0-dev'}


# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique
def canonical_entry(request,path):
    configured=urlsplit(settings.public_url)
    # The caller's Host can only decide to use the fixed configured destination.
    hosts=request.headers.getlist('host')
    expected={configured.netloc.lower()}
    if configured.port is None:expected.add(configured.netloc.lower()+':443')
    if len(hosts)!=1 or hosts[0].lower() not in expected:
        if path.startswith('/console/'):
            selected={}
            try:parameters=parse_qsl(request.url.query,max_num_fields=32,keep_blank_values=True)
            except ValueError:parameters=[]
            for name,value in parameters:
                if name in ('deployment','operation'):
                    try:selected[name]=str(UUID(value))
                    except ValueError:pass
                # @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#parcours-et-adresses
                elif name=='catalogue':
                    try:selected[name]=catalogue_query(value)
                    except ValueError:pass
            # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
            if path.endswith('/invocation-urls'):
                versions=[value for name,value in parameters if name=='version']
                if versions:
                    # Even an invalid/duplicate selector must remain a refused
                    # explicit selection instead of becoming the default view.
                    selected['version']=versions[0] if len(versions)==1 and len(versions[0])<=256 else 'invalid'
                elif request.url.query and not parameters:selected['version']='invalid'
            if path=='/console/functions':
                try:selected.update(dict(parse_qsl(catalogue_query(urlencode([(k,v) for k,v in parameters if k!='catalogue'])))))
                except ValueError:pass
            if selected:path+='?'+urlencode(selected)
        return RedirectResponse(settings.public_url+path,status_code=303)
    return None


# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique
@app.get('/')
@app.get('/console/{path:path}')
async def home(request:Request,path=''):
    return canonical_entry(request,'/console/'+path if request.url.path.startswith('/console/') else '/') or FileResponse(web_root/'index.html',media_type='text/html')


@app.get('/favicon.svg')
async def favicon():return FileResponse(web_root/'favicon.svg',media_type='image/svg+xml')


@app.get('/api/session')
async def session(request:Request):
    try:row=await identity.session(request)
    except HTTPException as error:
        if error.status_code==401:return {'authenticated':False}
        raise
    return {'authenticated':True,'user':{'id':row['subject'],'name':row['display_name']},
            'csrf_token':row['payload']['csrf'],'expires_at':row['expires_at']}


@app.get('/auth/login')
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique
async def login(request:Request):return canonical_entry(request,'/auth/login') or await identity.login(request)


@app.get('/auth/retour')
async def callback(request:Request):return await identity.callback(request)


# @spec docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#attente-de-droits
@app.get('/auth/attente')
async def access_waiting(request:Request):
    reason=request.query_params.get('reason')
    if reason not in ('verification','administration'):raise HTTPException(400,'Motif d’attente inconnu.')
    return (canonical_entry(request,'/auth/attente?'+urlencode({'reason':reason}))
            or FileResponse(web_root/'index.html',media_type='text/html'))


@app.post('/auth/logout')
async def logout(request:Request):
    result=await identity.logout(request)
    response=JSONResponse(result)
    response.delete_cookie(SESSION_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
    response.delete_cookie(FLOW_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
    return response
