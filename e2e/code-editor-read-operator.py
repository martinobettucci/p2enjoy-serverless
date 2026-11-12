# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_READ_CONCURRENCY.md
# @verifies docs/CODE_EDITOR_READ_CONCURRENCY.md#qualification-propre-à-linstrumentation
"""Hold actual DEV worker read syscalls; never change buffers, registers or results."""
import ctypes,hashlib,json,os,re,select,signal,socket,stat,subprocess,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control
from native_control_observer import NativeObserver

ROOT=Path('/srv/p2enjoy-serverless')
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
UNIT='serverless-restore-editor-read-'
WALL=0x40000000
OPTIONS=1|8  # TRACESYSGOOD | TRACECLONE; never EXITKILL.


def emit(value):print(json.dumps(value),flush=True)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def command(args,timeout=10):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout).stdout.strip()
def inspect(name):return json.loads(command(D+['inspect',name]))[0]
def status(tid):
    values=dict(v.split(':',1) for v in Path('/proc',str(tid),'status').read_text().splitlines() if ':' in v)
    return {'state':values['State'].split()[0],'tracer_pid':int(values['TracerPid']),'tgid':int(values['Tgid'])}
def atomic(folder,name,value):
    p=folder/(name+'.pending');p.write_text(json.dumps(value)+'\n');p.chmod(0o600);p.replace(folder/name)


def owner(item):
    assert birth(item['pid'])==item['birth'] and Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_identity_changed'
    assert Path('/proc',str(item['pid']),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert [current['Id'],current['Image'],current['State']['StartedAt']]==[item['container_id'],item['image'],item['started_at']] and current['State']['Running']
    assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']
    return {'pid':item['pid'],'birth':item['birth'],'cgroup_sha256':hashlib.sha256(item['cgroup'].encode()).hexdigest(),**status(item['pid'])}


def guard_states(unit):
    result={}
    for suffix in ('timer','service'):
        p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=LoadState','--property=MainPID'],capture_output=True,text=True,timeout=10)
        row=dict(v.split('=',1) for v in p.stdout.splitlines())
        assert row.get('LoadState') in ('loaded','not-found') and 'ActiveState' in row
        if p.returncode:assert row['LoadState']=='not-found' and row['ActiveState']=='inactive'
        result[suffix]=row
    return result


def finish_guard(unit):
    subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=10)
    deadline=time.monotonic()+50
    while True:
        states=guard_states(unit)
        if all(v['ActiveState']=='inactive' and v.get('MainPID','0')=='0' for v in states.values()):return states
        assert time.monotonic()<deadline,'guard_not_joined';time.sleep(.05)


def restore(folder,rescue):
    return json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover' if rescue else 'check'],60))


class WorkerTrace(NativeObserver):
    """Keep raw wait status so clone events cannot be confused with syscall stops."""
    def __init__(self,tid):
        super().__init__(tid);self.birth=birth(tid);self.held=None;self.raw_status=None

    def wait(self,deadline):
        while time.monotonic()<deadline:
            value,state=os.waitpid(self.pid,os.WNOHANG|WALL)
            if value:
                assert os.WIFSTOPPED(state),'tracee_exited'
                self.stopped=True;self.raw_status=state;return state
            time.sleep(.001)
        raise TimeoutError('tracee_stop_deadline')

    def detach(self):
        if not self.attached:return
        if not self.stopped:
            self.ptrace(0x4207);self.wait(time.monotonic()+2)
        state=self.raw_status;assert state is not None and os.WIFSTOPPED(state)
        event=state>>16;stopped=os.WSTOPSIG(state)
        assert event in (0,128),'detach_with_unjoined_clone'
        delivered=stopped if event==0 and stopped!=(signal.SIGTRAP|0x80) else 0
        self.ptrace(17,0,delivered);self.attached=False;self.stopped=False

    def proceed(self,main_pid,delivered=0):
        self.ptrace(7 if self.pid==main_pid else 24,0,delivered);self.stopped=False


