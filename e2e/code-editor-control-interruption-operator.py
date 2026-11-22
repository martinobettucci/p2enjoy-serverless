# @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#préconditions-et-historique
# @verifies docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_CONTROL_INTERRUPTION.md
# @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_CONTROL_INTERRUPTION.md#acquisition-et-coupure-gardées
# @spec docs/BACKLOG.md#sls-118 | docs/CODE_EDITOR_CONTROL_WINDOW.md#décision-avant-correction
# @verifies docs/BACKLOG.md#sls-118 | docs/CODE_EDITOR_CONTROL_WINDOW.md#replay-et-critères-de-preuve
"""Native DEV control cuts, armed before the real code-draft publication POST."""
import ast
from contextlib import closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import select
import shlex
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import time
from uuid import UUID, uuid4
import zipfile
from control_database import read_control, control_owner
from native_control_observer import NativeObserver

IMAGE = 'sha256:f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0'
PROTOCOL = {'version': 1, 'guard_delay_seconds': 45, 'restore_alarm_seconds': 180,
            'evidence_probe_timeout_seconds': 10}


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, timeout=10):
    value = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    assert value.returncode == 0, 'native_command_failed'
    return value.stdout.strip()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def encoded(value):
    return digest(json.dumps(value, sort_keys=True).encode())


def birth(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


def settings():
    result = {}
    for line in Path('/etc/spark/env').read_text().splitlines():
        fields = shlex.split(line, comments=True)
        if len(fields) == 1 and '=' in fields[0]:
            key, value = fields[0].split('=', 1)
            if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_DOCKER_SOCKET_HOST',
                       'SERVERLESS_STORAGE_ROOT_HOST'):
                result[key] = value
    return result


# Read literal bytes only: importing the historical operator would run its CLI.
tree = ast.parse(Path(__file__).with_name('publication-recovery-operator.py').read_text())
guards = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
          if isinstance(node, ast.Assign) and len(node.targets) == 1
          and isinstance(node.targets[0], ast.Name)
          and node.targets[0].id in ('RESTORE', 'KILL_CONTROL')}
RESTORE, KILL_CONTROL = guards['RESTORE'], guards['KILL_CONTROL']
assert digest(RESTORE.encode()) == 'd5fd248602d77a2928048f920c270b6b81b2ad549b0b567a1f07f11580a8459b'
assert digest(KILL_CONTROL.encode()) == '19359bde933e5eebf10de80d04eb7585a7b2a81fabf28f05c7370b877571321b'
assert 'signal.alarm(180)\n' in RESTORE
assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
assert platform.machine() == 'x86_64'
mode, namespace, function_id = sys.argv[1:4]
assert mode in ('inspect', 'receiving', 'validating', 'restore', 'rescue', 'evidence', 'receipt')
assert str(UUID(namespace)) == namespace and str(UUID(function_id)) == function_id
values = settings()
root = Path(values['SERVERLESS_STATE_HOST_PATH'])
control = root / 'control.sqlite3'
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host',
          'unix://' + values['SERVERLESS_DOCKER_SOCKET_HOST']]
with read_control(control) as db:
    ns = db.execute('SELECT name FROM namespaces WHERE id=?', (namespace,)).fetchone()
    assert ns and re.fullmatch('code-editor-control-interruption-[0-9a-f]{8}', ns['name'])
    row = db.execute('SELECT f.service_id FROM functions f JOIN services s ON s.id=f.service_id '
                     'WHERE f.id=? AND s.namespace_id=?', (function_id, namespace)).fetchone()
    assert row, 'owned_function_required'
    service = row['service_id']
    installation = db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]


def containers(kind):
    ids = command(docker + ['ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.kind=' + kind], 5).split()
    return json.loads(command(docker + ['inspect', *ids], 5)) if ids else []


