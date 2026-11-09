# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md#garde-et-restitution
"""Exact DEV duplicate-artifact permission fault and guarded same-container restart."""
import fcntl,hashlib,json,os,re,select,shlex,signal,socket,stat,subprocess,sys,time
from pathlib import Path
from uuid import UUID
from control_database import read_control

ROOT=Path('/srv/p2enjoy-serverless')
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
mode,function,namespace=sys.argv[1:4]
assert all(str(UUID(v))==v for v in (function,namespace))
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields=shlex.split(line,comments=True)
    if len(fields)==1 and '=' in fields[0]:
        key,value=fields[0].split('=',1)
        if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST'):settings[key]=value
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);assert state==ROOT/'state' and state.resolve()==state
control=state/'control.sqlite3';docker=['runuser','-u','spark-docker','--','docker','--host','unix://'+settings['SERVERLESS_DOCKER_SOCKET_HOST']]
def emit(value):print(json.dumps(value),flush=True)
def command(args,timeout=25,**kwargs):
    value=subprocess.run(args,capture_output=True,text=True,timeout=timeout,cwd=ROOT,**kwargs)
    assert value.returncode==0,'operator_command_failed'
    return value.stdout.strip()
def rows(sql,args=()):
    with read_control(control) as db:return [dict(v) for v in db.execute(sql,args)]
