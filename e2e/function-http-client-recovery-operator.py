# @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER_FAILURES.md#coupure-réelle-du-contrôle
# @verifies docs/CONSOLE_TESTER_FAILURES.md#coupure-réelle-du-contrôle
# @verifies docs/CONSOLE_TESTER_LOADING.md#décision-avant-code
"""Guarded real DEV interruption after the runtime confirms handler start."""
from contextlib import closing
import fcntl,hashlib,json,os,re,select,signal,socket,sqlite3,subprocess,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control,control_owner,ControlWriter
from native_control_observer import NativeObserver

def emit(value):print(json.dumps(value),flush=True)
def command(args,timeout=35,**kwargs):
 value=subprocess.run(args,capture_output=True,text=True,timeout=timeout,**kwargs)
 assert value.returncode==0,'operator_command_failed'
 return value.stdout.strip()
def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_command(limit,seconds):
 data=bytearray();deadline=time.monotonic()+seconds
 while True:
  remaining=deadline-time.monotonic();assert remaining>0,'command_deadline'
  assert select.select([sys.stdin.fileno()],[],[],remaining)[0],'command_deadline'
  part=os.read(sys.stdin.fileno(),limit+1-len(data));assert part,'command_eof'
  data.extend(part);assert len(data)<=limit,'command_limit'
  if b'\n' in data:
   assert data.endswith(b'\n') and data.count(b'\n')==1,'single_command_required'
   return bytes(data)

