# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
"""Independent DEV cut recovery: restart only the exact observed schema011 control."""
import datetime
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
import tempfile
import time
import urllib.request
from uuid import uuid4


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]


def identity(folder):
    info=folder.lstat()
    assert folder.parent==Path('/run') and re.fullmatch('serverless-restore-journal-cut-[0-9a-f]{32}',folder.name)
    assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
    path=folder/'identity.json';info=path.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<32768
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        assert os.fstat(fd)==info;item=json.loads(os.read(fd,32769))
    finally:os.close(fd)
    assert re.fullmatch('sha256:[0-9a-f]{64}',item['image']) and re.fullmatch('[0-9a-f]{64}',item['container_id'])
    assert isinstance(item['helper_pid'],int) and item['helper_pid']>1 and re.fullmatch('[0-9]+',item['helper_birth'])
    return item


def inspect(item,name):
    result=subprocess.run(item['docker']+['inspect',name],capture_output=True,text=True,check=True,timeout=10)
    return json.loads(result.stdout)[0]


def helper_fd(item):
    try:fd=os.pidfd_open(item['helper_pid'])
    except ProcessLookupError:return None
    try:
        if select.select([fd],[],[],0)[0] or birth(item['helper_pid'])!=item['helper_birth']:
            os.close(fd);return None
        assert sha(Path('/proc',str(item['helper_pid']),'cmdline'))==item['helper_command_sha256']
        assert next(row.split()[1] for row in Path('/proc',str(item['helper_pid']),'status').read_text().splitlines() if row.startswith('Uid:'))=='0'
        return fd
    except (FileNotFoundError,ProcessLookupError):os.close(fd);return None
    except BaseException:os.close(fd);raise


def write_receipt(folder,value):
    value.update(finished_at_ns=time.time_ns(),finished_monotonic_ns=time.monotonic_ns())
    with tempfile.NamedTemporaryFile(dir=folder,prefix='.restoration-pending-',delete=False) as stream:
        temporary=Path(stream.name);os.fchmod(stream.fileno(),0o600)
        stream.write((json.dumps(value)+'\n').encode());stream.flush();os.fsync(stream.fileno())
    try:os.link(temporary,folder/('restoration-receipt-'+uuid4().hex+'.json'))
    finally:temporary.unlink(missing_ok=True)


def command(item,args,timeout=30):
    return subprocess.run(item['docker']+args,capture_output=True,text=True,check=True,timeout=timeout).stdout


