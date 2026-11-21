# @spec docs/BACKLOG.md#sls-106 | docs/REGRESSION_ARTIFACT_CLEANUP.md#diagnostic-recoupé-et-décision-avant-code
# @verifies docs/BACKLOG.md#sls-106 | docs/REGRESSION_ARTIFACT_CLEANUP.md#correction-bornée
"""Read-only DEV verification of one campaign function after its public purge."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import sqlite3
import subprocess
import sys
from uuid import UUID

assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
assert len(sys.argv) == 4
function, namespace, operation = sys.argv[1:]
retained = operation == '--retained'
assert all(str(UUID(value)) == value for value in (function, namespace))
if not retained: assert str(UUID(operation)) == operation
OWNED = r'(?:qa-[0-9a-f]{8}|ui-[0-9a-f]{8}x{52}|invocation-[0-9a-f]{8}|publication-ui-[0-9a-f]{8})'
root = Path('/srv/p2enjoy-serverless')
sys.path.insert(0, str(root / 'e2e'))
from control_database import read_control, control_owner
settings = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    words = shlex.split(line, comments=True)
    if len(words) == 1 and '=' in words[0]:
        key, value = words[0].split('=', 1)
        if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_DOCKER_SOCKET_HOST'):
            settings[key] = value
state = Path(settings['SERVERLESS_STATE_HOST_PATH'])
storage = Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
assert state.parent == storage.parent == root
control = state / 'control.sqlite3'
if retained:
    with read_control(control) as db:
        db.execute('BEGIN')
        row = db.execute("""SELECT f.deleted_at,f.purged_at,n.name namespace_name FROM functions f
            JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id
            WHERE f.id=? AND n.id=?""", (function, namespace)).fetchone()
        assert row and re.fullmatch(OWNED, row['namespace_name']) and row['deleted_at'] and row['purged_at'] is None
        assert not db.execute('SELECT 1 FROM function_operations WHERE function_id=?', (function,)).fetchone()
        assert not db.execute('SELECT 1 FROM execution_instances WHERE function_id=?', (function,)).fetchone()
        assert not db.execute('SELECT 1 FROM invocations WHERE function_id=? AND completed_at IS NULL', (function,)).fetchone()
        revisions = [dict(v) for v in db.execute('SELECT id,archive_sha256,stored_bytes,deleted_at FROM revisions WHERE function_id=?', (function,))]
        assert len(revisions) == 1 and revisions[0]['stored_bytes'] > 0 and revisions[0]['deleted_at'] is None
    with control_owner(control), closing(sqlite3.connect('file:' + str(storage / 'registry.sqlite3') + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        agent = db.execute('SELECT state,pending_json FROM functions WHERE id=?', (function,)).fetchone()
        assert agent and agent['state'] == 'archived' and agent['pending_json'] is None
        assert not db.execute('SELECT 1 FROM leases WHERE function_id=?', (function,)).fetchone()
        volumes = [dict(v) for v in db.execute('SELECT kind,enabled,quota,phase FROM volumes WHERE function_id=? ORDER BY kind', (function,))]
        assert {v['kind'] for v in volumes} == {'data','cache'}
        assert all(v['enabled'] == 0 and v['quota'] == 2*1024**2 and v['phase'] == 'unmounted' for v in volumes)
    revision = revisions[0]; identifier = revision['id']; assert str(UUID(identifier)) == identifier
    archive = state / 'artifacts' / identifier / 'archive.zip'
    code = state / 'artifacts' / identifier / 'code/scheduled-storage.cjs'
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    code_sha = hashlib.sha256(code.read_bytes()).hexdigest()
    assert archive_sha == revision['archive_sha256']
    assert code_sha == hashlib.sha256((root/'qualification/artifacts/scheduled-storage.cjs').read_bytes()).hexdigest()
    records = {}
    for kind in ('data','cache'):
        path = storage / 'backings' / function / kind / 'record'
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes(); assert raw
        records[kind] = {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    print(json.dumps({'completed':True,'function_id':function,'namespace_id':namespace,
        'revision_id':identifier,'archive_sha256':archive_sha,'code_sha256':code_sha,
        'record_fingerprints':records,'volumes_disabled_and_retained':True,'volumes':volumes}))
    raise SystemExit(0)
with read_control(control) as db:
    db.execute('BEGIN')
    row = db.execute('''SELECT f.id,f.updated_at,f.deleted_at,f.purged_at,f.active_revision_id,f.config_json,f.environment_json,
        n.name namespace_name FROM functions f JOIN services s ON s.id=f.service_id
        JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?''', (function, namespace)).fetchone()
    assert row and re.fullmatch(OWNED, row['namespace_name']), 'owned_campaign_required'
    assert row['deleted_at'] and row['purged_at'] and row['active_revision_id'] is None
    assert json.loads(row['config_json']) == json.loads(row['environment_json']) == {}
    command = db.execute('SELECT id,state,kind,installation_id,storage_absent,result_version,phase,completed_at,error_code FROM storage_commands WHERE id=? AND function_id=?', (operation, function)).fetchone()
    assert command and command['state'] == 'completed' and command['kind'] == 'purge'
    installation = db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
    assert command['installation_id'] == installation
    assert command['phase'] is None and command['completed_at'] and command['error_code'] is None
    assert command['result_version'] == row['updated_at']
    assert not db.execute('SELECT 1 FROM function_operations WHERE function_id=?', (function,)).fetchone()
    assert not db.execute('SELECT 1 FROM execution_instances WHERE function_id=?', (function,)).fetchone()
    assert not db.execute('SELECT 1 FROM invocations WHERE function_id=? AND completed_at IS NULL', (function,)).fetchone()
    revisions = [dict(v) for v in db.execute('SELECT id,deleted_at,stored_bytes,inventory_json,events_json FROM revisions WHERE function_id=?', (function,))]
    deployments = [dict(v) for v in db.execute('SELECT id,state,reserved_bytes,configuration_cipher,validation_json,events_json FROM deployments WHERE function_id=?', (function,))]
    assert all(v['deleted_at'] and v['stored_bytes'] == 0 and json.loads(v['inventory_json']) == [] and json.loads(v['events_json']) == {} for v in revisions)
    assert all(v['state'] not in ('prepared','receiving','validating') and v['reserved_bytes'] == 0 and v['configuration_cipher'] is None and v['validation_json'] is None and json.loads(v['events_json']) == {} for v in deployments)
    artifact_ids = {v['id'] for v in revisions + deployments}
    instance_ids = {v[0] for v in db.execute('SELECT instance_id FROM invocations WHERE function_id=? AND instance_id IS NOT NULL', (function,))}
    operation_count = db.execute("SELECT count(*) FROM storage_commands WHERE function_id=? AND kind='purge'", (function,)).fetchone()[0]
assert all(str(UUID(value)) == value for value in artifact_ids | instance_ids)
with control_owner(control), closing(sqlite3.connect('file:' + str(storage / 'registry.sqlite3') + '?mode=ro', uri=True)) as db:
    db.row_factory = sqlite3.Row
    agent = db.execute('SELECT state,version,pending_json FROM functions WHERE id=?', (function,)).fetchone()
    assert not db.execute('SELECT 1 FROM leases WHERE function_id=?', (function,)).fetchone()
    assert not db.execute('SELECT 1 FROM volumes WHERE function_id=?', (function,)).fetchone()
    if command['storage_absent']:
        assert agent is None
        agent_receipt = None
    else:
        assert agent and agent['state'] == 'purged' and agent['pending_json'] is None
        agent_receipt = db.execute('SELECT operation_id,installation_id,kind,expected_version,version FROM discard_receipts WHERE operation_id=? AND function_id=?', (operation, function)).fetchone()
        assert agent_receipt and agent_receipt['kind'] == 'purge' and agent_receipt['version'] == agent_receipt['expected_version'] + 1
        assert agent_receipt['installation_id'] == installation
        assert agent['version'] == agent_receipt['version']
def absent(paths): return all(not os.path.lexists(path) for path in paths)
mounts = [re.sub(r'\\([0-7]{3})', lambda match: chr(int(match[1], 8)), line.split()[4]) for line in Path('/proc/self/mountinfo').read_text().splitlines()]
physical = {'artifacts_absent': absent(state / 'artifacts' / key for key in artifact_ids),
    'backings_absent': absent([storage / 'backings' / function]),
    'mount_directories_absent': absent([storage / 'mounts' / function]),
    'mounts_absent': not any(value == str(storage / 'mounts' / function) or value.startswith(str(storage / 'mounts' / function) + '/') for value in mounts),
    'execution_channels_absent': absent(state / 'execution' / key for key in instance_ids)}
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]
def run(args): return subprocess.check_output(args, text=True, timeout=60)
physical['containers_absent'] = not run(docker + ['ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.function=' + function]).strip()
physical['networks_absent'] = not run(docker + ['network', 'ls', '-q', '--filter', 'label=tech.p2enjoy.serverless.function=' + function]).strip()
assert all(physical.values()), 'physical_cleanup_incomplete'
program = """import json,os,sqlite3,sys
from contextlib import closing
from app.config import Vault
vault=Vault(os.environ['SERVERLESS_MASTER_KEY'])
with closing(sqlite3.connect('file:/state/control.sqlite3?mode=ro',uri=True)) as db:
 row=db.execute('SELECT secrets_cipher FROM functions WHERE id=?',(sys.argv[1],)).fetchone()
 assert row
 print(json.dumps({'secrets_empty':vault.open(row[0])=={}}))
"""
secrets = json.loads(run(docker + ['exec', 'serverless-api', 'python', '-B', '-c', program, function]))
assert secrets['secrets_empty']
print(json.dumps({'completed': True, 'function_id': function, 'namespace_id': namespace,
    'operation_id': operation, 'purge_commands': operation_count, 'physical': physical,
    'revision_ids': sorted(v['id'] for v in revisions), 'artifact_ids': sorted(artifact_ids),
    'instance_ids': sorted(instance_ids), 'agent_receipt': dict(agent_receipt) if agent_receipt else None,
    'control_purged': True, 'configuration_empty': True, 'secrets_empty': True, 'artifact_bytes': 0}))
