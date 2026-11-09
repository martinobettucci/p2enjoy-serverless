# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#constat-et-décision
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#preuves-à-terminer
"""Refuse corrupted copies of a genuinely committed, unfinished schema006 purge."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from uuid import UUID, uuid4

ROOT=Path('/srv/p2enjoy-serverless')
assert socket.gethostname()=='infra-serverless'
campaign=str(UUID(sys.argv[1]));phase=sys.argv[2];assert phase in ('artifacts','volumes')
original=ROOT/'qualification-history'/('function-version-purge-'+campaign)/'purge-inputs'/(phase+'-control.sqlite3')
assert original.is_file() and not original.is_symlink() and original.stat().st_uid==1001
assert original.stat().st_mode & 0o777==0o600
report=ROOT/'control/function-version-purge-correlation.json'
report.write_text(json.dumps({'completed':False,'cleanup':False,'skipped':0,'checks':[]})+'\n')
image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','p2enjoy-control:dev'],text=True).strip()
assert re.fullmatch('sha256:[0-9a-f]{64}',image)
work=Path(tempfile.mkdtemp(prefix='purge-correlation-rejections-',dir=ROOT/'control'))
nonce=uuid4().hex[:8];containers=[];checks=[];diagnostics=[];cleanup_errors=[];completed=False
original_sha=hashlib.sha256(original.read_bytes()).hexdigest()


def run(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,'purge_correlation_command_failed'
    return result.stdout.strip()


def observation(path):
    with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        return {'logical_sha256':hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest(),
                'schema_sha256':hashlib.sha256(json.dumps(db.execute(
                    'SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name').fetchall()).encode()).hexdigest(),
                'versions':[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')],
                'revision_columns':[r[1] for r in db.execute('PRAGMA table_info(revisions)')]}


def remove(name):
    run(['docker','rm','-f',name]);containers.remove(name)


try:
    with closing(sqlite3.connect('file:'+str(original)+'?mode=ro',uri=True)) as db:
        assert db.execute('SELECT count(*) FROM schema_migrations').fetchone()[0]==6
        pending=db.execute("SELECT c.id,c.function_id FROM storage_commands c JOIN function_operations o ON o.id=c.id "
            "WHERE c.kind='purge' AND c.state='pending' AND c.phase=? AND o.decision='commit'",(phase,)).fetchall()
        assert len(pending)==1;operation,function=pending[0]
        revision=db.execute("SELECT id FROM revisions WHERE function_id=? AND inventory_json='[]' AND events_json='{}' "
                            'AND stored_bytes>0 AND deleted_at IS NOT NULL',(function,)).fetchall()
        assert len(revision)==1;revision=revision[0][0]
        other_services=db.execute("SELECT id FROM services WHERE name='code-purge-other-service' AND deleted_at IS NULL").fetchall()
        assert len(other_services)==1;other_service=other_services[0][0]
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
    for index,(label,statement,args) in enumerate(faults,1):
        directory=work/label;directory.mkdir(mode=0o700);path=directory/'control.sqlite3'
        with closing(sqlite3.connect('file:'+str(original)+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(path)) as db:
            src.backup(db);db.execute('PRAGMA foreign_keys=ON')
            if label=='function-has-active-pointer':
                # The real reference trigger requires an available revision before assigning it.
                db.execute('UPDATE revisions SET deleted_at=NULL WHERE id=?',(revision,))
            db.execute(statement,args);db.commit()
        path.chmod(0o600);before=observation(path)
        name=f'serverless-purge-correlation-rejection-{nonce}-{index}';containers.append(name)
        compose=work/'compose.json'
        compose.write_text(json.dumps({'services':{'control':{'image':image,'container_name':name,
            'env_file':['/etc/spark/env','/run/spark/secrets'],'network_mode':'none','read_only':True,
            'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'mem_limit':'512m','cpus':1,'pids_limit':64,
            'tmpfs':['/tmp:size=16m,mode=1777,noexec,nosuid'],'volumes':[str(directory)+':/state']}}}))
        run(['docker','compose','-p','serverless-purge-correlation-'+nonce,'-f',str(compose),'up','-d','--force-recreate'])
        deadline=time.monotonic()+30
        while True:
            inspected=json.loads(run(['docker','inspect','--format','{{json .}}',name]));state=inspected['State']
            assert inspected['Image']==image
            if state['Status']=='exited':break
            assert time.monotonic()<deadline,'purge_correlation_rejection_did_not_exit';time.sleep(.1)
        assert state['ExitCode']!=0
        logs=subprocess.run(['docker','logs',name],text=True,capture_output=True,timeout=20)
        output=logs.stdout+logs.stderr
        assert 'user-defined function raised exception' in output and 'Application startup complete.' not in output
        after=observation(path);assert before==after,'refused_migration_changed_database'
        assert len(after['versions'])==6 and 'code_hash' not in after['revision_columns']
        diagnostics.append({'scenario':label,'log_sha256':hashlib.sha256(output.encode()).hexdigest()})
        remove(name)
        checks.append({'name':label,'status':'passed','application_exit_code':state['ExitCode'],
                       'transaction_rolled_back':True,'before':before,'after':after})
        print('PASS',label,flush=True)
    assert hashlib.sha256(original.read_bytes()).hexdigest()==original_sha
    completed=True
finally:
    for name in containers.copy():
        try:
            existing=subprocess.run(['docker','container','inspect',name],text=True,capture_output=True,timeout=30)
            if existing.returncode==0:remove(name)
            else:
                assert existing.returncode==1 and existing.stdout.strip()=='[]'
                assert existing.stderr.strip()=='Error response from daemon: No such container: '+name
                containers.remove(name)
        except BaseException as error:cleanup_errors.append({'container':name,'error':type(error).__name__})
    if not containers:
        try:shutil.rmtree(work)
        except BaseException as error:cleanup_errors.append({'work':work.name,'error':type(error).__name__})
    cleanup=not containers and not work.exists() and not cleanup_errors
    report.write_text(json.dumps({'completed':completed and cleanup,'cleanup':cleanup,'cleanup_errors':cleanup_errors,
        'skipped':0,'image':image,'campaign':campaign,'phase':phase,'backup_sha256':original_sha,
        'checks':checks,'diagnostics':diagnostics},indent=2)+'\n')
    assert cleanup,'purge_correlation_cleanup_incomplete'
