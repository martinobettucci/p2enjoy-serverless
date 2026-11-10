# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009
"""Read-only DEV recoup of the exact API-created schedule version campaign."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

campaign = json.loads(sys.argv[1])
assert set(campaign) == {'namespace_id', 'function_ids'}
assert str(UUID(campaign['namespace_id'])) == campaign['namespace_id']
assert len(campaign['function_ids']) == 3
assert len(set(campaign['function_ids'])) == 3
assert all(str(UUID(v)) == v for v in campaign['function_ids'])
purged = len(sys.argv) == 3 and sys.argv[2] == '--purged'
program = 'campaign=' + repr(campaign) + '\npurged=' + repr(purged) + '\n' + r'''
import hashlib,json,re,socket,subprocess,sys
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
ids=campaign['function_ids'];marks=','.join('?' for _ in ids)
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN')
 ns=db.execute('SELECT * FROM namespaces WHERE id=?',(campaign['namespace_id'],)).fetchone()
 assert ns and re.fullmatch('scheduled-functions-[0-9a-f]{8}',ns['name'])
 actual={r[0] for r in db.execute('SELECT f.id FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=?',(ns['id'],))}
 assert actual==set(ids)
 functions=[dict(r) for r in db.execute('SELECT id,name,active_revision_id,deleted_at,purged_at FROM functions WHERE id IN ('+marks+')',ids)]
 generations=[dict(r) for r in db.execute('SELECT * FROM schedule_generations WHERE function_id IN ('+marks+') ORDER BY id',ids)]
 firings=[dict(r) for r in db.execute('SELECT * FROM schedule_firings WHERE function_id IN ('+marks+') ORDER BY window_at,id',ids)]
 invocations=[dict(r) for r in db.execute('SELECT id,function_id,state,created_at,dispatched_at,completed_at,handler_started,requested_code_hash,resolved_code_hash,trigger,schedule_firing_id,schedule_slot,logs FROM invocations WHERE function_id IN ('+marks+') ORDER BY created_at,id',ids)]
 cursor=db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
 counts={n:db.execute(q).fetchone()[0] for n,q in {'functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','operations':'SELECT count(*) FROM function_operations','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
services=json.loads(subprocess.check_output(D+['inspect','serverless-api','serverless-runtime-reference'],text=True));assert all(v['State']['Health']['Status']=='healthy' for v in services)
physical=None;artifacts=None;embedded=None
if purged:
 assert not any(counts.values()) and all(v['purged_at'] for v in functions)
 assert not any(v['retired_at'] is None for v in generations)
 physical=json.loads(subprocess.check_output(['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps({campaign['namespace_id']:ids})],text=True));assert physical['completed']
 inventory={str(p.relative_to(root/'state/artifacts')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'state/artifacts').rglob('*')) if p.is_file()}
 artifacts={'files':len(inventory),'manifest_sha256':hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()}
 source="import hashlib,json;from pathlib import Path;r=Path('/app');print(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']}))"
 embedded=json.loads(subprocess.check_output(D+['exec','serverless-api','python','-B','-c',source],text=True))
print(json.dumps({'completed':True,'functions':functions,'generations':generations,'firings':firings,'invocations':invocations,'cursor':cursor,'counts':counts,'physical':physical,'original_artifacts':artifacts,'embedded_backend':embedded,'services':[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt']} for v in services],'official_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['/etc/spark/env','/run/spark/secrets','/etc/spark/routes']}}))
'''
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                         '-J', 'ubuntu@51.158.54.202', 'root@10.77.0.24', 'python3 -B -'],
                        input=program, text=True, capture_output=True, timeout=120)
assert result.returncode == 0, result.stderr[-2000:]
value = json.loads(result.stdout)
if purged:
    assert value['original_artifacts'] == {'files':5982, 'manifest_sha256':'846904e1437a034d7fd95488f246cd5b3dc935a4723d20abf9bb419673e5d482'}
    sources = {str(p.relative_to(Path('control'))):__import__('hashlib').sha256(p.read_bytes()).hexdigest()
               for p in [*Path('control/app').glob('*.py'), *Path('control/migrations').glob('*.sql')]}
    sources['function_code_hash.py'] = __import__('hashlib').sha256(Path('function_code_hash.py').read_bytes()).hexdigest()
    assert value['embedded_backend'] == sources
print(json.dumps(value))