def validation_rows():
    return [{'id': v['Id'], 'running': v['State']['Running'], 'image': v['Image'],
             'installation': v['Config']['Labels'].get('tech.p2enjoy.serverless.installation'),
             'mounts': [{k: m[k] for k in ('Source', 'Destination')} for m in v['Mounts']]}
            for v in containers('validation')]


def archive_metadata(candidate):
    folder = root / 'artifacts' / str(UUID(candidate))
    file = folder / 'archive.zip'
    assert not folder.is_symlink() and not file.is_symlink()
    result = {'directory_exists': folder.exists(), 'archive_exists': file.exists()}
    if file.exists():
        info = file.lstat()
        assert stat.S_ISREG(info.st_mode), 'regular_archive_required'
        result.update(archive_bytes=info.st_size, archive_mode=oct(stat.S_IMODE(info.st_mode)),
                      device=info.st_dev, inode=info.st_ino)
    return result


def draft_row(db):
    rows = db.execute('SELECT * FROM code_drafts WHERE function_id=? ORDER BY id', (function_id,)).fetchall()
    assert len(rows) <= 1, 'single_owned_draft_required'
    if not rows:
        return None
    row = dict(rows[0])
    ciphertext = row.pop('changes_cipher').encode('ascii')
    row.update(cipher_bytes=len(ciphertext), cipher_sha256=digest(ciphertext))
    return row


def inspect(candidate=None):
    with read_control(control) as db:
        db.execute('BEGIN')
        counts = {name: db.execute(sql).fetchone()[0] for name, sql in {
            'active_candidates': "SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
            'reserved_bytes': 'SELECT coalesce(sum(reserved_bytes),0) FROM deployments',
            'instances': 'SELECT count(*) FROM execution_instances',
            'active_calls': "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
            'operations': 'SELECT count(*) FROM function_operations'}.items()}
        row = dict(db.execute('SELECT * FROM functions WHERE id=?', (function_id,)).fetchone())
        function = {k: row[k] for k in ('id', 'service_id', 'active_revision_id', 'updated_at',
                    'first_published_code_hash', 'first_promoted_at', 'deleted_at', 'purged_at')}
        function['configuration_sha256'] = encoded({k: row[k] for k in ('config_json', 'environment_json', 'secrets_cipher')})
        revisions = [dict(v) for v in db.execute('SELECT id,code_hash,archive_sha256,created_at,deleted_at,stored_bytes '
                                                'FROM revisions WHERE function_id=? ORDER BY id', (function_id,))]
        archives = {}
        for revision in revisions:
            file = root / 'artifacts' / revision['id'] / 'archive.zip'
            metadata = archive_metadata(revision['id'])
            metadata['sha256'] = sha(file) if file.exists() else None
            if revision['stored_bytes']:
                assert metadata['sha256'] == revision['archive_sha256']
            archives[revision['id']] = metadata
        candidates = []
        for value in db.execute('SELECT id,function_id,service_id,state,error_code,reserved_bytes,'
                                'configuration_cipher IS NULL AS payload_erased,revision_id,code_hash,code_only '
                                'FROM deployments WHERE function_id=? ORDER BY id', (function_id,)):
            item = dict(value)
            item.update(archive_metadata(item['id']))
            candidates.append(item)
        audits = []
        for value in db.execute("SELECT id,action,detail_json FROM audit_events WHERE object_id=? "
                                "AND action IN ('deployment.prepare','function.deploy','deployment.abandon') ORDER BY id", (function_id,)):
            detail = json.loads(value['detail_json'])
            audits.append({'id': value['id'], 'action': value['action']} |
                          {k: detail[k] for k in ('deployment_id', 'revision_id', 'code_hash') if k in detail})
        result = {'counts': counts, 'function': function, 'draft': draft_row(db),
                  'versions': [dict(v) for v in db.execute('SELECT * FROM function_versions WHERE function_id=? ORDER BY code_hash', (function_id,))],
                  'revisions': revisions, 'archives': archives, 'candidates': candidates, 'audits': audits,
                  'draft_audits': [dict(v) for v in db.execute("SELECT id,action FROM audit_events WHERE object_id=? AND action IN ('code_draft.create','code_draft.save','code_draft.discard') ORDER BY id", (function_id,))],
                  'invocations': [dict(v) for v in db.execute('SELECT id,revision_id,state,handler_started,http_status FROM invocations WHERE function_id=? ORDER BY id', (function_id,))],
                  'integrity': db.execute('PRAGMA integrity_check').fetchone()[0],
                  'foreign_keys': [list(v) for v in db.execute('PRAGMA foreign_key_check')],
                  'migrations': [dict(v) for v in db.execute('SELECT * FROM schema_migrations ORDER BY version')]}
        if candidate:
            result['candidate'] = next((v for v in candidates if v['id'] == candidate), None)
    current = json.loads(command(docker + ['inspect', 'serverless-api'], 5))[0]
    result['control'] = {'Id': current['Id'], 'Image': current['Image'],
                         'started_at': current['State']['StartedAt'], 'running': current['State']['Running'],
                         'init_pid': current['State']['Pid']}
    result['validation_containers'] = validation_rows()
    result['validation_channels'] = sorted(p.name for p in (root / 'validation').iterdir())
    return result


