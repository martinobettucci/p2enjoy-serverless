# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#santé-et-reprise
"""Host-only process identities, FUSE mount identities and bounded real probes."""
import asyncio
from contextlib import suppress
import ctypes
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time
from uuid import uuid4


class StorageError(Exception):
    pass


def uuid(value):
    from uuid import UUID
    if not isinstance(value,str):raise StorageError('invalid_uuid')
    try:parsed=str(UUID(value))
    except ValueError:raise StorageError('invalid_uuid') from None
    if value!=parsed:raise StorageError('invalid_uuid')
    return parsed


def private_directory(path,create=False):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts or path==Path('/'):raise StorageError('invalid_root')
    if create:path.mkdir(mode=0o700)
    for parent in (*reversed(path.parents),path):
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode):raise StorageError('unsafe_path')
    info=path.stat()
    if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:raise StorageError('unsafe_permissions')
    return path


def mounts():
    result={}
    def decode(value):return re.sub(r'\\([0-7]{3})',lambda match:chr(int(match[1],8)),value)
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1);a=left.split();b=right.split()
        result[decode(a[4])]={'id':int(a[0]),'device':a[2],'type':b[0],'source':decode(b[1])}
    return result


def process_identity(pid):
    try:
        root=Path('/proc')/str(pid);data=(root/'stat').read_text().rsplit(')',1)[1].split()
        if data[0]=='Z':return None
        status=(root/'status').read_text();uid=int(next(line for line in status.splitlines() if line.startswith('Uid:')).split()[1])
        command=(root/'cmdline').read_bytes()
        if len(command)>8192:return None
        return {'pid':pid,'birth':data[19],'uid':uid,'command':[p.decode() for p in command.rstrip(b'\0').split(b'\0')],
                'exe':os.readlink(root/'exe')}
    except (FileNotFoundError,ProcessLookupError,PermissionError,UnicodeError,ValueError,StopIteration):return None


