# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
# @spec docs/BACKLOG.md#sls-076 | docs/DEPLOYMENT_NAMES.md#conteneurs-de-validation | docs/VALIDATOR_NAMES.md
"""Real Docker/Unix-HTTP validation; no daemon SDK, shell or business env inheritance."""
import argparse
import asyncio
import base64
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import tempfile
import time
from uuid import UUID,uuid4

LIMIT=256*1024
ERRORS={'invalid_handler','module_unreadable','module_link','module_not_file',
        'module_missing','module_ambiguous','dependency_missing','import_failed','import_invalid_namespace',
        'handler_not_callable','loader_start_failed','loader_exited'}


class ValidationError(Exception):
    pass


class UnixHTTP(http.client.HTTPConnection):
    def __init__(self,path,timeout):
        super().__init__('localhost',timeout=timeout)
        self.socket_path=str(path)

    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:self.sock.connect(self.socket_path)
        except BaseException:
            self.sock.close();self.sock=None
            raise


def request(path,method,target,body=None,timeout=5,max_bytes=LIMIT):
    connection=UnixHTTP(path,max(.01,timeout))
    try:
        data=json.dumps(body,separators=(',',':')).encode() if body is not None else None
        connection.request(method,target,body=data,headers={'Content-Type':'application/json','Connection':'close'})
        response=connection.getresponse()
        payload=response.read(max_bytes+1)
        if len(payload)>max_bytes:raise ValidationError('protocol_limit')
        return response.status,json.loads(payload) if payload else None
    except (ValueError,UnicodeError,http.client.HTTPException):
        raise ValidationError('protocol_invalid') from None
    finally:connection.close()


class Docker:
    def __init__(self,path):self.path=path

    def call(self,method,path,body=None,timeout=5,allowed=(200,201,204),max_bytes=LIMIT):
        status,data=request(self.path,method,'/v1.45'+path,body,timeout,max_bytes)
        if status not in allowed:raise ValidationError('docker_http_'+str(status))
        return data

    def image(self,image):
        if not re.fullmatch(r'sha256:[0-9a-f]{64}',image):raise ValidationError('image_id_required')
        data=self.call('GET','/images/'+image+'/json')
        if data['Architecture']!='amd64' or data['Os']!='linux':raise ValidationError('image_architecture')
        return data['Id']


def application_environment(environment,secrets):
    if not isinstance(environment,dict) or not isinstance(secrets,dict):raise ValidationError('invalid_configuration')
    if len(environment)>128 or len(secrets)>128 or environment.keys()&secrets.keys():raise ValidationError('invalid_configuration')
    combined=environment|secrets
    for key,value in combined.items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}',key) or not isinstance(value,str) or '\0' in value or len(value.encode())>16384:
            raise ValidationError('invalid_configuration')
    return combined


# @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#événement-réponse-et-journaux
# Shared byte-level redaction for validation and invocation records.
def redact_logs(encoded,truncated,secrets):
    try:logs=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError):raise ValidationError('protocol_invalid') from None
    if len(logs)>65536:raise ValidationError('protocol_limit')
    values=sorted({value.encode() for value in secrets.values() if value},key=len,reverse=True)
    # Preserve raw positions while masking. NUL is forbidden in secret values.
    for value in values:logs=logs.replace(value,b'\0'*len(value))
    if truncated and values:
        # Remove any incomplete suffix using the original byte offsets, before expanding markers.
        logs=logs[:max(0,len(logs)-max(map(len,values))+1)]
    logs=re.sub(b'\0+',b'[redacted]',logs)
    logs=logs.decode('utf8',errors='replace').encode('utf8')
    expanded=len(logs)>65536
    logs=logs[:65536]
    # This buffer is already valid UTF-8; only its last truncated code point may be incomplete.
    return {'logs':logs.decode('utf8',errors='ignore'),
            'logs_truncated':bool(truncated) or expanded}


