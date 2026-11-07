# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#installation-et-canal-opérateur
"""Private Unix RPC for the host volume supervisor, run by its DEV systemd unit."""
import asyncio
from contextlib import suppress
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import stat
import struct
import sys

# -I excludes the script directory; imports are restricted to this protected bundle.
BUNDLE=Path(__file__).resolve().parent
for candidate in (Path(__file__).resolve(),BUNDLE,*BUNDLE.parents):
    info=candidate.stat()
    if info.st_uid!=0 or info.st_mode&0o022:raise SystemExit('unprotected_storage_bundle')
sys.path.insert(0,str(BUNDLE))
from agent_system import StorageError,private_directory,uuid
from agent_volumes import Volumes,canonical,joined


def integer(name,default,low,high):
    raw=os.environ.get(name,str(default))
    if not raw.isdecimal() or not low<=int(raw)<=high:raise StorageError('invalid_configuration')
    return int(raw)


def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise StorageError('duplicate_key')
        result[key]=value
    return result


class Server:
    def __init__(self,volumes,directory):
        self.volumes=volumes;self.directory=private_directory(directory)
        self.path=self.directory/'agent.sock';self.connections=set();self.tasks=set();self.stopping=False;self.quiesced=False
        self.owner=os.open(self.directory/'socket.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(self.owner,fcntl.LOCK_EX|fcntl.LOCK_NB)

    def parse(self,line):
        try:request=json.loads(line,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
        except (UnicodeError,ValueError,RecursionError):raise StorageError('invalid_json') from None
        if not isinstance(request,dict):raise StorageError('invalid_request')
        operation=request.get('op')
        fields={
            'health':set(),'quiesce':{'installation_id'},'resume':{'installation_id'},'status':{'function_id'},'leases':{'installation_id','after'},
            'configure':{'function_id','configuration','expected_version'},
            'prepare-configuration':{'function_id','operation_id','installation_id','configuration','expected_version'},
            'commit-configuration':{'function_id','operation_id','installation_id'},
            'abort-configuration':{'function_id','operation_id','installation_id','configuration','expected_version'},
            'configuration-operation':{'function_id','operation_id','installation_id'},
            # @spec docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#décision-et-périmètre
            'start-discard':{'function_id','operation_id','installation_id','kind','expected_version'},
            'discard-operation':{'function_id','operation_id','installation_id'},
            'acquire':{'function_id','consumer_id','installation_id','configuration'},
            'release':{'consumer_id','installation_id'},'check':{'consumer_id','installation_id'},
            'archive':{'function_id','expected_version'},'purge':{'function_id','expected_version'},
            'clear-cache':{'function_id','expected_version'},
        }
        if not isinstance(operation,str) or operation not in fields:raise StorageError('invalid_operation')
        optional={'after'} if operation in ('prepare-configuration','start-discard') else {'after','expected_version'}
        if operation=='abort-configuration':
            optional.add('configuration')
            if ('configuration' in request)!=('expected_version' in request):raise StorageError('invalid_fields')
        if set(request)-{'op'}-fields[operation] or fields[operation]-optional-set(request):raise StorageError('invalid_fields')
        for field in ('function_id','consumer_id','installation_id','operation_id','after'):
            if field in request:uuid(request[field])
        if 'expected_version' in request and (type(request['expected_version']) is not int or request['expected_version']<0):raise StorageError('invalid_version')
        return request

    async def dispatch(self,request):
        v=self.volumes;op=request['op']
        if op=='health':return {**v.health(),'quiesced':self.quiesced}
        if op=='status':return v.snapshot(request['function_id'])
        if op=='configuration-operation':return v.configuration_operation(request['function_id'],request['operation_id'],request['installation_id'])
        if op=='discard-operation':return v.discards.query(request['function_id'],request['operation_id'],request['installation_id'])
        if op=='leases':
            rows=v.db.execute('SELECT consumer_id,function_id,mounts_json FROM leases WHERE installation_id=? AND consumer_id>? ORDER BY consumer_id LIMIT 51',
                (request['installation_id'],request.get('after',''))).fetchall()
            return {'leases':[{'consumer_id':r['consumer_id'],'function_id':r['function_id'],'complete':bool(json.loads(r['mounts_json']))} for r in rows[:50]],
                    'next':rows[49]['consumer_id'] if len(rows)>50 else None}
        if not v.ready or self.stopping:raise StorageError('agent_not_ready')
        try:await asyncio.wait_for(v.lock.acquire(),3)
        except TimeoutError:raise StorageError('agent_busy') from None
        try:
            if self.stopping:raise StorageError('agent_not_ready')
            if op in ('quiesce','resume'):
                if request['installation_id']!=v.id:raise StorageError('installation_conflict')
                if op=='quiesce':
                    health=v.health()
                    if not health['healthy'] or health['leases'] or health['pending_functions'] or health['mounted_or_reserved']:raise StorageError('maintenance_busy')
                self.quiesced=op=='quiesce'
                return {'quiesced':self.quiesced,'installation_id':v.id}
            if self.quiesced:raise StorageError('maintenance_active')
            if op=='start-discard':return v.discards.start(request['function_id'],request['operation_id'],request['installation_id'],request['kind'],request['expected_version'])
            if op=='prepare-configuration':return await v.prepare_configuration(request['function_id'],request['operation_id'],request['installation_id'],request['configuration'],request['expected_version'])
            if op in ('commit-configuration','abort-configuration'):
                unseen={'configuration':request['configuration'],'expected_version':request['expected_version']} if 'configuration' in request else None
                return await v.resolve_configuration(request['function_id'],request['operation_id'],request['installation_id'],'committed' if op=='commit-configuration' else 'aborted',unseen=unseen)
            if op=='configure':return await v.configure(request['function_id'],request['configuration'],request.get('expected_version'))
            if op=='acquire':return await v.acquire(request['function_id'],request['consumer_id'],request['installation_id'],request['configuration'])
            if op=='release':return await v.release(request['consumer_id'],request['installation_id'])
            if op=='check':return await v.check(request['consumer_id'],request['installation_id'])
            if op=='archive':return await v.archive(request['function_id'],request.get('expected_version'))
            return await v.discard(request['function_id'],op,request.get('expected_version'))
        finally:v.lock.release()

    async def handle(self,reader,writer):
        if self.stopping or len(self.tasks)>=16:
            writer.close();return
        task=asyncio.current_task();self.tasks.add(task)
        admitted=False
        try:
            if self.stopping or len(self.connections)>=16:raise StorageError('connection_limit')
            peer=writer.get_extra_info('socket').getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12)
            _,uid,_=struct.unpack('3i',peer)
            if uid!=os.getuid():raise StorageError('peer_denied')
            self.connections.add(writer);admitted=True
            try:line=await asyncio.wait_for(reader.readline(),3)
            except (ValueError,asyncio.LimitOverrunError):raise StorageError('request_too_large') from None
            except TimeoutError:raise StorageError('read_timeout') from None
            if not line.endswith(b'\n') or len(line)>16384:raise StorageError('invalid_frame')
            request=self.parse(line)
            result=await self.dispatch(request)
            response={'ok':True,'result':result}
        except StorageError as error:response={'ok':False,'error':str(error)}
        except (OSError,sqlite3.Error):response={'ok':False,'error':'storage_io_error'}
        except Exception:
            print('storage_internal_error',file=sys.stderr,flush=True)
            response={'ok':False,'error':'internal_error'}
        else:pass
        try:
            data=(canonical(response)+'\n').encode()
            if len(data)>65536:data=b'{"ok":false,"error":"response_too_large"}\n'
            writer.write(data)
            with suppress(OSError,TimeoutError):await asyncio.wait_for(writer.drain(),3)
        finally:
            writer.close()
            with suppress(OSError,TimeoutError):await asyncio.wait_for(writer.wait_closed(),1)
            if admitted:self.connections.discard(writer)
            self.tasks.discard(task)

    async def maintenance(self):
        while not self.volumes.ready and not self.stopping:
            async with self.volumes.lock:
                try:await self.volumes.recover()
                except (StorageError,OSError,sqlite3.Error):self.volumes.last_error='recovery_pending'
            if not self.volumes.ready:await asyncio.sleep(2)
        while not self.stopping:
            await asyncio.sleep(2)
            if self.stopping:break
            try:await self.volumes.maintain()
            except (StorageError,OSError,sqlite3.Error):self.volumes.last_error='recovery_pending'

    async def run(self):
        if self.path.exists():
            if not stat.S_ISSOCK(self.path.lstat().st_mode):raise StorageError('unsafe_socket')
            self.path.unlink()
        server=await asyncio.start_unix_server(self.handle,path=self.path,limit=16384)
        os.chmod(self.path,0o600)
        stopped=asyncio.Event();loop=asyncio.get_running_loop()
        for signum in (signal.SIGTERM,signal.SIGINT):loop.add_signal_handler(signum,stopped.set)
        maintenance=asyncio.create_task(self.maintenance())
        try:
            waiting=asyncio.create_task(stopped.wait())
            done,_=await asyncio.wait((waiting,maintenance),return_when=asyncio.FIRST_COMPLETED)
            if maintenance in done:
                waiting.cancel()
                await maintenance
        finally:
            self.stopping=True;server.close();await server.wait_closed()
            self.volumes.discards.stopping=True
            # In-flight durable mutations finish even if their clients disconnected.
            await joined(asyncio.gather(*tuple(self.tasks),return_exceptions=True))
            await joined(maintenance)
            await self.volumes.discards.finish()
            self.path.unlink(missing_ok=True);os.close(self.owner);self.volumes.close()


async def main():
    os.umask(0o077)
    root=os.environ.get('SERVERLESS_STORAGE_ROOT_HOST','')
    directory=os.environ.get('SERVERLESS_STORAGE_SOCKET_DIR_HOST','')
    volumes=Volumes(root,BUNDLE/'p2-quota',
        integer('SERVERLESS_STORAGE_BUDGET_MIB',32768,1,1048576)*1024**2,
        integer('SERVERLESS_STORAGE_RESERVE_MIB',8192,0,1048576)*1024**2,
        integer('SERVERLESS_STORAGE_MAX_MOUNTS',64,1,256))
    try:await Server(volumes,directory).run()
    finally:
        if not volumes.closed:volumes.close()


if __name__=='__main__':
    try:asyncio.run(main())
    except (StorageError,OSError,sqlite3.Error):raise SystemExit('storage_start_failed')