def finish_guard(unit):
    subprocess.run(['systemctl', 'stop', unit + '.timer'], capture_output=True, timeout=10)
    deadline = time.monotonic() + 45
    while True:
        states = {}
        for suffix in ('timer', 'service'):
            value = command(['systemctl', 'show', unit + '.' + suffix, '--property=ActiveState',
                             '--property=LoadState', '--property=MainPID'])
            states[suffix] = dict(v.split('=', 1) for v in value.splitlines())
        if all(v.get('ActiveState') == 'inactive' and v.get('MainPID', '0') == '0' for v in states.values()):
            return states
        assert time.monotonic() < deadline, 'guard_service_not_joined'
        time.sleep(.1)


if mode in ('restore', 'rescue', 'evidence', 'receipt'):
    unit = sys.argv[4]
    assert re.fullmatch('serverless-restore-publication-upload-[0-9a-f]{32}', unit)
    folder = Path('/run') / unit
    info = folder.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700
    item = json.loads((folder / 'identity.json').read_text())
    assert item['function_id'] == function_id and item['namespace_id'] == namespace and item['image'] == IMAGE
    if mode == 'receipt':
        files = {}
        for name in ('identity.json', 'kill-started.json', 'kill-result.json', 'interrupted.json',
                     'restored.json', 'restored-independent.json'):
            file = folder / name
            if file.exists():
                info = file.lstat()
                assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_size < 65536
                raw = file.read_bytes()
                files[name] = {'sha256': digest(raw), 'value': json.loads(raw)}
        assert sha(folder / 'restore.py') == item['restore_sha256'] == digest(RESTORE.encode())
        assert sha(folder / 'kill.py') == item['kill_sha256'] == digest(KILL_CONTROL.encode())
        assert files['kill-result.json']['value']['completed']
        assert files['kill-result.json']['value']['docker_client_joined']
        assert files['kill-result.json']['value']['exit_code'] == 137
        states = {}
        for suffix in ('timer', 'service'):
            value = command(['systemctl', 'show', unit + '.' + suffix, '--property=ActiveState',
                             '--property=LoadState', '--property=MainPID'])
            states[suffix] = dict(v.split('=', 1) for v in value.splitlines())
        helper_alive = False
        try:
            helper_alive = birth(item['helper_pid']) == item['helper_birth']
        except FileNotFoundError:
            pass
        emit({'completed': True, 'unit': unit, 'files': files, 'guard_states': states,
              'helper_same_process_alive': helper_alive,
              'program_sha256': {'restore': sha(folder / 'restore.py'), 'kill': sha(folder / 'kill.py')}})
    elif mode == 'evidence':
        file = folder / 'restored-independent.json'
        emit(json.loads(file.read_text()) if file.exists() else {'event': 'pending'})
    else:
        receipt = json.loads(command(['/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder),
                                      *(['guard'] if mode == 'rescue' else [])], 190))
        receipt['guard_states'] = finish_guard(unit)
        emit(receipt)
    sys.exit(0)
