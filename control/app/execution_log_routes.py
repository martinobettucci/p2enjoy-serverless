# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#api-droits-et-snapshots
"""Read-authorized journal API and administrator-owned retention policy."""
import asyncio
from contextlib import closing,contextmanager
from contextvars import ContextVar
import ctypes
import sqlite3
import time
from uuid import UUID

from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import Response
from pydantic import Field

from . import execution_log_queries as queries
from .execution_logs import policy,RETENTION_MINUTES
from .instances import joined
from .models import Strict

READ_BUDGET=ContextVar('execution_log_read_budget',default=None)


class LogPolicy(Strict):
    retention_minutes:int=Field(ge=1,le=RETENTION_MINUTES,strict=True)


@contextmanager
def reader_name(name):
    """Name the real Linux worker for operator diagnostics, restoring its name."""
    libc=ctypes.CDLL(None,use_errno=True)
    previous=ctypes.create_string_buffer(16)
    if libc.prctl(16,ctypes.byref(previous),0,0,0)!=0:raise OSError(ctypes.get_errno(),'thread_name_read')
    if libc.prctl(15,ctypes.c_char_p(name.encode('ascii')),0,0,0)!=0:raise OSError(ctypes.get_errno(),'thread_name_write')
    try:yield
    finally:
        if libc.prctl(15,ctypes.byref(previous),0,0,0)!=0:raise OSError(ctypes.get_errno(),'thread_name_restore')


