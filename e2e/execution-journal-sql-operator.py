# @spec docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
"""Observe and hold actual journal workers; no syscall/register/buffer replacement."""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import select
import signal
import socket
import stat
import struct
import subprocess
import sys
import time
from uuid import UUID

from control_database import read_control
from native_control_observer import NativeObserver
from native_signal_wakeup import NativeWakeup

ROOT=Path('/srv/p2enjoy-serverless')
CONTROL=ROOT/'state/control.sqlite3'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
PREFIX='serverless-restore-journal-sql-'
WALL=0x40000000
OPTIONS=1|8


def emit(value):print(json.dumps(value),flush=True)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def command(args,timeout=10):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout).stdout.strip()
def inspect(name):return json.loads(command(DOCKER+['inspect',name]))[0]
def status(tid):
    values=dict(v.split(':',1) for v in Path('/proc',str(tid),'status').read_text().splitlines() if ':' in v)
    return {'state':values['State'].split()[0],'tracer_pid':int(values['TracerPid']),'tgid':int(values['Tgid'])}
def atomic(folder,name,value):
    target=folder/(name+'.pending')
    with target.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(json.dumps(value)+'\n');stream.flush();os.fsync(stream.fileno())
    target.replace(folder/name)


def owner(item):
    assert birth(item['pid'])==item['birth'] and Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_identity_changed'
    assert Path('/proc',str(item['pid']),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert current['State']['Running'] and [current['Id'],current['Image'],current['State']['StartedAt']]==[item['container_id'],item['image'],item['started_at']]
    assert reference['State']['Running'] and [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference']
    return {'pid':item['pid'],'birth':item['birth'],'cgroup_sha256':hashlib.sha256(item['cgroup'].encode()).hexdigest(),**status(item['pid'])}


def guard_states(unit):
    result={}
    for suffix in ('timer','service'):
        process=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=LoadState','--property=MainPID'],capture_output=True,text=True,timeout=10)
        row=dict(v.split('=',1) for v in process.stdout.splitlines())
        assert row.get('LoadState') in ('loaded','not-found') and 'ActiveState' in row
        if process.returncode:assert row['LoadState']=='not-found' and row['ActiveState']=='inactive'
        result[suffix]=row
    return result


def finish_guard(unit):
    subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=10)
    deadline=time.monotonic()+50
    while True:
        states=guard_states(unit)
        if all(row['ActiveState']=='inactive' and row.get('MainPID','0')=='0' for row in states.values()):return states
        assert time.monotonic()<deadline,'guard_not_joined';time.sleep(.05)


def restore(folder,rescue):
    return json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover' if rescue else 'check'],60))


class JournalThread(NativeObserver):
    def __init__(self,tid):
        super().__init__(tid)
        self.birth=birth(tid);self.raw_status=None;self.parent_tid=None;self.early_child=False
        self.held=None;self.pending_lock=None;self.pending_reader_start=None;self.wal_acquired=None;self.wal_released=None;self.exited=None;self.is_main=False

    def record_exit(self,state):
        assert not self.is_main and self.held is None,'principal_or_held_reader_exited'
        self.attached=False;self.stopped=False
        self.exited={'tid':self.pid,'birth':self.birth,'raw_status':state,'at_ns':time.time_ns()}
        if self.memory is not None:os.close(self.memory);self.memory=None

    def wait(self,deadline):
        while time.monotonic()<deadline:
            tid,state=os.waitpid(self.pid,os.WNOHANG|WALL)
            if tid:
                if os.WIFEXITED(state) or os.WIFSIGNALED(state):self.record_exit(state);return None
                assert os.WIFSTOPPED(state),'tracee_exited'
                self.stopped=True;self.raw_status=state;return state
            time.sleep(.001)
        raise TimeoutError('native_thread_stop_deadline')

    def detach(self):
        if not self.attached:return
        if not self.stopped:
            if not self.interrupt(time.monotonic()+2):return
        event=self.raw_status>>16;stopped=os.WSTOPSIG(self.raw_status)
        assert event in (0,128),'detach_with_unjoined_clone'
        delivered=stopped if event==0 and stopped!=(signal.SIGTRAP|0x80) else 0
        self.ptrace(17,0,delivered);self.attached=False;self.stopped=False

    def interrupt(self,deadline):
        try:self.ptrace(0x4207)
        except ProcessLookupError:pass  # Its real exit must still be reaped below.
        self.wait(deadline)
        return self.attached

    def proceed(self,main,delivered=0):
        self.ptrace(7 if self.pid==main else 24,0,delivered);self.stopped=False


def check_thread(trace,item):
    value=status(trace.pid)
    assert birth(trace.pid)==trace.birth and value['tgid']==item['pid'] and value['tracer_pid']==os.getpid(),'thread_identity_changed'
    assert Path('/proc',str(trace.pid),'cgroup').read_text()==item['cgroup']
    return value


def match_open(trace,args,item,comm='journal-read'):
    if args[0]!=257 or trace.pid==item['pid']:return None
    if Path('/proc',str(trace.pid),'comm').read_text().strip()!=comm:return None
    expected=b'/state/control.sqlite3\0'
    if trace.memory is None:trace.memory=os.open(f'/proc/{trace.pid}/mem',os.O_RDONLY)
    if trace.match_line(args[2],len(expected),expected,0)!=len(expected):return None
    info=CONTROL.stat()
    assert stat.S_ISREG(info.st_mode) and [info.st_dev,info.st_ino]==item['database_identity'],'database_identity_changed'
    return {'tid':trace.pid,'birth':trace.birth,'syscall':257,'syscall_phase':'entry','path':'/state/control.sqlite3',
        'device':info.st_dev,'inode':info.st_ino,'comm':comm,'at_ns':time.time_ns()}


# @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
def match_reader_start(trace,op,args,item):
    if trace.pid==item['pid']:return None
    if op==1:
        trace.pending_reader_start=None
        if args[0]!=157 or args[1]!=15:return None
        previous=Path('/proc',str(trace.pid),'comm').read_text().strip()
        if previous=='journal-read':return None  # Never treat name restoration as entry.
        expected=b'journal-read\0'
        if trace.memory is None:trace.memory=os.open(f'/proc/{trace.pid}/mem',os.O_RDONLY)
        if trace.match_line(args[2],len(expected),expected,0)!=len(expected):return None
        trace.pending_reader_start={'tid':trace.pid,'birth':trace.birth,'syscall':157,'command':15,
            'syscall_phase':'exit','boundary':'reader-start','name_assignment_initial':True,
            'previous_name_sha256':hashlib.sha256(previous.encode()).hexdigest(),
            'application_buffers_read':False,'registers_or_results_modified':False}
    elif op==2:
        row=trace.pending_reader_start;trace.pending_reader_start=None
        if row is not None:
            assert args==0,'reader_name_assignment_failed'
            assert Path('/proc',str(trace.pid),'comm').read_text().strip()=='journal-read','reader_name_not_observed'
            row.update(syscall_result=args,comm='journal-read',at_ns=time.time_ns());return row
    return None


def wal_transition(trace,op,args,item,comm='journal-verify'):
    if trace.pid==item['pid']:return None
    if op==2:
        lock,trace.pending_lock=trace.pending_lock,None
        if lock and args==0:return {**lock,'syscall_phase':'exit','syscall_result':args,'at_ns':time.time_ns()}
        return None
    if op!=1:return None
    trace.pending_lock=None
    if args[0]!=72 or args[2]!=6:return None  # fcntl(F_SETLK)
    if Path('/proc',str(trace.pid),'comm').read_text().strip()!=comm:return None
    fd=Path('/proc',str(trace.pid),'fd',str(args[1]))
    try:
        if os.readlink(fd)!='/state/control.sqlite3-shm':return None
        info=fd.stat();expected=Path(str(CONTROL)+'-shm').stat()
    except FileNotFoundError:return None
    assert (info.st_dev,info.st_ino)==(expected.st_dev,expected.st_ino)
    if trace.memory is None:trace.memory=os.open(f'/proc/{trace.pid}/mem',os.O_RDONLY)
    raw=os.pread(trace.memory,32,args[3]);assert len(raw)==32
    kind,whence,start,length,pid=struct.unpack_from('hh4xqqi',raw)
    if kind not in (1,2) or (whence,start,length)!=(0,120,1):return None  # WAL write acquire/release
    trace.pending_lock={'tid':trace.pid,'birth':trace.birth,'syscall':72,'fd':args[1],
        'device':info.st_dev,'inode':info.st_ino,'path':'/state/control.sqlite3-shm',
        'lock_type':kind,'lock_start':start,'lock_length':length,'comm':comm}
    return None


# @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
def match_worker_finish(trace,op,args,item,barrier):
    """The existing diagnostic-name restoration occurs after the real callback returns."""
    comm={'read-result':'journal-read','read-decision':'journal-verify','policy-commit':'journal-write'}[barrier]
    transition=wal_transition(trace,op,args,item,comm)
    if transition:
        if transition['lock_type']==1:trace.wal_acquired=transition;trace.wal_released=None
        elif trace.wal_acquired:
            assert (transition['device'],transition['inode'])==(trace.wal_acquired['device'],trace.wal_acquired['inode'])
            trace.wal_released=transition
    if op!=1 or args[0]!=157 or args[1]!=15 or trace.pid==item['pid']:return None
    if Path('/proc',str(trace.pid),'comm').read_text().strip()!=comm:return None
    if barrier!='read-result' and not (trace.wal_acquired and trace.wal_released):return None
    return {'tid':trace.pid,'birth':trace.birth,'syscall':157,'command':15,'syscall_phase':'entry',
        'comm':comm,'boundary':barrier,'at_ns':time.time_ns(),
        'wal_acquired':trace.wal_acquired,'wal_released':trace.wal_released,
        'application_buffers_read':False,'registers_or_results_modified':False}



# @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
class SyscallDiagnostics:
    """Bounded observations only: no application buffers, registers or results changed."""
    def __init__(self):
        self.started=time.monotonic();self.workers={};self.workers_overflow=0;self.histogram={};self.histogram_overflow=0
        self.locks=[];self.locks_overflow=0;self.pending={};self.events=0
        self.opens=[];self.opens_overflow=0;self.pending_open={}
        self.polls=0;self.empty_polls=0;self.wait_statuses=0

    def observe(self,trace,op,args):
        self.events+=1
        elapsed=time.monotonic()-self.started
        if op==2:
            pending=self.pending.pop(trace.pid,None)
            if pending is not None:
                pending.update(syscall_result=args,exit_after_seconds=elapsed)
            opened=self.pending_open.pop(trace.pid,None)
            if opened is not None:opened.update(syscall_result=args,exit_after_seconds=elapsed)
            return
        if op!=1:return
        comm=Path('/proc',str(trace.pid),'comm').read_text().strip()
        # Only diagnostic worker names are included, never arbitrary memory strings.
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,15}',comm):comm='name-sha256-'+hashlib.sha256(comm.encode()).hexdigest()[:16]
        key=(trace.pid,trace.birth,comm)
        if key in self.workers:
            row=self.workers[key];row['entries']+=1;row['last_after_seconds']=elapsed
        elif len(self.workers)<128:
            self.workers[key]={'tid':trace.pid,'birth':trace.birth,'comm':comm,'entries':1,
                'first_after_seconds':elapsed,'last_after_seconds':elapsed}
        else:self.workers_overflow+=1
        pair=(comm,args[0])
        if pair in self.histogram:self.histogram[pair]+=1
        elif len(self.histogram)<512:self.histogram[pair]=1
        else:self.histogram_overflow+=1
        if args[0]==257 and comm=='journal-read':
            if len(self.opens)<64:
                row={'tid':trace.pid,'birth':trace.birth,'comm':comm,'syscall':257,'entry_after_seconds':elapsed,'syscall_result':None}
                self.opens.append(row);self.pending_open[trace.pid]=row
                try:
                    if trace.memory is None:trace.memory=os.open(f'/proc/{trace.pid}/mem',os.O_RDONLY)
                    path=bytearray();terminated=False
                    for offset in range(256):
                        byte=os.pread(trace.memory,1,args[2]+offset);assert len(byte)==1
                        if byte==b'\0':terminated=True;break
                        path.extend(byte)
                    raw=bytes(path);kind={b'/state/control.sqlite3':'database',b'/state/control.sqlite3-wal':'wal',b'/state/control.sqlite3-shm':'shm'}.get(raw)
                    row.update(path_kind=kind if terminated and kind else 'other',path_sha256=hashlib.sha256(raw).hexdigest(),path_bytes=len(raw),path_terminated=terminated)
                except OSError as error:row['observation_error_type']=type(error).__name__
            else:self.opens_overflow+=1
        if args[0]!=72 or not comm.startswith('journal-'):return
        if len(self.locks)>=128:self.locks_overflow+=1;return
        row={'tid':trace.pid,'birth':trace.birth,'comm':comm,'syscall':72,'fd':args[1],
            'command':args[2],'entry_after_seconds':elapsed,'syscall_result':None}
        self.locks.append(row);self.pending[trace.pid]=row
        fd=Path('/proc',str(trace.pid),'fd',str(args[1]))
        try:
            path=os.readlink(fd);info=fd.stat()
            expected=Path(str(CONTROL)+'-shm');expected_info=expected.stat() if expected.exists() else None
            row.update(path_sha256=hashlib.sha256(path.encode()).hexdigest(),
                exact_expected_path=path=='/state/control.sqlite3-shm',
                shm_basename=path.endswith('/control.sqlite3-shm'),device=info.st_dev,inode=info.st_ino,
                shm_identity_matches=expected_info is not None and (info.st_dev,info.st_ino)==(expected_info.st_dev,expected_info.st_ino))
            if args[2] in (6,7):
                if trace.memory is None:trace.memory=os.open(f'/proc/{trace.pid}/mem',os.O_RDONLY)
                raw=os.pread(trace.memory,32,args[3]);assert len(raw)==32
                kind,whence,start,length,pid=struct.unpack_from('hh4xqqi',raw)
                row.update(lock_type=kind,lock_whence=whence,lock_start=start,lock_length=length)
        except OSError as error:row['observation_error_type']=type(error).__name__

    def receipt(self,unit,held):
        return {'event':'syscall-diagnostic','unit':unit,'syscall_stops':self.events,'held_count':len(held),
            'poll_iterations':self.polls,'empty_polls':self.empty_polls,'waitpid_statuses':self.wait_statuses,
            'elapsed_seconds':time.monotonic()-self.started,'workers':list(self.workers.values()),'workers_overflow':self.workers_overflow,
            'syscalls':[{'comm':comm,'number':nr,'entries':count} for (comm,nr),count in sorted(self.histogram.items())],
            'syscall_histogram_overflow':self.histogram_overflow,'fcntl':self.locks,'fcntl_overflow':self.locks_overflow,
            'openat':self.opens,'openat_overflow':self.opens_overflow,
            'application_buffers_read':False,'registers_or_results_modified':False}


