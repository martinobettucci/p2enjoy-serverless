# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#bascule-du-contrôle-déjà008
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#résultats-et-régression
"""Guarded code-only DEV replacement; preserves data and official configuration."""
import fcntl,hashlib,json,os,re,socket,sqlite3,signal,subprocess,sys,time,urllib.request
from contextlib import closing
from pathlib import Path
from uuid import uuid4

ROOT=Path('/srv/p2enjoy-serverless');COMPOSE=ROOT/'control/compose.spark.yml'
OLD='sha256:19cfe884642a26f3e7dc0edb80505ecd11bacc3b07bcd931e68a08439063e470'
NEW='sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
OFFICIAL=['/etc/spark/env','/run/spark/secrets','/etc/spark/routes']
OPERATOR_FOLDER=None
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','authorized_dev_spark_required'


def group_members(pgid):
    found=[]
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields=path.read_text().rsplit(')',1)[1].split()
            if int(fields[2])==pgid and fields[0] not in ('Z','X'):found.append(int(path.parent.name))
        except FileNotFoundError:pass
    return found


def confirm_mutators(folder):
    for path in folder.glob('mutator-*.json'):
        value=json.loads(path.read_text())
        if value.get('joined'):continue
        assert 'pgid' in value,'mutator_launch_issue_unknown'
        assert not group_members(value['pgid']),'previous_mutator_group_not_joined'
        value['joined']=True;value['independent_absence_confirmation']=True;write(path,value)


def cmd(args,timeout=30,*,mutation=False):
    record=None;value=None
    if mutation:
        assert OPERATOR_FOLDER is not None
        confirm_mutators(OPERATOR_FOLDER)
        record=OPERATOR_FOLDER/('mutator-'+uuid4().hex+'.json')
        value={'launch_intent':True,'joined':False};write(record,value)
    p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT,start_new_session=True)
    if record is not None:
        value.update(pgid=p.pid,pid=p.pid);write(record,value)
    expired=False
    try:stdout,_=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        expired=True
        try:os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:stdout,_=p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            stdout,_=p.communicate(timeout=10)
    deadline=time.monotonic()+10
    while group_members(p.pid):
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        assert time.monotonic()<deadline,'deployment_command_group_not_joined';time.sleep(.1)
    if record is not None:value['joined']=True;write(record,value)
    assert not expired,'deployment_command_timed_out_after_group_join'
    assert p.returncode==0,'deployment_command_failed:'+str(args[0])
    return stdout.strip()


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    pending=path.with_name(path.name+'.pending')
    with pending.open('w') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    pending.replace(path)


def lookup_control():
    p=subprocess.run(DOCKER+['container','inspect','serverless-api'],capture_output=True,text=True,timeout=30,cwd=ROOT)
    if p.returncode==0:
        rows=json.loads(p.stdout);assert len(rows)==1;return rows[0]
    assert p.returncode==1 and json.loads(p.stdout)==[] and p.stderr.strip()=='Error response from daemon: No such container: serverless-api','control_inspection_failed'
    return None


def inspect():
    current=lookup_control();assert current is not None,'control_absent'
    return [current,json.loads(cmd(DOCKER+['inspect','serverless-runtime-reference']))[0]]
def configuration(row):
    return {'mounts':sorted([{k:m.get(k) for k in ('Type','Source','Destination','RW','Propagation')} for m in row['Mounts']],key=lambda v:v['Destination']),
        'host':{k:row['HostConfig'].get(k) for k in ('NetworkMode','ReadonlyRootfs','Memory','MemorySwap','NanoCpus','PidsLimit','CapDrop','SecurityOpt','Tmpfs','Init','RestartPolicy','PortBindings')},
        'environment_sha256':hashlib.sha256(json.dumps(sorted(row['Config']['Env'])).encode()).hexdigest(),
        'command':row['Config']['Cmd'],'entrypoint':row['Config'].get('Entrypoint')}


def identity_row(row):return {'id':row['Id'],'image':row['Image'],'started_at':row['State']['StartedAt'],'health':row['State'].get('Health',{}).get('Status')}
def check_scope(identity,*,allow_absent=False):
    assert {n:sha(n) for n in OFFICIAL}==identity['official_sha256'],'official_files_changed'
    assert sha(COMPOSE)==identity['compose_sha256'],'compose_changed'
    reference=json.loads(cmd(DOCKER+['inspect','serverless-runtime-reference']))[0]
    assert identity_row(reference)==identity['reference'],'reference_changed'
    current=lookup_control()
    if current is None:
        assert allow_absent and (Path(identity['folder'])/'replacement-intent.json').exists(),'unowned_control_absence'
        return None
    labels=current['Config']['Labels'];assert labels['com.docker.compose.project']=='p2enjoy-serverless-dev' and labels['com.docker.compose.service']=='control'
    assert current['Image'] in (OLD,NEW) and configuration(current)==identity['configuration'],'control_scope_changed'
    if current['Image']==OLD:assert current['Id']==identity['old']['id'] or (Path(identity['folder'])/'rollback-intent.json').exists(),'unknown_old_container'
    return current


