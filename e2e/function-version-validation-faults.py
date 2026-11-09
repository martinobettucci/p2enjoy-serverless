# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md#deux-erreurs-de-nettoyage-distinctes
"""Real DEV permissions faults for an exact validation pair, with restoration guard."""
import hashlib,json,os,re,select,shlex,signal,socket,stat,subprocess,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
mode,function,namespace=sys.argv[1:4]
assert all(str(UUID(v))==v for v in (function,namespace))
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields=shlex.split(line,comments=True)
    if len(fields)==1 and '=' in fields[0]:
        key,value=fields[0].split('=',1)
        if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST'):settings[key]=value
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);assert state.parent==Path('/srv/p2enjoy-serverless') and state.resolve()==state
control=state/'control.sqlite3'
docker=['docker','--host','unix://'+settings['SERVERLESS_DOCKER_SOCKET_HOST']]

def emit(value):print(json.dumps(value),flush=True)
def command(args,**options):
    p=subprocess.run(args,text=True,capture_output=True,timeout=25,**options)
    assert p.returncode==0,'operator_command_failed'
    return p.stdout.strip()
def rows(sql,args=()):
    with read_control(control) as db:return [dict(r) for r in db.execute(sql,args)]

owner=rows('''SELECT n.name FROM functions f JOIN services s ON s.id=f.service_id
    JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?''',(function,namespace))
assert len(owner)==1 and re.fullmatch(r'version-validation-[0-9a-f]{8}',owner[0]['name']),'owned_campaign_required'
assert not rows('SELECT 1 FROM functions WHERE deleted_at IS NULL AND id!=?',(function,)),'foreign_active_function'
installation=rows("SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']

def validators():
    ids=command(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation,
        '--filter','label=tech.p2enjoy.serverless.kind=validation']).split()
    return json.loads(command(docker+['inspect',*ids])) if ids else []

CONNECT='''import json,socket
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
try:s.connect('/docker.sock');print(json.dumps({'connected':True,'errno':None}))
except OSError as error:print(json.dumps({'connected':False,'errno':error.errno}))
finally:s.close()
'''
OPEN_DIRECTORY='''import json,os,sys
try:
 fd=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);os.close(fd);print(json.dumps({'opened':True,'errno':None}))
except OSError as error:print(json.dumps({'opened':False,'errno':error.errno}))
'''

def socket_details():
    info=json.loads(command(docker+['inspect','serverless-api']))[0]
    mount=[m for m in info['Mounts'] if m['Destination']=='/docker.sock'];assert len(mount)==1
    path=Path(mount[0]['Source']);assert str(path)==settings['SERVERLESS_DOCKER_SOCKET_HOST']
    value=path.lstat();assert stat.S_ISSOCK(value.st_mode) and value.st_uid==control.stat().st_uid
    connected=json.loads(command(docker+['exec','serverless-api','python','-B','-c',CONNECT]))
    return {'path':str(path),'identity':[value.st_dev,value.st_ino],'uid':value.st_uid,'gid':value.st_gid,
        'mode':stat.S_IMODE(value.st_mode),'connection':connected}

def snapshot(candidate):
    candidate=str(UUID(candidate));found=rows('''SELECT id,state,error_code,reserved_bytes,revision_id,
        configuration_cipher IS NULL AS configuration_empty,validation_json
        FROM deployments WHERE id=? AND function_id=?''',(candidate,function));assert len(found)==1
    row=found[0];value=json.loads(row.pop('validation_json') or 'null')
    row['validation']={k:value[k] for k in ('valid','error','container_removed','elapsed_seconds') if k in value} if value else None
    code=state/'artifacts'/candidate/'code';matched=[]
    for item in validators():
        mounts={m['Destination']:m['Source'] for m in item['Mounts']}
        if mounts.get('/code')!=str(code):continue
        labels=item['Config']['Labels'];assert labels['tech.p2enjoy.serverless.installation']==installation
        channel=Path(mounts['/protocol']);assert channel.parent==state/'validation' and channel.name.startswith('v-')
        marker=None
        if item['State']['Running']:
            program='const fs=require("node:fs"),p="/tmp/storage-validation-import.json";process.stdout.write(fs.existsSync(p)?fs.readFileSync(p,"utf8"):"null")'
            marker=json.loads(command(docker+['exec',item['Id'],'node','-e',program]))
            if marker:assert marker['revision']==json.loads((code/'revision.json').read_text())['revision'] and marker['pid']>0
        matched.append({'id':item['Id'],'running':item['State']['Running'],'marker':marker,'channel':channel.name,'channel_present':channel.is_dir()})
    fn=rows('SELECT active_revision_id,updated_at,config_json,environment_json,secrets_cipher FROM functions WHERE id=?',(function,))[0]
    configuration_sha256=hashlib.sha256(json.dumps([fn.pop(k) for k in ('config_json','environment_json','secrets_cipher')]).encode()).hexdigest()
    archive=state/'artifacts'/candidate/'archive.zip'
    return {'candidate':row,'validators':matched,'global_validators':[c['Id'] for c in validators()],
        'channels':[{'name':p.name,'mode':stat.S_IMODE(p.lstat().st_mode)} for p in (state/'validation').iterdir()],
        'code_present':code.is_dir(),'archive_present':archive.is_file(),
        'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest() if archive.is_file() else None,
        'function':{**fn,'configuration_sha256':configuration_sha256},
        'revisions':rows('SELECT id,code_hash,stored_bytes,deleted_at FROM revisions WHERE function_id=?',(function,))}

