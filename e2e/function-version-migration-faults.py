# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
"""Real application startup against faulted copies of the genuine pre-upgrade DB."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from uuid import UUID,uuid4

ROOT=Path('/srv/p2enjoy-serverless');assert Path('/etc/hostname').read_text().strip()=='infra-serverless'
report=ROOT/'control/function-version-migration-faults.json'
report.write_text(json.dumps({'completed':False,'cleanup':False,'skipped':0,'checks':[]})+'\n')
backup=sys.argv[1];identifier=str(UUID(sys.argv[2]));assert re.fullmatch('before-function-code-hash-[0-9a-f]{32}',backup)
original=ROOT/'state/backups'/backup/'control.sqlite3';assert original.is_file() and not original.is_symlink()
baseline=json.loads(original.with_name('baseline.json').read_text());assert baseline['scope']['function_id']==identifier
work=Path(tempfile.mkdtemp(prefix='version-migration-faults-',dir=ROOT/'control'));checks=[];containers=[];completed=False;cleanup_errors=[];diagnostics=[]
image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','p2enjoy-control:dev'],text=True).strip()
source_sha=hashlib.sha256(original.read_bytes()).hexdigest();nonce=uuid4().hex[:8]


def run(args,**kwargs):
    result=subprocess.run(args,capture_output=True,text=True,timeout=90,**kwargs)
    assert result.returncode==0,'migration_fault_command_failed'
    return result.stdout.strip()


def logical(path):
    with closing(sqlite3.connect(path)) as db:
        return hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest()


def copy_database(name):
    directory=work/name;directory.mkdir(mode=0o700);path=directory/'control.sqlite3'
    with closing(sqlite3.connect('file:'+str(original)+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(path)) as dest:src.backup(dest)
    return directory,path


def docker(name,directory,*command,detached=False):
    containers.append(name)
    if detached:
        compose=work/'compose.json'
        compose.write_text(json.dumps({'services':{'control':{'image':image,'container_name':name,
            'env_file':['/etc/spark/env','/run/spark/secrets'],'network_mode':'none','read_only':True,
            'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],'mem_limit':'512m','cpus':1,'pids_limit':64,
            'tmpfs':['/tmp:size=16m,mode=1777,noexec,nosuid'],'volumes':[str(directory)+':/state']}}}))
        return run(['docker','compose','-p','serverless-version-migration-'+nonce,'-f',str(compose),'up','-d','--force-recreate'])
    return run(['docker','run',*(['-d'] if detached else []),'--name',name,'--network','none','--read-only',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','512m','--cpus','1','--pids-limit','64',
        '--tmpfs','/tmp:size=16m,mode=1777,noexec,nosuid',
        '--mount','type=bind,source='+str(directory)+',target=/state',image,*command])


def remove(name):
    run(['docker','rm','-f',name]);containers.remove(name)


try:
    faults=[('missing-active-inventory',"inventory_json='[]'"),('invalid-inventory-json',"inventory_json='not-json'"),
            ('invalid-inventory-entry',"inventory_json='[{}]'"),('invalid-events',"events_json='{}'"),
            ('invalid-handler',"handler='../bad.handler'"),('invalid-runtime-image',"image_id='unknown'")]
    for index,(label,assignment) in enumerate(faults,1):
        directory,path=copy_database(label)
        with closing(sqlite3.connect(path)) as db:
            revision=db.execute('SELECT active_revision_id FROM functions WHERE id=?',(identifier,)).fetchone()[0];assert revision
            db.execute('UPDATE revisions SET '+assignment+' WHERE id=?',(revision,));db.commit()
        before=logical(path);name=f'serverless-version-migration-rejection-{nonce}-{index}'
        docker(name,directory,detached=True)
        deadline=time.monotonic()+30
        while True:
            state=json.loads(run(['docker','inspect','--format','{{json .State}}',name]))
            if state['Status']=='exited':break
            assert time.monotonic()<deadline,'migration_rejection_did_not_exit';time.sleep(.1)
        assert state['ExitCode']!=0
        output=subprocess.run(['docker','logs',name],text=True,capture_output=True,timeout=20)
        diagnostics.append({'scenario':label,'log_sha256':hashlib.sha256((output.stdout+output.stderr).encode()).hexdigest(),
            'exception_types':re.findall(r'^([a-zA-Z_.]+(?:Error|Exception)):',output.stdout+output.stderr,re.M)})
        assert 'user-defined function raised exception' in output.stdout+output.stderr
        assert 'Application startup complete.' not in output.stdout+output.stderr
        with closing(sqlite3.connect(path)) as db:
            assert not db.execute("SELECT 1 FROM schema_migrations WHERE version='007_function_code_hash.sql'").fetchone()
            assert 'code_hash' not in [r[1] for r in db.execute('PRAGMA table_info(revisions)')]
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert logical(path)==before,'failed_migration_changed_database'
        remove(name);checks.append({'name':label,'status':'passed','application_exit_code':state['ExitCode'],'transaction_rolled_back':True});print('PASS',label,flush=True)
    directory,path=copy_database('constraints');name='serverless-version-hash-constraints-'+nonce
    program=r'''
import json,sqlite3,uuid
from pathlib import Path
from app.db import Database
database=Database(Path('/state'));database.migrate();db=database.connect()
row=db.execute('SELECT * FROM revisions WHERE function_id=? AND deleted_at IS NULL LIMIT 1',(FUNCTION,)).fetchone();assert row
columns=row.keys();values=list(row);position=columns.index('code_hash');id_position=columns.index('id');checks=[]
def refused(label,sql,args,expected):
 db.execute('BEGIN IMMEDIATE')
 try:
  try:db.execute(sql,args)
  except sqlite3.IntegrityError as error:assert expected in str(error)
  else:raise AssertionError('constraint_not_enforced:'+label)
 finally:db.rollback()
 checks.append(label)
for label,value in [('missing',None),('short','a'*63),('uppercase','A'*64),('invalid-character','g'*64)]:
 candidate=values.copy();candidate[id_position]=str(uuid.uuid4());candidate[position]=value
 refused(label,'INSERT INTO revisions ('+','.join(columns)+') VALUES ('+','.join('?' for c in columns)+')',candidate,'revision_code_hash_required' if value is None else 'CHECK constraint failed')
for label,value in [('immutable-null',None),('immutable-other','b'*64)]:
 refused(label,'UPDATE revisions SET code_hash=? WHERE id=?',(value,row['id']),'revision_code_hash_immutable')
db.execute('BEGIN IMMEDIATE')
candidate=values.copy();candidate[id_position]=str(uuid.uuid4())
db.execute('INSERT INTO revisions ('+','.join(columns)+') VALUES ('+','.join('?' for c in columns)+')',candidate)
db.rollback();db.close();print(json.dumps({'checks':checks,'valid_control_insert':True}))
'''.replace('FUNCTION',repr(identifier))
    result=json.loads(docker(name,directory,'python','-B','-c',program));remove(name)
    assert len(result['checks'])==6 and result['valid_control_insert']
    checks.append({'name':'required-valid-immutable-hash','status':'passed',**result});print('PASS required-valid-immutable-hash',flush=True)
    assert hashlib.sha256(original.read_bytes()).hexdigest()==source_sha
    completed=True
finally:
    try:
        for name in containers.copy():
            try:
                existing=subprocess.run(['docker','container','inspect',name],text=True,capture_output=True,timeout=30)
                if existing.returncode==0:remove(name)
                else:
                    assert existing.returncode==1 and existing.stdout.strip()=='[]' and existing.stderr.strip()=='Error response from daemon: No such container: '+name
                    containers.remove(name)
            except BaseException as error:cleanup_errors.append({'container':name,'error':type(error).__name__})
        if not containers:
            try:shutil.rmtree(work)
            except BaseException as error:cleanup_errors.append({'work':work.name,'error':type(error).__name__})
    finally:
        cleanup=not containers and not work.exists() and not cleanup_errors
        report.write_text(json.dumps({'completed':completed and cleanup,'cleanup':cleanup,'cleanup_errors':cleanup_errors,
            'skipped':0,'image':image,'backup':backup,'backup_sha256':source_sha,'checks':checks,'diagnostics':diagnostics},indent=2)+'\n')
    assert cleanup,'migration_fault_cleanup_incomplete'