def up():
    cmd(DOCKER+['compose','--env-file',OFFICIAL[0],'--env-file',OFFICIAL[1],'-f',str(COMPOSE),'up','-d','--no-build','--wait','--wait-timeout','90','control'],timeout=115,mutation=True)


def healthy(row):
    assert row['State']['Running'] and row['State'].get('Health',{}).get('Status')=='healthy','control_not_healthy'
    with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=5) as response:
        assert response.status==200 and json.load(response)['status']=='ok'


def recover(folder):
    global OPERATOR_FOLDER
    OPERATOR_FOLDER=folder
    info=folder.lstat();assert folder.parent==Path('/run') and re.fullmatch(r'serverless-control-image-rollback-[a-f0-9]{32}',folder.name)
    assert not folder.is_symlink() and info.st_uid==0 and info.st_mode&0o777==0o700
    identity=json.loads((folder/'identity.json').read_text());assert identity['folder']==str(folder) and sha(folder/'operator.py')==identity['operator_sha256']
    fd=os.open(folder/'lock',os.O_RDWR|os.O_NOFOLLOW)
    try:
        deadline=time.monotonic()+125
        while True:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                assert time.monotonic()<deadline,'rollback_lock_timeout';time.sleep(.2)
        confirm_mutators(folder)
        current=check_scope(identity,allow_absent=True)
        if (folder/'success.json').exists():
            value=json.loads((folder/'success.json').read_text());assert current is not None and current['Id']==value['control']['id'] and current['Image']==NEW;healthy(current)
            return {'completed':True,'rollback_performed':False,'success_receipt_observed':True}
        if (folder/'restored.json').exists():
            value=json.loads((folder/'restored.json').read_text());assert current is not None and current['Id']==value['control']['id'] and current['Image']==OLD;healthy(current);return value
        if current is not None and current['Image']==NEW:assert (folder/'replacement-intent.json').exists(),'replacement_not_owned'
        assert cmd(DOCKER+['image','inspect','p2enjoy-control:dev','--format','{{.Id}}']) in (OLD,NEW)
        write(folder/'rollback-intent.json',{'from':identity_row(current) if current is not None else None,'to_image':OLD})
        cmd(DOCKER+['tag',OLD,'p2enjoy-control:dev'],mutation=True);up();current=check_scope(identity);assert current['Image']==OLD;healthy(current)
        value={'completed':True,'rollback_performed':True,'control':identity_row(current),'database_restored':False};write(folder/'restored.json',value);return value
    finally:os.close(fd)


def guard_states(unit):
    result={}
    for suffix in ('timer','service'):
        deadline=time.monotonic()+20
        while True:
            raw=cmd(['systemctl','show',unit+'.'+suffix,'--property=LoadState','--property=ActiveState'])
            row=dict(line.split('=',1) for line in raw.splitlines())
            if row['ActiveState']=='inactive':break
            assert time.monotonic()<deadline,'rollback_guard_still_active';time.sleep(.2)
        result[suffix]=row
    return result


if len(sys.argv)>1 and sys.argv[1]=='recover':
    print(json.dumps(recover(Path(sys.argv[2]))));raise SystemExit(0)

from control_database import read_control,control_owner
state=ROOT/'state/control.sqlite3';report=ROOT/'control/function-version-migration008-deploy.json'
assert not report.exists(),'preserve_previous_deployment_report'