if mode == 'inspect':
    emit(inspect(sys.argv[4] if len(sys.argv) > 4 else None))
    sys.exit(0)

candidate, draft_id, version_text = sys.argv[4:7]
assert str(UUID(candidate)) == candidate and str(UUID(draft_id)) == draft_id
version = int(version_text)
before = inspect()
assert before['counts'] == {'active_candidates': 0, 'reserved_bytes': 0, 'instances': 0, 'active_calls': 0, 'operations': 0}
assert before['validation_containers'] == before['validation_channels'] == []
assert before['draft'] and before['draft']['id'] == draft_id and before['draft']['version'] == version
assert before['draft']['actor_kind'] == 'admin' and before['function']['deleted_at'] is None
assert before['draft']['base_revision_id'] and before['draft']['base_function_version'] == before['function']['updated_at']
with read_control(control) as db:
    assert db.execute('SELECT count(*) FROM deployments WHERE id=?', (candidate,)).fetchone()[0] == 0
    assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0] == 1
    service_version = db.execute('SELECT updated_at FROM services WHERE id=?', (service,)).fetchone()[0]
assert not (root / 'artifacts' / candidate).exists() and not (root / 'artifacts' / candidate).is_symlink()
registry = Path(values['SERVERLESS_STORAGE_ROOT_HOST']) / 'registry.sqlite3'
with control_owner(control), closing(sqlite3.connect('file:' + str(registry) + '?mode=ro', uri=True)) as db:
    assert db.execute('SELECT count(*) FROM leases').fetchone()[0] == 0