RESTORE="import datetime,fcntl,hashlib,json,os,select,signal,socket,sqlite3,stat,subprocess,sys,time,urllib.request\nfrom pathlib import Path\nassert os.geteuid()==0 and socket.gethostname()=='infra-serverless'\nsignal.alarm(180)\nfolder=Path(sys.argv[1]);info=folder.lstat()\nassert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-http-client-')\nassert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700\nitem=json.loads((folder/'identity.json').read_text());independent=len(sys.argv)>2\nassert hashlib.sha256((folder/'restore.py').read_bytes()).hexdigest()==item['restore_sha256']\nassert {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in item['official_sha256']}==item['official_sha256']\nassert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in item['program_sha256']}==item['program_sha256'],'operator_program_changed'\nresult={'event':'restored','independent':independent,'container_id':item['container_id'],'image':item['image']}\nif independent:\n try:fd=os.pidfd_open(item['helper_pid'])\n except ProcessLookupError:pass\n else:\n  try:\n   row=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()\n   if row[19]==item['helper_birth']:\n    signal.pidfd_send_signal(fd,signal.SIGKILL)\n    ready,_,_=select.select([fd],[],[],10);assert ready,'observer_stop_unconfirmed'\n    result['observer_killed']=True\n  except (ProcessLookupError,FileNotFoundError):pass\n  finally:os.close(fd)\n result['observer_gone']=True\nlock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_NOFOLLOW)\ntry:\n info=os.fstat(lock);assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']\n deadline=time.monotonic()+40\n while True:\n  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break\n  except BlockingIOError:\n   assert time.monotonic()<deadline,'stop_mutator_not_joined';time.sleep(.1)\n if (folder/'kill-started.json').exists():\n  proof=json.loads((folder/'kill-result.json').read_text());assert proof['completed'] and proof['docker_client_joined'] and proof['exit_code']==137 and proof['container_id']==item['container_id'],'stop_mutation_outcome_unknown'\n  result['stop_receipt_sha256']=hashlib.sha256((folder/'kill-result.json').read_bytes()).hexdigest()\n def inspect(name):\n  return json.loads(subprocess.run(item['docker']+['inspect',name],check=True,capture_output=True,text=True,timeout=30).stdout)[0]\n current=inspect('serverless-api');assert current['Id']==item['container_id'] and current['Image']==item['image'],'control_replaced'\n expected_started_at=item['started_at']\n for name in ('restored.json','restored-independent.json'):\n  receipt_path=folder/name\n  if receipt_path.exists():\n   prior=json.loads(receipt_path.read_text());assert prior['container_id']==item['container_id'] and prior['image']==item['image'] and prior['healthy'],'invalid_restore_receipt'\n   expected_started_at=prior['started_at']\n   if current['State']['StartedAt']==expected_started_at:break\n assert current['State']['StartedAt']==expected_started_at,'unowned_control_restart'\n result['generation_before']=expected_started_at\n if (folder/'native-cut.json').exists():\n  result['native_receipt_sha256']=hashlib.sha256((folder/'native-cut.json').read_bytes()).hexdigest()\n else:result['native_receipt_sha256']=None\n reference=inspect('serverless-runtime-reference');assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'],'reference_replaced'\n result['original_process']={'pid':item['pid'],'birth':item['birth'],'alive':False,'cgroup_sha256':hashlib.sha256(item['cgroup'].encode()).hexdigest()}\n try:fd=os.pidfd_open(item['pid'])\n except ProcessLookupError:pass\n else:\n  try:\n   row=Path('/proc',str(item['pid']),'stat').read_text().rsplit(')',1)[1].split()\n   assert row[19]==item['birth'],'control_pid_reused'\n   assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_owner_changed'\n   tracer=int(next(line.split()[1] for line in Path('/proc',str(item['pid']),'status').read_text().splitlines() if line.startswith('TracerPid:')))\n   assert tracer==0,'control_still_traced'\n   result['original_process'].update(alive=True,tracer_pid=tracer)\n   signal.pidfd_send_signal(fd,signal.SIGCONT)\n  except (FileNotFoundError,ProcessLookupError):pass\n  finally:os.close(fd)\n result['was_running']=current['State']['Running'];result['exit_code_before']=current['State']['ExitCode']\n if not current['State']['Running']:\n  assert (folder/'kill-result.json').exists() and current['State']['ExitCode']==137,'unowned_control_stop'\n  start_before=time.time_ns()\n  subprocess.run(item['docker']+['start',item['container_id']],check=True,capture_output=True,timeout=30)\n  start_returned=time.time_ns()\n  restarted=inspect('serverless-api');assert restarted['Id']==item['container_id'] and restarted['Image']==item['image'] and restarted['State']['Running'],'control_start_failed'\n  expected_started_at=restarted['State']['StartedAt']\n  whole,fraction=expected_started_at.removesuffix('Z').split('.')\n  started_ns=int(datetime.datetime.strptime(whole,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp())*1000000000+int(fraction.ljust(9,'0'))\n  assert start_before<=started_ns<=start_returned,'unowned_control_start_generation'\n  result['own_start_window_ns']=[start_before,start_returned]\n deadline=time.monotonic()+35\n while True:\n  try:\n   with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:assert response.status==200\n   current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')\n   assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'\n   assert current['State']['StartedAt']==expected_started_at,'control_generation_changed_during_health'\n   break\n  except (OSError,AssertionError):\n   assert time.monotonic()<deadline,'control_health_not_restored';time.sleep(.2)\n current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')\n assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running'] and current['State']['StartedAt']==expected_started_at,'control_generation_changed_before_receipt'\n assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']\n result.update(healthy=True,reference_unchanged=True,stop_mutator_joined=True,started_at=current['State']['StartedAt'])\n name='restored-independent.json' if independent else 'restored.json'\n pending=folder/(name+'.pending');pending.write_text(json.dumps(result)+'\\n');pending.replace(folder/name)\n print(json.dumps(result),flush=True)\nfinally:os.close(lock)\n"

