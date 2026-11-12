# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#entrée-http | docs/ADMISSION.md#observations-et-cycle-du-contrôle
"""Authenticated public gateway and authorized execution observations."""
import asyncio
import base64
from contextlib import suppress
import json
import sqlite3
from uuid import UUID,uuid4

from fastapi import APIRouter,HTTPException,Query,Request
from fastapi.responses import JSONResponse,Response
from starlette.requests import ClientDisconnect

from .invocation_http import InvocationError,canonical_origin,declared_path,policy_allows,preflight_headers
from .network import client_address
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#sélection-http-et-admission
from .function_versions import selected_revision

METHODS=['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS']


def gateway_error(execution,request,status):
    identifier=getattr(request.state,'request_id',None) or str(uuid4())
    code={404:'route_not_found',405:'method_not_allowed',413:'body_limit',422:'invalid_request'}.get(status,'execution_unavailable')
    response=JSONResponse({'error':code,'invocation_id':identifier},status_code=status,
        headers={'X-Request-ID':identifier,'X-Serverless-Request-ID':identifier,'Vary':'Origin',
                 'Access-Control-Expose-Headers':'X-Request-ID, X-Serverless-Request-ID'})
    if request.method=='HEAD':response.body=b''
    try:
        origins=request.headers.getlist('origin')
        if len(origins)!=1:return response
        origin=canonical_origin(origins[0]);source_ip=client_address(request,execution.settings.trusted_proxies)
        function_id=str(UUID(request.url.path.split('/')[2].split('@',1)[0]))
        row=execution.db.one('SELECT s.policy_json FROM services s JOIN functions f ON f.service_id=s.id WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL',(function_id,))
        if row and policy_allows(json.loads(row['policy_json']),origin,source_ip):response.headers['Access-Control-Allow-Origin']=origin
    except (ValueError,IndexError,HTTPException,sqlite3.Error):pass
    return response


