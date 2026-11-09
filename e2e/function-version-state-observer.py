# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#décision-et-frontières
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#matrice-et-discriminants
"""Observe only a public version request line; never replace code, state or replies."""
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

RESTORE = r'''import fcntl,hashlib,json,os,select,signal,socket,sqlite3,stat,subprocess,sys,time,urllib.request
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(180)
folder=Path(sys.argv[1]);info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-version-state-')
assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
item=json.loads((folder/'identity.json').read_text());independent=len(sys.argv)>2
assert hashlib.sha256((folder/'restore.py').read_bytes()).hexdigest()==item['restore_sha256']
assert {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in item['official_sha256']}==item['official_sha256']
result={'event':'restored','independent':independent,'container_id':item['container_id'],'image':item['image']}
if independent:
 try:fd=os.pidfd_open(item['helper_pid'])
 except ProcessLookupError:pass
 else:
  try:
   row=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()
   if row[19]==item['helper_birth']:
    signal.pidfd_send_signal(fd,signal.SIGKILL)
    ready,_,_=select.select([fd],[],[],10);assert ready,'observer_stop_unconfirmed'
    result['observer_killed']=True
  except (ProcessLookupError,FileNotFoundError):pass
  finally:os.close(fd)
 result['observer_gone']=True
lock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_NOFOLLOW)
try:
 info=os.fstat(lock);assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']
 deadline=time.monotonic()+40
 while True:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   assert time.monotonic()<deadline,'stop_mutator_not_joined';time.sleep(.1)
 if (folder/'kill-started.json').exists():
  proof=json.loads((folder/'kill-result.json').read_text());assert proof['completed'] and proof['docker_client_joined'] and proof['exit_code']==137 and proof['container_id']==item['container_id'],'stop_mutation_outcome_unknown'
  result['stop_receipt_sha256']=hashlib.sha256((folder/'kill-result.json').read_bytes()).hexdigest()
 def inspect(name):
  return json.loads(subprocess.run(item['docker']+['inspect',name],check=True,capture_output=True,text=True,timeout=30).stdout)[0]
 current=inspect('serverless-api');assert current['Id']==item['container_id'] and current['Image']==item['image'],'control_replaced'
 reference=inspect('serverless-runtime-reference');assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'],'reference_replaced'
 try:fd=os.pidfd_open(item['pid'])
 except ProcessLookupError:pass
 else:
  try:
   row=Path('/proc',str(item['pid']),'stat').read_text().rsplit(')',1)[1].split()
   assert row[19]==item['birth'],'control_pid_reused'
   assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_owner_changed'
   signal.pidfd_send_signal(fd,signal.SIGCONT)
  except (FileNotFoundError,ProcessLookupError):pass
  finally:os.close(fd)
 result['was_running']=current['State']['Running'];result['exit_code_before']=current['State']['ExitCode']
 if not current['State']['Running']:
  subprocess.run(item['docker']+['start',item['container_id']],check=True,capture_output=True,timeout=30)
 deadline=time.monotonic()+35
 while True:
  try:
   with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:assert response.status==200
   current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')
   assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'
   break
  except (OSError,AssertionError):
   assert time.monotonic()<deadline,'control_health_not_restored';time.sleep(.2)
 current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')
 assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running']
 assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']
 result.update(healthy=True,reference_unchanged=True,stop_mutator_joined=True,started_at=current['State']['StartedAt'])
 name='restored-independent.json' if independent else 'restored.json'
 pending=folder/(name+'.pending');pending.write_text(json.dumps(result)+'\n');pending.replace(folder/name)
 print(json.dumps(result),flush=True)
finally:os.close(lock)
'''

