# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#discriminant-retenu
"""Observe three committed retention sets in an owned real DEV window."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import time
from uuid import UUID

from control_database import ControlObserver
from schedule_firing_volume_replay import BlockingNativeObserver, atomic

ROOT = Path('/srv/p2enjoy-serverless')
FIELDS = '''id,function_id,revision_id,instance_id,state,error_code,http_status,
    handler_started,completed_at,logs,trigger,resolved_code_hash,schedule_firing_id,schedule_slot'''


def traced_process(pid):
    process = Path('/proc', str(pid))
    birth = process.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19]
    status = process.joinpath('status').read_text().splitlines()
    tracer = int(next(line.split(':', 1)[1] for line in status if line.startswith('TracerPid:')))
    assert process.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19] == birth
    return {'pid': pid, 'birth': birth, 'tracer_pid': tracer}


def observe(args, receipt, target):
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    assert str(UUID(args.campaign)) == args.campaign
    ids = args.functions.split(',')
    assert len(ids) == len(set(ids)) == 2 and all(str(UUID(v)) == v for v in ids)
    assert args.window % 300 == 0 and -2 <= time.time() - args.window <= 2, 'near_real_window_required'
    work = ROOT / 'qualification-history' / ('instance-limit-' + args.campaign)
    info = work.lstat()
    assert work.resolve() == work and stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o750
    item = json.loads((work / 'restore.json').read_text())
    assert item['campaign'] == args.campaign and item['mode'] == 'instance-limit' and not item.get('restored')
    assert item['guard_seconds'] == 2700 and not item.get('firing_replay')
    assert info.st_gid == item['gid'], 'window_group_identity_changed'
    lock = os.fstat(args.lock_fd)
    assert [lock.st_dev, lock.st_ino] == item['lock_identity'] and lock.st_uid == 0 and stat.S_IMODE(lock.st_mode) == 0o600
    fcntl.flock(args.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    spec = importlib.util.spec_from_file_location('owned_window', ROOT / 'e2e/storage-legacy-environment.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.hashes() == item['configuration'], 'official_configuration_changed'
    assert not helper.container(item, item['original']['id'])['running'], 'original_control_must_be_stopped'
    assert item['temporary_installation'] != item['installation']
    for name, path in item['paths'].items():
        assert helper.same(path, item['replacement_dirs'][name]) and not helper.same(path, item['original_dirs'][name])
    current = helper.container(item, helper.temporary_control_name(item))
    assert current['running'] and current['image'] == item['original']['image']
    definition = json.loads(subprocess.check_output(item['docker'] + ['inspect', current['id']], text=True, timeout=10))[0]
    assert definition['Config']['Labels']['com.docker.compose.project'] == item['project']
    init = definition['State']['Pid']
    descendants = [init]
    for parent in descendants:
        descendants.extend(int(v) for v in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
    processes = [p for p in descendants if Path(os.readlink(f'/proc/{p}/exe')).name.startswith('python')
                 and Path('/proc', str(p), 'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
    assert len(processes) == 1, 'unique_control_process_required'
    pid = processes[0]
    assert Path('/proc', str(pid), 'cgroup').read_text() == Path('/proc', str(init), 'cgroup').read_text()
    birth = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
    control = Path(item['paths']['state']) / 'control.sqlite3'
    reader, observer = ControlObserver(control), None
    def calls():
        return reader.rows('SELECT ' + FIELDS + ' FROM invocations ORDER BY id')
    def firing():
        rows = reader.rows('SELECT * FROM schedule_firings WHERE function_id=? AND window_at=?', (ids[1], args.window))
        assert len(rows) <= 1, 'unexpected_firings'
        return rows[0] if rows else None
    def state():
        return {'invocations': calls(), 'firing': firing()}
    def ordered(rows):
        return sorted(rows, key=lambda v: (v['completed_at'], v['id']), reverse=True)
    def ids_of(rows):
        return sorted(v['id'] for v in rows)
    try:
        reader.open()
        namespaces = reader.rows('SELECT name FROM namespaces WHERE deleted_at IS NULL')
        assert len(namespaces) == 1 and namespaces[0]['name'] == item['namespace_name'], 'foreign_namespace'
        functions = reader.rows('SELECT id FROM functions WHERE deleted_at IS NULL ORDER BY id')
        assert [v['id'] for v in functions] == sorted(ids), 'unexpected_functions'
        running_deadline = time.monotonic() + 5
        while True:
            active = reader.rows('SELECT id,function_id,state,handler_started,completed_at,trigger FROM invocations WHERE completed_at IS NULL ORDER BY id')
            assert all(v['completed_at'] is None for v in active)
            if len(active) == 2 and {v['function_id'] for v in active} == set(ids) and all(v['handler_started'] and v['state'] == 'running' for v in active):
                break
            assert time.monotonic() < running_deadline and time.time() < args.window + 2.8, 'two_running_handlers_frontier_missed'
            time.sleep(.01)
        receipt.update(campaign=args.campaign, window=args.window, pid=pid, birth=birth,
                       container_id=current['id'], image=current['image'], running=active,
                       inherited_guard_lock=True, operator=traced_process(os.getpid()))
        observer = BlockingNativeObserver(pid)
        observer.start()
        attached = traced_process(pid)
        receipt['after_attach'] = attached
        assert attached['birth'] == birth and attached['tracer_pid'] == os.getpid(), 'native_tracer_identity_changed'
        initial = state()
        receipt['initial'] = initial
        receipt['initial_counts'] = {'total': len(initial['invocations']),
                                     'terminal': sum(v['completed_at'] is not None for v in initial['invocations'])}
        atomic(target, receipt)
        # @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#pannes-propres-de-lalarme35-et-de-la-commande40
        if args.deadline_fault:
            from source_observer_deadlines import arm
            arm(args.campaign, args.deadline_fault, receipt, target, observer)
        assert receipt['initial_counts'] == {'total': 10002, 'terminal': 10000}, 'retention_history_incomplete'
        assert initial['firing'] and initial['firing']['state'] == 'dispatched' and initial['firing']['completed_at'] is None
        source_id = initial['firing']['invocation_id']
        assert source_id in {v['id'] for v in active if v['trigger'] == 'schedule' and v['function_id'] == ids[1]}
        receipt['initial'] = initial
        atomic(target, receipt)
        before = protected = None
        deadline = time.monotonic() + 25
        pending = None
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
            if pending in (3, 72, 75) and phase in (1, 2):
                counts = reader.rows('SELECT count(*) AS total,sum(completed_at IS NOT NULL) AS terminal FROM invocations')[0]
                fire = firing()
                assert fire and fire['invocation_id'] == source_id
                if counts['terminal'] == 10002 and before is None:
                    assert fire['completed_at'] is None, 'source_closed_before_first_frontier'
                    before = state()
                    assert all(v['state'] == 'succeeded' and v['handler_started'] for v in before['invocations'])
                    receipt['before'] = before
                    atomic(target, receipt)
                elif before is not None and protected is None and counts['total'] == 10001:
                    assert fire['completed_at'] is None, 'source_closed_before_protected_gc'
                    protected = state()
                    ordinary = ordered([v for v in before['invocations'] if v['id'] != source_id])
                    assert ids_of(protected['invocations']) == sorted([source_id] + [v['id'] for v in ordinary[:10000]]), 'wrong_protected_survivors'
                    assert protected['firing'] == before['firing'], 'unclosed_firing_changed'
                    receipt['protected'] = protected
                    receipt['removed_while_protected'] = ordinary[-1]['id']
                    atomic(target, receipt)
                elif protected is not None and counts['total'] == 10000 and fire['completed_at'] is not None:
                    final = state()
                    assert ids_of(final['invocations']) == ids_of(ordered(before['invocations'])[:10000]), 'wrong_closed_survivors'
                    original_source = next(v for v in before['invocations'] if v['id'] == source_id)
                    assert next(v for v in final['invocations'] if v['id'] == source_id) == original_source, 'source_changed'
                    assert fire['state'] == 'succeeded' and fire['id'] == before['firing']['id']
                    receipt.update(final=final, removed_after_close=ordinary[-2]['id'], completed=True,
                                   observation_seconds=25-(deadline-time.monotonic()))
                    atomic(target, receipt)
                    return receipt
                elif counts['total'] < 10002 and before is None:
                    raise AssertionError('first_terminal_frontier_missed')
                elif counts['total'] < 10001 and protected is None:
                    raise AssertionError('protected_gc_frontier_missed')
            observer.resume()
    except BaseException as error:
        receipt['primary_failure'] = {'type': type(error).__name__,
            'reason': str(error) if isinstance(error, (AssertionError, TimeoutError)) else None}
        if receipt.get('inherited_guard_lock'):
            atomic(target, receipt)
        raise
    finally:
        try:
            try:
                if observer:
                    entered = time.monotonic()
                    receipt['detach_started_monotonic'] = entered
                    receipt['detach_signal_mask_before'] = sorted(int(v) for v in signal.pthread_sigmask(signal.SIG_BLOCK,set()))
                    try:
                        observer.detach()
                    except BaseException as error:
                        receipt.setdefault('cleanup_errors', []).append({'step': 'detach', 'type': type(error).__name__,
                            'reason': str(error) if isinstance(error, (AssertionError, TimeoutError)) else None,
                            'entered_monotonic': entered, 'finished_monotonic': time.monotonic(),
                            'duration': time.monotonic()-entered})
                        raise
                    finally:
                        receipt['detach_signal_mask_after'] = sorted(int(v) for v in signal.pthread_sigmask(signal.SIG_BLOCK,set()))
            finally:
                if receipt.get('inherited_guard_lock'):
                    try:
                        detached = traced_process(pid)
                        receipt['after_detach'] = detached
                        receipt['observer_memory_closed'] = observer is None or observer.memory is None
                        assert detached['birth'] == birth and detached['tracer_pid'] == 0, 'native_tracer_retained'
                        assert receipt['observer_memory_closed'], 'native_memory_descriptor_retained'
                    except BaseException as error:
                        receipt.setdefault('cleanup_errors', []).append({'step': 'detach-state', 'type': type(error).__name__,
                            'reason': str(error) if isinstance(error, (AssertionError, TimeoutError)) else None})
                        raise
        finally:
            try:
                try:
                    reader.close()
                except BaseException as error:
                    receipt.setdefault('cleanup_errors', []).append({'step': 'reader', 'type': type(error).__name__})
                    raise
                receipt['reader_closed'] = reader.db is None
            finally:
                if receipt.get('inherited_guard_lock'):
                    atomic(target, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign')
    parser.add_argument('functions')
    parser.add_argument('window', type=int)
    parser.add_argument('--lock-fd', type=int, required=True)
    parser.add_argument('--deadline-fault', choices=('global-alarm', 'command-timeout', 'detach-failure'))
    args = parser.parse_args()
    receipt = {'completed': False}
    target = ROOT / 'qualification-history' / ('instance-limit-' + args.campaign) / 'source-retention-observation.json'
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('native_observation_deadline')))
    signal.alarm(35)
    receipt['global_alarm_started_monotonic'] = time.monotonic()
    try:
        print(json.dumps(observe(args, receipt, target)))
    except BaseException as error:
        receipt.update(completed=False, failure_type=type(error).__name__,
                       reason=str(error) if isinstance(error, (AssertionError, TimeoutError)) else None)
        # Only an already validated window may receive a diagnostic file.
        if receipt.get('inherited_guard_lock'):
            atomic(target, receipt)
        print(json.dumps(receipt))
        raise SystemExit(1)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
