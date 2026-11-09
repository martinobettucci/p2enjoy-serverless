# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-de-corrélation-sur-copies007
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-de-corrélation-sur-copies007
"""Actual application startup against private copies of genuine pending schema007 purges."""
from contextlib import closing,contextmanager,nullcontext
import hashlib,json,os,re,shutil,socket,sqlite3,stat,subprocess,sys,tempfile,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import control_owner

ROOT=Path('/srv/p2enjoy-serverless');assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
campaign,phase,image=sys.argv[1:4];assert str(UUID(campaign))==campaign and phase in ('volumes','artifacts')
assert image=='sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4'
proof_path=ROOT/'docs/evidence/function-version-purge-migration008-dev-2026-11-09.json'
proof=json.loads(proof_path.read_text());assert proof['completed']
matched=[v['report'] for v in proof['historical_campaigns'] if v['report']['campaign']==campaign and v['report']['source_schema']=='007' and v['report']['phase']==phase and not v['report']['guarded']]
assert len(matched)==1 and matched[0]['completed'] and matched[0]['cleanup'],'genuine_completed_historical_window_required'
folder=ROOT/'qualification-history'/('function-version-purge-'+campaign);journal=folder/'restore.json';info=journal.lstat()
assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_mode&0o777==0o600
metadata=json.loads(journal.read_text());assert metadata['restored'] and metadata['source_schema']=='007' and metadata['target_schema']=='008'
original=folder/'purge-inputs'/(phase+'-control.sqlite3');info=original.lstat()
assert stat.S_ISREG(info.st_mode) and not original.is_symlink() and info.st_uid==1001 and info.st_mode&0o777==0o600
assert str(original)==metadata['purge_input']['backup']
def archive_snapshot():
    result={}
    for suffix in ('','-wal','-shm'):
        path=Path(str(original)+suffix)
        if not path.exists():
            assert suffix and not path.is_symlink(),'archive_file_missing_or_symlink';result[suffix]=None;continue
        info=path.lstat();assert stat.S_ISREG(info.st_mode) and not path.is_symlink() and info.st_uid==1001 and not info.st_mode&0o022
        if suffix=='-wal':assert info.st_size==0,'nonempty_archived_wal_refused'
        result[suffix]={'size':info.st_size,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),'device':info.st_dev,'inode':info.st_ino,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    return result
archive_before=archive_snapshot();archive_after=None
source_sha=hashlib.sha256(original.read_bytes()).hexdigest()
reference=next(v for v in matched[0]['evidence'] if v['scenario']=='migration-result')['before']
assert source_sha==metadata['purge_input']['backup_sha256']==reference['backup_sha256']
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
report=ROOT/('control/function-version-purge-correlation008-'+phase+'.json');assert not report.exists(),'preserve_previous_report'
nonce=uuid4().hex[:8];work=Path(tempfile.mkdtemp(prefix='function-version-purge-correlation008-',dir=ROOT/'control'));os.chown(work,1001,1001)
checks=[];observations=[];containers=[];cleanup_errors=[];completed=False;live_before=None;live_after=None

