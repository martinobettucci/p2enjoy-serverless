# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md#coupures-physiques-gardées
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md#coupures-physiques-gardées
"""Guarded physical upload cuts on the single authorized DEV Spark."""
from contextlib import closing
import fcntl,hashlib,json,os,platform,re,select,shlex,signal,socket,sqlite3,stat,subprocess,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control,control_owner
from native_control_observer import NativeObserver

def emit(value):print(json.dumps(value),flush=True)

def command(args,timeout=35,**kwargs):
 value=subprocess.run(args,capture_output=True,text=True,timeout=timeout,**kwargs)
 assert value.returncode==0,'operator_command_failed'
 return value.stdout.strip()

def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def encoded(value):return hashlib.sha256(json.dumps(value,sort_keys=True,default=lambda raw:raw.hex()).encode()).hexdigest()

def settings():
 result={}
 for line in Path('/etc/spark/env').read_text().splitlines():
  fields=shlex.split(line,comments=True)
  if len(fields)==1 and '=' in fields[0]:
   key,value=fields[0].split('=',1)
   if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST','SERVERLESS_STORAGE_ROOT_HOST'):result[key]=value
 return result

RESTORE = "import fcntl,hashlib,json,os,select,signal,socket,sqlite3,stat,subprocess,sys,time,urllib.request\nfrom pathlib import Path\nassert os.geteuid()==0 and socket.gethostname()=='infra-serverless'\nsignal.alarm(180)\nfolder=Path(sys.argv[1]);info=folder.lstat()\nassert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-publication-upload-')\nassert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700\nitem=json.loads((folder/'identity.json').read_text());independent=len(sys.argv)>2\nassert hashlib.sha256((folder/'restore.py').read_bytes()).hexdigest()==item['restore_sha256']\nassert {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in item['official_sha256']}==item['official_sha256']\nresult={'event':'restored','independent':independent,'container_id':item['container_id'],'image':item['image']}\nif independent:\n try:fd=os.pidfd_open(item['helper_pid'])\n except ProcessLookupError:pass\n else:\n  try:\n   row=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()\n   if row[19]==item['helper_birth']:\n    signal.pidfd_send_signal(fd,signal.SIGKILL)\n    ready,_,_=select.select([fd],[],[],10);assert ready,'observer_stop_unconfirmed'\n    result['observer_killed']=True\n  except (ProcessLookupError,FileNotFoundError):pass\n  finally:os.close(fd)\n result['observer_gone']=True\nlock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_NOFOLLOW)\ntry:\n info=os.fstat(lock);assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']\n deadline=time.monotonic()+40\n while True:\n  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break\n  except BlockingIOError:\n   assert time.monotonic()<deadline,'stop_mutator_not_joined';time.sleep(.1)\n if (folder/'kill-started.json').exists():\n  proof=json.loads((folder/'kill-result.json').read_text());assert proof['completed'] and proof['docker_client_joined'] and proof['exit_code']==137 and proof['container_id']==item['container_id'],'stop_mutation_outcome_unknown'\n  result['stop_receipt_sha256']=hashlib.sha256((folder/'kill-result.json').read_bytes()).hexdigest()\n def inspect(name):\n  return json.loads(subprocess.run(item['docker']+['inspect',name],check=True,capture_output=True,text=True,timeout=30).stdout)[0]\n current=inspect('serverless-api');assert current['Id']==item['container_id'] and current['Image']==item['image'],'control_replaced'\n reference=inspect('serverless-runtime-reference');assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'],'reference_replaced'\n try:fd=os.pidfd_open(item['pid'])\n except ProcessLookupError:pass\n else:\n  try:\n   row=Path('/proc',str(item['pid']),'stat').read_text().rsplit(')',1)[1].split()\n   assert row[19]==item['birth'],'control_pid_reused'\n   assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_owner_changed'\n   signal.pidfd_send_signal(fd,signal.SIGCONT)\n  except (FileNotFoundError,ProcessLookupError):pass\n  finally:os.close(fd)\n result['was_running']=current['State']['Running'];result['exit_code_before']=current['State']['ExitCode']\n if not current['State']['Running']:\n  subprocess.run(item['docker']+['start',item['container_id']],check=True,capture_output=True,timeout=30)\n deadline=time.monotonic()+35\n while True:\n  try:\n   with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:assert response.status==200\n   current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')\n   assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'\n   break\n  except (OSError,AssertionError):\n   assert time.monotonic()<deadline,'control_health_not_restored';time.sleep(.2)\n current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')\n assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running']\n assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']\n result.update(healthy=True,reference_unchanged=True,stop_mutator_joined=True,started_at=current['State']['StartedAt'])\n name='restored-independent.json' if independent else 'restored.json'\n pending=folder/(name+'.pending');pending.write_text(json.dumps(result)+'\\n');pending.replace(folder/name)\n print(json.dumps(result),flush=True)\nfinally:os.close(lock)\n"