def database_snapshot(path=state,*,archived=False):
    connection=closing(sqlite3.connect('file:'+str(path)+'?mode=ro&immutable=1',uri=True)) if archived else read_control(path)
    with connection as db:
        result={}
        db.execute('BEGIN')
        for (name,) in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall():
            rows=[json.dumps(list(v),separators=(',',':')) for v in db.execute('SELECT * FROM "'+name.replace('"','""')+'"')]
            result[name]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(sorted(rows)).encode()).hexdigest()}
        schema=hashlib.sha256(json.dumps([list(v) for v in db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name')]).encode()).hexdigest()
        versions=[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
        assert len(versions)==8 and versions[-1]=='008_function_versions.sql'
        assert [v[0] for v in db.execute('PRAGMA integrity_check')]==['ok'] and not db.execute('PRAGMA foreign_key_check').fetchall()
        for sql in ['SELECT count(*) FROM functions WHERE deleted_at IS NULL','SELECT count(*) FROM execution_instances','SELECT count(*) FROM function_operations',"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')","SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'SELECT coalesce(sum(reserved_bytes),0) FROM deployments']:
            assert db.execute(sql).fetchone()[0]==0,'live_installation_not_quiet'
        return {'tables':result,'schema_sha256':schema,'versions':versions,'integrity':'ok','foreign_keys':[]}

old,reference=inspect();assert old['Image']==OLD;healthy(old);assert reference['State']['Health']['Status']=='healthy'
assert cmd(DOCKER+['image','inspect','p2enjoy-control:dev','--format','{{.Id}}'])==NEW
assert cmd(DOCKER+['image','inspect','p2enjoy-control:before-migration008-guards','--format','{{.Id}}'])==OLD
before=database_snapshot();nonce=uuid4().hex;folder=Path('/run')/('serverless-control-image-rollback-'+nonce);folder.mkdir(mode=0o700)
OPERATOR_FOLDER=folder
(folder/'lock').touch(mode=0o600);(folder/'operator.py').write_bytes(Path(__file__).read_bytes())
backup=ROOT/'control'/('migration008-deployment-backup-'+nonce);backup.mkdir(mode=0o700);os.chown(backup,1001,1001)
with read_control(state) as source,control_owner(state),closing(sqlite3.connect(backup/'control.sqlite3')) as target:source.backup(target)
(backup/'control.sqlite3').chmod(0o600)
archive=ROOT/'qualification-history'/backup.name;backup.rename(archive);os.chown(archive,0,0)
assert database_snapshot(archive/'control.sqlite3',archived=True)==before,'native_backup_content_mismatch'
identity={'folder':str(folder),'old':identity_row(old),'new_image':NEW,'reference':identity_row(reference),'configuration':configuration(old),
    'official_sha256':{n:sha(n) for n in OFFICIAL},'compose_sha256':sha(COMPOSE),'operator_sha256':sha(folder/'operator.py')}
write(folder/'identity.json',identity)
result={'completed':False,'backup':str(archive),'backup_sha256':sha(archive/'control.sqlite3'),'before':before,'identity':identity,'database_restored':False}
write(report,result);armed=False
try:
    # Treat an unknown arming response as potentially armed; recovery is idempotent.
    armed=True
    cmd(['systemd-run','--quiet','--collect','--unit='+folder.name,'--on-active=180s','--timer-property=AccuracySec=100ms','--property=RuntimeMaxSec=270s','/usr/bin/python3','-I',str(folder/'operator.py'),'recover',str(folder)])
    assert cmd(['systemctl','is-active',folder.name+'.timer'])=='active'
    print(json.dumps({'event':'image-rollback-guard-armed','unit':folder.name}),flush=True)
    with (folder/'lock').open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert identity_row(check_scope(identity))==identity['old'] and database_snapshot()==before
        write(folder/'replacement-intent.json',{'old':identity['old'],'new_image':NEW})
        up();current=check_scope(identity);assert current['Image']==NEW and current['Id']!=old['Id'];healthy(current)
        after=database_snapshot();result['after']=after;assert after==before,'database_changed_during_code_only_replacement'
        result.update(completed=True,control=identity_row(current),all_tables_unchanged=True,reference_unchanged=True,official_files_unchanged=True)
        write(folder/'success.json',{'control':result['control'],'completed':True});write(report,result)
except BaseException as error:
    result['failure']=type(error).__name__+':'+str(error)
    if armed:
        try:result['recovery']=recover(folder)
        except BaseException as failure:result['recovery_error']=type(failure).__name__+':'+str(failure)
    write(report,result);raise
finally:
    if (folder/'success.json').exists() or (folder/'restored.json').exists():
        p=subprocess.run(['systemctl','stop',folder.name+'.timer'],capture_output=True,text=True,timeout=15)
        assert p.returncode in (0,5),'guard_timer_stop_failed'
        result['guard_states']=guard_states(folder.name);write(report,result)
print(json.dumps({'completed':True,'image':NEW,'control_id':result['control']['id'],'all_tables_unchanged':True,'backup':str(archive),'guard_states':result['guard_states']}))
