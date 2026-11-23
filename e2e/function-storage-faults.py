# @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle
# @verifies docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle | docs/ADMISSION.md#observation-durable-des-intentions-par-les-gardes
# @spec docs/BACKLOG.md#sls-146 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md#diagnostic-du-refus-de-commit-zip--sls-146
# @verifies docs/BACKLOG.md#sls-146 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md#diagnostic-du-refus-de-commit-zip--sls-146
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
from control_database import control_owner,ControlWriter,ControlObserver

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


def error_metadata(error):
    reason=str(error)
    return {'type':type(error).__name__,
            'reason':reason if re.fullmatch(r'[a-z_]{1,80}',reason) else 'operator_failure',
            'message_sha256':hashlib.sha256(reason.encode()).hexdigest()}


def process_identity(pid):
    path=Path('/proc',str(pid));state=(path/'stat').read_text().rsplit(')',1)[1].split()
    return {'pid':pid,'birth':state[19],'cgroup':(path/'cgroup').read_text()}


def failure(kind,error,traceback):
    reason=str(error)
    emit({'event':'fault-failed','type':kind.__name__,'reason':reason if re.fullmatch(r'[a-z_]{1,80}',reason) else 'operator_failure'})


sys.excepthook=failure


def command(args,**kwargs):
    result=subprocess.run(args,text=True,capture_output=True,timeout=80,**kwargs)
    if result.returncode:raise RuntimeError('operator_command_failed')
    return result.stdout.strip()


def rows(path,sql,parameters=()):
    assert path in (CONTROL,REGISTRY)
    assert (path.stat().st_uid,path.stat().st_gid)==(CONTROL.stat().st_uid,CONTROL.stat().st_gid),'database_owner_mismatch'
    with control_owner(CONTROL):
        with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True,timeout=2)) as db:
            db.row_factory=sqlite3.Row
            return [dict(row) for row in db.execute(sql,parameters)]


class RegistryWriter:
    """Keep ownership until SQLite closes, including an operator interruption."""
    def __init__(self):
        self.db=None;self.identity=None;self.interruption_pending=False

    def begin(self):
        assert self.db is None,'registry_writer_already_open'
        assert (REGISTRY.stat().st_uid,REGISTRY.stat().st_gid)==(CONTROL.stat().st_uid,CONTROL.stat().st_gid),'registry_owner_mismatch'
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGHUP,signal.SIGTERM,signal.SIGINT})
        try:
            with control_owner(CONTROL):
                self.db=sqlite3.connect('file:'+str(REGISTRY)+'?mode=rw',uri=True,timeout=2,isolation_level=None)
                self.db.execute('BEGIN IMMEDIATE')
                self.identity={'effective_uid':os.geteuid(),'effective_gid':os.getegid(),
                    'sidecar_uids':{suffix:Path(str(REGISTRY)+suffix).stat().st_uid for suffix in ('-wal','-shm')}}
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)

    def close(self,interrupt=False):
        if self.db is None:return
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGHUP,signal.SIGTERM,signal.SIGINT})
        try:
            with control_owner(CONTROL):
                # This helper-only probe injects a real OS signal while SQLite is
                # still open under its owner; it replaces no product dependency.
                if interrupt:
                    os.kill(os.getpid(),signal.SIGTERM)
                    self.interruption_pending=signal.SIGTERM in signal.sigpending()
                    assert self.interruption_pending,'operator_signal_not_queued'
                try:
                    if self.db.in_transaction:self.db.rollback()
                finally:
                    self.db.close()
                    self.db=None
            assert all((Path(str(REGISTRY)+suffix).stat().st_uid,Path(str(REGISTRY)+suffix).stat().st_gid)==
                       (CONTROL.stat().st_uid,CONTROL.stat().st_gid) for suffix in ('','-wal','-shm')),'registry_owner_changed'
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)


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
        assert re.fullmatch(r'(qa|ui|deploy|cli|publication-recovery|publication-api|publication-ui|invocation)-[0-9a-f]{8}x*',result[0]['namespace_name']),'campaign_namespace_required'
    else:
        # @verifies docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#suivi-et-réponses-perdues
        publication=(mode in ('commit','inspect') and re.fullmatch(r'publication-ui-[0-9a-f]{8}',result[0]['namespace_name']))
        if publication:
            assert result[0]['namespace_id']==str(UUID(sys.argv[3])),'campaign_namespace_required'
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
    agent_identity=process_identity(pid);birth=agent_identity['birth']
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
    emit({'event':'recovery-guard','unit':unit,'helper':process_identity(os.getpid()),
          'agent':agent_identity,'guard_seconds':delay});return unit


