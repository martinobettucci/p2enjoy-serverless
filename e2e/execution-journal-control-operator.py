# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @spec docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
"""Cut the real DEV control only after the original handler's durable counter."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import time
import traceback
from uuid import UUID

from control_database import read_control
from native_control_observer import NativeObserver
from native_signal_wakeup import NativeWakeup

ROOT=Path('/srv/p2enjoy-serverless');CONTROL=ROOT/'state/control.sqlite3'
PREFIX='serverless-restore-journal-cut-'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']


def emit(value):print(json.dumps(value),flush=True)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def command(args,timeout=10):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout).stdout.strip()
def inspect(name):return json.loads(command(DOCKER+['inspect',name]))[0]
def atomic(folder,name,value):
    target=folder/(name+'.pending')
    with target.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(json.dumps(value)+'\n');stream.flush();os.fsync(stream.fileno())
    target.replace(folder/name)


def guard_states(unit):
    result={}
    for suffix in ('timer','service'):
        value=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=LoadState','--property=ActiveState','--property=MainPID'],capture_output=True,text=True,timeout=10)
        row=dict(line.split('=',1) for line in value.stdout.splitlines())
        assert row.get('LoadState') in ('loaded','not-found') and 'ActiveState' in row
        if value.returncode:assert row['LoadState']=='not-found' and row['ActiveState']=='inactive'
        result[suffix]=row
    return result


def finish_guard(unit):
    subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=10)
    deadline=time.monotonic()+50
    while True:
        value=guard_states(unit)
        if all(row['ActiveState']=='inactive' and row.get('MainPID','0')=='0' for row in value.values()):return value
        assert time.monotonic()<deadline,'control_cut_guard_not_joined';time.sleep(.1)


def owned(namespace,fn):
    with read_control(CONTROL) as db:
        ns=db.execute('SELECT name,description FROM namespaces WHERE id=?',(namespace,)).fetchone();assert ns
        assert str(UUID(ns['description']))==ns['description']
        assert ns['name']=='execution-journal-api-'+ns['description'][:8]
        function=db.execute('SELECT f.* FROM functions f JOIN services s ON s.id=f.service_id WHERE f.id=? AND s.namespace_id=?',(fn,namespace)).fetchone();assert function
        assert function['name']=='journal-durable-counter' and function['deleted_at'] is None
        assert json.loads(function['config_json'])['storage']['data']['enabled']
        assert db.execute('SELECT count(*) FROM functions f JOIN services s ON s.id=f.service_id WHERE f.deleted_at IS NULL AND s.namespace_id<>?',(namespace,)).fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM schema_migrations WHERE version='011_execution_logs.sql'").fetchone()[0]==1
        return dict(function)


def prepare(namespace,fn,image,unit):
    owned(namespace,fn)
    with read_control(CONTROL) as db:
        for sql in ('SELECT count(*) FROM invocations WHERE completed_at IS NULL','SELECT count(*) FROM function_operations',
                    "SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')"):
            assert db.execute(sql).fetchone()[0]==0,'unowned_active_work'
        assert db.execute('SELECT count(*) FROM invocations WHERE function_id=?',(fn,)).fetchone()[0]==0,'counter_must_be_fresh'
        ready=[dict(row) for row in db.execute("SELECT e.id,e.revision_id,r.image_id FROM execution_instances e JOIN revisions r ON r.id=e.revision_id WHERE e.function_id=? AND e.state='ready'",(fn,))]
        assert len(ready)==1,'counter_warm_instance_required'
        installation=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()['value']
        assert str(UUID(installation))==installation
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert current['Image']==image and all(row['State']['Running'] and row['State']['Health']['Status']=='healthy' for row in (current,reference))
    descendants=[current['State']['Pid']]
    for parent in descendants:descendants.extend(int(value) for value in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
    processes=[pid for pid in descendants if Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
    assert len(processes)==1;pid=processes[0]
    assert Path('/proc',str(pid),'cgroup').read_bytes()==Path('/proc',str(current['State']['Pid']),'cgroup').read_bytes()
    runtime=pin_runtime(fn,ready[0],installation)
    folder=Path('/run')/unit;folder.mkdir(mode=0o700)
    lock=folder/'mutation.lock';lock.touch(mode=0o600);info=lock.stat()
    sources=[Path(__file__),Path(__file__).with_name('execution-journal-control-restore.py'),Path(__file__).with_name('execution-journal-control-kill.py'),
        Path(__file__).with_name('control_database.py'),Path(__file__).with_name('native_control_observer.py'),Path(__file__).with_name('native_signal_wakeup.py')]
    for name,source in [('restore.py',sources[1]),('kill.py',sources[2])]:
        target=folder/name;target.write_bytes(source.read_bytes());target.chmod(0o600)
    item={'namespace_id':namespace,'function_id':fn,'schema':'011_execution_logs.sql','container_id':current['Id'],'image':image,
        'started_at':current['State']['StartedAt'],'reference':[reference['Id'],reference['Image'],reference['State']['StartedAt']],
        'pid':pid,'birth':birth(pid),'cgroup':Path('/proc',str(pid),'cgroup').read_text(),
        'control_netns_inode':Path('/proc',str(pid),'ns/net').stat().st_ino,'start_instance_id':ready[0]['id'],'start_runtime':runtime,
        'helper_pid':os.getpid(),'helper_birth':birth(os.getpid()),'helper_command_sha256':sha('/proc/self/cmdline'),'docker':DOCKER,
        'official_sha256':{path:sha(path) for path in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},
        'program_sha256':{str(path.resolve()):sha(path) for path in sources},'restore_sha256':sha(folder/'restore.py'),'kill_sha256':sha(folder/'kill.py'),
        'lock_identity':[info.st_dev,info.st_ino]}
    atomic(folder,'identity.json',item)
    path=ROOT/'storage-state/backings'/fn/'data'
    assert all(not os.path.lexists(path/name) for name in ('journal-invocation-count.txt','journal-invocation-receipt.json','journal-invocation-receipt.pending.json')),'counter_must_be_empty'
    return folder,item,path


# @spec docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
def pin_runtime(fn,instance,installation):
    labels={'tech.p2enjoy.serverless.kind':'instance','tech.p2enjoy.serverless.function':fn,
        'tech.p2enjoy.serverless.instance':instance['id'],'tech.p2enjoy.serverless.revision':instance['revision_id'],
        'tech.p2enjoy.serverless.installation':installation}
    args=['ps','--no-trunc','--format','{{.ID}}']
    for key,value in labels.items():args.extend(['--filter','label='+key+'='+value])
    ids=command(DOCKER+args).splitlines();assert len(ids)==1,'counter_runtime_not_unique'
    runtime=inspect(ids[0]);assert runtime['Id']==ids[0] and runtime['Image']==instance['image_id'] and runtime['State']['Running']
    assert runtime['Name']=='/serverless-function-journal-durable-counter-'+UUID(instance['id']).hex
    assert all(runtime['Config']['Labels'].get(key)==value for key,value in labels.items())
    protocol=[m for m in runtime['Mounts'] if m['Destination']=='/protocol'];code=[m for m in runtime['Mounts'] if m['Destination']=='/code']
    assert len(protocol)==len(code)==1 and all(m['Type']=='bind' and m['RW'] is False for m in (protocol[0],code[0]))
    source=Path(protocol[0]['Source']);assert source.parent==ROOT/'state/execution'/instance['id'] and re.fullmatch('i-[a-z0-9_]+',source.name)
    assert code[0]['Source']==str(ROOT/'state/artifacts'/instance['revision_id']/'code')
    socket_path=source/'control.sock';info=socket_path.lstat();assert stat.S_ISSOCK(info.st_mode) and info.st_uid==1001
    runtime_pid=runtime['State']['Pid'];assert runtime_pid>1
    return {'container_id':runtime['Id'],'image':runtime['Image'],'started_at':runtime['State']['StartedAt'],'labels':labels,
        'pid':runtime_pid,'birth':birth(runtime_pid),'cgroup_sha256':sha(Path('/proc',str(runtime_pid),'cgroup')),
        'netns_inode':Path('/proc',str(runtime_pid),'ns/net').stat().st_ino,'socket_path':str(socket_path),
        'socket_identity':[info.st_dev,info.st_ino],'channel':'/state/execution/'+instance['id']+'/'+source.name+'/control.sock'}


def runtime_alive(runtime):
    assert birth(runtime['pid'])==runtime['birth'],'counter_runtime_process_changed'
    assert sha(Path('/proc',str(runtime['pid']),'cgroup'))==runtime['cgroup_sha256'],'counter_runtime_cgroup_changed'
    assert Path('/proc',str(runtime['pid']),'ns/net').stat().st_ino==runtime['netns_inode'],'counter_runtime_namespace_changed'
    info=Path(runtime['socket_path']).lstat()
    assert stat.S_ISSOCK(info.st_mode) and [info.st_dev,info.st_ino]==runtime['socket_identity'],'counter_runtime_channel_changed'


def unix_tables(item):
    runtime=item['start_runtime'];runtime_alive(runtime);rows=[]
    assert birth(item['pid'])==item['birth'],'counter_control_process_changed'
    assert Path('/proc',str(item['pid']),'ns/net').stat().st_ino==item['control_netns_inode'],'counter_control_namespace_changed'
    for scope,pid in (('control',item['pid']),('runtime',runtime['pid'])):
        inode=Path('/proc',str(pid),'ns/net').stat().st_ino
        with Path('/proc',str(pid),'net/unix').open('rb') as stream:raw=stream.read(1024**2+1)
        assert len(raw)<=1024**2,'counter_unix_table_byte_bound'
        for line in raw.decode().splitlines()[1:]:
            rows.append((scope,inode,line.split()))
    runtime_alive(runtime);return rows


# @spec docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
def counter_receipt(path,item,diagnostic,*,sql_timeout=2):
    diagnostic['phase']='counter_receipt_presence'
    receipt=path/'journal-invocation-receipt.json'
    if not os.path.lexists(receipt):return None
    diagnostic['phase']='counter_receipt_metadata';diagnostic['files']=[]
    for parent in (path.parent,path,receipt):
        info=parent.lstat();diagnostic['files'].append({'role':('function_backing' if parent==path.parent else 'data_backing' if parent==path else 'receipt'),
            'uid':info.st_uid,'gid':info.st_gid,'mode':stat.S_IMODE(info.st_mode),'type':stat.S_IFMT(info.st_mode),'device':info.st_dev,'inode':info.st_ino,'bytes':info.st_size})
        assert not stat.S_ISLNK(info.st_mode) and info.st_uid==1001,'owned_counter_path_required'
    info=receipt.lstat();assert stat.S_ISREG(info.st_mode) and info.st_size<=1024
    diagnostic['phase']='counter_receipt_json'
    raw=receipt.read_bytes()
    try:value=json.loads(raw)
    except (ValueError,UnicodeError):return None  # An actual write can still be in progress.
    assert set(value)=={'request_id','counter'} and value['counter']==1 and str(UUID(value['request_id']))==value['request_id']
    diagnostic['receipt']={'request_id':value['request_id'],'counter':value['counter'],'sha256':hashlib.sha256(raw).hexdigest()}
    pending=diagnostic.get('first_start_pending')
    if pending is not None:
        assert value['request_id']==pending['invocation']['id'],'counter_start_identity_changed'
        assert diagnostic['receipt']['sha256']==pending['receipt_sha256'],'counter_start_receipt_changed'
    diagnostic['phase']='counter_file'
    counter=path/'journal-invocation-count.txt';info=counter.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_uid==1001 and counter.read_bytes()==b'1\n'
    with read_control(CONTROL,timeout=sql_timeout) as db:
        diagnostic['phase']='counter_invocation'
        row=db.execute('SELECT id,function_id,state,handler_started,instance_id,completed_at,dispatched_at FROM invocations WHERE id=?',(value['request_id'],)).fetchone()
        diagnostic['invocation']=dict(row) if row else None
        assert row and row['function_id']==item['function_id'] and row['state']=='running' and row['completed_at'] is None
        active=[row[0] for row in db.execute('SELECT id FROM invocations WHERE completed_at IS NULL')]
        assert active==[value['request_id']]
        if row['handler_started'] is None:
            diagnostic.setdefault('first_start_pending',{'observed_at_ns':time.time_ns(),'invocation':dict(row),
                'receipt_sha256':hashlib.sha256(raw).hexdigest()})
            diagnostic['start_pending_polls']=diagnostic.get('start_pending_polls',0)+1
            return None
        assert row['handler_started']==1,'counter_start_acknowledgement_invalid'
    return {'request_id':value['request_id'],'counter':value['counter'],'receipt_sha256':hashlib.sha256(raw).hexdigest(),
        'counter_sha256':sha(counter),'receipt_inode':receipt.stat().st_ino,'counter_inode':counter.stat().st_ino,
        'invocation':dict(row),'observed_at_ns':time.time_ns(),
        'start_acknowledgement':{'first_pending':diagnostic.get('first_start_pending'),
            'pending_polls':diagnostic.get('start_pending_polls',0),'accepted_at_ns':time.time_ns()}}


# @spec docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
class CounterObserver(NativeObserver):
    """Wake through SIGCHLD; waitpid remains the only source of tracee status."""
    def __init__(self,pid,wakeup):
        super().__init__(pid)
        self.wakeup=wakeup
        self.metrics={'waiting_mode':'sigchld','polls':0,'stops':0,'empty_polls':0,'sleep_elapsed_ms':0,'wait_elapsed_ms':0,
            'wakeup_waits':0,'wakeup_bytes_drained':0}

    def wait(self,deadline):
        while True:
            assert time.monotonic()<deadline,'native_stop_not_observed'
            self.metrics['polls']+=1;value,state=os.waitpid(self.pid,os.WNOHANG)
            if value:
                assert os.WIFSTOPPED(state),'control_exited_during_observation'
                self.stopped=True;self.metrics['stops']+=1
                assert time.monotonic()<deadline,'native_stop_after_deadline'
                return os.WSTOPSIG(state)
            assert time.monotonic()<deadline,'native_stop_not_observed'
            self.metrics['empty_polls']+=1;before=time.monotonic();self.wakeup.wait(deadline)
            self.metrics['wait_elapsed_ms']+=(time.monotonic()-before)*1000
            self.metrics.update(wakeup_waits=self.wakeup.waits,wakeup_bytes_drained=self.wakeup.bytes_drained)


def started_receive(observer,item,deadline,diagnostic):
    expected=b'POST /started HTTP/1.1\r\n';pending=None;offsets={};events=0
    measure={'started_at_ns':time.time_ns(),'events':0,'syscalls':{},'positive_reads':0,'socket_reads':0,
        'unix_reads':0,'unix_samples':[],'unix_samples_overflow':0};diagnostic['receive']=measure;seen=set()
    channel=re.compile(re.escape(item['start_runtime']['channel']))
    observer.resume()
    while True:
        assert time.monotonic()<deadline,'started_receive_deadline'
        assert events<100000,'started_receive_event_bound';events+=1;measure['events']=events;measure['last_at_ns']=time.time_ns()
        assert not select.select([sys.stdin],[],[],0)[0],'counter_owner_closed_before_cut'
        stopped=observer.wait(deadline);stopped_monotonic=time.monotonic()
        if stopped!=signal.SIGTRAP | 0x80:
            assert stopped not in (signal.SIGSTOP,signal.SIGTRAP),'unexpected_native_stop'
            observer.resume(stopped);continue
        phase,data=observer.info()
        if phase==1:
            number,*args=data;pending=(number,args)
            measure['syscalls'][str(number)]=measure['syscalls'].get(str(number),0)+1
            if number==3:offsets.pop(args[0],None)
        elif phase==2 and pending:
            number,args=pending;pending=None
            if number in (0,45) and data>0:
                measure['positive_reads']+=1
                fd,pointer=args[:2]
                try:link=os.readlink('/proc/'+str(item['pid'])+'/fd/'+str(fd))
                except FileNotFoundError:link=''
                if link.startswith('socket:[') and offsets.get(fd,0) is not None:
                    measure['socket_reads']+=1
                    inode=link[8:-1]
                    sockets=unix_tables(item)
                    unix=[(scope,netns,row) for scope,netns,row in sockets if len(row)>=7 and row[6]==inode]
                    if unix:
                        measure['unix_reads']+=1
                        if inode not in seen:
                            seen.add(inode)
                            if len(measure['unix_samples'])<32:
                                scope,netns,row=unix[0];name=row[7] if len(row)==8 else ''
                                sample={'fd':fd,'inode':int(inode),'type':row[4],'state':row[5],'instance_matches':bool(channel.fullmatch(name)),
                                    'namespace_scope':scope,'netns_inode':netns}
                                if name.startswith('/state/execution/'):sample['path']=name
                                else:sample['path_sha256']=hashlib.sha256(name.encode()).hexdigest()
                                measure['unix_samples'].append(sample)
                            else:measure['unix_samples_overflow']+=1
                    matches={(netns,row[7]):(scope,netns,row) for scope,netns,row in sockets if len(row)==8 and row[6]==inode and row[4]=='0001' and channel.fullmatch(row[7])}
                    if len(matches)==1:
                        scope,netns,matched=next(iter(matches.values()))
                        assert os.readlink('/proc/'+str(item['pid'])+'/fd/'+str(fd))==link,'counter_protocol_descriptor_reused'
                        offset=observer.match_line(pointer,data,expected,offsets.get(fd,0));offsets[fd]=offset
                        if offset==len(expected):
                            assert time.monotonic()<deadline,'started_receive_after_deadline'
                            return {'boundary':'after-started-receive','syscall':number,'syscall_phase':'exit',
                                'fd':fd,'socket_inode':int(inode),'channel':matched[7],'instance_id':item['start_instance_id'],
                                'namespace_scope':scope,'netns_inode':netns,'runtime':item['start_runtime'],
                                'control_netns_inode':item['control_netns_inode'],
                                'control_table_contains_inode':any(side=='control' and row[6]==inode for side,_,row in unix),
                                'request_line_bytes':len(expected),'application_buffers_read':False,
                                'registers_or_results_modified':False,'events':events,'observed_at_ns':time.time_ns(),
                                'stopped_monotonic':stopped_monotonic}
        observer.resume()


def arm(namespace,fn,image,unit):
    folder,item,path=prepare(namespace,fn,image,unit);wakeup=NativeWakeup();observer=CounterObserver(item['pid'],wakeup);lock=None;mutator=None;armed=False
    started=time.monotonic();diagnostic={'phase':'arming_guard','native_wait':observer.metrics}
    try:
        armed=True
        command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=45s','--timer-property=AccuracySec=100ms',
            '--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=200s','--property=TimeoutStopSec=5s',
            '/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover'])
        assert command(['systemctl','is-active',unit+'.timer'])=='active'
        diagnostic['phase']='attaching_started_observer';wakeup.start();observer.start()
        emit({'event':'armed','unit':unit,'container_id':item['container_id'],'image':image,
            'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth']})
        diagnostic['phase']='observing_started_receive';start_gate=started_receive(observer,item,started+30,diagnostic)
        diagnostic['start_gate']=start_gate;held_started=start_gate.pop('stopped_monotonic');held_until=min(started+30,held_started+1)
        try:
            while True:
                assert time.monotonic()<held_until,'counter_pending_not_observed_before_release'
                assert counter_receipt(path,item,diagnostic,sql_timeout=0) is None,'counter_start_preceded_native_receive'
                assert time.monotonic()<held_until,'counter_pending_read_exceeded_hold'
                if diagnostic.get('first_start_pending'):break
                time.sleep(min(.01,max(0,held_until-time.monotonic())))
        finally:
            observer.detach();released=time.monotonic();start_gate['held_elapsed_ms']=(released-held_started)*1000
        assert released<=held_until,'started_receive_hold_exceeded'
        status=Path('/proc',str(item['pid']),'status').read_text().splitlines()
        assert next(row.split()[1] for row in status if row.startswith('TracerPid:'))=='0','started_observer_not_detached'
        emit({'event':'start-pending-observed','unit':unit,'gate':start_gate,'first_pending':diagnostic['first_start_pending'],
            'receive':diagnostic['receive'],'native_wait':observer.metrics})
        while True:
            assert time.monotonic()-started<30,'durable_counter_not_observed'
            if select.select([sys.stdin],[],[],0)[0]:raise RuntimeError('counter_owner_closed_before_cut')
            receipt=counter_receipt(path,item,diagnostic)
            if receipt:break
            time.sleep(.02)
        receipt['start_gate']=start_gate
        diagnostic['phase']='validating_control_generation'
        current=inspect('serverless-api');assert [current['Id'],current['Image'],current['State']['StartedAt']]==[item['container_id'],image,item['started_at']]
        assert birth(item['pid'])==item['birth'] and Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup']
        diagnostic['phase']='attaching_native_observer'
        observer.start();assert observer.attached and observer.stopped
        diagnostic['phase']='locking_native_mutation'
        lock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_NOFOLLOW);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        atomic(folder,'kill-started.json',{'counter':receipt,'requested_at_ns':time.time_ns()})
        diagnostic['phase']='launching_native_kill'
        mutator=subprocess.Popen(['/usr/bin/python3','-I',str(folder/'kill.py'),str(folder),str(lock)],pass_fds=(lock,),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        end=time.monotonic()+10
        while True:
            pid,state=os.waitpid(item['pid'],os.WNOHANG)
            if pid:
                assert os.WIFSIGNALED(state) and os.WTERMSIG(state)==signal.SIGKILL,'native_control_kill_not_observed'
                observer.attached=False;break
            assert time.monotonic()<end,'native_control_death_not_observed';time.sleep(.01)
        mutator.communicate(timeout=40);assert mutator.returncode==0
        killed=inspect('serverless-api');assert not killed['State']['Running'] and killed['State']['ExitCode']==137
        value={'event':'cut','unit':unit,'native_signal':9,'exit_code':137,'container_id':item['container_id'],'image':image,
            'counter':receipt,'docker_mutator_joined':True,'observed_at_ns':time.time_ns()}
        atomic(folder,'native-cut.json',value);emit(value)
        fcntl.flock(lock,fcntl.LOCK_UN);os.close(lock);lock=None
        end=started+35;assert end>time.monotonic()
        if not select.select([sys.stdin],[],[],end-time.monotonic())[0]:raise TimeoutError('counter_owner_did_not_finish')
        assert sys.stdin.readline() in ('restore\n',''),'unexpected_counter_owner_command'
    except BaseException as error:
        value={'event':'operator-failure','unit':unit,'observed_at_ns':time.time_ns(),'diagnostic':diagnostic,
            'failure_type':type(error).__name__,'errno':getattr(error,'errno',None),
            'message_sha256':hashlib.sha256(str(error).encode()).hexdigest(),
            'frames':[{'file':Path(frame.filename).name,'line':frame.lineno,'function':frame.name} for frame in traceback.extract_tb(error.__traceback__,limit=16)]}
        if isinstance(error,AssertionError) and str(error) in ('owned_counter_path_required','durable_counter_not_observed',
                'native_control_kill_not_observed','native_control_death_not_observed','counter_owner_did_not_finish'):
            value['assertion_code']=str(error)
        atomic(folder,'operator-failure.json',value);emit(value);raise
    finally:
        try:
            observer.detach()
            if mutator is not None:
                mutator.communicate(timeout=50);assert mutator.poll() is not None,'cut_mutator_not_joined'
            if lock is not None:fcntl.flock(lock,fcntl.LOCK_UN);os.close(lock)
            if armed:
                receipt=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'check'],190));emit(receipt)
                emit({'event':'guard-finished','unit':unit,'states':finish_guard(unit)})
        finally:wakeup.close()


def main():
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
    mode,namespace,fn,arg=sys.argv[1:5];assert str(UUID(namespace))==namespace and str(UUID(fn))==fn
    if mode=='arm':
        assert len(sys.argv)==6 and re.fullmatch('sha256:[0-9a-f]{64}',arg) and re.fullmatch(PREFIX+'[0-9a-f]{32}',sys.argv[5])
        arm(namespace,fn,arg,sys.argv[5]);return
    assert len(sys.argv)==5 and mode in ('recover','finish','evidence','kill-helper') and re.fullmatch(PREFIX+'[0-9a-f]{32}',arg)
    folder=Path('/run')/arg;item=json.loads((folder/'identity.json').read_text())
    assert item['namespace_id']==namespace and item['function_id']==fn
    if mode=='kill-helper':
        assert (folder/'native-cut.json').is_file()
        fd=os.pidfd_open(item['helper_pid'])
        try:
            assert birth(item['helper_pid'])==item['helper_birth'] and sha(Path('/proc',str(item['helper_pid']),'cmdline'))==item['helper_command_sha256']
            signal.pidfd_send_signal(fd,signal.SIGKILL);assert select.select([fd],[],[],5)[0]
        finally:os.close(fd)
        emit({'event':'helper-killed','unit':arg,'signal':9,'helper_pid':item['helper_pid'],
            'helper_birth':item['helper_birth'],'helper_joined_by_pidfd':True,'observed_at_ns':time.time_ns()});return
    if mode=='recover':
        receipt=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover'],190))
    else:
        receipts=[json.loads(path.read_text()) for path in folder.glob('restoration-receipt-*.json')]
        receipt=max(receipts,key=lambda row:row['finished_monotonic_ns']) if receipts else {'event':'pending','unit':arg}
    if mode=='finish':assert receipt.get('completed'),'restoration_receipt_missing'
    if mode!='evidence':receipt['guard_states']=finish_guard(arg)
    emit(receipt)


if __name__=='__main__':main()