class ExecutionLogRoutes:
    def __init__(self,database,identity,vault):
        self.db,self.identity,self.vault=database,identity,vault
        self.readers=0

    @contextmanager
    def reader_slot(self):
        if self.readers>=2:raise HTTPException(429,'Les lecteurs de journaux sont occupés.',headers={'Retry-After':'2'})
        self.readers+=1
        token=READ_BUDGET.set({'remaining':queries.READ_SECONDS})
        try:yield
        finally:
            READ_BUDGET.reset(token)
            self.readers-=1

    async def io(self,callback,*args,name='journal-check',**kwargs):
        budget=READ_BUDGET.get()
        started=time.monotonic()
        deadline=started+(budget['remaining'] if budget is not None else queries.READ_SECONDS)
        def work():
            with reader_name(name):
                if time.monotonic()>deadline:raise HTTPException(503,'log_read_timeout')
                result=callback(*args,deadline=deadline,**kwargs)
                if time.monotonic()>deadline:raise HTTPException(503,'log_read_timeout')
                return result
        try:return await joined(asyncio.create_task(asyncio.to_thread(work)))
        except (sqlite3.Error,OSError):raise HTTPException(503,'log_read_unavailable') from None
        finally:
            if budget is not None:budget['remaining']-=time.monotonic()-started

    def subject(self,sql,args,*,deadline):
        with closing(self.db.connect()) as db:
            queries.configure_sql(db,deadline)
            row=db.execute(sql,args).fetchone()
            return dict(row) if row else None

    async def authorize(self,request,key,kind):
        function=None
        if kind=='function':
            function=await self.io(self.subject,'SELECT id,service_id FROM functions WHERE id=? AND deleted_at IS NULL AND purged_at IS NULL',(str(key),),name='journal-subject')
            service_id=function['service_id'] if function else ''
            authorization=await self.identity.operation(request,service_id,'read',str(key))
            if function is None:raise HTTPException(404,'Fonction introuvable.')
        else:
            service_id=str(key)
            authorization=await self.identity.operation(request,service_id,'read',None)
        service=await self.io(self.subject,'SELECT id FROM services WHERE id=? AND deleted_at IS NULL',(service_id,),name='journal-subject')
        if service is None:raise HTTPException(404,'Service introuvable.')
        return authorization,service_id,function['id'] if function else None

    def final_check(self,authorization,service_id,function_id,result=None,*,deadline):
        with closing(self.db.connect()) as connection:
            queries.configure_sql(connection,deadline)
            # The read decision is ordered against accepted revocations/purges.
            # This brief reservation never survives into response transmission.
            connection.execute('BEGIN IMMEDIATE')
            if not connection.execute('SELECT id FROM services WHERE id=? AND deleted_at IS NULL',(service_id,)).fetchone():
                raise HTTPException(404,'Service introuvable.')
            if function_id and not connection.execute('SELECT id FROM functions WHERE id=? AND service_id=? AND deleted_at IS NULL AND purged_at IS NULL',(function_id,service_id)).fetchone():
                raise HTTPException(404,'Fonction introuvable.')
            current=policy(connection,service_id)
            if result:
                if current['version']!=result['policy_version']:raise HTTPException(410,'log_policy_changed')
                if current['prune_generation']!=result['prune_generation']:
                    raise HTTPException(410,'log_read_incomplete_'+(current['prune_reason'] or 'retention'))
                if result['earliest'] is not None and result['earliest']<current['effective_floor']:
                    raise HTTPException(410,'log_read_incomplete_retention')
            actor=self.identity.recheck(connection,authorization,service_id,'read',function_id,service_read=function_id is None)
            if result and queries.binding(actor,service_id,function_id)!=result['context']:
                raise HTTPException(409,'log_authorization_context_changed')
            if time.monotonic()>deadline:raise HTTPException(503,'log_read_timeout')
            connection.execute('COMMIT')
            return current

    async def read(self,request,key,kind,*,export=False):
        with self.reader_slot():
            authorization,service_id,function_id=await self.authorize(request,key,kind)
            actor=authorization.actor
            values=queries.parameters(request.query_params)
            # The slot remains held even after cancellation/deadline until real IO
            # joins. No abandoned worker can free capacity for a third reader.
            result=await self.io(queries.read,self.db,self.vault,service_id,function_id,actor,values,export=export,name='journal-read')
            current_authorization,current_service,current_function=await self.authorize(request,key,kind)
            if queries.binding(current_authorization.actor,current_service,current_function)!=result['context']:
                raise HTTPException(409,'log_authorization_context_changed')
            await self.io(self.final_check,current_authorization,service_id,function_id,result,name='journal-verify')
            data=result['data']
            if export:
                filename='journaux-'+kind+'-'+str(key)+('.jsonl' if result['format']=='jsonl' else '.txt')
                headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
                    'Content-Disposition':'attachment; filename="'+filename+'"',
                    'X-Log-Count':str(len(data['items'])),'X-Log-Partial':str(data['partial']).lower(),
                    'X-Log-Next-Offset':'' if data['next_offset'] is None else str(data['next_offset']),
                    'X-Log-Snapshot':data['snapshot'],'X-Log-Collection':data['collection']['id']}
                return Response(result['body'],media_type='application/x-ndjson' if result['format']=='jsonl' else 'text/plain',headers=headers)
            return Response(result['body'],media_type='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    async def get_policy(self,request,key):
        with self.reader_slot():
            authorization,service_id,function_id=await self.authorize(request,key,'service')
            current=await self.io(self.final_check,authorization,service_id,function_id,name='journal-policy')
            return self.public_policy(current)

    @staticmethod
    def public_policy(current):
        return {key:current[key] for key in ('service_id','retention_minutes','version','updated_at','effective_floor')}

    async def put_policy(self,request,key,data):
        if request.headers.get('x-serverless-token') is not None:
            raise HTTPException(403,'La conservation exige une session administrateur.')
        authorization=await self.identity.operation(request,str(key),'update',None)
        expected=request.headers.get('if-match')
        if expected is None:raise HTTPException(428,'If-Match est obligatoire pour cette opération.')
        return await self.io(self.write_policy,authorization,str(key),expected,data.retention_minutes,name='journal-write')

    def write_policy(self,authorization,key,expected,retention_minutes,*,deadline):
        now=time.time()
        with closing(self.db.connect()) as db:
            queries.configure_sql(db,deadline)
            db.execute('BEGIN IMMEDIATE')
            actor=self.identity.recheck(db,authorization,key,'update',None)
            if not db.execute('SELECT id FROM services WHERE id=? AND deleted_at IS NULL',(key,)).fetchone():
                raise HTTPException(404,'Service introuvable.')
            current=policy(db,key,now=now,create=True)
            if expected!=str(current['version']):raise HTTPException(409,'La conservation a changé. Relisez sa version avant de poursuivre.')
            changed=retention_minutes!=current['retention_minutes']
            if changed:
                floor=max(current['effective_floor'],now-retention_minutes*60)
                db.execute('''UPDATE service_log_policies SET retention_minutes=?,version=version+1,
                    updated_at=?,expiration_floor=? WHERE service_id=?''',(retention_minutes,now,floor,key))
                from .db import audit
                audit(db,actor,'service.log_retention',key,key,
                    {'retention_minutes':retention_minutes,'policy_version':current['version']+1})
            current=policy(db,key,now=now)
            if time.monotonic()>deadline:raise HTTPException(503,'log_policy_write_timeout')
            db.execute('COMMIT')
        return {**self.public_policy(current),'changed':changed}

    def routes(self):
        api=APIRouter()
        @api.get('/api/functions/{key}/logs')
        async def function_logs(request:Request,key:UUID):return await self.read(request,key,'function')
        @api.get('/api/services/{key}/logs')
        async def service_logs(request:Request,key:UUID):return await self.read(request,key,'service')
        @api.get('/api/functions/{key}/logs/export')
        async def function_export(request:Request,key:UUID):return await self.read(request,key,'function',export=True)
        @api.get('/api/services/{key}/logs/export')
        async def service_export(request:Request,key:UUID):return await self.read(request,key,'service',export=True)
        @api.get('/api/services/{key}/log-policy')
        async def read_policy(request:Request,key:UUID):return await self.get_policy(request,key)
        @api.put('/api/services/{key}/log-policy')
        async def update_policy(request:Request,key:UUID,data:LogPolicy):return await self.put_policy(request,key,data)
        return api