if mode=='health':emit(storage('health'));raise SystemExit(0)
function_owner=owned_function()
if mode=='interrupt-guard':
    target=json.loads(bytes.fromhex(sys.argv[3]));pid=int(target['pid']);fd=os.pidfd_open(pid)
    try:
        assert process_identity(pid)==target,'guard_identity_changed'
        arguments=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
        assert str(Path(__file__).resolve()).encode() in arguments and b'commit' in arguments and identifier.encode() in arguments,'owned_commit_guard_required'
        signal.pidfd_send_signal(fd,signal.SIGTERM)
        emit({'event':'guard-interrupted','signal':'SIGTERM','helper':target})
    finally:os.close(fd)
elif mode=='registry-close-interruption':
    def interrupted(signum,frame):raise InterruptedError('operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    writer=RegistryWriter();replacement=RegistryWriter();caught=False
    observer=ControlObserver(CONTROL);replacement_observer=ControlObserver(CONTROL)
    try:
        writer.begin()
        try:writer.close(interrupt=True)
        except InterruptedError:
            caught=True
            assert writer.db is None and os.geteuid()==0,'interruption_before_registry_close'
        assert caught and writer.interruption_pending,'operator_interruption_missing'
        writer.close()
        replacement.begin()
        with control_owner(CONTROL):
            assert replacement.db.in_transaction,'registry_writer_not_reacquired'
        replacement.close()
        observer.open();observer.rows('SELECT id FROM functions WHERE id=?',(identifier,));caught=False
        try:observer.close(interrupt=True)
        except InterruptedError:
            caught=True
            assert observer.db is None and os.geteuid()==0,'interruption_before_observer_close'
        assert caught and observer.interruption_pending,'observer_interruption_missing'
        replacement_observer.open()
        assert replacement_observer.rows('SELECT id FROM functions WHERE id=?',(identifier,))==[{'id':identifier}]
        replacement_observer.close()
        emit({'interruption_deferred':True,'writer_closed':writer.db is None,'writer_reacquired':True,
            'writer_identity':writer.identity,'replacement_identity':replacement.identity,'operator_uid':os.geteuid(),
            'observer_interruption_deferred':observer.interruption_pending,'observer_closed':observer.db is None,
            'observer_reopened':True,'observer_autocommit':True,'observer_identity':observer.identity,
            'replacement_observer_identity':replacement_observer.identity})
    finally:
        try:writer.close()
        finally:
            try:replacement.close()
            finally:
                try:observer.close()
                finally:replacement_observer.close()
elif mode=='empty-resolution-busy':
    with ControlWriter(CONTROL) as writer:
        emit({'event':'control-writer-identity',**writer.identity,'operator_uid':os.geteuid()})
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
            emit({**json.loads(command(DOCKER+['exec','-i','serverless-api','python','-B','-'],input=program)),
                  'writer_identity':writer.identity,'operator_uid':os.geteuid()})
        finally:writer.close()
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
    pidfd=None;paused=False;writer=None;registry_writer=None;guard=None;observer=None
    primary=None;finalization_errors=[]
    observation={'version':1,'mode':mode,'function_id':identifier,'namespace_id':function_owner['namespace_id'],
                 'phase':'starting','started_monotonic_ns':str(time.monotonic_ns()),'started_utc_ns':str(time.time_ns()),
                 'loops':{},'milestones':{},'signal_acknowledged':False}
    def phase(name):
        observation['phase']=name
        observation['milestones'][name]={'monotonic_ns':str(time.monotonic_ns()),'utc_ns':str(time.time_ns())}
    def reading(name,read):
        loop=observation['loops'].setdefault(name,{'calls':0,'returns':0})
        loop['calls']+=1;loop['entered_monotonic_ns']=str(time.monotonic_ns())
        result=read()
        loop['returns']+=1;loop['returned_monotonic_ns']=str(time.monotonic_ns())
        return result
    def cleanup(name,action):
        try:action();return True
        except BaseException as error:
            finalization_errors.append({'step':name,**error_metadata(error),'exception':error});return False
    def interrupted(signum,frame):raise InterruptedError('operator_interrupted')
    for signum in (signal.SIGHUP,signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
    try:
        pid=int(command(['systemctl','show','--property=MainPID','--value',UNIT]));pidfd=os.pidfd_open(pid)
        guard=recovery_guard(pid,5 if mode=='watchdog' else 110)
        if mode in ('commit','commit-database-busy'):
            phase('observer_open')
            observer=ControlObserver(CONTROL);observer.open()
            emit({'event':'control-observer-ready',**observer.identity,'autocommit':True,'operator_uid':os.geteuid()})
            phase('registry_writer_begin');registry_writer=RegistryWriter();registry_writer.begin()
            emit({'event':'registry-writer-identity',**registry_writer.identity,'operator_uid':os.geteuid()})
        phase('watching');emit({'event':'watching'});deadline=time.monotonic()+25;operation=None
        if mode=='watchdog':
            signal.pidfd_send_signal(pidfd,signal.SIGSTOP);paused=True;phase('stop_sent');emit({'event':'paused','phase':'watchdog'})
            action=input_command()
            if action=='kill-helper':os.kill(os.getpid(),signal.SIGKILL)
            assert action=='resume'
            raise SystemExit(0)
        phase('intention_wait');observation['loops']['intention']={'calls':0,'returns':0,'deadline_monotonic_ns':str(int(deadline*1e9))}
        while time.monotonic()<deadline:
            if registry_writer:
                pending=reading('intention',lambda:observer.rows('SELECT id FROM function_operations WHERE function_id=? AND storage_version IS NOT NULL AND decision=\'undecided\'',(identifier,)))
                observation['loops']['intention']['last_row_count']=len(pending)
                if pending:
                    operation=pending[0]['id'];break
                time.sleep(.001);continue
            pending=reading('intention',lambda:rows(REGISTRY,'SELECT pending_json FROM functions WHERE id=?',(identifier,)))
            observation['loops']['intention']['last_row_count']=len(pending)
            if pending and pending[0]['pending_json']:
                value=json.loads(pending[0]['pending_json'])
                if value.get('operation')=='configuration-prepared' and value['phase']=='preparing':
                    operation=value['operation_id'];break
            time.sleep(.001)
        assert operation,'preparation_intention_not_observed'
        observation['operation_id']=operation;phase('intention_observed');emit({'event':'preparation-observed','operation_id':operation})
        if mode=='prepare':
            signal.pidfd_send_signal(pidfd,signal.SIGSTOP);paused=True;phase('stop_sent')
            assert json.loads(rows(REGISTRY,'SELECT pending_json FROM functions WHERE id=?',(identifier,))[0]['pending_json'])['phase']=='preparing'
        else:
            phase('control_writer_begin');writer=ControlWriter(CONTROL);phase('control_writer_acquired');emit({'event':'control-writer-identity',**writer.identity,'operator_uid':os.geteuid()})
            phase('registry_writer_close');registry_writer.close();registry_writer=None;phase('registry_writer_closed')
            deadline=time.monotonic()+3
            phase('prepared_wait');observation['loops']['prepared']={'calls':0,'returns':0,'deadline_monotonic_ns':str(int(deadline*1e9))}
            while True:
                raw=reading('prepared',lambda:rows(REGISTRY,'SELECT pending_json FROM functions WHERE id=?',(identifier,)))[0]['pending_json']
                prepared_phase=json.loads(raw)['phase'] if raw else None
                observation['loops']['prepared']['last_phase']=prepared_phase
                if prepared_phase=='prepared':break
                assert time.monotonic()<deadline,'prepared_not_observed'
                time.sleep(.001)
            phase('prepared_observed');signal.pidfd_send_signal(pidfd,signal.SIGSTOP);paused=True;phase('stop_sent')
            phase('control_writer_close');writer.close();writer=None;phase('control_writer_closed')
            deadline=time.monotonic()+5
            phase('commit_wait');observation['loops']['commit']={'calls':0,'returns':0,'deadline_monotonic_ns':str(int(deadline*1e9))}
            while True:
                pending=reading('commit',lambda:observer.rows('SELECT decision FROM function_operations WHERE id=?',(operation,)))
                observation['loops']['commit']['last_row_count']=len(pending)
                observation['loops']['commit']['last_decision']=pending[0]['decision']if pending else None
                if pending and pending[0]['decision']=='commit':break
                assert time.monotonic()<deadline,'commit_not_observed'
                time.sleep(.001)
            if mode=='commit-database-busy':
                phase('busy_writer_begin')
                writer=ControlWriter(CONTROL);emit({'event':'control-writer-identity',**writer.identity,'operator_uid':os.geteuid()})
        phase('acquired')
        emit({'event':'paused','phase':mode,'operation_id':operation})
        action=input_command()
        if action=='kill-control':
            row=(observer.rows('SELECT decision FROM function_operations WHERE id=?',(operation,)) if observer else
                 rows(CONTROL,'SELECT decision FROM function_operations WHERE id=?',(operation,)))
            assert row and row[0]['decision']==('undecided' if mode=='prepare' else 'commit')
            command(DOCKER+['kill','--signal','KILL','serverless-api'])
            state=json.loads(command(DOCKER+['inspect','--format','{{json .State}}','serverless-api']))
            assert state['Status']=='exited' and state['ExitCode']==137,'control_crash_unconfirmed'
        else:assert action=='resume'
        signal.pidfd_send_signal(pidfd,signal.SIGCONT);paused=False;phase('continue_sent')
        emit({'event':'resumed','control_killed':action=='kill-control'})
    except BaseException as error:
        if isinstance(error,SystemExit)and error.code in (None,0):raise
        primary=error
        # Diagnostic I/O never replaces the real exception or delays restoration.
        try:emit({'event':'fault-primary',**error_metadata(error),'observation':observation})
        except BaseException as diagnostic_error:finalization_errors.append({'step':'primary_diagnostic',**error_metadata(diagnostic_error),'exception':diagnostic_error})
        raise
    finally:
        if registry_writer:cleanup('registry_writer_close',registry_writer.close)
        if writer:cleanup('control_writer_close',writer.close)
        if observer:cleanup('observer_close',observer.close)
        resumption={'result':'not_required'};may_disarm=True
        if pidfd is not None:
            def resume():
                try:signal.pidfd_send_signal(pidfd,signal.SIGCONT)
                except ProcessLookupError:resumption['result']='target_ended'
                else:resumption['result']='continue_sent'
            if paused:
                resumption['result']='failed';may_disarm=cleanup('agent_continue',resume)
            cleanup('pidfd_close',lambda:os.close(pidfd))
        if guard and may_disarm:cleanup('timer_stop',lambda:command(['systemctl','stop',guard+'.timer']))
        try:emit({'event':'fault-finalization','completed':not finalization_errors,
                  'errors':[{k:v for k,v in issue.items()if k!='exception'}for issue in finalization_errors],
                  'agent_resumption':resumption,'independent_guard_retained':bool(guard and not may_disarm),
                  'observation':observation,'finished_monotonic_ns':str(time.monotonic_ns()),'finished_utc_ns':str(time.time_ns())})
        except BaseException as error:finalization_errors.append({'step':'final_diagnostic',**error_metadata(error),'exception':error})
        if primary is None and finalization_errors:raise finalization_errors[0]['exception']
else:raise RuntimeError('operator_mode_invalid')