def routes(execution):
    api=APIRouter();db=execution.db;identity=execution.identity

    def cors(response,function_id,origin,source_ip,preflight=False):
        vary=[]
        for value in response.headers.getlist('vary'):vary.extend(x.strip() for x in value.split(','))
        for name in ['Origin']+(['Access-Control-Request-Method','Access-Control-Request-Headers'] if preflight else []):
            if name.lower() not in {v.lower() for v in vary}:vary.append(name)
        response.headers['Vary']=', '.join(vary)
        if origin and source_ip:
            try:
                row=db.one('SELECT s.policy_json FROM services s JOIN functions f ON f.service_id=s.id WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL',(function_id,))
                if row and policy_allows(json.loads(row['policy_json']),origin,source_ip):response.headers['Access-Control-Allow-Origin']=origin
            except sqlite3.Error:pass
        return response

    async def disconnected(request):
        while True:
            if (await request.receive())['type']=='http.disconnect':return

    async def invoke(request:Request,function_id:str,path:str|None=None):
        identifier=str(uuid4());origin=None;source_ip=None;call=None;watcher=None
        preflight=request.method=='OPTIONS' and 'access-control-request-method' in request.headers
        try:
            base,separator,selector=function_id.partition('@')
            requested_hash=selector if separator else None
            try:function_id=str(UUID(base))
            except ValueError:raise InvocationError(404,'function_not_found') from None
            origins=request.headers.getlist('origin');tokens=request.headers.getlist('x-serverless-token')
            if len(origins)>1 or len(tokens)>1:raise InvocationError(400,'duplicate_security_header')
            if origins and origins[0]!='null':
                try:origin=canonical_origin(origins[0])
                except ValueError:raise InvocationError(400,'invalid_origin') from None
            source_ip=client_address(request,execution.settings.trusted_proxies)
            function=db.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(function_id,))
            if not preflight:
                if not tokens or not tokens[0]:raise InvocationError(401,'missing_token')
                authorization=await identity.operation(request,function['service_id'] if function else '', 'read',function_id)
                if authorization.actor.kind!='token':raise InvocationError(401,'missing_token')
            if not function:raise InvocationError(404,'function_not_found')
            service=db.one('SELECT * FROM services WHERE id=? AND deleted_at IS NULL',(function['service_id'],))
            if not service:raise InvocationError(404,'service_not_found')
            if not policy_allows(json.loads(service['policy_json']),origin,source_ip):raise InvocationError(403,'network_policy_denied')
            if preflight:
                methods=request.headers.getlist('access-control-request-method')
                if len(methods)!=1 or methods[0] not in METHODS or not origin:raise InvocationError(400,'invalid_preflight')
                # The preflight never runs a handler or silently chooses default
                # events when a selector is malformed/unavailable.
                from contextlib import closing
                with closing(db.connect()) as connection:
                    connection.execute('BEGIN')
                    current=connection.execute('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(function_id,)).fetchone()
                    if not current:raise InvocationError(404,'function_not_found')
                    revision=selected_revision(connection,current,requested_hash)
                    declared_path(revision,path,methods[0])
                names=preflight_headers(request.headers.getlist('access-control-request-headers'))
                response=Response(status_code=204,headers={'Access-Control-Allow-Methods':methods[0],'Access-Control-Allow-Headers':', '.join(names)})
            else:
                call=execution.receive(function_id,authorization,request.method,path,origin,source_ip,requested_hash);identifier=call.id
                request.state.invocation_authorized=True
                body=bytearray()
                try:
                    async with asyncio.timeout(30):
                        async for chunk in request.stream():
                            body.extend(chunk)
                            if len(body)>1024**2:raise InvocationError(413,'body_limit')
                except TimeoutError:raise InvocationError(408,'body_timeout') from None
                execution.enqueue(call,list(request.headers.raw),request.scope['query_string'],bytes(body))
                watcher=asyncio.create_task(disconnected(request))
                await asyncio.wait((call.future,watcher),return_when=asyncio.FIRST_COMPLETED)
                if watcher.done() and not call.future.done():
                    with suppress(sqlite3.Error):execution.disconnect(call)
                    return Response(status_code=499)
                outcome=call.future.result()
                if outcome.get('state')=='succeeded':
                    value=outcome['response'];payload=base64.b64decode(value['body']) if value['isBase64Encoded'] else value['body'].encode('utf8')
                    response=Response(content=b'' if request.method=='HEAD' or value['statusCode'] in (204,304) else payload,status_code=value['statusCode'])
                    for name,value in value['headers']:
                        if name.lower() not in ('x-request-id','x-serverless-request-id','x-serverless-code-hash'):response.headers.append(name,value)
                else:response=JSONResponse({'error':outcome['error'],'invocation_id':identifier},status_code=outcome['http_status'])
        except (ClientDisconnect,asyncio.CancelledError):
            if call:
                with suppress(sqlite3.Error):execution.disconnect(call)
            raise
        except (HTTPException,sqlite3.Error) as error:
            status=error.status_code if isinstance(error,HTTPException) else 503
            code=error.detail if isinstance(error,InvocationError) else {400:'invalid_request',401:'invalid_token',403:'forbidden',409:'function_busy',413:'body_limit'}.get(status,'execution_unavailable')
            if call and not call.admitted and execution.waiting.get(call.id) is call:
                # reject records its pending decision before SQL; maintenance owns retry.
                with suppress(sqlite3.Error):execution.reject(call,status,code)
            response=JSONResponse({'error':code,'invocation_id':identifier},status_code=status)
        finally:
            if watcher:
                watcher.cancel()
                with suppress(asyncio.CancelledError):await watcher
        if request.method=='HEAD':response.body=b''
        response.headers['X-Serverless-Request-ID']=identifier
        response.headers['X-Request-ID']=identifier
        # @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md#jetons-copie-et-corrélation
        names=[name.strip() for value in response.headers.getlist('access-control-expose-headers') for name in value.split(',') if name.strip()]
        for name in ('X-Request-ID','X-Serverless-Request-ID'):
            if name.lower() not in {value.lower() for value in names}:names.append(name)
        response.headers['Access-Control-Expose-Headers']=', '.join(names)
        if call and call.resolved_code_hash:
            response.headers['X-Serverless-Code-Hash']=call.resolved_code_hash
            names=[name.strip() for value in response.headers.getlist('access-control-expose-headers') for name in value.split(',') if name.strip()]
            if 'x-serverless-code-hash' not in {name.lower() for name in names}:names.append('X-Serverless-Code-Hash')
            response.headers['Access-Control-Expose-Headers']=', '.join(names)
        return cors(response,function_id,origin,source_ip,preflight)

    @api.api_route('/invoke/{function_id}',methods=METHODS)
    async def implicit(request:Request,function_id:str):return await invoke(request,function_id)

    @api.api_route('/invoke/{function_id}/{path:path}',methods=METHODS)
    async def explicit(request:Request,function_id:str,path:str):return await invoke(request,function_id,path)

    async def observation(request,key):
        function=db.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        await identity.authorize(request,function['service_id'] if function else '', 'read',str(key))
        if not function:raise HTTPException(404,'Fonction introuvable.')

    @api.get('/api/functions/{key}/instances')
    async def instances(request:Request,key:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        await observation(request,key)
        rows=db.all('''SELECT i.id,i.function_id,i.revision_id,r.code_hash,i.cpu_nanos,i.memory_mib,i.state,i.created_at,i.ready_at,i.last_used_at,i.error_code
            FROM execution_instances i JOIN revisions r ON r.id=i.revision_id
            WHERE i.function_id=? ORDER BY i.created_at,i.id LIMIT ? OFFSET ?''',(str(key),limit,offset))
        for row in rows:
            row['metrics']=None;row['metrics_error']='instance_unavailable'
            instance=execution.instances.get(row['id'])
            if instance and instance.container and not instance.closing:
                try:row['metrics']=await instance.stats();row['metrics_error']=None
                except Exception:row['metrics_error']='metrics_unavailable'
        total=db.one('SELECT count(*) AS n FROM execution_instances WHERE function_id=?',(str(key),))['n']
        return {'items':rows,'total':total,'limit':limit,'offset':offset}

    @api.get('/api/functions/{key}/invocations')
    async def invocations(request:Request,key:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        await observation(request,key)
        rows=db.all('SELECT * FROM invocations WHERE function_id=? ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?',(str(key),limit,offset))
        for row in rows:
            if row['handler_started'] is not None:row['handler_started']=bool(row['handler_started'])
            row['logs_truncated']=bool(row['logs_truncated'])
        total=db.one('SELECT count(*) AS n FROM invocations WHERE function_id=?',(str(key),))['n']
        return {'items':rows,'total':total,'limit':limit,'offset':offset}

    # @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md#api-de-la-console
    @api.get('/api/functions/{key}/invocations/{identifier}')
    async def invocation(request:Request,key:UUID,identifier:UUID):
        await observation(request,key)
        row=db.one('SELECT * FROM invocations WHERE id=? AND function_id=?',(str(identifier),str(key)))
        if not row:raise HTTPException(404,'Cette invocation est absente ou n’est plus conservée.')
        if row['handler_started'] is not None:row['handler_started']=bool(row['handler_started'])
        row['logs_truncated']=bool(row['logs_truncated'])
        return row

    return api
