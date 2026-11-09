# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
# @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuves-et-manuel
# @verifies docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuves-et-manuel
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#qualification-réelle-et-autorité
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#qualification-réelle-et-autorité
# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
# @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
# @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
# @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#preuves-et-limites
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#preuves-et-limites
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md#preuves-et-limites
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md#preuves-et-limites
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#livraison-et-limites
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#livraison-et-limites
"""Read-only physical recoup of completed, API-created storage console campaigns.

Run as root on the DEV SPARK with one JSON argument mapping namespace UUIDs
to their complete list of function UUIDs. Never reads or prints secret values
outside the existing control container. An incomplete cleanup fails the proof.
"""
from contextlib import closing, contextmanager
import json
import os
import pwd
from pathlib import Path
import re
import shlex
import socket
import sqlite3
import subprocess
import sys
from uuid import UUID

sys.path.insert(0, '/srv/p2enjoy-serverless/e2e')
from control_database import read_control

assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
campaigns = json.loads(sys.argv[1])
assert isinstance(campaigns, dict) and 1 <= len(campaigns) <= 10
identifiers = []
for namespace, functions in campaigns.items():
    assert str(UUID(namespace)) == namespace and isinstance(functions, list)
    assert all(str(UUID(value)) == value for value in functions)
    identifiers.extend(functions)
assert len(set(identifiers)) == len(identifiers) <= 50
settings = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    parts = shlex.split(line, comments=True)
    if len(parts) == 1 and '=' in parts[0]:
        key, value = parts[0].split('=', 1)
        if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_DOCKER_SOCKET_HOST'):
            settings[key] = value
state = Path(settings['SERVERLESS_STATE_HOST_PATH'])
storage = Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]

def run(*args, input=None):
    return subprocess.run(docker + list(args), input=input, text=True, capture_output=True, check=True, timeout=30).stdout.strip()

result = {'completed': False, 'target': 'infra-serverless DEV', 'campaigns': campaigns, 'functions': {}}
artifact_ids, instance_ids = set(), set()
with read_control(state / 'control.sqlite3') as db:
    db.execute('BEGIN')
    installation = db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
    for namespace, functions in campaigns.items():
        row = db.execute('SELECT name,deleted_at FROM namespaces WHERE id=?', (namespace,)).fetchone()
        # @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_ROUTE_CYCLES.md#responsabilités-et-nettoyage
        # @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_ROUTE_CYCLES.md#responsabilités-et-nettoyage
        assert row and row['deleted_at'] is not None and re.fullmatch(r'(?:(storage-console-api|storage-ui|storage-recovery|storage-validation|service-configuration|service-transport|invocation-url-transport|invocation-addresses(?:-ui)?|invocation-route-cycles|invocation-route-pause|source-access|invocation-pagination-(?:ui|cli)|validator-names|function-versions|version-cli|version-upload-capacity|version-duplicate-recovery|version-state-transport)-[0-9a-f]{8}|function-catalogue-(?:api|ui)-[0-9a-f]{8}(?:-[a-z0-9_-]{1,32})?)', row['name']), 'owned_campaign_required'
        actual = {r[0] for r in db.execute('SELECT f.id FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=?', (namespace,))}
        assert actual == set(functions), 'campaign_inventory_mismatch'
        assert not db.execute('SELECT 1 FROM services WHERE namespace_id=? AND deleted_at IS NULL', (namespace,)).fetchone(), 'live_campaign_service'
        assert not db.execute('SELECT 1 FROM service_tokens t JOIN services s ON s.id=t.service_id WHERE s.namespace_id=? AND t.revoked_at IS NULL', (namespace,)).fetchone(), 'live_campaign_token'
    for identifier in identifiers:
        row = db.execute('''SELECT f.id,
            f.deleted_at IS NOT NULL AS function_deleted, f.purged_at IS NOT NULL AS function_purged,
            f.active_revision_id IS NULL AS revision_detached,
            f.config_json='{}' AS configuration_empty, f.environment_json='{}' AS environment_empty,
            s.deleted_at IS NOT NULL AS service_deleted,
            NOT EXISTS(SELECT 1 FROM function_operations WHERE function_id=f.id) AS guard_absent,
            NOT EXISTS(SELECT 1 FROM execution_instances WHERE function_id=f.id) AS instances_absent,
            NOT EXISTS(SELECT 1 FROM invocations WHERE function_id=f.id AND state IN ('receiving','queued','admitted','running')) AS active_calls_absent,
            NOT EXISTS(SELECT 1 FROM storage_commands WHERE function_id=f.id AND state IN ('preparing','pending')) AS pending_commands_absent,
            NOT EXISTS(SELECT 1 FROM revisions WHERE function_id=f.id AND
                (deleted_at IS NULL OR stored_bytes!=0 OR inventory_json!='[]' OR events_json!='{}')) AS revision_content_cleared,
            NOT EXISTS(SELECT 1 FROM deployments WHERE function_id=f.id AND
                (state IN ('prepared','receiving','validating') OR reserved_bytes!=0 OR configuration_cipher IS NOT NULL
                 OR validation_json IS NOT NULL OR events_json!='{}')) AS deployment_content_cleared
            FROM functions f JOIN services s ON s.id=f.service_id WHERE f.id=?''', (identifier,)).fetchone()
        assert row and all(row[key] for key in row.keys() if key != 'id'), 'control_cleanup_incomplete'
        receipt = db.execute("SELECT id,result_version FROM storage_commands WHERE function_id=? AND kind='purge' AND state='completed' AND phase IS NULL AND completed_at IS NOT NULL AND error_code IS NULL", (identifier,)).fetchone()
        assert receipt, 'completed_purge_missing'
        result['functions'][identifier] = {'control': dict(row), 'operation_id': receipt['id'], 'result_version': receipt['result_version']}
        artifact_ids.update(r[0] for r in db.execute('SELECT id FROM revisions WHERE function_id=? UNION SELECT id FROM deployments WHERE function_id=?', (identifier, identifier)))
        instance_ids.update(r[0] for r in db.execute('SELECT instance_id FROM invocations WHERE function_id=? AND instance_id IS NOT NULL', (identifier,)))
    result['global_control_reservations'] = dict(db.execute('SELECT count(*) AS instances,coalesce(sum(cpu_nanos),0) AS cpu_nanos,coalesce(sum(memory_mib),0) AS memory_mib FROM execution_instances').fetchone())
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []

