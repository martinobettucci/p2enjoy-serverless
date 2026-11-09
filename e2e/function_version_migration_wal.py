# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#verrou-et-interruption-native
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#verrou-et-interruption-native
"""Observe real private SQLite WAL writes, with an independent bounded cleanup guard."""
from contextlib import contextmanager
import fcntl,hashlib,json,os,re,signal,socket,stat,subprocess,time
from pathlib import Path
from uuid import uuid4
from native_control_observer import NativeObserver

ROOT=Path('/srv/p2enjoy-serverless')
def command(args,timeout=30):
    value=subprocess.run(args,capture_output=True,text=True,timeout=timeout,cwd=ROOT)
    assert value.returncode==0,'wal_operator_command_failed'
    return value.stdout.strip()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def process_state(pid):return next(v.split(':',1)[1].strip().split()[0] for v in Path('/proc',str(pid),'status').read_text().splitlines() if v.startswith('State:'))
def write(path,value):
    pending=path.with_name(path.name+'.pending')
    with pending.open('w') as stream:json.dump(value,stream);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    pending.replace(path)
def inspect(docker,record,image,nonce):
    p=subprocess.run(docker+['container','inspect',record['id']],capture_output=True,text=True,timeout=25,cwd=ROOT)
    if p.returncode:
        assert p.returncode==1 and p.stdout.strip()=='[]' and p.stderr.strip()=='Error response from daemon: No such container: '+record['id'],'wal_container_absence_unconfirmed'
        return None
    values=json.loads(p.stdout);assert len(values)==1;value=values[0]
    assert value['Id']==record['id'] and value['Name']=='/'+record['name'] and value['Image']==image
    assert re.fullmatch(r'serverless-migration008-wal-interruption-[0-9a-f]{8}',record['name'])
    labels=value['Config']['Labels'];assert labels['tech.p2enjoy.serverless.migration-proof']==nonce and labels['com.docker.compose.project']=='serverless-migration008-'+nonce and labels['com.docker.compose.service']=='control'
    assert [v['Source'] for v in value['Mounts'] if v['Destination']=='/state']==[record['directory']]
    assert all(v['Destination'] in ('/state','/tmp') for v in value['Mounts']) and value['HostConfig']['NetworkMode']=='none' and not value['HostConfig']['PortBindings']
    assert not value['HostConfig'].get('Init') and value['HostConfig']['ReadonlyRootfs']
    return value

def stopped_start_command(docker,image):
    value=json.loads(command(docker+['image','inspect',image]))[0]
    assert value['Id']==image and not value['Config'].get('Entrypoint')
    args=value['Config']['Cmd'];assert args[:5]==['python','-B','-m','uvicorn','app.main:app'] and args[args.index('--workers')+1]=='1'
    source='\n'.join(['import os,signal,sys','child=os.fork()','if child==0:',' os.kill(os.getpid(),signal.SIGSTOP)',' os.execvp('+repr(args[0])+','+repr(args)+')','else:',' _,status=os.waitpid(child,0)',' sys.exit(os.WEXITSTATUS(status) if os.WIFEXITED(status) else 128+os.WTERMSIG(status))'])
    return ['python','-B','-c',source]

def stopped_writer(docker,record,image,nonce):
    end=time.monotonic()+10
    while True:
        value=inspect(docker,record,image,nonce);assert value and value['State']['Running']
        init=value['State']['Pid'];children=Path('/proc',str(init),'task',str(init),'children').read_text().split();assert len(children)<=1,'ambiguous_private_writer'
        if children:
            pid=int(children[0]);identity=birth(pid)
            if process_state(pid)=='T':break
        assert time.monotonic()<end,'private_writer_not_stopped';time.sleep(.02)
    assert pid!=init and value['Config']['Cmd']==stopped_start_command(docker,image)
    args=Path('/proc',str(pid),'cmdline').read_bytes().split(bytes([0]));assert args[-1]==b'' and args[:-1]==[v.encode() for v in value['Config']['Cmd']]
    assert Path('/proc',str(pid),'cgroup').read_text()==Path('/proc',str(init),'cgroup').read_text()
    assert int(next(v.split(':',1)[1].strip() for v in Path('/proc',str(pid),'status').read_text().splitlines() if v.startswith('PPid:')))==init
    return value,init,pid,identity