KILL_CONTROL="import fcntl,hashlib,json,os,signal,socket,stat,subprocess,sys\nfrom pathlib import Path\nassert os.geteuid()==0 and socket.gethostname()=='infra-serverless'\nsignal.alarm(45)\nfolder=Path(sys.argv[1]);fd=int(sys.argv[2]);info=folder.lstat()\nassert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-http-client-') and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700\nitem=json.loads((folder/'identity.json').read_text());info=os.fstat(fd)\nassert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']\nassert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==item['kill_sha256']\nassert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in item['program_sha256']}==item['program_sha256'],'operator_program_changed'\nassert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in item['official_sha256']}==item['official_sha256'],'official_configuration_changed'\nfcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)\nresult={'completed':False,'container_id':item['container_id'],'image':item['image'],'docker_client_joined':False}\ndef inspect():return json.loads(subprocess.check_output(item['docker']+['inspect',item['container_id']],text=True,timeout=5))[0]\ntry:\n current=inspect();assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running'] and current['State']['StartedAt']==item['started_at'],'control_generation_changed'\n try:\n  p=subprocess.run(item['docker']+['kill','--signal','KILL',item['container_id']],capture_output=True,timeout=25)\n except subprocess.TimeoutExpired:\n  result.update(docker_client_joined=False,error='docker_kill_timeout');raise\n result['docker_client_joined']=True\n assert p.returncode==0,'docker_kill_failed'\n current=inspect();assert not current['State']['Running'] and current['State']['ExitCode']==137 and current['State']['StartedAt']==item['started_at']\n result.update(completed=True,exit_code=137)\nexcept Exception as error:result['error_type']=type(error).__name__\nfinally:\n path=folder/'kill-result.json';pending=folder/'kill-result.pending';pending.write_text(json.dumps(result)+'\\n');os.chmod(pending,0o600);pending.replace(path)\nassert result['completed'],'stop_outcome_unknown'\n"

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
root=Path('/srv/p2enjoy-serverless');control=root/'state/control.sqlite3'
mode,function_id,namespace=sys.argv[1:4]
assert mode in ('arm','watchdog','inspect','restore','rescue','evidence','refusal-lock')
assert str(UUID(function_id))==function_id and str(UUID(namespace))==namespace
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
with read_control(control) as db:
 owner=db.execute('SELECT f.service_id,n.name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?',(function_id,namespace)).fetchone()
 assert owner and owner['name'].startswith('function-http-client-recovery-'),'owned_campaign_required'
 service=owner['service_id']

def inspect(name):return json.loads(command(D+['inspect',name]))[0]
def snapshot():
 with read_control(control) as db:
  db.execute('BEGIN')
  row=dict(db.execute('SELECT * FROM functions WHERE id=?',(function_id,)).fetchone())
  function={k:row[k] for k in ('id','active_revision_id','updated_at','deleted_at','purged_at')}
  function['configuration_sha256']=hashlib.sha256(json.dumps({k:v for k,v in row.items() if k not in function},sort_keys=True).encode()).hexdigest()
  invocations=[dict(v) for v in db.execute('SELECT id,state,handler_started,http_status,error_code,created_at,dispatched_at,completed_at,resolved_code_hash FROM invocations WHERE function_id=? ORDER BY created_at,id',(function_id,))]
  result={'function':function,'invocations':invocations,'integrity':db.execute('PRAGMA integrity_check').fetchone()[0],'foreign_keys':[list(v) for v in db.execute('PRAGMA foreign_key_check')]}
  db.rollback()
  return result

# @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER_LOADING.md#décision-avant-code
def current_process_identity():
 current_control=inspect('serverless-api');current_reference=inspect('serverless-runtime-reference')
 assert current_control['Id']==item['container_id'] and current_control['Image']==item['image'] and current_control['State']['Running'] and current_control['State']['StartedAt']==item['started_at'],'control_generation_changed_before_attach'
 assert [current_reference['Id'],current_reference['Image'],current_reference['State']['StartedAt']]==item['reference'],'reference_changed_before_attach'
 assert birth(pid)==item['birth'] and Path('/proc',str(pid),'cgroup').read_text()==item['cgroup'],'control_process_changed_before_attach'
 assert Path(os.readlink('/proc/'+str(pid)+'/exe')).name.startswith('python') and Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00'),'control_command_changed_before_attach'
 status=Path('/proc',str(pid),'status').read_text().splitlines()
 return {'pid':pid,'birth':item['birth'],'cgroup_sha256':hashlib.sha256(item['cgroup'].encode()).hexdigest(),'tracer_pid':int(next(v.split()[1] for v in status if v.startswith('TracerPid:'))),'state':next(v.split()[1] for v in status if v.startswith('State:'))}

def finish_guard(unit):
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=10)
 deadline=time.monotonic()+45
 while True:
  states={}
  for suffix in ('timer','service'):
   p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=LoadState','--property=MainPID'],capture_output=True,text=True,timeout=10)
   states[suffix]=dict(v.split('=',1) for v in p.stdout.splitlines())
  if all(v.get('ActiveState')=='inactive' and v.get('MainPID','0')=='0' for v in states.values()):return states
  assert time.monotonic()<deadline,'guard_service_not_joined'
  time.sleep(.1)

