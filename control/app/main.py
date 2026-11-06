# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md | docs/SCHEMA.md
# Application lifecycle, bounded input, safe errors and canonical auth routes.
from contextlib import asynccontextmanager
import html
import json
import logging
from pathlib import Path
import sqlite3
from urllib.parse import urlencode
from uuid import UUID,uuid4

from cryptography.fernet import InvalidToken
from fastapi import FastAPI,HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse,HTMLResponse,JSONResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .auth import Identity,SESSION_COOKIE,FLOW_COOKIE
from .config import Settings,Vault
from .db import Database,audit
from .deployments import Deployments
from .network import forwarded_addresses

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
                limit=64*1024**2 if scope.get('state',{}).get('artifact_upload_authorized') is True else 256*1024
                if total>limit:raise HTTPException(413,'Le corps de requête dépasse sa limite autorisée.')
            return message
        await self.app(scope,limited,send)


settings=Settings.load()
database=Database(settings.state_dir)
vault=Vault(settings.master_key)
identity=Identity(settings,database,vault)
deployments=Deployments(settings,database,identity,vault)


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
        yield
    finally:
        await deployments.close()
        await identity.close()


app=FastAPI(title='P2Enjoy Serverless',lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(BodyLimit)
app.include_router(router(database,identity,vault))
app.include_router(deployments.routes())
web_root=Path(__file__).parent.parent/'web'
app.mount('/assets',StaticFiles(directory=web_root/'assets'),name='assets')


@app.middleware('http')
async def response_headers(request:Request,call_next):
    request.state.request_id=str(uuid4())
    response=await call_next(request)
    response.headers['X-Request-ID']=request.state.request_id
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    return response


@app.exception_handler(HTTPException)
async def http_error(request:Request,error:HTTPException):
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
            if actor.kind=='admin' and key:
                if route.startswith('/api/services/'):service_id=key
                elif route.startswith('/api/functions/') or route.startswith('/api/tokens/'):
                    table='functions' if '/functions/' in route else 'service_tokens'
                    row=database.one(f'SELECT service_id FROM {table} WHERE id=?',(key,))
                    if row:service_id=row['service_id']
                elif route.startswith('/api/deployments/'):
                    row=database.one('SELECT service_id,function_id FROM deployments WHERE id=?',(key,))
                    if row:service_id=row['service_id'];key=row['function_id']
            with database.transaction() as db:
                audit(db,actor,'request.denied',key,service_id,{'status':error.status_code,'route':route})
    response=JSONResponse({'error':error.detail},status_code=error.status_code,headers=error.headers)
    if request.url.path=='/auth/login' and 'text/html' in request.headers.get('accept',''):
        document=(web_root/'index.html').read_text().replace('<body>',
            '<body data-auth-error="'+html.escape(str(error.detail),quote=True)+'">',1)
        response=HTMLResponse(document,status_code=error.status_code,headers=error.headers)
    if request.url.path=='/auth/retour' and 'text/html' in request.headers.get('accept',''):
        response=RedirectResponse(settings.public_url+'/#'+urlencode({'auth-error':str(error.detail)}),status_code=303)
    if request.url.path=='/auth/retour':response.delete_cookie(FLOW_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
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
    logger.error(json.dumps({'event':'database.unavailable','request_id':getattr(request.state,'request_id',None)}))
    return JSONResponse({'error':'Le stockage du contrôle est temporairement indisponible.'},status_code=503)


@app.get('/healthz')
async def health():
    database.one('SELECT 1')
    if deployments.cleanup_error:raise HTTPException(503,'Le nettoyage des artefacts doit être repris.')
    return {'status':'ok','component':'control','version':'0.1.0-dev'}


@app.get('/')
@app.get('/console/{path:path}')
async def home(path=''):return FileResponse(web_root/'index.html',media_type='text/html')


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
async def login(request:Request):return await identity.login(request)


@app.get('/auth/retour')
async def callback(request:Request):return await identity.callback(request)


@app.post('/auth/logout')
async def logout(request:Request):
    result=await identity.logout(request)
    response=JSONResponse(result)
    response.delete_cookie(SESSION_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
    response.delete_cookie(FLOW_COOKIE,secure=True,httponly=True,samesite='lax',path='/')
    return response