def resume_wrapper(docker,record,image,nonce):
    value,init,pid,identity=stopped_writer(docker,record,image,nonce)
    assert birth(pid)==identity;os.kill(pid,signal.SIGCONT)
    return {'pid':pid,'birth':identity,'container_init_pid':init,'signal':signal.SIGCONT}

CLEANUP=r'''import fcntl,hashlib,json,os,select,signal,socket,stat,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(45)
folder=Path(sys.argv[1]);info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith('serverless-cleanup-migration-wal-') and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
for name in ('identity.json','cleanup.py','lock'):assert not (folder/name).is_symlink()
item=json.loads((folder/'identity.json').read_text());assert hashlib.sha256((folder/'cleanup.py').read_bytes()).hexdigest()==item['cleanup_sha256']
fd=os.open(folder/'lock',os.O_RDWR|os.O_NOFOLLOW);value=os.fstat(fd);assert [value.st_dev,value.st_ino]==item['lock_identity'] and value.st_uid==0;fcntl.flock(fd,fcntl.LOCK_EX)
try:
 if (folder/'finished.json').exists():
  result=json.loads((folder/'finished.json').read_text());assert result['absence_confirmed'] and (result['container_removed'] or result['container_already_absent']) and result['container_id']==item['record']['id']
  print(json.dumps({'completed':True,'normal_cleanup_already_confirmed':True,'container_removed':result['container_removed'],'container_already_absent':result['container_already_absent'],'container_id':item['record']['id']}));sys.exit(0)
 record=item['record'];docker=item['docker']
 def inspected():
  p=subprocess.run(docker+['container','inspect',record['id']],capture_output=True,text=True,timeout=20,cwd='/srv/p2enjoy-serverless')
  if p.returncode:
   assert p.returncode==1 and p.stdout.strip()=='[]' and p.stderr.strip()=='Error response from daemon: No such container: '+record['id'],'private_container_absence_unconfirmed'
   return None
  value=json.loads(p.stdout)[0];assert value['Id']==record['id'] and value['Name']=='/'+record['name'] and value['Image']==item['image']
  labels=value['Config']['Labels'];assert labels['tech.p2enjoy.serverless.migration-proof']==item['nonce'] and labels['com.docker.compose.project']=='serverless-migration008-'+item['nonce'] and labels['com.docker.compose.service']=='control'
  assert [v['Source'] for v in value['Mounts'] if v['Destination']=='/state']==[record['directory']]
  assert all(v['Destination'] in ('/state','/tmp') for v in value['Mounts']) and value['HostConfig']['NetworkMode']=='none' and not value['HostConfig']['PortBindings']
  return value
 current=inspected();result={'completed':False,'independent':True,'container_id':record['id'],'observer_pid':item['observer_pid']}
 if current is not None:
  try:process=os.pidfd_open(item['observer_pid'])
  except ProcessLookupError:result['observer_already_absent']=True
  else:
   try:
    pid=item['observer_pid'];born=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
    if born==item['observer_birth']:
     assert hashlib.sha256(Path('/proc',str(pid),'cmdline').read_bytes()).hexdigest()==item['observer_argv_sha256'],'observer_identity_changed'
     signal.pidfd_send_signal(process,signal.SIGKILL);assert select.select([process],[],[],10)[0],'observer_death_unconfirmed';result['observer_killed']=True
    else:result['observer_pid_reused_not_signaled']=True
   except (FileNotFoundError,ProcessLookupError):result['observer_already_absent']=True
   finally:os.close(process)
  assert inspected() is not None
  p=subprocess.run(docker+['rm','-f',record['id']],capture_output=True,text=True,timeout=25,cwd='/srv/p2enjoy-serverless');assert p.returncode==0,'private_container_remove_failed'
  assert inspected() is None;result['container_removed']=True
 else:result['container_already_absent']=True
 result['completed']=True;pending=folder/'independent.pending';pending.write_text(json.dumps(result));pending.replace(folder/'independent.json');print(json.dumps(result),flush=True)
finally:os.close(fd)
'''

