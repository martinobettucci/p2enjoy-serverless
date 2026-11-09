# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#invariants-et-matrice-négative
"""Real application startup on private faulty copies of the genuine schema007 backup."""
from contextlib import closing,contextmanager,nullcontext
import hashlib,json,os,re,shutil,socket,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
from uuid import UUID,uuid4
from control_database import control_owner,ControlWriter

ROOT=Path('/srv/p2enjoy-serverless')
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
backup,function,selection,image=sys.argv[1:5]
assert re.fullmatch(r'function-versions-before008-[0-9]{19}',backup) and str(UUID(function))==function
assert re.fullmatch(r'sha256:[0-9a-f]{64}',image)
expected=json.load(sys.stdin);assert set(expected)=={'control_tables','source_image'} and re.fullmatch(r'sha256:[0-9a-f]{64}',expected['source_image'])
original=ROOT/'qualification-history'/backup/'control.sqlite3';assert original.is_file() and not original.is_symlink() and original.stat().st_uid==1001 and original.stat().st_mode&0o777==0o600
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
report=ROOT/'control/function-version-migration008.json';assert not report.exists(),'preserve_previous_report'
nonce=uuid4().hex[:8];work=Path(tempfile.mkdtemp(prefix='function-version-migration008-',dir=ROOT/'control'));os.chown(work,1001,1001)
checks=[];observations=[];containers=[];completed=False;cleanup_errors=[];live_before=None;live_after=None
def save():report.write_text(json.dumps({'completed':completed and not cleanup_errors,'cleanup':not cleanup_errors and not containers and not work.exists(),'cleanup_errors':cleanup_errors,'skipped':0,'selection':selection,'image':image,'backup':backup,'function_id':function,'checks':checks,'observations':observations,'unconfirmed_containers':containers,'live_before':live_before,'live_after':live_after},indent=2)+'\n')
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
        counts={name:db.execute(sql).fetchone()[0] for name,sql in {'active_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'active_uploads':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'operations':'SELECT count(*) FROM function_operations','reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
    assert not any(counts.values()),'live_installation_not_quiet'
    return {'services':[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status'],'environment_sha256':hashlib.sha256(json.dumps(sorted(v['Config']['Env'])).encode()).hexdigest()} for v in services],
        'counts':counts,'official_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')}}
def tables(db):
    result={}
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        values=[json.dumps(list(row),separators=(',',':')) for row in db.execute('SELECT * FROM "'+name.replace('"','""')+'"')]
        result[name]={'rows':len(values),'sha256':hashlib.sha256(json.dumps(sorted(values)).encode()).hexdigest()}
    return result
def snapshot(path):
    with database(path) as db:
        return {'logical_sha256':hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest(),
            'schema_sha256':hashlib.sha256(json.dumps(db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name').fetchall()).encode()).hexdigest(),
            'versions':[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')],
            'function_columns':[v[1] for v in db.execute('PRAGMA table_info(functions)')],
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
    labels=value['Config']['Labels'];assert labels['com.docker.compose.project']=='serverless-migration008-'+nonce and labels['com.docker.compose.service']=='control' and labels['tech.p2enjoy.serverless.migration-proof']==nonce,'foreign_proof_container'
    assert [v['Source'] for v in value['Mounts'] if v['Destination']=='/state']==[record['directory']]
    assert all(v['Destination'] in ('/state','/tmp') for v in value['Mounts']) and value['HostConfig']['NetworkMode']=='none'
    if record['id'] is not None:assert value['Id']==record['id'],'proof_container_replaced'
    return value
def start(label,directory,command_override=None):
    name='serverless-migration008-'+label+'-'+nonce;assert lookup(name) is None,'proof_container_name_taken'
    record={'name':name,'id':None,'directory':str(directory)};containers.append(record)
    compose=work/'compose.json';compose.write_text(json.dumps({'services':{'control':{'image':image,'container_name':name,'env_file':['/etc/spark/env','/run/spark/secrets'],
        'labels':{'tech.p2enjoy.serverless.migration-proof':nonce},'network_mode':'none','read_only':True,'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'mem_limit':'512m','cpus':1,'pids_limit':64,
        'tmpfs':['/tmp:size=16m,mode=1777,noexec,nosuid'],'volumes':[str(directory)+':/state']}}}));compose.chmod(0o644)
    if command_override is not None:
        definition=json.loads(compose.read_text());definition['services']['control']['command']=command_override;compose.write_text(json.dumps(definition))
    run(DOCKER+['compose','-p','serverless-migration008-'+nonce,'-f',str(compose),'up','-d','--no-build'])
    created=owned(record);assert created is not None,'proof_container_creation_unknown';record['id']=created['Id']
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
def positive_start(label,directory,path):
    name,state,raw=start(label,directory)
    assert state['ExitCode']!=0 and 'FileNotFoundError' in raw and 'in reconcile_docker' in raw and 'Application startup complete.' not in raw,'isolated_post_migration_failure_not_observed'
    result=verify_upgrade(path);remove(name)
    return {'migration':result,'exit_code':state['ExitCode'],'socket_intentionally_not_mounted':True,'log_sha256':hashlib.sha256(raw.encode()).hexdigest()}

def constraints_program():
    return r'''import json,sqlite3
function=FUNCTION
db=sqlite3.connect('/state/control.sqlite3',isolation_level=None);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
fn=db.execute('SELECT * FROM functions WHERE id=?',(function,)).fetchone();active=db.execute('SELECT * FROM revisions WHERE id=?',(fn['active_revision_id'],)).fetchone()
other=db.execute("SELECT * FROM function_versions WHERE function_id=? AND code_hash!=? AND state='available' LIMIT 1",(function,active['code_hash'])).fetchone();assert other
foreign=db.execute('SELECT * FROM revisions WHERE function_id!=? AND code_hash IS NOT NULL LIMIT 1',(function,)).fetchone();assert foreign
alias=db.execute('SELECT id FROM revisions WHERE function_id=? AND code_hash=? AND id!=? LIMIT 1',(function,active['code_hash'],active['id'])).fetchone();assert alias
checks=[]
def refused(label,sql,args,expected,before=None):
 db.execute('BEGIN IMMEDIATE')
 try:
  if before:db.execute(*before)
  try:db.execute(sql,args)
  except sqlite3.IntegrityError as error:assert expected in str(error),label
  else:raise AssertionError('constraint_not_enforced:'+label)
 finally:db.rollback()
 checks.append(label)
refused('revision-hash-mismatch','UPDATE function_versions SET revision_id=? WHERE function_id=? AND code_hash=?',(other['revision_id'],function,active['code_hash']),'invalid_version_revision')
refused('foreign-revision','UPDATE function_versions SET revision_id=? WHERE function_id=? AND code_hash=?',(foreign['id'],function,active['code_hash']),'invalid_version_revision')
refused('function-immutable','UPDATE function_versions SET function_id=? WHERE function_id=? AND code_hash=?',(foreign['function_id'],function,active['code_hash']),'invalid_version_revision')
refused('hash-immutable','UPDATE function_versions SET code_hash=? WHERE function_id=? AND code_hash=?',(other['code_hash'],function,active['code_hash']),'invalid_version_revision')
for state in ('archived','deleted'):refused('retained-active-'+state,'UPDATE function_versions SET state=? WHERE function_id=? AND code_hash=?',(state,function,active['code_hash']),'active_version_is_retained')
refused('archived-activation','UPDATE functions SET active_revision_id=? WHERE id=?',(other['revision_id'],function),'active_version_unavailable',("UPDATE function_versions SET state='archived' WHERE function_id=? AND code_hash=?",(function,other['code_hash'])))
for label,value in [('null',None),('other',other['code_hash'])]:refused('first-hash-'+label,'UPDATE functions SET first_published_code_hash=? WHERE id=?',(value,function),'first_published_hash_immutable')
for label,value in [('null',None),('other',fn['first_promoted_at']+1)]:refused('first-promotion-'+label,'UPDATE functions SET first_promoted_at=? WHERE id=?',(value,function),'first_promotion_immutable')
refused('invalid-version-state',"UPDATE function_versions SET state='unknown' WHERE function_id=? AND code_hash=?",(function,other['code_hash']),'CHECK constraint failed')
refused('duplicate-version','INSERT INTO function_versions SELECT * FROM function_versions WHERE function_id=? AND code_hash=?',(function,active['code_hash']),'UNIQUE constraint failed')
refused('invalid-code-only','UPDATE deployments SET code_only=2 WHERE function_id=?',(function,),'CHECK constraint failed')
db.execute('BEGIN IMMEDIATE')
try:
 db.execute('UPDATE function_versions SET revision_id=? WHERE function_id=? AND code_hash=?',(alias['id'],function,active['code_hash']))
 db.execute("UPDATE function_versions SET state='archived' WHERE function_id=? AND code_hash=?",(function,other['code_hash']))
 db.execute("UPDATE function_versions SET state='available' WHERE function_id=? AND code_hash=?",(function,other['code_hash']))
 db.execute('UPDATE deployments SET code_only=1 WHERE function_id=?',(function,))
finally:db.rollback()
db.close();print(json.dumps({'checks':checks,'positive_controls':3,'rolled_back':True}))
'''.replace('FUNCTION',repr(function))

try:
    assert not Path(str(original)+'-wal').exists() and not Path(str(original)+'-shm').exists(),'archived_backup_has_live_sidecars'
    live_before=live_state();assert all(v['health']=='healthy' for v in live_before['services'])
    source_sha=hashlib.sha256(original.read_bytes()).hexdigest()
    with database(original) as db:
        assert tables(db)==expected['control_tables'],'historical_backup_table_mismatch'
        versions=[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')];assert len(versions)==7 and versions[-1]=='007_function_code_hash.sql'
        active=db.execute('SELECT active_revision_id FROM functions WHERE id=? AND deleted_at IS NULL',(function,)).fetchone()[0];assert active
        other=db.execute('SELECT id FROM functions WHERE id!=? LIMIT 1',(function,)).fetchone()[0]
        token=db.execute('SELECT id FROM service_tokens LIMIT 1').fetchone()[0]
        inventory=json.loads(db.execute('SELECT inventory_json FROM revisions WHERE id=?',(active,)).fetchone()[0]);assert inventory
    faults={
        'deleted-function-with-target':("UPDATE functions SET deleted_at=updated_at WHERE id=?",(function,),'historical_active_version_required'),
        'foreign-active-alias':('UPDATE revisions SET function_id=? WHERE id=?',(other,active),'historical_active_version_required'),
        'active-code-without-charge':('UPDATE revisions SET stored_bytes=0 WHERE id=?',(active,),'historical_active_version_required'),
        'missing-retained-inventory':("UPDATE revisions SET inventory_json='[]' WHERE id=?",(active,),'user-defined function raised exception'),
        'changed-retained-inventory':('UPDATE revisions SET inventory_json=? WHERE id=?',(json.dumps([{**v,'sha256':('0'*64 if v['sha256']!='0'*64 else '1'*64)} if i==0 else v for i,v in enumerate(inventory)]),active),'historical_code_hash_mismatch'),
        'orphan-service-token':('UPDATE service_tokens SET service_id=? WHERE id=?',(str(uuid4()),token),'historical_foreign_key_required')}
    selected=list(faults)+['positive','writer-lock','constraints'] if selection=='rejections-and-controls' else list(faults) if selection=='all-rejections' else [selection];assert all(v in {*faults,'positive','writer-lock','constraints'} for v in selected)
    observations.append({'source_sha256':source_sha,'historical_tables_verified':True,'source_versions':versions,'source_image':expected['source_image'],'active_revision_id':active,'selected_scenarios':selected})
    for label in selected:
        directory,path=copy_database(label)
        if label in ('positive','writer-lock','constraints'):
            try:
                details={}
                if label=='writer-lock':
                    before=snapshot(path)
                    with ControlWriter(path):
                        name,state,raw=start('writer-lock-held',directory);after=snapshot(path)
                        assert state['ExitCode']!=0 and 'database is locked' in raw and before==after
                        details['held_writer']={'exit_code':state['ExitCode'],'log_sha256':hashlib.sha256(raw.encode()).hexdigest(),'database_unchanged':True};remove(name)
                details.update(positive_start(label+'-upgrade',directory,path))
                if label=='constraints':
                    before=snapshot(path);name,state,raw=start('registry-constraints',directory,['python','-B','-c',constraints_program()])
                    assert state['ExitCode']==0;result=json.loads(raw.strip().split('\n')[-1]);assert len(result['checks'])==14 and result['positive_controls']==3 and result['rolled_back']
                    assert snapshot(path)==before;remove(name);details['constraints']=result
                observations.append({'scenario':label,**details});checks.append({'name':label,'status':'passed'});print('PASS',label,flush=True);save();continue
            except BaseException as error:
                checks.append({'name':label,'status':'failed','error':type(error).__name__});raise
        statement,args,diagnostic=faults[label]
        with database(path,writable=True) as db:db.execute(statement,args)
        before=snapshot(path);name,state,raw=start(label,directory);after=snapshot(path)
        observation={'scenario':label,'before':before,'after':after,'container_id':json.loads(run(DOCKER+['inspect','--format','{{json .Id}}',name])),
            'exit_code':state['ExitCode'],'log_sha256':hashlib.sha256(raw.encode()).hexdigest(),'expected_diagnostic':diagnostic,'diagnostic_observed':diagnostic in raw,
            'exception_types':re.findall(r'^([a-zA-Z_.]+(?:Error|Exception)):',raw,re.M),'application_ready': 'Application startup complete.' in raw,
            'migration008_applied':any(v.startswith('008_') for v in after['versions'])};observations.append(observation);save()
        try:
            assert state['ExitCode']!=0 and 'Application startup complete.' not in raw
            assert not observation['migration008_applied'],'incoherent_history_was_migrated'
            assert diagnostic in raw,'expected_migration_rejection_missing'
            assert before==after,'failed_migration_changed_database'
        except BaseException as error:
            checks.append({'name':label,'status':'failed','error':type(error).__name__});raise
        remove(name);checks.append({'name':label,'status':'passed','transaction_rolled_back':True});print('PASS',label,flush=True);save()
    assert hashlib.sha256(original.read_bytes()).hexdigest()==source_sha,'historical_original_changed'
    completed=True
finally:
    for record in containers.copy():
        try:remove(record['name'])
        except BaseException as error:cleanup_errors.append({'container':record,'error':type(error).__name__})
    if not containers:
        try:shutil.rmtree(work)
        except BaseException as error:cleanup_errors.append({'work':work.name,'error':type(error).__name__})
    if 'source_sha' in globals() and hashlib.sha256(original.read_bytes()).hexdigest()!=source_sha:cleanup_errors.append({'step':'original_backup_changed'})
    if live_before is not None:
        live_after=live_state()
        if live_after!=live_before:cleanup_errors.append({'step':'live_installation_changed'})
    save()
