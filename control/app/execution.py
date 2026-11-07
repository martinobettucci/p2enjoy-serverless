# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md | docs/SCHEMA.md#réservations-et-invocations
"""Durable admission, warm instances and ownership until confirmed disposal."""
import asyncio
from contextlib import suppress
from dataclasses import dataclass
import hashlib
import json
import logging
import math
import sqlite3
import time
from urllib.parse import urlencode
from uuid import UUID,uuid4

from fastapi import HTTPException

from .instances import joined
from .artifacts import ArtifactError
from .managed_instances import ManagedInstance
from .storage_client import StorageError
from .validator import Docker,ValidationError
from .function_operations import storage_configuration
from .invocation_http import InvocationError,declared_path,event_envelope,policy_allows

logger=logging.getLogger('p2enjoy.control')
ACTIVE=('receiving','queued','admitted','running')


@dataclass
class WaitingCall:
    id:str
    function_id:str
    authorization:object
    method:str
    path:str|None
    origin:str|None
    source_ip:str
    future:object
    payload:object=None
    deadline:float|None=None
    attempted:bool=False
    admitted:bool=False
    rejection:tuple|None=None


class Execution:
    def __init__(self,settings,database,identity,vault,operations,deployments):
        self.settings,self.db,self.identity,self.vault=settings,database,identity,vault
        self.operations,self.deployments=operations,deployments
        self.root=settings.state_dir/'execution';self.installation=None
        self.instances={};self.workers={};self.retiring={};self.waiting={};self.retry_at={};self.finalizing={};self.shutdown_task=None
        self.task=None;self.wake=asyncio.Event();self.closing=False;self.reconciled=False;self.maintenance_error=False;self.started=False

    def minimum_budget(self,db,function_id=None,config=None):
        cpu=memory=count=0
        configs=[json.loads(row['config_json']) for row in db.execute('SELECT id,config_json FROM functions WHERE deleted_at IS NULL') if row['id']!=function_id]
        if config is not None:configs.append(config)
        for item in configs:
            minimum=item['min_instances'];count+=minimum;memory+=minimum*item['memory_mib'];cpu+=minimum*math.ceil(item['cpu']*1000000000)
        if cpu>self.settings.function_cpu_nanos or memory>self.settings.function_memory_mib or count>self.settings.function_instance_limit:
            raise InvocationError(409,'minimum_budget_exceeded')

    def current(self,db,function_id):
        function=db.execute('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(function_id,)).fetchone()
        if not function:raise InvocationError(404,'function_not_found')
        service=db.execute('SELECT * FROM services WHERE id=? AND deleted_at IS NULL',(function['service_id'],)).fetchone()
        if not service:raise InvocationError(404,'service_not_found')
        revision=db.execute('SELECT * FROM revisions WHERE id=? AND deleted_at IS NULL',(function['active_revision_id'],)).fetchone()
        return dict(function),dict(service),dict(revision) if revision else None

    def snapshot(self,function,service,revision):
        if not revision:raise InvocationError(409,'function_not_deployed')
        config=json.loads(function['config_json'])
        environment,secrets=self.deployments.effective(service,{'environment':json.loads(function['environment_json']),'secrets':self.vault.open(function['secrets_cipher'])})
        snapshot={'function_id':function['id'],'revision_id':revision['id'],'name':function['name'],'config':config,
                  'environment':environment,'secrets':secrets,'image':revision['image_id']}
        generation=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        return snapshot,generation

    def check_call(self,db,call):
        function,service,revision=self.current(db,call.function_id)
        self.identity.recheck(db,call.authorization,service['id'],'read',function['id'])
        if not policy_allows(json.loads(service['policy_json']),call.origin,call.source_ip):raise InvocationError(403,'network_policy_denied')
        self.operations.function_available(db,function['id'])
        path=declared_path(revision,call.path,call.method)
        return function,service,revision,path

    def receive(self,function_id,authorization,method,path,origin,source_ip):
        if self.closing or not self.reconciled:raise InvocationError(503,'execution_unavailable')
        call=WaitingCall(str(uuid4()),function_id,authorization,method,path,origin,source_ip,asyncio.get_running_loop().create_future())
        with self.db.transaction(busy_timeout=0) as db:
            function,service,_,_=self.check_call(db,call)
            total=db.execute("SELECT count(*) FROM invocations WHERE state IN ('receiving','queued')").fetchone()[0]
            per_function=db.execute("SELECT count(*) FROM invocations WHERE function_id=? AND state IN ('receiving','queued')",(function_id,)).fetchone()[0]
            if total>=self.settings.waiting_call_limit or per_function>=self.settings.function_waiting_call_limit:raise InvocationError(429,'queue_full')
            db.execute("INSERT INTO invocations(id,actor_kind,actor_id,service_id,function_id,state,created_at,handler_started) VALUES(?,?,?,?,?,'receiving',?,0)",
                       (call.id,authorization.actor.kind,authorization.actor.id,service['id'],function_id,time.time()))
        self.waiting[call.id]=call
        return call

    def enqueue(self,call,raw_headers,query,body):
        if self.waiting.get(call.id) is not call:raise InvocationError(503,'execution_unavailable')
        with self.db.transaction(busy_timeout=0) as db:
            function,_,_,_=self.check_call(db,call)
            timeout=json.loads(function['config_json'])['queue_timeout_seconds']
            db.execute("UPDATE invocations SET state='queued',queued_at=? WHERE id=? AND state='receiving'",(time.time(),call.id))
        call.payload=(raw_headers,query,body);call.deadline=time.monotonic()+timeout
        # Zero allows exactly this immediate admission attempt, including a cold start.
        self.attempt(call)
        self.wake.set()

    def write_terminal(self,db,identifier,state,code,status,*,result=None):
        result=result or {}
        db.execute('UPDATE invocations SET state=?,error_code=?,http_status=?,completed_at=?,handler_started=coalesce(?,handler_started),logs=?,logs_truncated=? WHERE id=?',
            (state,code,status,time.time(),result.get('handler_started'),result.get('logs',''),int(result.get('logs_truncated',False)),identifier))

    def terminal(self,identifier,state,code,status,*,result=None):
        with self.db.transaction(busy_timeout=0) as db:self.write_terminal(db,identifier,state,code,status,result=result)

    def reject(self,call,status,code,state='rejected'):
        first_rejection=call.rejection is None
        call.rejection=(status,code,state)
        try:self.terminal(call.id,state,code,status)
        except sqlite3.Error:
            if first_rejection:logger.warning(json.dumps({'event':'execution.rejection_pending','invocation_id':call.id,'state':state,'error_code':code,'http_status':status}))
            raise
        self.waiting.pop(call.id,None);call.payload=None
        if not call.future.done():call.future.set_result({'error':code,'http_status':status,'invocation_id':call.id})

    def disconnect(self,call):
        if not call.admitted and self.waiting.get(call.id) is call:self.reject(call,499,'client_disconnected','disconnected')

    def capacity(self,db,config):
        cpu,memory,count=db.execute('SELECT coalesce(sum(cpu_nanos),0),coalesce(sum(memory_mib),0),count(*) FROM execution_instances').fetchone()
        return (cpu+math.ceil(config['cpu']*1000000000)<=self.settings.function_cpu_nanos and
                memory+config['memory_mib']<=self.settings.function_memory_mib and count<self.settings.function_instance_limit)

    def reserve(self,db,snapshot,generation):
        identifier=str(uuid4());config=snapshot['config'];now=time.time()
        db.execute("INSERT INTO execution_instances VALUES(?,?,?,?,?,?,'starting',?,?,NULL,?,NULL)",
            (identifier,snapshot['function_id'],snapshot['revision_id'],generation,math.ceil(config['cpu']*1000000000),config['memory_mib'],self.vault.seal(snapshot),now,now))
        return identifier

    def attempt(self,call):
        if call.payload is None or call.admitted or self.closing:return
        try:
            with self.db.transaction(busy_timeout=0) as db:
                function,service,revision,path=self.check_call(db,call)
                if call.attempted and time.monotonic()>=call.deadline:raise InvocationError(429,'queue_timeout')
                call.attempted=True
                # Receiving and queued calls of the same function retain arrival order.
                first=db.execute("SELECT id FROM invocations WHERE function_id=? AND state IN ('receiving','queued') ORDER BY created_at,id LIMIT 1",(function['id'],)).fetchone()
                active=db.execute("SELECT count(*) FROM invocations WHERE function_id=? AND state IN ('admitted','running')",(function['id'],)).fetchone()[0]
                snapshot,generation=self.snapshot(function,service,revision);config=snapshot['config']
                rows=db.execute('SELECT * FROM execution_instances WHERE function_id=?',(function['id'],)).fetchall()
                exclusive=any(self.vault.open(row['snapshot_cipher'])['config']['storage']['data']['enabled'] and
                    self.vault.open(row['snapshot_cipher'])['config']['storage']['concurrency']=='exclusive' for row in rows if row['state']=='busy')
                unavailable=(first['id']!=call.id or active>=config['concurrency'] or (active and (exclusive or
                    (config['storage']['data']['enabled'] and config['storage']['concurrency']=='exclusive'))))
                ready=next((row for row in rows if row['state']=='ready' and row['generation']==generation and row['id'] in self.instances and row['id'] not in self.workers and row['id'] not in self.retiring),None)
                if unavailable or (ready is None and (len(rows)>=config['max_instances'] or not self.capacity(db,config))):
                    if time.monotonic()>=call.deadline:raise InvocationError(429,'queue_timeout')
                    return
                identifier=ready['id'] if ready else self.reserve(db,snapshot,generation)
                db.execute("UPDATE execution_instances SET state='busy',last_used_at=? WHERE id=?",(time.time(),identifier))
                db.execute("UPDATE invocations SET state='admitted',revision_id=?,instance_id=?,admitted_at=? WHERE id=?",(revision['id'],identifier,time.time(),call.id))
            call.admitted=True;self.waiting.pop(call.id,None)
            payload=call.payload;call.payload=None
            event=event_envelope(call.method,path,*payload,call.source_ip,call.id)
            self.launch(identifier,self.run_call(identifier,snapshot,call,event))
        except HTTPException as error:
            code=error.detail if isinstance(error,InvocationError) else {401:'invalid_token',403:'forbidden',409:'function_busy',422:'invalid_configuration'}.get(error.status_code,'function_unavailable')
            self.reject(call,error.status_code,code)

    def launch(self,identifier,coroutine):
        task=asyncio.create_task(coroutine);self.workers[identifier]=task
        def finished(done):
            if self.workers.get(identifier) is done:self.workers.pop(identifier,None)
            if not done.cancelled() and done.exception():
                self.maintenance_error=True;logger.error(json.dumps({'event':'execution.owner_failed','instance_id':identifier,'error_type':type(done.exception()).__name__}))
            self.wake.set()
        task.add_done_callback(finished)

    def schedule_retirement(self,identifier):
        with self.db.transaction(busy_timeout=0) as db:db.execute("UPDATE execution_instances SET state='draining' WHERE id=?",(identifier,))
        self.launch(identifier,self.retire(identifier))

    def handler_started(self,invocation):
        try:
            with self.db.transaction(busy_timeout=0) as db:
                if db.execute("UPDATE invocations SET handler_started=1 WHERE id=? AND state='running'",(invocation,)).rowcount!=1:raise ValidationError('observation_unavailable')
        except sqlite3.Error:raise ValidationError('observation_unavailable') from None

    def driver(self,identifier,snapshot):
        if identifier in self.instances:return self.instances[identifier]
        work=self.root/identifier;work.mkdir(mode=0o700)
        config=snapshot['config']
        instance=ManagedInstance(instance_id=identifier,started_callback=self.handler_started,docker_socket='/docker.sock',image=snapshot['image'],
            code=self.settings.host_state_dir/'artifacts'/snapshot['revision_id']/'code',work=work,host_work=self.settings.host_state_dir/'execution'/identifier,
            installation=self.installation,function_id=snapshot['function_id'],revision_id=snapshot['revision_id'],handler=config['handler'],
            function_name=snapshot['name'],environment=snapshot['environment'],secrets=snapshot['secrets'],memory_mib=config['memory_mib'],cpu=config['cpu'],
            storage=self.operations.storage,storage_configuration=storage_configuration(config))
        self.instances[identifier]=instance
        return instance

    async def run_call(self,identifier,snapshot,call,event):
        instance=None;result=None
        try:
            instance=self.driver(identifier,snapshot)
            if not instance.managed_started:await instance.start()
            with self.db.transaction(busy_timeout=0) as db:
                db.execute('UPDATE execution_instances SET ready_at=coalesce(ready_at,?) WHERE id=?',(time.time(),identifier))
                db.execute("UPDATE invocations SET state='running',dispatched_at=?,handler_started=NULL WHERE id=?",(time.time(),call.id))
            result=await instance.invoke(event,snapshot['config']['timeout_seconds'],call.id)
            status=result['response']['statusCode'] if result['state']=='succeeded' else 504 if result['error']=='invocation_timeout' else 502 if result['error'] in ('handler_error','handler_exited','invalid_handler_response') else 503
            result['http_status']=status
        except asyncio.CancelledError:
            result={'state':'interrupted','error':'control_interrupted','http_status':503,'invocation_id':call.id}
        except Exception as error:
            result={'state':'failed','error':'runtime_unavailable','http_status':503,'invocation_id':call.id}
            logger.error(json.dumps({'event':'execution.failed','invocation_id':call.id,'error_type':type(error).__name__}))
        finally:
            result=result or {'state':'failed','error':'execution_unavailable','http_status':503,'invocation_id':call.id}
            self.finalizing[call.id]=identifier
            await joined(self.finish_call(identifier,call,result))

    async def finish_call(self,identifier,call,result):
        # The owner stays alive until history and the instance disposition agree.
        force_close=not result.get('instance_available');reported=False
        while True:
            try:
                retire=force_close or self.closing
                removed=await self.retire(identifier) if retire else False
                with self.db.transaction(busy_timeout=0) as db:
                    self.write_terminal(db,call.id,result['state'],result.get('error'),result['http_status'],result=result)
                    if not retire:db.execute("UPDATE execution_instances SET state='ready',last_used_at=? WHERE id=?",(time.time(),identifier))
                    elif not removed:db.execute("UPDATE execution_instances SET state='cleanup_failed',error_code='cleanup_failed' WHERE id=?",(identifier,))
                self.finalizing.pop(call.id,None)
                if not call.future.done():call.future.set_result(result)
                return
            except sqlite3.Error:
                if not reported:
                    logger.error(json.dumps({'event':'execution.finalization_pending','invocation_id':call.id,'result_state':result['state']}))
                    reported=True
                force_close=True
                if self.closing:
                    # Dispose still attempts Docker and lease cleanup when SQL writes fail.
                    await self.retire(identifier)
                    if not call.future.done():call.future.set_result({'error':'control_interrupted','http_status':503,'invocation_id':call.id})
                    return
                await asyncio.sleep(.5)

    async def warm(self,identifier,snapshot):
        try:
            instance=self.driver(identifier,snapshot);await instance.start()
            with self.db.transaction(busy_timeout=0) as db:db.execute("UPDATE execution_instances SET state='ready',ready_at=?,last_used_at=? WHERE id=?",(time.time(),time.time(),identifier))
        except BaseException:
            self.retry_at[snapshot['function_id']]=time.monotonic()+5
            await joined(self.retire(identifier));raise

    async def retire(self,identifier):
        task=self.retiring.get(identifier)
        if task is None or task.done():
            task=asyncio.create_task(self.dispose(identifier));self.retiring[identifier]=task
        try:return await joined(task)
        finally:
            if task.done() and self.retiring.get(identifier) is task:self.retiring.pop(identifier,None)

    async def dispose(self,identifier):
        try:
            with suppress(sqlite3.Error):
                with self.db.transaction(busy_timeout=0) as db:db.execute("UPDATE execution_instances SET state='draining' WHERE id=?",(identifier,))
            instance=self.instances.get(identifier)
            if instance and not await instance.close():raise ValidationError('cleanup_failed')
            # A constructor failure may leave an empty owned channel directory but no lease.
            if not instance:
                if any(item['consumer_id']==identifier for item in await self.operations.storage.leases(self.installation)):
                    raise ValidationError('cleanup_failed')
            await joined(asyncio.to_thread(self.deployments.remove,self.root,identifier))
            with self.db.transaction(busy_timeout=0) as db:db.execute('DELETE FROM execution_instances WHERE id=?',(identifier,))
            self.instances.pop(identifier,None);return True
        except (OSError,ArtifactError,ValidationError,StorageError,sqlite3.Error):
            with suppress(sqlite3.Error):
                with self.db.transaction(busy_timeout=0) as db:db.execute("UPDATE execution_instances SET state='cleanup_failed',error_code='cleanup_failed' WHERE id=?",(identifier,))
            return False

    async def reconcile_orphan(self,identifier):
        # A task failure never makes its durable busy reservation reusable.
        while True:
            removed=await self.retire(identifier)
            try:
                with self.db.transaction(busy_timeout=0) as db:
                    db.execute("UPDATE invocations SET state='interrupted',error_code='execution_owner_lost',http_status=503,completed_at=? WHERE instance_id=? AND state IN ('admitted','running')",(time.time(),identifier))
                    if not removed:db.execute("UPDATE execution_instances SET state='cleanup_failed',error_code='cleanup_failed' WHERE id=?",(identifier,))
                return
            except sqlite3.Error:
                if self.closing:return
                await asyncio.sleep(.5)

    async def drain(self,function_id):
        with self.db.transaction(busy_timeout=0) as db:
            if db.execute("SELECT 1 FROM invocations WHERE function_id=? AND state IN ('admitted','running')",(function_id,)).fetchone():
                raise InvocationError(409,'function_busy')
            identifiers=[row['id'] for row in db.execute('SELECT id FROM execution_instances WHERE function_id=?',(function_id,))]
            db.execute("UPDATE execution_instances SET state='draining' WHERE function_id=?",(function_id,))
        for identifier in identifiers:
            task=self.workers.get(identifier)
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):await joined(task)
            if not await self.retire(identifier):raise InvocationError(503,'cleanup_failed')

    def remove_owned_docker(self):
        docker=Docker('/docker.sock');installation={'tech.p2enjoy.serverless.installation':self.installation}
        for kind,collection in [('instance','containers'),('instance-network','networks')]:
            labels={**installation,'tech.p2enjoy.serverless.kind':kind}
            query=urlencode({'all':'1','filters':json.dumps({'label':[k+'='+v for k,v in labels.items()]})})
            for item in docker.call('GET','/'+collection+('/json' if collection=='containers' else '')+'?'+query,max_bytes=4*1024**2):
                target='/'+collection+'/'+item['Id'];inspect=target+('/json' if collection=='containers' else '')
                row=docker.call('GET',inspect,allowed=(200,404))
                if not row or not row.get('Id'):continue
                actual=row.get('Config',{}).get('Labels',{}) if collection=='containers' else row.get('Labels',{})
                if any(actual.get(k)!=v for k,v in labels.items()):raise ValidationError('cleanup_ownership')
                for key in ('function','revision','instance'):
                    value=actual.get('tech.p2enjoy.serverless.'+key)
                    if str(UUID(value))!=value:raise ValidationError('cleanup_ownership')
                docker.call('DELETE',target+('?force=1&v=1' if collection=='containers' else ''),timeout=10,allowed=(204,404))
                docker.call('GET',inspect,allowed=(404,))

    async def recover(self):
        self.reconciled=False
        # @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
        if self.operations.discards:self.operations.discards.execution_reconciled=False
        try:
            await joined(asyncio.to_thread(self.remove_owned_docker))
            for lease in await self.operations.storage.leases(self.installation):
                await self.operations.storage.release_confirmed(lease['function_id'],lease['consumer_id'],self.installation)
            for path in self.root.iterdir():
                if str(UUID(path.name))!=path.name:raise ValidationError('cleanup_ownership')
                await joined(asyncio.to_thread(self.deployments.remove,self.root,path.name))
            with self.db.transaction(busy_timeout=0) as db:
                db.execute('DELETE FROM execution_instances')
                db.execute("UPDATE invocations SET state='interrupted',error_code='control_interrupted',http_status=503,completed_at=? WHERE state IN ('receiving','queued','admitted','running')",(time.time(),))
            if self.operations.discards:self.operations.discards.execution_reconciled=True
            await self.operations.sweep()
            self.reconciled=not self.operations.cleanup_error and self.operations.agent_ready
        except Exception as error:
            logger.error(json.dumps({'event':'execution.recovery_failed','error_type':type(error).__name__}))

    async def ready(self,installation):
        self.installation=installation;self.started=True;self.root.mkdir(mode=0o700,exist_ok=True)
        with self.db.transaction(busy_timeout=0) as db:self.minimum_budget(db)
        await self.recover()
        self.task=asyncio.create_task(self.maintain())

    async def tick(self):
        # Retire stale generations and excess idle instances before filling minima.
        current={}
        with self.db.transaction(busy_timeout=0) as db:
            for function in db.execute('SELECT id FROM functions WHERE deleted_at IS NULL AND active_revision_id IS NOT NULL').fetchall():
                try:
                    fn,service,revision=self.current(db,function['id']);snapshot,generation=self.snapshot(fn,service,revision)
                    self.operations.function_available(db,fn['id']);current[fn['id']]=(snapshot,generation)
                except HTTPException:continue
        counts={}
        for row in self.db.all('SELECT * FROM execution_instances ORDER BY last_used_at DESC,id'):
            if row['id'] in self.workers or row['id'] in self.retiring:continue
            if row['state'] in ('starting','busy'):
                self.launch(row['id'],self.reconcile_orphan(row['id']));continue
            target=current.get(row['function_id']);counts[row['function_id']]=counts.get(row['function_id'],0)+1
            stale=not target or target[1]!=row['generation']
            excess=target and counts[row['function_id']]>target[0]['config']['min_instances']
            idle=target and time.time()-row['last_used_at']>=target[0]['config']['idle_seconds']
            over_max=target and counts[row['function_id']]>target[0]['config']['max_instances']
            if row['state'] in ('cleanup_failed','draining') or (row['state']=='ready' and (stale or over_max or (excess and idle))):
                self.schedule_retirement(row['id'])
        # Admission never awaits a Docker operation; each accepted call owns its task.
        for call in tuple(self.waiting.values()):
            if call.rejection:self.reject(call,*call.rejection)
            else:self.attempt(call)
        for function_id,(snapshot,generation) in current.items():
            if self.retry_at.get(function_id,0)>time.monotonic():continue
            with self.db.transaction(busy_timeout=0) as db:
                rows=db.execute('SELECT state,generation FROM execution_instances WHERE function_id=?',(function_id,)).fetchall()
                config=snapshot['config']
                present=sum(row['generation']==generation and row['state'] in ('starting','ready','busy') for row in rows)
                if present>=config['min_instances'] or len(rows)>=config['max_instances'] or not self.capacity(db,config):continue
                identifier=self.reserve(db,snapshot,generation)
            self.launch(identifier,self.warm(identifier,snapshot))
        # Reclaim the oldest ready excess under real queue/minimum pressure.
        pressure=any(call.payload is not None for call in self.waiting.values()) or any(
            self.db.one("SELECT count(*) AS n FROM execution_instances WHERE function_id=? AND generation=? AND state IN ('starting','ready','busy')",(key,generation))['n']<snapshot['config']['min_instances'] for key,(snapshot,generation) in current.items())
        if pressure:
            for row in self.db.all("SELECT * FROM execution_instances WHERE state='ready' ORDER BY last_used_at,id"):
                if row['id'] in self.workers or row['id'] in self.retiring:continue
                target=current.get(row['function_id']);minimum=target[0]['config']['min_instances'] if target else 0
                count=self.db.one("SELECT count(*) AS n FROM execution_instances WHERE function_id=? AND state IN ('ready','busy','starting')",(row['function_id'],))['n']
                if count>minimum:self.schedule_retirement(row['id']);break
        with self.db.transaction(busy_timeout=0) as db:
            db.execute('DELETE FROM invocations WHERE completed_at IS NOT NULL AND completed_at<?',(time.time()-7*86400,))
            db.execute('DELETE FROM invocations WHERE id IN (SELECT id FROM invocations WHERE completed_at IS NOT NULL ORDER BY completed_at DESC,id DESC LIMIT -1 OFFSET 10000)')

    async def maintain(self):
        while not self.closing:
            try:
                if not self.reconciled:await self.recover()
                else:await self.tick()
                self.maintenance_error=False
            except Exception as error:
                self.maintenance_error=True
                logger.error(json.dumps({'event':'execution.maintenance_failed','error_type':type(error).__name__}))
            self.wake.clear()
            with suppress(TimeoutError):await asyncio.wait_for(self.wake.wait(),.1 if self.reconciled else 5)

    async def close(self):
        self.closing=True;self.wake.set()
        if not self.started:return
        if self.shutdown_task is None:self.shutdown_task=asyncio.create_task(self.shutdown())
        await joined(self.shutdown_task)

    async def shutdown(self):
        failures=[]
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):await joined(self.task)
        for call in tuple(self.waiting.values()):
            try:self.reject(call,503,'control_interrupted','interrupted')
            except Exception as error:
                failures.append(type(error).__name__)
                if not call.future.done():call.future.set_result({'error':'control_interrupted','http_status':503,'invocation_id':call.id})
        tasks=tuple(self.workers.values())
        for task in tasks:task.cancel()
        if tasks:
            results=await asyncio.gather(*tasks,return_exceptions=True)
            failures.extend(type(result).__name__ for result in results if isinstance(result,Exception))
        identifiers=set(self.instances)
        try:identifiers.update(row['id'] for row in self.db.all('SELECT id FROM execution_instances'))
        except sqlite3.Error:failures.append('database_unavailable')
        for identifier in identifiers:
            try:
                if not await self.retire(identifier):failures.append('cleanup_pending')
            except Exception as error:failures.append(type(error).__name__)
        if failures or self.finalizing:
            logger.error(json.dumps({'event':'execution.shutdown_pending','failures':failures,'pending_finalizations':len(self.finalizing)}))

    def healthy(self):
        if not self.reconciled or self.maintenance_error or self.finalizing or any(call.rejection for call in self.waiting.values()):return False
        return not any(row['state']=='cleanup_failed' or (row['state'] in ('starting','busy') and row['id'] not in self.workers)
            for row in self.db.all('SELECT id,state FROM execution_instances'))