KILL_CONTROL = "import fcntl,hashlib,json,os,signal,socket,stat,subprocess,sys\nfrom pathlib import Path\nassert os.geteuid()==0 and socket.gethostname()=='infra-serverless'\nsignal.alarm(45)\nfolder=Path(sys.argv[1]);fd=int(sys.argv[2]);info=folder.lstat()\nassert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-publication-upload-') and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700\nitem=json.loads((folder/'identity.json').read_text());info=os.fstat(fd)\nassert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']\nassert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==item['kill_sha256']\nfcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)\nresult={'completed':False,'container_id':item['container_id'],'image':item['image'],'docker_client_joined':False}\ndef inspect():return json.loads(subprocess.check_output(item['docker']+['inspect',item['container_id']],text=True,timeout=5))[0]\ntry:\n current=inspect();assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running']\n try:\n  p=subprocess.run(item['docker']+['kill','--signal','KILL',item['container_id']],capture_output=True,timeout=25)\n except subprocess.TimeoutExpired:\n  result.update(docker_client_joined=False,error='docker_kill_timeout');raise\n result['docker_client_joined']=True\n assert p.returncode==0,'docker_kill_failed'\n current=inspect();assert not current['State']['Running'] and current['State']['ExitCode']==137\n result.update(completed=True,exit_code=137)\nexcept Exception as error:result['error_type']=type(error).__name__\nfinally:\n path=folder/'kill-result.json';pending=folder/'kill-result.pending';pending.write_text(json.dumps(result)+'\\n');os.chmod(pending,0o600);pending.replace(path)\nassert result['completed'],'stop_outcome_unknown'\n"

def finish_guard(unit):
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=10)
 end=time.monotonic()+45
 while True:
  states={}
  for suffix in ('timer','service'):
   p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=LoadState','--property=MainPID'],capture_output=True,text=True,timeout=10)
   states[suffix]=dict(v.split('=',1) for v in p.stdout.splitlines())
  if all(v.get('ActiveState')=='inactive' and v.get('MainPID','0')=='0' for v in states.values()):return states
  assert time.monotonic()<end,'guard_service_not_joined'
  time.sleep(.1)

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless' and platform.machine()=='x86_64','dev_spark_required'
mode,namespace=sys.argv[1:3]
assert mode in ('inspect','receiving','validating','restore','rescue','evidence') and str(UUID(namespace))==namespace
values=settings();root=Path(values['SERVERLESS_STATE_HOST_PATH']);control=root/'control.sqlite3'
docker=['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST']]
function_id=sys.argv[3] if len(sys.argv)>3 else None
with read_control(control) as db:
 owner=db.execute('SELECT name FROM namespaces WHERE id=?',(namespace,)).fetchone()
 assert owner and re.fullmatch('publication-recovery-[0-9a-f]{8}',owner['name']),'owned_namespace_required'
 installation=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
 if function_id:
  assert str(UUID(function_id))==function_id
  row=db.execute('SELECT f.service_id FROM functions f JOIN services s ON s.id=f.service_id WHERE f.id=? AND s.namespace_id=?',(function_id,namespace)).fetchone()
  assert row,'owned_function_required'
  service=row['service_id']