# @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures

def close_traces(traces,item):
    errors=[]
    for trace in reversed(list(traces.values())):
        try:
            if trace.attached:
                try:assert birth(trace.pid)==trace.birth
                except FileNotFoundError:
                    assert not trace.held and not trace.is_main
                    assert not trace.interrupt(time.monotonic()+2),'missing_thread_without_exit'
                trace.detach()
        except (OSError,AssertionError,TimeoutError,ChildProcessError) as error:errors.append({'tid':trace.pid,'type':type(error).__name__})
        finally:
            if trace.memory is not None:os.close(trace.memory);trace.memory=None
    return errors


def prepare(namespace,image,count,unit,barrier):
    with read_control(CONTROL) as db:
        ns=db.execute('SELECT name,description FROM namespaces WHERE id=? AND deleted_at IS NULL',(namespace,)).fetchone();assert ns
        assert str(UUID(ns['description']))==ns['description']
        assert ns['name'] in ('execution-journal-api-'+ns['description'][:8],'execution-journal-ui-'+ns['description'][:8])
        assert db.execute('SELECT count(*) FROM functions f JOIN services s ON s.id=f.service_id WHERE f.deleted_at IS NULL AND s.namespace_id<>?',(namespace,)).fetchone()[0]==0,'foreign_live_function'
        assert db.execute('SELECT count(*) FROM invocations WHERE completed_at IS NULL').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM function_operations').fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM schema_migrations WHERE version='011_execution_logs.sql'").fetchone()[0]==1
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert current['Image']==image and all(row['State']['Running'] and row['State']['Health']['Status']=='healthy' for row in (current,reference))
    descendants=[current['State']['Pid']]
    for parent in descendants:descendants.extend(int(value) for value in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
    pids=[pid for pid in descendants if Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
    assert len(pids)==1;pid=pids[0]
    assert Path('/proc',str(pid),'cgroup').read_bytes()==Path('/proc',str(current['State']['Pid']),'cgroup').read_bytes()
    assert re.fullmatch(PREFIX+'[0-9a-f]{32}',unit)
    folder=Path('/run')/unit;folder.mkdir(mode=0o700)
    source=Path(__file__).with_name('execution-journal-sql-restore.py');info=CONTROL.stat()
    item={'namespace_id':namespace,'count':count,'barrier':barrier,'container_id':current['Id'],'image':image,
        'started_at':current['State']['StartedAt'],'reference':[reference['Id'],reference['Image'],reference['State']['StartedAt']],
        'pid':pid,'birth':birth(pid),'cgroup':Path('/proc',str(pid),'cgroup').read_text(),'database_identity':[info.st_dev,info.st_ino],
        'limits_nofile':list(resource.prlimit(pid,resource.RLIMIT_NOFILE)),'helper_pid':os.getpid(),'helper_birth':birth(os.getpid()),
        'helper_command_sha256':hashlib.sha256(Path('/proc/self/cmdline').read_bytes()).hexdigest(),'docker':DOCKER,
        'official_sha256':{path:sha(path) for path in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},
        'restore_sha256':sha(source),'program_sha256':{str(path.resolve()):sha(path) for path in (Path(__file__),source,Path(__file__).with_name('native_control_observer.py'),Path(__file__).with_name('control_database.py'),Path(__file__).with_name('native_signal_wakeup.py'))}}
    atomic(folder,'identity.json',item);(folder/'restore.py').write_bytes(source.read_bytes());(folder/'restore.py').chmod(0o600)
    return folder,item


def expired(signum,frame):raise TimeoutError('native_observation_deadline')


def next_syscall(traces,item,main,clones,exited,diagnostics,wakeup,deadline):
    """Consume real lifecycle events and yield only a stopped worker syscall."""
    diagnostics.polls+=1
    tid,state=os.waitpid(-1,os.WNOHANG|WALL)
    if not tid:
        diagnostics.empty_polls+=1;wakeup.wait(deadline);return None
    diagnostics.wait_statuses+=1
    if os.WIFEXITED(state) or os.WIFSIGNALED(state):
        assert tid in traces and tid!=main.pid and traces[tid].held is None,'principal_or_held_reader_exited'
        trace=traces[tid];trace.record_exit(state);exited.append(trace.exited);return None
    assert os.WIFSTOPPED(state),'unexpected_wait_status'
    event=state>>16;stopped=os.WSTOPSIG(state)
    if tid not in traces:
        assert event==128 and stopped==signal.SIGTRAP and len(traces)<64,'unexpected_inherited_stop'
        trace=JournalThread(tid);check_thread(trace,item);trace.attached=True;trace.early_child=True;traces[tid]=trace
    trace=traces[tid];trace.stopped=True;trace.raw_status=state;check_thread(trace,item)
    if event==3:
        child=ctypes.c_ulong();trace.ptrace(0x4201,0,ctypes.addressof(child))
        if child.value in traces:
            new=traces[child.value];assert new.early_child and new.parent_tid is None
        else:
            assert len(traces)<64;new=JournalThread(child.value);check_thread(new,item);new.attached=True;traces[new.pid]=new
        new.parent_tid=tid;clones.append({'parent_tid':tid,'child_tid':new.pid,'child_birth':new.birth,'initial_stop_seen_first':new.early_child})
        trace.proceed(main.pid);return None
    if event==128:
        assert stopped==signal.SIGTRAP,'unexpected_group_stop'
        trace.proceed(main.pid);return None
    if stopped==(signal.SIGTRAP|0x80):
        assert tid!=main.pid,'main_syscall_trace_forbidden'
        return trace,*trace.info()
    assert event==0,'unexpected_ptrace_event';trace.proceed(main.pid,stopped)
    return None


# @spec docs/BACKLOG.md#sls-127 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-127 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
def exhaust_reader_descriptors(traces,item,held,folder):
    """Both genuine SQLite DB open attempts fail; restore the limit before Python."""
    assert len(held)==1
    reader=traces[held[0]['tid']];deadline=time.monotonic()+2
    changed=False
    try:
        for trace in traces.values():
            if not trace.attached:continue
            if not trace.stopped:
                if not trace.interrupt(deadline):continue
            check_thread(trace,item)
        assert {int(path.name) for path in Path('/proc',str(item['pid']),'task').iterdir()}=={tid for tid,trace in traces.items() if trace.attached},'unjoined_fault_thread'
        op,args=reader.info();assert op==1 and match_open(reader,args,item)
        assert args[3]&os.O_ACCMODE==os.O_RDWR,'first_database_open_not_read_write'
        opens=[{'flags':args[3],'access_mode':args[3]&os.O_ACCMODE,'phase':'before-limit-restoration'}]
        assert list(resource.prlimit(item['pid'],resource.RLIMIT_NOFILE))==item['limits_nofile']
        resource.prlimit(item['pid'],resource.RLIMIT_NOFILE,(0,item['limits_nofile'][1]));changed=True
        reader.proceed(item['pid']);state=reader.wait(deadline)
        assert os.WSTOPSIG(state)==(signal.SIGTRAP|0x80) and state>>16==0
        op,result=reader.info();assert op==2 and result==-errno.EMFILE,'real_EMFILE_not_observed'
        opens[0]['syscall_result']=result
        # Keep the real descriptor exhaustion through SQLite's read-only fallback.
        pending_open=None;fallback_observed=False;stops=0
        while stops<64 and time.monotonic()<deadline:
            reader.proceed(item['pid']);state=reader.wait(deadline);stops+=1
            assert state is not None and os.WSTOPSIG(state)==(signal.SIGTRAP|0x80) and state>>16==0
            op,args=reader.info()
            if op==1:
                pending_open=None
                if match_open(reader,args,item):
                    assert args[3]&os.O_ACCMODE==os.O_RDONLY,'fallback_database_open_not_read_only'
                    assert resource.prlimit(item['pid'],resource.RLIMIT_NOFILE)[0]==0
                    pending_open={'flags':args[3],'access_mode':args[3]&os.O_ACCMODE,'phase':'before-limit-restoration'}
            elif op==2 and pending_open is not None:
                assert args==-errno.EMFILE,'fallback_real_EMFILE_not_observed'
                pending_open['syscall_result']=args;opens.append(pending_open);fallback_observed=True;break
        assert fallback_observed,'bounded_next_database_open_not_observed'
        resource.prlimit(item['pid'],resource.RLIMIT_NOFILE,tuple(item['limits_nofile']));changed=False
        assert list(resource.prlimit(item['pid'],resource.RLIMIT_NOFILE))==item['limits_nofile']
        value={'event':'native-fault','unit':folder.name,'reader':held[0],'syscall_result':result,
            'database_opens':opens,'fallback_syscall_stops':stops,'restoration_after_open_attempt':2,
            'fault_seconds':2-(deadline-time.monotonic()),
            'restored_before_Python':True,'limits_nofile':item['limits_nofile'],
            'threads_stopped':[{'tid':trace.pid,'birth':trace.birth,**check_thread(trace,item)} for trace in traces.values() if trace.attached and trace.stopped],
            'threads_exited':[trace.exited for trace in traces.values() if trace.exited],
            'at_ns':time.time_ns()}
        atomic(folder,'native-fault.json',value);emit(value)
    finally:
        if changed:resource.prlimit(item['pid'],resource.RLIMIT_NOFILE,tuple(item['limits_nofile']))


def hold(namespace,image,count,unit,barrier):
    folder,item=prepare(namespace,image,count,unit,barrier)
    traces={};held=[];armed=False;started=time.monotonic();events=0;clones=[];exited=[];phase='prepared';diagnostics=SyscallDiagnostics();wakeup=NativeWakeup()
    alarm=signal.signal(signal.SIGALRM,expired);assert signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0)
    signal.setitimer(signal.ITIMER_REAL,50)
    emit({'event':'prepared','unit':unit,'count':count,'barrier':barrier})
    try:
        wakeup.start()
        armed=True
        command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=60s','--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=60s','--property=TimeoutStopSec=5s','/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover'])
        assert command(['systemctl','is-active',unit+'.timer'])=='active'
        fresh=owner(item);assert fresh['tracer_pid']==0 and fresh['state'] not in ('t','T')
        phase='attaching';main=JournalThread(item['pid']);main.is_main=True;traces[main.pid]=main
        main.ptrace(0x4206,0,OPTIONS);main.attached=True;main.ptrace(0x4207);main.wait(time.monotonic()+3)
        census={int(path.name) for path in Path('/proc',str(main.pid),'task').iterdir()};assert len(census)<=64
        for tid in sorted(census-{main.pid}):
            trace=JournalThread(tid);traces[tid]=trace
            assert status(tid)['tracer_pid']==0 and status(tid)['tgid']==item['pid']
            trace.ptrace(0x4206,0,OPTIONS);trace.attached=True;trace.ptrace(0x4207);trace.wait(time.monotonic()+3)
            if trace.attached:check_thread(trace,item)
        for trace in traces.values():
            if trace.attached:trace.proceed(main.pid)
        phase='acquiring';emit({'event':'armed','unit':unit,'threads_attached':len(traces),'process':owner(item),
            'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth']})
        while len(held)<count or any(trace.early_child and trace.parent_tid is None for trace in traces.values()):
            assert time.monotonic()-started<40,'reader_acquisition_deadline'
            if select.select([sys.stdin],[],[],0)[0]:raise RuntimeError('owner_closed_before_hold')
            events+=1;assert events<=200000,'native_event_limit'
            observed=next_syscall(traces,item,main,clones,exited,diagnostics,wakeup,started+40)
            if observed is None:continue
            trace,op,args=observed
            diagnostics.observe(trace,op,args)
            if barrier=='reader-start':
                matched=match_reader_start(trace,op,args,item)
            elif barrier=='sqlite-reservation':
                transition=wal_transition(trace,op,args,item)
                matched=transition if transition and transition['lock_type']==1 else None
            elif barrier in ('read-result','read-decision','policy-commit'):
                matched=match_worker_finish(trace,op,args,item,barrier)
            else:matched=match_open(trace,args,item,comm='journal-write' if barrier=='write' else 'journal-read') if op==1 else None
            if matched:
                assert trace.held is None;trace.held=matched;held.append(matched)
                emit({'event':'reader-held','unit':unit,'reader':matched,'held_count':len(held)});continue
            trace.proceed(main.pid)
        phase='held'
        if barrier=='fault':
            phase='native-descriptor-fault';exhaust_reader_descriptors(traces,item,held,folder);return
        for trace in list(traces.values()):
            if trace.held is None and trace.attached:trace.detach()
        assert status(main.pid)['tracer_pid']==0 and status(main.pid)['state'] not in ('t','T')
        for row in held:
            trace=traces[row['tid']];assert check_thread(trace,item)['state']=='t' and trace.stopped
        value={'event':'held','unit':unit,'readers':held,'events':events,'threads_seen':len(traces),'clone_events':clones,'exited_threads':exited}
        atomic(folder,'held.json',value);emit(value)
        deadline=started+45;assert deadline>time.monotonic()
        if not select.select([sys.stdin],[],[],deadline-time.monotonic())[0]:raise TimeoutError('reader_hold_deadline')
        line=sys.stdin.readline();assert line in ('release\n',''),'unexpected_owner_command'
        emit({'event':'releasing','unit':unit,'reason':'release' if line else 'EOF'})
    except BaseException as error:
        trace=error.__traceback__
        while trace and trace.tb_next:trace=trace.tb_next
        value={'event':'operator-failed','unit':unit,'phase':phase,'failure_type':type(error).__name__,
            'message_sha256':hashlib.sha256(str(error).encode()).hexdigest(),'source_line':trace.tb_lineno if trace else None,'held_count':len(held),'events':events}
        atomic(folder,'operator-failure.json',value);emit(value);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,alarm)
        try:
            try:
                diagnostic=diagnostics.receipt(unit,held)
                diagnostic.update(wakeup_waits=wakeup.waits,wakeup_bytes_drained=wakeup.bytes_drained)
                atomic(folder,'syscall-diagnostic.json',diagnostic);emit(diagnostic)
            finally:
                errors=close_traces(traces,item)
                if errors:emit({'event':'detach-errors','unit':unit,'errors':errors})
                if armed:
                    emit(restore(folder,False));emit({'event':'guard-finished','unit':unit,'states':finish_guard(unit)})
        finally:wakeup.close()


