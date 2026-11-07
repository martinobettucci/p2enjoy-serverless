# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
"""Bounded real Docker socket denial while an owned upload validates in DEV."""
from contextlib import closing
import hashlib,json,os,re,select,shlex,signal,socket,sqlite3,stat,subprocess,sys,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
mode,function,namespace=sys.argv[1:4]
assert str(UUID(function))==function and str(UUID(namespace))==namespace
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields=shlex.split(line,comments=True)
    if len(fields)==1 and '=' in fields[0]:
        key,value=fields[0].split('=',1)
        if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST'):settings[key]=value
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);control=state/'control.sqlite3'
docker=['docker','--host','unix://'+settings['SERVERLESS_DOCKER_SOCKET_HOST']]

def emit(value):print(json.dumps(value),flush=True)
def command(args,**kwargs):
    value=subprocess.run(args,text=True,capture_output=True,timeout=20,**kwargs)
    assert value.returncode==0,'operator_command_failed'
    return value.stdout.strip()
def rows(sql,args=()):
    with read_control(control) as db:return [dict(row) for row in db.execute(sql,args)]

owned=rows('''SELECT f.id,n.name FROM functions f JOIN services s ON s.id=f.service_id
    JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?''',(function,namespace))
assert len(owned)==1 and re.fullmatch(r'storage-validation-[0-9a-f]{8}',owned[0]['name']),'owned_campaign_required'
assert not rows('''SELECT 1 FROM functions f JOIN services s ON s.id=f.service_id
    WHERE f.deleted_at IS NULL AND s.namespace_id!=?''',(namespace,)),'foreign_active_function'
installation=rows("SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']

def containers():
    identifiers=command(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation,
        '--filter','label=tech.p2enjoy.serverless.kind=validation']).split()
    return json.loads(command(docker+['inspect',*identifiers])) if identifiers else []

def snapshot(candidate):
    candidate=str(UUID(candidate))
    found=rows('''SELECT id,state,error_code,reserved_bytes,revision_id,
        configuration_cipher IS NULL AS configuration_empty,validation_json
        FROM deployments WHERE id=? AND function_id=?''',(candidate,function))
    assert len(found)==1,'owned_candidate_required'
    row=found[0];validation=json.loads(row.pop('validation_json') or 'null')
    row['validation']={k:validation[k] for k in ('valid','error','container_removed','elapsed_seconds') if k in validation} if validation else None
    code=state/'artifacts'/candidate/'code';matched=[]
    for item in containers():
        mounts={entry['Destination']:entry['Source'] for entry in item['Mounts']}
        if mounts.get('/code')!=str(code):continue
        labels=item['Config']['Labels']
        assert labels['tech.p2enjoy.serverless.installation']==installation and labels['tech.p2enjoy.serverless.kind']=='validation'
        channel=Path(mounts['/protocol']);assert channel.parent==state/'validation' and channel.name.startswith('v-')
        marker=None
        if item['State']['Running']:
            program='const fs=require("node:fs"),p="/tmp/storage-validation-import.json";process.stdout.write(fs.existsSync(p)?fs.readFileSync(p,"utf8"):"null")'
            marker=json.loads(command(docker+['exec',item['Id'],'node','-e',program]))
            if marker:
                assert marker['revision']==json.loads((code/'revision.json').read_text())['revision'] and marker['pid']>0,'import_marker_mismatch'
        matched.append({'id':item['Id'],'running':item['State']['Running'],'marker':marker,'channel':channel.name,'channel_present':channel.is_dir()})
    archive=state/'artifacts'/candidate/'archive.zip'
    return {'candidate':row,'validators':matched,'channels':[p.name for p in (state/'validation').iterdir()],
        'code_present':code.is_dir(),'archive_present':archive.is_file(),
        'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest() if archive.is_file() else None,
        'function':rows('SELECT id,purged_at FROM functions WHERE id=?',(function,))[0],
        'guards':rows('SELECT id,kind,decision,error_code FROM function_operations WHERE function_id=?',(function,)),
        'commands':rows('SELECT id,state,phase,error_code,result_version FROM storage_commands WHERE function_id=?',(function,)),
        'revisions':rows('SELECT id,stored_bytes,deleted_at FROM revisions WHERE function_id=?',(function,))}

CONNECT='''import errno,json,socket
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
try:
 s.connect('/docker.sock');print(json.dumps({'connected':True,'errno':None}))
except OSError as error:print(json.dumps({'connected':False,'errno':error.errno}))
finally:s.close()
'''
def socket_details():
    info=json.loads(command(docker+['inspect','serverless-api']))[0]
    mounts=[item for item in info['Mounts'] if item['Destination']=='/docker.sock']
    assert len(mounts)==1 and mounts[0]['Source']==settings['SERVERLESS_DOCKER_SOCKET_HOST'],'docker_socket_mismatch'
    path=Path(mounts[0]['Source']);value=path.lstat()
    assert stat.S_ISSOCK(value.st_mode) and value.st_uid==control.stat().st_uid,'docker_socket_owner_mismatch'
    connection=json.loads(command(docker+['exec','serverless-api','python','-B','-c',CONNECT]))
    return {'path':str(path),'identity':[value.st_dev,value.st_ino],'uid':value.st_uid,'gid':value.st_gid,'mode':stat.S_IMODE(value.st_mode),'connection':connection}