def save():
    report.write_text(json.dumps({'completed':completed and not cleanup_errors,'cleanup':not containers and not work.exists() and not cleanup_errors,'cleanup_errors':cleanup_errors,'skipped':0,'image':image,'source_campaign':campaign,'phase':phase,'backup_sha256':source_sha,'archive_before':archive_before,'archive_after':archive_after,'source_proof_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),'checks':checks,'observations':observations,'unconfirmed_containers':containers,'live_before':live_before,'live_after':live_after},indent=2)+'\n')

def run(args,timeout=60,**kwargs):
    value=subprocess.run(args,capture_output=True,text=True,timeout=timeout,cwd=ROOT,**kwargs)
    assert value.returncode==0,'migration_operator_command_failed'
    return value.stdout.strip()
@contextmanager
def database(path,*,writable=False):
    # The archived backup is immutable and root-private; it has no live WAL.
    # Every working-copy connection keeps the same UID as the real application.
    archived=path==original
    with nullcontext() if archived else control_owner(path):
        suffix='?mode=ro&immutable=1' if archived else '?mode=rw' if writable else '?mode=ro'
        with closing(sqlite3.connect('file:'+str(path)+suffix,uri=True,isolation_level=None)) as db:yield db

def live_state():
    services=json.loads(run(DOCKER+['inspect','serverless-api','serverless-runtime-reference']))
    with control_owner(ROOT/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(ROOT/'state/control.sqlite3')+'?mode=ro',uri=True)) as db:
        db.execute('BEGIN')
        live_tables=tables(db)
        counts={name:db.execute(sql).fetchone()[0] for name,sql in {'active_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'active_uploads':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'operations':'SELECT count(*) FROM function_operations','reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
    assert not any(counts.values()),'live_installation_not_quiet'
    return {'services':[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status'],'environment_sha256':hashlib.sha256(json.dumps(sorted(v['Config']['Env'])).encode()).hexdigest()} for v in services],
        'counts':counts,'control_tables':live_tables,'official_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')}}
def tables(db):
    result={}
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        values=[json.dumps(list(row),sort_keys=True,default=lambda raw:raw.hex()) for row in db.execute('SELECT * FROM "'+name.replace('"','""')+'"')]
        result[name]={'rows':len(values),'sha256':hashlib.sha256(json.dumps(sorted(values)).encode()).hexdigest()}
    return result
def snapshot(path):
    with database(path) as db:
        return {'logical_sha256':hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest(),
            'schema_sha256':hashlib.sha256(json.dumps(db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name').fetchall()).encode()).hexdigest(),
            'versions':[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')],
            'function_columns':[v[1] for v in db.execute('PRAGMA table_info(functions)')],
            'revision_columns':[v[1] for v in db.execute('PRAGMA table_info(revisions)')],
            'version_registry_present':bool(db.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='function_versions'").fetchone()),
            'tables':tables(db),'integrity':[v[0] for v in db.execute('PRAGMA integrity_check')],
            'foreign_keys':[list(v) for v in db.execute('PRAGMA foreign_key_check')]}
def copy_database(label):
    directory=work/label;directory.mkdir(mode=0o700);path=directory/'control.sqlite3'
    with database(original) as src,closing(sqlite3.connect(path)) as target:src.backup(target)
    os.chown(directory,1001,1001);os.chown(path,1001,1001);path.chmod(0o600)
    return directory,path
def lookup(name):
    value=subprocess.run(DOCKER+['container','inspect',name],capture_output=True,text=True,timeout=25,cwd=ROOT)
    if value.returncode==0:
        result=json.loads(value.stdout);assert len(result)==1;return result[0]
    assert value.returncode==1 and value.stdout.strip()=='[]' and value.stderr.strip()=='Error response from daemon: No such container: '+name,'container_absence_unconfirmed'
    return None
def owned(record):
    value=lookup(record['name'])
    if value is None:return None
    assert value['Name']=='/'+record['name'] and value['Image']==image
    labels=value['Config']['Labels'];assert labels['com.docker.compose.project']=='serverless-purge-correlation008-'+nonce and labels['com.docker.compose.service']=='control' and labels['tech.p2enjoy.serverless.purge-correlation-proof']==nonce,'foreign_proof_container'
    assert [v['Source'] for v in value['Mounts'] if v['Destination']=='/state']==[record['directory']]
    assert all(v['Destination'] in ('/state','/tmp') for v in value['Mounts']) and value['HostConfig']['NetworkMode']=='none'
    if record['id'] is not None:assert value['Id']==record['id'],'proof_container_replaced'
    return value
def start(label,directory):
    name='serverless-purge-correlation008-'+label+'-'+nonce;assert lookup(name) is None,'proof_container_name_taken'
    record={'name':name,'id':None,'directory':str(directory)};containers.append(record)
    compose=work/'compose.json';compose.write_text(json.dumps({'services':{'control':{'image':image,'container_name':name,'env_file':['/etc/spark/env','/run/spark/secrets'],
        'labels':{'tech.p2enjoy.serverless.purge-correlation-proof':nonce},'network_mode':'none','init':False,'read_only':True,'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'mem_limit':'512m','cpus':1,'pids_limit':64,
        'tmpfs':['/tmp:size=16m,mode=1777,noexec,nosuid'],'volumes':[str(directory)+':/state']}}}));compose.chmod(0o644)
    run(DOCKER+['compose','-p','serverless-purge-correlation008-'+nonce,'-f',str(compose),'up','-d','--no-build'])
    created=owned(record);assert created is not None,'proof_container_creation_unknown';record['id']=created['Id']
    return exited(name,directory)

def exited(name,directory):
    record=next(v for v in containers if v['name']==name);assert owned(record) is not None
    state=None;deadline=time.monotonic()+40
    while True:
        state=json.loads(run(DOCKER+['inspect','--format','{{json .State}}',name]))
        if state['Status']=='exited':break
        assert time.monotonic()<deadline,'isolated_startup_did_not_exit';time.sleep(.1)
    logs=subprocess.run(DOCKER+['logs',name],capture_output=True,text=True,timeout=20);raw=logs.stdout+logs.stderr
    configuration=json.loads(run(DOCKER+['inspect',name]))[0]
    assert configuration['Image']==image and configuration['HostConfig']['NetworkMode']=='none' and not configuration['HostConfig']['PortBindings']
    assert all(v['Destination'] in ('/state','/tmp') for v in configuration['Mounts']) and [v['Source'] for v in configuration['Mounts'] if v['Destination']=='/state']==[str(directory)]
    assert set(configuration['HostConfig']['Tmpfs'])=={'/tmp'}
    assert not any(v['Destination'] in ('/docker.sock','/storage-agent') for v in configuration['Mounts'])
    return name,state,raw

def remove(name):
    record=next(v for v in containers if v['name']==name);current=owned(record)
    if current is not None:
        record['id']=current['Id'];run(DOCKER+['rm','-f',record['id']]);assert lookup(record['id']) is None
    containers.remove(record)

def retained_rows(db,name,columns,versions=None):
    query='SELECT '+','.join('"'+v.replace('"','""')+'"' for v in columns)+' FROM "'+name.replace('"','""')+'"'
    if name=='schema_migrations':query+=' WHERE version IN ('+','.join('?' for _ in versions)+')'
    values=[json.dumps(list(v),separators=(',',':')) for v in db.execute(query,versions if name=='schema_migrations' else ())]
    return hashlib.sha256(json.dumps(sorted(values)).encode()).hexdigest()
def verify_upgrade(path):
    with database(original) as old,database(path) as new:
        old.row_factory=new.row_factory=sqlite3.Row
        versions=[v[0] for v in new.execute('SELECT version FROM schema_migrations ORDER BY version')]
        assert len(versions)==8 and versions[-1]=='008_function_versions.sql'
        old_versions=[v[0] for v in old.execute('SELECT version FROM schema_migrations ORDER BY version')]
        assert versions[:-1]==old_versions
        preserved=[]
        for (name,) in old.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall():
            columns=[v[1] for v in old.execute('PRAGMA table_info("'+name.replace('"','""')+'")')]
            assert retained_rows(old,name,columns,old_versions)==retained_rows(new,name,columns,old_versions),'historical_columns_changed:'+name
            preserved.append(name)
        functions={v['id']:dict(v) for v in old.execute('SELECT id,active_revision_id FROM functions')};revisions=[dict(v) for v in old.execute('SELECT id,function_id,code_hash,created_at,deleted_at,stored_bytes FROM revisions')]
        groups={};histories={}
        for revision in revisions:
            histories.setdefault(revision['function_id'],[]).append(revision)
            if revision['code_hash'] is not None:groups.setdefault((revision['function_id'],revision['code_hash']),[]).append(revision)
        actual={(v['function_id'],v['code_hash']):dict(v) for v in new.execute('SELECT * FROM function_versions')};assert set(actual)==set(groups)
        for key,aliases in groups.items():
            active=functions[key[0]]['active_revision_id'];available=lambda v:v['deleted_at'] is None and v['stored_bytes']>0
            canonical=min(aliases,key=lambda v:(v['id']!=active,not available(v),v['created_at'],v['id']));first=min(v['created_at'] for v in aliases)
            assert actual[key]=={'function_id':key[0],'code_hash':key[1],'revision_id':canonical['id'],'created_at':first,'state':'available' if any(available(v) for v in aliases) else 'deleted','updated_at':first}
        for row in new.execute('SELECT id,first_published_code_hash,first_promoted_at FROM functions'):
            history=sorted(histories.get(row['id'],[]),key=lambda v:(v['created_at'],v['id']))
            assert row['first_published_code_hash']==(history[0]['code_hash'] if history else None)
            assert row['first_promoted_at']==(history[0]['created_at'] if history else None)
        revision_hashes={v['id']:v['code_hash'] for v in revisions}
        deployment_backfills=0;invocation_backfills=0
        for row in new.execute('SELECT revision_id,code_hash,code_changed,version_restored,result_function_version,default_code_hash_at_publication,restore_code_hash,code_only FROM deployments'):
            assert row['code_hash']==revision_hashes.get(row['revision_id']) and row['code_only']==0
            assert all(row[k] is None for k in ('code_changed','version_restored','result_function_version','default_code_hash_at_publication','restore_code_hash'));deployment_backfills+=1
        for row in new.execute('SELECT revision_id,requested_code_hash,resolved_code_hash FROM invocations'):
            assert row['requested_code_hash'] is None and row['resolved_code_hash']==revision_hashes.get(row['revision_id']);invocation_backfills+=1
        assert new.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not new.execute('PRAGMA foreign_key_check').fetchall()
        return {'preserved_tables':preserved,'deployment_backfills':deployment_backfills,'invocation_backfills':invocation_backfills,'groups':len(groups),'unknown_tombstones':sum(v['code_hash'] is None for v in revisions),
            'known_deleted_aliases':sum(v['code_hash'] is not None and v['deleted_at'] is not None for v in revisions),'duplicate_groups':sum(len(v)>1 for v in groups.values()),
            'unknown_first_with_later_known':sum(bool(v) and v[0]['code_hash'] is None and any(r['code_hash'] is not None for r in v[1:]) for v in [sorted(history,key=lambda r:(r['created_at'],r['id'])) for history in histories.values()]),'versions':versions}
save()
try:
    live_before=live_state();assert live_before['services'][0]['image']==image
    initial=snapshot(original);assert initial['tables']==reference['tables'] and initial['integrity']==['ok'] and initial['foreign_keys']==[]
    assert len(initial['versions'])==7 and initial['versions'][-1]=='007_function_code_hash.sql' and 'code_hash' in initial['revision_columns'] and not initial['version_registry_present']
    with database(original) as db:
        pending=db.execute("SELECT c.id,c.function_id FROM storage_commands c JOIN function_operations o ON o.id=c.id WHERE c.kind='purge' AND c.state='pending' AND c.phase=? AND o.decision='commit'",(phase,)).fetchall()
        assert len(pending)==1;operation,function=pending[0]
        code=db.execute("SELECT id,code_hash FROM revisions WHERE function_id=? AND inventory_json='[]' AND events_json='{}' AND stored_bytes>0 AND deleted_at IS NOT NULL",(function,)).fetchall()
        assert len(code)==1;revision,known_hash=code[0];assert re.fullmatch(r'[0-9a-f]{64}',known_hash)
        peers=db.execute("SELECT id FROM services WHERE name='code-purge-other-service' AND deleted_at IS NULL").fetchall();assert len(peers)==1;other_service=peers[0][0]
    observations.append({'source_verified':True,'source_schema':'007','function_id':function,'revision_id':revision,'known_hash':known_hash,'source_snapshot':initial})
    faults=[
        ('missing-purge-guard','DELETE FROM function_operations WHERE id=?',(operation,)),
        ('different-operation-id','UPDATE function_operations SET id=? WHERE id=?',(str(uuid4()),operation)),
        ('aborted-purge-guard',"UPDATE function_operations SET decision='abort' WHERE id=?",(operation,)),
        ('different-guard-function','UPDATE function_operations SET function_id=? WHERE id=?',(str(uuid4()),operation)),
        ('different-guard-service','UPDATE function_operations SET service_id=? WHERE id=?',(other_service,operation)),
        ('different-command-service','UPDATE storage_commands SET service_id=? WHERE id=?',(other_service,operation)),
        ('different-function-service','UPDATE functions SET service_id=? WHERE id=?',(other_service,function)),
        ('different-guard-kind',"UPDATE function_operations SET kind='clear-cache' WHERE id=?",(operation,)),
        ('different-command-kind',"UPDATE storage_commands SET kind='clear-cache' WHERE id=?",(operation,)),
        ('uncommitted-command',"UPDATE storage_commands SET state='preparing' WHERE id=?",(operation,)),
        ('before-purge-phase',"UPDATE storage_commands SET phase='draining' WHERE id=?",(operation,)),
        ('different-installation','UPDATE storage_commands SET installation_id=? WHERE id=?',(str(uuid4()),operation)),
        ('different-result-version','UPDATE storage_commands SET result_version=result_version+1 WHERE id=?',(operation,)),
        ('different-command-version','UPDATE storage_commands SET expected_function_version=expected_function_version+1 WHERE id=?',(operation,)),
        ('different-guard-version','UPDATE function_operations SET expected_function_version=expected_function_version+1 WHERE id=?',(operation,)),
        ('function-not-deleted','UPDATE functions SET deleted_at=NULL WHERE id=?',(function,)),
        ('function-has-active-pointer','UPDATE functions SET active_revision_id=? WHERE id=?',(revision,function)),
        ('revision-not-deleted','UPDATE revisions SET deleted_at=NULL WHERE id=?',(revision,)),
        ('events-not-cleared',"UPDATE revisions SET events_json='[]' WHERE id=?",(revision,)),
        ('inventory-not-purge-value',"UPDATE revisions SET inventory_json='[ ]' WHERE id=?",(revision,)),
    ]
    for label,statement,args in faults:
        directory,path=copy_database(label)
        try:
            with database(path,writable=True) as db:
                db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
                if label=='function-has-active-pointer':db.execute('UPDATE revisions SET deleted_at=NULL WHERE id=?',(revision,))
                assert db.execute(statement,args).rowcount==1,'fault_not_applied_once';db.commit()
            before=snapshot(path);assert before['integrity']==['ok'] and before['foreign_keys']==[] and len(before['versions'])==7 and not before['version_registry_present']
            name,state,raw=start(label,directory)
            expected='historical_active_version_required' if label=='function-has-active-pointer' else 'user-defined function raised exception'
            assert state['ExitCode']!=0 and expected in raw and 'Application startup complete.' not in raw,'expected_correlation_refusal_missing'
            assert 'in reconcile_docker' not in raw,'post_migration_failure_is_not_refusal'
            after=snapshot(path);assert before==after,'refused_migration_changed_database'
            remove(name);checks.append({'name':label,'status':'passed','transaction_rolled_back':True})
            observations.append({'scenario':label,'before':before,'after':after,'exit_code':state['ExitCode'],'expected_diagnostic':expected,'diagnostic_observed':True,'log_sha256':hashlib.sha256(raw.encode()).hexdigest()});save();print('PASS '+label,flush=True)
        except BaseException as error:
            checks.append({'name':label,'status':'failed','error':type(error).__name__});save();raise
    label='positive-same-container-retry';directory,path=copy_database(label)
    try:
        name,state,raw=start(label,directory)
        assert state['ExitCode']!=0 and 'FileNotFoundError' in raw and 'in reconcile_docker' in raw and 'Application startup complete.' not in raw
        upgraded=verify_upgrade(path);snapshot008=snapshot(path);record=next(v for v in containers if v['name']==name);identifier=record['id']
        run(DOCKER+['start',identifier]);_,retried,second_log=exited(name,directory)
        assert retried['ExitCode']!=0 and 'FileNotFoundError' in second_log and 'in reconcile_docker' in second_log and 'Application startup complete.' not in second_log
        assert snapshot(path)==snapshot008 and owned(record)['Id']==identifier,'same_container_retry_changed_migrated_data'
        remove(name);checks.append({'name':label,'status':'passed'})
        observations.append({'scenario':label,'migration':upgraded,'same_container_id':identifier,'schema008_snapshot':snapshot008,'retry_identical':True,'socket_intentionally_not_mounted':True,'application_ready':False,'first_log_sha256':hashlib.sha256(raw.encode()).hexdigest(),'retry_log_sha256':hashlib.sha256(second_log.encode()).hexdigest(),'first_exit_code':state['ExitCode'],'retry_exit_code':retried['ExitCode']});save();print('PASS '+label,flush=True)
    except BaseException as error:
        checks.append({'name':label,'status':'failed','error':type(error).__name__});save();raise
    archive_after=archive_snapshot();assert len(checks)==21 and archive_before==archive_after and hashlib.sha256(original.read_bytes()).hexdigest()==source_sha
    live_after=live_state();assert live_before==live_after,'served_installation_changed';completed=True
finally:
    for record in containers.copy():
        try:remove(record['name'])
        except BaseException as error:cleanup_errors.append({'container':record['name'],'error':type(error).__name__})
    if not containers:
        try:shutil.rmtree(work)
        except BaseException as error:cleanup_errors.append({'work':work.name,'error':type(error).__name__})
    try:
        archive_after=archive_snapshot()
        if archive_after!=archive_before or hashlib.sha256(original.read_bytes()).hexdigest()!=source_sha:cleanup_errors.append({'source_backup':'changed'})
    except BaseException as error:cleanup_errors.append({'source_backup':type(error).__name__})
    save();assert not cleanup_errors and not containers and not work.exists(),'correlation_copy_cleanup_incomplete'