def safe_result(data,secrets):
    if not isinstance(data,dict) or data.get('state')!='done' or type(data.get('valid')) is not bool:
        raise ValidationError('protocol_invalid')
    result={'valid':data['valid'],**redact_logs(data.get('logs',''),data.get('logs_truncated'),secrets)}
    if data['valid']:
        module=data.get('module')
        if not isinstance(module,str) or not re.fullmatch(r'[A-Za-z0-9_./-]+\.(?:js|cjs|mjs)',module):
            raise ValidationError('protocol_invalid')
        result['module']=module
    else:
        code=data.get('error')
        if not isinstance(code,str):raise ValidationError('protocol_invalid')
        result['error']=code if code in ERRORS else 'import_failed'
    return result


async def validate_async(*,docker_socket,image,code,work,handler,environment,secrets,installation,host_work=None):
    """code is a daemon-host path; work is local, host_work its explicit host mapping."""
    installation=str(UUID(str(installation)))
    if not isinstance(handler,str) or len(handler)>256:raise ValidationError('invalid_handler')
    payload={'handler':handler,'environment':application_environment(environment,secrets)}
    if len(json.dumps(payload).encode())>LIMIT:raise ValidationError('configuration_limit')
    code=Path(code)
    if not code.is_absolute() or '..' in code.parts:raise ValidationError('invalid_code_path')
    work=Path(work)
    if not work.is_dir():raise ValidationError('work_missing')
    host_work=Path(host_work) if host_work else work.resolve()
    if not host_work.is_absolute():raise ValidationError('invalid_work_path')
    docker=Docker(docker_socket)
    image=docker.image(image)
    channel=Path(tempfile.mkdtemp(prefix='v-',dir=work))
    protocol=channel/'control.sock'
    if len(os.fsencode(protocol))>100:
        channel.rmdir();raise ValidationError('socket_path_limit')
    name='serverless-code-validator-'+uuid4().hex
    container=None;removed=False;result=None;server=None
    started=time.monotonic();deadline=started+15
    def remaining():
        value=deadline-time.monotonic()
        if value<=0:raise TimeoutError()
        return value
    labels={'tech.p2enjoy.serverless.installation':installation,'tech.p2enjoy.serverless.kind':'validation'}
    future=asyncio.get_running_loop().create_future()
    tasks=set();claimed=False
    async def exchange(reader,writer):
        nonlocal claimed
        task=asyncio.current_task();tasks.add(task)
        try:
            if len(tasks)>4:return
            async with asyncio.timeout(remaining()):
                header=await reader.readuntil(b'\r\n\r\n')
                if len(header)>8192:return
                lines=header.decode('ascii').split('\r\n')
                method,path,version=lines[0].split(' ')
                if version not in ('HTTP/1.0','HTTP/1.1'):return
                headers={}
                for line in lines[1:]:
                    if not line:continue
                    key,value=line.split(':',1);key=key.strip().lower()
                    if key in headers:return
                    headers[key]=value.strip()
                if 'transfer-encoding' in headers:return
                length=headers.get('content-length','0')
                if not re.fullmatch(r'[0-9]{1,6}',length) or int(length)>LIMIT:return
                body=await reader.readexactly(int(length))
                status=404;answer={'error':'not_found'}
                if method=='GET' and path=='/status':
                    status=200 if future.done() else 202;answer={'state':'done' if future.done() else 'running' if claimed else 'prepared'}
                elif method=='GET' and path=='/configuration':
                    if claimed:status=409;answer={'error':'already_started'}
                    else:claimed=True;status=200;answer=payload
                elif method=='POST' and path=='/result':
                    if not claimed or future.done():status=409;answer={'error':'invalid_state'}
                    elif headers.get('content-type')!='application/json':status=415;answer={'error':'content_type'}
                    else:
                        result_data=json.loads(body)
                        # Check and redact before admitting a terminal result.
                        clean=safe_result(result_data,secrets)
                        future.set_result(clean);status=202;answer={'accepted':True}
                data=json.dumps(answer,separators=(',',':')).encode()
                writer.write(f'HTTP/1.1 {status} Response\r\nContent-Type: application/json\r\nContent-Length: {len(data)}\r\nConnection: close\r\n\r\n'.encode()+data)
                await writer.drain()
        except (OSError,ValueError,TypeError,ValidationError,asyncio.IncompleteReadError,asyncio.LimitOverrunError,TimeoutError):
            pass  # A malformed private protocol never produces a successful result.
        finally:
            writer.close()
            try:await asyncio.wait_for(writer.wait_closed(),1)
            except (OSError,TimeoutError):pass
            tasks.discard(task)
    try:
        server=await asyncio.start_unix_server(exchange,path=str(protocol),limit=8192)
        os.chmod(protocol,0o600)
        config={'Image':image,'User':'0:0','WorkingDir':'/runtime','Labels':labels,
                'Entrypoint':['node','/runtime/validate-supervisor.mjs'],'Cmd':[],
                'HostConfig':{'NetworkMode':'none','ReadonlyRootfs':True,'CapDrop':['ALL'],
                    'SecurityOpt':['no-new-privileges:true'],'Memory':512*1024**2,'MemorySwap':512*1024**2,
                    'NanoCpus':250000000,'PidsLimit':64,'Init':True,
                    'Tmpfs':{'/tmp':'rw,noexec,nosuid,size=16m,mode=1777'},
                    'LogConfig':{'Type':'none'},
                    'Mounts':[{'Type':'bind','Source':str(code),'Target':'/code','ReadOnly':True},
                              {'Type':'bind','Source':str(host_work/channel.name),'Target':'/protocol','ReadOnly':True}]}}
        data=docker.call('POST','/containers/create?name='+name,config,timeout=remaining())
        container=data['Id']
        docker.call('POST','/containers/'+container+'/start',timeout=remaining())
        result=await asyncio.wait_for(future,remaining())
    except (TimeoutError,socket.timeout):result={'valid':False,'error':'validation_timeout','logs':'','logs_truncated':False}
    except (OSError,ValidationError) as error:
        result={'valid':False,'error':str(error) if isinstance(error,ValidationError) else 'runtime_unavailable',
                'logs':'','logs_truncated':False}
    finally:
        if server:
            server.close()
        for task in tuple(tasks):task.cancel()
        if tasks:await asyncio.gather(*tuple(tasks),return_exceptions=True)
        if server:await server.wait_closed()
        # A create timeout may leave a container whose response was lost: use our unique name.
        target=container or name
        try:
            data=docker.call('GET','/containers/'+target+'/json',timeout=5,allowed=(200,404))
            if isinstance(data,dict) and data.get('Id'):
                if data.get('Config',{}).get('Labels',{}).get('tech.p2enjoy.serverless.installation')!=installation:
                    raise ValidationError('cleanup_ownership')
                docker.call('DELETE','/containers/'+target+'?force=1&v=1',timeout=10,allowed=(204,404))
                status,_=request(docker_socket,'GET','/v1.45/containers/'+target+'/json',timeout=5)
                if status!=404:raise ValidationError('cleanup_failed')
            removed=True
        except (OSError,ValidationError):
            result={'valid':False,'error':'cleanup_failed','logs':'','logs_truncated':False}
        if removed:shutil.rmtree(channel)
    result['image_id']=image
    result['elapsed_seconds']=round(time.monotonic()-started,3)
    result['container_removed']=removed
    return result


def validate(**kwargs):return asyncio.run(validate_async(**kwargs))


def main():
    parser=argparse.ArgumentParser(description='Validation réelle Node dans Docker DEV')
    for name in ('image','code','work','handler','installation'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--host-work')
    parser.add_argument('--docker-socket',default='/run/user/1001/docker.sock')
    args=parser.parse_args()
    try:
        raw=sys.stdin.buffer.read(LIMIT+1)
        if len(raw)>LIMIT:raise ValidationError('configuration_limit')
        config=json.loads(raw)
        if not isinstance(config,dict) or set(config)-{'environment','secrets'}:raise ValidationError('invalid_configuration')
        result=validate(**vars(args),environment=config.get('environment',{}),secrets=config.get('secrets',{}))
    except (ValidationError,ValueError,TypeError,OSError):
        print(json.dumps({'valid':False,'error':'validation_input_or_prerequisite'}));return 1
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['valid'] else 1


if __name__=='__main__':sys.exit(main())
