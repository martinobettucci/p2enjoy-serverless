# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#déploiement-et-retour-arrière
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation
"""Native backup and before/after conservation proof on the single DEV SPARK."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import stat
import sys
from uuid import UUID,uuid4
from control_database import control_owner,read_control

ROOT=Path('/srv/p2enjoy-serverless')
assert os.getuid()==0 and Path('/etc/hostname').read_text().strip()=='infra-serverless'
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    parts=shlex.split(line,comments=True)
    if len(parts)==1 and '=' in parts[0]:
        key,value=parts[0].split('=',1)
        if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_STORAGE_ROOT_HOST'):settings[key]=value
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);storage=Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
assert state.parent==ROOT and storage.parent==ROOT
control=state/'control.sqlite3'
scope=json.load(sys.stdin);assert set(scope)=={'namespace_id','function_id','purged_function_id'}
for value in scope.values():assert str(UUID(value))==value
phase=sys.argv[1];assert phase in ('backup','verify','clean')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def tables(db,columns=None):
    names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='schema_migrations' ORDER BY name")]
    assert all(re.fullmatch('[a-z_][a-z_0-9]*',n) for n in names)
    result={}
    for name in names:
        fields=columns[name]['columns'] if columns else [r[1] for r in db.execute('PRAGMA table_info('+name+')')]
        assert all(re.fullmatch('[a-z_][a-z_0-9]*',n) for n in fields)
        rows=[list(row) for row in db.execute('SELECT '+','.join(fields)+' FROM '+name)]
        rows.sort(key=lambda row:json.dumps(row,sort_keys=True,separators=(',',':')))
        result[name]={'columns':fields,'count':len(rows),'sha256':digest(rows)}
    return result


def files(db):
    result={}
    for row in db.execute('SELECT id,inventory_json FROM revisions WHERE function_id IN (?,?)',
                          (scope['function_id'],scope['purged_function_id'])):
        folder=state/'artifacts'/row['id'];entries={}
        if folder.exists():
            assert folder.is_dir() and not folder.is_symlink()
            for path in sorted(folder.rglob('*')):
                info=path.lstat();assert stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
                if path.is_file():entries[str(path.relative_to(folder))]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'size':info.st_size,'mode':stat.S_IMODE(info.st_mode),'inode':info.st_ino,'mtime_ns':info.st_mtime_ns}
        result[row['id']]=entries
    return result


def validate_scope(db,clean=False):
    namespace=db.execute('SELECT name,deleted_at FROM namespaces WHERE id=?',(scope['namespace_id'],)).fetchone()
    assert namespace and re.fullmatch('version-registry-[0-9a-f]{8}',namespace['name'])
    for key in ('function_id','purged_function_id'):
        row=db.execute('SELECT f.deleted_at,f.active_revision_id,s.namespace_id FROM functions f JOIN services s ON s.id=f.service_id WHERE f.id=?',(scope[key],)).fetchone()
        assert row and row['namespace_id']==scope['namespace_id']
        assert (row['deleted_at'] is not None)==(key=='purged_function_id' or clean)
    assert not db.execute('SELECT 1 FROM execution_instances').fetchone()
    assert not db.execute("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')").fetchone()
    assert not db.execute("SELECT 1 FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()
    assert not db.execute('SELECT 1 FROM function_operations').fetchone()
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()


def registry():
    with control_owner(control),closing(sqlite3.connect('file:'+str(storage/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        assert not db.execute('SELECT 1 FROM leases').fetchone()
        return {name:[dict(r) for r in db.execute('SELECT * FROM '+name+' WHERE function_id IN (?,?) ORDER BY function_id',
                    (scope['function_id'],scope['purged_function_id']))] for name in ('volumes','configuration_receipts')}


if phase=='backup':
    with read_control(control) as db:
        db.execute('BEGIN');validate_scope(db)
        assert 'code_hash' not in [r[1] for r in db.execute('PRAGMA table_info(revisions)')]
        before={'scope':scope,'tables':tables(db),'artifacts':files(db),'agent':registry(),
                'migrations':[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]}
        with control_owner(control):
            folder=state/'backups'/('before-function-code-hash-'+uuid4().hex)
            folder.mkdir(mode=0o700,parents=True)
            target=folder/'control.sqlite3'
            with closing(sqlite3.connect(target)) as backup:
                db.backup(backup);assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            os.chmod(target,0o600)
            (folder/'baseline.json').write_text(json.dumps(before));os.chmod(folder/'baseline.json',0o600)
            backup_sha=hashlib.sha256(target.read_bytes()).hexdigest()
    print(json.dumps({'completed':True,'backup':folder.name,'backup_sha256':backup_sha,'backup_mode':0o600,
        'table_checksums':before['tables'],'artifacts':before['artifacts'],'agent_sha256':digest(before['agent']),
        'migrations':before['migrations']}))
elif phase=='verify':
    name=sys.argv[2];assert re.fullmatch('before-function-code-hash-[0-9a-f]{32}',name)
    folder=state/'backups'/name;assert not folder.is_symlink()
    before=json.loads((folder/'baseline.json').read_text());assert before['scope']==scope
    with read_control(control) as db:
        db.execute('BEGIN');validate_scope(db)
        assert tables(db,before['tables'])==before['tables'],'historical_columns_changed'
        assert files(db)==before['artifacts'],'historical_artifacts_changed'
        assert registry()==before['agent'],'historical_agent_configuration_changed'
        versions=[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
        assert versions==before['migrations']+['007_function_code_hash.sql']
        rows=[dict(r) for r in db.execute('SELECT id,function_id,code_hash FROM revisions WHERE function_id IN (?,?) ORDER BY id',
            (scope['function_id'],scope['purged_function_id']))]
        assert all(r['code_hash'] is None if r['function_id']==scope['purged_function_id'] else re.fullmatch('[0-9a-f]{64}',r['code_hash']) for r in rows)
    print(json.dumps({'completed':True,'historical_tables_unchanged':True,'historical_artifacts_unchanged':True,
        'agent_configuration_unchanged':True,'backup':name,'migrations':versions,'migrated_revisions':rows}))
else:
    with read_control(control) as db:
        db.execute('BEGIN');validate_scope(db,clean=True)
        rows=[dict(r) for r in db.execute('''SELECT f.id,f.deleted_at,f.active_revision_id,s.deleted_at AS service_deleted,n.deleted_at AS namespace_deleted
            FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id
            WHERE n.id=?''',(scope['namespace_id'],))]
        assert all(r['deleted_at'] and r['active_revision_id'] is None and r['service_deleted'] and r['namespace_deleted'] for r in rows)
        assert not db.execute('''SELECT 1 FROM revisions r JOIN functions f ON f.id=r.function_id JOIN services s ON s.id=f.service_id
            WHERE s.namespace_id=? AND (r.stored_bytes!=0 OR r.deleted_at IS NULL OR r.inventory_json!='[]')''',(scope['namespace_id'],)).fetchone()
        for r in rows:
            for child in ('backings','mounts'):assert not os.path.lexists(storage/child/r['id'])
    print(json.dumps({'completed':True,'deleted_functions':[r['id'] for r in rows],'active_resources_absent':True,'artifacts_and_volumes_absent':True}))
