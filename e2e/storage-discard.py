# @spec docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#qualification-réelle
# @verifies docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#qualification-réelle
"""Installed DEV agent, real Docker/FUSE writes, lost replies and physical faults."""
import copy
from contextlib import closing,contextmanager
import json
import os
from pathlib import Path
import pwd
import signal
import sqlite3
import subprocess
import time
from uuid import uuid4

ROOT=Path('/srv/p2enjoy-serverless');REPORT=ROOT/'storage/discard-proof.json'
REPORT.write_text('{"completed":false,"cleanup":false,"skipped":0}\n')
assert os.getuid()==0 and Path('/etc/hostname').read_text().strip()=='infra-serverless'
ACCOUNT=pwd.getpwnam('spark-docker');UNIT='p2enjoy-storage-dev.service'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
INSTALLATION=str(uuid4());FUNCTIONS=[];LEASES={};CONTAINERS={};GUARDS=[];CHECKS=[];OBSERVATIONS={}
CREATED_CONTAINERS=[]
BASE={'data':{'enabled':True,'quota_mib':2},'cache':{'enabled':True,'quota_mib':2}}
OFF={'data':{'enabled':False,'quota_mib':64},'cache':{'enabled':False,'quota_mib':64}}
completed=False;cleanup_errors=[];failure=None;initial=None


def run(args,**kwargs):
    return subprocess.run(args,check=True,text=True,capture_output=True,timeout=400,**kwargs).stdout.strip()


def call(operation,denied=None,**fields):
    process=subprocess.run(DOCKER+['exec','-i','serverless-api','python','-B','-m','app.storage_client'],
        input=json.dumps({'op':operation,**fields})+'\n',text=True,capture_output=True,timeout=70)
    answer=json.loads(process.stdout)
    if denied:
        assert not answer['ok'] and answer['error'] in (denied if isinstance(denied,tuple) else (denied,)),answer
        return answer
    assert process.returncode==0 and answer['ok'],answer
    return answer['result']


def wait_for(fn,predicate,seconds=45):
    deadline=time.monotonic()+seconds;value=None
    while time.monotonic()<deadline:
        value=fn()
        if predicate(value):return value
        time.sleep(.04)
    raise AssertionError(('condition non atteinte',value))


def ready():
    def read():
        try:return call('health')
        except (AssertionError,ValueError):return {}
    return wait_for(read,lambda v:v.get('ready'))


def status(identifier):return call('status',function_id=identifier)


def function(config=BASE):
    identifier=str(uuid4());FUNCTIONS.append(identifier)
    call('configure',function_id=identifier,configuration=config)
    return identifier


def request(identifier,kind='clear-cache'):
    return {'function_id':identifier,'operation_id':str(uuid4()),'installation_id':INSTALLATION,
            'kind':kind,'expected_version':status(identifier)['version']}


def query(req,denied=None):
    return call('discard-operation',denied=denied,**{key:req[key] for key in ('function_id','operation_id','installation_id')})


def finish(req):return wait_for(lambda:query(req),lambda value:value['state']=='completed',180)


def acquire(identifier,config=BASE):
    consumer=str(uuid4());LEASES[consumer]=identifier
    lease=call('acquire',function_id=identifier,consumer_id=consumer,installation_id=INSTALLATION,configuration=config)
    return consumer,lease


def release(consumer):
    call('release',consumer_id=consumer,installation_id=INSTALLATION);del LEASES[consumer]


def docker_files(identifier,program,config=BASE,keep=False):
    consumer,lease=acquire(identifier,config)
    name='serverless-storage-discard-client-'+uuid4().hex;CONTAINERS[name]=consumer;CREATED_CONTAINERS.append(name)
    args=DOCKER+['run','--name',name,'--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','1']
    for target,source in lease['paths'].items():args+=['--mount',f'type=bind,src={source},dst={target}']
    try:result=run(args+[IMAGE,'python','-B','-c',program])
    finally:
        run(DOCKER+['rm','-f',name]);del CONTAINERS[name]
        if not keep:release(consumer)
    return (consumer,result) if keep else result


def passed(name):
    CHECKS.append({'name':name,'status':'passed'});print('PASS '+name,flush=True)


