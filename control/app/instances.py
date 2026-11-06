# @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#instance-et-processus
"""Production Docker instance lifecycle, shared by admission and operator diagnostics."""
import argparse
import asyncio
import base64
from contextlib import suppress
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets as random_secrets
import shutil
import signal
import sys
import tempfile
import time
from urllib.parse import urlencode
from uuid import UUID,uuid4

from .validator import Docker,ERRORS,ValidationError,application_environment,redact_logs,request

PROTOCOL_LIMIT=10*1024**2
BODY_LIMIT=6*1024**2
HEADER_NAME=re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+")
WITHHELD={'connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer',
          'transfer-encoding','upgrade','content-length','host','x-serverless-request-id'}
INVOCATION_ERRORS=ERRORS|{'handler_error','invalid_handler_response','handler_exited','child_start_failed'}


async def joined(awaitable):
    task=asyncio.ensure_future(awaitable);cancelled=False
    while not task.done():
        try:await asyncio.shield(task)
        except asyncio.CancelledError:cancelled=True
    result=task.result()
    if cancelled:raise asyncio.CancelledError
    return result


def response(data):
    if not isinstance(data,dict) or set(data)!={'statusCode','bodyBase64','isBase64Encoded','headers'}:
        raise ValidationError('invalid_handler_response')
    if type(data['statusCode']) is not int or not 200<=data['statusCode']<=599 or type(data['isBase64Encoded']) is not bool or not isinstance(data['bodyBase64'],str):
        raise ValidationError('invalid_handler_response')
    try:
        if len(data['bodyBase64'])>BODY_LIMIT*4//3:raise ValueError
        raw=base64.b64decode(data['bodyBase64'],validate=True)
        if base64.b64encode(raw).decode()!=data['bodyBase64']:raise ValueError
        body=data['bodyBase64'] if data['isBase64Encoded'] else raw.decode('utf8')
    except (ValueError,UnicodeError):raise ValidationError('invalid_handler_response') from None
    if len(raw)>BODY_LIMIT:raise ValidationError('invalid_handler_response')
    if not isinstance(data['headers'],list) or len(data['headers'])>128:raise ValidationError('invalid_handler_response')
    headers=[];size=0;connection_fields=set()
    for pair in data['headers']:
        if not isinstance(pair,list) or len(pair)!=2 or not all(isinstance(value,str) for value in pair):raise ValidationError('invalid_handler_response')
        name,value=pair
        if not HEADER_NAME.fullmatch(name) or len(name)>256 or any(ord(c)<32 or ord(c)==127 or ord(c)>255 for c in value):raise ValidationError('invalid_handler_response')
        size+=len(name.encode())+len(value.encode())
        if size>32768:raise ValidationError('invalid_handler_response')
        name=name.lower()
        if name=='connection':
            for token in value.split(','):
                token=token.strip().lower()
                if not HEADER_NAME.fullmatch(token):raise ValidationError('invalid_handler_response')
                connection_fields.add(token)
        if name not in WITHHELD and not name.startswith('access-control-'):headers.append([name,value])
    return {'statusCode':data['statusCode'],'body':body,'isBase64Encoded':data['isBase64Encoded'],
            'headers':[pair for pair in headers if pair[0] not in connection_fields]}