class System:
    def __init__(self,root,binary,db):
        self.root=Path(root);self.binary=Path(binary);self.db=db
        self.boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        self.children={};self.probe_process=None
        if not self.binary.is_file() or self.binary.is_symlink():raise StorageError('binary_missing')
        for path in (self.binary,*self.binary.parents):
            info=path.stat()
            if info.st_uid!=0 or info.st_mode&0o022:raise StorageError('binary_not_protected')

    def paths(self,row):
        function=uuid(row['function_id']);kind=row['kind']
        if kind not in ('data','cache'):raise StorageError('invalid_kind')
        return self.root/'backings'/function/kind,self.root/'mounts'/function/kind

    def command(self,row):
        backing,mount=self.paths(row)
        binary=row['daemon_binary'] or str(self.binary)
        return [binary,'-direct','-backing',str(backing),'-mount',str(mount),'-bytes',str(row['daemon_quota']),'-name','p2q-'+uuid(row['generation']).replace('-','')]

    def mounted(self,row):
        _,mount=self.paths(row);item=mounts().get(str(mount))
        if not item:return None
        if item['type']!='fuse.p2quota' or not row['generation'] or item['source']!='p2q-'+uuid(row['generation']).replace('-',''):
            raise StorageError('foreign_mount')
        return item

    def identity(self,row):
        if not row['generation'] or row['daemon_boot']!=self.boot:return None
        expected=self.command(row)
        candidates=[row['daemon_pid']] if row['daemon_pid'] else [int(p.name) for p in Path('/proc').iterdir() if p.name.isdecimal()]
        matches=[]
        for pid in candidates:
            info=process_identity(pid)
            if info and info['uid']==os.getuid() and info['command']==expected and info['exe']==expected[0]:
                if row['daemon_birth'] and info['birth']!=row['daemon_birth']:continue
                matches.append(info)
        if len(matches)>1:raise StorageError('ambiguous_process')
        return matches[0] if matches else None

    async def signal(self,identity,signum):
        if not identity:return
        try:fd=os.pidfd_open(identity['pid'])
        except ProcessLookupError:return
        try:
            if process_identity(identity['pid'])!=identity:raise StorageError('process_changed')
            signal.pidfd_send_signal(fd,signum)
        except ProcessLookupError:pass
        finally:os.close(fd)

    async def dead(self,identity,timeout):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            current=process_identity(identity['pid'])
            if not current or current['birth']!=identity['birth']:return True
            await asyncio.sleep(.02)
        return False

    async def launch(self,row):
        command=self.command(row)
        process=await asyncio.create_subprocess_exec(*command,stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL,env={},start_new_session=True)
        self.children[process.pid]=process
        info=process_identity(process.pid)
        if not info:raise StorageError('mount_start_failed')
        self.db.execute('UPDATE volumes SET daemon_pid=?,daemon_birth=? WHERE function_id=? AND kind=?',
            (info['pid'],info['birth'],row['function_id'],row['kind']))
        return info

    async def stop(self,row):
        mounted=self.mounted(row);identity=self.identity(row)
        if identity:
            await self.signal(identity,signal.SIGTERM)
            if not await self.dead(identity,3):raise StorageError('unmount_busy')
        mounted=self.mounted(row)
        if mounted:
            _,path=self.paths(row);libc=ctypes.CDLL(None,use_errno=True)
            if libc.umount2(os.fsencode(path),0)!=0:raise StorageError('unmount_failed')
        if self.mounted(row):raise StorageError('unmount_failed')
        if identity and not await self.dead(identity,.1):raise StorageError('daemon_survived')
        for pid,child in tuple(self.children.items()):
            if child.returncode is not None:self.children.pop(pid)

    async def reap_probe(self):
        previous=self.db.execute('SELECT * FROM probes WHERE id=1').fetchone()
        if not previous:return
        if previous['boot']==self.boot:
            expected=json.loads(previous['command_json'])
            candidates=[previous['pid']] if previous['pid'] else [int(p.name) for p in Path('/proc').iterdir() if p.name.isdecimal()]
            for pid in candidates:
                info=process_identity(pid)
                if not info or info['uid']!=os.getuid() or info['command']!=expected or info['exe']!=str(Path(expected[0]).resolve()):continue
                if previous['birth'] and info['birth']!=previous['birth']:continue
                await self.signal(info,signal.SIGKILL)
                if not await self.dead(info,.2):raise StorageError('probe_pending')
        self.db.execute('DELETE FROM probes WHERE id=1')

    async def probe(self,row):
        await self.reap_probe()
        before=self.mounted(row)
        if not before or not self.identity(row):raise StorageError('mount_unavailable')
        _,mount=self.paths(row)
        command=[sys.executable,'-I','-B',str(Path(__file__).resolve()),'--probe',str(mount),str(uuid4())]
        self.db.execute('INSERT INTO probes VALUES(1,NULL,NULL,?,?)',(self.boot,json.dumps(command)))
        process=await asyncio.create_subprocess_exec(*command,stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,env={},limit=4096)
        self.probe_process=process;identity=process_identity(process.pid)
        if identity:self.db.execute('UPDATE probes SET pid=?,birth=? WHERE id=1',(identity['pid'],identity['birth']))
        reading=asyncio.create_task(process.communicate())
        try:
            output,_=await asyncio.wait_for(asyncio.shield(reading),1)
            if process.returncode or len(output)>4096:raise StorageError('mount_unavailable')
            data=json.loads(output)
            if self.mounted(row)!=before or data['device']!=before['device']:raise StorageError('mount_changed')
            if data['quota']!=row['daemon_quota'] or not 0<=data['used']<=data['quota']:raise StorageError('quota_mismatch')
            return data
        except (TimeoutError,OSError,ValueError,KeyError):raise StorageError('probe_failed') from None
        finally:
            if process.returncode is None:
                with suppress(ProcessLookupError):process.kill()
                with suppress(TimeoutError):await asyncio.wait_for(asyncio.shield(reading),.3)
            if process.returncode is not None:
                self.db.execute('DELETE FROM probes WHERE id=1');self.probe_process=None
            # The durable row prevents more probes while a syscall remains unkillable.
            if not reading.done():reading.add_done_callback(lambda task:task.exception() if not task.cancelled() else None)


def probe_main(path):
    # Drop every capability before a potentially blocked filesystem operation.
    class Header(ctypes.Structure):_fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
    class Data(ctypes.Structure):_fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
    libc=ctypes.CDLL(None,use_errno=True);header=Header(0x20080522,0);data=(Data*2)()
    if libc.capset(ctypes.byref(header),ctypes.byref(data))!=0:raise OSError('capabilities')
    info=os.stat(path);space=os.statvfs(path)
    print(json.dumps({'device':str(os.major(info.st_dev))+':'+str(os.minor(info.st_dev)),
        'quota':space.f_blocks*space.f_frsize,'used':(space.f_blocks-space.f_bfree)*space.f_frsize}),flush=True)


if __name__=='__main__':
    if len(sys.argv)!=4 or sys.argv[1]!='--probe':raise SystemExit(2)
    try:probe_main(sys.argv[2])
    except (OSError,ValueError):raise SystemExit(1)