def register_read(sql,parameters=()):
    # Opening WAL under its owner prevents a root-owned sidecar during a restart.
    os.setegid(ACCOUNT.pw_gid);os.seteuid(ACCOUNT.pw_uid)
    try:
        with closing(sqlite3.connect('file:'+str(STATE/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
            return db.execute(sql,parameters).fetchall()
    finally:os.seteuid(0);os.setegid(0)


@contextmanager
def registry_writer():
    writer=None
    try:
        os.setegid(ACCOUNT.pw_gid);os.seteuid(ACCOUNT.pw_uid)
        try:
            writer=sqlite3.connect(STATE/'registry.sqlite3',isolation_level=None)
            writer.execute('BEGIN IMMEDIATE')
        finally:os.seteuid(0);os.setegid(0)
        yield
    finally:
        if writer is not None:
            os.setegid(ACCOUNT.pw_gid);os.seteuid(ACCOUNT.pw_uid)
            try:
                try:
                    if writer.in_transaction:writer.execute('ROLLBACK')
                finally:writer.close()
            finally:os.seteuid(0);os.setegid(0)


def journal_events(cursor):
    rows=[]
    for line in run(['journalctl','-u',UNIT,'--after-cursor='+cursor,'--output=cat','--no-pager']).splitlines():
        try:rows.append(json.loads(line))
        except ValueError:pass
    return rows


def guard_directory(path,temporary_mode):
    assert path==STATE/'mounts' or (path.parent==STATE/'backings' and path.name in FUNCTIONS)
    info=path.stat();mode=info.st_mode&0o777
    assert info.st_uid==ACCOUNT.pw_uid and mode==0o700 and not path.is_symlink()
    unit='serverless-storage-discard-restore-'+uuid4().hex
    code='from pathlib import Path;import os;p=Path('+repr(str(path))+');s=p.stat();assert (s.st_dev,s.st_ino)=='+repr((info.st_dev,info.st_ino))+';os.chmod(p,'+str(mode)+')'
    run(['systemd-run','--quiet','--unit='+unit,'--on-active=180s','/usr/bin/python3','-I','-c',code])
    entry=(path,info.st_dev,info.st_ino,mode,unit);GUARDS.append(entry)
    path.chmod(temporary_mode)
    return entry


def restore(entry):
    path,device,inode,mode,unit=entry
    assert (path.stat().st_dev,path.stat().st_ino)==(device,inode)
    path.chmod(mode)
    run(['systemctl','stop',unit+'.timer'])
    assert path.stat().st_mode&0o777==mode
    GUARDS.remove(entry)


def lost_reply(req):
    program="import socket,sys;s=socket.socket(socket.AF_UNIX);s.connect('/storage-agent/agent.sock');s.sendall(sys.stdin.buffer.read());s.shutdown(socket.SHUT_RDWR);s.close()"
    run(DOCKER+['exec','-i','serverless-api','python','-B','-c',program],input=json.dumps({'op':'start-discard',**req})+'\n')


try:
    def expired(signum,frame):raise TimeoutError('Échéance de campagne')
    signal.signal(signal.SIGALRM,expired);signal.alarm(1800)
    initial=ready();assert initial['healthy'] and initial['allocated_bytes']==0 and initial['leases']==0
    STATE=Path(run(DOCKER+['exec','serverless-api','python','-B','-c','import os;print(os.environ["SERVERLESS_STORAGE_ROOT_HOST"])']))
    assert STATE.parent==ROOT
    OBSERVATIONS['initial_trash']=sorted(p.name for p in (STATE/'trash').iterdir())
    IMAGE=run(DOCKER+['inspect','--format','{{.Image}}','serverless-api'])
    assert register_read('PRAGMA user_version')==[(4,)]
    assert register_read('PRAGMA integrity_check')==[('ok',)]
    OBSERVATIONS['initial']=initial
    identifier=function();req=request(identifier)
    for key in req:
        incomplete=dict(req);del incomplete[key]
        call('start-discard',denied='invalid_fields',**incomplete)
    for key,value,error in [('operation_id','bad','invalid_uuid'),('expected_version',True,'invalid_version'),
                            ('expected_version',-1,'invalid_version'),('kind','data','invalid_discard_kind'),
                            ('expected_version',req['expected_version']+1,'version_conflict')]:
        call('start-discard',denied=error,**{**req,key:value})
    call('start-discard',denied='invalid_fields',**req,unknown=True)
    call('start-discard',denied='archive_required',**{**req,'kind':'purge'})
    query(req,denied='operation_unknown')
    passed('Migration 004 et refus stricts avant décision')

    consumer=docker_files(identifier,"from pathlib import Path;Path('/data/keep').write_text('persistent');Path('/cache/keep').write_text('first')",keep=True)[0]
    call('start-discard',denied='volume_busy',**req)
    release(consumer)
    lost_reply(req);result=finish(req)
    assert result['version']==req['expected_version']+1 and result['error_code'] is None
    after=status(identifier);assert after['configuration']==BASE and after['volumes']['cache']['quota_bytes']==2*1024**2
    consumer=docker_files(identifier,"from pathlib import Path;assert Path('/data/keep').read_text()=='persistent';assert list(Path('/cache').iterdir())==[];Path('/cache/rebuilt').write_text('second')",keep=True)[0]
    assert call('start-discard',**req)==result
    assert query(req)==result
    # The real consumer remains leased while the old decision is replayed.
    call('check',consumer_id=consumer,installation_id=INSTALLATION)
    release(consumer)
    docker_files(identifier,"from pathlib import Path;assert Path('/cache/rebuilt').read_text()=='second';assert Path('/data/keep').read_text()=='persistent'")
    passed('Réponse perdue, reçu retrouvé et rejeu sans effacer le cache reconstruit sous bail')

    query({**req,'installation_id':str(uuid4())},denied='operation_owner')
    call('start-discard',denied='operation_owner',**{**req,'installation_id':str(uuid4())})
    call('start-discard',denied='operation_conflict',**{**req,'kind':'purge'})
    call('start-discard',denied='operation_conflict',**{**req,'expected_version':result['version']})
    other=function();other_version=status(other)['version']
    call('start-discard',denied='operation_conflict',**{**req,'function_id':other,'expected_version':other_version})
    for op in ('prepare-configuration','abort-configuration'):
        call(op,denied='operation_conflict',function_id=other,operation_id=req['operation_id'],installation_id=INSTALLATION,configuration=BASE,expected_version=other_version)
    configuration_id=str(uuid4())
    call('prepare-configuration',function_id=other,operation_id=configuration_id,installation_id=INSTALLATION,configuration=BASE,expected_version=other_version)
    call('start-discard',denied='operation_pending',**request(other))
    call('start-discard',denied='operation_conflict',**{**request(identifier),'operation_id':configuration_id})
    call('abort-configuration',function_id=other,operation_id=configuration_id,installation_id=INSTALLATION)
    call('start-discard',denied='operation_conflict',**{**request(identifier),'operation_id':configuration_id})
    passed('Propriétaire, paramètres et UUID croisés entre effacement et préparation/abandon')

    disabled=copy.deepcopy(BASE);disabled['cache']['enabled']=False
    call('configure',function_id=identifier,configuration=disabled)
    next_req=request(identifier);call('start-discard',**next_req);finish(next_req)
    assert status(identifier)['configuration']==disabled
    query(req,denied='operation_unknown');call('start-discard',denied='version_conflict',**req)
    call('configure',function_id=identifier,configuration=BASE)
    docker_files(identifier,"from pathlib import Path;assert list(Path('/cache').iterdir())==[];assert Path('/data/keep').read_text()=='persistent'")
    passed('Cache désactivé vidé, quota conservé et ancienne demande refusée après remplacement du reçu')

    empty=function(OFF);empty_req=request(empty);done=call('start-discard',**empty_req)
    assert done['state']=='completed' and done['version']==empty_req['expected_version']+1
    assert not status(empty)['volumes'] and call('start-discard',**empty_req)==done
    passed('Cache absent acquitté sans allocation ni montage')

    fault_req=request(identifier);entry=guard_directory(STATE/'backings'/identifier,0o500)
    call('start-discard',**fault_req)
    pending=wait_for(lambda:query(fault_req),lambda value:value['error_code']=='storage_io_error')
    assert pending['state']=='pending' and pending['phase']=='stopping'
    assert status(identifier)['volumes']['cache']['quota_bytes']==2*1024**2
    assert query(next_req)['state']=='completed'
    assert call('start-discard',**fault_req)['operation_id']==fault_req['operation_id']
    call('acquire',denied='operation_pending',function_id=identifier,consumer_id=str(uuid4()),installation_id=INSTALLATION,configuration=BASE)
    call('start-discard',denied='operation_pending',**request(identifier))
    second_req=request(other);call('start-discard',**second_req);finish(second_req)
    assert query(fault_req)['state']=='pending'
    OBSERVATIONS['permission_failure']=pending
    passed('Erreur physique conservée, même reçu et autre effacement traité sans famine')
    pid_before=run(['systemctl','show','--property=MainPID','--value',UNIT])
    cursor=run(['journalctl','-u',UNIT,'-n','0','--show-cursor','--no-pager']).split('-- cursor: ')[1].strip()
    with registry_writer():
        events=wait_for(lambda:journal_events(cursor),lambda rows:any(
            isinstance(row,dict) and row.get('event')=='storage_discard_worker_failed' and
            row.get('function_id')==identifier and row.get('error_code')=='registry_unavailable' for row in rows))
        OBSERVATIONS['sqlite_worker_failure']=[row for row in events if isinstance(row,dict) and row.get('function_id')==identifier]
        assert query(fault_req)['state']=='pending'
    restore(entry);finish(fault_req)
    assert run(['systemctl','show','--property=MainPID','--value',UNIT])==pid_before
    passed('Reprise du worker après contention SQLite réelle sans redémarrage')
    fault_req=request(identifier);entry=guard_directory(STATE/'backings'/identifier,0o500)
    call('start-discard',**fault_req)
    wait_for(lambda:query(fault_req),lambda value:value['error_code']=='storage_io_error')
    run(['systemctl','restart',UNIT]);ready()
    assert query(fault_req)['state']=='pending'
    restore(entry);finish(fault_req)
    docker_files(identifier,"from pathlib import Path;assert Path('/data/keep').read_text()=='persistent';assert list(Path('/cache').iterdir())==[]")
    passed('Intention conservée après restart et reprise après restauration des permissions')

    large=copy.deepcopy(BASE);large['cache']['quota_mib']=768
    call('configure',function_id=identifier,configuration=large)
    docker_files(identifier,"from pathlib import Path;root=Path('/cache');\nfor i in range(300):\n d=root/str(i);d.mkdir()\n for j in range(500):(d/str(j)).touch()",config=large)
    consumer,lease=acquire(other)
    large_req=request(identifier);call('start-discard',**large_req)
    wait_for(lambda:query(large_req),lambda value:value['phase']=='erasing')
    entry=guard_directory(STATE/'backings'/identifier,0o500)
    t=time.monotonic();call('check',consumer_id=consumer,installation_id=INSTALLATION);elapsed=time.monotonic()-t
    observed=query(large_req);assert observed['phase']=='erasing',observed
    assert elapsed<3,elapsed
    release(consumer)
    assert query(large_req)['phase']=='erasing'
    consumer,lease=acquire(other)
    assert query(large_req)['phase']=='erasing'
    call('check',consumer_id=consumer,installation_id=INSTALLATION);release(consumer)
    pending=wait_for(lambda:query(large_req),lambda value:value['phase']=='finalizing' and value['error_code']=='storage_io_error',180)
    OBSERVATIONS['unrelated_check_during_erasure_seconds']=elapsed
    OBSERVATIONS['finalizing_before_kill']=pending
    passed('Suppression de 150 000 fichiers hors verrou et baux d’une autre fonction disponibles')
    run(['systemctl','kill','--kill-whom=main','--signal=SIGKILL',UNIT]);ready()
    pending=wait_for(lambda:query(large_req),lambda value:value['phase']=='finalizing' and value['error_code']=='storage_io_error')
    assert pending['operation_id']==large_req['operation_id']
    restore(entry);finish(large_req)
    docker_files(identifier,"from pathlib import Path;assert list(Path('/cache').iterdir())==[];assert Path('/data/keep').read_text()=='persistent';Path('/cache/after-recovery').write_text('kept')",config=large)
    assert call('start-discard',**large_req)['state']=='completed'
    docker_files(identifier,"from pathlib import Path;assert Path('/cache/after-recovery').read_text()=='kept'",config=large)
    passed('SIGKILL en finalizing, reçu durable et cache recréé préservé après reprise')

    before_budget=call('health')['allocated_bytes'];allocation=sum(v['quota_bytes'] for v in status(identifier)['volumes'].values())
    call('archive',function_id=identifier)
    call('start-discard',denied='function_archived',**request(identifier))
    assert not call('health')['mounted_or_reserved'] and not call('health')['leases']
    entry=guard_directory(STATE/'mounts',0o300)
    purge_req=request(identifier,'purge');call('start-discard',**purge_req)
    pending=wait_for(lambda:query(purge_req),lambda value:value['phase']=='finalizing' and value['error_code']=='storage_io_error')
    assert not (STATE/'mounts'/identifier).exists()
    assert call('health')['allocated_bytes']==before_budget
    time.sleep(5)
    assert query(purge_req)['state']=='pending'
    restore(entry);purged=finish(purge_req)
    passed('Synchronisation du parent exigée même après retrait du répertoire de montage')
    assert status(identifier)['state']=='purged' and not status(identifier)['volumes']
    assert call('health')['allocated_bytes']==before_budget-allocation
    assert not (STATE/'backings'/identifier).exists() and not (STATE/'mounts'/identifier).exists()
    assert call('start-discard',**purge_req)==purged
    repeat=request(identifier,'purge');repeated=call('start-discard',**repeat)
    assert repeated['state']=='completed' and repeated['version']==repeat['expected_version']+1
    query(purge_req,denied='operation_unknown');call('start-discard',denied='version_conflict',**purge_req)
    run(['systemctl','restart',UNIT]);ready();assert query(repeat)==repeated
    passed('Purge, libération exacte, tombstone et reçu persisté après restart')
    completed=True
except BaseException as error:
    failure={'type':type(error).__name__,'message':str(error)}
    raise
finally:
    signal.alarm(0)
    for entry in list(GUARDS):
        try:restore(entry)
        except BaseException as error:cleanup_errors.append('permission: '+str(error))
    try:run(['systemctl','start',UNIT]);ready()
    except BaseException as error:cleanup_errors.append('agent: '+str(error))
    for name,consumer in list(CONTAINERS.items()):
        try:run(DOCKER+['rm','-f',name]);del CONTAINERS[name]
        except BaseException as error:cleanup_errors.append('container: '+str(error))
    for consumer in list(LEASES):
        if consumer in CONTAINERS.values():continue
        try:release(consumer)
        except BaseException as error:cleanup_errors.append('lease: '+str(error))
    for identifier in FUNCTIONS:
        try:
            snapshot=wait_for(lambda:status(identifier),lambda v:not v['pending'],180)
            if snapshot['state']=='active':call('archive',function_id=identifier)
            if snapshot['state']!='purged':
                req=request(identifier,'purge');call('start-discard',**req);finish(req)
            assert not status(identifier)['volumes']
            assert not (STATE/'backings'/identifier).exists() and not (STATE/'mounts'/identifier).exists()
        except BaseException as error:cleanup_errors.append('function '+identifier+': '+str(error))
    final=None
    try:
        final=wait_for(lambda:call('health'),lambda v:v['healthy'])
        assert initial and final['installation_id']==initial['installation_id']
        assert final['allocated_bytes']==initial['allocated_bytes'] and not final['leases'] and not final['mounted_or_reserved']
        assert register_read('PRAGMA integrity_check')==[('ok',)]
        assert sorted(p.name for p in (STATE/'trash').iterdir())==OBSERVATIONS['initial_trash']
        live=set(run(DOCKER+['ps','-a','--format','{{.Names}}']).splitlines())
        assert not live.intersection(CREATED_CONTAINERS)
        mounts=Path('/proc/self/mountinfo').read_text()
        assert not any('/'+identifier+'/' in mounts for identifier in FUNCTIONS)
    except BaseException as error:cleanup_errors.append('final: '+str(error))
    REPORT.write_text(json.dumps({'completed':completed,'cleanup':not cleanup_errors,'passed':len(CHECKS),
        'failed':int(not completed),'skipped':0,'checks':CHECKS,'functions':FUNCTIONS,'observations':OBSERVATIONS,
        'failure':failure,'cleanup_errors':cleanup_errors,'final':final},indent=2)+'\n')
    print(json.dumps({'completed':completed,'passed':len(CHECKS),'cleanup':not cleanup_errors,'cleanup_errors':cleanup_errors}),flush=True)
    if cleanup_errors:raise AssertionError('Nettoyage incomplet')
