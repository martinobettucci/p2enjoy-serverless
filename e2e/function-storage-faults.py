# @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle
# @verifies docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle
"""DEV-only real process gates and filesystem consumers for the HTTPS campaign."""
from contextlib import closing,suppress
import json
import hashlib
import os
import re
from pathlib import Path
import select
import shlex
import signal
import sqlite3
import subprocess
import sys
import time
from uuid import UUID,uuid4

assert os.getuid()==0 and Path('/etc/hostname').read_text().strip()=='infra-serverless'
ROOT=Path('/srv/p2enjoy-serverless');UNIT='p2enjoy-storage-dev.service'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    words=shlex.split(line,comments=True)
    if len(words)==1 and '=' in words[0]:
        name,value=words[0].split('=',1)
        if name in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_STORAGE_ROOT_HOST'):settings[name]=value
CONTROL=Path(settings['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3'
REGISTRY=Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])/'registry.sqlite3'
assert CONTROL.parent.parent==ROOT and REGISTRY.parent.parent==ROOT
mode=sys.argv[1];identifier=str(UUID(sys.argv[2])) if len(sys.argv)>2 else None


def emit(value):print(json.dumps(value),flush=True)


def failure(kind,error,traceback):
    reason=str(error)
    emit({'event':'fault-failed','type':kind.__name__,'reason':reason if re.fullmatch(r'[a-z_]{1,80}',reason) else 'operator_failure'})


sys.excepthook=failure


def command(args,**kwargs):
    result=subprocess.run(args,text=True,capture_output=True,timeout=80,**kwargs)
    if result.returncode:raise RuntimeError('operator_command_failed')
    return result.stdout.strip()


def rows(path,sql,parameters=()):
    with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True,timeout=2)) as db:
        db.row_factory=sqlite3.Row
        return [dict(row) for row in db.execute(sql,parameters)]


def storage(operation,**fields):
    result=json.loads(command(DOCKER+['exec','-i','serverless-api','python','-B','-m','app.storage_client'],
        input=json.dumps({'op':operation,**fields})+'\n'))
    assert result['ok'],'storage_operation_failed'
    return result['result']


def owned_function():
    result=rows(CONTROL,'SELECT f.*,n.id AS namespace_id,n.name AS namespace_name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=?',(identifier,))
    assert len(result)==1,'campaign_function_required'
    if mode=='archive-cleanup':
        assert result[0]['namespace_id']==str(UUID(sys.argv[3])),'campaign_namespace_required'
        assert re.fullmatch(r'(qa|ui|deploy|cli|publication-recovery)-[0-9a-f]{8}x*',result[0]['namespace_name']),'campaign_namespace_required'
    else:assert result[0]['namespace_name'].startswith('storage-api-'),'campaign_function_required'
    return result[0]


def input_command(timeout=110):
    ready,_,_=select.select([sys.stdin],[],[],timeout)
    if not ready:raise TimeoutError('operator_command_timeout')
    value=sys.stdin.readline().strip()
    if value not in ('resume','kill-control','release','kill-helper'):raise RuntimeError('operator_command_invalid')
    return value


def retained_files():
    result={}
    for kind in ('data','cache'):
        path=REGISTRY.parent/'backings'/identifier/kind/'keep'
        if path.is_file():
            with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            result[kind]={'bytes':path.stat().st_size,'sha256':digest}
    return result


def consumer_labels(record):
    return {'tech.p2enjoy.serverless.kind':'volume-api-proof','tech.p2enjoy.serverless.function':record['function_id'],
            'tech.p2enjoy.serverless.consumer':record['consumer_id'],'tech.p2enjoy.serverless.installation':record['installation_id']}


