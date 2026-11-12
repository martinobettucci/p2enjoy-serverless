# @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER_TASK_EXCEPTION.md
# @verifies docs/CONSOLE_TESTER_TASK_EXCEPTION.md#matrice-de-qualification
"""One real CA openat fails with EMFILE; resources restored before Python runs."""
from contextlib import closing
import datetime,errno,hashlib,json,os,re,resource,select,signal,socket,sqlite3,subprocess,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control,control_owner
from native_control_observer import NativeObserver

ROOT=Path('/srv/p2enjoy-serverless')
CA=b'/usr/local/lib/python3.14/site-packages/certifi/cacert.pem\0'
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']


class DeadlineObserver(NativeObserver):
    """Wait for an actual ptrace stop without a millisecond poll per syscall."""
    def __init__(self,pid):
        super().__init__(pid)
        assert signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),'helper_alarm_already_active'
        self.previous_alarm=signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM,self.expired)

    @staticmethod
    def expired(signum,frame):
        raise TimeoutError('native_stop_not_observed')

    def wait(self,deadline):
        remaining=deadline-time.monotonic()
        assert remaining>0,'native_stop_not_observed'
        signal.setitimer(signal.ITIMER_REAL,remaining)
        try:
            value,state=os.waitpid(self.pid,0)
            assert value==self.pid and os.WIFSTOPPED(state),'control_exited_during_observation'
            self.stopped=True
            return os.WSTOPSIG(state)
        finally:signal.setitimer(signal.ITIMER_REAL,0)

    def detach(self):
        try:super().detach()
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,self.previous_alarm)


def emit(v):print(json.dumps(v),flush=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def command(args,timeout=10):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout).stdout.strip()
def inspect(name):return json.loads(command(D+['inspect',name]))[0]
def status(tid):
    rows=dict(v.split(':',1) for v in Path('/proc',str(tid),'status').read_text().splitlines() if ':' in v)
    return {'state':rows['State'].split()[0],'tracer_pid':int(rows['TracerPid']),'tgid':int(rows['Tgid'])}
def atomic(folder,name,v):
    p=folder/(name+'.pending');p.write_text(json.dumps(v)+'\n');p.chmod(0o600);p.replace(folder/name)
def snapshot(fn):
    with read_control(ROOT/'state/control.sqlite3') as db:
        db.execute('BEGIN')
        result={'invocations':[dict(v) for v in db.execute('SELECT id,state,handler_started,http_status,completed_at FROM invocations WHERE function_id=? ORDER BY id',(fn,))],
                'test_audits':[dict(v) for v in db.execute("SELECT id,action,object_id,created_at FROM audit_events WHERE object_id=? AND action='function.test' ORDER BY created_at,id",(fn,))],
                'integrity':db.execute('PRAGMA integrity_check').fetchone()[0],
                'foreign_keys':[list(v) for v in db.execute('PRAGMA foreign_key_check')]}
        db.rollback();return result

def identity(item):
    assert birth(item['pid'])==item['birth'] and Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_process_changed'
    assert Path('/proc',str(item['pid']),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')
    a,b=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert a['State']['Running'] and [a['Id'],a['Image'],a['State']['StartedAt']]==[item['container_id'],item['image'],item['started_at']]
    assert b['State']['Running'] and [b['Id'],b['Image'],b['State']['StartedAt']]==item['reference']
    return {'pid':item['pid'],'birth':item['birth'],'cgroup_sha256':hashlib.sha256(item['cgroup'].encode()).hexdigest(),**status(item['pid'])}

def guard_states(unit):
    states={}
    for suffix in ('timer','service'):
        p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=LoadState','--property=MainPID'],capture_output=True,text=True,timeout=10)
        values=dict(v.split('=',1) for v in p.stdout.splitlines())
        assert values.get('LoadState') in ('loaded','not-found') and 'ActiveState' in values,'unknown_guard_state'
        if p.returncode:assert values['LoadState']=='not-found' and values['ActiveState']=='inactive'
        states[suffix]=values
    return states
def finish_guard(unit):
    subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=10)
    end=time.monotonic()+50
    while True:
        states=guard_states(unit)
        if all(v.get('ActiveState')=='inactive' and v.get('MainPID','0')=='0' for v in states.values()):return states
        assert time.monotonic()<end,'guard_not_joined';time.sleep(.05)