def check_thread(trace,item):
    value=status(trace.pid)
    assert birth(trace.pid)==trace.birth and value['tgid']==item['pid'] and value['tracer_pid']==os.getpid(),'thread_identity_changed'
    assert Path('/proc',str(trace.pid),'cgroup').read_text()==item['cgroup']
    return value


def file_match(trace,args,item):
    if args[0]!=0 or trace.pid==item['pid'] or args[3]<=0:return None
    fd=args[1];path=Path('/proc',str(trace.pid),'fd',str(fd))
    try:
        if os.readlink(path)!=item['container_path']:return None
        info=path.stat()
    except FileNotFoundError:return None
    assert stat.S_ISREG(info.st_mode) and [info.st_dev,info.st_ino,info.st_size]==item['file_identity'],'file_identity_changed'
    thread=check_thread(trace,item);assert thread['state']=='t'
    return {'tid':trace.pid,'birth':trace.birth,'fd':fd,'device':info.st_dev,'inode':info.st_ino,'size':info.st_size,'read_count':args[3],'syscall':0,'syscall_phase':'entry','file_path':item['container_path'],'at_ns':time.time_ns()}


def cleanup_traces(traces,item):
    # Detach never declares success by itself. The independent receipt later
    # enumerates every real thread, including inherited children not yet reported.
    errors=[]
    for trace in reversed(list(traces.values())):
        if not trace.attached:continue
        try:
            assert birth(trace.pid)==trace.birth
            trace.detach()
        except (OSError,AssertionError,TimeoutError,ChildProcessError) as error:
            errors.append({'tid':trace.pid,'type':type(error).__name__})
    return errors


