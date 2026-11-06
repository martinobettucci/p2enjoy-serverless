# @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#configuration-de-stockage-en-deux-phases
# @verifies docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#configuration-de-stockage-en-deux-phases
"""Real prepared quota decisions, physical Docker writes and interrupted DEV agent."""
import copy
from contextlib import closing,suppress
import json
import os
from pathlib import Path
import pwd
import signal
import sqlite3
import subprocess
import time
from uuid import uuid4

ROOT=Path('/srv/p2enjoy-serverless');REPORT=ROOT/'storage/preparations-proof.json'
REPORT.write_text('{"completed":false,"cleanup":false,"skipped":0}\n')
assert os.getuid()==0 and Path('/etc/hostname').read_text().strip()=='infra-serverless'
ACCOUNT=pwd.getpwnam('spark-docker');UNIT='p2enjoy-storage-dev.service'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
INSTALLATION=str(uuid4());FUNCTIONS=[];OPERATIONS=[];LEASES={};CONTAINERS={};CHECKS=[]
BASE={'data':{'enabled':True,'quota_mib':2},'cache':{'enabled':True,'quota_mib':2}}
OFF={'data':{'enabled':False,'quota_mib':64},'cache':{'enabled':False,'quota_mib':64}}
completed=False;cleanup_errors=[];children=[];agent_pidfd=None;unexpected_file=None


class RPCFailure(AssertionError):
    def __init__(self,answer):super().__init__(answer);self.code=answer.get('error')


def run(args,**kwargs):return subprocess.run(args,check=True,text=True,capture_output=True,timeout=90,**kwargs).stdout.strip()


def command():return DOCKER+['exec','-i','serverless-api','python','-B','-m','app.storage_client']


def call(operation,denied=None,**fields):
    process=subprocess.run(command(),input=json.dumps({'op':operation,**fields})+'\n',text=True,capture_output=True,timeout=70)
    answer=json.loads(process.stdout)
    if denied:
        assert not answer['ok'] and answer['error'] in (denied if isinstance(denied,tuple) else (denied,)),answer
        return answer
    if process.returncode!=0 or not answer['ok']:raise RPCFailure(answer)
    return answer['result']


def ready():
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        result=subprocess.run(command(),input='{"op":"health"}\n',text=True,capture_output=True,timeout=15)
        try:answer=json.loads(result.stdout)
        except ValueError:answer={}
        if answer.get('ok') and answer['result']['ready']:return answer['result']
        time.sleep(.1)
    raise AssertionError('Agent non rétabli')


def status(identifier):return call('status',function_id=identifier)


def function(config=BASE):
    identifier=str(uuid4());FUNCTIONS.append(identifier)
    call('configure',function_id=identifier,configuration=config)
    return identifier


def prepare(identifier,config,expected=None):
    operation=str(uuid4());OPERATIONS.append((identifier,operation))
    if expected is None:expected=status(identifier)['version']
    return operation,call('prepare-configuration',function_id=identifier,operation_id=operation,
                          installation_id=INSTALLATION,configuration=config,expected_version=expected)


def decision(identifier,operation,choice,denied=None):
    return call(choice+'-configuration',denied=denied,function_id=identifier,operation_id=operation,installation_id=INSTALLATION)


def query(identifier,operation,denied=None,installation=INSTALLATION):
    return call('configuration-operation',denied=denied,function_id=identifier,operation_id=operation,installation_id=installation)


def docker_files(identifier,config,program):
    consumer=str(uuid4());LEASES[consumer]=identifier
    lease=call('acquire',function_id=identifier,consumer_id=consumer,installation_id=INSTALLATION,configuration=config)
    name='serverless-storage-transaction-client-'+uuid4().hex;CONTAINERS[name]=(consumer,identifier)
    args=DOCKER+['run','--name',name,'--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','.25']
    for target,source in lease['paths'].items():args+=['--mount',f'type=bind,src={source},dst={target}']
    try:return run(args+[IMAGE,'python','-B','-c',program])
    finally:
        run(DOCKER+['rm','-f',name]);del CONTAINERS[name]
        call('release',consumer_id=consumer,installation_id=INSTALLATION);del LEASES[consumer]


def purge(identifier):
    try:snapshot=status(identifier)
    except RPCFailure as error:
        if error.code=='function_unknown':return
        raise
    if snapshot['state']=='purged':return
    call('archive',function_id=identifier);call('purge',function_id=identifier)


