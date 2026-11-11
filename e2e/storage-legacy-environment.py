# @spec docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md
# @verifies docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#fenêtre-et-conservation-des-données
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#preuves-à-terminer
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#matrice-réelle
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UNKNOWN_FIRST.md#matrice-publique-et-marqueurs
# @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#installation-temporaire-réelle
# @verifies docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#scénarios-requis
"""DEV-only isolated installations with an independent identity-based restore."""
from contextlib import closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import select
import shlex
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import time
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control_database import control_owner

BASE = Path('/srv/p2enjoy-serverless')
HISTORY = BASE / 'qualification-history'
AGENT = 'p2enjoy-storage-dev.service'
TEMP = 'serverless-api-archive-migration'
OFFICIAL = ['/etc/spark/env', '/run/spark/secrets', '/etc/spark/routes']
LOCK = None
LOCK_PATH = Path('/run/serverless-archive-migration.lock')
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
SCHEMA_006 = ['001_control.sql', '002_login_limits.sql', '003_deployments.sql',
              '004_function_operations.sql', '005_execution.sql', '006_storage_commands.sql']
SCHEMA_007 = SCHEMA_006 + ['007_function_code_hash.sql']
SCHEMA_008 = SCHEMA_007 + ['008_function_versions.sql']
SCHEMA_006_REVISION = 'f56d79ebe3d1d84731bfd262d1e6a9d5b5a680c0'


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, allowed=(0,), *, combined_output=False):
    # The native timeout and inherited flock survive a killed Python/SSH driver.
    result = subprocess.run(['timeout', '--signal=KILL', '40s', *args],
                            capture_output=True, text=True, timeout=45,
                            cwd=BASE,
                            pass_fds=() if LOCK is None else (LOCK,))
    assert result.returncode in allowed, 'bounded_operator_command_failed: ' + args[0]
    return (result.stdout + result.stderr if combined_output else result.stdout).strip()


def atomic(path, value):
    temporary = path.with_suffix('.pending')
    with open(temporary, 'w', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def identity(path):
    info = Path(path).lstat()
    assert stat.S_ISDIR(info.st_mode), 'directory_required'
    return {'device': info.st_dev, 'inode': info.st_ino, 'uid': info.st_uid,
            'gid': info.st_gid, 'mode': stat.S_IMODE(info.st_mode)}


def same(path, expected):
    return Path(path).exists() and identity(path) == expected


def hashes():
    return {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in OFFICIAL}


def temporary_control_name(item):
    if item.get('mode') == 'instance-limit':return 'serverless-api-instance-limit'
    return 'serverless-api-code-history' if item.get('mode')=='function-version-unknown-first' else TEMP


def docker(item, *args):
    return command(item['docker'] + list(args))


def container(item, name):
    rows = json.loads(docker(item, 'inspect', name))
    assert len(rows) == 1
    row = rows[0]
    return {'id': row['Id'], 'image': row['Image'], 'running': row['State']['Running'],
            'status': row['State'].get('Health', {}).get('Status'),
            'started_at': row['State']['StartedAt']}


def rows(item, path, query, args=()):
    with control_owner(Path(item['paths']['state']) / 'control.sqlite3'):
        with closing(sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True, timeout=2)) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(query, args)]


def database_snapshot(item, name, backup=None):
    path = Path(item['paths'][name]) / ('control.sqlite3' if name == 'state' else 'registry.sqlite3')
    with control_owner(Path(item['paths']['state']) / 'control.sqlite3'):
        with closing(sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True, timeout=2)) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            tables = {}
            for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                assert re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*', table)
                records = [json.dumps(list(row), sort_keys=True, default=lambda b: b.hex())
                           for row in db.execute('SELECT * FROM ' + table)]
                tables[table] = {'rows': len(records), 'sha256': hashlib.sha256(
                    json.dumps(sorted(records)).encode()).hexdigest()}
            if backup is not None:
                assert not backup.exists()
                with closing(sqlite3.connect(backup)) as target:
                    db.backup(target)
                    assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                os.chmod(backup, 0o600)
    return tables


def artifacts(item):
    root = Path(item['paths']['state']) / 'artifacts'
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*')) if path.is_file()}


