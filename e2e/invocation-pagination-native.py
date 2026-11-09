# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
"""Read-only native correlation on the authorized SPARK, as control DB owner.

All helpers share the contract above. Only root's serial proof invokes this
collector; stdin lists exact campaign identities and invocation receipts.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from uuid import UUID
from control_database import read_control, control_owner


def main():
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
    payload = json.load(sys.stdin)
    assert set(payload) == {'reports'} and len(payload['reports']) <= 2
    settings = {}
    for line in Path('/etc/spark/env').read_text().splitlines():
        fields = shlex.split(line, comments=True)
        if len(fields) == 1 and '=' in fields[0]:
            key, value = fields[0].split('=', 1)
            if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_DOCKER_SOCKET_HOST'):
                settings[key] = value
    state = Path(settings['SERVERLESS_STATE_HOST_PATH'])
    control = state / 'control.sqlite3'
    docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]

    def command(args):
        return subprocess.check_output(args, text=True, timeout=30)

    result = {'observed_at_ns': str(time.time_ns()), 'owned_functions': [], 'invocations': []}
    with read_control(control) as db:
        db.execute('BEGIN')
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        result['migrations'] = [r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
        assert len(result['migrations']) == 8
        result['global_counts'] = {name: db.execute(sql).fetchone()[0] for name, sql in {
            'active_functions': 'SELECT count(*) FROM functions WHERE deleted_at IS NULL',
            'instances': 'SELECT count(*) FROM execution_instances',
            'active_invocations': "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
            'active_deployments': "SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
            'operations': 'SELECT count(*) FROM function_operations',
            'reserved_bytes': 'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
        assert not any(result['global_counts'].values())
        installation = db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
        for report in payload['reports']:
            assert report['completed'] and report['cleanup'] and report['prefix'].startswith('invocation-pagination-')
            assert len(report['function_ids']) == 1
            function = report['function_ids'][0]
            for identifier in (function, report['namespace_id'], report['service_id']):
                assert str(UUID(identifier)) == identifier
            row = db.execute('''SELECT f.id,f.deleted_at,f.purged_at,f.active_revision_id,n.name,
                s.deleted_at AS service_deleted,n.deleted_at AS namespace_deleted FROM functions f
                JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id
                WHERE f.id=? AND s.id=? AND n.id=?''', (function, report['service_id'], report['namespace_id'])).fetchone()
            assert row and row['name'] == report['prefix']
            assert row['deleted_at'] and row['purged_at'] and row['active_revision_id'] is None
            assert row['service_deleted'] and row['namespace_deleted']
            revisions = [dict(r) for r in db.execute('SELECT id,code_hash,stored_bytes,deleted_at FROM revisions WHERE function_id=?', (function,))]
            candidates = [dict(r) for r in db.execute('SELECT id,state,reserved_bytes,validation_json FROM deployments WHERE function_id=?', (function,))]
            assert all(r['deleted_at'] and r['stored_bytes'] == 0 for r in revisions)
            assert all(r['state'] in ('published', 'failed', 'expired') and r['reserved_bytes'] == 0 and r['validation_json'] is None for r in candidates)
            assert not db.execute("SELECT 1 FROM function_versions WHERE function_id=? AND state!='deleted'", (function,)).fetchone()
            assert not db.execute('SELECT 1 FROM service_tokens WHERE service_id=? AND revoked_at IS NULL', (report['service_id'],)).fetchone()
            for identifier in {r['id'] for r in revisions + candidates}:
                assert not (state / 'artifacts' / identifier).exists()
            result['owned_functions'].append({**dict(row), 'revisions': len(revisions), 'candidates': len(candidates), 'artifact_paths_absent': True, 'tokens_revoked': True})
            calls = [v for v in report['evidence'] if 'invocation_id' in v]
            expected_ids = []
            for call in calls:
                invocation = db.execute('''SELECT id,state,handler_started,requested_code_hash,resolved_code_hash
                    FROM invocations WHERE id=? AND function_id=?''', (call['invocation_id'], function)).fetchone()
                assert invocation and invocation['state'] == 'succeeded' and invocation['handler_started']
                assert invocation['resolved_code_hash'] == call['code_hash']
                assert invocation['requested_code_hash'] == (call['code_hash'] if '@' in call['invoked_url'] else None)
                expected_ids.append(invocation['id']); result['invocations'].append(dict(invocation))
            actual_ids = [r[0] for r in db.execute('SELECT id FROM invocations WHERE function_id=?', (function,))]
            assert sorted(actual_ids) == sorted(expected_ids), 'unaccounted_campaign_invocation'
    result['validation_containers'] = command(docker + ['ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.installation=' + installation,
                                             '--filter', 'label=tech.p2enjoy.serverless.kind=validation']).split()
    assert not result['validation_containers']
    result['validation_channels'] = [p.name for p in (state / 'validation').iterdir()]
    assert not result['validation_channels']
    containers = json.loads(command(docker + ['inspect', 'serverless-api', 'serverless-runtime-reference']))
    result['containers'] = {r['Name'].lstrip('/'): {'id': r['Id'], 'image': r['Image'], 'started_at': r['State']['StartedAt'],
                           'health': r['State'].get('Health', {}).get('Status')} for r in containers}
    assert all(v['health'] == 'healthy' for v in result['containers'].values())
    result['official_sha256'] = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ['/etc/spark/env', '/run/spark/secrets']}
    files = sorted(['function_code_hash.py'] + [str(p.relative_to('/srv/p2enjoy-serverless/control')) for p in Path('/srv/p2enjoy-serverless/control/app').glob('*.py')]
                   + [str(p.relative_to('/srv/p2enjoy-serverless/control')) for p in Path('/srv/p2enjoy-serverless/control/migrations').glob('*.sql')])
    script = 'import hashlib,json;from pathlib import Path;names=' + repr(files) + ";print(json.dumps({n:hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest() for n in names}))"
    result['embedded_sha256'] = json.loads(command(docker + ['exec', 'serverless-api', 'python', '-B', '-c', script]))
    with control_owner(control), closing(sqlite3.connect('file:' + str(Path(settings['SERVERLESS_STORAGE_ROOT_HOST']) / 'registry.sqlite3') + '?mode=ro', uri=True)) as db:
        result['storage_counts'] = {name: db.execute(sql).fetchone()[0] for name, sql in {
            'leases': 'SELECT count(*) FROM leases', 'probes': 'SELECT count(*) FROM probes',
            'pending': 'SELECT count(*) FROM functions WHERE pending_json IS NOT NULL',
            'mounted': "SELECT count(*) FROM volumes WHERE phase!='unmounted'"}.items()}
        assert not any(result['storage_counts'].values())
    if payload['reports']:
        campaigns = {report['namespace_id']: report['function_ids'] for report in payload['reports']}
        physical = json.loads(command([sys.executable, '-B', '/srv/p2enjoy-serverless/e2e/storage-console-inspect.py', json.dumps(campaigns)]))
        assert physical['completed'] and all(physical['physical'].values())
        for report in payload['reports']:
            purge = next(row['purged'] for row in report['evidence'] if 'purged' in row)
            assert physical['functions'][purge['function_id']]['operation_id'] == purge['operation_id']
        result['physical_cleanup'] = physical
    print(json.dumps(result))


if __name__ == '__main__':
    main()