def clean_consumer(path):
    record=json.loads(path.read_text())
    assert record['function_id']==identifier and str(UUID(record['consumer_id']))==record['consumer_id']
    assert str(UUID(record['installation_id']))==record['installation_id']
    assert path.name=='volume-api-client-'+record['consumer_id']+'.json'
    name='serverless-volume-api-client-'+UUID(record['consumer_id']).hex
    found=command(DOCKER+['ps','-aq','--filter','name=^/'+name+'$'])
    if found:
        labels=json.loads(command(DOCKER+['inspect','--format','{{json .Config.Labels}}',name]))
        assert all(labels.get(key)==value for key,value in consumer_labels(record).items()),'foreign_container'
        command(DOCKER+['rm','-f',name])
    assert not command(DOCKER+['ps','-aq','--filter','name=^/'+name+'$']),'container_removal_unconfirmed'
    storage('release',consumer_id=record['consumer_id'],installation_id=record['installation_id'])
    path.unlink()


def recovery_guard(pid,delay=110):
    unit='serverless-resume-storage-'+uuid4().hex
    birth=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
    program='''import json,os,signal,sys
from pathlib import Path
try:
 p=int(sys.argv[1]);fd=os.pidfd_open(p)
 try:
  state=Path('/proc',str(p),'stat').read_text().rsplit(')',1)[1].split()
  if state[19]==sys.argv[2]:
   signal.pidfd_send_signal(fd,signal.SIGCONT)
   print(json.dumps({'event':'storage-guard-resumed','function_id':sys.argv[3],'pid':p,'birth':state[19],'was_stopped':state[0] in ('T','t')}),flush=True)
 finally:os.close(fd)
except (ProcessLookupError,FileNotFoundError):pass
'''
    command(['systemd-run','--quiet','--collect','--on-active='+str(delay)+'s','--unit',unit,
        '--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0',
        '--property=Type=oneshot','/usr/bin/python3','-I','-c',program,str(pid),birth,identifier])
    emit({'event':'recovery-guard','unit':unit});return unit


if mode=='health':emit(storage('health'));raise SystemExit(0)
owned_function()
if mode=='empty-resolution-busy':
    with closing(sqlite3.connect(CONTROL,timeout=2,isolation_level=None)) as writer:
        writer.execute('BEGIN IMMEDIATE')
        try:
            program='''import asyncio,json
from uuid import uuid4
from app.main import operations
from fastapi import HTTPException
async def prove():
 identifier=str(uuid4())
 try:
  async with operations.responsibility(identifier):pass
 except HTTPException as error:
  print(json.dumps({'resolved':False,'status':error.status_code,'mutation_committed':error.headers.get('X-Serverless-Mutation-Committed'),'writer_lock_held':True}));return
 assert not operations.live and not operations.cleanup_error
 assert operations.database.one('SELECT 1 FROM function_operations WHERE id=?',(identifier,)) is None
 print(json.dumps({'resolved':True,'writer_lock_held':True}))
asyncio.run(prove())
'''
            emit(json.loads(command(DOCKER+['exec','-i','serverless-api','python','-B','-'],input=program)))
        finally:writer.rollback()
elif mode=='audit-failure':
    request_id=str(UUID(sys.argv[3]))
    logs=subprocess.run(DOCKER+['logs','--tail','300','serverless-api'],text=True,capture_output=True,timeout=20)
    assert logs.returncode==0
    matched=[]
    for line in (logs.stdout+'\n'+logs.stderr).splitlines():
        if line.startswith('{'):
            value=json.loads(line)
            if value.get('event')=='audit.unavailable' and value.get('request_id')==request_id:matched.append(value)
    emit({'request_id':request_id,'audit_unavailable':len(matched)})
elif mode=='guard-evidence':
    unit=sys.argv[3]
    assert re.fullmatch(r'serverless-resume-storage-[0-9a-f]{32}',unit),'invalid_guard_unit'
    evidence=[]
    for line in command(['journalctl','--no-pager','-o','cat','-u',unit+'.service']).splitlines():
        if line.startswith('{'):
            value=json.loads(line)
            if value.get('event')=='storage-guard-resumed' and value.get('function_id')==identifier:evidence.append(value)
    emit({'unit':unit,'events':evidence})