RESTORE='''import json,os,select,signal,socket,stat,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
item=json.loads(sys.argv[1]);independent=sys.argv[2]=='guard'
if independent:
 try:fd=os.pidfd_open(item['helper_pid'])
 except ProcessLookupError:pass
 else:
  try:
   birth=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]
   if birth==item['helper_birth']:
    signal.pidfd_send_signal(fd,signal.SIGKILL);assert select.select([fd],[],[],10)[0],'helper_stop_unconfirmed'
  except (ProcessLookupError,FileNotFoundError):pass
  finally:os.close(fd)
path=Path(item['path'])
flags=os.O_NOFOLLOW|(os.O_RDONLY|os.O_DIRECTORY if item['kind']=='channel' else os.O_PATH)
fd=os.open(path,flags)
try:
 before=os.fstat(fd)
 assert [before.st_dev,before.st_ino]==item['identity'] and (before.st_uid,before.st_gid)==(item['uid'],item['gid'])
 assert (stat.S_ISDIR(before.st_mode) if item['kind']=='channel' else stat.S_ISSOCK(before.st_mode))
 if item['kind']=='channel':os.fchmod(fd,item['mode'])
 else:
  pinned='/proc/self/fd/'+str(fd);resolved=os.stat(pinned)
  assert [resolved.st_dev,resolved.st_ino]==item['identity']
  os.chmod(pinned,item['mode'])
 after=os.fstat(fd)
 assert [after.st_dev,after.st_ino]==item['identity'] and stat.S_IMODE(after.st_mode)==item['mode'],'permission_restore_failed'
finally:os.close(fd)
p=subprocess.run(item['docker']+['exec','serverless-api','python','-B','-c',item['connect']],capture_output=True,text=True,timeout=20,check=True)
assert json.loads(p.stdout)['connected'],'docker_not_accessible_after_restore'
print(json.dumps({'event':'permission-restored','function_id':item['function_id'],'candidate_id':item['candidate_id'],
 'kind':item['kind'],'independent':independent,'previous_mode':stat.S_IMODE(before.st_mode),'mode':item['mode'],
 'identity':item['identity'],'uid':item['uid'],'gid':item['gid'],'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth'],'docker_connected':True,'mutation_on_pinned_inode':True}),flush=True)
'''

def set_permission(item,mode):
    flags=os.O_NOFOLLOW|(os.O_RDONLY|os.O_DIRECTORY if item['kind']=='channel' else os.O_PATH)
    fd=os.open(item['path'],flags)
    try:
        before=os.fstat(fd)
        assert [before.st_dev,before.st_ino]==item['identity'] and (before.st_uid,before.st_gid)==(item['uid'],item['gid'])
        assert (stat.S_ISDIR(before.st_mode) if item['kind']=='channel' else stat.S_ISSOCK(before.st_mode))
        if item['kind']=='channel':os.fchmod(fd,mode)
        else:
            pinned='/proc/self/fd/'+str(fd);resolved=os.stat(pinned)
            assert [resolved.st_dev,resolved.st_ino]==item['identity']
            os.chmod(pinned,mode)
        after=os.fstat(fd)
        assert [after.st_dev,after.st_ino]==item['identity'] and stat.S_IMODE(after.st_mode)==mode
        return {'identity':item['identity'],'mode':mode,'mutation_on_pinned_inode':True}
    finally:os.close(fd)

def guard_evidence(unit):
    assert re.fullmatch(r'serverless-restore-version-validation-[0-9a-f]{32}',unit)
    events=[]
    for line in command(['journalctl','--no-pager','-o','cat','-u',unit+'.service']).splitlines():
        if line.startswith('{'):
            value=json.loads(line)
            if value.get('event')=='permission-restored' and value['function_id']==function:events.append(value)
    states={}
    for suffix in ('timer','service'):
        p=subprocess.run(['systemctl','is-active',unit+'.'+suffix],capture_output=True,text=True,timeout=10)
        value=p.stdout.strip();assert value in ('active','inactive','activating','deactivating','failed','unknown')
        states[suffix]=value
    return {'events':events,'unit_states':states}