def passed(name):CHECKS.append({'name':name,'status':'passed'});print('PASS '+name,flush=True)


def registry(identifier):
    with closing(sqlite3.connect('file:'+str(STATE/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
        return db.execute('SELECT pending_json FROM functions WHERE id=?',(identifier,)).fetchone()


try:
    def expired(signum,frame):raise TimeoutError('Échéance de campagne')
    signal.signal(signal.SIGALRM,expired);signal.alarm(360)
    initial=ready();assert initial['healthy'] and initial['allocated_bytes']==0 and initial['leases']==0
    state=run(DOCKER+['exec','serverless-api','python','-B','-c','import os;print(os.environ["SERVERLESS_STORAGE_ROOT_HOST"])'])
    STATE=Path(state);assert STATE.parent==ROOT
    IMAGE=run(DOCKER+['inspect','--format','{{.Image}}','serverless-api'])
    identifier=str(uuid4());FUNCTIONS.append(identifier)
    operation,prepared=prepare(identifier,BASE,0)
    before=status(identifier);assert prepared['state']=='prepared' and before['configuration']==OFF and before['version']==0
    assert before['pending'] and all(row['quota_bytes']==0 and row['phase']=='unmounted' for row in before['volumes'].values())
    assert call('health')['allocated_bytes']==4*1024**2
    repeated=call('prepare-configuration',function_id=identifier,operation_id=operation,installation_id=INSTALLATION,configuration=BASE,expected_version=0)
    assert repeated==prepared
    refused_consumer=str(uuid4());LEASES[refused_consumer]=identifier
    call('acquire',denied='operation_pending',function_id=identifier,consumer_id=refused_consumer,installation_id=INSTALLATION,configuration=BASE)
    for kind in ('configure','archive','clear-cache'):
        call(kind,denied='operation_pending',function_id=identifier,**({'configuration':BASE} if kind=='configure' else {}))
    query(identifier,operation,denied='operation_owner',installation=str(uuid4()))
    for choice in ('commit','abort'):
        call(choice+'-configuration',denied='operation_owner',function_id=identifier,operation_id=operation,installation_id=str(uuid4()))
    assert query(identifier,operation)['state']=='prepared'
    changed=copy.deepcopy(BASE);changed['data']['quota_mib']=3
    call('prepare-configuration',denied='operation_conflict',function_id=identifier,operation_id=operation,installation_id=INSTALLATION,configuration=changed,expected_version=0)
    refused_function=str(uuid4());FUNCTIONS.append(refused_function);OPERATIONS.append((refused_function,operation))
    call('prepare-configuration',denied='operation_conflict',function_id=refused_function,operation_id=operation,installation_id=INSTALLATION,configuration=BASE,expected_version=0)
    call('prepare-configuration',denied='invalid_fields',function_id=identifier,operation_id=str(uuid4()),installation_id=INSTALLATION,configuration=BASE)
    passed('Préparation réelle, configuration non publiée, réservation et refus de concurrence/propriétaire')
    committed=decision(identifier,operation,'commit');assert committed['state']=='committed' and committed['version']==1
    assert decision(identifier,operation,'commit')==committed
    decision(identifier,operation,'abort',denied='operation_decided')
    assert status(identifier)['configuration']==BASE and call('health')['allocated_bytes']==4*1024**2
    docker_files(identifier,BASE,"from pathlib import Path;Path('/data/keep').write_text('persistent');Path('/cache/keep').write_text('cached')")
    passed('Commit idempotent, décision opposée refusée et écritures Docker sur les volumes publiés')

    held=str(uuid4());LEASES[held]=identifier
    call('acquire',function_id=identifier,consumer_id=held,installation_id=INSTALLATION,configuration=BASE)
    rejected_operation=str(uuid4());OPERATIONS.append((identifier,rejected_operation))
    call('prepare-configuration',denied='volume_busy',function_id=identifier,operation_id=rejected_operation,
         installation_id=INSTALLATION,configuration=changed,expected_version=status(identifier)['version'])
    call('release',consumer_id=held,installation_id=INSTALLATION);del LEASES[held]
    assert not status(identifier)['pending'] and status(identifier)['configuration']==BASE
    passed('Préparation sous bail actif refusée sans mutation ni réservation supplémentaire')

    small={kind:{'enabled':True,'quota_mib':1} for kind in ('data','cache')}
    operation,_=prepare(identifier,small)
    filler_config={'data':{'enabled':True,'quota_mib':initial['budget_bytes']//1024**2-4},'cache':OFF['cache']}
    filler=function(filler_config);assert call('health')['allocated_bytes']==initial['budget_bytes']
    rejected=str(uuid4());FUNCTIONS.append(rejected)
    call('configure',denied='storage_budget',function_id=rejected,configuration={'data':{'enabled':True,'quota_mib':1},'cache':OFF['cache']})
    aborted=decision(identifier,operation,'abort');assert aborted['state']=='aborted' and status(identifier)['configuration']==BASE
    assert call('health')['allocated_bytes']==initial['budget_bytes']
    assert docker_files(identifier,BASE,"from pathlib import Path;print(Path('/data/keep').read_text())")=='persistent'
    purge(filler)
    operation,_=prepare(identifier,small);filler=function(filler_config)
    decision(identifier,operation,'commit')
    call('configure',function_id=rejected,configuration={'data':{'enabled':True,'quota_mib':2},'cache':OFF['cache']})
    assert call('health')['allocated_bytes']==initial['budget_bytes']
    purge(filler);purge(rejected)
    passed('Baisse de quota : ancien budget réservé jusqu’à abort/commit, même sous saturation globale')

    empty=str(uuid4());FUNCTIONS.append(empty);operation,_=prepare(empty,BASE,0)
    result=decision(empty,operation,'abort')
    assert result['state']=='aborted' and status(empty)['volumes']=={} and status(empty)['version']==1
    assert not (STATE/'backings'/empty).exists() and not (STATE/'mounts'/empty).exists()
    assert decision(empty,operation,'abort')==result
    decision(empty,operation,'commit',denied='operation_decided')
    newer,_=prepare(empty,BASE,1);decision(empty,newer,'commit')
    call('prepare-configuration',denied='version_conflict',function_id=empty,operation_id=operation,installation_id=INSTALLATION,configuration=BASE,expected_version=0)
    purge(empty)
    passed('Abort d’une création : chemins nouveaux retirés, reçu monotone et ancien rejeu refusé')

    data_only={'data':{'enabled':True,'quota_mib':2},'cache':OFF['cache']}
    occupied=function(data_only)
    docker_files(occupied,data_only,"from pathlib import Path;Path('/data/large').write_bytes(b'A'*(1280*1024))")
    desired={'data':{'enabled':True,'quota_mib':1},'cache':{'enabled':True,'quota_mib':1}}
    version=status(occupied)['version'];allocated=call('health')['allocated_bytes']
    call('configure',denied='quota_below_usage',function_id=occupied,configuration=desired)
    assert status(occupied)['version']==version and set(status(occupied)['volumes'])=={'data'}
    operation=str(uuid4());OPERATIONS.append((occupied,operation))
    call('prepare-configuration',denied='quota_below_usage',function_id=occupied,operation_id=operation,installation_id=INSTALLATION,configuration=desired,expected_version=version)
    assert query(occupied,operation)['state']=='aborted' and set(status(occupied)['volumes'])=={'data'}
    assert status(occupied)['configuration']==data_only and call('health')['allocated_bytes']==allocated
    assert docker_files(occupied,data_only,"from pathlib import Path;print(Path('/data/large').stat().st_size)")=='1310720'
    passed('Refus sous usage : donnée antérieure conservée et nouveau cache compensé, deux chemins de configuration')

    operation,_=prepare(identifier,BASE)
    allocated=call('health')['allocated_bytes']
    run(['systemctl','restart',UNIT]);ready()
    assert query(identifier,operation)['state']=='prepared' and status(identifier)['configuration']==small
    assert call('health')['allocated_bytes']==allocated
    decision(identifier,operation,'commit')
    assert docker_files(identifier,BASE,"from pathlib import Path;print(Path('/data/keep').read_text())")=='persistent'
    passed('Restart après préparation : décision attendue, réservation conservée et commit explicite')

    partial=str(uuid4());FUNCTIONS.append(partial);operation=str(uuid4());OPERATIONS.append((partial,operation))
    pid=int(run(['systemctl','show','--property=MainPID','--value',UNIT]));agent_pidfd=os.pidfd_open(pid)
    payload={'op':'prepare-configuration','function_id':partial,'operation_id':operation,'installation_id':INSTALLATION,'configuration':BASE,'expected_version':0}
    process=subprocess.Popen(command(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    children.append(process);process.stdin.write(json.dumps(payload)+'\n');process.stdin.flush();process.stdin.close();process.stdin=None
    deadline=time.monotonic()+15
    while True:
        row=registry(partial)
        if row and row[0] and json.loads(row[0]).get('phase')=='preparing':break
        assert process.poll() is None and time.monotonic()<deadline,'Préparation intermédiaire non observée'
        time.sleep(.001)
    signal.pidfd_send_signal(agent_pidfd,signal.SIGSTOP)
    assert json.loads(registry(partial)[0])['phase']=='preparing'
    signal.pidfd_send_signal(agent_pidfd,signal.SIGKILL);os.close(agent_pidfd);agent_pidfd=None
    output,errors=process.communicate(timeout=20)
    response=json.loads(output);assert response['ok'] is False and response['error']=='storage_transport' and response['uncertain']
    ready();assert query(partial,operation)['state']=='preparing'
    decision(partial,operation,'commit',denied='preparation_incomplete')
    decision(partial,operation,'abort');assert status(partial)['volumes']=={}
    passed('SIGKILL pendant préparation observée : réponse perdue, aucun commit implicite et abort récupéré')

    dirty=str(uuid4());FUNCTIONS.append(dirty);operation,_=prepare(dirty,BASE,0)
    unexpected_file=STATE/'backings'/dirty/'data'/'unexpected';unexpected_file.write_text('preserve this actual file')
    allocated=call('health')['allocated_bytes']
    decision(dirty,operation,'abort',denied='preparation_not_empty')
    assert unexpected_file.read_text()=='preserve this actual file' and call('health')['allocated_bytes']==allocated
    assert query(dirty,operation)['state']=='aborting'
    assert not (STATE/'backings'/dirty/'cache').exists() and not (STATE/'mounts'/dirty/'cache').exists()
    run(['systemctl','restart',UNIT]);ready()
    assert query(dirty,operation)['state']=='aborting' and unexpected_file.read_text()=='preserve this actual file'
    assert call('health')['allocated_bytes']==allocated
    unexpected_file.unlink();unexpected_file=None
    result=decision(dirty,operation,'abort');assert result['state']=='aborted' and status(dirty)['volumes']=={}
    passed('Abort partiel et restart : donnée inattendue et réservation préservées, reprise après résolution')

    prior=str(uuid4());FUNCTIONS.append(prior)
    backing=STATE/'backings'/prior/'data';backing.mkdir(parents=True,mode=0o700)
    for path in (backing.parent,backing):path.chmod(0o700);os.chown(path,ACCOUNT.pw_uid,ACCOUNT.pw_gid)
    operation,_=prepare(prior,data_only,0);decision(prior,operation,'abort')
    assert backing.is_dir() and not list(backing.iterdir()) and status(prior)['volumes']=={}
    passed('Provenance physique : répertoire vide antérieur préservé pendant abort')

    unseen=str(uuid4());FUNCTIONS.append(unseen);operation=str(uuid4());OPERATIONS.append((unseen,operation))
    allocated=call('health')['allocated_bytes']
    decision(unseen,operation,'abort',denied='function_unknown')
    fields={'function_id':unseen,'operation_id':operation,'installation_id':INSTALLATION,'configuration':BASE,'expected_version':0}
    cancelled=call('abort-configuration',**fields)
    assert cancelled['state']=='aborted' and cancelled['version']==1 and status(unseen)['volumes']=={}
    assert call('health')['allocated_bytes']==allocated and not (STATE/'backings'/unseen).exists()
    assert call('prepare-configuration',**fields)==cancelled
    assert call('abort-configuration',**fields)==cancelled
    call('abort-configuration',denied='operation_conflict',**(fields|{'configuration':changed}))
    call('abort-configuration',denied='operation_owner',**(fields|{'installation_id':str(uuid4())}))
    decision(unseen,operation,'commit',denied='operation_decided')
    call('abort-configuration',denied='invalid_fields',**{key:value for key,value in fields.items() if key!='configuration'})
    passed('Abort avant envoi : reçu sans allocation, prepare retardé neutralisé et identité stricte')

    operation=str(uuid4());OPERATIONS.append((occupied,operation));version=status(occupied)['version']
    fields={'function_id':occupied,'operation_id':operation,'installation_id':INSTALLATION,'configuration':BASE,'expected_version':version}
    held=str(uuid4());LEASES[held]=occupied
    call('acquire',function_id=occupied,consumer_id=held,installation_id=INSTALLATION,configuration=data_only)
    call('abort-configuration',denied='volume_busy',**fields)
    call('release',consumer_id=held,installation_id=INSTALLATION);del LEASES[held]
    call('abort-configuration',denied='version_conflict',**(fields|{'expected_version':version+1}))
    result=call('abort-configuration',**fields)
    assert result['state']=='aborted' and status(occupied)['configuration']==data_only and status(occupied)['version']==version+1
    assert docker_files(occupied,data_only,"from pathlib import Path;print(Path('/data/large').stat().st_size)")=='1310720'
    assert call('health')['allocated_bytes']==allocated
    passed('Abandon inconnu sur fonction existante : refus sous bail/version puis conservation des données et quotas')
    completed=True
finally:
    signal.alarm(0)
    blocked=set();final=None
    if agent_pidfd is not None:
        try:
            with suppress(ProcessLookupError):signal.pidfd_send_signal(agent_pidfd,signal.SIGCONT)
        except BaseException as error:cleanup_errors.append('agent_resume:'+type(error).__name__)
        finally:os.close(agent_pidfd)
    try:run(['systemctl','start',UNIT]);ready()
    except BaseException as error:cleanup_errors.append('agent_start:'+type(error).__name__)
    for child in children:
        try:child.communicate(timeout=70)
        except BaseException as error:
            cleanup_errors.append('pending_client:'+type(error).__name__);blocked.update(FUNCTIONS)
    if unexpected_file:
        try:unexpected_file.unlink(missing_ok=True)
        except BaseException as error:cleanup_errors.append('injected_file:'+type(error).__name__)
    for name,(consumer,identifier) in CONTAINERS.items():
        try:run(DOCKER+['rm','-f',name])
        except BaseException as error:
            cleanup_errors.append('container:'+type(error).__name__);blocked.add(identifier)
    for consumer,identifier in LEASES.items():
        if identifier in blocked:continue
        try:call('release',consumer_id=consumer,installation_id=INSTALLATION)
        except BaseException as error:
            cleanup_errors.append('lease:'+type(error).__name__);blocked.add(identifier)
    for identifier in dict.fromkeys(reversed(FUNCTIONS)):
        if identifier in blocked:continue
        try:
            snapshot=status(identifier)
            if snapshot['pending']:
                pending=json.loads(registry(identifier)[0])
                assert pending.get('installation_id')==INSTALLATION and (identifier,pending.get('operation_id')) in OPERATIONS
                decision(identifier,pending['operation_id'],'abort')
        except RPCFailure as error:
            if error.code!='function_unknown':cleanup_errors.append('preparation:'+error.code);blocked.add(identifier)
        except BaseException as error:
            cleanup_errors.append('preparation:'+type(error).__name__);blocked.add(identifier)
    for identifier in FUNCTIONS:
        if identifier in blocked:continue
        try:purge(identifier)
        except BaseException as error:cleanup_errors.append('purge:'+type(error).__name__)
    try:
        deadline=time.monotonic()+10
        while True:
            final=call('health')
            if final['healthy']:break
            if time.monotonic()>deadline:cleanup_errors.append('agent_not_healthy');break
            time.sleep(.2)
        if final['allocated_bytes'] or final['leases'] or final['mounted_or_reserved'] or final['pending_functions']:cleanup_errors.append('remaining_resources')
    except BaseException as error:cleanup_errors.append('health:'+type(error).__name__)
    REPORT.write_text(json.dumps({'completed':completed and not cleanup_errors,'cleanup':not cleanup_errors,'passed':len(CHECKS),
        'failed':int(not completed or bool(cleanup_errors)),'skipped':0,'checks':CHECKS,'cleanup_errors':cleanup_errors,
        'installation_id':INSTALLATION,'functions':FUNCTIONS,'blocked_functions':sorted(blocked),'final_health':final},ensure_ascii=False,indent=2)+'\n')
    assert not cleanup_errors,cleanup_errors
print(json.dumps({'completed':True,'passed':len(CHECKS),'cleanup':True,'failed':0,'skipped':0}))
