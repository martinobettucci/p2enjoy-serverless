# @spec docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
"""Frozen independent DEV reader-tracer restoration; never restarts the control."""
import hashlib,json,os,re,resource,select,signal,socket,stat,subprocess,sys,tempfile,time,urllib.error,urllib.request
from pathlib import Path
from uuid import uuid4


def birth(pid):
    return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]


def status(pid):
    values=dict(line.split(':',1) for line in Path('/proc',str(pid),'status').read_text().splitlines() if ':' in line)
    return {'state':values['State'].split()[0],'tracer_pid':int(values['TracerPid']),'tgid':int(values['Tgid'])}


def read_identity(folder):
    info=folder.lstat()
    assert folder.parent==Path('/run') and re.fullmatch('serverless-restore-journal-sql-[0-9a-f]{32}',folder.name)
    assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
    path=folder/'identity.json';info=path.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<32768
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        assert os.fstat(fd)==info,'identity_changed_during_open'
        item=json.loads(os.read(fd,32769))
    finally:os.close(fd)
    assert isinstance(item['helper_pid'],int) and item['helper_pid']>1 and re.fullmatch('[0-9]+',item['helper_birth'])
    assert re.fullmatch('[0-9a-f]{64}',item['helper_command_sha256'])
    return item


def attest(item):
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==item['restore_sha256']
    for field in ('program_sha256','official_sha256'):
        assert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in item[field]}==item[field]


def inspect(item,name):
    result=subprocess.run(item['docker']+['inspect',name],capture_output=True,text=True,check=True,timeout=5)
    return json.loads(result.stdout)[0]


def owner(item):
    assert birth(item['pid'])==item['birth'],'control_pid_changed'
    assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_cgroup_changed'
    current=inspect(item,'serverless-api');reference=inspect(item,'serverless-runtime-reference')
    assert [current['Id'],current['Image'],current['State']['StartedAt']]==[item['container_id'],item['image'],item['started_at']] and current['State']['Running'],'control_generation_changed'
    assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running'],'reference_changed'
    return current,reference


def helper_fd(item):
    try:
        fd=os.pidfd_open(item['helper_pid'])
    except ProcessLookupError:
        return None
    try:
        if select.select([fd],[],[],0)[0]:
            os.close(fd);return None
        if birth(item['helper_pid'])!=item['helper_birth']:
            os.close(fd);return None  # The original helper exited; never signal its successor.
        command=Path('/proc',str(item['helper_pid']),'cmdline').read_bytes()
        assert hashlib.sha256(command).hexdigest()==item['helper_command_sha256'],'helper_command_changed'
        assert next(line.split()[1] for line in Path('/proc',str(item['helper_pid']),'status').read_text().splitlines() if line.startswith('Uid:'))=='0'
        return fd
    except (FileNotFoundError,ProcessLookupError):
        os.close(fd);return None
    except BaseException:
        os.close(fd);raise


def record_receipt(folder,result):
    # Exclusive publication preserves every terminal attempt. Ordering uses the
    # host monotonic clock, not filesystem scheduling or a mutable latest file.
    result.update(finished_at_ns=time.time_ns(),finished_monotonic_ns=time.monotonic_ns())
    target=folder/('restoration-receipt-'+uuid4().hex+'.json')
    with tempfile.NamedTemporaryFile(dir=folder,prefix='.restoration-pending-',delete=False) as stream:
        pending=Path(stream.name)
        stream.write((json.dumps(result)+'\n').encode());stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o600)
    try:
        os.link(pending,target)  # Atomic, and refuses to replace an existing receipt.
    finally:pending.unlink(missing_ok=True)


class RestorationDeadline(RuntimeError):
    """Global guard expiry, distinct from an individual network timeout."""


def alarm_expired(signum,frame):
    raise RestorationDeadline('restoration_deadline')