def prepare(fn,ns,image,count,unit):
    with read_control(ROOT/'state/control.sqlite3') as db:
        row=db.execute('SELECT n.name,n.description nonce,s.description service_nonce,f.name function_name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=? AND f.deleted_at IS NULL',(fn,ns)).fetchone()
        assert row and str(UUID(row['nonce']))==row['nonce']==row['service_nonce']
        assert row['name']=='code-editor-read-concurrency-'+row['nonce'][:8]
        assert row['function_name']=='editor-reader-lifecycle-'+row['nonce'][:8]
        assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM invocations WHERE completed_at IS NULL').fetchone()[0]==0
        for table in ('execution_instances','function_operations'):assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()[0]==0
        rev=db.execute('SELECT r.* FROM revisions r JOIN functions f ON f.active_revision_id=r.id WHERE f.id=? AND r.deleted_at IS NULL AND r.stored_bytes>0',(fn,)).fetchone();assert rev
        item=next(v for v in json.loads(rev['inventory_json']) if v['path']=='reader-gate.txt')
        revision=str(UUID(rev['id']));file=ROOT/'state/artifacts'/revision/'code/reader-gate.txt';info=file.stat()
        assert stat.S_ISREG(info.st_mode) and not file.is_symlink() and info.st_size==item['size'] and sha(file)==item['sha256']
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert current['Image']==image and all(v['State']['Running'] and v['State']['Health']['Status']=='healthy' for v in (current,reference))
    assert set(command(D+['ps','-q','--no-trunc']).split())=={current['Id'],reference['Id']}
    descendants=[current['State']['Pid']]
    for parent in descendants:descendants.extend(int(v) for v in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
    pids=[pid for pid in descendants if Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')];assert len(pids)==1;pid=pids[0]
    assert Path('/proc',str(pid),'cgroup').read_bytes()==Path('/proc',str(current['State']['Pid']),'cgroup').read_bytes()
    assert re.fullmatch(UNIT+'[0-9a-f]{32}',unit)
    folder=Path('/run')/unit;folder.mkdir(mode=0o700)
    source=Path(__file__).with_name('code-editor-read-restore.py')
    item={'function_id':fn,'namespace_id':ns,'revision_id':revision,'container_id':current['Id'],'image':image,'started_at':current['State']['StartedAt'],'reference':[reference['Id'],reference['Image'],reference['State']['StartedAt']],
          'pid':pid,'birth':birth(pid),'cgroup':Path('/proc',str(pid),'cgroup').read_text(),'helper_pid':os.getpid(),'helper_birth':birth(os.getpid()),'docker':D,
          'container_path':'/state/artifacts/'+revision+'/code/reader-gate.txt','file_identity':[info.st_dev,info.st_ino,info.st_size],'file_sha256':sha(file),'count':count,
          'official_sha256':{n:sha(n) for n in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},'restore_sha256':sha(source),
          'program_sha256':{str(p.resolve()):sha(p) for p in [Path(__file__),source,Path(__file__).with_name('native_control_observer.py'),Path(__file__).with_name('control_database.py')]}}
    atomic(folder,'identity.json',item);(folder/'restore.py').write_bytes(source.read_bytes());(folder/'restore.py').chmod(0o600)
    return folder,item


def expired(signum,frame):raise TimeoutError('native_observation_deadline')

def hold(fn,ns,image,count,unit):
    folder,item=prepare(fn,ns,image,count,unit);unit=folder.name;traces={};held=[];armed=False;phase='prepared';started=time.monotonic();events=0;failure=None
    previous_alarm=signal.signal(signal.SIGALRM,expired);assert signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0);signal.setitimer(signal.ITIMER_REAL,50)
    emit({'event':'prepared','unit':unit,'image':image,'count':count})
    try:
        armed=True
        command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=60s','--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=60s','--property=TimeoutStopSec=5s','/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover'])
        assert command(['systemctl','is-active',unit+'.timer'])=='active'
        fresh=owner(item);assert fresh['tracer_pid']==0 and fresh['state'] not in ('t','T'),'control_already_traced_or_stopped'
        phase='attaching';main=WorkerTrace(item['pid']);assert main.birth==item['birth'];traces[main.pid]=main
        main.ptrace(0x4206,0,OPTIONS);main.attached=True;main.ptrace(0x4207);main.wait(time.monotonic()+3)
        census={int(p.name) for p in Path('/proc',str(main.pid),'task').iterdir()};assert len(census)<=64
        for tid in sorted(census-{main.pid}):
            trace=WorkerTrace(tid);traces[tid]=trace;before=status(tid);assert before['tracer_pid']==0 and before['tgid']==item['pid']
            assert birth(tid)==trace.birth and Path('/proc',str(tid),'cgroup').read_text()==item['cgroup']
            trace.ptrace(0x4206,0,OPTIONS);trace.attached=True;trace.ptrace(0x4207);trace.wait(time.monotonic()+3);check_thread(trace,item)
        for trace in traces.values():trace.proceed(main.pid)
        phase='reading';emit({'event':'armed','unit':unit,'process':owner(item),'threads_attached':len(traces),'count':count})
        while len(held)<count:
            assert time.monotonic()-started<40,'reader_acquisition_deadline'
            if select.select([sys.stdin],[],[],0)[0]:raise RuntimeError('owner_closed_before_hold')
            tid,state=os.waitpid(-1,os.WNOHANG|WALL)
            if not tid:time.sleep(.001);continue
            events+=1;assert events<=200000,'native_event_limit'
            assert tid in traces and os.WIFSTOPPED(state),'unexpected_tracee_event'
            trace=traces[tid];trace.stopped=True;trace.raw_status=state;check_thread(trace,item)
            event=state>>16;stopped=os.WSTOPSIG(state)
            if event==3:
                child=ctypes.c_ulong();trace.ptrace(0x4201,0,ctypes.addressof(child));new=WorkerTrace(child.value)
                assert new.pid not in traces and len(traces)<64;new.attached=True;traces[new.pid]=new
                trace.proceed(main.pid);continue
            if event==128:
                assert stopped==signal.SIGTRAP,'unexpected_group_stop'
                trace.proceed(main.pid);continue
            if stopped==(signal.SIGTRAP|0x80):
                assert tid!=main.pid,'main_syscall_trace_forbidden'
                op,args=trace.info();matched=file_match(trace,args,item) if op==1 else None
                if matched:
                    assert trace.held is None;trace.held=matched;held.append(matched);emit({'event':'reader-held','unit':unit,'reader':matched,'held_count':len(held)});continue
                trace.proceed(main.pid);continue
            assert event==0,'unexpected_ptrace_event'
            # This is a genuine signal-delivery stop; preserve delivery.
            trace.proceed(main.pid,stopped)
        phase='held'
        for trace in list(traces.values()):
            if trace.held is None:trace.detach()
        assert status(main.pid)['tracer_pid']==0 and status(main.pid)['state'] not in ('t','T')
        for row in held:
            trace=traces[row['tid']];check_thread(trace,item);assert trace.stopped
            observed=file_match(trace,trace.info()[1],item);assert observed is not None
            assert {k:v for k,v in observed.items() if k!='at_ns'}=={k:v for k,v in row.items() if k!='at_ns'}
        value={'event':'held','unit':unit,'process':owner(item),'readers':held,'events':events,'threads_seen':len(traces)};atomic(folder,'held.json',value);emit(value)
        deadline=started+45
        assert deadline>time.monotonic(),'reader_hold_deadline'
        ready=select.select([sys.stdin],[],[],deadline-time.monotonic())[0]
        if not ready:raise TimeoutError('reader_hold_deadline')
        line=sys.stdin.readline();assert line in ('release\n',''),'unexpected_owner_command'
        emit({'event':'releasing','unit':unit,'reason':'release' if line else 'EOF'})
    except BaseException as error:
        failure={'event':'operator-failed','unit':unit,'phase':phase,'failure_type':type(error).__name__,'message_sha256':hashlib.sha256(str(error).encode()).hexdigest(),'events':events,'held_count':len(held)}
        atomic(folder,'operator-failure.json',failure);emit(failure);raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous_alarm)
        errors=cleanup_traces(traces,item)
        if errors:emit({'event':'detach-errors','unit':unit,'errors':errors})
        if armed:
            receipt=restore(folder,False);emit(receipt);emit({'event':'guard-finished','unit':unit,'states':finish_guard(unit)})


