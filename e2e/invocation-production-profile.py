# @spec docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#passage-sql-historique-f73
# @verifies docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#résultat-et-nettoyage
# @spec docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#charge-et-mesures-sqlclient
"""Read actual SQL work and phase timestamps from the owned DEV invocation fixture."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import socket
import subprocess
import sys
import time
from uuid import UUID

ROOT = Path('/srv/p2enjoy-serverless')
IMAGE = 'sha256:f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0'
CURRENT_IMAGE = 'sha256:f016a1b71cb055c4f4c4e2fb2a2622c67c93f7a6ec26b39ec7e663cd9de4c0c7'
LEGACY_EXPIRATION = 'SELECT e.sequence,e.service_id,e.payload_bytes FROM execution_log_events e JOIN service_log_policies p ON p.service_id=e.service_id WHERE e.observed_at<max(p.expiration_floor,?-p.retention_minutes*60) ORDER BY e.sequence LIMIT ?'
CURRENT_EXPIRATION = 'SELECT e.sequence,e.service_id,e.payload_bytes FROM service_log_policies p CROSS JOIN execution_log_events e WHERE e.service_id=p.service_id AND e.observed_at<max(p.expiration_floor,?-p.retention_minutes*60) ORDER BY e.sequence LIMIT ?'

INSPECTION = r'''
import hashlib,json,sqlite3,time
from pathlib import Path
functions=FUNCTION_IDS
expected_migrations=EXPECTED_MIGRATIONS
with sqlite3.connect('file:/state/control.sqlite3?mode=ro',uri=True,timeout=1) as db:
 db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
 assert [r[0]for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]==expected_migrations
 assert sorted(r[0]for r in db.execute('SELECT id FROM functions WHERE deleted_at IS NULL'))==sorted(functions)
 counts={n:db.execute('SELECT count(*) FROM '+n).fetchone()[0]for n in ('invocations','execution_log_events','service_log_policies','schedule_firings')}
 assert db.execute('SELECT count(*) FROM invocations WHERE function_id NOT IN (?,?)',functions).fetchone()[0]==0
 assert counts['schedule_firings']==0 and db.execute("SELECT count(*) FROM invocations WHERE trigger<>'http'").fetchone()[0]==0
 # These are native metadata, never reconstructed rows, logs, or secret values.
 calls=[dict(zip(('id','function_id','state','created_at','queued_at','admitted_at','dispatched_at','completed_at'),r))for r in db.execute('SELECT id,function_id,state,created_at,queued_at,admitted_at,dispatched_at,completed_at FROM invocations ORDER BY created_at,id')]
 now=time.time()
 queries={'admission_global_queued_count':("SELECT count(*) FROM invocations WHERE state IN ('receiving','queued')",())}
 for index,fn in enumerate(functions):
  for name,sql in (
   ('admission_first',"SELECT id FROM invocations WHERE function_id=? AND state IN ('receiving','queued') ORDER BY created_at,id LIMIT 1"),
   ('admission_queued_count',"SELECT count(*) FROM invocations WHERE function_id=? AND state IN ('receiving','queued')"),
   ('admission_active_count',"SELECT count(*) FROM invocations WHERE function_id=? AND state IN ('admitted','running')")):
   queries[name+'_'+str(index)]=(sql,(fn,))
 queries.update({
  'logs_expiration':(LOGS_EXPIRATION_QUERY,(now,200)),
  'buffers_expiration':("SELECT i.id,i.service_id FROM invocations i JOIN service_log_policies p ON p.service_id=i.service_id WHERE i.completed_at<max(p.expiration_floor,?-p.retention_minutes*60) AND i.logs_collection_state<>'expired' ORDER BY i.completed_at,i.id LIMIT ?",(now,200)),
  'invocation_age_candidates':('SELECT id FROM invocations WHERE completed_at IS NOT NULL AND completed_at<? AND NOT EXISTS (SELECT 1 FROM schedule_firings t WHERE t.invocation_id=invocations.id AND t.completed_at IS NULL)',(now-7*86400,)),
  'invocation_count_candidates':('SELECT id FROM invocations WHERE completed_at IS NOT NULL AND NOT EXISTS (SELECT 1 FROM schedule_firings t WHERE t.invocation_id=invocations.id AND t.completed_at IS NULL) ORDER BY completed_at DESC,id DESC LIMIT -1 OFFSET 10000',()),
  'eviction_first':('SELECT sequence,service_id,payload_bytes FROM execution_log_events ORDER BY sequence LIMIT ?',(1,))})
 results={}
 for name,(sql,params)in queries.items():
  samples=[]
  for iteration in range(3):
   progress_calls=[0]
   def progress():
    progress_calls[0]+=1
    return int(progress_calls[0]>=100000)
   db.set_progress_handler(progress,100)
   wall=time.monotonic_ns();cpu=time.process_time_ns();rows=db.execute(sql,params).fetchall()
   samples.append({'iteration':iteration,'wall_ns':time.monotonic_ns()-wall,'cpu_ns':time.process_time_ns()-cpu,'result_rows':len(rows),'vm_progress_calls':progress_calls[0],'vm_progress_quantum':100})
   db.set_progress_handler(None,0)
  results[name]={'sql':sql,'parameters':list(params),'plan':[list(r)for r in db.execute('EXPLAIN QUERY PLAN '+sql,params)],'samples':samples}
 backend={str(p.relative_to(Path('/app'))):hashlib.sha256(p.read_bytes()).hexdigest()for p in [*Path('/app/app').glob('*.py'),*Path('/app/migrations').glob('*.sql'),Path('/app/function_code_hash.py')]}
 result={'completed':True,'qualified_groups':0,'sqlite_version':sqlite3.sqlite_version,'sqlite_source_id':db.execute('SELECT sqlite_source_id()').fetchone()[0],
  'cardinalities':counts,'calls':calls,'queries':results,'backend_sha256':backend,
  'collection_id':db.execute('SELECT collection_id FROM execution_log_state WHERE singleton=1').fetchone()[0],
  'limitations':['Read-only measurement process costs, not application CPU/runtime.','Probe intervals may affect concurrent throughput.','No COMMIT/fsync or network duration attributed by SELECTs.']}
 print(json.dumps(result))
'''


def main():
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    current_cost = len(sys.argv) == 7 and sys.argv[-1] == '--current-cost-profile'
    assert len(sys.argv) == (7 if current_cost else 6)
    campaign, point, container_id, image, functions_raw = sys.argv[1:6]
    assert str(UUID(campaign)) == campaign and point in (('256', '1024', '2048', 'complete', 'smoke-complete') if current_cost else ('256', '1024', '2048', 'complete'))
    assert re.fullmatch('[a-f0-9]{64}', container_id) and image == (CURRENT_IMAGE if current_cost else IMAGE)
    functions = functions_raw.split(',')
    assert len(functions) == len(set(functions)) == 2 and all(str(UUID(v)) == v for v in functions)
    work = ROOT / 'qualification-history' / ('instance-limit-' + campaign)
    assert work.resolve() == work and not work.is_symlink()
    info = work.stat(); assert info.st_uid == 0 and info.st_mode & 0o777 == 0o750
    journal = work / 'restore.json'
    item = json.loads(journal.read_bytes())
    assert info.st_gid == item['gid'] == pwd.getpwnam('spark-docker').pw_gid
    assert item['campaign'] == campaign and item['work'] == str(work)
    assert item['mode'] == 'instance-limit' and item['guard_seconds'] == 2700 and not item.get('restored')
    assert not item.get('retention_replay') and not item.get('firing_replay')
    if current_cost:
        cost=item['invocation_cost_profile'];assert cost['mode'] in ('smoke','full','parser-loss') and not cost.get('completed')
        assert (point=='smoke-complete') == (cost['mode']!='full')
    else:assert not item.get('invocation_cost_profile')
    source = ROOT / 'e2e/storage-legacy-environment.py'
    spec = importlib.util.spec_from_file_location('profile_window', source)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    before = helper.instance_limit_observation(item)
    assert before['container']['id'] == container_id and before['container']['image'] == image
    assert sorted(v['id'] for v in before['functions'] if not v['deleted_at']) == sorted(functions)
    migrations = [p.name for p in sorted((ROOT / 'control/migrations').glob('*.sql'))]
    assert migrations == helper.SCHEMA_011
    inspection = INSPECTION.replace('FUNCTION_IDS', repr(functions)).replace('EXPECTED_MIGRATIONS', repr(migrations)).replace('LOGS_EXPIRATION_QUERY',repr(CURRENT_EXPIRATION if current_cost else LEGACY_EXPIRATION))
    started = time.time_ns()
    process = subprocess.run(item['docker'] + ['exec', container_id, 'python', '-B', '-c', inspection],
                             capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, 'production_sql_read_failed'
    result = json.loads(process.stdout)
    expected = {str(p.relative_to(ROOT / 'control')): hashlib.sha256(p.read_bytes()).hexdigest()
                for directory, pattern in (('control/app', '*.py'), ('control/migrations', '*.sql'))
                for p in (ROOT / directory).glob(pattern)}
    expected['function_code_hash.py'] = hashlib.sha256((ROOT / 'function_code_hash.py').read_bytes()).hexdigest()
    assert result['backend_sha256'] == expected and len(expected) == 42
    after = helper.container(item, helper.temporary_control_name(item))
    assert after['id'] == container_id and after['image'] == image and after['running']
    assert not json.loads(journal.read_bytes()).get('restored')
    result.update(campaign=campaign, point=point, container_id=container_id, image=image, profile_scope='current-cost' if current_cost else 'legacy-f73',
                  started_at_ns=str(started) if current_cost else started, finished_at_ns=str(time.time_ns()) if current_cost else time.time_ns(),
                  operator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  sql_program_sha256=hashlib.sha256(inspection.encode()).hexdigest())
    print(json.dumps(result))


if __name__ == '__main__': main()
