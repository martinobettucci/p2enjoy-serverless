# @spec docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md
# @verifies docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#fenêtre-et-conservation-des-données
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#preuves-à-terminer
"""DEV-only historical installation window with an independent identity-based restore."""
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
        candidates = docker(item, 'ps', '-aq', '--filter', 'name=^/' + TEMP + '$').split()
        if candidates:
            assert len(candidates) == 1
            definition = json.loads(docker(item, 'inspect', candidates[0]))[0]
            assert definition['Config']['Labels']['com.docker.compose.project'] == item['project']
            docker(item, 'rm', '-f', candidates[0])
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
    result = command(item['docker'] + ['exec', TEMP, 'python', '-B', '-c', program], (0, 1))
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
    source = source.replace('    container_name: serverless-api\n', '    container_name: ' + TEMP + '\n')
    source = source.replace('    image: p2enjoy-control:dev\n', '    image: ' + image + '\n')
    source = source.replace('    build:\n      context: ..\n      dockerfile: control/Dockerfile\n', '')
    source = source.replace('    restart: unless-stopped\n', '    restart: "no"\n')
    compose = Path(item['work']) / 'compose.yml'
    compose.write_text(source)
    os.chmod(compose, 0o640)
    os.chown(compose, 0, item['gid'])
    docker(item, 'compose', '--env-file', '/etc/spark/env', '--env-file', '/run/spark/secrets',
           '-f', str(compose), 'up', '-d', '--no-build')
    if readiness == 'migration-refusal':
        def exited():
            state = json.loads(docker(item, 'inspect', '--format', '{{json .State}}', TEMP))
            return state if state['Status'] == 'exited' else None
        state = until(exited, 'migration_refusal_missing', 30)
        assert state['ExitCode'] != 0, 'migration_refusal_exit_required'
        current = container(item,TEMP)
        assert current['image'] == image and not current['running'] and current['id'] != item['original']['id']
        identifier = rows(item,Path(item['paths']['state']) / 'control.sqlite3',"SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
        assert identifier == item['temporary_installation'] and identifier != item['installation']
        logs = command(item['docker'] + ['logs', TEMP], combined_output=True)
        assert 'user-defined function raised exception' in logs and 'Application startup complete.' not in logs
        return {'container': current, 'installation_id':identifier, 'migration_refused': True, 'exit_code': state['ExitCode'],
                'udf_error_seen': True, 'log_sha256': hashlib.sha256(logs.encode()).hexdigest()}
    def ready():
        value = container(item, TEMP)
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
    observation['function'] = rows(item, control, '''SELECT id,service_id,deleted_at,updated_at,active_revision_id
        FROM functions WHERE id=?''', (function,))[0]
    revisions = rows(item, control, '''SELECT id,stored_bytes,deleted_at,inventory_json,events_json,archive_sha256'''
        + (',code_hash' if hashed else '') + ' FROM revisions WHERE function_id=? ORDER BY id', (function,))
    observation['has_code_hash_column'] = hashed
    observation['code'] = [{**{key:row[key] for key in ('id','stored_bytes','deleted_at','archive_sha256')},
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
    assert before['versions'] == SCHEMA_006 and not before['has_code_hash_column']
    assert len(before['purge_commands']) == len(before['purge_guards']) == len(before['code']) == 1
    request, guard = before['purge_commands'][0], before['purge_guards'][0]
    assert request['state'] == 'pending' and request['phase'] == phase and request['id'] == guard['id']
    assert guard['decision'] == 'commit' and guard['kind'] == 'purge'
    assert before['function']['deleted_at'] and before['function']['active_revision_id'] is None
    assert before['code'][0]['empty_inventory'] and before['code'][0]['empty_events'] and before['code'][0]['stored_bytes'] > 0
    assert before['artifacts'][before['code'][0]['id']]
    current = container(item, TEMP);assert current['image'] == item['historical_image'] and current['running']
    docker(item, 'rm', '-f', TEMP)
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


def main():
    global LOCK
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    mode, campaign = sys.argv[1:3]
    assert str(UUID(campaign)) == campaign
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
    candidates = [HISTORY / (prefix + campaign) for prefix in ('storage-absence-', 'function-version-purge-')]
    if mode in ('restore', 'status'):
        existing = [path for path in candidates if (path / 'restore.json').exists()]
        assert len(existing) <= 1, 'ambiguous_campaign_window'
        work = existing[0] if existing else candidates[0]
    else:work = candidates[1] if mode == 'function-version-purge' else candidates[0]
    journal = work / 'restore.json'
    if mode in ('restore', 'status'):
        if mode == 'status' and not journal.exists():
            emit({'restored': False, 'not_started': True, 'campaign': campaign})
            return
        item = json.loads(journal.read_text())
        assert item['campaign'] == campaign and item['work'] == str(work)
        if mode == 'status':
            emit({'restored': item.get('restored', False), 'restoration': item.get('restoration'),
                  'driver_alive': alive(item), 'unit': item['unit'],
                  'timer_state':command(['systemctl','is-active',item['unit'] + '.timer'],(0,3,4)),
                  'service_state':command(['systemctl','is-active',item['unit'] + '.service'],(0,3,4))})
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
    assert mode in ('partial', 'historical', 'function-version-purge')
    old_image = sys.argv[3]
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', old_image)
    if mode == 'function-version-purge':
        attestation = HISTORY / 'function-version-schema006-image.json';info = attestation.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'protected_schema006_attestation_required'
        reference = json.loads(attestation.read_text())
        assert reference['completed'] and reference['revision'] == SCHEMA_006_REVISION
        assert reference['schema_migrations'] == SCHEMA_006 and reference['image'] == old_image, 'known_schema006_image_required'
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
    for previous in [*HISTORY.glob('storage-absence-*/restore.json'), *HISTORY.glob('function-version-purge-*/restore.json')]:
        assert json.loads(previous.read_text()).get('restored'), 'previous_window_not_restored'
    work.mkdir(mode=0o750)
    os.chown(work, 0, account.pw_gid)
    originals = {key: identity(path) for key, path in paths.items()}
    assert all(value['device'] == work.stat().st_dev for value in originals.values())
    assert all((value['uid'], value['gid']) == (account.pw_uid, account.pw_gid) and
               value['mode'] in ((0o700, 0o750) if key == 'state' else (0o700,))
               for key, value in originals.items()), 'official_directory_permissions'
    item = {'campaign': campaign, 'work': str(work), 'paths': paths, 'original_dirs': originals,
            'mode':mode, 'historical_image':old_image,
            'namespace_name':('code-purge-migration-' if mode == 'function-version-purge' else 'legacy-') + campaign[:8],
            'lock_identity': [lock_info.st_dev, lock_info.st_ino],
            'uid': account.pw_uid, 'gid': account.pw_gid, 'configuration': hashes(),
            'docker': ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']],
            'unit': ('serverless-restore-version-purge-' if mode == 'function-version-purge' else 'serverless-restore-archive-migration-') + campaign,
            'project': ('function-version-purge-' if mode == 'function-version-purge' else 'archive-migration-') + campaign,
            'driver_pid': os.getpid(), 'driver_birth': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]}
    item['original'] = container(item, 'serverless-api')
    item['reference'] = container(item, 'serverless-runtime-reference')
    assert item['original']['status'] == 'healthy' and item['reference']['running']
    item['installation'] = rows(item, Path(paths['state']) / 'control.sqlite3', "SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']
    quiet_control(item)
    no_references(item, allow_original=True)
    assert agent_call(item, {'op': 'health'})['healthy']
    # Freeze the restoration code and its identity-switching helper for this window.
    for name in ('storage-legacy-environment.py', 'control_database.py'):
        shutil.copyfile(Path(__file__).parent / name, work / name)
        os.chmod(work / name, 0o600)
    atomic(journal, item)
    command(['systemd-run', '--quiet', '--collect', '--unit=' + item['unit'],
             '--on-active=' + ('60s' if mode == 'partial' else '900s'),
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
        emit({'event': 'historical-ready', 'container': current, 'installation_id': item['temporary_installation']})
        for line in sys.stdin:
            request = json.loads(line)
            op = request['op']
            if op == 'restore':
                break
            if op == 'upgrade':
                assert not item.get('upgraded'), 'already_upgraded'
                docker(item, 'rm', '-f', TEMP)
                item['upgraded'] = True
                atomic(journal, item)
                result = start_control(item, journal, item['original']['image'])
            elif op == 'restart':
                assert item.get('upgraded')
                docker(item, 'restart', TEMP)
                # A deliberately contradictory pending command degrades health; API remains readable.
                result = container(item, TEMP)
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
                    assert after['versions'] == SCHEMA_007 and after['has_code_hash_column']
                    assert all(row['code_hash'] is None and row['empty_inventory'] and row['empty_events'] for row in after['code'])
                    assert artifacts(item) == fixture['artifact_sha256'], 'migrated_purge_changed_retained_artifacts'
                    result = {'container':result,'before':fixture,'after':after,'anonymous_api_readable':True}
            elif op == 'resume-historical':
                assert item.get('mode') == 'function-version-purge' and item.get('migration_refused')
                before = purge_upgrade_observation(item,request['function_id'])
                assert before['versions'] == SCHEMA_006 and not before['has_code_hash_column'], 'downgrade_after_migration_forbidden'
                assert database_snapshot(item,'state') == item['purge_input']['tables']
                assert schema_objects(item) == item['purge_input']['schema_objects'], 'historical_resume_schema_changed'
                docker(item,'rm','-f',TEMP)
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