def containers(kind):
 ids=command(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind='+kind]).split()
 return json.loads(command(docker+['inspect',*ids])) if ids else []
def inspect(candidate=None):
 result={}
 with read_control(control) as db:
  db.execute('BEGIN')
  result['counts']={n:db.execute(sql).fetchone()[0] for n,sql in {'active_candidates':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'operations':'SELECT count(*) FROM function_operations'}.items()}
  if function_id:
   row=dict(db.execute('SELECT * FROM functions WHERE id=?',(function_id,)).fetchone())
   result['function']={k:row[k] for k in ('id','active_revision_id','updated_at','first_published_code_hash','first_promoted_at')}
   result['function']['configuration_sha256']=encoded({k:row[k] for k in ('config_json','environment_json','secrets_cipher')})
   result['versions']=[dict(v) for v in db.execute('SELECT * FROM function_versions WHERE function_id=? ORDER BY code_hash',(function_id,))]
   result['revisions']=[dict(v) for v in db.execute('SELECT id,code_hash,archive_sha256,created_at,deleted_at,stored_bytes FROM revisions WHERE function_id=? ORDER BY id',(function_id,))]
   result['archives']={}
   for row in result['revisions']:
    folder=root/'artifacts'/row['id'];file=folder/'archive.zip'
    assert not folder.is_symlink()
    result['archives'][row['id']]={'directory_exists':folder.exists(),'sha256':sha(file) if file.exists() else None}
    if row['stored_bytes']>0:assert result['archives'][row['id']]['sha256']==row['archive_sha256']
  if candidate:
   assert str(UUID(candidate))==candidate and function_id
   row=db.execute('SELECT id,state,error_code,reserved_bytes,configuration_cipher IS NULL AS payload_erased,revision_id FROM deployments WHERE id=? AND function_id=?',(candidate,function_id)).fetchone();assert row,'owned_candidate_required'
   row=dict(row);folder=root/'artifacts'/candidate;assert not folder.is_symlink();file=folder/'archive.zip'
   row.update(directory_exists=folder.exists(),archive_bytes=file.stat().st_size if file.exists() else 0);result['candidate']=row
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 result['validation_containers']=[{'id':v['Id'],'running':v['State']['Running'],'image':v['Image'],'installation':v['Config']['Labels'].get('tech.p2enjoy.serverless.installation'),'mounts':[{k:m[k] for k in ('Source','Destination')} for m in v['Mounts']]} for v in containers('validation')]
 result['validation_channels']=[p.name for p in (root/'validation').iterdir()]
 current=json.loads(command(docker+['inspect','serverless-api']))[0];result['control']={k:current[k] for k in ('Id','Image')};result['control'].update(started_at=current['State']['StartedAt'],running=current['State']['Running'])
 return result

if mode in ('restore','rescue','evidence'):
 assert function_id
 unit=sys.argv[4];assert re.fullmatch('serverless-restore-publication-upload-[0-9a-f]{32}',unit)
 folder=Path('/run')/unit;item=json.loads((folder/'identity.json').read_text());assert item['function_id']==function_id and item['namespace_id']==namespace
 if mode in ('restore','rescue'):
  receipt=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),*(['guard'] if mode=='rescue' else [])],timeout=190));receipt['guard_states']=finish_guard(unit);emit(receipt)
 else:
  p=folder/'restored-independent.json'
  if not p.exists():p=folder/'restored.json'
  emit(json.loads(p.read_text()) if p.exists() else {'event':'pending'})
 sys.exit(0)