elif mode=='inspect':
    snapshot=storage('status',function_id=identifier)
    receipt=rows(REGISTRY,'SELECT operation_id,decision,expected_version,version,configuration_json FROM configuration_receipts WHERE function_id=?',(identifier,))
    operation=rows(CONTROL,'SELECT id,kind,decision,storage_version,error_code FROM function_operations WHERE function_id=?',(identifier,))
    emit({'storage':snapshot,'receipt':receipt[0] if receipt else None,'operation':operation[0] if operation else None,'retained_files':retained_files()})
elif mode=='cleanup-clients':
    cleaned=[]
    for record_path in (ROOT/'control').glob('volume-api-client-*.json'):
        if json.loads(record_path.read_text()).get('function_id')==identifier:
            clean_consumer(record_path);cleaned.append(record_path.name)
    emit({'cleaned':cleaned})
elif mode in ('purge','archive-cleanup'):
    assert owned_function()['deleted_at'] is not None,'delete_through_api_first'
    before=storage('status',function_id=identifier)
    assert before['state'] in ('archived','purged') and not before['leases'] and not before['pending']
    files=retained_files();after=storage('purge',function_id=identifier)
    assert after['state']=='purged' and not after['volumes']
    emit({'archived_before_purge':before,'files_before_purge':files,'purged':True})