def unit_states(unit):
    result={}
    for suffix in ('timer','service'):
        p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=LoadState','--property=ActiveState','--property=MainPID'],capture_output=True,text=True,timeout=10)
        result[suffix]=dict(v.split('=',1) for v in p.stdout.splitlines())
    return result

def trace_and_kill(docker,record,image,nonce,observer,folder):
    value,init,pid,born=stopped_writer(docker,record,image,nonce)
    assert observer.pid==pid
    assert set(v.name for v in Path('/proc',str(pid),'task').iterdir())=={str(pid)}
    cgroup=Path('/proc',str(pid),'cgroup').read_text();wal=Path(record['directory'])/'control.sqlite3-wal'
    database=Path(record['directory'])/'control.sqlite3'
    with database.open('rb') as stream:header=stream.read(100)
    assert header[:16]==b'SQLite format 3\x00';page_size=int.from_bytes(header[16:18],'big');page_size=65536 if page_size==1 else page_size
    assert 512<=page_size<=65536 and page_size&(page_size-1)==0
    observer.start();os.kill(pid,signal.SIGCONT);observer.resume();deadline=time.monotonic()+140;pending=None;frame=None;calls=0;exec_completed=False;memory_refreshed=False
    while frame is None:
        stopped=observer.wait(deadline)
        if stopped!=signal.SIGTRAP|0x80:
            assert stopped in (signal.SIGTRAP,signal.SIGCONT,signal.SIGSTOP),'unexpected_private_process_signal'
            observer.resume(signal.SIGCONT if stopped==signal.SIGCONT else 0);continue
        phase,data=observer.info()
        if phase==1:
            number,*args=data;pending={'number':number,'args':args};calls+=1
            if number==18 and args[2]==24 and args[3]>=32 and (args[3]-32)%(page_size+24)==0 and wal.exists():
                target=os.stat('/proc/'+str(pid)+'/fd/'+str(args[0]));actual=wal.lstat()
                if [target.st_dev,target.st_ino]==[actual.st_dev,actual.st_ino]:
                    assert stat.S_ISREG(actual.st_mode) and actual.st_uid==1001
                    assert exec_completed,'writer_exec_not_observed'
                    if not memory_refreshed:
                        previous=observer.memory;observer.memory=None;os.close(previous)
                        observer.memory=os.open('/proc/'+str(pid)+'/mem',os.O_RDONLY);memory_refreshed=True
                    raw=os.pread(observer.memory,24,args[1]);assert len(raw)==24
                    page,commit=int.from_bytes(raw[:4],'big'),int.from_bytes(raw[4:8],'big')
                    if page>0 and commit==0:pending['frame']={'page':page,'commit_size':commit,'fd':args[0],'offset':args[3],'identity':[actual.st_dev,actual.st_ino],'header':raw.hex()}
        elif phase==2 and pending:
            if pending['number']==59 and data==0:exec_completed=True
            if 'frame' in pending:
                assert data==24,'wal_frame_write_not_completed'
                frame=pending['frame'];frame['syscall_return']=data
                descriptor=os.open(wal,os.O_RDONLY|os.O_NOFOLLOW)
                try:
                    info=os.fstat(descriptor);assert [info.st_dev,info.st_ino]==frame['identity'];assert os.pread(descriptor,24,frame['offset']).hex()==frame.pop('header')
                finally:os.close(descriptor)
                assert birth(pid)==born and Path('/proc',str(pid),'cgroup').read_text()==cgroup
                assert set(v.name for v in Path('/proc',str(pid),'task').iterdir())=={str(pid)}
                assert next(v.split(':',1)[1].strip() for v in Path('/proc',str(pid),'status').read_text().splitlines() if v.startswith('TracerPid:'))==str(os.getpid())
                break
            pending=None
        observer.resume()
    boundary={'pid':pid,'birth':born,'container_init_pid':init,'writer_is_child':True,'container_id':record['id'],'page_size':page_size,'frame':frame,'syscall_entries_observed':calls,'observed_at_ns':str(time.time_ns()),'single_thread':True,'exec_observed':exec_completed,'memory_view_reopened_after_exec':memory_refreshed,'application_buffers_unchanged':True}
    write(folder/'boundary.json',boundary)
    current=inspect(docker,record,image,nonce);assert current['State']['Pid']==init and current['State']['Running']
    killer=subprocess.Popen(docker+['kill','--signal','KILL',record['id']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT)
    try:
        end=time.monotonic()+20
        while True:
            child,status=os.waitpid(pid,os.WNOHANG)
            if child:break
            assert time.monotonic()<end,'private_process_death_not_observed';time.sleep(.01)
        assert child==pid and os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL
        stdout,stderr=killer.communicate(timeout=25);assert killer.returncode==0 and stdout.strip()==record['id'],'private_docker_kill_failed'
    finally:
        if killer.poll() is None:killer.kill();killer.communicate(timeout=10)
    observer.detach()
    stopped=inspect(docker,record,image,nonce);assert not stopped['State']['Running'] and stopped['State']['ExitCode']==137
    result={'boundary':boundary,'native_death':{'pid':pid,'birth':born,'signaled':True,'signal':9},'docker_exit_code':137,'same_container_id':stopped['Id']}
    write(folder/'interrupted.json',result);return result

@contextmanager
def interrupted_wal_copy(docker,record,image,nonce):
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
    assert re.fullmatch(r'[0-9a-f]{8}',nonce) and re.fullmatch(r'sha256:[0-9a-f]{64}',image)
    path=Path(record['directory']);assert path.name=='wal-interruption' and path.parent.parent==ROOT/'control' and path.parent.name.startswith('function-version-migration008-') and path.resolve()==path
    value,init,pid,born=stopped_writer(docker,record,image,nonce)
    unit='serverless-cleanup-migration-wal-'+uuid4().hex;folder=Path('/run')/unit;folder.mkdir(mode=0o700)
    lock=os.open(folder/'lock',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);info=os.fstat(lock);os.close(lock)
    item={'record':record.copy(),'image':image,'nonce':nonce,'docker':docker,'observer_pid':os.getpid(),'observer_birth':birth(os.getpid()),'observer_argv_sha256':hashlib.sha256(Path('/proc/self/cmdline').read_bytes()).hexdigest(),'lock_identity':[info.st_dev,info.st_ino],'cleanup_sha256':hashlib.sha256(CLEANUP.encode()).hexdigest()}
    write(folder/'identity.json',item);(folder/'cleanup.py').write_text(CLEANUP);observer=NativeObserver(pid);proof={'unit':unit,'identity':item,'arming_response_known':False}
    try:
        command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=180s','--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=50s','/usr/bin/python3','-I',str(folder/'cleanup.py'),str(folder)])
        proof['arming_response_known']=True;assert unit_states(unit)['timer']['ActiveState']=='active'
        print(json.dumps({'event':'wal-guard-armed','unit':unit,'container_id':record['id']}),flush=True)
        proof.update(trace_and_kill(docker,record,image,nonce,observer,folder));yield proof
    finally:
        observer.detach()
        descriptor=os.open(folder/'lock',os.O_RDWR|os.O_NOFOLLOW)
        try:
            fcntl.flock(descriptor,fcntl.LOCK_EX);current=inspect(docker,record,image,nonce)
            if current is not None:command(docker+['rm','-f',record['id']]);assert inspect(docker,record,image,nonce) is None
            terminal={'container_removed':current is not None,'container_already_absent':current is None,'absence_confirmed':True,'container_id':record['id'],'normal':True,'completed_at_ns':str(time.time_ns())};write(folder/'finished.json',terminal)
            p=subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,text=True,timeout=10)
            state=unit_states(unit);assert p.returncode==0 or p.returncode==5 and state['timer']['LoadState']=='not-found'
        finally:os.close(descriptor)
        end=time.monotonic()+20
        while True:
            states=unit_states(unit)
            if all(v['ActiveState']=='inactive' for v in states.values()):break
            assert time.monotonic()<end,'wal_cleanup_guard_not_terminal';time.sleep(.1)
        assert states['service'].get('MainPID')=='0' or states['service']['LoadState']=='not-found'
        proof.update(container_removed=terminal['container_removed'],container_already_absent=terminal['container_already_absent'],absence_confirmed=True,guard_states=states,finished=terminal)
