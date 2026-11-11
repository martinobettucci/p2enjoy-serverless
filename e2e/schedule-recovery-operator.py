# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#interruptions-pendant-sauvegarde-et-copie
# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RECOVERY.md#périmètre-et-frontières | docs/SCHEDULE_RECOVERY.md#garde-et-restitution
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RECOVERY.md#campagne-séquentielle
# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-authentique-avant-vieillissement
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-authentique-avant-vieillissement
"""Observe real scheduler commits, capture retention witnesses or interrupt owned DEV."""
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
import shutil
import shlex
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import time
from uuid import UUID, uuid4
from control_database import ControlObserver, control_owner, read_control
from native_control_observer import NativeObserver


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, timeout=35):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    assert result.returncode == 0, 'operator_command_failed'
    return result.stdout.strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def birth(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


def finish_guard(unit):
    subprocess.run(['systemctl', 'stop', unit+'.timer'], capture_output=True, timeout=10)
    end = time.monotonic()+45
    while True:
        states = {}
        for suffix in ('timer', 'service'):
            result = subprocess.run(['systemctl', 'show', unit+'.'+suffix,
                                     '--property=ActiveState', '--property=LoadState', '--property=MainPID'],
                                    capture_output=True, text=True, timeout=10)
            states[suffix] = dict(v.split('=', 1) for v in result.stdout.splitlines())
        if all(v.get('ActiveState') == 'inactive' and v.get('MainPID', '0') == '0' for v in states.values()):
            return states
        assert time.monotonic() < end, 'guard_service_not_joined'
        time.sleep(.1)


assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless' and platform.machine() == 'x86_64', 'dev_spark_required'
mode, function_id, namespace = sys.argv[1:4]
assert mode in ('before', 'claimed', 'linked', 'watchdog', 'inspect', 'restore', 'rescue', 'evidence', 'terminal-capture')
assert str(UUID(function_id)) == function_id and str(UUID(namespace)) == namespace
assert not any(v.startswith('--capture-loss') for v in sys.argv[4:]) or mode == 'terminal-capture', 'capture_loss_requires_terminal_capture'
capture_loss = None
if mode == 'terminal-capture':
    options = sys.argv[5:]
    assert not options or len(options) == 1 and options[0] in (
        '--capture-loss=control-backup', '--capture-loss=artifact-copy'), 'capture_loss_option_required'
    capture_loss = options[0].split('=', 1)[1] if options else None

root = Path('/srv/p2enjoy-serverless')
values = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields = shlex.split(line, comments=True)
    if len(fields) == 1 and '=' in fields[0]:
        key, value = fields[0].split('=', 1)
        if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_DOCKER_SOCKET_HOST', 'SERVERLESS_STORAGE_ROOT_HOST'):
            values[key] = value
control = Path(values['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3'
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST']]
with read_control(control) as db:
    row = db.execute('SELECT f.service_id,n.name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?', (function_id, namespace)).fetchone()
    assert row and re.fullmatch('scheduled-functions-[0-9a-f]{8}', row['name']), 'owned_campaign_required'
    service_id = row['service_id']


def durable():
    with read_control(control) as db:
        db.execute('BEGIN')
        row = dict(db.execute('SELECT * FROM functions WHERE id=?', (function_id,)).fetchone())
        protected = {key: hashlib.sha256(str(row[key]).encode()).hexdigest()
                     for key in ('config_json', 'environment_json', 'secrets_cipher')}
        return {'function':{k:row[k] for k in ('id', 'name', 'active_revision_id', 'updated_at', 'deleted_at', 'purged_at')},
                'configuration_sha256':protected,
                'cursor':db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0],
                'generations':[dict(v) for v in db.execute('SELECT * FROM schedule_generations WHERE function_id=? ORDER BY id', (function_id,))],
                'firings':[dict(v) for v in db.execute('SELECT * FROM schedule_firings WHERE function_id=? ORDER BY window_at,id', (function_id,))],
                'invocations':[dict(v) for v in db.execute('SELECT id,function_id,state,created_at,dispatched_at,completed_at,handler_started,requested_code_hash,resolved_code_hash,trigger,schedule_firing_id,schedule_slot,error_code,logs FROM invocations WHERE function_id=? ORDER BY created_at,id', (function_id,))]}


if mode in ('restore', 'rescue', 'evidence'):
    unit = sys.argv[4]
    assert re.fullmatch('serverless-restore-schedule-[0-9a-f]{32}', unit)
    folder = Path('/run')/unit
    info = folder.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700
    item = json.loads((folder/'identity.json').read_text())
    assert item['function_id'] == function_id and item['namespace_id'] == namespace
    if mode in ('restore', 'rescue'):
        assert sha(folder/'restore.py') == item['restore_sha256']
        receipt = json.loads(command(['/usr/bin/python3', '-I', str(folder/'restore.py'), str(folder), *(['guard'] if mode == 'rescue' else [])], timeout=190))
        receipt['guard_states'] = finish_guard(unit)
        emit(receipt)
    else:
        receipt = folder/'restored-independent.json'
        if not receipt.exists():
            receipt = folder/'restored.json'
        emit(json.loads(receipt.read_text()) if receipt.exists() else {'event':'pending'})
    sys.exit(0)
if mode == 'inspect':
    result = durable()
    services = json.loads(command(docker+['inspect', 'serverless-api', 'serverless-runtime-reference']))
    result['services'] = [{'id':v['Id'], 'image':v['Image'], 'started_at':v['State']['StartedAt'], 'running':v['State']['Running']} for v in services]
    result['official_sha256'] = {p:sha(p) for p in ('/etc/spark/env', '/run/spark/secrets', '/etc/spark/routes')}
    emit(result)
    sys.exit(0)

window = int(sys.argv[4])
assert window % 300 == 0 and 0 < window-time.time() < (600 if mode == 'watchdog' else 30), 'near_future_boundary_required'
with read_control(control) as db:
    assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0] == 1
    for query in ("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
                  "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
                  'SELECT count(*) FROM function_operations', 'SELECT count(*) FROM execution_instances',
                  'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'):
        assert db.execute(query).fetchone()[0] == 0, 'quiet_installation_required'
    generation = db.execute('SELECT * FROM schedule_generations WHERE function_id=? AND retired_at IS NULL', (function_id,)).fetchone()
    assert generation and json.loads(generation['events_json'])['schedules'] == [{'cron':'*/5 * * * *', 'enabled':True, 'timezone':'UTC'}]
    assert not db.execute('SELECT 1 FROM schedule_firings WHERE function_id=? AND window_at=?', (function_id, window)).fetchone()
registry = Path(values['SERVERLESS_STORAGE_ROOT_HOST'])/'registry.sqlite3'
with control_owner(control), closing(sqlite3.connect('file:'+str(registry)+'?mode=ro', uri=True)) as db:
    assert db.execute('SELECT count(*) FROM leases').fetchone()[0] == 0, 'quiet_storage_required'
for kind in ('instance', 'validation'):
    assert not command(docker+['ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.kind='+kind]), 'untracked_consumer_present'
current, reference = json.loads(command(docker+['inspect', 'serverless-api', 'serverless-runtime-reference']))
assert all(v['State']['Running'] and v['State']['Health']['Status'] == 'healthy' for v in (current, reference))
init = current['State']['Pid']
descendants = [init]
for parent in descendants:
    descendants.extend(int(v) for v in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
processes = [p for p in descendants if Path(os.readlink(f'/proc/{p}/exe')).name.startswith('python') and Path('/proc', str(p), 'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
assert len(processes) == 1, 'unique_control_process_required'
pid = processes[0]
assert Path('/proc', str(pid), 'cgroup').read_text() == Path('/proc', str(init), 'cgroup').read_text()

# Extract only already-qualified program literals, never execute the historical operator.
historical = Path(__file__).with_name('function-version-state-observer.py')
constants = {node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse(historical.read_text()).body
             if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('RESTORE', 'KILL_CONTROL')}
assert set(constants) == {'RESTORE', 'KILL_CONTROL'}
assert all(v.count('serverless-restore-version-state-') == 1 for v in constants.values())
restore_program, kill_program = (constants[name].replace('serverless-restore-version-state-', 'serverless-restore-schedule-') for name in ('RESTORE', 'KILL_CONTROL'))
unit = 'serverless-restore-schedule-'+uuid4().hex
folder = Path('/run')/unit
folder.mkdir(mode=0o700)
lock = os.open(folder/'mutation.lock', os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
lock_info = os.fstat(lock)
backup_folder = root/'qualification-history'/('before-schedule-recovery-'+uuid4().hex)
backup_folder.mkdir(mode=0o700)
owner = control.stat()
os.chown(backup_folder, owner.st_uid, owner.st_gid)
backup = backup_folder/'control.sqlite3'
with control_owner(control), closing(sqlite3.connect(control)) as source, closing(sqlite3.connect(backup)) as destination:
    source.backup(destination)
    assert destination.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
os.chmod(backup, 0o600)
item = {'function_id':function_id, 'namespace_id':namespace, 'window':window, 'mode':mode,
        'official_sha256':{p:sha(p) for p in ('/etc/spark/env', '/run/spark/secrets', '/etc/spark/routes')},
        'restore_sha256':hashlib.sha256(restore_program.encode()).hexdigest(), 'kill_sha256':hashlib.sha256(kill_program.encode()).hexdigest(),
        'historical_program_source_sha256':sha(historical), 'operator_sha256':sha(__file__), 'native_observer_sha256':sha(Path(__file__).with_name('native_control_observer.py')),
        'backup':str(backup), 'backup_sha256':sha(backup), 'container_id':current['Id'], 'image':current['Image'], 'started_at':current['State']['StartedAt'],
        'reference':[reference['Id'], reference['Image'], reference['State']['StartedAt']], 'docker':docker, 'pid':pid, 'birth':birth(pid),
        'cgroup':Path('/proc', str(pid), 'cgroup').read_text(), 'helper_pid':os.getpid(), 'helper_birth':birth(os.getpid()),
        'lock_identity':[lock_info.st_dev, lock_info.st_ino]}
if capture_loss:
    item['capture_loss'] = capture_loss
for name, content in [('identity.json', json.dumps(item)), ('restore.py', restore_program), ('kill.py', kill_program)]:
    path = folder/name
    path.write_text(content)
    os.chmod(path, 0o600)
reader = ControlObserver(control)
observer = NativeObserver(pid)
armed = False
try:
    reader.open()
    guard_seconds = 12 if mode == 'watchdog' else 680 if mode == 'before' else 80
    command(['systemd-run', '--quiet', '--collect', '--unit='+unit, '--on-active='+str(guard_seconds)+'s',
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '--property=RuntimeMaxSec=190s', '--property=TimeoutStopSec=5s',
             '/usr/bin/python3', '-I', str(folder/'restore.py'), str(folder), 'guard'])
    armed = True
    assert command(['systemctl', 'is-active', unit+'.timer']) == 'active'
    emit({'event':'guard-armed', 'unit':unit, 'identity':item})
    before = durable()
    emit({'event':'armed', 'unit':unit, 'before':before})
    if mode != 'watchdog':
        while time.time() < window-(1.5 if mode == 'before' else .4):
            time.sleep(.01)
    if mode == 'terminal-capture':
        running_deadline = time.monotonic()+30
        while True:
            started = reader.rows('SELECT id,state,handler_started,completed_at FROM invocations WHERE function_id=? AND schedule_slot=?', (function_id, window))
            assert not any(v['completed_at'] is not None for v in started), 'running_capture_frontier_missed'
            if len(started)==1 and started[0]['state']=='running' and started[0]['handler_started']:
                emit({'event':'handler-running-before-observation', 'invocation':started[0], 'observed_at':time.time()})
                break
            assert time.monotonic()<running_deadline, 'handler_not_started_before_observation'
            time.sleep(.05)
    observer.start()
    if mode == 'watchdog':
        emit({'event':'suspended', 'unit':unit})
        assert select.select([sys.stdin], [], [], 8)[0] and sys.stdin.readline().strip() == 'lose-observer'
        emit({'event':'observer-loss', 'signal':'SIGKILL', 'unit':unit})
        os.kill(os.getpid(), signal.SIGKILL)

    def checkpoint():
        cursor = reader.rows('SELECT window_at FROM schedule_cursor WHERE singleton=1')[0]['window_at']
        firing = reader.rows('SELECT * FROM schedule_firings WHERE function_id=? AND window_at=?', (function_id, window))
        calls = reader.rows('SELECT id,state,handler_started,completed_at,schedule_firing_id FROM invocations WHERE function_id=? AND schedule_slot=?', (function_id, window))
        return {'cursor':cursor, 'firings':firing, 'invocations':calls}

    if mode == 'before':
        gated = checkpoint()
        assert time.time() < window and gated['cursor'] < window and not gated['firings'] and not gated['invocations'], 'before_claim_not_observed'
    else:
        pending = None
        deadline = time.monotonic()+45
        observer.resume()
        while True:
            stopped_signal = observer.wait(deadline)
            if stopped_signal != signal.SIGTRAP|0x80:
                assert stopped_signal not in (signal.SIGSTOP, signal.SIGTRAP)
                observer.resume(stopped_signal)
                continue
            phase, data = observer.info()
            if phase == 1:
                pending = data[0]
            elif phase == 2 and pending in (3, 18, 72, 75, 257):
                gated = checkpoint()
                if gated['cursor'] == window and len(gated['firings']) == 1:
                    firing = gated['firings'][0]
                    if mode == 'claimed' and firing['state'] == 'claimed' and firing['invocation_id'] is None and not gated['invocations']:
                        break
                    if (mode == 'terminal-capture' and firing['state'] == 'dispatched' and firing['completed_at'] is None
                            and len(gated['invocations']) == 1 and firing['invocation_id'] == gated['invocations'][0]['id']
                            and gated['invocations'][0]['state'] == 'succeeded'
                            and gated['invocations'][0]['handler_started'] and gated['invocations'][0]['completed_at'] is not None):
                        break
                    if (mode == 'linked' and firing['state'] == 'dispatched' and len(gated['invocations']) == 1
                            and firing['invocation_id'] == gated['invocations'][0]['id']
                            and gated['invocations'][0]['state'] in ('receiving', 'queued')
                            and gated['invocations'][0]['completed_at'] is None
                            and not gated['invocations'][0]['handler_started']):
                        break
            observer.resume()
    emit({'event':'gated', 'mode':mode, 'checkpoint':gated, 'durable':durable()})
    # @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-authentique-avant-vieillissement
    if mode == 'terminal-capture':
        assert select.select([sys.stdin], [], [], 8)[0] and sys.stdin.readline().strip() == 'capture', 'capture_command_required'
        capture = root/'qualification-history'/('schedule-retention-'+uuid4().hex)
        capture.mkdir(mode=0o700)
        os.chown(capture, owner.st_uid, owner.st_gid)
        snapshot = capture/'control.sqlite3'
        # @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#interruptions-pendant-sauvegarde-et-copie
        loss_fd = None
        if capture_loss:
            loss_fd = os.open(folder/'capture-loss.json', os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            os.fsync(loss_fd)
            directory_fd = os.open(folder, os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

        def pause_incomplete_copy(progress):
            assert loss_fd is not None and capture_loss
            descriptor = os.fstat(loss_fd)
            receipt = {'event':'capture-copy-paused', 'phase':capture_loss,
                       'capture_id':capture.name, 'capture_complete':False,
                       'function_id':function_id, 'namespace_id':namespace, 'window':window,
                       'helper_pid':os.getpid(), 'helper_birth':birth(os.getpid()),
                       'control_pid':pid, 'control_birth':item['birth'],
                       'operator_sha256':item['operator_sha256'], 'sampled_at':time.time(),
                       'effective_uid':os.geteuid(), 'effective_gid':os.getegid(),
                       'receipt_identity':[descriptor.st_dev,descriptor.st_ino],
                       'progress':progress}
            body = memoryview((json.dumps(receipt)+'\n').encode())
            while body:
                count = os.write(loss_fd, body)
                assert count > 0, 'capture_loss_receipt_write_failed'
                body = body[count:]
            os.fsync(loss_fd)
            os.close(loss_fd)
            emit(receipt)
            os.kill(os.getpid(), signal.SIGSTOP)
            raise AssertionError('capture_fault_unexpectedly_resumed')

        if capture_loss == 'control-backup':
            with control_owner(control):
                descriptor = os.open(snapshot, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
                os.close(descriptor)
        with control_owner(control), closing(sqlite3.connect('file:'+str(control)+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(snapshot)) as destination:
            if capture_loss == 'control-backup':
                assert source.execute('PRAGMA page_count').fetchone()[0] > 16, 'capture_source_too_small_for_fault'
                def incomplete_backup(status, remaining, total):
                    assert status == sqlite3.SQLITE_OK and 0 < remaining < total, 'nonfinal_backup_progress_required'
                    pause_incomplete_copy({'status':status, 'remaining':remaining, 'total':total,
                                           'copied_pages':total-remaining, 'backup_complete':False})
                source.backup(destination, pages=16, progress=incomplete_backup)
            else:
                source.backup(destination)
            assert destination.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            destination.row_factory = sqlite3.Row
            captured_firing = dict(destination.execute('SELECT * FROM schedule_firings WHERE id=?', (gated['firings'][0]['id'],)).fetchone())
            captured_call = dict(destination.execute('SELECT id,state,handler_started,completed_at,schedule_firing_id FROM invocations WHERE id=?', (captured_firing['invocation_id'],)).fetchone())
            assert captured_firing == gated['firings'][0] and captured_call == gated['invocations'][0], 'captured_terminal_predicate_changed'
            witnesses = [dict(v) for v in destination.execute("SELECT id,state,trigger,completed_at,handler_started FROM invocations WHERE function_id=? AND trigger='http' AND state='succeeded' AND handler_started=1 AND completed_at<?", (function_id, captured_call['completed_at']))]
            assert len(witnesses) == 1, 'one_genuine_http_witness_required'
            extra = dict(destination.execute('SELECT resolved_code_hash,schedule_slot,trigger,logs FROM invocations WHERE id=?', (captured_call['id'],)).fetchone())
            source_call = next(v for v in durable()['invocations'] if v['id']==captured_call['id'])
            assert all(source_call[k]==v for k,v in extra.items()), 'captured_runtime_observation_changed'
            assert extra['resolved_code_hash']==captured_firing['code_hash'] and extra['schedule_slot']==window and extra['trigger']=='schedule'
            received = json.loads(extra['logs'].strip())
            assert received=={'marker':'scheduled-retention-source','request_id':captured_call['id'],'method':'POST','path':'/',
                              'body':{},'trigger':'schedule','slot':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(window)),
                              'authorization_present':False,'platform_token_present':False}, 'captured_handler_metadata_invalid'
            captured_call.update(extra)

        os.chmod(snapshot, 0o600)
        receipt = {'event':'retention-captured', 'capture_id':capture.name, 'backup_sha256':sha(snapshot),
                   'captured_at':time.time(), 'firing':captured_firing, 'invocation':captured_call,
                   'http_witness':witnesses[0], 'eligible_after':max(captured_call['completed_at'], witnesses[0]['completed_at'])+7*86400+1,
                   'source_read_only':True, 'dates_unchanged':True, 'image':current['Image']}
        observer.detach()
        emit({'event':'control-resumed-after-capture', 'capture_id':capture.name})
        deadline = time.monotonic()+45
        while True:
            live = durable()
            settled = next(v for v in live['firings'] if v['id']==captured_firing['id'])
            if settled['state']=='succeeded' and settled['completed_at'] is not None and not reader.rows('SELECT id FROM execution_instances'):
                break
            assert time.monotonic()<deadline, 'capture_source_not_settled_after_resume'
            time.sleep(.1)
        assert len([v for v in live['invocations'] if v['schedule_slot']==window])==1, 'capture_source_replayed'
        artifact_root = control.parent/'artifacts'
        def inventory(directory):
            result = {}
            for path in sorted(directory.rglob('*')):
                info = path.lstat()
                assert stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'capture_artifact_type'
                if stat.S_ISREG(info.st_mode):
                    result[str(path.relative_to(directory))]={'sha256':sha(path), 'bytes':info.st_size, 'mode':stat.S_IMODE(info.st_mode)}
            return result
        before_artifacts = inventory(artifact_root)
        assert shutil.disk_usage(capture).free > sum(v['bytes'] for v in before_artifacts.values())*2+1024**3, 'capture_disk_margin_required'
        if capture_loss == 'artifact-copy':
            assert len(before_artifacts) > 1, 'multiple_artifacts_required_for_fault'
            def incomplete_artifact_copy(source_path, destination_path):
                copied_path = shutil.copy2(source_path, destination_path)
                relative = str(Path(source_path).relative_to(artifact_root))
                info = Path(destination_path).stat()
                observed = {'sha256':sha(destination_path), 'bytes':info.st_size,
                            'mode':stat.S_IMODE(info.st_mode)}
                assert observed == before_artifacts[relative], 'copied_fault_artifact_changed'
                copied_files = sum(1 for path in (capture/'artifacts').rglob('*') if path.is_file())
                assert 0 < copied_files < len(before_artifacts), 'incomplete_artifact_tree_required'
                # This first real copy must suspend; resuming is always an error.
                pause_incomplete_copy({'copied_files':copied_files, 'expected_files':len(before_artifacts),
                                       'file':{'path':relative, **observed},
                                       'source_inventory_sha256':hashlib.sha256(json.dumps(before_artifacts,sort_keys=True).encode()).hexdigest(),
                                       'control_backup_sha256':sha(snapshot), 'backup_complete':True,
                                       'artifact_copy_complete':False})
                return copied_path
            shutil.copytree(artifact_root, capture/'artifacts', copy_function=incomplete_artifact_copy)
        else:
            shutil.copytree(artifact_root, capture/'artifacts', copy_function=shutil.copy2)
        assert inventory(artifact_root)==before_artifacts==inventory(capture/'artifacts'), 'capture_artifacts_changed'
        with control_owner(control), closing(sqlite3.connect('file:'+str(registry)+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(capture/'registry.sqlite3')) as destination:
            assert source.execute('SELECT count(*) FROM leases').fetchone()[0]==0, 'capture_registry_must_be_quiet'
            source.backup(destination)
            assert destination.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        os.chmod(capture/'registry.sqlite3', 0o600)
        receipt.update(registry_sha256=sha(capture/'registry.sqlite3'), artifact_files=len(before_artifacts),
                       artifact_inventory_sha256=hashlib.sha256(json.dumps(before_artifacts,sort_keys=True).encode()).hexdigest(),
                       completed_after_resume=settled, private_capture_preserved=True)
        (capture/'artifacts.json').write_text(json.dumps(before_artifacts,sort_keys=True)+'\n')
        (capture/'capture.json').write_text(json.dumps(receipt)+'\n')
        os.chmod(capture/'artifacts.json',0o600);os.chmod(capture/'capture.json',0o600)
        emit(receipt)
        raise SystemExit(0)
    assert select.select([sys.stdin], [], [], 8)[0] and sys.stdin.readline().strip() == 'cut', 'cut_command_required'
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        (folder/'kill-started.json').write_text(json.dumps({'requested':True})+'\n')
        os.chmod(folder/'kill-started.json', 0o600)
        stopped = subprocess.Popen(['/usr/bin/python3', '-I', str(folder/'kill.py'), str(folder), str(lock)], pass_fds=(lock,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end = time.monotonic()+10
        while True:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited:
                assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL, 'control_death_unconfirmed'
                observer.attached = False
                break
            assert time.monotonic() < end, 'control_death_not_observed'
            time.sleep(.01)
        stopped.communicate(timeout=40)
        assert stopped.returncode == 0
        killed = json.loads(command(docker+['inspect', current['Id']]))[0]
        assert not killed['State']['Running'] and killed['State']['ExitCode'] == 137
        after_death = checkpoint()
        assert after_death == gated, 'claimed_state_changed_after_crash'
        emit({'event':'cut', 'exit_code':137, 'checkpoint':after_death, 'durable':durable()})
    finally:
        if 'stopped' in locals():
            stopped.communicate(timeout=50)
            assert stopped.poll() is not None
        fcntl.flock(lock, fcntl.LOCK_UN)
    if mode == 'before':
        for boundary in (window, window+300, window+600):
            while time.time() < boundary+1:
                assert not select.select([sys.stdin], [], [], .25)[0], 'unexpected_input_during_downtime'
            state = json.loads(command(docker+['inspect', current['Id']]))[0]
            assert not state['State']['Running'] and state['State']['ExitCode'] == 137
            assert checkpoint() == gated
            emit({'event':'missed-boundary', 'window':boundary, 'control_stopped':True})
        while time.time() < window+605:
            time.sleep(.05)
finally:
    observer.detach()
    if armed:
        emit(json.loads(command(['/usr/bin/python3', '-I', str(folder/'restore.py'), str(folder)], timeout=190)))
        emit({'event':'guard-finished', 'unit':unit, 'states':finish_guard(unit)})
    reader.close()
    os.close(lock)