def main():
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','DEV_only'
    assert len(sys.argv) in (5,7);mode,fn,ns,arg=sys.argv[1:5];assert str(UUID(fn))==fn and str(UUID(ns))==ns
    if mode=='hold':
        assert len(sys.argv)==7 and re.fullmatch('sha256:[0-9a-f]{64}',arg);count=int(sys.argv[5]);assert 1<=count<=4
        hold(fn,ns,arg,count,sys.argv[6]);return
    assert mode in ('recover','finish','evidence','kill','suspend','recover-low-fds') and len(sys.argv)==5 and re.fullmatch(UNIT+'[0-9a-f]{32}',arg)
    folder=Path('/run')/arg;item=json.loads((folder/'identity.json').read_text());assert item['function_id']==fn and item['namespace_id']==ns
    if mode=='recover-low-fds':
        receipt=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),mode],60))
        assert receipt['event']=='restoration-failed' and receipt['errno']==24 and receipt['helper_gone'] and receipt['own_nofile_restored']
        receipt['guard_states']=finish_guard(arg);emit(receipt);return
    if mode in ('kill','suspend'):
        assert (folder/'held.json').is_file();owner(item)
        fd=os.pidfd_open(item['helper_pid'])
        try:
            assert birth(item['helper_pid'])==item['helper_birth'] and not select.select([fd],[],[],0)[0]
            delivered=signal.SIGKILL if mode=='kill' else signal.SIGSTOP
            signal.pidfd_send_signal(fd,delivered)
            if mode=='kill':assert select.select([fd],[],[],5)[0],'helper_exit_unconfirmed'
            else:
                deadline=time.monotonic()+2
                while status(item['helper_pid'])['state']!='T':
                    assert time.monotonic()<deadline,'helper_stop_unconfirmed';time.sleep(.005)
            emit({'event':'helper-signalled','unit':arg,'signal':int(delivered),'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth'],'observed_at_ns':time.time_ns()})
        finally:os.close(fd)
        return
    if mode=='evidence':
        receipts=[json.loads(p.read_text()) for p in folder.glob('restoration-receipt-*.json')]
        emit(max(receipts,key=lambda v:v['finished_monotonic_ns']) if receipts else {'event':'pending'});return
    receipt=restore(folder,mode=='recover');receipt['guard_states']=finish_guard(arg);emit(receipt)


if __name__=='__main__':main()