registry = storage / 'registry.sqlite3'

@contextmanager
def read_registry():
    account = pwd.getpwnam('spark-docker')
    info = registry.stat()
    assert (info.st_uid, info.st_gid) == (account.pw_uid, account.pw_gid), 'registry_owner_mismatch'
    groups = os.getgroups()
    try:
        os.setgroups(os.getgrouplist(account.pw_name, account.pw_gid))
        os.setegid(account.pw_gid)
        os.seteuid(account.pw_uid)
        with closing(sqlite3.connect('file:' + str(registry) + '?mode=ro', uri=True)) as db:
            yield db
    finally:
        os.seteuid(0)
        os.setegid(0)
        os.setgroups(groups)
    for path in (registry, Path(str(registry) + '-wal'), Path(str(registry) + '-shm')):
        assert (path.stat().st_uid, path.stat().st_gid) == (account.pw_uid, account.pw_gid), 'registry_sidecar_owner_mismatch'

with read_registry() as db:
    db.row_factory = sqlite3.Row
    db.execute('BEGIN')
    for identifier in identifiers:
        row = db.execute('SELECT state,pending_json FROM functions WHERE id=?', (identifier,)).fetchone()
        assert row and row['state'] == 'purged' and row['pending_json'] is None
        assert not db.execute('SELECT 1 FROM volumes WHERE function_id=?', (identifier,)).fetchone()
        assert not db.execute('SELECT 1 FROM leases WHERE function_id=?', (identifier,)).fetchone()
        receipt = db.execute('SELECT operation_id,installation_id,kind,expected_version,version FROM discard_receipts WHERE function_id=?', (identifier,)).fetchone()
        assert receipt and receipt['operation_id'] == result['functions'][identifier]['operation_id']
        assert receipt['installation_id'] == installation and receipt['kind'] == 'purge' and receipt['version'] == receipt['expected_version'] + 1
        result['functions'][identifier]['agent_receipt'] = dict(receipt)
    result['global_storage_allocated_bytes'] = db.execute('SELECT coalesce(sum(quota),0) FROM volumes').fetchone()[0]

def absent(paths):
    return all(not os.path.lexists(path) for path in paths)

mounts = [re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), line.split()[4]) for line in Path('/proc/self/mountinfo').read_text().splitlines()]
physical = {
    'artifacts_absent': absent(state / 'artifacts' / key for key in artifact_ids),
    'backings_absent': absent(storage / 'backings' / key for key in identifiers),
    'mount_directories_absent': absent(storage / 'mounts' / key for key in identifiers),
    'mounts_absent': all(not any(value == str(storage / 'mounts' / key) or value.startswith(str(storage / 'mounts' / key) + '/') for value in mounts) for key in identifiers),
    'known_execution_channels_absent': absent(state / 'execution' / key for key in instance_ids),
    # Trash/validator channel UUIDs are no longer attributable after completion.
    # Require a globally empty inventory instead of assuming foreign ownership.
    'global_trash_empty': not any((storage / 'trash').iterdir()),
    'global_validation_channels_empty': not any((state / 'validation').iterdir()),
    'global_execution_channels_empty': not any((state / 'execution').iterdir()),
}
for identifier in identifiers:
    label = 'label=tech.p2enjoy.serverless.function=' + identifier
    physical['containers_absent_' + identifier] = not run('ps', '-aq', '--filter', label)
    physical['networks_absent_' + identifier] = not run('network', 'ls', '-q', '--filter', label)
physical['global_validators_absent'] = not run('ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.installation=' + installation, '--filter', 'label=tech.p2enjoy.serverless.kind=validation')
assert all(physical.values()), 'physical_cleanup_incomplete'
result['physical'] = physical
result['artifact_ids'] = sorted(artifact_ids)
result['instance_ids'] = sorted(instance_ids)
program = '''import json,os,sqlite3,sys
from contextlib import closing
from app.config import Vault
ids=json.load(sys.stdin);vault=Vault(os.environ['SERVERLESS_MASTER_KEY']);result=[]
with closing(sqlite3.connect('file:/state/control.sqlite3?mode=ro',uri=True)) as db:
 for identifier in ids:
  row=db.execute('SELECT secrets_cipher FROM functions WHERE id=?',(identifier,)).fetchone()
  assert row is not None,'campaign_function_missing'
  result.append({'function_id':identifier,'secrets_empty':vault.open(row[0])=={}})
print(json.dumps(result))
'''
secrets = json.loads(run('exec', '-i', 'serverless-api', 'python', '-B', '-c', program, input=json.dumps(identifiers)))
assert {row['function_id'] for row in secrets} == set(identifiers) and all(row['secrets_empty'] for row in secrets), 'persisted_secrets_not_empty'
result['secrets'] = secrets
result['control_image'] = run('inspect', '--format', '{{.Image}}', 'serverless-api')
result['completed'] = True
print(json.dumps(result))