class Instance:
    def __init__(self,*,docker_socket,image,code,work,installation,function_id,revision_id,
                 handler,function_name,environment,secrets,memory_mib=256,cpu=.25,host_work=None,mounts=None,network='bridge'):
        self.id=str(uuid4());self.installation=str(UUID(installation));self.function_id=str(UUID(function_id));self.revision_id=str(UUID(revision_id))
        if type(memory_mib) is not int or not 128<=memory_mib<=8192:raise ValidationError('invalid_memory')
        if isinstance(cpu,bool) or not isinstance(cpu,(int,float)) or not math.isfinite(cpu) or not .05<=cpu<=1:raise ValidationError('invalid_cpu')
        if not isinstance(handler,str) or len(handler)>256 or not isinstance(function_name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,62}',function_name):
            raise ValidationError('invalid_function')
        self.environment=application_environment(environment,secrets);self.secrets=dict(secrets)
        if len(json.dumps({'handler':handler,'environment':self.environment}).encode())>256*1024:raise ValidationError('configuration_limit')
        self.handler,self.function_name,self.memory_mib,self.cpu=handler,function_name,memory_mib,cpu
        self.code=Path(code);self.work=Path(work);self.host_work=Path(host_work) if host_work else self.work.resolve()
        if any(not path.is_absolute() or '..' in path.parts for path in (self.code,self.host_work)):raise ValidationError('invalid_host_path')
        if network not in ('none','bridge'):raise ValidationError('invalid_network')
        self.network_mode=network;self.mounts=mounts or {}
        if set(self.mounts)-{'/data','/cache'}:raise ValidationError('invalid_mount')
        for path in self.mounts.values():
            if not isinstance(path,str) or not Path(path).is_absolute() or '..' in Path(path).parts:raise ValidationError('invalid_mount')
        self.docker=Docker(docker_socket);self.image=image
        self.labels={'tech.p2enjoy.serverless.installation':self.installation,'tech.p2enjoy.serverless.kind':'instance',
                     'tech.p2enjoy.serverless.function':self.function_id,'tech.p2enjoy.serverless.revision':self.revision_id,
                     'tech.p2enjoy.serverless.instance':self.id}
        self.name='p2-i-'+UUID(self.id).hex;self.container=None;self.network=None;self.channel=None;self.server=None
        self.key=random_secrets.token_urlsafe(32);self.bootstrapped=False;self.ready=asyncio.Event();self.wake=asyncio.Event()
        self.job=None;self.future=None;self.claimed=False;self.started_observed=False;self.connections=set();self.baseline=set()
        self.busy=False;self.closing=False;self.removed=False;self.cleanup_error=False;self._close_task=None;self.lifecycle_lock=asyncio.Lock()

    async def call(self,method,path,body=None,**kwargs):
        return await joined(asyncio.to_thread(self.docker.call,method,path,body,**kwargs))

    async def exchange(self,reader,writer):
        task=asyncio.current_task();self.connections.add(task)
        try:
            if len(self.connections)>4:return
            async with asyncio.timeout(5):
                raw=await reader.readuntil(b'\r\n\r\n')
                if len(raw)>8192:return
                lines=raw.decode('ascii').split('\r\n');method,path,version=lines[0].split(' ')
                if version not in ('HTTP/1.0','HTTP/1.1'):return
                headers={}
                for line in lines[1:]:
                    if not line:continue
                    key,value=line.split(':',1);key=key.strip().lower()
                    if key in headers:return
                    headers[key]=value.strip()
                length=headers.get('content-length','0')
                if 'transfer-encoding' in headers or not re.fullmatch(r'[0-9]{1,8}',length) or int(length)>PROTOCOL_LIMIT:return
                status=404;answer={'error':'not_found'}
                if self.closing:status=410;answer={'error':'closing'}
                elif path=='/bootstrap' and method=='POST':
                    if self.bootstrapped:status=409;answer={'error':'already_started'}
                    elif int(length)>1024 or headers.get('content-type')!='application/json':status=400;answer={'error':'invalid_bootstrap'}
                    else:
                        data=json.loads(await reader.readexactly(int(length)))
                        clock=data.get('monotonic_ns') if isinstance(data,dict) else None
                        if not isinstance(clock,str) or not re.fullmatch(r'[0-9]{1,20}',clock) or abs(time.monotonic_ns()-int(clock))>1000000000:
                            status=422;answer={'error':'clock_mismatch'}
                        else:self.bootstrapped=True;status=200;answer={'key':self.key,'mounts':list(self.mounts)}
                elif not self.bootstrapped or not hmac.compare_digest(headers.get('x-instance-key',''),self.key):
                    status=403;answer={'error':'forbidden'}
                elif method=='GET' and path=='/next' and int(length)==0:
                    self.ready.set()
                    if not self.job or self.claimed:
                        with suppress(TimeoutError):await asyncio.wait_for(self.wake.wait(),1)
                        self.wake.clear()
                    if self.closing:status=410;answer={'error':'closing'}
                    elif self.job and not self.claimed:self.claimed=True;status=200;answer=self.job
                    else:status=204;answer=None
                elif method=='POST' and path=='/started':
                    if headers.get('content-type')!='application/json' or int(length)>1024:status=400;answer={'error':'invalid_start'}
                    elif not self.job or not self.claimed or not self.future or self.future.done():status=409;answer={'error':'invalid_state'}
                    else:
                        data=json.loads(await reader.readexactly(int(length)))
                        if not isinstance(data,dict) or data.get('invocation_id')!=self.job['invocation_id']:raise ValidationError('protocol_invalid')
                        self.started_observed=True;status=202;answer={'accepted':True}
                elif method=='POST' and path=='/result':
                    if headers.get('content-type')!='application/json':status=415;answer={'error':'content_type'}
                    elif not self.job or not self.claimed or not self.future or self.future.done():status=409;answer={'error':'invalid_state'}
                    else:
                        data=json.loads(await reader.readexactly(int(length)))
                        if not isinstance(data,dict) or data.get('invocation_id')!=self.job['invocation_id'] or type(data.get('handler_started')) is not bool:
                            raise ValidationError('protocol_invalid')
                        clean={'handler_started':data['handler_started'],**redact_logs(data.get('logs',''),data.get('logs_truncated'),self.secrets)}
                        if data.get('state')=='succeeded':clean.update(state='succeeded',response=response(data.get('response')))
                        elif data.get('state')=='failed' and data.get('error') in INVOCATION_ERRORS:clean.update(state='failed',error=data['error'])
                        else:raise ValidationError('protocol_invalid')
                        if time.monotonic_ns()>int(self.job['deadline_ns']):
                            self.future.set_exception(TimeoutError());status=410;answer={'error':'invocation_timeout'}
                        else:self.future.set_result(clean);status=202;answer={'accepted':True}
                body=json.dumps(answer,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode() if answer is not None else b''
                if len(body)>PROTOCOL_LIMIT:raise ValidationError('protocol_limit')
                writer.write(f'HTTP/1.1 {status} Response\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n'.encode()+body)
                await writer.drain()
        except (OSError,ValueError,TypeError,UnicodeError,ValidationError,asyncio.IncompleteReadError,asyncio.LimitOverrunError,TimeoutError):pass
        finally:
            writer.close()
            try:
                with suppress(OSError,TimeoutError):await asyncio.wait_for(writer.wait_closed(),1)
            finally:self.connections.discard(task)

    async def processes(self,timeout=5):
        data=await self.call('GET','/containers/'+self.container+'/top?'+urlencode({'ps_args':'-eo pid,ppid,comm'}),timeout=timeout)
        try:
            index=data['Titles'].index('PID');rows=data['Processes']
            if len(rows)>64:raise ValueError
            return {int(row[index]) for row in rows}
        except (KeyError,ValueError,TypeError,IndexError):raise ValidationError('process_inventory_invalid') from None

    async def start(self):
        owned=False
        try:
            async with self.lifecycle_lock:
                if self.server is not None or self.closing:raise ValidationError('instance_already_started')
                owned=True
                return await self._start()
        except BaseException:
            if owned:await self.close()
            raise

    async def _start(self):
        if self.server is not None or self.closing:raise ValidationError('instance_already_started')
        deadline=time.monotonic()+15
        def left():
            if self.closing:raise ValidationError('instance_stopped')
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ValidationError('instance_start_timeout')
            return remaining
        self.image=await joined(asyncio.to_thread(self.docker.image,self.image))
        left()
        self.channel=Path(tempfile.mkdtemp(prefix='i-',dir=self.work));protocol=self.channel/'control.sock'
        if len(os.fsencode(protocol))>100:
            self.channel.rmdir();self.channel=None;raise ValidationError('socket_path_limit')
        self.server=await asyncio.start_unix_server(self.exchange,path=str(protocol),limit=8192,backlog=8)
        os.chmod(protocol,0o600)
        if self.network_mode=='bridge':
            labels={**self.labels,'tech.p2enjoy.serverless.kind':'instance-network'}
            self.network=(await self.call('POST','/networks/create',{'Name':self.name,'Driver':'bridge','Labels':labels},timeout=min(5,left())))['Id']
        config={'Image':self.image,'User':'0:0','WorkingDir':'/runtime','Labels':self.labels,
            'Entrypoint':['node','/runtime/invoke-supervisor.mjs'],'Cmd':[],
            'HostConfig':{'NetworkMode':self.network or 'none','ReadonlyRootfs':True,'CapDrop':['ALL'],
                'SecurityOpt':['no-new-privileges:true'],'Memory':self.memory_mib*1024**2,'MemorySwap':self.memory_mib*1024**2,
                'NanoCpus':int(self.cpu*1000000000),'PidsLimit':64,'Init':True,'LogConfig':{'Type':'none'},
                'Tmpfs':{'/tmp':'rw,noexec,nosuid,size=16m,mode=1777'},
                'Mounts':[{'Type':'bind','Source':str(self.code),'Target':'/code','ReadOnly':True},
                          {'Type':'bind','Source':str(self.host_work/self.channel.name),'Target':'/protocol','ReadOnly':True}]+
                         [{'Type':'bind','Source':value,'Target':key,'ReadOnly':False} for key,value in self.mounts.items()]}}
        self.container=(await self.call('POST','/containers/create?name='+self.name,config,timeout=left()))['Id']
        await self.call('POST','/containers/'+self.container+'/start',timeout=left())
        while not self.ready.is_set():
            remaining=min(.2,left())
            with suppress(TimeoutError):await asyncio.wait_for(self.ready.wait(),remaining)
            state=(await self.call('GET','/containers/'+self.container+'/json',timeout=left()))['State']
            if not state['Running']:raise ValidationError('instance_start_failed')
        self.baseline=await self.processes(timeout=left());left()
        if not self.baseline or len(self.baseline)>3:raise ValidationError('instance_processes_invalid')
        return self

    async def stats(self):
        data=await self.call('GET','/containers/'+self.container+'/stats?stream=false',timeout=2)
        return {'memory_usage_bytes':data.get('memory_stats',{}).get('usage'),
                'memory_limit_bytes':data.get('memory_stats',{}).get('limit'),
                'cpu_usage_ns':data.get('cpu_stats',{}).get('cpu_usage',{}).get('total_usage'),
                'pids_current':data.get('pids_stats',{}).get('current')}

    async def invoke(self,event,timeout_seconds,invocation_id=None):
        if self.busy or self.closing or not self.ready.is_set():raise ValidationError('instance_unavailable')
        if isinstance(timeout_seconds,bool) or not isinstance(timeout_seconds,(int,float)) or not math.isfinite(timeout_seconds) or not .1<=timeout_seconds<=86400:
            raise ValidationError('invalid_timeout')
        if not isinstance(event,dict) or len(json.dumps(event,ensure_ascii=False,allow_nan=False).encode())>8*1024**2:raise ValidationError('event_limit')
        invocation_id=str(UUID(invocation_id)) if invocation_id else str(uuid4())
        self.busy=True;started=time.monotonic();deadline=started+timeout_seconds
        self.future=asyncio.get_running_loop().create_future();self.claimed=False;self.started_observed=False
        self.job={'invocation_id':invocation_id,'deadline_ns':str(time.monotonic_ns()+int(timeout_seconds*1000000000)),
                  'handler':self.handler,'environment':self.environment,'event':event,
                  'context':{'awsRequestId':invocation_id,'functionName':self.function_name,'functionVersion':self.revision_id,
                             'memoryLimitInMB':str(self.memory_mib)}}
        self.wake.set();result=None
        try:
            while not self.future.done():
                left=deadline-time.monotonic()
                if left<=0:raise TimeoutError
                await asyncio.wait([self.future],timeout=min(.2,left))
                if not self.future.done():
                    state=(await self.call('GET','/containers/'+self.container+'/json',timeout=min(1,max(.01,deadline-time.monotonic()))))['State']
                    if not state['Running']:
                        fatal_codes={120:'runtime_protocol_limit',121:'runtime_protocol_rejected',122:'runtime_cleanup_failed',
                                     123:'storage_mount_missing',124:'invocation_timeout',125:'runtime_protocol_timeout',126:'runtime_failure'}
                        error='memory_exceeded' if state.get('OOMKilled') else fatal_codes.get(state.get('ExitCode'),'runtime_exited')
                        raise ValidationError(error)
            result=self.future.result()
            if not self.closing and await self.processes()!=self.baseline:
                if not await self.close():raise ValidationError('cleanup_failed')
            return {**result,'invocation_id':invocation_id,'instance_id':self.id,
                    'elapsed_seconds':round(time.monotonic()-started,6),'instance_available':not self.closing}
        except (TimeoutError,OSError,ValidationError) as error:
            code='invocation_timeout' if isinstance(error,TimeoutError) else str(error) if isinstance(error,ValidationError) else 'runtime_unavailable'
            external_close=self.closing
            removed=await self.close()
            if external_close and removed and self.future.done() and not self.future.cancelled() and self.future.exception() is None:
                return {**self.future.result(),'invocation_id':invocation_id,'instance_id':self.id,
                        'elapsed_seconds':round(time.monotonic()-started,6),'instance_available':False,'container_removed':True}
            return {'state':'failed','error':code if removed else 'cleanup_failed','invocation_id':invocation_id,'instance_id':self.id,
                    'elapsed_seconds':round(time.monotonic()-started,6),'instance_available':False,
                    'handler_started':result['handler_started'] if result else True if self.started_observed else None if self.claimed else False,'logs':result.get('logs','') if result else '',
                    'logs_truncated':bool(result and result.get('logs_truncated')),'container_removed':removed}
        except BaseException:
            await self.close();raise
        finally:
            if self.future and self.future.done() and not self.future.cancelled():self.future.exception()
            self.job=None;self.future=None;self.busy=False

    async def close(self):
        self.closing=True;self.wake.set()
        if self._close_task is None or (self._close_task.done() and not self._close_task.cancelled() and self._close_task.result() is False):
            self._close_task=asyncio.create_task(self._close())
        return await joined(self._close_task)

    async def _close(self):
        async with self.lifecycle_lock:return await self._dispose()

    async def _dispose(self):
        self.closing=True;self.wake.set();removed=False
        try:
            target=self.container or self.name
            row=await self.call('GET','/containers/'+target+'/json',allowed=(200,404))
            if isinstance(row,dict) and row.get('Id'):
                labels=row.get('Config',{}).get('Labels',{})
                if any(labels.get(key)!=value for key,value in self.labels.items()):raise ValidationError('cleanup_ownership')
                await self.call('DELETE','/containers/'+target+'?force=1&v=1',timeout=10,allowed=(204,404))
            status,_=await joined(asyncio.to_thread(request,self.docker.path,'GET','/v1.45/containers/'+target+'/json'))
            if status!=404:raise ValidationError('cleanup_failed')
            if self.network_mode=='bridge':
                target=self.network or self.name
                row=await self.call('GET','/networks/'+target,allowed=(200,404))
                if isinstance(row,dict) and row.get('Id'):
                    expected={**self.labels,'tech.p2enjoy.serverless.kind':'instance-network'}
                    if any(row.get('Labels',{}).get(key)!=value for key,value in expected.items()):raise ValidationError('cleanup_ownership')
                    await self.call('DELETE','/networks/'+target,allowed=(204,404))
                status,_=await joined(asyncio.to_thread(request,self.docker.path,'GET','/v1.45/networks/'+target))
                if status!=404:raise ValidationError('cleanup_failed')
            removed=True
        except (OSError,ValidationError):self.cleanup_error=True
        finally:
            if self.server:self.server.close()
            for task in tuple(self.connections):task.cancel()
            if self.connections:await asyncio.gather(*tuple(self.connections),return_exceptions=True)
            if self.server:await self.server.wait_closed()
            if removed and self.channel:
                try:await joined(asyncio.to_thread(shutil.rmtree,self.channel))
                except FileNotFoundError:pass
                except OSError:removed=False
            if self.future and not self.future.done():self.future.set_result({'state':'failed','error':'instance_stopped','handler_started':True if self.started_observed else None if self.claimed else False,'logs':'','logs_truncated':False})
        self.removed=removed;self.cleanup_error=not removed
        return removed


async def diagnose(args):
    # This entry point requires the real Docker operator socket, not a public identity.
    loop=asyncio.get_running_loop();owner=asyncio.current_task()
    for signum in (signal.SIGTERM,signal.SIGINT):loop.add_signal_handler(signum,owner.cancel)
    reader=asyncio.StreamReader(limit=PROTOCOL_LIMIT+1)
    transport,_=await loop.connect_read_pipe(lambda:asyncio.StreamReaderProtocol(reader),sys.stdin.buffer)
    instance=None;output=sys.stdout.fileno();was_blocking=os.get_blocking(output);os.set_blocking(output,False)
    async def emit(value):
        payload=memoryview((json.dumps(value,ensure_ascii=False)+'\n').encode())
        async with asyncio.timeout(10):
            while payload:
                try:payload=payload[os.write(output,payload):]
                except BlockingIOError:
                    writable=loop.create_future()
                    def ready():
                        if not writable.done():writable.set_result(None)
                    loop.add_writer(output,ready)
                    try:await writable
                    finally:loop.remove_writer(output)
    async def read():
        line=await reader.readline()
        if not line:return None
        if len(line)>PROTOCOL_LIMIT:raise ValidationError('diagnostic_limit')
        value=json.loads(line)
        if not isinstance(value,dict):raise ValidationError('invalid_command')
        return value
    try:
        data=await read()
        if data is None or set(data)-{'environment','secrets','mounts'}:raise ValidationError('invalid_configuration')
        instance=Instance(docker_socket=args.docker_socket,image=args.image,code=args.code,work=args.work,host_work=args.host_work,
            installation=args.installation,function_id=args.function_id,revision_id=args.revision_id,handler=args.handler,
            function_name=args.function_name,environment=data.get('environment',{}),secrets=data.get('secrets',{}),
            memory_mib=args.memory_mib,cpu=args.cpu,mounts=data.get('mounts'),network=args.network)
        await instance.start()
        await emit({'ready':True,'instance_id':instance.id,'container_id':instance.container,'network_id':instance.network,
                    'baseline_pids':sorted(instance.baseline),'channel':str(instance.channel)})
        while True:
            command=await read()
            if command is None or command.get('operation')=='close':break
            if command.get('operation')=='stats':answer=await instance.stats()
            elif command.get('operation')=='invoke':answer=await instance.invoke(command['event'],command.get('timeout_seconds',5))
            else:raise ValidationError('invalid_operation')
            await emit(answer)
    except asyncio.CancelledError:pass
    finally:
        transport.close()
        if instance:
            # Further signals cancel this await but joined waits for the shared cleanup task.
            try:removed=await instance.close()
            except asyncio.CancelledError:removed=instance.removed
            await emit({'closed':removed})
            if not removed:raise ValidationError('cleanup_failed')
        os.set_blocking(output,was_blocking)
        for signum in (signal.SIGTERM,signal.SIGINT):loop.remove_signal_handler(signum)


def main():
    parser=argparse.ArgumentParser(description='Diagnostic d’une véritable instance Docker DEV')
    for name in ('image','code','work','installation','function-id','revision-id','handler','function-name'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--host-work');parser.add_argument('--docker-socket',default='/run/user/1001/docker.sock')
    parser.add_argument('--memory-mib',type=int,default=256);parser.add_argument('--cpu',type=float,default=.25)
    parser.add_argument('--network',choices=('bridge','none'),default='bridge')
    args=parser.parse_args()
    try:asyncio.run(diagnose(args))
    except (BrokenPipeError,TimeoutError):return 1
    except (ValidationError,OSError,ValueError,TypeError,KeyError) as error:
        print(json.dumps({'error':str(error) if isinstance(error,ValidationError) else 'instance_unavailable'}),flush=True);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