RESTORE='''import json,os,select,signal,socket,stat,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
item=json.loads(sys.argv[1]);guard=sys.argv[2]=='guard'
if guard:
 try:fd=os.pidfd_open(item['helper_pid'])
 except ProcessLookupError:pass
 else:
  try:
   birth=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]
   if birth==item['helper_birth']:
    signal.pidfd_send_signal(fd,signal.SIGKILL)
    ready,_,_=select.select([fd],[],[],10)
    assert ready,'helper_stop_unconfirmed'
  except (ProcessLookupError,FileNotFoundError):pass
  finally:os.close(fd)
path=Path(item['path']);before=path.lstat()
assert stat.S_ISSOCK(before.st_mode) and [before.st_dev,before.st_ino]==item['identity'],'socket_replaced'
assert (before.st_uid,before.st_gid)==(item['uid'],item['gid']),'socket_owner_changed'
os.chmod(path,item['mode'],follow_symlinks=False)
after=path.lstat();assert [after.st_dev,after.st_ino]==item['identity'] and stat.S_IMODE(after.st_mode)==item['mode'],'socket_restore_failed'
result=subprocess.run(item['docker']+['exec','serverless-api','python','-B','-c',item['connect']],capture_output=True,text=True,timeout=20,check=True)
connection=json.loads(result.stdout);assert connection['connected'],'control_socket_not_restored'
print(json.dumps({'event':'socket-restored','function_id':item['function_id'],'candidate_id':item['candidate_id'],
 'independent':guard,'previous_mode':stat.S_IMODE(before.st_mode),'mode':item['mode'],'identity':item['identity'],'control_connected':True}),flush=True)
'''

if mode=='inspect':emit(snapshot(sys.argv[4]))
elif mode=='socket-status':emit(socket_details())
elif mode=='preflight':
    assert 'name=rootless' in json.loads(command(docker+['info','--format','{{json .SecurityOptions}}'])),'rootless_docker_required'
    assert not rows('SELECT 1 FROM execution_instances'),'instances_present'
    assert not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')"),'active_invocations_present'
    assert not rows("SELECT 1 FROM deployments WHERE state IN ('receiving','validating')"),'active_upload_present'
    assert not rows('SELECT 1 FROM function_operations'),'operation_present'
    assert not containers() and not list((state/'validation').iterdir()),'validation_cleanup_pending'
    value=socket_details();assert value['mode'] and value['connection']['connected']
    emit({'ready':True,'socket':value})
elif mode=='guard-evidence':
    unit=sys.argv[4];assert re.fullmatch(r'serverless-restore-validation-socket-[0-9a-f]{32}',unit)
    events=[]
    for line in command(['journalctl','--no-pager','-o','cat','-u',unit+'.service']).splitlines():
        if line.startswith('{'):
            value=json.loads(line)
            if value.get('event')=='socket-restored' and value['function_id']==function:events.append(value)
    emit({'events':events})
elif mode in ('deny-docker','watchdog-docker'):
    candidate=str(UUID(sys.argv[4]));deadline=time.monotonic()+20
    while True:
        observed=snapshot(candidate)
        if observed['candidate']['state']=='validating' and len(observed['validators'])==1 and observed['validators'][0]['marker']:break
        assert time.monotonic()<deadline,'active_validation_not_observed';time.sleep(.05)
    assert observed['validators'][0]['running'] and len(containers())==1,'single_live_validation_required'
    assert not rows('SELECT 1 FROM execution_instances'),'instances_present'
    assert not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')"),'active_invocations_present'
    assert not rows("SELECT 1 FROM deployments WHERE state IN ('receiving','validating') AND id!=?",(candidate,)),'foreign_upload_present'
    item=socket_details();assert item['mode'] and item.pop('connection')['connected']
    item.update(function_id=function,candidate_id=candidate,docker=docker,connect=CONNECT,helper_pid=os.getpid(),
        helper_birth=Path('/proc',str(os.getpid()),'stat').read_text().rsplit(')',1)[1].split()[19])
    unit='serverless-restore-validation-socket-'+uuid4().hex
    command(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active='+('5s' if mode=='watchdog-docker' else '90s'),
        '--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0',
        '/usr/bin/python3','-I','-c',RESTORE,json.dumps(item),'guard'])
    def interrupted(signum,frame):raise InterruptedError('operator_interrupted')
    for signum in (signal.SIGHUP,signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
    try:
        assert command(['systemctl','is-active',unit+'.timer'])=='active','independent_guard_not_armed'
        emit({'event':'guard-armed','unit':unit,'socket':{k:item[k] for k in ('path','identity','uid','gid','mode')}})
        value=Path(item['path']).lstat();assert [value.st_dev,value.st_ino]==item['identity']
        os.chmod(item['path'],0,follow_symlinks=False)
        denied=socket_details();assert denied['mode']==0 and denied['connection']=={'connected':False,'errno':13},'control_socket_not_denied'
        emit({'event':'fault-active','before':observed,'socket':{k:item[k] for k in ('path','identity','uid','gid','mode')},'denied':denied['connection']})
        ready,_,_=select.select([sys.stdin],[],[],70);assert ready,'fault_release_timeout'
        action=sys.stdin.readline().strip()
        if action=='kill-helper':os.kill(os.getpid(),signal.SIGKILL)
        assert action=='resume','invalid_fault_action'
    finally:
        restored=json.loads(command(['/usr/bin/python3','-I','-c',RESTORE,json.dumps(item),'normal']))
        emit(restored)
        command(['systemctl','stop',unit+'.timer'])
else:raise RuntimeError('unknown_fault_mode')