if mode in ('restore','rescue','evidence'):
 unit=sys.argv[4];assert re.fullmatch('serverless-restore-http-client-[0-9a-f]{32}',unit)
 folder=Path('/run')/unit;item=json.loads((folder/'identity.json').read_text())
 assert item['function_id']==function_id and item['namespace_id']==namespace
 if mode in ('restore','rescue'):
  receipt=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),*(['guard'] if mode=='rescue' else [])],timeout=190));receipt['guard_states']=finish_guard(unit);emit(receipt)
 else:
  path=folder/'restored-independent.json'
  if not path.exists():path=folder/'restored.json'
  emit(json.loads(path.read_text()) if path.exists() else {'event':'pending'})
 sys.exit(0)
if mode=='inspect':emit(snapshot());sys.exit(0)

with read_control(control) as db:
 assert db.execute("SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')").fetchone()[0]==0,'quiet_invocations_required'
 for table in ('execution_instances','function_operations','code_drafts'):assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0,'quiet_resources_required'
 assert db.execute("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()[0]==0,'quiet_validation_required'
 assert db.execute('SELECT count(*) FROM functions f JOIN services s ON s.id=f.service_id WHERE f.deleted_at IS NULL AND s.namespace_id<>?',(namespace,)).fetchone()[0]==0,'exclusive_campaign_required'
with control_owner(control),closing(sqlite3.connect('file:'+str(root/'storage-state/registry.sqlite3')+'?mode=ro',uri=True)) as db:
 assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0,'quiet_storage_required'
 assert db.execute('SELECT count(*) FROM functions WHERE pending_json IS NOT NULL').fetchone()[0]==0,'quiet_storage_decisions_required'
for kind in ('instance','validation'):assert not command(D+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind='+kind]),'untracked_consumer_present'
current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference')
assert current['State']['Running'] and reference['State']['Running']
assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'
if mode=='refusal-lock':
 signal.alarm(20);started=time.monotonic();before=snapshot();writer=ControlWriter(control);reason='pending'
 try:
  assert writer.db.total_changes==0
  emit({'event':'armed','mode':mode,'before':before,'identity':writer.identity,'sql_changes':0,'max_wait_seconds':15})
  try:
   line=read_command(32,15);assert line==b'release\n','invalid_release_command';reason='released'
  except AssertionError as error:
   reason=str(error)
   if reason not in ('command_eof','command_deadline'):raise
  assert writer.db.total_changes==0
 finally:
  changes=writer.db.total_changes if writer.db is not None else None;writer.close()
  emit({'event':'lock-released','reason':reason,'sql_changes':changes,'connection_closed':writer.db is None,'elapsed_seconds':time.monotonic()-started})
 sys.exit(0)

init=current['State']['Pid'];descendants=[init]
for parent in descendants:descendants.extend(int(v) for v in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
pids=[pid for pid in descendants if Path(os.readlink('/proc/'+str(pid)+'/exe')).name.startswith('python') and Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00')]
assert len(pids)==1,'unique_control_process_required'
pid=pids[0];assert Path('/proc',str(pid),'cgroup').read_text()==Path('/proc',str(init),'cgroup').read_text(),'container_owner_required'
before=snapshot();unit='serverless-restore-http-client-'+uuid4().hex;folder=Path('/run')/unit;folder.mkdir(mode=0o700)
lock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);info=os.fstat(lock)
item={'function_id':function_id,'namespace_id':namespace,'service_id':service,'container_id':current['Id'],'image':current['Image'],'started_at':current['State']['StartedAt'],
 'reference':[reference['Id'],reference['Image'],reference['State']['StartedAt']],'pid':pid,'birth':birth(pid),'cgroup':Path('/proc',str(pid),'cgroup').read_text(),
 'helper_pid':os.getpid(),'helper_birth':birth(os.getpid()),'docker':D,'lock_identity':[info.st_dev,info.st_ino],
 'official_sha256':{name:sha(name) for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},'restore_sha256':hashlib.sha256(RESTORE.encode()).hexdigest(),
 'kill_sha256':hashlib.sha256(KILL_CONTROL.encode()).hexdigest(),'program_sha256':{str(Path(__file__).resolve()):sha(__file__),str(Path(__file__).with_name('native_control_observer.py').resolve()):sha(Path(__file__).with_name('native_control_observer.py'))}}
for name,content in [('identity.json',json.dumps(item)),('restore.py',RESTORE),('kill.py',KILL_CONTROL)]:
 path=folder/name;path.write_text(content);path.chmod(0o600)
observer=NativeObserver(pid);armed=False;stopped=None
try:
 command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active='+('12s' if mode=='watchdog' else '70s'),'--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=190s','--property=TimeoutStopSec=5s','/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'guard'])
 armed=True;assert command(['systemctl','is-active',unit+'.timer'])=='active','guard_not_armed'
 emit({'event':'armed','unit':unit,'container_id':current['Id'],'image':current['Image'],'started_at':item['started_at'],'before':before})
 if mode=='watchdog':
  assert current_process_identity()['tracer_pid']==0,'control_already_traced'
  observer.start();traced=current_process_identity();assert traced['tracer_pid']==os.getpid() and traced['state']=='t','control_native_stop_changed'
  emit({'event':'suspended','unit':unit,'process':traced,'helper_pid':os.getpid()})
  assert read_command(32,8)==b'lose-observer\n','watchdog_command_required'
  emit({'event':'observer-loss','unit':unit,'signal':'SIGKILL'});os.kill(os.getpid(),signal.SIGKILL)
 line=read_command(64,40).decode('ascii')
 action,identifier=line.strip().split(' ');assert action=='cut' and str(UUID(identifier))==identifier
 with read_control(control) as db:
  invocation=db.execute('SELECT id,function_id,state,handler_started,dispatched_at,completed_at FROM invocations WHERE id=?',(identifier,)).fetchone()
  assert invocation and invocation['function_id']==function_id and invocation['state']=='running' and invocation['handler_started']==1 and invocation['completed_at'] is None,'started_owned_handler_required'
  assert invocation['dispatched_at'] is not None and 0<=time.time()-invocation['dispatched_at']<5,'handler_window_exhausted'
  dispatched_at=invocation['dispatched_at'];observed=dict(invocation)
 observed_control=inspect('serverless-api')
 assert observed_control['Id']==current['Id'] and observed_control['Image']==current['Image'] and observed_control['State']['StartedAt']==item['started_at'] and birth(pid)==item['birth'],'control_identity_changed'
 assert current_process_identity()['tracer_pid']==0,'control_already_traced'
 observer.start();traced=current_process_identity();assert traced['tracer_pid']==os.getpid() and traced['state']=='t','control_native_stop_changed'
 emit({'event':'gated','invocation':observed,'unit':unit,'process':traced})
 fcntl.flock(lock,fcntl.LOCK_EX)
 try:
  path=folder/'kill-started.json';path.write_text(json.dumps({'requested':True,'invocation_id':identifier})+'\n');path.chmod(0o600)
  stopped=subprocess.Popen(['/usr/bin/python3','-I',str(folder/'kill.py'),str(folder),str(lock)],pass_fds=(lock,),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  deadline=time.monotonic()+10
  while True:
   waited,status=os.waitpid(pid,os.WNOHANG)
   if waited:
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL,'native_kill_unconfirmed'
    observed_at=time.time();assert observed_at<dispatched_at+8,'native_kill_after_handler_window'
    observer.attached=False;break
   assert time.monotonic()<deadline,'control_death_not_observed';time.sleep(.01)
  stopped.communicate(timeout=40);assert stopped.returncode==0,'kill_mutator_failed'
  killed=inspect(current['Id']);assert not killed['State']['Running'] and killed['State']['ExitCode']==137
  native={'event':'cut','unit':unit,'invocation_id':identifier,'native_signal':9,'native_exit_observed_at':observed_at,'earliest_handler_completion_at':dispatched_at+8,'exit_code':137,'durable':snapshot()}
  pending=folder/'native-cut.pending';pending.write_text(json.dumps(native)+'\n');pending.chmod(0o600);pending.replace(folder/'native-cut.json')
  emit(native|{'native_receipt_sha256':sha(folder/'native-cut.json')})
 finally:
  if stopped is not None:stopped.communicate(timeout=50);assert stopped.poll() is not None,'mutator_not_joined'
  fcntl.flock(lock,fcntl.LOCK_UN)
finally:
 observer.detach();os.close(lock)
 if armed:
  emit(json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder)],timeout=190)))
  emit({'event':'guard-finished','unit':unit,'states':finish_guard(unit)})