def started_ns(value):
    whole,fraction=value.removesuffix('Z').split('.')
    return int(datetime.datetime.strptime(whole,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp())*10**9+int(fraction.ljust(9,'0'))


def expired(signum,frame):raise TimeoutError('journal_control_restoration_deadline')


def restore(folder,rescue):
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
    item=identity(folder);helper=None;lock=None;phase='prepared'
    previous=signal.signal(signal.SIGALRM,expired);signal.alarm(180)
    result={'event':'restored','unit':folder.name,'completed':False,'independent':rescue,
        'container_id':item['container_id'],'image':item['image'],'started_at_before':item['started_at'],
        'database_restored':False,'started_at_ns':time.time_ns()}
    try:
        if rescue:
            phase='joining_owned_helper';helper=helper_fd(item)
            if helper is not None:
                try:signal.pidfd_send_signal(helper,signal.SIGKILL)
                except ProcessLookupError:pass
                assert select.select([helper],[],[],10)[0],'helper_exit_unconfirmed'
            result['helper_gone']=True
        phase='joining_stop_mutator'
        lock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_NOFOLLOW);info=os.fstat(lock)
        assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']
        end=time.monotonic()+40
        while True:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                assert time.monotonic()<end,'stop_mutator_not_joined';time.sleep(.1)
        if (folder/'kill-started.json').exists():
            cut=json.loads((folder/'kill-result.json').read_text())
            assert cut['completed'] and cut['docker_client_joined'] and cut['container_id']==item['container_id'] and cut['exit_code']==137,'stop_mutation_unknown'
            result['stop_receipt_sha256']=sha(folder/'kill-result.json')
        result['stop_mutator_joined']=True
        phase='checking_container_identity'
        current,reference=inspect(item,'serverless-api'),inspect(item,'serverless-runtime-reference')
        assert [current['Id'],current['Image']]==[item['container_id'],item['image']],'control_replaced'
        assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running'],'reference_changed'
        expected=item['started_at']
        prior=[json.loads(path.read_text()) for path in folder.glob('restoration-receipt-*.json')]
        for receipt in sorted(prior,key=lambda row:row['finished_monotonic_ns'],reverse=True):
            if receipt.get('completed'):
                assert receipt['container_id']==item['container_id'] and receipt['image']==item['image']
                expected=receipt['started_at'];break
        assert current['State']['StartedAt']==expected,'unowned_control_restart'
        if not current['State']['Running']:
            assert (folder/'kill-result.json').exists() and current['State']['ExitCode']==137,'unowned_control_stop'
            phase='restarting_same_schema011_image';requested=time.time_ns()
            command(item,['start',item['container_id']]);returned=time.time_ns()
            current=inspect(item,'serverless-api');expected=current['State']['StartedAt']
            assert requested<=started_ns(expected)<=returned,'new_generation_outside_start_window'
            result['own_start_window_ns']=[requested,returned]
        phase='checking_health';end=time.monotonic()+35
        while True:
            try:
                with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:
                    assert response.status==200 and json.load(response)['status']=='ok'
                current=inspect(item,'serverless-api');reference=inspect(item,'serverless-runtime-reference')
                assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy';break
            except (OSError,AssertionError):
                assert time.monotonic()<end,'control_health_not_restored';time.sleep(.2)
        assert [current['Id'],current['Image'],current['State']['StartedAt']]==[item['container_id'],item['image'],expected] and current['State']['Running']
        assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']
        result.update(healthy=True,reference_unchanged=True,started_at=expected)
        descendants=[current['State']['Pid']]
        for parent in descendants:descendants.extend(int(value) for value in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
        processes=[pid for pid in descendants if Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
        assert len(processes)==1
        threads=[]
        for path in Path('/proc',str(processes[0]),'task').iterdir():
            try:
                rows=dict(line.split(':',1) for line in (path/'status').read_text().splitlines() if ':' in line)
                row={'tid':int(path.name),'birth':birth(int(path.name)),'state':rows['State'].split()[0],'tracer_pid':int(rows['TracerPid'])}
            except (FileNotFoundError,ProcessLookupError):continue
            assert row['tracer_pid']==0 and row['state'] not in ('t','T'),'control_thread_not_released'
            threads.append(row)
        assert threads;result['threads']=threads
        phase='attesting_sources_and_configuration'
        assert sha(Path(__file__))==item['restore_sha256']
        for key in ('official_sha256','program_sha256'):
            assert {name:sha(name) for name in item[key]}==item[key]
        result['completed']=True;write_receipt(folder,result);return result
    except BaseException as error:
        result.update(event='restoration-failed',phase=phase,failure_type=type(error).__name__)
        # Full source/configuration attestation can fail, but it must never leave
        # this already recognized tracer alive and retaining the HTTP process.
        if rescue and helper is not None:
            try:
                if not select.select([helper],[],[],0)[0]:signal.pidfd_send_signal(helper,signal.SIGKILL)
                result['helper_joined_on_failure']=bool(select.select([helper],[],[],5)[0])
            except ProcessLookupError:result['helper_joined_on_failure']=True
        write_receipt(folder,result);raise
    finally:
        if lock is not None:os.close(lock)
        if helper is not None:os.close(helper)
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)


if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[2] in ('check','recover')
    print(json.dumps(restore(Path(sys.argv[1]),sys.argv[2]=='recover')),flush=True)