def restored(folder,recover):
    return json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover' if recover else 'check'],60))


def diagnose(folder,item,fn):
    current=identity(item);assert current['tracer_pid']==0 and current['state'] not in ('t','T')
    assert list(resource.prlimit(item['pid'],resource.RLIMIT_NOFILE))==item['limits_nofile']
    fault=json.loads((folder/'native-fault.json').read_text())
    assert fault['syscall_result']==-errno.EMFILE and fault['restored_before_Python']
    after=snapshot(fn);assert after['invocations']==fault['native_at_entry']['invocations']
    assert after['test_audits']==fault['native_at_entry']['test_audits']
    # Real Docker output stays in memory and is bounded before decoding. Never
    # publish traceback source lines, request buffers or raw log fragments.
    end=datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc=subprocess.Popen(D+['logs','--timestamps','--since',item['log_since'],'--until',end,item['container_id']],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    raw=bytearray();deadline=time.monotonic()+10
    try:
        while True:
            assert time.monotonic()<deadline,'logs_deadline'
            if not select.select([proc.stdout],[],[],.1)[0]:continue
            chunk=os.read(proc.stdout.fileno(),min(65536,2*1024**2+1-len(raw)))
            if not chunk:break
            raw.extend(chunk);assert len(raw)<=2*1024**2,'logs_limit'
        assert proc.wait(timeout=2)==0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
        proc.stdout.close()
    text=bytes(raw).decode('utf8',errors='strict')
    classes=sorted(set(re.findall(r'(?:^|[ |])((?:ssl\.)?SSLError|OSError):',text,re.M)))
    assert classes and all(v in ('ssl.SSLError','SSLError','OSError') for v in classes),'unexpected_exception_class_not_proven'
    names={'/app/app/function_http_client.py','/usr/local/lib/python3.14/site-packages/httpx/_client.py','/usr/local/lib/python3.14/site-packages/httpx/_config.py','/usr/local/lib/python3.14/ssl.py'}
    frames=[]
    for path,line,function in re.findall(r'File "([^"\r\n]+)", line ([0-9]+), in ([A-Za-z_][A-Za-z_0-9]*)',text):
        if path in names:
            value={'file':path,'line':int(line),'function':function}
            if value not in frames:frames.append(value)
    assert any(v['file']=='/app/app/function_http_client.py' and v['function']=='forward' for v in frames)
    assert any(v['file'].endswith('/httpx/_config.py') and v['function']=='create_ssl_context' for v in frames)
    assert any(v['file'].endswith('/ssl.py') and v['function']=='create_default_context' for v in frames)
    assert len(after['test_audits'])==len(fault['native_before']['test_audits'])+1
    assert after['invocations']==fault['native_before']['invocations']
    return {'event':'diagnosed','completed':True,'process':current,'limits_nofile':item['limits_nofile'],'exception_classes':classes,'public_frames':frames,'logs_bytes':len(raw),'logs_sha256':hashlib.sha256(raw).hexdigest(),'unexpected_TLS_exception':True,'unique_test_audit':True,'no_gateway_invocation':True,'native_after':after,'native_fault':fault}


def main():
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','DEV_only'
    assert len(sys.argv)==5
    mode,fn,ns,arg=sys.argv[1:]
    assert mode in ('fault','rescue-window','recover','finish','evidence','inspect','diagnose')
    assert str(UUID(fn))==fn and str(UUID(ns))==ns
    with read_control(ROOT/'state/control.sqlite3') as db:
        row=db.execute('SELECT n.name,n.description nonce,s.description service_nonce,f.name function_name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?',(fn,ns)).fetchone()
        assert row and row['name'].startswith('function-http-client-task-exception-')
        assert str(UUID(row['nonce']))==row['nonce'] and row['nonce']==row['service_nonce'],'owned_original_fixture_required'
        assert row['name']=='function-http-client-task-exception-'+row['nonce'][:8]
        assert row['function_name']=='tester-task-capacity-observer-'+row['nonce'][:8]
    if mode in ('recover','finish','evidence'):
        assert re.fullmatch('serverless-restore-task-exception-[0-9a-f]{32}',arg)
        folder=Path('/run')/arg;item=json.loads((folder/'identity.json').read_text())
        assert item['function_id']==fn and item['namespace_id']==ns
        if mode=='evidence':
            receipts=[json.loads(p.read_text()) for p in folder.glob('restoration-receipt-*.json')]
            for value in receipts:
                assert value['unit']==arg and value['pid']==item['pid'] and value['birth']==item['birth']
                assert all(value[k]==item[k] for k in ('container_id','image','started_at'))
                assert isinstance(value['finished_monotonic_ns'],int) and value['event'] in ('restored','restoration-failed')
            emit(max(receipts,key=lambda value:value['finished_monotonic_ns']) if receipts else {'event':'pending'})
        else:
            receipt=restored(folder,mode=='recover');receipt['guard_states']=finish_guard(arg);emit(receipt)
        return
    if mode in ('inspect','diagnose'):
        assert re.fullmatch('serverless-restore-task-exception-[0-9a-f]{32}',arg)
        item=json.loads((Path('/run')/arg/'identity.json').read_text());assert item['function_id']==fn and item['namespace_id']==ns
        if mode=='diagnose':emit(diagnose(Path('/run')/arg,item,fn));return
        process=identity(item);assert process['tracer_pid']==0 and process['state'] not in ('t','T')
        assert list(resource.prlimit(item['pid'],resource.RLIMIT_NOFILE))==item['limits_nofile']
        emit({'event':'inspected','process':process,'limits_nofile':item['limits_nofile'],'native':snapshot(fn)});return
    assert re.fullmatch('sha256:[0-9a-f]{64}',arg)
    with read_control(ROOT/'state/control.sqlite3') as db:
        assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM functions WHERE id=? AND deleted_at IS NULL',(fn,)).fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM invocations WHERE completed_at IS NULL').fetchone()[0]==0
        for table in ('execution_instances','function_operations','code_drafts'):assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
        assert db.execute("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()[0]==0
    with control_owner(ROOT/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(ROOT/'storage-state/registry.sqlite3')+'?mode=ro',uri=True)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM functions WHERE pending_json IS NOT NULL').fetchone()[0]==0
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
    assert current['Image']==arg and all(v['State']['Running'] and v['State']['Health']['Status']=='healthy' for v in (current,reference))
    assert set(command(D+['ps','-q','--no-trunc']).split())=={current['Id'],reference['Id']}
    descendants=[current['State']['Pid']]
    for parent in descendants:descendants.extend(int(v) for v in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
    pids=[pid for pid in descendants if Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
    assert len(pids)==1;pid=pids[0]
    assert Path('/proc',str(pid),'cgroup').read_bytes()==Path('/proc',str(current['State']['Pid']),'cgroup').read_bytes()
    original=resource.prlimit(pid,resource.RLIMIT_NOFILE);assert 0<original[0]<=original[1]
    unit='serverless-restore-task-exception-'+uuid4().hex;folder=Path('/run')/unit;folder.mkdir(mode=0o700)
    source=Path(__file__).with_name('function-http-client-task-restore.py')
    item={'log_since':datetime.datetime.now(datetime.timezone.utc).isoformat(),'function_id':fn,'namespace_id':ns,'container_id':current['Id'],'image':arg,'started_at':current['State']['StartedAt'],'reference':[reference['Id'],reference['Image'],reference['State']['StartedAt']],
          'pid':pid,'birth':birth(pid),'cgroup':Path('/proc',str(pid),'cgroup').read_text(),'limits_nofile':list(original),'helper_pid':os.getpid(),'helper_birth':birth(os.getpid()),'docker':D,
          'official_sha256':{n:sha(n) for n in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},'restore_sha256':sha(source),
          'program_sha256':{str(p.resolve()):sha(p) for p in [Path(__file__),source,Path(__file__).with_name('native_control_observer.py'),Path(__file__).with_name('control_database.py')]}}
    atomic(folder,'identity.json',item);(folder/'restore.py').write_bytes(source.read_bytes());(folder/'restore.py').chmod(0o600)
    before=snapshot(fn);assert before['integrity']=='ok' and not before['foreign_keys']
    observers={};armed=False;limit_changed=False;fault=None;failure_info=None;phase=1;operation_started=time.monotonic()
    observed={'stops':0,'entries':0,'exits':0,'syscall_entries':{},'signals':{},'open_candidates':{},'CA_comparisons':0,'CA_matches':{}}
    emit({'event':'prepared','unit':unit,'mode':mode,'image':arg,'container_id':current['Id'],'started_at':item['started_at']})
    try:
        armed=True  # Retain the attempted unit even if systemd-run loses its response.
        command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=12s','--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=60s','--property=TimeoutStopSec=5s','/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'recover'])
        assert command(['systemctl','is-active',unit+'.timer'])=='active'
        assert identity(item)['tracer_pid']==0
        main_observer=DeadlineObserver(pid);observers[pid]=main_observer;main_observer.start()
        traced=identity(item);assert traced['tracer_pid']==os.getpid() and traced['state']=='t'
        emit({'event':'armed','unit':unit,'mode':mode,'image':arg,'container_id':current['Id'],'started_at':item['started_at'],'process':traced,'limits_nofile':list(original),'before':before})
        phase=2;deadline=time.monotonic()+8
        while True:
            assert time.monotonic()<deadline,'CA_open_not_observed'
            main_observer.resume();stopped=main_observer.wait(deadline)
            observed['stops']+=1;observed['last_signal']=stopped
            if stopped!=(signal.SIGTRAP|0x80):
                key=str(stopped);observed['signals'][key]=observed['signals'].get(key,0)+1
                assert stopped==signal.SIGTRAP,'unexpected_control_signal';continue
            op,args=main_observer.info();observed['last_event']=op
            if op==2:observed['exits']+=1
            if op==1:
                observed['entries']+=1;number=args[0];observed['last_syscall']=number;key=str(number)
                observed['syscall_entries'][key]=observed['syscall_entries'].get(key,0)+1
                if number in (2,257,437):
                    observed['open_candidates'][key]=observed['open_candidates'].get(key,0)+1
                    observed['CA_comparisons']+=1
                    matched=main_observer.match_line(args[1] if number==2 else args[2],len(CA),CA,0)==len(CA)
                    if matched:observed['CA_matches'][key]=observed['CA_matches'].get(key,0)+1
                    if number==257 and matched:break
        phase=3
        assert args[3]&os.O_ACCMODE==os.O_RDONLY,'CA_read_only_open_required'
        phase=4;at_entry=snapshot(fn)
        assert at_entry['invocations']==before['invocations']
        assert len(at_entry['test_audits'])==len(before['test_audits'])+1,'one_new_test_audit_required'
        assert all(v in at_entry['test_audits'] for v in before['test_audits'])
        phase=5;freeze_deadline=time.monotonic()+2;thread_births={pid:birth(pid)}
        while True:
            census={int(v.name) for v in Path('/proc',str(pid),'task').iterdir()};assert 0<len(census)<=64
            for tid in sorted(census-set(observers)):
                assert time.monotonic()<freeze_deadline
                obs=NativeObserver(tid);observers[tid]=obs;thread_births[tid]=birth(tid)
                assert status(tid)['tracer_pid']==0
                obs.ptrace(0x4206,0,1);obs.attached=True;obs.ptrace(0x4207);obs.wait(freeze_deadline)
            after={int(v.name) for v in Path('/proc',str(pid),'task').iterdir()}
            assert time.monotonic()<freeze_deadline
            if census==after==set(observers):break
        frozen=[]
        for tid in sorted(observers):
            v=status(tid);assert birth(tid)==thread_births[tid] and v['tracer_pid']==os.getpid() and v['state']=='t' and v['tgid']==pid
            frozen.append({'tid':tid,'birth':thread_births[tid],**v})
        # No subprocess or detached mutator operates the limit. The independent
        # guard stops this exact helper before restoring it on forced rescue.
        phase=6;fresh=identity(item);assert fresh['tracer_pid']==os.getpid() and fresh['state']=='t'
        assert {int(v.name) for v in Path('/proc',str(pid),'task').iterdir()}==set(observers)
        for tid in observers:
            v=status(tid);assert birth(tid)==thread_births[tid] and v['state']=='t' and v['tracer_pid']==os.getpid() and v['tgid']==pid
        assert resource.prlimit(pid,resource.RLIMIT_NOFILE)==original
        fault={'observation':observed,'event':'fault-active','unit':unit,'mode':mode,'syscall':'openat','CA_path_matched':True,'threads':frozen,'audit':at_entry['test_audits'][-1],'native_before':before,'native_at_entry':at_entry,'original_limits':list(original),'entry_at_ns':time.time_ns()}
        atomic(folder,'fault-entry.json',fault)
        phase=7;resource.prlimit(pid,resource.RLIMIT_NOFILE,(0,original[1]));limit_changed=True
        assert resource.prlimit(pid,resource.RLIMIT_NOFILE)==(0,original[1])
        fault['limit_zero_at_ns']=time.time_ns()
        if mode=='rescue-window':
            atomic(folder,'fault-held.json',fault);emit(fault)
            # Deliberately leave all tracees stopped. A separate restorer stops
            # this helper, restores NOFILE, then terminates it; no self-KILL.
            while True:signal.pause()
        phase=8;main_observer.resume();assert main_observer.wait(deadline)==(signal.SIGTRAP|0x80)
        op,result=main_observer.info();fault.update(syscall_exit_at_ns=time.time_ns(),syscall_result=result)
        assert op==2 and result==-errno.EMFILE,'real_EMFILE_required'
        resource.prlimit(pid,resource.RLIMIT_NOFILE,original)
        assert resource.prlimit(pid,resource.RLIMIT_NOFILE)==original
        limit_changed=False;fault.update(limits_restored_at_ns=time.time_ns(),restored_limits=list(original),restored_before_Python=True)
        atomic(folder,'native-fault.json',fault);emit(fault)
    except BaseException as error:
        trace=error.__traceback__
        while trace and trace.tb_next:trace=trace.tb_next
        message=str(error)
        codes={'CA_open_not_observed','native_stop_not_observed','unexpected_control_signal','native_observation_failed','one_new_test_audit_required','CA_read_only_open_required','real_EMFILE_required','control_process_changed','control_pid_changed','control_generation_changed','unknown_guard_state'}
        filename=Path(trace.tb_frame.f_code.co_filename).name if trace else ''
        file_ids={'function-http-client-task-operator.py':'task_operator','native_control_observer.py':'native_observer','control_database.py':'control_database'}
        source={'file_id':file_ids.get(filename,'other'),'line':trace.tb_lineno} if trace else None
        if source and filename not in file_ids:source['filename_sha256']=hashlib.sha256(filename.encode()).hexdigest()
        failure_info={'event':'operator-failed','unit':unit,'phase':phase,'reason_code':message if message in codes else 'unclassified','failure_type':type(error).__name__,'message_sha256':hashlib.sha256(message.encode()).hexdigest(),'elapsed_ms':round((time.monotonic()-operation_started)*1000,3),'observation':observed,'limit_changed':limit_changed,'original_limits':list(original),'observers_registered':len(observers),'source':source}
        if isinstance(getattr(error,'errno',None),int):failure_info['errno']=error.errno
        raise
    finally:
        # Restoring the original resource takes precedence over detaching any
        # tracee, including if a native assertion failed after the syscall.
        if limit_changed:
            assert birth(pid)==item['birth'] and Path('/proc',str(pid),'cgroup').read_text()==item['cgroup']
            resource.prlimit(pid,resource.RLIMIT_NOFILE,original)
            assert resource.prlimit(pid,resource.RLIMIT_NOFILE)==original
        for obs in reversed(list(observers.values())):obs.detach()
        receipt=restored(folder,False) if armed else None
        states=finish_guard(unit) if armed else None
        if failure_info is not None:
            if receipt:
                failure_info.update(observed_limits_after_restore=receipt['limits_after'],restoration_known=receipt['completed'],threads_released=True)
            try:
                atomic(folder,'operator-failure.json',failure_info);emit(failure_info)
            except Exception:
                pass  # Diagnostic I/O must not replace the original exception.
        if receipt:
            emit(receipt)
            emit({'event':'guard-finished','unit':unit,'states':states})


if __name__=='__main__':main()