owner=rows('SELECT n.name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?',(function,namespace))
assert len(owner)==1 and re.fullmatch(r'version-duplicate-recovery-[0-9a-f]{8}',owner[0]['name']),'owned_campaign_required'
assert not rows('SELECT 1 FROM functions WHERE deleted_at IS NULL AND id!=?',(function,)),'foreign_active_function'
installation=rows("SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
def write(path,value):
    pending=path.with_name(path.name+'.pending')
    with pending.open('w') as stream:json.dump(value,stream);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    pending.replace(path)
def configuration(item):
    return {'mounts':sorted([{k:m.get(k) for k in ('Type','Source','Destination','RW','Propagation')} for m in item['Mounts']],key=lambda m:m['Destination']),
        'host':{k:item['HostConfig'].get(k) for k in ('NetworkMode','ReadonlyRootfs','Memory','MemorySwap','NanoCpus','PidsLimit','CapDrop','SecurityOpt','Tmpfs')},
        'environment_sha256':hashlib.sha256(json.dumps(sorted(item['Config']['Env'])).encode()).hexdigest(),'command':item['Config']['Cmd'],'entrypoint':item['Config']['Entrypoint']}
def services():return json.loads(command(docker+['inspect','serverless-api','serverless-runtime-reference']))
def identities(items):return [{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'running':v['State']['Running'],'health':v['State'].get('Health',{}).get('Status'),'configuration':configuration(v)} for v in items]
def containers():
    ids=command(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind=validation']).split()
    return json.loads(command(docker+['inspect',*ids])) if ids else []
def snapshot(candidate):
    candidate=str(UUID(candidate));found=rows('SELECT id,state,error_code,reserved_bytes,revision_id,code_hash,code_changed,configuration_cipher IS NULL AS configuration_empty,validation_json FROM deployments WHERE id=? AND function_id=?',(candidate,function));assert len(found)==1
    row=found[0];validation=json.loads(row.pop('validation_json') or 'null');row['validation']={k:validation[k] for k in ('valid','error','container_removed','elapsed_seconds') if k in validation} if validation else None
    fn=rows('SELECT active_revision_id,updated_at,config_json,environment_json,secrets_cipher FROM functions WHERE id=?',(function,))[0]
    fn['configuration_sha256']=hashlib.sha256(json.dumps([fn.pop(k) for k in ('config_json','environment_json','secrets_cipher')]).encode()).hexdigest()
    paths={};revisions=rows('SELECT id,code_hash,stored_bytes,deleted_at FROM revisions WHERE function_id=? ORDER BY id',(function,))
    for key in {candidate,*[v['id'] for v in revisions]}:
        path=state/'artifacts'/key
        if path.exists():
            info=path.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==1001
            paths[key]={'exists':True,'identity':[info.st_dev,info.st_ino,info.st_uid,info.st_gid],'mode':stat.S_IMODE(info.st_mode),
                'files':{str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob('*')) if p.is_file()}}
        else:paths[key]={'exists':False}
    return {'observed_at_ns':str(time.time_ns()),'candidate':row,'function':fn,'revisions':revisions,'versions':rows('SELECT code_hash,revision_id,state FROM function_versions WHERE function_id=? ORDER BY code_hash',(function,)),
        'paths':paths,'validators':[{'id':v['Id'],'running':v['State']['Running'],'mounts':{m['Destination']:m['Source'] for m in v['Mounts']},'installation':v['Config']['Labels'].get('tech.p2enjoy.serverless.installation')} for v in containers()],
        'channels':[p.name for p in (state/'validation').iterdir()]}
def target_fd(candidate):
    fd=os.open(state,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for name in ('artifacts',candidate):
            child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child
        return fd
    except BaseException:os.close(fd);raise
def identity(fd):
    v=os.fstat(fd);return [v.st_dev,v.st_ino,v.st_uid,v.st_gid]
OPEN='''import json,os,sys
from pathlib import Path
caps=int(next(v.split(':',1)[1].strip() for v in Path('/proc/self/status').read_text().splitlines() if v.startswith('CapEff:')),16)
assert caps==0
try:
 fd=os.open('/state/artifacts/'+sys.argv[1],os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);os.close(fd);result=0
except OSError as error:result=error.errno
print(json.dumps({'errno':result,'cap_eff':caps,'uid':os.getuid()}))
'''

RESTORE=r'''import fcntl,hashlib,json,os,select,signal,socket,stat,subprocess,sys,time,urllib.request
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(110)
folder=Path(sys.argv[1]);trigger=sys.argv[2];info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-duplicate-code-') and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
for name in ('identity.json','restore.py','lock'):assert not (folder/name).is_symlink()
item=json.loads((folder/'identity.json').read_text());assert hashlib.sha256((folder/'restore.py').read_bytes()).hexdigest()==item['restore_sha256']
fd=os.open(folder/'lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fstat(fd);assert [lock.st_dev,lock.st_ino]==item['lock_identity'];fcntl.flock(fd,fcntl.LOCK_EX)
def command(args,timeout=25):return subprocess.check_output(args,text=True,timeout=timeout,cwd='/srv/p2enjoy-serverless').strip()
def inspect():return json.loads(command(item['docker']+['inspect',item['control']['id'],'serverless-runtime-reference']))
def config(v):
 return {'mounts':sorted([{k:m.get(k) for k in ('Type','Source','Destination','RW','Propagation')} for m in v['Mounts']],key=lambda m:m['Destination']),
  'host':{k:v['HostConfig'].get(k) for k in ('NetworkMode','ReadonlyRootfs','Memory','MemorySwap','NanoCpus','PidsLimit','CapDrop','SecurityOpt','Tmpfs')},
  'environment_sha256':hashlib.sha256(json.dumps(sorted(v['Config']['Env'])).encode()).hexdigest(),'command':v['Config']['Cmd'],'entrypoint':v['Config']['Entrypoint']}
def validate(items):
 current,reference=items
 assert current['Id']==item['control']['id'] and current['Image']==item['control']['image'] and config(current)==item['control']['configuration']
 assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==[item['reference'][k] for k in ('id','image','started_at')] and reference['State']['Running']
 assert config(reference)==item['reference']['configuration']
 if current['State']['StartedAt']!=item['control']['started_at']:assert (folder/'restart-intent.json').is_file(),'unexpected_control_restart'
 return current,reference
try:
 result={'trigger':trigger,'candidate_id':item['candidate_id'],'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth']}
 if trigger in ('independent','external-recovery'):
  try:process=os.pidfd_open(item['helper_pid'])
  except ProcessLookupError:result['helper_already_absent']=True
  else:
   try:
    birth=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]
    if birth==item['helper_birth']:
     args=Path('/proc',str(item['helper_pid']),'cmdline').read_bytes().split(b'\0')
     assert item['helper_path'].encode() in args and item['candidate_id'].encode() in args,'foreign_helper_process'
     signal.pidfd_send_signal(process,signal.SIGKILL);assert select.select([process],[],[],10)[0];result['helper_killed_by_guard']=True
    else:result['helper_pid_reused_no_signal']=True
   except FileNotFoundError:result['helper_already_absent']=True
   finally:os.close(process)
 if (folder/'restored.json').is_file():
  previous=json.loads((folder/'restored.json').read_text());current,reference=validate(inspect())
  assert previous['completed'] and [current['Id'],current['State']['StartedAt']]==[previous['control_id'],previous['started_at']] and current['State']['Running']
  assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'
  for name,digest in item['official_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
  print(json.dumps(previous),flush=True);sys.exit(0)
 current,reference=validate(inspect())
 directory=os.open(item['state'],os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  for name in ('artifacts',item['candidate_id']):
   child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory);os.close(directory);directory=child
  before=os.fstat(directory);assert [before.st_dev,before.st_ino,before.st_uid,before.st_gid]==item['artifact_identity'],'candidate_inode_changed'
  os.fchmod(directory,item['artifact_mode']);after=os.fstat(directory);assert stat.S_IMODE(after.st_mode)==item['artifact_mode']
  result['permission']={'identity':item['artifact_identity'],'previous_mode':stat.S_IMODE(before.st_mode),'mode':item['artifact_mode']}
 except FileNotFoundError:
  sys.path.insert(0,'/srv/p2enjoy-serverless/e2e');from control_database import read_control
  with read_control(Path(item['state'])/'control.sqlite3') as db:
   candidate=db.execute('SELECT state,reserved_bytes,revision_id FROM deployments WHERE id=? AND function_id=?',(item['candidate_id'],item['function_id'])).fetchone()
   assert candidate and candidate['state']=='published' and candidate['reserved_bytes']==0 and candidate['revision_id']!=item['candidate_id'],'candidate_disappearance_unconfirmed'
  assert not (Path(item['state'])/'artifacts'/item['candidate_id']).exists()
  result['permission']={'already_cleaned':True,'identity':item['artifact_identity'],'mode':item['artifact_mode']}
 finally:os.close(directory)
 if not current['State']['Running']:
  assert item['allow_restart'] and (folder/'interrupt-intent.json').is_file(),'restart_not_authorized'
  assert current['State']['StartedAt']==item['control']['started_at'] and current['State']['ExitCode']==137,'original_control_not_stopped137'
  intent=folder/'restart-intent.json';assert not intent.exists(),'restart_outcome_unknown_requires_review'
  with intent.open('x') as stream:json.dump({'id':current['Id'],'old_started_at':current['State']['StartedAt']},stream);stream.flush();os.fsync(stream.fileno())
  command(item['docker']+['start',current['Id']]);result['restart_performed']=True
 else:result['restart_performed']=False
 deadline=time.monotonic()+75
 while True:
  current,reference=validate(inspect())
  try:
   with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:healthy=response.status==200 and json.load(response)['status']=='ok'
  except OSError:healthy=False
  if healthy and current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy':break
  assert current['State']['Running'] and time.monotonic()<deadline,'control_not_recovered';time.sleep(.3)
 for name,digest in item['official_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
 result.update(completed=True,control_id=current['Id'],image=current['Image'],started_at=current['State']['StartedAt'],reference_unchanged=True,official_unchanged=True)
 receipt=folder/'restored.json'
 if receipt.exists():result=json.loads(receipt.read_text());assert result['completed'] and result['control_id']==current['Id']
 else:
  pending=folder/'restored.pending';pending.write_text(json.dumps(result));pending.replace(receipt)
 print(json.dumps(result),flush=True)
finally:os.close(fd)
'''

def load(unit):
    assert re.fullmatch(r'serverless-restore-duplicate-code-[0-9a-f]{32}',unit)
    folder=Path('/run')/unit;info=folder.lstat();assert info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700 and not folder.is_symlink()
    item=json.loads((folder/'identity.json').read_text());assert item['function_id']==function and item['namespace_id']==namespace
    assert hashlib.sha256((folder/'restore.py').read_bytes()).hexdigest()==item['restore_sha256']
    return folder,item
def unit_states(unit):
    result={}
    for suffix in ('timer','service'):
        p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=MainPID','--property=LoadState'],capture_output=True,text=True,timeout=10)
        result[suffix]=dict(line.split('=',1) for line in p.stdout.splitlines())
    return result

if mode=='fault':
    child=os.fork()
    if child:
        try:child_birth=Path('/proc',str(child),'stat').read_text().rsplit(')',1)[1].split()[19]
        except FileNotFoundError:child_birth=None
        _,status=os.waitpid(child,0)
        emit({'event':'helper-terminated','pid':child,'birth':child_birth,'signaled':os.WIFSIGNALED(status),'signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None})
        sys.exit(0 if os.WIFEXITED(status) and os.WEXITSTATUS(status)==0 else 1)

if mode=='inspect':emit(snapshot(sys.argv[4]))
elif mode=='preflight':
    assert not rows('SELECT 1 FROM execution_instances') and not rows('SELECT 1 FROM function_operations')
    assert not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')")
    assert not rows("SELECT 1 FROM deployments WHERE state IN ('receiving','validating')") and not containers() and not list((state/'validation').iterdir())
    items=identities(services());assert all(v['running'] and v['health']=='healthy' for v in items)
    emit({'ready':True,'services':items,'official_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')}})
elif mode in ('evidence','release','interrupt'):
    folder,item=load(sys.argv[4])
    if mode=='release':
        command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'external-recovery'],timeout=120)
        p=subprocess.run(['systemctl','stop',folder.name+'.timer'],capture_output=True,text=True,timeout=10)
        states=unit_states(folder.name);assert p.returncode==0 or (p.returncode==5 and states['timer'].get('LoadState')=='not-found')
    if mode=='interrupt':
        with (folder/'lock').open('r+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            assert item['allow_restart'] and time.monotonic()<item['armed_monotonic']+item['delay_seconds']-10
            assert unit_states(folder.name)['timer']['ActiveState']=='active'
            value=snapshot(item['candidate_id']);candidate=value['candidate']
            assert candidate['state']=='published' and candidate['reserved_bytes']>0 and candidate['revision_id']!=candidate['id']
            assert candidate['validation']['valid'] and candidate['validation']['container_removed'] and not value['validators'] and not value['channels']
            assert not rows('SELECT 1 FROM execution_instances') and not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')")
            current=identities(services());assert current[0]['id']==item['control']['id'] and current[0]['started_at']==item['control']['started_at'] and current[0]['configuration']==item['control']['configuration'] and current[1]==item['reference']
            write(folder/'interrupt-intent.json',{'control_id':item['control']['id'],'old_started_at':item['control']['started_at'],'candidate_id':item['candidate_id']})
            command(docker+['kill','--signal','KILL',item['control']['id']]);stopped=services()[0]
            assert stopped['Id']==item['control']['id'] and not stopped['State']['Running'] and stopped['State']['ExitCode']==137
            write(folder/'interrupted.json',{'exit_code':137,'control_id':stopped['Id'],'old_started_at':stopped['State']['StartedAt'],'candidate':snapshot(item['candidate_id'])})
    emit({'unit':folder.name,'identity':item,'states':unit_states(folder.name),'restored':json.loads((folder/'restored.json').read_text()) if (folder/'restored.json').exists() else None,'interrupted':json.loads((folder/'interrupted.json').read_text()) if (folder/'interrupted.json').exists() else None})
elif mode=='fault':
    candidate,kind,unit=sys.argv[4:7];assert kind in ('normal','restart') and re.fullmatch(r'serverless-restore-duplicate-code-[0-9a-f]{32}',unit)
    deadline=time.monotonic()+10
    while True:
        before=snapshot(candidate);matched=[v for v in before['validators'] if v['mounts'].get('/code')==str(state/'artifacts'/candidate/'code') and v['running']]
        assert before['candidate']['state']=='validating' and before['candidate']['reserved_bytes']>0
        if len(matched)==1:
            assert matched[0]['installation']==installation and len(before['validators'])==1
            program='const fs=require("node:fs"),p="/tmp/validator-name-import.json";process.stdout.write(fs.existsSync(p)?fs.readFileSync(p,"utf8"):"null")'
            marker=json.loads(command(docker+['exec',matched[0]['id'],'node','-e',program]))
            if marker:assert marker['mode']=='success' and marker['pid']>0;break
        assert time.monotonic()<deadline,'real_import_marker_missing';time.sleep(.05)
    assert not any(v['id']==candidate for v in before['revisions'])
    assert not rows('SELECT 1 FROM execution_instances') and not rows('SELECT 1 FROM function_operations')
    assert len(rows("SELECT id FROM deployments WHERE state IN ('receiving','validating')"))==1
    items=identities(services());assert all(v['running'] and v['health']=='healthy' for v in items)
    directory=target_fd(candidate);original=identity(directory);original_mode=stat.S_IMODE(os.fstat(directory).st_mode)
    assert original==before['paths'][candidate]['identity'] and original_mode==before['paths'][candidate]['mode'] and original_mode==0o700
    folder=Path('/run')/unit;folder.mkdir(mode=0o700);lock=os.open(folder/'lock',os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600);lock_info=os.fstat(lock);os.close(lock)
    item={'function_id':function,'namespace_id':namespace,'candidate_id':candidate,'state':str(state),'artifact_identity':original,'artifact_mode':original_mode,
        'control':items[0],'reference':items[1],'docker':docker,'allow_restart':kind=='restart','delay_seconds':45 if kind=='restart' else 90,
        'helper_pid':os.getpid(),'helper_birth':Path('/proc',str(os.getpid()),'stat').read_text().rsplit(')',1)[1].split()[19],'helper_path':str(ROOT/'e2e/function-version-duplicate-recovery-operator.py'),
        'lock_identity':[lock_info.st_dev,lock_info.st_ino],'restore_sha256':hashlib.sha256(RESTORE.encode()).hexdigest(),'armed_monotonic':time.monotonic(),
        'official_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')}}
    write(folder/'identity.json',item);(folder/'restore.py').write_text(RESTORE);armed=False
    try:
        def interrupted(*_):raise InterruptedError('fault_helper_interrupted')
        for value in (signal.SIGHUP,signal.SIGTERM,signal.SIGINT):signal.signal(value,interrupted)
        command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active='+str(item['delay_seconds'])+'s','--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0','--property=RuntimeMaxSec=115s','/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'independent']);armed=True
        assert unit_states(unit)['timer']['ActiveState']=='active';emit({'event':'guard-armed','unit':unit})
        assert identity(directory)==original;os.fchmod(directory,0);assert stat.S_IMODE(os.fstat(directory).st_mode)==0
        denied=json.loads(command(docker+['exec','serverless-api','python','-B','-c',OPEN,candidate]));assert denied['errno']==13 and denied['cap_eff']==0
        emit({'event':'fault-active','unit':unit,'before':before,'marker':marker,'denied':denied,'artifact_identity':original,'artifact_mode':original_mode})
        assert select.select([sys.stdin],[],[],80)[0],'fault_release_timeout'
        action=sys.stdin.readline().strip()
        if action=='kill-helper':emit({'event':'helper-sigkill','pid':os.getpid(),'birth':item['helper_birth']});os.kill(os.getpid(),signal.SIGKILL)
        assert action=='release','invalid_fault_action'
    finally:
        os.close(directory)
        if armed:
            restored=json.loads(command(['/usr/bin/python3','-I',str(folder/'restore.py'),str(folder),'explicit'],timeout=120))
            p=subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,text=True,timeout=10);states=unit_states(unit)
            assert p.returncode==0 or (p.returncode==5 and states['timer'].get('LoadState')=='not-found')
            emit({'event':'permission-restored','unit':unit,'restored':restored})
else:raise RuntimeError('unknown_mode')