KILL_CONTROL = r'''import fcntl,hashlib,json,os,signal,socket,stat,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(45)
folder=Path(sys.argv[1]);fd=int(sys.argv[2]);info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-version-state-') and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
item=json.loads((folder/'identity.json').read_text());info=os.fstat(fd)
assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==item['kill_sha256']
fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
result={'completed':False,'container_id':item['container_id'],'image':item['image'],'docker_client_joined':False}
def inspect():return json.loads(subprocess.check_output(item['docker']+['inspect',item['container_id']],text=True,timeout=5))[0]
try:
 current=inspect();assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running']
 try:
  p=subprocess.run(item['docker']+['kill','--signal','KILL',item['container_id']],capture_output=True,timeout=25)
 except subprocess.TimeoutExpired:
  result.update(docker_client_joined=False,error='docker_kill_timeout');raise
 result['docker_client_joined']=True
 assert p.returncode==0,'docker_kill_failed'
 current=inspect();assert not current['State']['Running'] and current['State']['ExitCode']==137
 result.update(completed=True,exit_code=137)
except Exception as error:result['error_type']=type(error).__name__
finally:
 path=folder/'kill-result.json';pending=folder/'kill-result.pending';pending.write_text(json.dumps(result)+'\n');os.chmod(pending,0o600);pending.replace(path)
assert result['completed'],'stop_outcome_unknown'
'''

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless' and platform.machine()=='x86_64','dev_spark_required'
mode,function_id,namespace=sys.argv[1:4]
assert mode in ('before','after','watchdog','inspect','restore','rescue','evidence')
assert str(UUID(function_id))==function_id and str(UUID(namespace))==namespace
values=settings();control=Path(values['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3'
docker=['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST']]
with read_control(control) as db:
 owner=db.execute('SELECT f.service_id,n.name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?',(function_id,namespace)).fetchone()
 assert owner and re.fullmatch('version-state-transport-[0-9a-f]{8}',owner['name']),'owned_campaign_required'
 service=owner['service_id']

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

def durable():
 with read_control(control) as db:
  db.execute('BEGIN')
  row=dict(db.execute('SELECT * FROM functions WHERE id=? AND service_id=?',(function_id,service)).fetchone());config=json.loads(row['config_json'])
  function={k:row[k] for k in ('id','active_revision_id','updated_at','first_published_code_hash','first_promoted_at')}
  if row['purged_at'] is not None:
   assert config=={} and row['deleted_at'] is not None,'purged_configuration_not_empty'
   handler=runtime=None
  else:handler,runtime=config.pop('handler'),config.pop('runtime')
  function.update(handler=handler,runtime=runtime,resource_configuration_sha256=encoded(config),other_fields_sha256=encoded({k:v for k,v in row.items() if k not in ('active_revision_id','updated_at','config_json')}))
  versions=[dict(v) for v in db.execute('SELECT * FROM function_versions WHERE function_id=? ORDER BY code_hash',(function_id,))]
  revisions=[];artifacts={}
  for raw in db.execute('SELECT * FROM revisions WHERE function_id=? ORDER BY id',(function_id,)):
   v=dict(raw);revisions.append({k:v[k] for k in ('id','code_hash','created_at','deleted_at','stored_bytes','handler','runtime','image_id','archive_sha256')}|{'other_fields_sha256':encoded({k:z for k,z in v.items() if k not in ('deleted_at','stored_bytes')})})
   path=control.parent/'artifacts'/v['id'];assert not path.is_symlink()
   artifacts[v['id']]={'exists':path.exists(),'files':{str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()}} if path.exists() else {'exists':False,'files':{}}
  audits=[{'id':v['id'],'action':v['action'],'created_at':v['created_at'],'detail_sha256':hashlib.sha256(v['detail_json'].encode()).hexdigest()} for v in db.execute('SELECT * FROM audit_events WHERE object_id=? ORDER BY created_at,id',(function_id,))]
  result={'function':function,'versions':versions,'revisions':revisions,'artifacts':artifacts,'audits':audits,
   'service_sha256':encoded(dict(db.execute('SELECT * FROM services WHERE id=?',(service,)).fetchone())),
   'candidates':[dict(v) for v in db.execute('SELECT id,state,revision_id,code_hash,reserved_bytes FROM deployments WHERE function_id=? ORDER BY id',(function_id,))],
   'invocations':[dict(v) for v in db.execute('SELECT id,state,handler_started,requested_code_hash,resolved_code_hash FROM invocations WHERE function_id=? ORDER BY id',(function_id,))]}
  return result

def committed(before,after):
 versions={v['code_hash']:v for v in before['versions']};assert selected_hash in versions
 target=versions[selected_hash] if action=='promote' else versions[replacement]
 revision=next(v for v in before['revisions'] if v['id']==target['revision_id'])
 expected=dict(before['function']);expected.update(active_revision_id=revision['id'],handler=revision['handler'],runtime=revision['runtime'],updated_at=after['function']['updated_at'])
 assert expected==after['function'] and after['function']['updated_at']>before['function']['updated_at'],'coupled_function_decision_missing'
 expected_versions=[dict(v) for v in before['versions']]
 if action!='promote':
  changed=next(v for v in expected_versions if v['code_hash']==selected_hash);changed.update(state='archived' if action=='archive' else 'deleted',updated_at=after['function']['updated_at'])
 assert after['versions']==expected_versions,'unexpected_version_decision'
 old_audits={v['id']:v for v in before['audits']};new_audits={v['id']:v for v in after['audits']};assert all(new_audits.get(k)==v for k,v in old_audits.items())
 extra=[v for k,v in new_audits.items() if k not in old_audits];assert len(extra)==1 and extra[0]['action']=={'promote':'function.version_promote','archive':'version.archive','delete':'version.delete'}[action]
 detail={'code_hash':selected_hash,'revision_id':revision['id']} if action=='promote' else {'code_hash':selected_hash,'replacement_code_hash':replacement,'disable_default':False}
 assert extra[0]['detail_sha256']==hashlib.sha256(json.dumps(detail,separators=(',',':')).encode()).hexdigest(),'decision_audit_mismatch'
 for key in ('service_sha256','candidates','invocations'):assert after[key]==before[key],key
 if action!='delete':
  assert before['revisions']==after['revisions'] and before['artifacts']==after['artifacts'],'archive_or_promotion_changed_code'
 else:
  assert len(before['revisions'])==len(after['revisions'])
  for a,z in zip(before['revisions'],after['revisions']):
   if a['code_hash']!=selected_hash:assert a==z and before['artifacts'][a['id']]==after['artifacts'][a['id']]
   else:
    assert {k:v for k,v in a.items() if k not in ('deleted_at','stored_bytes')}=={k:v for k,v in z.items() if k not in ('deleted_at','stored_bytes')}
    assert z['deleted_at'] and z['stored_bytes']==0 and not after['artifacts'][z['id']]['exists'],'quiet_delete_not_physically_settled'

if mode in ('restore','rescue','evidence'):
 unit=sys.argv[4];assert re.fullmatch('serverless-restore-version-state-[0-9a-f]{32}',unit)
 folder=Path('/run')/unit;item=json.loads((folder/'identity.json').read_text());assert item['function_id']==function_id and item['namespace_id']==namespace
 if mode in ('restore','rescue'):
  receipt=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),*(['guard'] if mode=='rescue' else [])],timeout=190));receipt['guard_states']=finish_guard(unit);emit(receipt)
 else:
  p=folder/'restored-independent.json'
  if not p.exists():p=folder/'restored.json'
  emit(json.loads(p.read_text()) if p.exists() else {'event':'pending'})
 sys.exit(0)
