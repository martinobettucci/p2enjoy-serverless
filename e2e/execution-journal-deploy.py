# @spec docs/BACKLOG.md#sls-124 | docs/EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-du-focus--sls-124
# @spec docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-de-code-compatible011--sls-128
# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOG_DEPLOYMENT.md
# @verifies docs/BACKLOG.md#sls-124 | docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOG_DEPLOYMENT.md#deux-frontières-explicites
"""Supervised DEV schema011 deployment; never replace an accepted database."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlsplit
from uuid import UUID,uuid4

ROOT=Path('/srv/p2enjoy-serverless');CONTROL=ROOT/'state/control.sqlite3';COMPOSE=ROOT/'control/compose.spark.yml'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
OFFICIAL=('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')
PREFIX='serverless-apply-journal-schema-'
UPDATE_PREFIX='serverless-update-journal-code-'
UPDATE_BASELINE='sha256:1aa70214be1ba72bd75bea301fac23a3dbcdaf6547de1b3521c9547c8ac35292'
FOCUS_BASELINE='sha256:bf9b61a60ae4d9284b037cce90816754c85ad43195500fa8542f8cfcd8c73c17'
OLD='sha256:04604089a8cb61d6015be0cde1671f29265878ff4f6f081509542ebc126055fc'
RUN_FOLDER=None


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encode(value):return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()


def write(folder,name,value):
    target=folder/name;temporary=folder/(name+'.pending-'+uuid4().hex)
    with temporary.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);json.dump(value,stream,separators=(',',':'));stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(target);fd=os.open(folder,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def command(args,timeout=30):
    value=subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout,cwd=ROOT)
    return value.stdout.strip()


def process_identity(pid):
    path=Path('/proc',str(pid));fields=(path/'stat').read_text().rsplit(')',1)[1].split()
    values=dict(line.split(':',1) for line in (path/'status').read_text().splitlines() if ':' in line)
    return {'pid':pid,'birth':fields[19],'state':fields[0],'uid':int(values['Uid'].split()[0]),
        'cgroup':(path/'cgroup').read_text(),'parent':int(fields[1])}


def observed_children(parent,expected):
    result=[];queue=[parent];seen=set()
    while queue:
        pid=queue.pop()
        if pid in seen:continue
        seen.add(pid);assert len(seen)<=256,'deployment_process_bound'
        try:
            for task in Path('/proc',str(pid),'task').iterdir():
                try:queue.extend(int(value) for value in (task/'children').read_text().split())
                except FileNotFoundError:continue
            if pid!=parent:
                row=process_identity(pid);assert row['cgroup']==expected and row['uid']==1001,'docker_descendant_left_unit'
                result.append(row)
        except FileNotFoundError:continue
    return result


def docker_result(args,timeout=30):
    if RUN_FOLDER is None:return subprocess.run(DOCKER+args,capture_output=True,text=True,timeout=timeout,cwd=ROOT)
    account=pwd.getpwnam('spark-docker');expected=process_identity(os.getpid())['cgroup']
    invocation=['/usr/bin/docker','--config',str(Path(account.pw_dir)/'.docker'),'--host','unix:///run/user/1001/docker.sock',*args]
    path='docker-command-'+uuid4().hex+'.json'
    record={'intent':True,'joined':False,'argv_sha256':hashlib.sha256(encode(invocation)).hexdigest(),'timeout_seconds':timeout,'at_ns':time.time_ns()}
    write(RUN_FOLDER,path,record)
    child=subprocess.Popen(
        invocation,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT,
        user=account.pw_uid,group=account.pw_gid,extra_groups=os.getgrouplist(account.pw_name,account.pw_gid))
    try:
        native=process_identity(child.pid);assert native['uid']==account.pw_uid and native['cgroup']==expected,'docker_client_left_unit_cgroup'
        record.update(process=native);write(RUN_FOLDER,path,record)
        deadline=time.monotonic()+timeout;descendants={}
        while True:
            for row in observed_children(child.pid,expected):descendants[(row['pid'],row['birth'])]=row
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('deployment_docker_command_deadline')
            try:stdout,stderr=child.communicate(timeout=min(.1,remaining));break
            except subprocess.TimeoutExpired:continue
        record['descendants_observed']=list(descendants.values())
        assert cgroup_members(expected.split('::',1)[1].strip())==[os.getpid()],'docker_descendants_not_joined'
        record.update(joined=True,returncode=child.returncode,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),finished_at_ns=time.time_ns())
        write(RUN_FOLDER,path,record)
        return subprocess.CompletedProcess(invocation,child.returncode,stdout,stderr)
    except BaseException as error:
        record['failure_type']=type(error).__name__
        if child.poll() is None:child.kill()
        try:
            child.communicate(timeout=10)
            record['joined']=cgroup_members(expected.split('::',1)[1].strip())==[os.getpid()]
        except (OSError,AssertionError,subprocess.TimeoutExpired) as cleanup:
            record['joined']=False;record['cleanup_failure_type']=type(cleanup).__name__
        record.update(returncode=child.returncode,finished_at_ns=time.time_ns())
        write(RUN_FOLDER,path,record);raise


def docker(args,timeout=30):
    result=docker_result(args,timeout);assert result.returncode==0,'docker_command_failed'
    return result.stdout.strip()
def inspect(name):return json.loads(docker(['inspect',name]))[0]


def configuration(item):
    return {'mounts':sorted([{key:row.get(key) for key in ('Type','Source','Destination','RW','Propagation')} for row in item['Mounts']],key=lambda row:row['Destination']),
        'host':{key:item['HostConfig'].get(key) for key in ('NetworkMode','ReadonlyRootfs','Memory','MemorySwap','NanoCpus','PidsLimit','CapDrop','SecurityOpt','Tmpfs','Init','RestartPolicy','PortBindings')},
        'environment_sha256':hashlib.sha256(encode(sorted(item['Config']['Env']))).hexdigest(),
        'command':item['Config']['Cmd'],'entrypoint':item['Config'].get('Entrypoint')}


def public_container(item):
    return {'id':item['Id'],'image':item['Image'],'started_at':item['State']['StartedAt'],
        'running':item['State']['Running'],'healthy':item['State'].get('Health',{}).get('Status')=='healthy'}


def state_identity():
    result={}
    for path in (CONTROL.parent,CONTROL):
        value=path.lstat()
        assert (stat.S_ISDIR(value.st_mode) if path==CONTROL.parent else stat.S_ISREG(value.st_mode)),'unsafe_control_state_path'
        result[str(path)]={'device':value.st_dev,'inode':value.st_ino,'uid':value.st_uid,'gid':value.st_gid,'mode':stat.S_IMODE(value.st_mode)}
    return result


def healthy(item):
    assert item['State']['Running'] and item['State']['Health']['Status']=='healthy'
    with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=3) as response:
        assert response.status==200 and json.load(response)['status']=='ok'


def access_module(folder=None):
    directory=folder if folder is not None else Path(__file__).parent
    sys.path.insert(0,str(directory))
    from control_database import read_control,control_owner
    return read_control,control_owner


def snapshot(*,path=CONTROL,archived=False,columns=None):
    read_control,_=access_module(Path(__file__).parent if Path(__file__).parent.parent==Path('/run') else None)
    context=closing(sqlite3.connect('file:'+str(path)+'?mode=ro&immutable=1',uri=True)) if archived else read_control(path)
    with context as db:
        db.row_factory=sqlite3.Row
        db.execute('BEGIN');tables={}
        names=[row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
        for name in names:
            actual=[row[1] for row in db.execute('PRAGMA table_info("'+name.replace('"','""')+'")')]
            selected=columns[name] if columns is not None and name in columns else actual
            assert all(column in actual for column in selected)
            query='SELECT '+','.join('"'+column.replace('"','""')+'"' for column in selected)+' FROM "'+name.replace('"','""')+'" ORDER BY rowid'
            digest=hashlib.sha256();count=0
            for row in db.execute(query):
                raw=encode(list(row));digest.update(len(raw).to_bytes(8,'big'));digest.update(raw);count+=1
            tables[name]={'columns':actual,'selected_columns':selected,'rows':count,'sha256':digest.hexdigest()}
        versions=[row[0] for row in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
        integrity=[row[0] for row in db.execute('PRAGMA integrity_check')]
        foreign=[list(row) for row in db.execute('PRAGMA foreign_key_check')]
        counts={key:db.execute(sql).fetchone()[0] for key,sql in {
            'live_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL',
            'instances':'SELECT count(*) FROM execution_instances','operations':'SELECT count(*) FROM function_operations',
            'active_invocations':'SELECT count(*) FROM invocations WHERE completed_at IS NULL',
            'active_candidates':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
            'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
        schema_sha256=hashlib.sha256(encode([list(row) for row in db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name')])).hexdigest()
        collection=None
        if 'execution_log_state' in tables:
            collection=dict(db.execute('SELECT * FROM execution_log_state WHERE singleton=1').fetchone())
            total,size=db.execute('SELECT count(*),coalesce(sum(payload_bytes),0) FROM execution_log_events').fetchone()
            assert collection['event_count']==total and collection['payload_bytes']==size
        db.rollback()
    assert integrity==['ok'] and foreign==[]
    return {'tables':tables,'versions':versions,'integrity':integrity,'foreign_keys':foreign,'counts':counts,
        'schema_sha256':schema_sha256,'collection':collection}


def exact_schema(snapshot,versions):
    assert snapshot['versions']==versions,'migration_set_changed'
    assert not any(snapshot['counts'].values()),'installation_not_idle'


def backup(folder,name):
    read_control,control_owner=access_module(Path(__file__).parent if Path(__file__).parent.parent==Path('/run') else None)
    target=folder/name;assert not os.path.lexists(target)
    before=snapshot()
    with read_control(CONTROL) as source,control_owner(CONTROL),closing(sqlite3.connect(target)) as destination:
        source.backup(destination)
    target.chmod(0o600)
    archived=snapshot(path=target,archived=True);after=snapshot()
    assert before==archived==after,'native_backup_changed_during_copy'
    return {'path':str(target),'sha256':sha(target),'snapshot':archived}


def identity(folder):
    info=folder.lstat();assert folder.parent==Path('/run') and re.fullmatch('(?:'+PREFIX+'|'+UPDATE_PREFIX+')[0-9a-f]{32}',folder.name)
    assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
    target=folder/'identity.json';info=target.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<131072
    fd=os.open(target,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        assert os.fstat(fd)==info;item=json.loads(os.read(fd,131073))
    finally:os.close(fd)
    assert item['folder']==str(folder) and sha(folder/'operator.py')==item['operator_sha256']
    assert sha(folder/'control_database.py')==item['database_helper_sha256']
    assert item.get('mode','schema-migration') in ('schema-migration','code-update')
    assert folder.name.startswith(UPDATE_PREFIX if item.get('mode')=='code-update' else PREFIX)
    if item.get('mode')=='code-update':
        assert item['update_profile'] in ('purge-rollback','journal-focus')
        assert item['old']['image']==(FOCUS_BASELINE if item['update_profile']=='journal-focus' else UPDATE_BASELINE)
    return item


def replacement_intent(item):
    return Path(item['folder'])/('code-update-intent.json' if item.get('mode')=='code-update' else 'migration-intent.json')


def previous_start_receipt(item):
    return Path(item['folder'])/('previous-control-restarted.json' if item.get('mode')=='code-update' else 'schema010-restarted.json')


def unit_properties(unit):
    names=('Type','Restart','RemainAfterExit','KillMode','KillSignal','SendSIGKILL','RuntimeMaxUSec','TimeoutStopUSec',
        'User','Group','MainPID','ControlPID','ControlGroup','FragmentPath','ExecStart','ExecStopPost')
    raw=command(['systemctl','show',unit+'.service',*['--property='+name for name in names]])
    return dict(line.split('=',1) for line in raw.splitlines())


def duration_microseconds(value):
    if value.isdigit():return int(value)
    factors={'us':1,'ms':1000,'s':1000000,'min':60000000,'h':3600000000}
    total=0
    for part in value.split():
        match=re.fullmatch('([0-9]+)(us|ms|min|s|h)',part);assert match,'unsupported_unit_duration'
        total+=int(match[1])*factors[match[2]]
    return total


def cgroup_members(group):
    assert group.startswith('/') and '..' not in Path(group).parts
    root=Path('/sys/fs/cgroup')/group.lstrip('/');assert root.is_dir()
    return sorted({int(value) for path in root.rglob('cgroup.procs') for value in path.read_text().split()})


def attest_unit(folder,role):
    values=unit_properties(folder.name)
    for key,expected in {'Type':'exec','Restart':'no','RemainAfterExit':'no','KillMode':'control-group',
        'SendSIGKILL':'yes','User':'root','Group':'root'}.items():assert values[key]==expected,'unit_property_changed:'+key
    assert values['KillSignal'] in ('9','SIGKILL')
    assert duration_microseconds(values['RuntimeMaxUSec'])==140000000
    assert duration_microseconds(values['TimeoutStopUSec'])==200000000
    assert str(folder/'operator.py')+' apply '+str(folder)+' ;' in values['ExecStart']
    assert str(folder/'operator.py')+' finalize '+str(folder)+' ;' in values['ExecStopPost']
    current=process_identity(os.getpid())
    assert current['cgroup']=='0::'+values['ControlGroup']+'\n'
    assert int(values['MainPID'] if role=='apply' else values['ControlPID'])==os.getpid()
    assert cgroup_members(values['ControlGroup'])==[os.getpid()],'prior_unit_processes_survive'
    if role=='finalize':
        assert int(values['MainPID'])==0
        for path in folder.glob('docker-command-*.json'):
            record=json.loads(path.read_text())
            if 'process' not in record:
                # The old cgroup has been proved empty above. Preserve the
                # unknown command outcome; only forward recovery is permitted
                # after migration-intent, even when no PID receipt survived.
                continue
            try:now=process_identity(record['process']['pid'])
            except FileNotFoundError:continue
            assert now['birth']!=record['process']['birth'] or now['state'] in ('Z','X'),'old_docker_client_not_joined'
    fragment=Path(values['FragmentPath']);info=fragment.lstat()
    assert fragment==Path('/run/systemd/transient')/(folder.name+'.service') and stat.S_ISREG(info.st_mode) and info.st_uid==0
    values.update(native_process=current,fragment_sha256=sha(fragment),systemd_version=command(['systemctl','--version']).splitlines()[0])
    write(folder,'unit-'+role+'.json',values)
    return values


def scope(item,*,allow_absent=False):
    assert {name:sha(name) for name in OFFICIAL}==item['official_sha256'] and sha(COMPOSE)==item['compose_sha256']
    assert state_identity()==item['state_identity'],'control_state_inode_changed'
    reference=inspect('serverless-runtime-reference');assert public_container(reference)==item['reference']
    current=None
    for attempt in range(3):
        identifiers=docker(['ps','-aq','--no-trunc','--filter','name=^/serverless-api$'],10).split()
        assert len(identifiers)<=1,'ambiguous_api_inventory'
        if not identifiers:
            assert allow_absent and replacement_intent(item).is_file(),'unowned_api_absence'
            return None
        probe=docker_result(['inspect',identifiers[0]],10)
        if probe.returncode==0:current=json.loads(probe.stdout)[0];break
        # Only a successful inventory confirming that this exact ID disappeared
        # permits another read. An inspect error is never interpreted as absence.
        assert not docker(['ps','-aq','--no-trunc','--filter','id='+identifiers[0]],10),'container_inspection_unavailable'
    assert current is not None and current['Name']=='/serverless-api','api_identity_not_stable'
    assert current['Image'] in (item['old']['image'],item['new_image']) and configuration(current)==item['configuration'],'control_identity_diverged'
    labels=current['Config']['Labels']
    assert labels['com.docker.compose.project']=='p2enjoy-serverless-dev' and labels['com.docker.compose.service']=='control'
    if current['Image']==item['old']['image']:
        assert current['Id']==item['old']['id'],'foreign_previous_control_container'
        expected=item['old']['started_at'];receipt=previous_start_receipt(item)
        if receipt.is_file():
            owned_start=json.loads(receipt.read_text())
            assert owned_start['container_id']==item['old']['id'] and owned_start['image']==item['old']['image']
            expected=owned_start['started_at']
        assert current['State']['StartedAt']==expected,'foreign_previous_control_generation'
    else:
        assert replacement_intent(item).is_file(),'unowned_schema011_container'
        assert labels.get(item.get('ownership_label','tech.p2enjoy.serverless.schema-deployment'))==item['unit'],'foreign_schema011_container'
    return current


def select_new(item):
    assert sha(item['compose_override'])==item['compose_override_sha256']
    docker(['tag',item['new_image'],'p2enjoy-control:dev'])
    docker(['compose','--env-file',OFFICIAL[0],'--env-file',OFFICIAL[1],'-f',str(COMPOSE),'-f',item['compose_override'],
        'up','-d','--no-build','--wait','--wait-timeout','90','control'],115)


def embedded_manifest():
    code="import hashlib,json;from pathlib import Path;files={};files.update({'control/app/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/app').glob('*.py')});files.update({'control/migrations/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/migrations').glob('*.sql')});files['function_code_hash.py']=hashlib.sha256(Path('/app/function_code_hash.py').read_bytes()).hexdigest();print(json.dumps({'backend':files,'web':{str(p.relative_to('/app/web')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/web').rglob('*') if p.is_file()}}))"
    return json.loads(docker(['exec','serverless-api','python','-B','-c',code]))


def verify_new(item):
    current=scope(item);assert current['Image']==item['new_image'];healthy(current)
    before=item['initial_backup']['snapshot']
    columns={name:row['columns'] for name,row in before['tables'].items()}
    state=snapshot(columns=columns);exact_schema(state,item['new_migrations'])
    for name,row in before['tables'].items():
        if name=='schema_migrations' and item.get('mode')!='code-update':continue
        assert state['tables'][name]['rows']==row['rows'] and state['tables'][name]['sha256']==row['sha256'],'existing_table_changed:'+name
    read_control,_=access_module(Path(__file__).parent)
    with read_control(CONTROL) as db:
        collection=dict(db.execute('SELECT * FROM execution_log_state WHERE singleton=1').fetchone())
        assert str(UUID(collection['collection_id']))==collection['collection_id']
        if item.get('mode')=='code-update':
            assert state['schema_sha256']==before['schema_sha256'],'existing_schema_changed'
            assert collection==before['collection'],'existing_collection_changed'
        else:assert collection['event_count']==collection['payload_bytes']==0
    for path,expected in item['image_manifest']['web'].items():
        request=urllib.request.Request('http://127.0.0.1:18090/'+('' if path=='index.html' else path),headers={'Host':item['public_host']})
        with urllib.request.urlopen(request,timeout=3) as response:
            assert response.status==200 and hashlib.sha256(response.read(2*1024**2+1)).hexdigest()==expected,'served_web_mismatch'
            assert 'no-store' in response.headers.get('Cache-Control','')
    actual=embedded_manifest();assert actual==item['image_manifest'],'deployed_files_differ_from_image'
    return {'control':public_container(current),'snapshot':state,'collection':collection,
        'official_files_unchanged':True,'reference_unchanged':True,'existing_columns_unchanged':True}


def prepare(image,*,mode='schema-migration',profile='purge-rollback'):
    signal.signal(signal.SIGALRM,expired);signal.alarm(90)
    assert mode in ('schema-migration','code-update')
    assert profile in ('purge-rollback','journal-focus')
    baseline=(FOCUS_BASELINE if profile=='journal-focus' else UPDATE_BASELINE) if mode=='code-update' else OLD
    assert re.fullmatch('sha256:[0-9a-f]{64}',image) and image!=baseline
    manifest=json.load(sys.stdin);assert set(manifest)=={'backend','web'} and len(manifest['backend'])==42 and len(manifest['web'])==4
    assert all(re.fullmatch('[0-9a-f]{64}',value) for group in manifest.values() for value in group.values())
    backend={str(path.relative_to(ROOT)) for path in (ROOT/'control/app').glob('*.py')}|{str(path.relative_to(ROOT)) for path in (ROOT/'control/migrations').glob('*.sql')}|{'function_code_hash.py'}
    assert set(manifest['backend'])==backend
    assert all(re.fullmatch(r'(index\.html|favicon\.svg|assets/index-[a-zA-Z0-9_-]+\.(js|css))',path) for path in manifest['web'])
    for path,expected in manifest['backend'].items():assert sha(ROOT/path)==expected,'source_not_synchronized'
    current,reference=inspect('serverless-api'),inspect('serverless-runtime-reference');assert current['Image']==baseline
    assert docker(['ps','-aq','--no-trunc','--filter','name=^/serverless-api$'],10).split()==[current['Id']]
    healthy(current);assert reference['State']['Running'] and reference['State']['Health']['Status']=='healthy'
    assert docker(['image','inspect',image,'--format','{{.Id}}'])==image
    baseline_manifest=None
    if mode=='code-update':
        baseline_manifest=embedded_manifest()
        assert baseline_manifest['backend'].keys()==manifest['backend'].keys(),'code_update_backend_set_changed'
        changes=sorted(name for name,value in manifest['backend'].items() if baseline_manifest['backend'][name]!=value)
        if profile=='purge-rollback':
            assert baseline_manifest['web']==manifest['web'],'code_update_web_changed'
            assert changes==['control/app/execution_logs.py'],'code_update_unexpected_backend_changes'
        else:
            assert not changes,'focus_update_backend_changed'
            def by_type(web):
                assert len(web)==4 and 'index.html' in web and 'favicon.svg' in web
                js=[value for name,value in web.items() if name.startswith('assets/index-') and name.endswith('.js')]
                css=[value for name,value in web.items() if name.startswith('assets/index-') and name.endswith('.css')]
                assert len(js)==len(css)==1
                return {'html':web['index.html'],'favicon':web['favicon.svg'],'js':js[0],'css':css[0]}
            previous,candidate=by_type(baseline_manifest['web']),by_type(manifest['web'])
            assert all(previous[key]==candidate[key] for key in ('favicon','css')),'focus_update_style_or_identity_changed'
            assert all(previous[key]!=candidate[key] for key in ('html','js')),'focus_update_bundle_not_changed'
    nonce=uuid4().hex;folder=Path('/run')/((UPDATE_PREFIX if mode=='code-update' else PREFIX)+nonce);folder.mkdir(mode=0o700)
    write(folder,'preparation-intent.json',{'unit':folder.name,'image':image,'old':public_container(current),'at_ns':time.time_ns()})
    ownership_label='tech.p2enjoy.serverless.code-update' if mode=='code-update' else 'tech.p2enjoy.serverless.schema-deployment'
    override=ROOT/('.execution-journal-compose-'+nonce+'.json')
    with override.open('x') as stream:
        os.fchmod(stream.fileno(),0o644)
        json.dump({'services':{'control':{'image':image,'labels':{ownership_label:folder.name}}}},stream)
        stream.flush();os.fsync(stream.fileno())
    for name,source in [('operator.py',Path(__file__)),('control_database.py',Path(__file__).with_name('control_database.py'))]:
        target=folder/name;target.write_bytes(source.read_bytes());target.chmod(0o600)
    archive=ROOT/('.execution-journal-migration-backup-'+nonce)
    archive.mkdir(mode=0o700);os.chown(archive,1001,1001)
    initial=backup(archive,'control-before-stop.sqlite3')
    migrations=sorted(path.name for path in (ROOT/'control/migrations').glob('*.sql'))
    assert len(migrations)==11 and migrations[-1]=='011_execution_logs.sql'
    old_migrations=migrations if mode=='code-update' else migrations[:-1]
    exact_schema(initial['snapshot'],old_migrations)
    item={'mode':mode,'update_profile':profile if mode=='code-update' else None,'ownership_label':ownership_label,'folder':str(folder),'unit':folder.name,'old':public_container(current),'new_image':image,'reference':public_container(reference),
        'public_host':urlsplit(dict(value.split('=',1) for value in current['Config']['Env'])['SERVERLESS_PUBLIC_URL']).netloc,
        'state_identity':state_identity(),
        'configuration':configuration(current),'official_sha256':{name:sha(name) for name in OFFICIAL},'compose_sha256':sha(COMPOSE),
        'compose_override':str(override),'compose_override_sha256':sha(override),
        'operator_sha256':sha(folder/'operator.py'),'database_helper_sha256':sha(folder/'control_database.py'),
        'initial_backup':initial,'backup_folder':str(archive),'old_migrations':old_migrations,'new_migrations':migrations,'image_manifest':manifest,'baseline_manifest':baseline_manifest}
    write(folder,'identity.json',item)
    return {'completed':True,'prepared':True,'mode':mode,'update_profile':profile if mode=='code-update' else None,'unit':folder.name,'folder':str(folder),'new_image':image,'initial_backup':str(archive),'database_restored':False}


def apply(folder):
    global RUN_FOLDER
    RUN_FOLDER=folder
    item=identity(folder);phase='checking_baseline'
    try:
        attest_unit(folder,'apply')
        assert public_container(scope(item))==item['old']
        state=snapshot();exact_schema(state,item['old_migrations'])
        write(folder,'stop-intent.json',{'old':item['old'],'at_ns':time.time_ns()})
        phase='stopping_owned_control';docker(['stop','--time','10',item['old']['id']],20)
        old=scope(item);assert not old['State']['Running']
        phase='final_native_backup';final=backup(Path(item['backup_folder']),'control-final-before-update.sqlite3' if item.get('mode')=='code-update' else 'control-final-schema010.sqlite3')
        exact_schema(final['snapshot'],item['old_migrations']);write(folder,'final-backup.json',final)
        os.chown(item['backup_folder'],0,0)
        # Verify against this final stopped state, not the earlier live snapshot.
        item['initial_backup']=final
        write(folder,replacement_intent(item).name,{'new_image':item['new_image'],'final_backup_sha256':final['sha256'],'at_ns':time.time_ns()})
        phase='starting_schema011';select_new(item)
        phase='verifying_schema011';result=verify_new(item)
        write(folder,'success.json',{'completed':True,**result,'database_restored':False,'at_ns':time.time_ns()})
        print(json.dumps({'completed':True,'unit':folder.name,'control':result['control']}),flush=True)
    except BaseException as error:
        write(folder,'primary-failure.json',{'phase':phase,'type':type(error).__name__,
            'message_sha256':hashlib.sha256(str(error).encode()).hexdigest(),'at_ns':time.time_ns()});raise


def expired(signum,frame):raise TimeoutError('journal_deployment_finalization_deadline')


def finalize(folder):
    global RUN_FOLDER
    signal.signal(signal.SIGALRM,expired);signal.alarm(180)
    RUN_FOLDER=folder
    item=identity(folder);result={'unit':folder.name,'completed':False,'database_restored':False,
        'service_result':os.environ.get('SERVICE_RESULT'),'exit_code':os.environ.get('EXIT_CODE'),'exit_status':os.environ.get('EXIT_STATUS')}
    try:
        attest_unit(folder,'finalize')
        current=scope(item,allow_absent=True)
        if (folder/'success.json').is_file():
            success=json.loads((folder/'success.json').read_text());assert public_container(current)==success['control'];healthy(current)
            result.update(verification_only=True,control=public_container(current))
        elif replacement_intent(item).is_file():
            result['forward_resume']=True
            if (folder/'final-backup.json').is_file():item['initial_backup']=json.loads((folder/'final-backup.json').read_text())
            select_new(item);result.update(verify_new(item))
        elif (folder/'stop-intent.json').is_file():
            assert current is not None and current['Id']==item['old']['id'] and current['Image']==item['old']['image']
            if current['State']['Running']:docker(['stop','--time','10',item['old']['id']],20)
            stopped=scope(item);assert not stopped['State']['Running']
            state=snapshot();exact_schema(state,item['old_migrations'])
            requested=time.time_ns();docker(['start',item['old']['id']]);returned=time.time_ns()
            restarted=inspect('serverless-api')
            assert restarted['Id']==item['old']['id'] and restarted['Image']==item['old']['image']
            import datetime
            whole,fraction=restarted['State']['StartedAt'].removesuffix('Z').split('.')
            actual=int(datetime.datetime.strptime(whole,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp())*10**9+int(fraction.ljust(9,'0'))
            assert requested<=actual<=returned,'previous_control_generation_outside_start_window'
            write(folder,previous_start_receipt(item).name,{'container_id':restarted['Id'],'image':item['old']['image'],'started_at':restarted['State']['StartedAt'],
                'own_start_window_ns':[requested,returned]})
            end=time.monotonic()+35
            while True:
                try:current=scope(item);healthy(current);break
                except (OSError,AssertionError):
                    assert time.monotonic()<end;time.sleep(.2)
            result.update(restored_same_previous_control=True,control=public_container(current))
        else:
            assert public_container(current)==item['old'];healthy(current)
            result.update(verification_only=True,control=public_container(current))
        result['completed']=True;write(folder,'finalization.json',result);print(json.dumps(result),flush=True)
    except BaseException as error:
        result.update(failure_type=type(error).__name__,failure_message_sha256=hashlib.sha256(str(error).encode()).hexdigest())
        write(folder,'finalization.json',result);raise
    finally:signal.alarm(0)


if __name__=='__main__':
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','DEV_only'
    assert len(sys.argv)==3 and sys.argv[1] in ('prepare','prepare-update','prepare-ui-update','apply','finalize')
    if sys.argv[1] in ('prepare','prepare-update','prepare-ui-update'):print(json.dumps(prepare(sys.argv[2],mode='schema-migration' if sys.argv[1]=='prepare' else 'code-update',profile='journal-focus' if sys.argv[1]=='prepare-ui-update' else 'purge-rollback')),flush=True)
    elif sys.argv[1]=='apply':apply(Path(sys.argv[2]))
    else:finalize(Path(sys.argv[2]))
