# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#chargement-gardé-de-la-copie
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#observation-du-replay-et-preuves-propres
"""Verify, copy and observe a sealed real DEV installation without editing rows."""
import argparse
from contextlib import closing
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import time
from uuid import UUID

from control_database import ControlObserver, read_control
from native_control_observer import NativeObserver

ROOT = Path('/srv/p2enjoy-serverless')
HISTORY = ROOT / 'qualification-history'
MODULE = Path(__file__)


class BlockingNativeObserver(NativeObserver):
    """Wait for real child notifications with a monotonic deadline, without polling."""
    # @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#dépassement-reproduit-et-décision-de-correction
    def wait(self, deadline):
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        try:
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGCHLD})
            while True:
                assert time.monotonic() < deadline, 'native_stop_not_observed'
                waited, status = os.waitpid(self.pid, os.WNOHANG)
                if waited:
                    assert os.WIFSTOPPED(status), 'control_exited_during_observation'
                    self.stopped = True
                    assert time.monotonic() < deadline, 'native_stop_not_observed'
                    return os.WSTOPSIG(status)
                remaining = deadline-time.monotonic()
                assert remaining > 0, 'native_stop_not_observed'
                # Blocking SIGCHLD before waitpid avoids losing a stop between
                # the status check and sigtimedwait. Other children only wake
                # this loop; their statuses never stand in for this control.
                signal.sigtimedwait({signal.SIGCHLD}, remaining)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def atomic(path, value):
    pending = path.with_suffix('.pending')
    with open(pending, 'w', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def snapshot_module():
    spec = importlib.util.spec_from_file_location('firing_volume_snapshot', ROOT / 'e2e/schedule-firing-volume-snapshot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sealed_file(path):
    info = path.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o400, 'sealed_file_required'
    assert path.resolve() == path, 'canonical_sealed_file_required'


def immutable(path):
    sealed_file(path)
    assert all(not os.path.lexists(str(path) + suffix) for suffix in ('-wal', '-shm', '-journal')), 'sealed_sidecar_present'
    db = sqlite3.connect('file:' + str(path) + '?mode=ro&immutable=1', uri=True, isolation_level=None)
    db.row_factory = sqlite3.Row
    return db


def verify_capture(identifier):
    assert re.fullmatch('schedule-firing-volume-[a-f0-9]{32}', identifier), 'canonical_capture_required'
    folder = HISTORY / identifier
    info = folder.lstat()
    assert folder.resolve() == folder and stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700, 'private_capture_required'
    sealed_file(folder / 'capture.json')
    receipt = json.loads((folder / 'capture.json').read_text())
    evidence = ROOT / 'docs/evidence/schedule-firing-volume-capture-dev-2026-11-11.json'
    public = json.loads(evidence.read_text())
    assert public['completed'] and public['capture_qualified'] and receipt == public['receipt'], 'known_capture_required'
    assert receipt['completed'] and receipt['capture_id'] == identifier and receipt['source_read_only'] and receipt['dates_unchanged']
    witness = receipt['witnesses']
    installation = witness['installation_id']
    assert str(UUID(installation)) == installation
    ids = [v['id'] for v in witness['functions']]
    assert len(ids) == len(set(ids)) == 16
    namespace = witness['namespace']['name']
    assert re.fullmatch('instance-limit-[a-f0-9]{8}', namespace)
    snapshot = snapshot_module()
    assert sha(folder / 'control.sqlite3') == receipt['backup_sha256']
    with closing(immutable(folder / 'control.sqlite3')) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert snapshot.witnesses(db, ids, witness['cursor'], namespace, installation) == witness
    assert sha(folder / 'registry.sqlite3') == receipt['registry_sha256']
    with closing(immutable(folder / 'registry.sqlite3')) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        for query in ['SELECT count(*) FROM leases', 'SELECT count(*) FROM probes',
                      "SELECT count(*) FROM volumes WHERE phase!='unmounted'",
                      'SELECT count(*) FROM functions WHERE pending_json IS NOT NULL']:
            assert db.execute(query).fetchone()[0] == 0, 'sealed_registry_not_quiet'
    sealed_file(folder / 'artifacts.json')
    assert (folder / 'artifacts').is_dir() and (folder / 'artifacts').resolve() == folder / 'artifacts'
    inventory = json.loads((folder / 'artifacts.json').read_text())
    assert snapshot.inventory(folder / 'artifacts') == inventory
    assert len(inventory) == receipt['artifact_files']
    assert hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest() == receipt['artifact_inventory_sha256']
    image_folder = HISTORY / receipt['image_capture_id']
    assert re.fullmatch('schedule-retention-[a-f0-9]{32}', image_folder.name) and image_folder.resolve() == image_folder
    assert json.loads((image_folder / 'preservation.json').read_text())['images'] == receipt['images']
    for role, row in receipt['images'].items():
        path = image_folder / (role + '-image.tar')
        sealed_file(path)
        assert path.stat().st_size == row['bytes'] and sha(path) == row['archive_sha256']
    return {'capture_id': identifier, 'receipt_sha256': sha(folder / 'capture.json'),
            'public_evidence_sha256': sha(evidence), 'control_sha256': receipt['backup_sha256'],
            'registry_sha256': receipt['registry_sha256'], 'artifact_inventory_sha256': receipt['artifact_inventory_sha256'],
            'artifact_files': len(inventory), 'namespace_name': namespace,
            'namespace_id': witness['namespace']['id'], 'installation_id': installation,
            'function_ids': ids, 'cursor': witness['cursor'], 'initial_firings': 256,
            'declarations_per_window': 256, 'eligible_after': receipt['eligible_after'],
            'oldest_completed_at': min(v['completed_at'] for v in witness['firings']),
            'images': receipt['images'], 'image_capture_id': receipt['image_capture_id']}


def timing(source, mode):
    now = time.time()
    boundary = int(now // 300) * 300
    missed = (boundary - source['cursor']) // 300
    assert source['oldest_completed_at'] > now - 604700, 'capture_too_old_for_numeric_proof'
    if mode == 'preflight':
        assert 1 <= missed <= 38, 'preflight_requires_below_count_limit'
    elif mode == 'count':
        assert missed >= 39, 'numeric_replay_not_yet_eligible'
    return boundary, missed


def window(campaign, fd):
    assert str(UUID(campaign)) == campaign
    work = HISTORY / ('instance-limit-' + campaign)
    item = json.loads((work / 'restore.json').read_text())
    assert item['campaign'] == campaign and item['mode'] == 'instance-limit' and not item.get('restored')
    lock = os.fstat(fd)
    assert [lock.st_dev, lock.st_ino] == item['lock_identity'] and lock.st_uid == 0 and stat.S_IMODE(lock.st_mode) == 0o600
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for name, directory in item['paths'].items():
        assert snapshot_module().identity(Path(directory)) == item['replacement_dirs'][name]
        assert item['replacement_dirs'][name] != item['original_dirs'][name]
    source = verify_capture(item['firing_replay']['source']['capture_id'])
    assert source == item['firing_replay']['source'], 'capture_changed_since_preflight'
    assert item['namespace_name'] == source['namespace_name'] and item['temporary_installation'] == source['installation_id']
    assert source['installation_id'] != item['installation']
    return work, item, source


def kill_pair(item, receipt_path, receipt):
    receipt.update(fault_signal='SIGKILL', driver_killed=True)
    pid = item['driver_pid']
    status = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    assert status[19] == item['driver_birth'] and status[0] != 'Z', 'driver_identity_changed'
    atomic(receipt_path, receipt)
    fd = os.pidfd_open(pid)
    try:
        signal.pidfd_send_signal(fd, signal.SIGKILL)
    finally:
        os.close(fd)
    os.kill(os.getpid(), signal.SIGKILL)


def seed(campaign, fd):
    work, item, source = window(campaign, fd)
    assert not Path(item['paths']['state'], 'control.sqlite3').exists()
    folder = HISTORY / source['capture_id']
    artifacts = Path(item['paths']['state']) / 'artifacts'
    assert not artifacts.exists()
    shutil.copytree(folder / 'artifacts', artifacts, copy_function=shutil.copy2)
    for path in [artifacts, *artifacts.rglob('*')]:
        os.chown(path, item['uid'], item['gid'], follow_symlinks=False)
    assert snapshot_module().inventory(artifacts) == json.loads((folder / 'artifacts.json').read_text())
    def publish(name, target, expected):
        assert not target.exists()
        pending = target.with_suffix('.replay-pending')
        assert not pending.exists()
        with (folder / name).open('rb') as original, pending.open('xb') as output:
            shutil.copyfileobj(original, output)
            output.flush()
            os.fsync(output.fileno())
            os.fchown(output.fileno(), item['uid'], item['gid'])
            os.fchmod(output.fileno(), 0o600)
        assert sha(pending) == expected
        pending.replace(target)
        directory = os.open(target.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    publish('registry.sqlite3', Path(item['paths']['storage']) / 'registry.sqlite3', source['registry_sha256'])
    receipt = {'completed': False, 'artifacts_verified': True, 'registry_published': True,
               'control_published': False, 'source_unchanged': True, 'inherited_guard_lock': True,
               'capture_id': source['capture_id'], 'campaign': campaign, 'sampled_at': time.time()}
    path = work / 'firing-replay-seed.json'
    atomic(path, receipt)
    if item['firing_replay']['mode'] == 'seed-loss':
        kill_pair(item, path, receipt)
    publish('control.sqlite3', Path(item['paths']['state']) / 'control.sqlite3', source['control_sha256'])
    receipt.update(completed=True, control_published=True)
    assert verify_capture(source['capture_id']) == source
    atomic(path, receipt)
    return receipt


def observe(campaign, fd):
    work, item, source = window(campaign, fd)
    mode = item['firing_replay']['mode']
    boundary, missed = timing(source, mode)
    assert boundary == item['firing_replay']['armed_boundary'], 'replay_boundary_changed_since_arm'
    assert 10 <= item['firing_replay']['armed_at'] - boundary <= 120
    assert 10 <= time.time() - boundary <= 150, 'replay_start_window_margin'
    control = Path(item['paths']['state']) / 'control.sqlite3'
    reader = ControlObserver(control)
    observer = None
    receipt = {'completed': False, 'mode': mode, 'source_capture': source['capture_id'],
               'start_boundary': boundary, 'missed_windows': missed, 'inherited_guard_lock': True}
    result_path = work / 'firing-replay-observation.json'
    def command(*args):
        return subprocess.check_output(item['docker'] + list(args), text=True, stderr=subprocess.PIPE, timeout=20)
    def sample(full=False):
        cursor = reader.rows('SELECT window_at FROM schedule_cursor WHERE singleton=1')[0]['window_at']
        count = reader.rows('SELECT count(*) AS n FROM schedule_firings')[0]['n']
        value = {'cursor': cursor, 'count': count}
        if full:
            value['firings'] = reader.rows('SELECT * FROM schedule_firings ORDER BY id')
            value['invocations'] = reader.rows('''SELECT id,function_id,revision_id,resolved_code_hash,state,error_code,
                http_status,handler_started,instance_id,completed_at,logs,trigger,
                schedule_firing_id,schedule_expression,schedule_origin,schedule_slot FROM invocations ORDER BY id''')
        return value
    initial = json.loads((HISTORY / source['capture_id'] / 'capture.json').read_text())['witnesses']
    generations = {v['function_id']: v for v in initial['generations']}
    def check_rows(value):
        assert value['invocations'] == initial['invocations'], 'unexpected_invocation_during_recovery'
        original = {v['id']: v for v in initial['firings']}
        assert len(value['firings']) == value['count']
        for firing in value['firings']:
            if firing['id'] in original:
                assert firing == original[firing['id']], 'captured_firing_changed'
            else:
                assert firing['state'] == 'skipped_downtime' and firing['completed_at'] and firing['invocation_id'] is None
                assert firing['function_id'] in source['function_ids'] and 0 <= firing['schedule_index'] < 16
                generation = generations[firing['function_id']]
                assert firing['generation_id'] == generation['id'] and firing['code_hash'] == generation['code_hash']
                assert firing['expression'] == '*/5 * * * *' and firing['origin'] == 'manifest' and firing['coalesced'] == 1
                assert source['cursor'] < firing['window_at'] <= value['cursor'] and firing['nominal_at'] == firing['window_at']
                assert boundary <= firing['claimed_at'] <= firing['completed_at'] <= time.time() and firing['error_code'] is None
        assert all(any(v['id'] == key for v in value['firings']) for key in original)
        for window_at in range(source['cursor'], value['cursor'] + 1, 300):
            rows = [v for v in value['firings'] if v['window_at'] == window_at]
            assert len(rows) == 256, 'incomplete_recovered_window'
            for identifier in source['function_ids']:
                assert {v['schedule_index'] for v in rows if v['function_id'] == identifier} == set(range(16))
        assert all(sum(v['function_id'] == identifier for v in value['firings']) < 10000 for identifier in source['function_ids'])
    try:
        reader.open()
        command('compose', '--env-file', '/etc/spark/env', '--env-file', '/run/spark/secrets',
                '-f', str(work / 'compose.yml'), 'up', '-d', '--no-build')
        definitions = json.loads(command('inspect', 'serverless-api-instance-limit'))
        row = definitions[0]
        assert row['State']['Running'] and row['Image'] == source['images']['control']['image']
        assert row['Config']['Labels']['com.docker.compose.project'] == item['project']
        init = row['State']['Pid']
        find_deadline = time.monotonic() + 3
        while True:
            descendants = [init]
            processes = []
            try:
                for parent in descendants:
                    descendants.extend(int(v) for v in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
                processes = [p for p in descendants if Path(os.readlink(f'/proc/{p}/exe')).name.startswith('python')
                             and Path('/proc', str(p), 'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
            except (FileNotFoundError, ProcessLookupError):
                pass
            assert len(processes) <= 1, 'unique_control_process_required'
            if processes:
                break
            assert time.monotonic() < find_deadline, 'control_process_missing'
            time.sleep(.01)
        pid = processes[0]
        cgroup = Path('/proc', str(pid), 'cgroup').read_text()
        assert cgroup == Path('/proc', str(init), 'cgroup').read_text(), 'controller_cgroup_mismatch'
        birth = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        observer = BlockingNativeObserver(pid)
        observer.start()
        assert Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19] == birth
        receipt.update(container_id=row['Id'], image=row['Image'], init_pid=init, pid=pid, birth=birth,
                       cgroup_sha256=hashlib.sha256(cgroup.encode()).hexdigest(),
                       observer_attached=True, native_stop=observer.stopped)
        atomic(result_path, receipt)
        if mode == 'observer-loss':
            kill_pair(item, result_path, receipt)
        wanted_windows = missed if mode == 'preflight' else min(missed, 40)
        wanted_cursor = source['cursor'] + wanted_windows * 300
        expected_before = 256 * (1 + wanted_windows)
        pending = None
        deadline = time.monotonic() + 25
        before = None
        initial_stop = sample()
        receipt['initial_stop'] = initial_stop
        assert initial_stop['cursor'] <= wanted_cursor, 'recovery_frontier_already_passed'
        near_end = initial_stop['cursor'] >= wanted_cursor - 300
        if initial_stop['cursor'] == wanted_cursor:
            assert initial_stop['count'] == expected_before, 'before_retention_frontier_missed'
            before = sample(full=True)
            check_rows(before)
            receipt['before'] = before
            atomic(result_path, receipt)
            if mode == 'preflight':
                assert time.monotonic() < deadline, 'native_observation_deadline'
                receipt.update(completed=True, count_retention_qualified=False, observed_at=time.time(),
                               observation_seconds=25-(deadline-time.monotonic()))
                atomic(result_path, receipt)
                return receipt
        observer.resume()
        while True:
            stopped = observer.wait(deadline)
            if stopped != signal.SIGTRAP | 0x80:
                assert stopped not in (signal.SIGSTOP, signal.SIGTRAP)
                observer.resume(stopped)
                continue
            phase, data = observer.info()
            if phase == 1:
                pending = data[0]
            eligible = pending == 75 or (before is not None and pending in (3, 72)) or (mode == 'preflight' and near_end and pending == 3)
            if eligible and phase in (1, 2):
                value = sample()
                near_end = value['cursor'] >= wanted_cursor - 300
                assert value['cursor'] <= wanted_cursor, 'recovery_frontier_already_passed'
                if before is None and value['cursor'] == wanted_cursor:
                    assert value['count'] == expected_before, 'before_retention_frontier_missed'
                    before = sample(full=True)
                    check_rows(before)
                    receipt['before'] = before
                    atomic(result_path, receipt)
                    if mode == 'preflight':
                        break
                elif before is not None and value['cursor'] == wanted_cursor and value['count'] == 10000:
                    actual = reader.rows('SELECT id FROM schedule_firings ORDER BY id')
                    ordered = sorted(before['firings'], key=lambda v: (v['completed_at'], v['id']), reverse=True)
                    assert [v['id'] for v in actual] == sorted(v['id'] for v in ordered[:10000]), 'wrong_count_survivors'
                    assert sample()['cursor'] == wanted_cursor
                    receipt['after'] = {'cursor': wanted_cursor, 'count': 10000, 'ids': [v['id'] for v in actual],
                                        'removed_ids': [v['id'] for v in ordered[10000:]]}
                    break
            observer.resume()
        assert time.time() < boundary + 270, 'replay_next_window_too_close'
        assert time.monotonic() < deadline, 'native_observation_deadline'
        receipt.update(completed=True, count_retention_qualified=mode == 'count', observed_at=time.time(),
                       observation_seconds=25-(deadline-time.monotonic()))
        atomic(result_path, receipt)
        return receipt
    finally:
        if observer:
            observer.detach()
        reader.close()


def inspect_replay(campaign, fd):
    _, item, source = window(campaign, fd)
    with read_control(Path(item['paths']['state']) / 'control.sqlite3') as db:
        db.execute('BEGIN')
        cursor = db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
        rows = [dict(v) for v in db.execute('SELECT * FROM schedule_firings ORDER BY id')]
        calls = [dict(v) for v in db.execute('SELECT id,function_id,state,handler_started,completed_at FROM invocations ORDER BY id')]
        generations = [dict(v) for v in db.execute('SELECT * FROM schedule_generations ORDER BY id')]
        assert db.execute('SELECT count(*) FROM execution_instances').fetchone()[0] == 0
    assert len(calls) == 2 and all(v['state'] == 'succeeded' and v['handler_started'] for v in calls)
    assert len(generations) == 16 and all(v['retired_at'] is None for v in generations)
    assert {v['function_id'] for v in generations} == set(source['function_ids'])
    return {'completed': True, 'cursor': cursor, 'firings': rows, 'invocations': calls, 'generations': generations}


def main():
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['verify', 'seed', 'observe', 'inspect'])
    parser.add_argument('identifier')
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('replay_native_deadline')))
    signal.alarm(35)
    try:
        if args.operation == 'verify':
            result = verify_capture(args.identifier)
        else:
            assert args.lock_fd is not None
            result = {'seed': seed, 'observe': observe, 'inspect': inspect_replay}[args.operation](args.identifier, args.lock_fd)
        print(json.dumps(result))
        signal.alarm(0)
    except BaseException as error:
        trace=error.__traceback__
        source_line=None
        while trace is not None:
            if Path(trace.tb_frame.f_code.co_filename)==MODULE:
                source_line=trace.tb_lineno
            trace=trace.tb_next
        print(json.dumps({'completed': False, 'failure_type': type(error).__name__,
                          'source_line':source_line,'reason': str(error) if isinstance(error, AssertionError) else None}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