if mode=='inspect':emit(inspect(sys.argv[4] if len(sys.argv)>4 else None));sys.exit(0)
assert function_id
candidate=sys.argv[4];before=inspect(candidate)
assert before['candidate']['state']=='prepared' and before['candidate']['reserved_bytes']==0
assert before['counts']=={'active_candidates':1,'reserved_bytes':0,'instances':0,'active_calls':0,'operations':0},'quiet_installation_required'
assert before['validation_containers']==before['validation_channels']==[]
with read_control(control) as db:assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0]==1
registry=Path(values['SERVERLESS_STORAGE_ROOT_HOST'])/'registry.sqlite3'
with control_owner(control),closing(sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True)) as db:assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0
assert not containers('instance')
current=json.loads(command(docker+['inspect','serverless-api']))[0];reference=json.loads(command(docker+['inspect','serverless-runtime-reference']))[0]
assert current['State']['Running'] and reference['State']['Running'] and current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'
runtime_image=dict(v.split('=',1) for v in current['Config']['Env'])['SERVERLESS_RUNTIME_IMAGE'];assert re.fullmatch('sha256:[0-9a-f]{64}',runtime_image)
init=current['State']['Pid'];descendants=[init]
for parent in descendants:descendants.extend(int(v) for v in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
processes=[p for p in descendants if Path(os.readlink(f'/proc/{p}/exe')).name.startswith('python') and Path('/proc',str(p),'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00')]
assert len(processes)==1;pid=processes[0]
assert Path('/proc',str(pid),'cgroup').read_text()==Path('/proc',str(init),'cgroup').read_text()
unit='serverless-restore-publication-upload-'+uuid4().hex;folder=Path('/run')/unit;folder.mkdir(mode=0o700)
lock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);info=os.fstat(lock)
item={'namespace_id':namespace,'function_id':function_id,'candidate_id':candidate,'phase':mode,'official_sha256':{n:sha(n) for n in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},'restore_sha256':hashlib.sha256(RESTORE.encode()).hexdigest(),'kill_sha256':hashlib.sha256(KILL_CONTROL.encode()).hexdigest(),'operator_sha256':sha(__file__),'native_observer_sha256':sha(Path(__file__).with_name('native_control_observer.py')),'container_id':current['Id'],'image':current['Image'],'started_at':current['State']['StartedAt'],'reference':[reference['Id'],reference['Image'],reference['State']['StartedAt']],'docker':docker,'pid':pid,'birth':birth(pid),'cgroup':Path('/proc',str(pid),'cgroup').read_text(),'helper_pid':os.getpid(),'helper_birth':birth(os.getpid()),'lock_identity':[info.st_dev,info.st_ino]}
for leaf,body in [('identity.json',json.dumps(item)),('restore.py',RESTORE),('kill.py',KILL_CONTROL)]:p=folder/leaf;p.write_text(body);os.chmod(p,0o600)
observer=NativeObserver(pid);armed=False
try:
 command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=45s','--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=190s','--property=TimeoutStopSec=5s','/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'guard'])
 armed=True;assert command(['systemctl','is-active',unit+'.timer'])=='active'
 emit({'event':'guard-armed','unit':unit});emit({'event':'armed','unit':unit,'before':before})
 assert select.select([sys.stdin],[],[],20)[0] and sys.stdin.readline().strip()=='observe','observe_command_required'
 deadline=time.monotonic()+20;observed=None
 while time.monotonic()<deadline:
  value=inspect(candidate);phase=value['candidate']['state']
  assert phase in ('prepared','receiving',mode),'window_missed_'+phase
  if phase==mode:
   if mode=='receiving' and value['candidate']['archive_bytes']>0:observed=value;break
   if mode=='validating':
    matches=[v for v in value['validation_containers'] if v['running'] and v['image']==runtime_image and v['installation']==installation and any(m['Destination']=='/code' and m['Source']==str(root/'artifacts'/candidate/'code') for m in v['mounts'])]
    if len(matches)==1:observed=value;break
  time.sleep(.05)
 assert observed,'physical_phase_not_observed'
 observer.start();gated=inspect(candidate);assert gated['candidate']['state']==mode,'window_missed_after_attach'
 if mode=='validating':assert any(v['running'] and v['image']==runtime_image and v['id']==matches[0]['id'] for v in gated['validation_containers']),'validator_not_alive_at_gate'
 emit({'event':'gated','phase':mode,'observed':observed,'durable':gated})
 assert select.select([sys.stdin],[],[],8)[0] and sys.stdin.readline().strip()=='interrupt','interrupt_command_required'
 fcntl.flock(lock,fcntl.LOCK_EX)
 try:
  (folder/'kill-started.json').write_text(json.dumps({'requested':True})+'\n');os.chmod(folder/'kill-started.json',0o600)
  stopped=subprocess.Popen(['/usr/bin/python3','-I',str(folder/'kill.py'),str(folder),str(lock)],pass_fds=(lock,),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  end=time.monotonic()+10
  while True:
   waited,status=os.waitpid(pid,os.WNOHANG)
   if waited:
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL,'native_control_death_unconfirmed';observer.attached=False;break
   assert time.monotonic()<end,'control_death_not_observed';time.sleep(.01)
  stopped.communicate(timeout=40);assert stopped.returncode==0
  killed=json.loads(command(docker+['inspect',current['Id']]))[0];assert not killed['State']['Running'] and killed['State']['ExitCode']==137
  proof={'event':'cut','unit':unit,'phase':mode,'exit_code':137,'native_signal':signal.SIGKILL,'candidate_id':candidate};p=folder/'interrupted.json';p.write_text(json.dumps(proof)+'\n');os.chmod(p,0o600);emit(proof)
 finally:
  if 'stopped' in locals():stopped.communicate(timeout=50);assert stopped.poll() is not None,'stop_mutator_not_joined'
  fcntl.flock(lock,fcntl.LOCK_UN)
 if mode=='validating':
  emit({'event':'observer-loss','unit':unit,'signal':'SIGKILL'});os.kill(os.getpid(),signal.SIGKILL)
finally:
 observer.detach();os.close(lock)
 if armed:
  emit(json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder)],timeout=190)))
  emit({'event':'guard-finished','unit':unit,'states':finish_guard(unit)})