elif mode in ('write','read','hold-lease'):
    before=storage('status',function_id=identifier);consumer=str(uuid4());installation=str(uuid4())
    name='serverless-volume-api-client-'+UUID(consumer).hex
    record={'function_id':identifier,'consumer_id':consumer,'installation_id':installation}
    record_path=ROOT/'control'/('volume-api-client-'+consumer+'.json')
    fd=os.open(record_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(record,stream);stream.flush();os.fsync(stream.fileno())
    emit({'event':'consumer',**record})
    try:
        lease=storage('acquire',function_id=identifier,consumer_id=consumer,installation_id=installation,configuration=before['configuration'])
        image=command(DOCKER+['inspect','--format','{{.Image}}','serverless-api'])
        args=DOCKER+['create','--name',name,'--network','none','--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','.25']
        for key,value in consumer_labels(record).items():args+=['--label',key+'='+value]
        for target,source in lease['paths'].items():args+=['--mount',f'type=bind,src={source},dst={target}']
        program="from pathlib import Path;import json,hashlib;print(json.dumps({'bytes':Path('/data/keep').stat().st_size,'sha256':hashlib.sha256(Path('/data/keep').read_bytes()).hexdigest(),'cache':Path('/cache/keep').read_text()}))"
        if mode=='write':program="from pathlib import Path;Path('/data/keep').write_bytes(b'K'*(1280*1024));Path('/cache/keep').write_text('cached');print('written')"
        if mode=='hold-lease':program='import time;time.sleep(120)'
        command(args+[image,'python','-B','-c',program])
        if mode=='hold-lease':
            command(DOCKER+['start',name]);emit({'event':'leased','consumer_id':consumer})
            assert input_command()=='release'
        else:
            output=command(DOCKER+['start','-a',name])
            state=json.loads(command(DOCKER+['inspect','--format','{{json .State}}',name]))
            assert state['ExitCode']==0
            emit({'result':output})
    finally:
        clean_consumer(record_path)
elif mode in ('prepare','commit','commit-database-busy','watchdog'):
    pidfd=None;paused=False;writer=None;registry_writer=None;guard=None
    def interrupted(signum,frame):raise InterruptedError('operator_interrupted')
    for signum in (signal.SIGHUP,signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
    try:
        pid=int(command(['systemctl','show','--property=MainPID','--value',UNIT]));pidfd=os.pidfd_open(pid)
        guard=recovery_guard(pid,5 if mode=='watchdog' else 110)
        if mode in ('commit','commit-database-busy'):
            registry_writer=sqlite3.connect(REGISTRY,timeout=2,isolation_level=None)
            registry_writer.execute('BEGIN IMMEDIATE')
        emit({'event':'watching'});deadline=time.monotonic()+25;operation=None
        if mode=='watchdog':
            signal.pidfd_send_signal(pidfd,signal.SIGSTOP);paused=True;emit({'event':'paused','phase':'watchdog'})
            action=input_command()
            if action=='kill-helper':os.kill(os.getpid(),signal.SIGKILL)
            assert action=='resume'
            raise SystemExit(0)
        while time.monotonic()<deadline:
            if registry_writer:
                pending=rows(CONTROL,'SELECT id FROM function_operations WHERE function_id=? AND storage_version IS NOT NULL AND decision=\'undecided\'',(identifier,))
                if pending:
                    operation=pending[0]['id'];break
                time.sleep(.001);continue
            pending=rows(REGISTRY,'SELECT pending_json FROM functions WHERE id=?',(identifier,))
            if pending and pending[0]['pending_json']:
                value=json.loads(pending[0]['pending_json'])
                if value.get('operation')=='configuration-prepared' and value['phase']=='preparing':
                    operation=value['operation_id'];break
            time.sleep(.001)
        assert operation,'preparation_intention_not_observed'
        emit({'event':'preparation-observed','operation_id':operation})
        if mode=='prepare':
            signal.pidfd_send_signal(pidfd,signal.SIGSTOP);paused=True
            assert json.loads(rows(REGISTRY,'SELECT pending_json FROM functions WHERE id=?',(identifier,))[0]['pending_json'])['phase']=='preparing'
        else:
            writer=sqlite3.connect(CONTROL,timeout=2,isolation_level=None);writer.execute('BEGIN IMMEDIATE')
            registry_writer.rollback();registry_writer.close();registry_writer=None
            deadline=time.monotonic()+3
            while True:
                raw=rows(REGISTRY,'SELECT pending_json FROM functions WHERE id=?',(identifier,))[0]['pending_json']
                phase=json.loads(raw)['phase'] if raw else None
                if phase=='prepared':break
                assert time.monotonic()<deadline,'prepared_not_observed'
                time.sleep(.001)
            signal.pidfd_send_signal(pidfd,signal.SIGSTOP);paused=True
            writer.rollback();writer.close();writer=None
            deadline=time.monotonic()+5
            while True:
                pending=rows(CONTROL,'SELECT decision FROM function_operations WHERE id=?',(operation,))
                if pending and pending[0]['decision']=='commit':break
                assert time.monotonic()<deadline,'commit_not_observed'
                time.sleep(.001)
            if mode=='commit-database-busy':
                writer=sqlite3.connect(CONTROL,timeout=2,isolation_level=None);writer.execute('BEGIN IMMEDIATE')
        emit({'event':'paused','phase':mode,'operation_id':operation})
        action=input_command()
        if action=='kill-control':
            row=rows(CONTROL,'SELECT decision FROM function_operations WHERE id=?',(operation,))
            assert row and row[0]['decision']==('undecided' if mode=='prepare' else 'commit')
            command(DOCKER+['kill','--signal','KILL','serverless-api'])
            state=json.loads(command(DOCKER+['inspect','--format','{{json .State}}','serverless-api']))
            assert state['Status']=='exited' and state['ExitCode']==137,'control_crash_unconfirmed'
        else:assert action=='resume'
        signal.pidfd_send_signal(pidfd,signal.SIGCONT);paused=False
        emit({'event':'resumed','control_killed':action=='kill-control'})
    finally:
        try:
            try:
                if registry_writer:registry_writer.rollback();registry_writer.close()
            finally:
                if writer:writer.rollback();writer.close()
        finally:
            if pidfd is not None:
                try:
                    if paused:
                        with suppress(ProcessLookupError):signal.pidfd_send_signal(pidfd,signal.SIGCONT)
                finally:os.close(pidfd)
            if guard:command(['systemctl','stop',guard+'.timer'])
else:raise RuntimeError('operator_mode_invalid')