if mode=='preflight':
    assert 'name=rootless' in json.loads(command(docker+['info','--format','{{json .SecurityOptions}}']))
    assert not rows('SELECT 1 FROM execution_instances')
    assert not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')")
    assert not rows("SELECT 1 FROM deployments WHERE state IN ('receiving','validating')")
    assert not rows('SELECT 1 FROM function_operations') and not validators() and not list((state/'validation').iterdir())
    value=socket_details();assert value['mode'] and value['connection']['connected']
    emit({'ready':True,'socket':value,'observed_at_ns':str(time.time_ns())})
elif mode=='socket-status':emit(socket_details())
elif mode=='inspect':emit(snapshot(sys.argv[4]))
elif mode=='guard-evidence':emit(guard_evidence(sys.argv[4]))
elif mode=='history':
    start=int(sys.argv[4]);assert 0<time.time_ns()-start<180*10**9
    end=time.time_ns();events=[]
    raw=command(docker+['events','--since',str(start//10**9),'--until',str(end//10**9+1),
        '--filter','type=container','--filter','event=create',
        '--filter','label=tech.p2enjoy.serverless.installation='+installation,
        '--filter','label=tech.p2enjoy.serverless.kind=validation','--format','{{json .}}'])
    for line in raw.splitlines():
        value=json.loads(line)
        if start<=value['timeNano']<=end:
            assert value['Action']=='create';events.append({'container_id':value['Actor']['ID'],'time_ns':str(value['timeNano'])})
    emit({'started_at_ns':str(start),'ended_at_ns':str(end),'creates':events})
elif mode=='fault':
    first,second,kind=sys.argv[4:7];assert kind in ('socket','channel')
    assert all(str(UUID(v))==v for v in (first,second)) and first!=second
    deadline=time.monotonic()+12
    while True:
        a,b=snapshot(first),snapshot(second)
        if (a['candidate']['state']==b['candidate']['state']=='validating' and len(a['validators'])==1
            and a['validators'][0]['marker'] and not b['validators']):break
        assert time.monotonic()<deadline,'admitted_pair_not_observed';time.sleep(.05)
    assert len(validators())==1 and a['validators'][0]['running']
    assert a['candidate']['reserved_bytes']>0 and b['candidate']['reserved_bytes']>0 and b['code_present']
    assert not rows('SELECT 1 FROM execution_instances') and not rows('SELECT 1 FROM function_operations')
    assert not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')")
    assert not rows("SELECT 1 FROM deployments WHERE state IN ('receiving','validating') AND id NOT IN (?,?)",(first,second))
    original=socket_details();assert original['mode'] and original['connection']['connected']
    if kind=='socket':item={k:original[k] for k in ('path','identity','uid','gid','mode')}
    else:
        path=state/'validation'/a['validators'][0]['channel'];info=path.lstat()
        assert stat.S_ISDIR(info.st_mode) and info.st_uid==control.stat().st_uid
        item={'path':str(path),'identity':[info.st_dev,info.st_ino],'uid':info.st_uid,'gid':info.st_gid,'mode':stat.S_IMODE(info.st_mode)}
    item.update(kind=kind,function_id=function,candidate_id=first,docker=docker,connect=CONNECT,helper_pid=os.getpid(),
        helper_birth=Path('/proc',str(os.getpid()),'stat').read_text().rsplit(')',1)[1].split()[19])
    unit='serverless-restore-version-validation-'+uuid4().hex
    command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active='+('90s' if kind=='socket' else '35s'),
        '--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0',
        '/usr/bin/python3','-I','-c',RESTORE,json.dumps(item),'guard'])
    def interrupted(*_):raise InterruptedError('fault_helper_interrupted')
    for signum in (signal.SIGHUP,signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
    try:
        assert command(['systemctl','is-active',unit+'.timer'])=='active'
        emit({'event':'guard-armed','unit':unit,'kind':kind,'identity':item['identity'],'mode':item['mode']})
        changed=set_permission(item,0)
        if kind=='socket':denied=socket_details()['connection'];assert denied=={'connected':False,'errno':13}
        else:
            denied=json.loads(command(docker+['exec','serverless-api','python','-B','-c',OPEN_DIRECTORY,'/state/validation/'+Path(item['path']).name]))
            assert denied=={'opened':False,'errno':13} and socket_details()['connection']['connected']
        emit({'event':'fault-active','kind':kind,'first':a,'second':b,'target':{k:item[k] for k in ('identity','uid','gid','mode')},'denied':denied,'permission_change':changed})
        assert select.select([sys.stdin],[],[],70)[0],'fault_release_timeout'
        action=sys.stdin.readline().strip()
        if action=='kill-helper':
            emit({'event':'helper-sigkill','pid':os.getpid(),'birth':item['helper_birth']});os.kill(os.getpid(),signal.SIGKILL)
        assert action=='resume','invalid_release'
    finally:
        restored=json.loads(command(['/usr/bin/python3','-I','-c',RESTORE,json.dumps(item),'normal']))
        emit(restored);command(['systemctl','stop',unit+'.timer'])
else:raise RuntimeError('unknown_mode')
