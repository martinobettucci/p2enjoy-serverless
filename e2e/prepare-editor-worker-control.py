# @spec docs/BACKLOG.md#sls-147 | docs/CODE_EDITOR_READ_CONCURRENCY.md#préparation-explicite-du-contrôle-courant--sls-147
# @verifies docs/BACKLOG.md#sls-147 | docs/SCHEMA_011_REGRESSIONS.md#préparation-des-workers--sls-147
"""Prepare the real idle DEV control once, preserving its data and identity."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
HELPERS = runpy.run_path(str(ROOT / 'e2e/schedule_regressions.py'))
IMAGE = 'sha256:f016a1b71cb055c4f4c4e2fb2a2622c67c93f7a6ec26b39ec7e663cd9de4c0c7'


def diagnosis(error):
    return {'type': type(error).__name__, 'errno': getattr(error, 'errno', None),
            'returncode': getattr(error, 'returncode', None),
            'message_sha256': hashlib.sha256(str(error).encode()).hexdigest()}


def remote_program(before):
    return 'expected=' + repr(before) + '\n' + r'''
from contextlib import closing
import hashlib,json,os,socket,sqlite3,subprocess,sys,time,urllib.request,uuid
from pathlib import Path
assert socket.gethostname()=='infra-serverless' and os.geteuid()==0
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control,control_owner
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
protected={'control':{'security_metadata','namespaces','services','functions','service_tokens','revisions','function_versions','code_drafts','service_log_policies','schema_migrations'},
 'registry':{'metadata','functions','volumes','configuration_receipts','discard_receipts'}}
def call(args,timeout=15):return subprocess.check_output(args,text=True,timeout=timeout)
def inspect(timeout=15):return json.loads(call(D+['inspect','serverless-api','serverless-runtime-reference'],timeout))
def info(row):return {'id':row['Id'],'image':row['Image'],'pid':row['State']['Pid'],'running':row['State']['Running'],'health':row['State']['Health']['Status'],'started_at':row['State']['StartedAt']}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def database_state(db,kind):
 tables={r[0]:r[1]for r in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")}
 assert protected[kind]<=set(tables)
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not db.execute('PRAGMA foreign_key_check').fetchall()
 counts={};hashes={}
 for table in tables:
  quoted='"'+table.replace('"','""')+'"';counts[table]=db.execute('SELECT count(*) FROM '+quoted).fetchone()[0]
  if table in protected[kind]:
   rows=sorted(json.dumps(list(row),separators=(',',':'),ensure_ascii=False,default=lambda x:{'bytes':x.hex()})for row in db.execute('SELECT * FROM '+quoted))
   hashes[table]=digest(('\n'.join(rows)+'\n').encode())
 return {'table_counts':counts,'protected_sha256':hashes,'schema_sha256':digest(json.dumps(tables,sort_keys=True).encode())}
def files():
 values={str(p.relative_to(root/'state/artifacts')):digest(p.read_bytes())for p in sorted((root/'state/artifacts').rglob('*'))if p.is_file()}
 return {'files':len(values),'manifest_sha256':digest(json.dumps(values,sort_keys=True).encode())}
def official():return {p:digest(Path(p).read_bytes())if Path(p).exists()else None for p in expected['official_sha256']}
def control_pid(row):
 pids=[row['State']['Pid']]
 for parent in pids:pids.extend(int(x)for x in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
 found=[p for p in pids if Path('/proc',str(p),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
 assert len(found)==1;pid=found[0]
 for path in Path('/proc',str(pid),'task').iterdir():
  try:state=dict(x.split(':',1)for x in(path/'status').read_text().splitlines()if':'in x)
  except FileNotFoundError:continue
  assert int(state['TracerPid'])==0 and state['State'].split()[0]not in('t','T')
 return {'pid':pid,'birth':Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]}
before=inspect();assert [info(x)[k]for x in before for k in('id','image','started_at')]==[x[k]for x in expected['services']for k in('id','image','started_at')]
assert all(x['State']['Running']and x['State']['Health']['Status']=='healthy'for x in before)
assert set(call(D+['ps','-a','--format','{{.Names}}']).split())=={'serverless-api','serverless-runtime-reference'}
assert call(['systemctl','is-active','p2enjoy-storage-dev.service']).strip()=='active'
assert not any('serverless-restore-'in x for x in call(['systemctl','list-units','--type=service','--type=timer','--state=activating,active','--no-legend','--no-pager']).splitlines())
owner_before=control_pid(before[0]);assert official()==expected['official_sha256']and files()==expected['original_artifacts']
with read_control(root/'state/control.sqlite3')as db:
 assert db.execute('SELECT count(*) FROM code_drafts').fetchone()[0]==0
folder=root/'qualification-history'/('before-editor-worker-preparation-'+uuid.uuid4().hex)
folder.mkdir(mode=0o700);os.chown(folder,1001,1001)
backups={}
for kind,path in [('control',root/'state/control.sqlite3'),('registry',root/'storage-state/registry.sqlite3')]:
 with control_owner(root/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True,timeout=2,isolation_level=None))as db:
  db.execute('BEGIN');state=database_state(db,kind);target=folder/(kind+'.sqlite3')
  with closing(sqlite3.connect(target))as copied:
   db.backup(copied);assert database_state(copied,kind)==state
  db.rollback();target.chmod(0o600)
  assert target.stat().st_uid==1001
  backups[kind]={'path':str(target),'sha256':digest(target.read_bytes()),'uid':1001,'mode':'0600','state':state}
# One Docker request only. An observation timeout never issues a second restart.
started=time.time_ns();restart_timeout=False;restart_code=None;primary=None
try:
 result=subprocess.run(D+['restart','--time','20','serverless-api'],capture_output=True,timeout=35)
 restart_code=result.returncode
 if result.returncode:primary=RuntimeError('docker_restart_nonzero:'+str(result.returncode))
except subprocess.TimeoutExpired:
 restart_timeout=True
after=None;after_databases={};secondary=[];validated=False
try:
 deadline=time.monotonic()+120
 while True:
  remaining=deadline-time.monotonic();assert remaining>0,'fresh_control_generation_not_confirmed'
  after=inspect(min(15,remaining));assert time.monotonic()<deadline,'fresh_control_confirmation_late'
  assert after[0]['Id']==before[0]['Id']and after[0]['Image']==before[0]['Image']
  assert info(after[1])==info(before[1])
  if after[0]['State']['Running']and after[0]['State']['Health']['Status']=='healthy'and after[0]['State']['StartedAt']!=before[0]['State']['StartedAt']:break
  remaining=deadline-time.monotonic();assert remaining>0,'fresh_control_generation_not_confirmed';time.sleep(min(.5,remaining))
 owner_after=control_pid(after[0]);assert owner_after!=owner_before
 with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=5)as response:assert response.status==200
 after_databases={}
 for kind,path in [('control',root/'state/control.sqlite3'),('registry',root/'storage-state/registry.sqlite3')]:
  with control_owner(root/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True,timeout=2))as db:
   state=database_state(db,kind);after_databases[kind]=state
   assert state['schema_sha256']==backups[kind]['state']['schema_sha256']and state['protected_sha256']==backups[kind]['state']['protected_sha256']
  assert digest(Path(backups[kind]['path']).read_bytes())==backups[kind]['sha256']
 assert official()==expected['official_sha256']and files()==expected['original_artifacts']
 validated=True
except BaseException as error:
 if primary is None:primary=error
 else:secondary.append({'phase':'reconcile','type':type(error).__name__,'message_sha256':digest(str(error).encode())})
value={'completed':primary is None,'before':[info(x)for x in before],'after':[info(x)for x in after]if after is not None else None,'owner_before':owner_before,'owner_after':locals().get('owner_after'),'backups':backups,'databases_after':after_databases,'restart_started_at_ns':started,'restart_exit_code':restart_code,'restart_observation_timeout':restart_timeout,'same_cid_image':validated,'reference_unchanged':validated,'protected_tables_unchanged':validated,'secondary_errors':secondary,'failure':{'type':type(primary).__name__,'message_sha256':digest(str(primary).encode())}if primary is not None else None,'groups_added':0}
try:print(json.dumps(value),flush=True)
except BaseException as error:
 if primary is None:primary=error
 else:secondary.append({'phase':'print','type':type(error).__name__,'message_sha256':digest(str(error).encode())})
if primary is not None:raise primary
'''


def prepare():
    os.chdir(ROOT)
    os.umask(0o077)
    folder = ROOT / '.local/e2e' / ('editor-worker-preparation-' + uuid4().hex)
    folder.mkdir(mode=0o700, parents=True)
    value = {'completed': False, 'groups_added': 0, 'failure': None,
             'secondary_errors': [], 'created_at_ns': time.time_ns(),
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
             'preparer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    primary = None
    try:
        assert not subprocess.check_output(['git', 'status', '--porcelain']), 'committed_clean_sources_required'
        before = HELPERS['native_state']()
        assert before['services'][0]['image'] == IMAGE
        value['native_before'] = before
        program = remote_program(before)
        (folder / 'remote-program.py').write_text(program)
        value['remote_program_sha256'] = hashlib.sha256(program.encode()).hexdigest()
        value['exit_code'] = None
        value['transport_result'] = 'not-started'
        # Redirect before launch: partial streams survive a transport timeout.
        with (folder / 'stdout').open('xb') as stdout, (folder / 'stderr').open('xb') as stderr:
            value['transport_result'] = 'pending'
            try:
                result = subprocess.run(HELPERS['SSH'] + ['python3 -B -'], input=program.encode(),
                                        stdout=stdout, stderr=stderr, timeout=240)
                value['exit_code'] = result.returncode
                value['transport_result'] = 'observed'
                if result.returncode != 0:
                    primary = RuntimeError('native_worker_preparation_failed:' + str(result.returncode))
            except BaseException as error:
                primary = error
                value['transport_result'] = 'unknown'
        for channel in ('stdout', 'stderr'):
            try:
                raw = (folder / channel).read_bytes()
                value[channel] = {'path': str((folder / channel).relative_to(ROOT)),
                                  'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            except BaseException as error:
                if primary is None:
                    primary = error
                else:
                    value['secondary_errors'].append({'phase': channel + '-retain', **diagnosis(error)})
        try:
            raw = (folder / 'stdout').read_bytes()
            if raw:
                value['native_preparation'] = json.loads(raw)
        except BaseException as error:
            if primary is None:
                primary = error
            else:
                value['secondary_errors'].append({'phase': 'parse', **diagnosis(error)})
        # Observe even after timeout/nonzero; never repeat the Docker request.
        try:
            after = HELPERS['native_state']()
            value['native_after'] = after
            HELPERS['same_installation'](before, after)
        except BaseException as error:
            if primary is None:
                primary = error
            else:
                value['secondary_errors'].append({'phase': 'native-after', **diagnosis(error)})
        if primary is not None:
            raise primary
        assert value['native_preparation']['completed']
        assert after['services'][0]['started_at'] != before['services'][0]['started_at']
        value.update(native_after=after, completed=True)
    except BaseException as error:
        if primary is None:
            primary = error
        elif error is not primary:
            value['secondary_errors'].append({'phase': 'prepare', **diagnosis(error)})
        value['failure'] = diagnosis(primary)
    value['finished_at_ns'] = time.time_ns()
    path = folder / 'report.json'
    try:
        path.write_text(json.dumps(value, indent=2) + '\n')
    except BaseException as error:
        value['secondary_errors'].append({'phase': 'save', **diagnosis(error)})
        value['completed'] = False
        if primary is None:
            primary = error
            value['failure'] = diagnosis(error)
    try:
        print(json.dumps({'completed': value['completed'] and primary is None,
                          'report': str(path.relative_to(ROOT)), 'groups_added': 0}), flush=True)
    except BaseException as error:
        value['secondary_errors'].append({'phase': 'print', **diagnosis(error)})
        value['completed'] = False
        if primary is None:
            primary = error
            value['failure'] = diagnosis(error)
    if primary is not None:
        # A distinct terminal receipt preserves publication errors when possible;
        # failure to save it never replaces the first exception.
        try:
            (folder / 'publication-errors.json').write_text(json.dumps(value, indent=2) + '\n')
        except BaseException as error:
            value['secondary_errors'].append({'phase': 'terminal-save', **diagnosis(error)})
        raise primary
    return str(path.relative_to(ROOT))


if __name__ == '__main__':
    assert sys.argv[1:] == []
    prepare()