assert not containers('instance')
current, reference = json.loads(command(docker + ['inspect', 'serverless-api', 'serverless-runtime-reference'], 5))
assert current['Image'] == IMAGE and before['control']['Id'] == current['Id']
assert current['State']['Health']['Status'] == reference['State']['Health']['Status'] == 'healthy'
runtime_image = dict(v.split('=', 1) for v in current['Config']['Env'])['SERVERLESS_RUNTIME_IMAGE']
assert re.fullmatch('sha256:[0-9a-f]{64}', runtime_image)
init = current['State']['Pid']
descendants = [init]
for parent in descendants:
    descendants.extend(int(v) for v in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
processes = [pid for pid in descendants if Path(os.readlink(f'/proc/{pid}/exe')).name.startswith('python')
             and Path('/proc', str(pid), 'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00')]
assert len(processes) == 1
pid = processes[0]
assert Path('/proc', str(pid), 'cgroup').read_text() == Path('/proc', str(init), 'cgroup').read_text()
unit = 'serverless-restore-publication-upload-' + uuid4().hex
folder = Path('/run') / unit
folder.mkdir(mode=0o700)
lock = os.open(folder / 'mutation.lock', os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
info = os.fstat(lock)
item = {'restore_protocol': PROTOCOL, 'namespace_id': namespace, 'function_id': function_id,
        'candidate_id': candidate, 'draft_id': draft_id, 'draft_version': version, 'phase': mode,
        'official_sha256': {name: sha(name) for name in ('/etc/spark/env', '/run/spark/secrets', '/etc/spark/routes')},
        'restore_sha256': digest(RESTORE.encode()), 'kill_sha256': digest(KILL_CONTROL.encode()),
        'operator_sha256': sha(__file__), 'native_observer_sha256': sha(Path(__file__).with_name('native_control_observer.py')),
        'container_id': current['Id'], 'image': current['Image'], 'started_at': current['State']['StartedAt'],
        'reference': [reference['Id'], reference['Image'], reference['State']['StartedAt']], 'docker': docker,
        'pid': pid, 'birth': birth(pid), 'cgroup': Path('/proc', str(pid), 'cgroup').read_text(),
        'helper_pid': os.getpid(), 'helper_birth': birth(os.getpid()), 'lock_identity': [info.st_dev, info.st_ino]}
for leaf, body in [('identity.json', json.dumps(item)), ('restore.py', RESTORE), ('kill.py', KILL_CONTROL)]:
    file = folder / leaf
    file.write_text(body)
    os.chmod(file, 0o600)


def probe():
    with read_control(control) as db:
        row = db.execute('SELECT id,function_id,service_id,actor_kind,actor_id,state,reserved_bytes,code_only,'
                         'expected_function_version,expected_service_version FROM deployments WHERE id=?', (candidate,)).fetchone()
        if not row:
            return {'state': 'absent'}
        row = dict(row)
        draft = db.execute('SELECT id,version,last_deployment_id,last_publication_version FROM code_drafts WHERE id=?', (draft_id,)).fetchone()
    row.update(archive_metadata(candidate), draft_link=dict(draft) if draft else None)
    return row


def checked_probe(row):
    assert row['state'] in ('absent', 'prepared', 'receiving', 'validating'), 'window_missed_' + row['state']
    if row['state'] == 'absent':
        return
    assert row['function_id'] == function_id and row['service_id'] == service and row['code_only'] == 1
    assert (row['actor_kind'], row['actor_id']) == (before['draft']['actor_kind'], before['draft']['actor_id'])
    assert row['expected_function_version'] == before['function']['updated_at'] and row['expected_service_version'] == service_version
    assert row['draft_link'] == {'id': draft_id, 'version': version, 'last_deployment_id': candidate, 'last_publication_version': version}
    assert row['reserved_bytes'] > 0 if row['state'] in ('receiving', 'validating') else row['reserved_bytes'] == 0


def matching_validators():
    rows = validation_rows()
    return [v for v in rows if v['running'] and v['image'] == runtime_image and v['installation'] == installation
            and any(m['Destination'] == '/code' and m['Source'] == str(root / 'artifacts' / candidate / 'code') for m in v['mounts'])]


observer = NativeObserver(pid)
armed = False
timeline = []
try:
    command(['systemd-run', '--quiet', '--collect', '--unit=' + unit, '--on-active=45s',
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '--property=RuntimeMaxSec=190s', '--property=TimeoutStopSec=5s',
             '/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder), 'guard'])
    armed = True
    assert command(['systemctl', 'is-active', unit + '.timer']) == 'active'
    emit({'event': 'guard-armed', 'unit': unit})
    emit({'event': 'armed', 'unit': unit, 'before': before, 'restore_protocol': PROTOCOL,
          'identity': {k: item[k] for k in ('container_id', 'image', 'started_at', 'pid', 'birth', 'reference', 'restore_sha256', 'kill_sha256')}})
    assert select.select([sys.stdin], [], [], 20)[0] and sys.stdin.readline().strip() == 'observe'
    started = time.monotonic_ns()
    deadline = time.monotonic() + 20
    probes, observed, matches = 0, None, []
    last = None
    while time.monotonic() < deadline:
        value = probe()
        probes += 1
        signature = (value['state'], value.get('archive_mode'), value.get('archive_bytes'))
        if signature != last:
            timeline.append({'elapsed_ns': time.monotonic_ns() - started, 'probe': probes, 'value': value})
            last = signature
        checked_probe(value)
        if mode == 'receiving' and value['state'] == 'validating':
            raise AssertionError('receiving_window_missed')
        if value['state'] == mode and value.get('archive_bytes', 0) > 0 and value.get('archive_mode') == '0o444':
            if mode == 'receiving':
                observed = value
                break
            matches = matching_validators()
            if len(matches) == 1:
                observed = value
                break
            assert len(matches) == 0, 'multiple_owned_validators'
        time.sleep(.01)
    emit({'event': 'phase-observation', 'phase': mode, 'probes': probes, 'elapsed_ns': time.monotonic_ns() - started, 'timeline': timeline})
    assert observed, 'physical_phase_not_observed'
    observer.start()
    gated = probe()
    emit({'event': 'phase-retained', 'phase': mode, 'value': gated})
    checked_probe(gated)
    assert gated['state'] == mode and gated.get('archive_mode') == '0o444', 'window_missed_after_attach'
    if mode == 'validating':
        alive = matching_validators()
        assert len(alive) == 1 and alive[0]['id'] == matches[0]['id'], 'validator_not_alive_at_gate'
    file = root / 'artifacts' / candidate / 'archive.zip'
    zip_before = archive_metadata(candidate)
    archive_sha = sha(file)
    expected_names = {'publication-recovery.cjs', 'publication-marker.json'}
    if mode == 'receiving':
        expected_names |= {f'extraction-inputs/file-{index:05d}.txt' for index in range(18000)}
    with zipfile.ZipFile(file) as archive:
        assert len(archive.infolist()) == len(expected_names) and set(archive.namelist()) == expected_names
        assert archive.testzip() is None, 'complete_archive_crc_required'
    assert archive_metadata(candidate) == zip_before and sha(file) == archive_sha
    if mode == 'validating':
        alive = matching_validators()
        emit({'event': 'validator-after-archive-check', 'validators': alive})
        assert len(alive) == 1 and alive[0]['id'] == matches[0]['id'], 'validator_window_missed_during_archive_check'
        matches = alive
    emit({'event': 'gated', 'phase': mode, 'unit': unit, 'observed': observed, 'durable': gated,
          'archive': zip_before | {'sha256': archive_sha, 'entries': len(expected_names), 'all_crc_valid': True},
          'validator': matches[0] if matches else None})
    assert select.select([sys.stdin], [], [], 8)[0] and sys.stdin.readline().strip() == 'interrupt'
    assert birth(pid) == item['birth'] and Path('/proc', str(pid), 'cgroup').read_text() == item['cgroup']
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        file = folder / 'kill-started.json'
        file.write_text(json.dumps({'requested': True}) + '\n')
        os.chmod(file, 0o600)
        stopped = subprocess.Popen(['/usr/bin/python3', '-I', str(folder / 'kill.py'), str(folder), str(lock)],
                                   pass_fds=(lock,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end = time.monotonic() + 10
        while True:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited:
                assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
                observer.attached = False
                break
            assert time.monotonic() < end, 'control_death_not_observed'
            time.sleep(.01)
        stopped.communicate(timeout=40)
        assert stopped.returncode == 0
        killed = json.loads(command(docker + ['inspect', current['Id']], 5))[0]
        assert not killed['State']['Running'] and killed['State']['ExitCode'] == 137
        proof = {'event': 'cut', 'unit': unit, 'phase': mode, 'exit_code': 137, 'native_signal': 9, 'candidate_id': candidate}
        file = folder / 'interrupted.json'
        file.write_text(json.dumps(proof) + '\n')
        os.chmod(file, 0o600)
        emit(proof)
    finally:
        if 'stopped' in locals():
            stopped.communicate(timeout=50)
            assert stopped.poll() is not None, 'stop_mutator_not_joined'
        fcntl.flock(lock, fcntl.LOCK_UN)
    if mode == 'validating':
        emit({'event': 'observer-loss', 'unit': unit, 'signal': 'SIGKILL'})
        os.kill(os.getpid(), signal.SIGKILL)
except BaseException as error:
    emit({'event': 'operator-failed', 'phase': mode, 'type': type(error).__name__,
          'message_sha256': digest(str(error).encode()), 'timeline': timeline})
    raise
finally:
    observer.detach()
    os.close(lock)
    if armed:
        emit(json.loads(command(['/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder)], 190)))
        emit({'event': 'guard-finished', 'unit': unit, 'states': finish_guard(unit)})