def no_references(item, allow_original=False):
    paths = list(item['paths'].values())
    registry = Path(item['paths']['storage']) / 'registry.sqlite3'
    if registry.exists():
        tables = {row['name'] for row in rows(item, registry, "SELECT name FROM sqlite_master WHERE type='table'")}
        if same(item['paths']['storage'], item['original_dirs']['storage']):
            assert {'leases', 'probes', 'volumes', 'functions'} <= tables, 'original_registry_schema_changed'
        else:
            assert same(item['paths']['storage'], item['replacement_dirs']['storage']), 'unknown_registry_directory'
        for table, query in [('leases', 'SELECT 1 FROM leases'), ('probes', 'SELECT 1 FROM probes'),
                             ('volumes', "SELECT 1 FROM volumes WHERE phase!='unmounted'"),
                             ('functions', 'SELECT 1 FROM functions WHERE pending_json IS NOT NULL')]:
            if table in tables:
                assert not rows(item, registry, query), 'storage_reference_retained'
    ids = docker(item, 'ps', '-q').split()
    if ids:
        for row in json.loads(docker(item, 'inspect', *ids)):
            if allow_original and row['Id'] == item['original']['id']:
                continue
            for mount in row['Mounts']:
                source = mount.get('Source', '')
                assert not any(source == p or source.startswith(p + '/') for p in paths), 'consumer_container_retained'
    # Inspect all visible mount namespaces, including the rootless daemon's.
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal():
            continue
        try:
            mountinfo = (proc / 'mountinfo').read_text()
            arguments = (proc / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        for line in mountinfo.splitlines():
            left, right = line.split(' - ', 1)
            if right.split()[0].startswith('fuse'):
                assert not any(p in left for p in paths), 'fuse_mount_retained'
        if b'--probe' in arguments or b'-backing' in arguments:
            assert not any(arg.decode(errors='replace').startswith(p + '/') for arg in arguments for p in paths), 'volume_process_retained'


def quiet_control(item):
    path = Path(item['paths']['state']) / 'control.sqlite3'
    for query in ["SELECT 1 FROM functions WHERE deleted_at IS NULL",
                  "SELECT 1 FROM deployments WHERE state IN ('prepared','receiving','validating')",
                  'SELECT 1 FROM function_operations', 'SELECT 1 FROM execution_instances',
                  "SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')"]:
        assert not rows(item, path, query), 'active_control_resource'


def agent_call(item, value):
    with control_owner(Path(item['paths']['state']) / 'control.sqlite3'):
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(15)
            client.connect(str(Path(item['paths']['channel']) / 'agent.sock'))
            client.sendall(json.dumps(value).encode() + b'\n')
            data = b''
            while not data.endswith(b'\n'):
                part = client.recv(65536)
                assert part and len(data) + len(part) <= 65536
                data += part
    result = json.loads(data)
    assert result['ok'], 'agent_request_failed'
    return result['result']


def agent_ready(item):
    try:
        return agent_call(item, {'op': 'health'})['healthy']
    except (ConnectionRefusedError, FileNotFoundError, TimeoutError, ConnectionResetError):
        return False


def until(action, message, seconds=90):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = action()
        if value:
            return value
        time.sleep(.25)
    raise AssertionError(message)


def alive(item):
    try:
        text = Path('/proc', str(item['driver_pid']), 'stat').read_text().rsplit(')', 1)[1].split()
        return text[19] == item['driver_birth'] and text[0] != 'Z'
    except FileNotFoundError:
        return False


def restore(item, journal, independent):
    if item.get('restored'):
        emit(item['restoration'])
        return item['restoration']
    if not item.get('originals_verified'):
        original = container(item, item['original']['id'])
        assert original['image'] == item['original']['image']
        if original['running']:
            docker(item, 'stop', '--time', '15', item['original']['id'])
        assert not container(item, item['original']['id'])['running']
        # Remove only this campaign's temporary container; original ID remains intact.
        candidates = docker(item, 'ps', '-aq', '--filter', 'name=^/' + temporary_control_name(item) + '$').split()
        if candidates:
            assert len(candidates) == 1
            definition = json.loads(docker(item, 'inspect', candidates[0]))[0]
            assert definition['Config']['Labels']['com.docker.compose.project'] == item['project']
            # @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#perte-avec-consommateur-et-raccordement--réalisation
            if (item.get('mode') == 'instance-limit' and item.get('temporary_installation')
                    and definition['State']['Running'] and 'before_consumer_cleanup' not in item):
                try:
                    item['before_consumer_cleanup'] = instance_limit_observation(item)
                    item['before_consumer_cleanup']['sampled_at'] = time.time()
                except InstanceLimitObservationUnavailable as error:
                    # Ownership refusals are never optional diagnostics.
                    item['consumer_cleanup_observation_error'] = {'type':str(error)}
                atomic(journal,item)
            docker(item, 'rm', '-f', candidates[0])
        if item.get('mode') in ('function-version-unknown-first','instance-limit'):cleanup_history_consumers(item,journal)
        command(['systemctl', 'stop', AGENT])
        assert command(['systemctl', 'is-active', AGENT], (0, 3)) == 'inactive'
        # Recover temporary installation identity even if the driver died before recording it.
        state = Path(item['paths']['state'])
        if state.exists() and not same(state, item['original_dirs']['state']) and (state / 'control.sqlite3').exists():
            tables = rows(item, state / 'control.sqlite3', "SELECT name FROM sqlite_master WHERE name='security_metadata'")
            installation = rows(item, state / 'control.sqlite3', "SELECT value FROM security_metadata WHERE name='installation-id'") if tables else []
            if installation:
                identifier = installation[0]['value']
                assert str(UUID(identifier)) == identifier and identifier != item['installation']
                owned = docker(item, 'ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.installation=' + identifier).split()
                for identifier in owned:
                    definition = json.loads(docker(item, 'inspect', identifier))[0]
                    assert definition['Config']['Labels'].get('tech.p2enjoy.serverless.kind') == 'validation'
                    docker(item, 'rm', '-f', identifier)
        # During a partial swap state may be absent, so registry reads use the preserved owner.
        owner = state / 'control.sqlite3'
        if not owner.exists():
            saved_state = Path(item['work']) / 'original-state'
            assert same(saved_state, item['original_dirs']['state'])
            temporary = dict(item, paths=dict(item['paths'], state=str(saved_state)))
            no_references(temporary)
        else:
            no_references(item)
        for key, official in item['paths'].items():
            path, original = Path(official), Path(item['work']) / ('original-' + key)
            expected = item['original_dirs'][key]
            if same(path, expected):
                assert not original.exists(), 'duplicate_original_directory'
                continue
            assert same(original, expected), 'original_directory_identity_missing'
            if path.exists():
                assert same(path, item.get('replacement_dirs', {}).get(key, {})), 'unknown_replacement_directory'
                discarded = Path(item['work']) / ('discarded-' + key)
                assert not discarded.exists(), 'discarded_directory_already_exists'
                os.rename(path, discarded)
            os.rename(original, path)
            assert same(path, expected)
            atomic(journal, item)
        if 'baseline' in item:
            assert database_snapshot(item, 'state') == item['baseline']['state'], 'control_rows_changed'
            assert database_snapshot(item, 'storage') == item['baseline']['storage'], 'storage_rows_changed'
            assert artifacts(item) == item['baseline']['artifacts'], 'original_artifacts_changed'
        assert hashes() == item['configuration'], 'official_configuration_changed'
        item['originals_verified'] = True
        atomic(journal, item)
    assert all(same(path, item['original_dirs'][key]) for key, path in item['paths'].items())
    assert hashes() == item['configuration'], 'official_configuration_changed'
    if item.get('mode') == 'instance-limit':
        proposal=Path('/etc/spark/env.?')
        assert (hashlib.sha256(proposal.read_bytes()).hexdigest() if proposal.exists() else None) == item['proposal_sha256'], 'official_proposal_changed'
    command(['systemctl', 'start', AGENT])
    assert command(['systemctl', 'is-active', AGENT]) == 'active'
    until(lambda: agent_ready(item), 'restored_agent_unhealthy')
    docker(item, 'start', item['original']['id'])
    current = until(lambda: (value if (value := container(item, item['original']['id']))['status'] == 'healthy' else None), 'restored_control_unhealthy')
    assert current['image'] == item['original']['image']
    reference = container(item, 'serverless-runtime-reference')
    assert reference == item['reference'], 'reference_executor_changed'
    for key in item['paths']:
        discarded = Path(item['work']) / ('discarded-' + key)
        if discarded.exists():
            assert same(discarded, item['replacement_dirs'][key]), 'discarded_identity_changed'
            assert not same(discarded, item['original_dirs'][key]), 'refusing_original_cleanup'
            shutil.rmtree(discarded)
        unused = Path(item['work']) / ('replacement-' + key)
        if unused.exists():
            if key in item.get('replacement_dirs', {}):
                assert same(unused, item['replacement_dirs'][key]), 'unused_replacement_identity_changed'
            else:
                assert item.get('creating_replacement') == key, 'unplanned_replacement'
                info = identity(unused)
                assert info['device'] == item['original_dirs'][key]['device'] and info['mode'] == 0o700
                assert (info['uid'], info['gid']) in ((0, 0), (item['uid'], item['gid']))
            unused.rmdir()
    command(['systemctl', 'stop', item['unit'] + '.timer'])
    result = {'event': 'restored', 'independent': independent, 'original_id': current['id'],
              'image': current['image'], 'directories_identical': True, 'databases_identical': 'baseline' in item,
              'artifacts_identical': 'baseline' in item, 'configuration_unchanged': True,
              'agent_healthy': True, 'control_healthy': True, 'reference_unchanged': True,
              'temporary_directories_removed': True}
    item.update(restored=True, restoration=result)
    atomic(journal, item)
    emit(result)
    return result


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
def anonymous_api_readable(item):
    program = '''import json,urllib.request,urllib.error
request=urllib.request.Request('http://127.0.0.1:18090/api/session',headers={'Host':'serverless.lelabs.tech'})
try:
 with urllib.request.urlopen(request,timeout=2) as response:
  available=response.status==200 and json.load(response).get('authenticated') is False
except (OSError,ValueError,urllib.error.URLError):available=False
print(json.dumps({'available':available}))
'''
    result = command(item['docker'] + ['exec', temporary_control_name(item), 'python', '-B', '-c', program], (0, 1))
    return bool(result and json.loads(result)['available'])


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
def start_control(item, journal, image, *, readiness='healthy'):
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', image)
    assert readiness in ('healthy', 'anonymous-api', 'migration-refusal')
    if readiness != 'healthy':assert item.get('mode') == 'function-version-purge'
    assert not item.get('restored')
    assert all(not same(path, item['original_dirs'][key]) for key, path in item['paths'].items())
    source = (BASE / 'control/compose.spark.yml').read_text()
    assert 'name: p2enjoy-serverless-dev\n' in source and '    container_name: serverless-api\n' in source
    source = source.replace('name: p2enjoy-serverless-dev\n', 'name: ' + item['project'] + '\n')
    source = source.replace('    container_name: serverless-api\n', '    container_name: ' + temporary_control_name(item) + '\n')
    source = source.replace('    image: p2enjoy-control:dev\n', '    image: ' + image + '\n')
    source = source.replace('    build:\n      context: ..\n      dockerfile: control/Dockerfile\n', '')
    source = source.replace('    restart: unless-stopped\n', '    restart: "no"\n')
    # @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#installation-temporaire-réelle
    if item.get('mode') == 'instance-limit':
        assert image == item['original']['image'], 'same_served_image_required'
        assert source.count('    network_mode: host\n') == 1 and '    environment:' not in source
        source = source.replace('    network_mode: host\n',
            '    environment:\n      SERVERLESS_FUNCTION_INSTANCE_LIMIT: "2"\n    network_mode: host\n')
    compose = Path(item['work']) / 'compose.yml'
    compose.write_text(source)
    os.chmod(compose, 0o640)
    os.chown(compose, 0, item['gid'])
    docker(item, 'compose', '--env-file', '/etc/spark/env', '--env-file', '/run/spark/secrets',
           '-f', str(compose), 'up', '-d', '--no-build')
    if readiness == 'migration-refusal':
        def exited():
            state = json.loads(docker(item, 'inspect', '--format', '{{json .State}}', temporary_control_name(item)))
            return state if state['Status'] == 'exited' else None
        state = until(exited, 'migration_refusal_missing', 30)
        assert state['ExitCode'] != 0, 'migration_refusal_exit_required'
        current = container(item,temporary_control_name(item))
        assert current['image'] == image and not current['running'] and current['id'] != item['original']['id']
        identifier = rows(item,Path(item['paths']['state']) / 'control.sqlite3',"SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
        assert identifier == item['temporary_installation'] and identifier != item['installation']
        logs = command(item['docker'] + ['logs', temporary_control_name(item)], combined_output=True)
        assert 'user-defined function raised exception' in logs and 'Application startup complete.' not in logs
        return {'container': current, 'installation_id':identifier, 'migration_refused': True, 'exit_code': state['ExitCode'],
                'udf_error_seen': True, 'log_sha256': hashlib.sha256(logs.encode()).hexdigest()}
    def ready():
        value = container(item, temporary_control_name(item))
        assert value['running'], 'temporary_control_exited_before_readiness'
        if readiness == 'healthy':return value if value['status'] == 'healthy' else None
        return value if anonymous_api_readable(item) else None
    current = until(ready, 'temporary_control_unavailable')
    assert current['image'] == image
    identifier = rows(item, Path(item['paths']['state']) / 'control.sqlite3', "SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
    assert str(UUID(identifier)) == identifier and identifier != item['installation']
    if item.get('temporary_installation'):assert identifier == item['temporary_installation'], 'temporary_installation_changed'
    item['temporary_installation'] = identifier
    atomic(journal, item)
    return current


def inspect_function(item, function):
    assert str(UUID(function)) == function
    control = Path(item['paths']['state']) / 'control.sqlite3'
    registry = Path(item['paths']['storage']) / 'registry.sqlite3'
    owner = rows(item, control, '''SELECT n.name FROM functions f JOIN services s ON s.id=f.service_id
                 JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=?''', (function,))
    assert owner == [{'name': item.get('namespace_name', 'legacy-' + item['campaign'][:8])}], 'foreign_function'
    versions = [row['version'] for row in rows(item, control, 'SELECT version FROM schema_migrations ORDER BY version')]
    new = '006_storage_commands.sql' in versions
    revisions = rows(item, control, 'SELECT id,stored_bytes,deleted_at FROM revisions WHERE function_id=?', (function,))
    return {'versions': versions, 'revisions': revisions,
            'artifacts': {row['id']: (Path(item['paths']['state']) / 'artifacts' / row['id']).exists() for row in revisions},
            'agent': rows(item, registry, 'SELECT state,version,pending_json FROM functions WHERE id=?', (function,)),
            'agent_receipts': rows(item, registry, 'SELECT operation_id,kind,expected_version,version FROM discard_receipts WHERE function_id=?', (function,)),
            'commands': rows(item, control, 'SELECT id,state,phase,storage_absent,result_version,error_code FROM storage_commands WHERE function_id=?', (function,)) if new else [],
            'guards': rows(item, control, 'SELECT id,decision FROM function_operations WHERE function_id=?', (function,)) if new else [],
            'reserved_bytes': rows(item, control, 'SELECT coalesce(sum(reserved_bytes),0) AS bytes FROM deployments WHERE function_id=?', (function,))[0]['bytes']}


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
def purge_upgrade_observation(item, function):
    assert item.get('mode') == 'function-version-purge'
    observation = inspect_function(item, function)
    control = Path(item['paths']['state']) / 'control.sqlite3'
    registry = Path(item['paths']['storage']) / 'registry.sqlite3'
    hashed = any(row['name'] == 'code_hash' for row in rows(item, control, 'PRAGMA table_info(revisions)'))
    versioned = observation['versions'] == SCHEMA_008
    observation['function'] = rows(item, control, 'SELECT id,service_id,deleted_at,updated_at,active_revision_id'
        + (',first_published_code_hash,first_promoted_at' if versioned else '') + ' FROM functions WHERE id=?', (function,))[0]
    observation['version_registry'] = rows(item,control,'SELECT function_id,code_hash,revision_id,created_at,state,updated_at FROM function_versions WHERE function_id=? ORDER BY code_hash',(function,)) if versioned else None
    revisions = rows(item, control, '''SELECT id,stored_bytes,deleted_at,created_at,inventory_json,events_json,archive_sha256'''
        + (',code_hash' if hashed else '') + ' FROM revisions WHERE function_id=? ORDER BY id', (function,))
    observation['has_code_hash_column'] = hashed
    observation['code'] = [{**{key:row[key] for key in ('id','stored_bytes','deleted_at','created_at','archive_sha256')},
        'empty_inventory':json.loads(row['inventory_json']) == [], 'empty_events':json.loads(row['events_json']) == {},
        'code_hash':row.get('code_hash')} for row in revisions]
    observation['purge_commands'] = rows(item, control, '''SELECT id,function_id,service_id,installation_id,kind,state,phase,
        storage_absent,expected_function_version,result_version,error_code FROM storage_commands
        WHERE function_id=? AND kind='purge' ORDER BY created_at,id''', (function,))
    observation['purge_guards'] = rows(item, control, '''SELECT id,function_id,service_id,kind,decision,storage_version,
        expected_function_version,expected_service_version FROM function_operations WHERE function_id=?''', (function,))
    observation['installation_id'] = rows(item, control, "SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
    observation['agent_volumes'] = rows(item, registry, 'SELECT kind,phase FROM volumes WHERE function_id=? ORDER BY kind', (function,))
    observation['agent_leases'] = rows(item, registry, 'SELECT consumer_id FROM leases WHERE function_id=?', (function,))
    return observation


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#preuves-à-terminer
def stopped_purge_input(item, journal, function, phase):
    assert phase in ('volumes', 'artifacts') and item.get('mode') == 'function-version-purge'
    assert item['denied']['function_id'] == function and not item.get('upgraded')
    before = purge_upgrade_observation(item, function)
    assert before['versions'] == (SCHEMA_007 if item.get('source_schema')=='007' else SCHEMA_006)
    assert before['has_code_hash_column'] == (item.get('source_schema')=='007')
    assert len(before['purge_commands']) == len(before['purge_guards']) == len(before['code']) == 1
    request, guard = before['purge_commands'][0], before['purge_guards'][0]
    assert request['state'] == 'pending' and request['phase'] == phase and request['id'] == guard['id']
    assert guard['decision'] == 'commit' and guard['kind'] == 'purge'
    assert before['function']['deleted_at'] and before['function']['active_revision_id'] is None
    assert before['code'][0]['empty_inventory'] and before['code'][0]['empty_events'] and before['code'][0]['stored_bytes'] > 0
    assert before['artifacts'][before['code'][0]['id']]
    current = container(item, temporary_control_name(item));assert current['image'] == item['historical_image'] and current['running']
    docker(item, 'rm', '-f', temporary_control_name(item))
    stopped = purge_upgrade_observation(item, function)
    assert stopped['purge_commands'][0]['phase'] == phase, 'requested_purge_phase_already_advanced'
    def agent_finished():
        value = purge_upgrade_observation(item, function)
        return value if (len(value['agent']) == 1 and value['agent'][0]['state'] == 'purged' and
            value['agent'][0]['pending_json'] is None and not value['agent_volumes'] and not value['agent_leases']) else None
    drained = until(agent_finished, 'temporary_agent_purge_not_finished')
    assert drained['purge_commands'][0]['phase'] == phase
    no_references(item)
    folder = Path(item['work']) / 'purge-inputs';folder.mkdir(mode=0o700, exist_ok=True);os.chown(folder,item['uid'],item['gid'])
    backup = folder / (phase + '-control.sqlite3')
    tables = database_snapshot(item, 'state', backup)
    result = {'phase':phase,'function_id':function,'observation':drained,'tables':tables,'schema_objects':schema_objects(item),'artifact_sha256':artifacts(item),
              'backup':str(backup),'backup_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'backup_mode':stat.S_IMODE(backup.stat().st_mode)}
    item['purge_input'] = result;atomic(journal,item)
    return result


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#matrice-réelle
def verify_purge_version_migration(item,fixture,after):
    before=fixture['observation'];assert len(before['code'])==len(after['code'])==1
    old,new=before['code'][0],after['code'][0]
    assert new==old,'migration_changed_purge_revision'
    assert after['function']=={**before['function'],'first_published_code_hash':old['code_hash'],'first_promoted_at':old['created_at']}
    assert len(after['purge_commands'])==1
    prior,current=before['purge_commands'][0],after['purge_commands'][0]
    assert {k:v for k,v in current.items() if k not in ('phase','error_code')}=={k:v for k,v in prior.items() if k not in ('phase','error_code')},'purge_command_identity_changed'
    assert (current['phase'],current['error_code'])==(prior['phase'],prior['error_code']) or (prior['phase']=='volumes' and current['phase']=='artifacts' and current['error_code']=='artifact_cleanup_pending')
    assert after['purge_guards']==before['purge_guards'],'purge_guard_changed'
    if old['code_hash'] is None:assert after['version_registry']==[],'invented_unknown_version'
    else:
        assert re.fullmatch(r'[0-9a-f]{64}',old['code_hash'])
        assert after['version_registry']==[{'function_id':fixture['function_id'],'code_hash':old['code_hash'],'revision_id':old['id'],'created_at':old['created_at'],'state':'deleted','updated_at':old['created_at']}]
    control=Path(item['paths']['state'])/'control.sqlite3'
    backup=Path(fixture['backup'])
    with control_owner(control),closing(sqlite3.connect('file:'+str(backup)+'?mode=ro',uri=True)) as historical,closing(sqlite3.connect('file:'+str(control)+'?mode=ro',uri=True)) as migrated:
        preserved=[]
        historical.execute('BEGIN');migrated.execute('BEGIN')
        permitted=[]
        for (table,) in historical.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"):
            if table=='schema_migrations':continue
            assert re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*',table)
            columns=[v[1] for v in historical.execute('PRAGMA table_info('+table+')')]
            projection=','.join(columns);query='SELECT '+projection+' FROM '+table
            previous=[dict(zip(columns,v)) for v in historical.execute(query)]
            actual=[dict(zip(columns,v)) for v in migrated.execute(query)]
            if table in ('storage_commands','function_operations'):
                old_row=[v for v in previous if v['id']==prior['id']];new_row=[v for v in actual if v['id']==prior['id']]
                assert len(old_row)==len(new_row)==1,'correlated_purge_row_missing'
                old_row,new_row=old_row[0],new_row[0]
                allowed=('phase','error_code') if table=='storage_commands' else ('error_code',)
                assert new_row['error_code']==current['error_code'],'purge_diagnostic_changed_during_observation'
                if table=='storage_commands':assert new_row['phase']==current['phase']
                for key in allowed:
                    if new_row[key]!=old_row[key]:
                        assert prior['phase']=='volumes' and current['phase']=='artifacts' and current['error_code']=='artifact_cleanup_pending','unexpected_purge_transition'
                        permitted.append({'table':table,'id':prior['id'],'column':key,'before':old_row[key],'after':new_row[key]})
                        new_row[key]=old_row[key]
            encode=lambda records:sorted(json.dumps(v,sort_keys=True,default=lambda raw:raw.hex()) for v in records)
            assert encode(previous)==encode(actual),'historical_columns_changed:'+table
            preserved.append(table)
    after['old_column_conservation']={'tables':preserved,'source_schema':item['source_schema'],'new_storage_command_phase_observed':current['phase'],'permitted_correlated_changes':permitted}
    deployments=rows(item,control,'SELECT id,revision_id,code_hash,code_only FROM deployments WHERE function_id=?',(fixture['function_id'],))
    assert len(deployments)==1 and deployments[0]['revision_id']==old['id'] and deployments[0]['code_hash']==old['code_hash'] and deployments[0]['code_only']==0


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
def schema_objects(item):
    objects = rows(item,Path(item['paths']['state']) / 'control.sqlite3',
        "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
    return [{key:row[key] for key in ('type','name','tbl_name')} |
            {'sql_sha256':hashlib.sha256((row['sql'] or '').encode()).hexdigest()} for row in objects]


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
def release_purge_artifact(item, journal, function):
    assert item.get('mode') == 'function-version-purge' and item['denied']['function_id'] == function
    assert not item['denied'].get('released')
    observation = purge_upgrade_observation(item,function)
    assert len(observation['purge_commands']) == len(observation['purge_guards']) == 1
    request, guard = observation['purge_commands'][0], observation['purge_guards'][0]
    assert request['state'] == 'pending' and request['phase'] == 'artifacts' and request['id'] == guard['id'] and guard['decision'] == 'commit'
    previous = item['denied']['identity'];path = Path(item['denied']['path'])
    fd = os.open(path,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        current = os.fstat(fd)
        assert (current.st_dev,current.st_ino,current.st_uid,current.st_gid,stat.S_IMODE(current.st_mode)) == (previous['device'],previous['inode'],0,0,0o500)
        os.fchmod(fd,previous['mode'])
        os.fchown(fd,previous['uid'],previous['gid'])
        after = os.fstat(fd)
        assert (after.st_dev,after.st_ino,after.st_uid,after.st_gid,stat.S_IMODE(after.st_mode)) == (previous['device'],previous['inode'],previous['uid'],previous['gid'],previous['mode'])
    finally:os.close(fd)
    item['denied']['released'] = True;atomic(journal,item)
    return {'released':True,'function_id':function,'descriptor_identity_confirmed':True,'owner_changed_last':True}


# @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#scénarios-requis
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UNKNOWN_FIRST.md#restitution-avec-consommateur-vivant
def cleanup_history_consumers(item,journal):
    state=Path(item['paths']['state']);registry=Path(item['paths']['storage'])/'registry.sqlite3'
    if same(state,item['original_dirs']['state']) or not (state/'control.sqlite3').exists():return
    assert same(state,item['replacement_dirs']['state'])
    tables=rows(item,state/'control.sqlite3',"SELECT name FROM sqlite_master WHERE type='table' AND name='security_metadata'")
    ids=rows(item,state/'control.sqlite3',"SELECT value FROM security_metadata WHERE name='installation-id'") if tables else []
    if not ids:
        no_references(item);item['history_cleanup']={'installation_not_created':True,'consumers_absent':True};atomic(journal,item);return
    installation=ids[0]['value'];assert str(UUID(installation))==installation and installation!=item['installation']
    if item.get('temporary_installation'):assert installation==item['temporary_installation']
    if item.get('mode') == 'instance-limit':
        namespaces=rows(item,state/'control.sqlite3','SELECT name FROM namespaces WHERE deleted_at IS NULL')
        assert all(v['name']==item['namespace_name'] for v in namespaces),'foreign_namespace'
    functions={v['id']:v['name'] for v in rows(item,state/'control.sqlite3','''SELECT f.id,f.name FROM functions f
        JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE n.name=?''',(item['namespace_name'],))}
    revisions={v['id']:v for v in rows(item,state/'control.sqlite3','SELECT id,function_id,image_id FROM revisions')}
    candidates={v['id']:v['function_id'] for v in rows(item,state/'control.sqlite3','SELECT id,function_id FROM deployments')}
    expected_runtime=None
    for line in Path('/etc/spark/env').read_text().splitlines():
        fields=shlex.split(line,comments=True)
        if len(fields)==1 and fields[0].startswith('SERVERLESS_RUNTIME_IMAGE='):expected_runtime=fields[0].split('=',1)[1]
    assert expected_runtime and re.fullmatch(r'sha256:[a-f0-9]{64}',expected_runtime)
    owned=docker(item,'ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation).split()
    records=[];consumers=set()
    for identifier in owned:
        value=json.loads(docker(item,'inspect',identifier))[0];labels=value['Config']['Labels'];kind=labels.get('tech.p2enjoy.serverless.kind');mounts={v['Destination']:v['Source'] for v in value['Mounts']}
        assert labels['tech.p2enjoy.serverless.installation']==installation and value['Image']==expected_runtime
        if kind=='instance':
            function,revision,consumer=(labels['tech.p2enjoy.serverless.'+k] for k in ('function','revision','instance'))
            assert function in functions and revision in revisions and revisions[revision]['function_id']==function and value['Image']==revisions[revision]['image_id']
            assert str(UUID(consumer))==consumer and value['Name']=='/serverless-function-'+functions[function]+'-'+UUID(consumer).hex
            assert mounts.get('/code')==str(state/'artifacts'/revision/'code');consumers.add(consumer)
        else:
            assert kind=='validation';code=Path(mounts['/code']);candidate=code.parent.name
            assert candidate in candidates and candidates[candidate] in functions and code==state/'artifacts'/candidate/'code'
            consumer=None
        records.append({'id':value['Id'],'image':value['Image'],'kind':kind,'consumer_id':consumer})
    networks=docker(item,'network','ls','-q','--filter','label=tech.p2enjoy.serverless.installation='+installation,'--filter','label=tech.p2enjoy.serverless.kind=instance-network').split()
    net_records=[]
    for identifier in networks:
        value=json.loads(docker(item,'network','inspect',identifier))[0];labels=value['Labels']
        assert labels['tech.p2enjoy.serverless.installation']==installation and labels['tech.p2enjoy.serverless.kind']=='instance-network'
        assert labels['tech.p2enjoy.serverless.function'] in functions and labels['tech.p2enjoy.serverless.revision'] in revisions
        assert revisions[labels['tech.p2enjoy.serverless.revision']]['function_id']==labels['tech.p2enjoy.serverless.function']
        assert str(UUID(labels['tech.p2enjoy.serverless.instance']))==labels['tech.p2enjoy.serverless.instance']
        net_records.append(value['Id'])
    leases=rows(item,registry,'SELECT consumer_id,installation_id,function_id FROM leases') if registry.exists() else []
    for lease in leases:
        assert lease['installation_id']==installation and lease['function_id'] in functions
        assert str(UUID(lease['consumer_id']))==lease['consumer_id']
        declared=rows(item,state/'control.sqlite3','SELECT id FROM execution_instances WHERE id=? AND function_id=?',(lease['consumer_id'],lease['function_id']))
        assert declared or lease['consumer_id'] in consumers,'unowned_history_lease'
    item['history_cleanup']={'installation_id':installation,'containers':records,'networks':net_records,'leases':leases,'removed_containers':[],'removed_networks':[],'released_consumers':[]}
    atomic(journal,item)
    for value in records:
        docker(item,'rm','-f',value['id']);assert not docker(item,'ps','-aq','--filter','id='+value['id'])
        item['history_cleanup']['removed_containers'].append(value['id']);atomic(journal,item)
    for identifier in net_records:
        value=json.loads(docker(item,'network','inspect',identifier))[0];assert not value['Containers'],'foreign_network_consumer'
        docker(item,'network','rm',identifier);item['history_cleanup']['removed_networks'].append(identifier);atomic(journal,item)
    assert not docker(item,'ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation)
    for lease in leases:
        result=agent_call(item,{'op':'release','consumer_id':lease['consumer_id'],'installation_id':installation});assert result['released']
        assert not rows(item,registry,'SELECT 1 FROM leases WHERE consumer_id=?',(lease['consumer_id'],))
        item['history_cleanup']['released_consumers'].append(lease['consumer_id']);atomic(journal,item)
    assert not rows(item,registry,'SELECT 1 FROM leases') if registry.exists() else True


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UNKNOWN_FIRST.md#matrice-publique-et-marqueurs
def history_observation(item,function):
    assert item.get('mode')=='function-version-unknown-first'
    observed=inspect_function(item,function);control=Path(item['paths']['state'])/'control.sqlite3'
    hashed='007_function_code_hash.sql' in observed['versions'];versioned='008_function_versions.sql' in observed['versions']
    observed['function']=rows(item,control,'SELECT id,service_id,name,active_revision_id,created_at,updated_at,deleted_at,purged_at'+
        (',first_published_code_hash,first_promoted_at' if versioned else '')+' FROM functions WHERE id=?',(function,))[0]
    revisions=rows(item,control,'SELECT id,handler,created_at,deleted_at,stored_bytes,inventory_json,events_json'+(',code_hash' if hashed else '')+' FROM revisions WHERE function_id=? ORDER BY created_at,id',(function,))
    observed['history']=[{**{k:v[k] for k in ('id','handler','created_at','deleted_at','stored_bytes')},'code_hash':v.get('code_hash'),
        'inventory_empty':json.loads(v['inventory_json'])==[],'events_empty':json.loads(v['events_json'])=={},
        'inventory_sha256':hashlib.sha256(v['inventory_json'].encode()).hexdigest(),'events_sha256':hashlib.sha256(v['events_json'].encode()).hexdigest()} for v in revisions]
    observed['version_registry']=rows(item,control,'SELECT * FROM function_versions WHERE function_id=? ORDER BY created_at,code_hash',(function,)) if versioned else None
    observed['invocations']=rows(item,control,'SELECT id,revision_id,instance_id,state,handler_started,error_code,http_status,created_at,dispatched_at'+(',requested_code_hash,resolved_code_hash' if versioned else '')+' FROM invocations WHERE function_id=? ORDER BY created_at,id',(function,))
    observed['instances']=rows(item,control,'SELECT id,function_id,revision_id,state FROM execution_instances WHERE function_id=?',(function,))
    registry=Path(item['paths']['storage'])/'registry.sqlite3';observed['leases']=rows(item,registry,'SELECT consumer_id,installation_id,function_id FROM leases WHERE function_id=?',(function,))
    return observed


def save_history_backup(item,label):
    folder=Path(item['work'])/'history-inputs';folder.mkdir(mode=0o700,exist_ok=True);os.chown(folder,item['uid'],item['gid'])
    path=folder/(label+'-control.sqlite3');tables=database_snapshot(item,'state',path)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tables':tables,'mode':stat.S_IMODE(path.stat().st_mode)}


def compare_history_columns(item,backup,*,edited_revision=None):
    control=Path(item['paths']['state'])/'control.sqlite3'
    with control_owner(control),closing(sqlite3.connect('file:'+backup['path']+'?mode=ro',uri=True)) as old,closing(sqlite3.connect('file:'+str(control)+'?mode=ro',uri=True)) as new:
        old.execute('BEGIN');new.execute('BEGIN');preserved=[]
        for (table,) in old.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"):
            assert re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*',table)
            columns=[v[1] for v in old.execute('PRAGMA table_info('+table+')')];query='SELECT '+','.join(columns)+' FROM '+table
            before=[dict(zip(columns,v)) for v in old.execute(query)];after=[dict(zip(columns,v)) for v in new.execute(query)]
            if table=='schema_migrations':after=[v for v in after if v['version'] in {r['version'] for r in before}]
            if table=='revisions' and edited_revision:
                a=[v for v in before if v['id']==edited_revision];b=[v for v in after if v['id']==edited_revision];assert len(a)==len(b)==1
                assert b[0]['inventory_json']=='[]' and b[0]['events_json']=='{}'
                b[0]['inventory_json']=a[0]['inventory_json'];b[0]['events_json']=a[0]['events_json']
            encode=lambda records:sorted(json.dumps(v,sort_keys=True,default=lambda raw:raw.hex()) for v in records)
            assert encode(before)==encode(after),'history_columns_changed:'+table;preserved.append(table)
        return preserved


def prepare_history007(item,journal,request):
    assert not item.get('history_stage')
    function=request['function_id'];variant=request['variant'];assert variant in ('preserved-first','unknown-first-tombstone')
    before=history_observation(item,function);assert before['versions']==SCHEMA_006 and len(before['history'])==2 and not before['instances'] and not before['leases']
    first,later=before['history'];assert first['deleted_at'] and first['stored_bytes']==0 and not first['inventory_empty'] and not before['artifacts'][first['id']]
    assert before['function']['active_revision_id']==later['id'] and later['deleted_at'] is None and later['stored_bytes']>0
    assert container(item,temporary_control_name(item))['image']==item['historical_image']
    docker(item,'rm','-f',temporary_control_name(item));no_references(item)
    backup=save_history_backup(item,'006-api');control=Path(item['paths']['state'])/'control.sqlite3'
    if variant=='unknown-first-tombstone':
        with control_owner(control),closing(sqlite3.connect('file:'+str(control)+'?mode=rw',uri=True)) as db:
            db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
            assert db.execute("UPDATE revisions SET inventory_json='[]',events_json='{}' WHERE id=? AND function_id=? AND deleted_at IS NOT NULL AND stored_bytes=0",(first['id'],function)).rowcount==1
            db.commit();assert not db.execute('PRAGMA foreign_key_check').fetchall()
    conserved=compare_history_columns(item,backup,edited_revision=first['id'] if variant=='unknown-first-tombstone' else None)
    fixture=save_history_backup(item,'006-prepared');item['history_stage']='007';item['history_input']={'variant':variant,'function_id':function,'before':before,'api_backup':backup,'prepared_backup':fixture,'preserved_tables':conserved};atomic(journal,item)
    current=start_control(item,journal,item['intermediate_image']);after=history_observation(item,function);assert after['versions']==SCHEMA_007
    a,b=after['history'];assert a['code_hash'] is None if variant=='unknown-first-tombstone' else re.fullmatch(r'[a-f0-9]{64}',a['code_hash'])
    assert re.fullmatch(r'[a-f0-9]{64}',b['code_hash']) and after['function']==before['function'] and a['id']==first['id'] and b['id']==later['id']
    return {'container':current,'variant':variant,'input':item['history_input'],'after':after,'prepared_columns_preserved':compare_history_columns(item,fixture)}


def upgrade_history008(item,journal,function):
    assert item.get('history_stage')=='007' and item['history_input']['function_id']==function
    before=history_observation(item,function);assert before['versions']==SCHEMA_007 and not before['instances'] and not before['leases']
    docker(item,'rm','-f',temporary_control_name(item));no_references(item);backup=save_history_backup(item,'007-retained')
    item['history_stage']='008';item['upgraded']=True;atomic(journal,item)
    current=start_control(item,journal,item['original']['image']);after=history_observation(item,function);assert after['versions']==SCHEMA_008
    first=before['history'][0];assert after['function']=={**before['function'],'first_published_code_hash':first['code_hash'],'first_promoted_at':first['created_at']}
    assert after['history']==before['history']
    expected=[v for v in before['history'] if v['code_hash'] is not None];actual=after['version_registry'];assert len(actual)==len(expected)
    for revision in expected:
        match=[v for v in actual if v['code_hash']==revision['code_hash']];assert len(match)==1
        assert match[0]=={'function_id':function,'code_hash':revision['code_hash'],'revision_id':revision['id'],'created_at':revision['created_at'],'state':'deleted' if revision['deleted_at'] else 'available','updated_at':revision['created_at']}
    hashes={v['id']:v['code_hash'] for v in before['history']}
    for call in after['invocations']:assert call['requested_code_hash'] is None and call['resolved_code_hash']==hashes[call['revision_id']]
    return {'container':current,'before':before,'after':after,'input007':backup,'preserved_tables':compare_history_columns(item,backup)}



# @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#refus-dappartenance-obligatoire
class InstanceLimitObservationUnavailable(RuntimeError):
    """A technical exec failure, never a failed ownership precondition."""


# @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#scénarios-requis
def instance_limit_observation(item):
    """Read the real consumed budgets, database and native Docker identities only."""
    assert item.get('mode') == 'instance-limit' and not item.get('restored')
    current=container(item,temporary_control_name(item))
    assert current['image']==item['original']['image'] and current['running']
    assert not container(item,item['original']['id'])['running']
    assert all(same(path,item['replacement_dirs'][key]) for key,path in item['paths'].items())
    assert hashes()==item['configuration'],'official_configuration_changed'
    control=Path(item['paths']['state'])/'control.sqlite3'
    namespace=rows(item,control,'SELECT id,name FROM namespaces WHERE deleted_at IS NULL')
    assert all(v['name']==item['namespace_name'] for v in namespace),'foreign_namespace'
    keys=('SERVERLESS_FUNCTION_INSTANCE_LIMIT','SERVERLESS_FUNCTION_CPU_BUDGET','SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB')
    program='import os,json;print(json.dumps({k:os.environ[k] for k in '+repr(keys)+'}))'
    try:
        budgets=json.loads(docker(item,'exec',temporary_control_name(item),'python','-B','-c',program))
    except (AssertionError,subprocess.SubprocessError,json.JSONDecodeError) as error:
        raise InstanceLimitObservationUnavailable(type(error).__name__) from None
    assert budgets==dict(zip(keys,('2','1','8192'))),'isolated_consumed_budgets_required'
    functions=rows(item,control,'SELECT id,name,deleted_at FROM functions')
    instances=rows(item,control,'SELECT id,function_id,revision_id,state,cpu_nanos,memory_mib FROM execution_instances ORDER BY id')
    invocations=rows(item,control,'SELECT id,function_id,state,trigger,error_code,handler_started,instance_id,completed_at FROM invocations ORDER BY id')
    firings=rows(item,control,'SELECT id,function_id,state,error_code,invocation_id,window_at FROM schedule_firings ORDER BY id')
    identifiers=docker(item,'ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+item['temporary_installation']).split()
    definitions=json.loads(docker(item,'inspect',*identifiers)) if identifiers else []
    containers=[{'id':v['Id'],'image':v['Image'],'running':v['State']['Running'],
        'kind':v['Config']['Labels'].get('tech.p2enjoy.serverless.kind'),
        'instance_id':v['Config']['Labels'].get('tech.p2enjoy.serverless.instance'),
        'cpu_nanos':v['HostConfig']['NanoCpus'],'memory_bytes':v['HostConfig']['Memory']} for v in definitions]
    return {'budgets':budgets,'container':current,'installation_id':item['temporary_installation'],
        'functions':functions,'instances':instances,'invocations':invocations,'firings':firings,
        'containers':containers,'official_configuration_unchanged':True,'original_control_stopped':True}


def main():
    global LOCK
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    mode, campaign = sys.argv[1:3]
    assert str(UUID(campaign)) == campaign
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
    candidates = [HISTORY / (prefix + campaign) for prefix in ('storage-absence-', 'function-version-purge-', 'function-version-unknown-first-', 'instance-limit-')]
    if mode in ('restore', 'status', 'signal-driver'):
        existing = [path for path in candidates if (path / 'restore.json').exists()]
        assert len(existing) <= 1, 'ambiguous_campaign_window'
        work = existing[0] if existing else candidates[0]
    else:work = candidates[3] if mode=='instance-limit' else candidates[2] if mode=='function-version-unknown-first' else candidates[1] if mode == 'function-version-purge' else candidates[0]
    journal = work / 'restore.json'
    if mode in ('restore', 'status', 'signal-driver'):
        if mode == 'status' and not journal.exists():
            emit({'restored': False, 'not_started': True, 'campaign': campaign})
            return
        item = json.loads(journal.read_text())
        assert item['campaign'] == campaign and item['work'] == str(work)
        if mode == 'status':
            emit({'restored': item.get('restored', False), 'restoration': item.get('restoration'),
                  'driver_alive': alive(item), 'unit': item['unit'],
                  'timer_state':command(['systemctl','is-active',item['unit'] + '.timer'],(0,3,4)),
                  'service_state':command(['systemctl','is-active',item['unit'] + '.service'],(0,3,4)),
                  **({'before_consumer_cleanup':item.get('before_consumer_cleanup'),
                      'consumer_cleanup':item.get('history_cleanup'),
                      'observation_error':item.get('consumer_cleanup_observation_error'),
                      'before_observer_fault':item.get('before_observer_fault')} if item.get('mode')=='instance-limit' else {})})
            return
        if mode == 'signal-driver':
            assert item.get('mode') == 'instance-limit' and len(sys.argv) == 4
            requested={'SIGTERM':signal.SIGTERM,'SIGKILL':signal.SIGKILL}[sys.argv[3]]
            assert alive(item),'driver_must_be_alive'
            fd=os.pidfd_open(item['driver_pid'])
            try:
                assert alive(item),'driver_identity_changed'
                signal.pidfd_send_signal(fd,requested)
                assert select.select([fd],[],[],10)[0],'driver_not_terminated'
            finally:os.close(fd)
            emit({'event':'driver-signalled','signal':int(requested),'driver_dead':not alive(item)})
            return
        if alive(item):
            fd = os.pidfd_open(item['driver_pid'])
            try:
                assert alive(item)
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert select.select([fd], [], [], 10)[0], 'driver_not_joined'
            finally:
                os.close(fd)
        LOCK = os.open(LOCK_PATH, os.O_RDWR | os.O_NOFOLLOW)
        lock_info = os.fstat(LOCK)
        assert [lock_info.st_dev, lock_info.st_ino] == item['lock_identity'] and lock_info.st_uid == 0
        until(lambda: lock_available(LOCK), 'mutator_not_joined', 45)
        item = json.loads(journal.read_text())
        restore(item, journal, True)
        return
    assert mode in ('partial', 'historical', 'function-version-purge','function-version-unknown-first','instance-limit')
    old_image = sys.argv[3]
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', old_image)
    options=sys.argv[4:]
    assert len(options)==len(set(options)) and set(options)<={'--source-schema007','--target-schema008','--guard-seconds=120'}
    assert not options or mode in ('function-version-purge','function-version-unknown-first','instance-limit')
    if mode=='instance-limit':assert set(options)<={'--guard-seconds=120'}
    else:assert '--guard-seconds=120' not in options
    source_schema='007' if '--source-schema007' in options else '006'
    target_schema='008' if '--target-schema008' in options else '007'
    assert source_schema!='007' or target_schema=='008','source007_requires_explicit_target008'
    if mode=='function-version-unknown-first':assert source_schema=='006' and target_schema=='008','unknown_first_requires_006_to008'
    if mode in ('function-version-purge','function-version-unknown-first'):
        attestation = HISTORY / ('function-version-schema'+source_schema+'-image.json');info = attestation.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'protected_historical_attestation_required'
        reference = json.loads(attestation.read_text());assert reference['completed']
        if source_schema=='006':assert reference['revision'] == SCHEMA_006_REVISION
        else:assert reference['schema']=='007' and reference['registry_proof_sha256']==hashlib.sha256((BASE/'docs/evidence/function-version-registry-dev-2026-11-09.json').read_bytes()).hexdigest()
        assert reference['schema_migrations'] == (SCHEMA_007 if source_schema=='007' else SCHEMA_006) and reference['image'] == old_image, 'known_historical_image_required'
    intermediary=None
    if mode=='function-version-unknown-first':
        path=HISTORY/'function-version-schema007-image.json';info=path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022
        intermediary=json.loads(path.read_text());assert intermediary['completed'] and intermediary['schema']=='007' and intermediary['schema_migrations']==SCHEMA_007
        assert intermediary['registry_proof_sha256']==hashlib.sha256((BASE/'docs/evidence/function-version-registry-dev-2026-11-09.json').read_bytes()).hexdigest()
        assert command(['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','image','inspect','--format','{{.Id}}',intermediary['image']])==intermediary['image']
    account = pwd.getpwnam('spark-docker')
    settings = {}
    for line in Path('/etc/spark/env').read_text().splitlines():
        fields = shlex.split(line, comments=True)
        if len(fields) == 1 and '=' in fields[0]:
            name, value = fields[0].split('=', 1)
            if name.startswith('SERVERLESS_'):
                settings[name] = value
    assert settings['SERVERLESS_PUBLIC_URL'] == 'https://serverless.lelabs.tech'
    paths = dict(zip(('state', 'storage', 'channel'), [settings[name] for name in (
        'SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_STORAGE_SOCKET_DIR_HOST')]))
    for path in paths.values():
        assert Path(path).is_absolute() and str(Path(path).resolve()) == path
        assert Path(path).parent == BASE, 'dedicated_official_directory_required'
    assert len(set(paths.values())) == 3
    # Check the actual local image before any stop, guard, backup or directory move.
    image_id = command(['runuser','-u','spark-docker','--','docker','--host',
        'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST'],'image','inspect','--format','{{.Id}}',old_image])
    assert image_id == old_image, 'historical_image_missing'
    HISTORY.mkdir(mode=0o755, exist_ok=True)
    assert HISTORY.resolve() == HISTORY and HISTORY.stat().st_uid == 0
    LOCK = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock_info = os.fstat(LOCK)
    assert stat.S_ISREG(lock_info.st_mode) and lock_info.st_uid == 0 and stat.S_IMODE(lock_info.st_mode) == 0o600
    fcntl.flock(LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for previous in [*HISTORY.glob('storage-absence-*/restore.json'), *HISTORY.glob('function-version-purge-*/restore.json'), *HISTORY.glob('function-version-unknown-first-*/restore.json'), *HISTORY.glob('instance-limit-*/restore.json')]:
        assert json.loads(previous.read_text()).get('restored'), 'previous_window_not_restored'
    work.mkdir(mode=0o750)
    os.chown(work, 0, account.pw_gid)
    originals = {key: identity(path) for key, path in paths.items()}
    assert all(value['device'] == work.stat().st_dev for value in originals.values())
    assert all((value['uid'], value['gid']) == (account.pw_uid, account.pw_gid) and
               value['mode'] in ((0o700, 0o750) if key == 'state' else (0o700,))
               for key, value in originals.items()), 'official_directory_permissions'
    item = {'campaign': campaign, 'work': str(work), 'paths': paths, 'original_dirs': originals,
            'mode':mode, 'historical_image':old_image,'source_schema':source_schema,'target_schema':target_schema,
            'namespace_name':('code-first-unknown-' if mode=='function-version-unknown-first' else 'code-purge-migration-' if mode == 'function-version-purge' else 'legacy-') + campaign[:8],
            'lock_identity': [lock_info.st_dev, lock_info.st_ino],
            'uid': account.pw_uid, 'gid': account.pw_gid, 'configuration': hashes(),
            'docker': ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']],
            'unit': ('serverless-restore-code-history-' if mode=='function-version-unknown-first' else 'serverless-restore-version-purge-' if mode == 'function-version-purge' else 'serverless-restore-archive-migration-') + campaign,
            'project': ('function-version-unknown-first-' if mode=='function-version-unknown-first' else 'function-version-purge-' if mode == 'function-version-purge' else 'archive-migration-') + campaign,
            'driver_pid': os.getpid(), 'driver_birth': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]}
    if mode == 'instance-limit':
        item.update(namespace_name='instance-limit-' + campaign[:8],
            unit='serverless-restore-instance-limit-' + campaign,
            project='instance-limit-' + campaign, source_schema='009', target_schema='009')
    if intermediary:item['intermediate_image']=intermediary['image']
    item['original'] = container(item, 'serverless-api')
    item['reference'] = container(item, 'serverless-runtime-reference')
    assert item['original']['status'] == 'healthy' and item['reference']['running']
    item['installation'] = rows(item, Path(paths['state']) / 'control.sqlite3', "SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
    if mode == 'instance-limit':
        assert old_image == item['original']['image'], 'same_served_image_required'
        assert settings['SERVERLESS_FUNCTION_INSTANCE_LIMIT'] == '32', 'official_limit32_required'
        assert settings['SERVERLESS_FUNCTION_CPU_BUDGET'] == '1'
        assert settings['SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB'] == '8192'
        actual=[v['version'] for v in rows(item,Path(paths['state'])/'control.sqlite3','SELECT version FROM schema_migrations ORDER BY version')]
        assert actual == SCHEMA_008 + ['009_schedules.sql'], 'current_schema009_required'
        proposal=Path('/etc/spark/env.?')
        item['proposal_sha256']=hashlib.sha256(proposal.read_bytes()).hexdigest() if proposal.exists() else None

    if mode in ('function-version-purge','function-version-unknown-first'):
        actual=[v['version'] for v in rows(item,Path(paths['state'])/'control.sqlite3','SELECT version FROM schema_migrations ORDER BY version')]
        assert actual==(SCHEMA_008 if target_schema=='008' else SCHEMA_007),'explicit_target_schema_mismatch'
    quiet_control(item)
    no_references(item, allow_original=True)
    assert agent_call(item, {'op': 'health'})['healthy']
    # Freeze the restoration code and its identity-switching helper for this window.
    for name in ('storage-legacy-environment.py', 'control_database.py'):
        shutil.copyfile(Path(__file__).parent / name, work / name)
        os.chmod(work / name, 0o600)
    atomic(journal, item)
    command(['systemd-run', '--quiet', '--collect', '--unit=' + item['unit'],
             '--on-active=' + ('60s' if mode == 'partial' else '120s' if '--guard-seconds=120' in options else '900s'),
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '/usr/bin/python3', '-B', str(work / 'storage-legacy-environment.py'), 'restore', campaign])
    assert command(['systemctl', 'is-active', item['unit'] + '.timer']) == 'active'
    emit({'event': 'guard-armed', 'unit': item['unit'], 'campaign': campaign,
          'current_image': item['original']['image'], 'original_id':item['original']['id']})
    try:
        docker(item, 'stop', '--time', '15', item['original']['id'])
        assert not container(item, item['original']['id'])['running']
        command(['systemctl', 'stop', AGENT])
        assert command(['systemctl', 'is-active', AGENT], (0, 3)) == 'inactive'
        quiet_control(item)
        no_references(item)
        backups = work / 'backups'
        backups.mkdir(mode=0o700)
        os.chown(backups, account.pw_uid, account.pw_gid)
        item['baseline'] = {key: database_snapshot(item, key, backups / (key + '.sqlite3')) for key in ('state', 'storage')}
        item['baseline']['artifacts'] = artifacts(item)
        atomic(journal, item)
        for key, path in paths.items():
            assert same(path, originals[key]), 'original_identity_changed'
            os.rename(path, work / ('original-' + key))
            atomic(journal, item)
            if mode == 'partial':
                emit({'event': 'first-directory-moved', 'campaign': campaign})
                os.kill(os.getpid(), signal.SIGKILL)
        item['replacement_dirs'] = {}
        for key, path in paths.items():
            item['creating_replacement'] = key
            atomic(journal, item)
            replacement = work / ('replacement-' + key)
            replacement.mkdir(mode=0o700)
            os.chown(replacement, account.pw_uid, account.pw_gid)
            item['replacement_dirs'][key] = identity(replacement)
            item.pop('creating_replacement')
            atomic(journal, item)
            os.rename(replacement, path)
        command(['systemctl', 'start', AGENT])
        current = start_control(item, journal, old_image)
        emit({'event': 'instance-limit-ready' if mode == 'instance-limit' else 'historical-ready',
              'container': current, 'installation_id': item['temporary_installation'],
              **({'capacity': instance_limit_observation(item)} if mode == 'instance-limit' else {})})
        for line in sys.stdin:
            request = json.loads(line)
            op = request['op']
            if op == 'restore':
                break
            if mode == 'instance-limit':assert op in ('capacity','pause-observation'), 'instance_limit_operation_required'
            if op == 'capacity':
                assert mode == 'instance-limit'
                result = instance_limit_observation(item)
            elif op == 'pause-observation':
                assert mode == 'instance-limit' and 'before_observer_fault' not in item
                item['before_observer_fault'] = instance_limit_observation(item)
                item['before_observer_fault']['sampled_at'] = time.time()
                atomic(journal,item)
                target=item['before_observer_fault']['container']['id']
                docker(item,'pause',target)
                paused=json.loads(docker(item,'inspect',target))[0]
                assert paused['Id']==target and paused['State']['Paused']
                result={'paused':True,'id':target,'before':item['before_observer_fault']}
            elif op in ('history-observe','history-prepare007','history-upgrade008'):
                assert item.get('mode')=='function-version-unknown-first'
                if op=='history-observe':result=history_observation(item,request['function_id'])
                elif op=='history-prepare007':result=prepare_history007(item,journal,request)
                else:result=upgrade_history008(item,journal,request['function_id'])
            elif op == 'upgrade':
                assert not item.get('upgraded'), 'already_upgraded'
                docker(item, 'rm', '-f', temporary_control_name(item))
                item['upgraded'] = True
                atomic(journal, item)
                result = start_control(item, journal, item['original']['image'])
            elif op == 'restart':
                assert item.get('upgraded')
                docker(item, 'restart', temporary_control_name(item))
                # A deliberately contradictory pending command degrades health; API remains readable.
                result = container(item, temporary_control_name(item))
            # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#preuves-à-terminer
            elif op in ('upgrade-readable', 'upgrade-refusal'):
                assert item.get('mode') == 'function-version-purge' and not item.get('upgraded')
                fixture = stopped_purge_input(item,journal,request['function_id'],request['phase'])
                item['upgraded'] = True;atomic(journal,item)
                result = start_control(item,journal,item['original']['image'],
                    readiness='migration-refusal' if op == 'upgrade-refusal' else 'anonymous-api')
                after = purge_upgrade_observation(item,request['function_id'])
                if op == 'upgrade-refusal':
                    assert after['versions'] == SCHEMA_006 and not after['has_code_hash_column']
                    assert database_snapshot(item,'state') == fixture['tables'], 'refused_migration_changed_rows'
                    assert schema_objects(item) == fixture['schema_objects'], 'refused_migration_changed_schema'
                    assert artifacts(item) == fixture['artifact_sha256'], 'refused_migration_changed_artifacts'
                    item['migration_refused'] = True;atomic(journal,item)
                    result = {**result,'rollback_complete':True,'before':fixture,'after':after}
                else:
                    assert after['versions'] == (SCHEMA_008 if item.get('target_schema')=='008' else SCHEMA_007) and after['has_code_hash_column']
                    assert all(row['code_hash']==previous['code_hash'] and row['empty_inventory'] and row['empty_events'] for row,previous in zip(after['code'],fixture['observation']['code']))
                    if item.get('target_schema')=='008':verify_purge_version_migration(item,fixture,after)
                    assert artifacts(item) == fixture['artifact_sha256'], 'migrated_purge_changed_retained_artifacts'
                    result = {'container':result,'before':fixture,'after':after,'anonymous_api_readable':True}
            elif op == 'resume-historical':
                assert item.get('mode') == 'function-version-purge' and item.get('migration_refused')
                before = purge_upgrade_observation(item,request['function_id'])
                assert before['versions'] == SCHEMA_006 and not before['has_code_hash_column'], 'downgrade_after_migration_forbidden'
                assert database_snapshot(item,'state') == item['purge_input']['tables']
                assert schema_objects(item) == item['purge_input']['schema_objects'], 'historical_resume_schema_changed'
                docker(item,'rm','-f',temporary_control_name(item))
                result = start_control(item,journal,item['historical_image'],readiness='anonymous-api')
                item['upgraded'] = False;item['migration_refused'] = False;atomic(journal,item)
                result = {'container':result,'same_database_resumed':True,'after':purge_upgrade_observation(item,request['function_id'])}
            elif op == 'inspect-purge-upgrade':
                result = purge_upgrade_observation(item,request['function_id'])
            elif op == 'release-artifact':
                result = release_purge_artifact(item,journal,request['function_id'])
            elif op == 'inspect':
                result = inspect_function(item, request['function_id'])
            elif op == 'deny-artifact':
                assert not item.get('denied')
                function = request['function_id']
                value = inspect_function(item, function)
                assert len(value['revisions']) == 1
                path = Path(paths['state']) / 'artifacts' / value['revisions'][0]['id']
                item['denied'] = {'path': str(path), 'identity': identity(path), 'function_id': function}
                atomic(journal, item)
                os.chown(path, 0, 0)
                os.chmod(path, 0o500)
                result = {'denied': True, 'function_id': function}
            elif op == 'introduce-storage':
                function = request['function_id']
                value = inspect_function(item, function)
                assert item['denied']['function_id'] == function and not value['agent']
                assert len(value['commands']) == 1 and value['commands'][0]['storage_absent'] == 1
                assert value['commands'][0]['state'] == 'pending' and value['commands'][0]['phase'] == 'artifacts'
                result = agent_call(item, {'op': 'configure', 'function_id': function,
                    'configuration': {kind: {'enabled': False, 'quota_mib': 8} for kind in ('data', 'cache')}})
                path = Path(item['denied']['path'])
                previous, current = item['denied']['identity'], identity(path)
                assert (current['device'], current['inode']) == (previous['device'], previous['inode'])
                os.chown(path, previous['uid'], previous['gid'])
                os.chmod(path, previous['mode'])
                item['denied']['released'] = True
                atomic(journal, item)
            else:
                raise AssertionError('unknown_campaign_operation')
            emit({'event': 'result', 'op': op, 'value': result})
    finally:
        restore(item, journal, False)


def lock_available(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


if __name__ == '__main__':
    main()