def main():
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','DEV_only'
    mode,namespace,arg=sys.argv[1:4];assert str(UUID(namespace))==namespace
    if mode=='hold':
        assert len(sys.argv)==7 and re.fullmatch('sha256:[0-9a-f]{64}',arg)
        count=int(sys.argv[4]);unit=sys.argv[5];barrier=sys.argv[6]
        assert 1<=count<=2 and barrier in ('read','reader-start','read-result','read-decision','policy-commit','sqlite-reservation','fault','write') and (barrier in ('read','reader-start') or count==1)
        hold(namespace,arg,count,unit,barrier);return
    assert len(sys.argv)==4 and mode in ('recover','finish','evidence','kill','suspend') and re.fullmatch(PREFIX+'[0-9a-f]{32}',arg)
    folder=Path('/run')/arg;item=json.loads((folder/'identity.json').read_text());assert item['namespace_id']==namespace
    if mode in ('kill','suspend'):
        assert (folder/'held.json').is_file();owner(item)
        fd=os.pidfd_open(item['helper_pid'])
        try:
            assert birth(item['helper_pid'])==item['helper_birth'] and not select.select([fd],[],[],0)[0]
            delivered=signal.SIGKILL if mode=='kill' else signal.SIGSTOP
            signal.pidfd_send_signal(fd,delivered)
            if mode=='kill':assert select.select([fd],[],[],5)[0]
            else:
                deadline=time.monotonic()+2
                while status(item['helper_pid'])['state']!='T':
                    assert time.monotonic()<deadline;time.sleep(.005)
            emit({'event':'helper-signalled','unit':arg,'signal':int(delivered),'observed_at_ns':time.time_ns(),
                'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth'],'helper_joined_by_pidfd':mode=='kill'})
        finally:os.close(fd)
    elif mode=='evidence':
        receipts=[json.loads(path.read_text()) for path in folder.glob('restoration-receipt-*.json')]
        emit(max(receipts,key=lambda row:row['finished_monotonic_ns']) if receipts else {'event':'pending'})
    else:
        receipt=restore(folder,mode=='recover');receipt['guard_states']=finish_guard(arg);emit(receipt)


if __name__=='__main__':main()