def restore_limits(item):
    assert birth(item['pid'])==item['birth']
    assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup']
    assert Path('/proc',str(item['pid']),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')
    current=resource.prlimit(item['pid'],resource.RLIMIT_NOFILE)
    if list(current)!=item['limits_nofile']:
        assert item['barrier']=='fault' and list(current)==[0,item['limits_nofile'][1]],'foreign_resource_limit'
        resource.prlimit(item['pid'],resource.RLIMIT_NOFILE,tuple(item['limits_nofile']))
    assert list(resource.prlimit(item['pid'],resource.RLIMIT_NOFILE))==item['limits_nofile']


def restore(folder,rescue,diagnostic_failure=False):
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
    item=read_identity(folder);fd=None;own_limits=None
    started=time.monotonic();restoration_deadline=started+55
    previous_alarm=signal.signal(signal.SIGALRM,alarm_expired);signal.alarm(55)
    phase='prepared'
    result={'attempt_id':uuid4().hex,'started_at_ns':time.time_ns(),'event':'restored','independent':rescue,'unit':folder.name,'pid':item['pid'],'birth':item['birth'],'container_id':item['container_id'],'image':item['image'],'started_at':item['started_at'],'cgroup_sha256':hashlib.sha256(item['cgroup'].encode()).hexdigest()}
    try:
        restorer_cgroup=Path('/proc/self/cgroup').read_text()
        guard_unit=folder.name+'.service'
        in_guard=any(line.split(':',2)[-1].rstrip('/').split('/')[-1]==guard_unit for line in restorer_cgroup.splitlines())
        result.update(restorer_pid=os.getpid(),restorer_birth=birth(os.getpid()),
            restorer_cgroup_sha256=hashlib.sha256(restorer_cgroup.encode()).hexdigest(),
            restorer_systemd_unit=guard_unit if in_guard else None,
            restoration_origin='systemd_guard' if in_guard else 'operator')
        if rescue:
            phase='stopping_helper';fd=helper_fd(item)
            if fd is not None:
                try:
                    signal.pidfd_send_signal(fd,signal.SIGSTOP)
                    result['helper_stop_requested_at_ns']=time.time_ns()
                except ProcessLookupError:
                    result['helper_exit_during_stop']=True
                deadline=time.monotonic()+2
                while not select.select([fd],[],[],0)[0]:
                    try:
                        if birth(item['helper_pid'])!=item['helper_birth']:
                            result['helper_original_exited']=True;break
                        if status(item['helper_pid'])['state']=='T':
                            result['helper_stopped_at_ns']=time.time_ns();break
                    except (FileNotFoundError,ProcessLookupError):
                        result['helper_exit_during_stop']=True;break
                    assert time.monotonic()<deadline,'helper_stop_unconfirmed'
                    time.sleep(.005)
                if select.select([fd],[],[],0)[0]:result['helper_exited_before_restore']=True
            else:result['helper_already_gone']=True
        phase='restoring_reader_resources'
        restore_limits(item);result['limits_nofile_restored']=True
        phase='joining_helper'
        if fd is not None:
            if not select.select([fd],[],[],0)[0]:
                try:
                    signal.pidfd_send_signal(fd,signal.SIGKILL)
                    result['helper_killed_at_ns']=time.time_ns()
                except ProcessLookupError:result['helper_exit_before_kill']=True
            assert select.select([fd],[],[],5)[0],'helper_exit_unconfirmed'
            result['helper_joined_at_ns']=time.time_ns()
        result['helper_gone']=rescue
        phase='attesting_sources_and_configuration'
        attest(item)
        phase='validating_owner'
        if diagnostic_failure:
            own_limits=resource.getrlimit(resource.RLIMIT_NOFILE)
            resource.setrlimit(resource.RLIMIT_NOFILE,(0,own_limits[1]))
        owner(item)
        phase='joining_threads'
        deadline=time.monotonic()+10
        while True:
            threads=[]
            for path in Path('/proc',str(item['pid']),'task').iterdir():
                try:threads.append({'tid':int(path.name),'birth':birth(int(path.name)),**status(int(path.name))})
                except (FileNotFoundError,ProcessLookupError):pass
            if threads and all(v['tracer_pid']==0 and v['state'] not in ('t','T') and v['tgid']==item['pid'] for v in threads):break
            assert time.monotonic()<deadline,'threads_not_released'
            time.sleep(.02)
        result['threads']=threads
        phase='checking_health';result['health_checks']=[];result['health_checks_overflow']=0
        while True:
            remaining=restoration_deadline-time.monotonic()
            if remaining<=0:raise RestorationDeadline('restoration_health_deadline')
            probe={'at_ns':time.time_ns(),'http_status':None}
            try:
                try:
                    with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=min(5,remaining)) as response:
                        probe['http_status']=response.status
                except (urllib.error.URLError,OSError,TimeoutError) as error:
                    probe['failure_type']=type(error).__name__
                    if isinstance(getattr(error,'code',None),int):probe['http_status']=error.code
                if time.monotonic()>=restoration_deadline:raise RestorationDeadline('restoration_health_deadline')
                current,reference=owner(item)
                probe.update(api_health=current['State']['Health']['Status'],reference_health=reference['State']['Health']['Status'])
            except BaseException as error:
                probe.setdefault('failure_type',type(error).__name__);raise
            finally:
                if len(result['health_checks'])<128:result['health_checks'].append(probe)
                else:result['health_checks_overflow']+=1
                result['last_health_check']=probe
            if probe['http_status']==200 and probe['api_health']==probe['reference_health']=='healthy':break
            remaining=restoration_deadline-time.monotonic()
            if remaining<=0:raise RestorationDeadline('restoration_health_deadline')
            time.sleep(min(.2,remaining))
        result.update(healthy=True,reference_unchanged=True,completed=True)
        record_receipt(folder,result)
        return result
    except BaseException as error:
        if own_limits is not None:
            resource.setrlimit(resource.RLIMIT_NOFILE,own_limits)
            result['own_nofile_restored']=list(resource.getrlimit(resource.RLIMIT_NOFILE))==list(own_limits)
            own_limits=None
        result.update(completed=False,phase=phase,failure_type=type(error).__name__)
        if isinstance(getattr(error,'errno',None),int):result['errno']=error.errno
        # Only the exact helper is owned by this guard. Release its tracees even
        # if owner validation or the stop acknowledgement failed; never leave a
        # stopped tracer alive because application diagnostics are unavailable.
        if rescue and fd is not None:
            try:
                restore_limits(item);result['limits_nofile_restored_on_failure']=True
            except (OSError,AssertionError):result['limits_restoration_unconfirmed']=True
            try:
                if not select.select([fd],[],[],0)[0]:signal.pidfd_send_signal(fd,signal.SIGKILL)
                result['helper_joined_on_failure']=bool(select.select([fd],[],[],5)[0])
            except ProcessLookupError:result['helper_joined_on_failure']=True
        try:
            if birth(item['pid'])==item['birth'] and Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup']:
                result['control_identity_preserved_on_failure']=True
            if fd is not None:result['helper_exit_observed_on_failure']=bool(select.select([fd],[],[],0)[0])
        except (OSError,AssertionError):result['failure_observation_unavailable']=True
        result['event']='restoration-failed';record_receipt(folder,result)
        # A journalled identifier ties a failed receipt to its actual systemd unit too.
        if not diagnostic_failure:
            print(json.dumps({key:result.get(key) for key in ('event','unit','attempt_id','completed','phase',
                'restorer_pid','restorer_birth','restorer_cgroup_sha256','restorer_systemd_unit','restoration_origin')}),flush=True)
        raise
    finally:
        if own_limits is not None:resource.setrlimit(resource.RLIMIT_NOFILE,own_limits)
        signal.alarm(0);signal.signal(signal.SIGALRM,previous_alarm)
        if fd is not None:os.close(fd)


if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[2] in ('check','recover','recover-low-fds')
    folder=Path(sys.argv[1]);fault=sys.argv[2]=='recover-low-fds'
    try:value=restore(folder,sys.argv[2]!='check',fault)
    except OSError as error:
        assert fault and error.errno==24
        receipts=[json.loads(p.read_text()) for p in folder.glob('restoration-receipt-*.json')]
        value=max(receipts,key=lambda v:v['finished_monotonic_ns'])
        assert value['event']=='restoration-failed' and value['errno']==24 and value['own_nofile_restored'] and value['helper_gone']
    print(json.dumps(value),flush=True)