if mode=='inspect':emit(durable());sys.exit(0)
selected_hash,action,replacement=sys.argv[4:7];assert re.fullmatch('[0-9a-f]{64}',selected_hash) and re.fullmatch('[0-9a-f]{64}',replacement) and selected_hash!=replacement
assert action in ('promote','archive','delete')
with read_control(control) as db:
 assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0]==1
 for sql in ("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')","SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'SELECT count(*) FROM function_operations','SELECT count(*) FROM execution_instances','SELECT coalesce(sum(reserved_bytes),0) FROM deployments'):
  assert db.execute(sql).fetchone()[0]==0,'quiet_installation_required'

registry=Path(values['SERVERLESS_STORAGE_ROOT_HOST'])/'registry.sqlite3'
assert (registry.stat().st_uid,registry.stat().st_gid)==(control.stat().st_uid,control.stat().st_gid),'registry_owner_mismatch'
with control_owner(control),closing(sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True)) as db:
 assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0,'quiet_storage_leases_required'
for kind in ('instance','validation'):
 assert not command(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind='+kind]),'untracked_consumers_present'
current = json.loads(command(docker + ['inspect', 'serverless-api']))[0]
reference = json.loads(command(docker + ['inspect', 'serverless-runtime-reference']))[0]
assert current['State']['Running'] and reference['State']['Running'], 'running_installation_required'
assert current['State']['Health']['Status'] == reference['State']['Health']['Status'] == 'healthy', 'healthy_installation_required'
init = current['State']['Pid']
descendants = [init]
for parent in descendants:
    descendants.extend(int(value) for value in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
processes = [pid for pid in descendants
             if Path(os.readlink(f'/proc/{pid}/exe')).name.startswith('python')
             and Path('/proc', str(pid), 'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00')]
assert len(processes) == 1, 'unique_control_process_required'
pid = processes[0]
assert Path('/proc', str(pid), 'cgroup').read_text() == Path('/proc', str(init), 'cgroup').read_text(), 'container_owner_required'
before = durable()
assert len(before['versions'])==2 and all(v['state']=='available' for v in before['versions'])
assert before['function']['active_revision_id']==next(v['revision_id'] for v in before['versions'] if v['code_hash']==(replacement if action=='promote' else selected_hash))
assert before['function']['first_promoted_at'] is not None
unit = 'serverless-restore-version-state-' + uuid4().hex
folder = Path('/run') / unit
folder.mkdir(mode=0o700)
lock = os.open(folder / 'mutation.lock', os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
info = os.fstat(lock)
item = {'function_id':function_id,'selected_hash':selected_hash,'action':action,'replacement':replacement,'official_sha256':{n:sha(n) for n in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},'restore_sha256':hashlib.sha256(RESTORE.encode()).hexdigest(),'kill_sha256':hashlib.sha256(KILL_CONTROL.encode()).hexdigest(),'operator_sha256':sha(__file__),'native_observer_sha256':sha(Path(__file__).with_name('native_control_observer.py')),'service_id': service, 'namespace_id': namespace, 'container_id': current['Id'], 'image': current['Image'],'started_at':current['State']['StartedAt'],
        'reference': [reference['Id'], reference['Image'], reference['State']['StartedAt']], 'docker': docker, 'pid': pid, 'birth': birth(pid),
        'cgroup': Path('/proc', str(pid), 'cgroup').read_text(), 'helper_pid': os.getpid(), 'helper_birth': birth(os.getpid()),
        'lock_identity': [info.st_dev, info.st_ino]}
(folder / 'identity.json').write_text(json.dumps(item))
(folder / 'restore.py').write_text(RESTORE)
(folder/'kill.py').write_text(KILL_CONTROL);os.chmod(folder/'kill.py',0o600)
os.chmod(folder/'identity.json',0o600);os.chmod(folder/'restore.py',0o600)
observer, armed = NativeObserver(pid), False
try:
    command(['systemd-run', '--quiet', '--collect', '--unit=' + unit, '--on-active=' + ('12s' if mode.endswith('watchdog') else '70s'),
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '--property=RuntimeMaxSec=190s', '--property=TimeoutStopSec=5s',
             '/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder), 'guard'])
    armed = True
    assert command(['systemctl', 'is-active', unit + '.timer']) == 'active', 'guard_not_armed'
    emit({'event': 'guard-armed', 'unit': unit})
    observer.start()
    emit({'event': 'armed', 'unit': unit, 'container_id': current['Id'], 'image': current['Image'], 'before': before})
    if mode.endswith('watchdog'):
        emit({'event': 'suspended', 'unit': unit})
        # Intentional observer death proves independent detach/resume and health.
        assert select.select([sys.stdin], [], [], 8)[0], 'watchdog_command_missing'
        assert sys.stdin.readline().strip() == 'lose-observer'
        emit({'event': 'observer-loss', 'signal': 'SIGKILL', 'unit': unit})
        os.kill(os.getpid(), signal.SIGKILL)
    suffix='' if action=='delete' else '/'+action
    expected=(('DELETE' if action=='delete' else 'POST')+f' /api/functions/{function_id}/versions/{selected_hash}'+suffix+' HTTP/1.1\r\n').encode('ascii')
    pending, offsets, target, gated = None, {}, None, False
    deadline = time.monotonic() + 45
    observer.resume()
    while not gated:
        stopped_signal = observer.wait(deadline)
        if stopped_signal != signal.SIGTRAP | 0x80:
            assert stopped_signal not in (signal.SIGSTOP, signal.SIGTRAP), 'unexpected_native_stop'
            observer.resume(stopped_signal)
            continue
        phase, data = observer.info()
        if phase == 1:
            number, *args = data
            pending = (number, args)
            fd = args[0]
            if number == 3:  # close: clear identities before descriptor reuse.
                offsets.pop(fd, None)
                assert fd != target, 'target_connection_closed_before_gate'
            if target is not None and fd == target and number in (1, 20, 44, 46):
                assert mode.endswith('after'), 'unexpected_response_gate'
                after = durable()
                committed(before,after)
                gated = True
                gate = {'boundary': 'before-send', 'syscall': number, 'durable': after}
        elif phase == 2 and pending:
            number, args = pending
            pending = None
            # CPython sockets use recvfrom; read is included for ABI completeness.
            if number in (0, 45) and data > 0:
                fd, pointer = args[:2]
                try:
                    link = os.readlink(f'/proc/{pid}/fd/{fd}')
                except FileNotFoundError:
                    link = ''
                if link.startswith('socket:[') and target is None and offsets.get(fd, 0) is not None:
                    # Require the actual upstream TCP socket listening on 18090.
                    inode = link[8:-1]
                    tcp = []
                    for name in ('tcp', 'tcp6'):
                        tcp.extend(line.split() for line in Path('/proc', str(pid), 'net', name).read_text().splitlines()[1:])
                    if any(row[9] == inode and row[1].endswith(':46AA') for row in tcp):
                        offset = observer.match_line(pointer, data, expected, offsets.get(fd, 0))
                        offsets[fd] = offset
                        if offset == len(expected):
                            target = fd
                            if mode.endswith('before'):
                                received = durable()
                                assert received==before,'decision_preceded_receive_gate'
                                gated = True
                                gate = {'boundary': 'after-receive', 'syscall': number, 'durable': received}
            if number in (1, 20, 44, 46) and data > 0:
                offsets.pop(args[0], None)
        if not gated:
            observer.resume()
    emit({'event': 'gated', **gate, 'service_id': service})
    assert select.select([sys.stdin], [], [], 8)[0], 'cut_command_missing'
    assert sys.stdin.readline().strip() == 'cut', 'cut_command_required'
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        (folder/'kill-started.json').write_text(json.dumps({'requested':True})+'\n');os.chmod(folder/'kill-started.json',0o600)
        stopped = subprocess.Popen(['/usr/bin/python3','-I',str(folder/'kill.py'),str(folder),str(lock)],
                                   pass_fds=(lock,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Consume the traced death so tini/Docker can observe actual termination.
        end = time.monotonic() + 10
        while True:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited:
                assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL, 'control_death_unconfirmed'
                observer.attached = False
                break
            assert time.monotonic() < end, 'control_death_not_observed'
            time.sleep(.01)
        stopped.communicate(timeout=40)
        assert stopped.returncode == 0, 'control_kill_failed'
        killed = json.loads(command(docker + ['inspect', current['Id']]))[0]
        assert not killed['State']['Running'] and killed['State']['ExitCode'] == 137, 'control_crash_unconfirmed'
        emit({'event': 'cut', 'exit_code': 137, 'durable': durable()})
    finally:
        # Never release the shared description while its bounded mutator lives.
        if 'stopped' in locals():
            stopped.communicate(timeout=50)
            assert stopped.poll() is not None,'stop_mutator_not_joined'
        fcntl.flock(lock, fcntl.LOCK_UN)
finally:
    observer.detach()
    os.close(lock)
    if armed:
        emit(json.loads(command(['/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder)], timeout=190)))
        emit({'event':'guard-finished','unit':unit,'states':finish_guard(unit)})
