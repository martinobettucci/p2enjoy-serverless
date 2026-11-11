# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#mesure-de-lattente-native-sans-événement
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#mesure-de-lattente-native-sans-événement
"""Measure the shared kernel wait against a genuinely frozen DEV control."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
from uuid import UUID

ROOT = Path('/srv/p2enjoy-serverless')
sys.path.insert(0, str(ROOT/'e2e'))
from control_database import ControlObserver
from schedule_firing_volume_replay import BlockingNativeObserver, atomic


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args, timeout=5):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=timeout).strip()


def process(pid):
    root = Path('/proc', str(pid))
    value = root.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    status = root.joinpath('status').read_text().splitlines()
    return {'pid': pid, 'birth': value[19], 'state': value[0],
            'cgroup': root.joinpath('cgroup').read_text(),
            'tracer_pid': int(next(v.split(':', 1)[1] for v in status if v.startswith('TracerPid:')))}


def context(campaign):
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    assert str(UUID(campaign)) == campaign
    work = ROOT/'qualification-history'/('instance-limit-'+campaign)
    info = work.lstat()
    assert work.resolve() == work and stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o750
    item = json.loads((work/'restore.json').read_text())
    assert item['campaign'] == campaign and item['mode'] == 'instance-limit' and item['guard_seconds'] == 120 and not item.get('restored')
    assert not item.get('retention_replay') and not item.get('firing_replay')
    assert info.st_gid == item['gid']
    spec = importlib.util.spec_from_file_location('owned_window', ROOT/'e2e/storage-legacy-environment.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    assert helper.hashes() == item['configuration']
    assert not helper.container(item, item['original']['id'])['running']
    assert item['temporary_installation'] != item['installation']
    for name, path in item['paths'].items():
        assert helper.same(path, item['replacement_dirs'][name]) and not helper.same(path, item['original_dirs'][name])
    return work, item, helper


def definition(item, identifier):
    values = json.loads(command(item['docker']+['inspect', identifier]))
    assert len(values) == 1
    value = values[0]
    assert value['Id'] == identifier and value['Image'] == item['original']['image']
    assert value['Config']['Labels']['com.docker.compose.project'] == item['project'] and value['State']['Running']
    return value


def thaw(campaign):
    work, item, _ = context(campaign)
    identity = json.loads((work/'native-wait-identity.json').read_text())
    assert digest(Path(__file__)) == identity['thaw_source_sha256']
    before = definition(item, identity['container_id'])
    current = process(identity['control']['pid'])
    assert all(current[k] == identity['control'][k] for k in ('pid', 'birth', 'cgroup'))
    if before['State']['Paused']:
        command(item['docker']+['unpause', identity['container_id']])
    after = definition(item, identity['container_id'])
    assert not after['State']['Paused']
    receipt = {'completed': True, 'campaign': campaign, 'actor': process(os.getpid()),
               'container_id': identity['container_id'], 'image': after['Image'],
               'was_paused': before['State']['Paused'], 'paused_after': False,
               'control': process(identity['control']['pid']), 'monotonic': time.monotonic(),
               'source_sha256': digest(Path(__file__)),
               'requested_after_wait': (work/'native-wait-finished.json').exists()}
    atomic(work/'native-wait-thaw.json', receipt)
    print(json.dumps(receipt), flush=True)


def unit_state(unit):
    result = subprocess.run(['systemctl', 'show', unit, '--property=LoadState', '--property=ActiveState',
        '--property=SubState', '--property=MainPID', '--property=Result', '--property=ExecMainCode',
        '--property=ExecMainStatus', '--property=ActiveEnterTimestampMonotonic', '--property=TimersMonotonic'],
        capture_output=True, text=True, timeout=5)
    value = dict(v.split('=', 1) for v in result.stdout.splitlines())
    assert result.returncode == 0 or value.get('LoadState') == 'not-found'
    return value


def measure(args):
    work, item, helper = context(args.campaign)
    lock = os.fstat(args.lock_fd)
    assert [lock.st_dev, lock.st_ino] == item['lock_identity'] and lock.st_uid == 0 and stat.S_IMODE(lock.st_mode) == 0o600
    fcntl.flock(args.lock_fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
    current = helper.container(item, helper.temporary_control_name(item))
    value = definition(item, current['id']); assert not value['State']['Paused']
    init = value['State']['Pid']; descendants = [init]
    for parent in descendants:
        descendants.extend(int(v) for v in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
    candidates = [p for p in descendants if Path(os.readlink('/proc/'+str(p)+'/exe')).name.startswith('python')
                  and Path('/proc', str(p), 'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
    assert len(candidates) == 1
    pid = candidates[0]; original = process(pid)
    assert original['cgroup'] == process(init)['cgroup'] and original['tracer_pid'] == 0
    path = work/'native-wait-observation.json'
    receipt = {'completed': False, 'campaign': args.campaign, 'control': original,
        'container_id': current['id'], 'image': current['image'], 'operator': process(os.getpid()),
        'source_sha256': digest(__file__), 'class_source_sha256': digest(ROOT/'e2e/schedule_firing_volume_replay.py'),
        'class_name': 'schedule_firing_volume_replay.BlockingNativeObserver', 'cleanup_errors': []}
    reader = ControlObserver(Path(item['paths']['state'])/'control.sqlite3'); observer = None; unit = None
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('native_observation_deadline')))
    signal.alarm(35)
    try:
        reader.open()
        assert reader.rows('SELECT count(*) AS n FROM functions WHERE deleted_at IS NULL')[0]['n'] == 0
        assert reader.rows('SELECT count(*) AS n FROM invocations')[0]['n'] == 0
        observer = BlockingNativeObserver(pid); observer.start()
        receipt['after_attach'] = process(pid)
        assert receipt['after_attach']['tracer_pid'] == os.getpid()
        frozen = work/'native-wait-thaw.py'; shutil.copyfile(__file__, frozen); os.chmod(frozen, 0o600)
        atomic(work/'native-wait-identity.json', {'container_id': current['id'], 'control': original,
            'thaw_source_sha256': digest(frozen)})
        unit = 'serverless-native-observer-thaw-'+args.campaign
        command(['systemd-run', '--quiet', '--unit='+unit, '--on-active=28s',
            '--timer-property=AccuracySec=10ms', '--timer-property=RandomizedDelaySec=0',
            '--property=Type=oneshot', '--property=RemainAfterExit=yes', '--property=TimeoutStartSec=10',
            '/usr/bin/python3', '-B', str(frozen), 'thaw', args.campaign])
        timer = unit_state(unit+'.timer'); assert timer['ActiveState'] == 'active'
        activated = int(timer['ActiveEnterTimestampMonotonic'])/1_000_000
        assert activated > 0
        receipt.update(unit=unit, timer_before=timer, thaw_deadline_monotonic=activated+28)
        command(item['docker']+['pause', current['id']]); paused = definition(item, current['id'])
        assert paused['State']['Paused']; receipt['pause_confirmed'] = {'paused': True, 'monotonic': time.monotonic()}
        observer.resume()
        waited, status = os.waitpid(pid, os.WNOHANG)
        receipt['pending_status'] = {'pid': waited, 'status': status}
        if waited:
            observer.stopped = os.WIFSTOPPED(status)
        assert waited == 0, 'native_stop_already_pending'
        entered = time.monotonic(); remaining = signal.getitimer(signal.ITIMER_REAL)[0]
        assert remaining > 30 and activated+28-entered > 26, 'native_wait_setup_margin_exhausted'
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        alarm_handler = signal.getsignal(signal.SIGALRM)
        receipt['wait'] = {'entered_monotonic': entered, 'deadline_monotonic': entered+25,
                           'global_alarm_remaining': remaining, 'returned': False,
                           'signal_mask_before': sorted(int(v) for v in mask),
                           'sigchld_handler_default': signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL}
        atomic(path, receipt)
        try:
            receipt['wait'].update(signal=observer.wait(entered+25), returned=True)
        except BaseException as error:
            receipt['wait'].update(exception={'type': type(error).__name__, 'message': str(error)})
        receipt['wait'].update(finished_monotonic=time.monotonic(), duration=time.monotonic()-entered)
        receipt['wait'].update(signal_mask_after=sorted(int(v) for v in signal.pthread_sigmask(signal.SIG_BLOCK, set())),
            global_alarm_remaining_after=signal.getitimer(signal.ITIMER_REAL)[0],
            alarm_handler_unchanged=signal.getsignal(signal.SIGALRM) is alarm_handler)
        # Persist the primary observation before thaw or detach can fail.
        atomic(work/'native-wait-finished.json', receipt['wait']); atomic(path, receipt)
    except BaseException as error:
        receipt['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        if unit:
            try:
                if not (work/'native-wait-thaw.json').exists():
                    receipt['thaw_requested_monotonic'] = time.monotonic()
                    command(['systemctl', 'start', unit+'.service'], timeout=8)
                thawed = json.loads((work/'native-wait-thaw.json').read_text())
                assert thawed['completed'] and not thawed['paused_after'] and thawed['container_id'] == current['id']
                assert not definition(item, current['id'])['State']['Paused']
                receipt['thaw'] = thawed; receipt['thaw_confirmed_monotonic'] = time.monotonic()
                end = time.monotonic()+5
                while True:
                    terminal = unit_state(unit+'.service')
                    if terminal.get('MainPID', '0') == '0' and terminal['SubState'] in ('exited', 'failed'):
                        break
                    assert time.monotonic() < end, 'thaw_service_not_terminal'
                    time.sleep(.01)
                receipt['thaw_terminal'] = terminal
                atomic(path, receipt)
                assert terminal['MainPID'] == '0' and terminal['SubState'] == 'exited' and terminal['Result'] == 'success' and terminal['ExecMainCode'] == '1' and terminal['ExecMainStatus'] == '0'
            except BaseException as error:
                receipt['cleanup_errors'].append({'step': 'thaw', 'type': type(error).__name__, 'message': str(error)})
            finally:
                try:
                    receipt['thaw_before_stop'] = unit_state(unit+'.service')
                    atomic(path, receipt)
                    command(['systemctl', 'stop', unit+'.timer', unit+'.service'])
                    states = {s: unit_state(unit+'.'+s) for s in ('timer', 'service')}
                    for suffix, state in states.items():
                        if state['ActiveState'] == 'failed':
                            receipt.setdefault('thaw_failed_states', {})[suffix] = state
                            atomic(path, receipt)
                            command(['systemctl', 'reset-failed', unit+'.'+suffix])
                    states = {s: unit_state(unit+'.'+s) for s in ('timer', 'service')}
                    assert all(v['ActiveState'] == 'inactive' and v.get('MainPID', '0') == '0' for v in states.values())
                    receipt['thaw_joined'] = states
                except BaseException as error:
                    receipt['cleanup_errors'].append({'step': 'thaw-join', 'type': type(error).__name__, 'message': str(error)})
        try:
            # Never detach a frozen process: the independent window guard is the fallback.
            if observer and not definition(item, current['id'])['State']['Paused']:
                receipt['detach_started_monotonic'] = time.monotonic(); observer.detach()
                receipt['after_detach'] = process(pid)
                assert receipt['after_detach']['tracer_pid'] == 0
                receipt['memory_closed'] = observer.memory is None
                assert receipt['memory_closed']
        except BaseException as error:
            receipt['cleanup_errors'].append({'step': 'detach', 'type': type(error).__name__, 'message': str(error)})
        try:
            reader.close(); receipt['reader_closed'] = reader.db is None
            assert receipt['reader_closed']
        except BaseException as error:
            receipt['cleanup_errors'].append({'step': 'reader', 'type': type(error).__name__, 'message': str(error)})
        signal.alarm(0)
        receipt['completed'] = 'failure' not in receipt and bool(receipt.get('wait', {}).get('finished_monotonic')) and not receipt['cleanup_errors'] and receipt.get('after_detach', {}).get('tracer_pid') == 0 and receipt.get('memory_closed', False) and receipt.get('reader_closed', False)
        atomic(path, receipt)
    print(json.dumps(receipt), flush=True)
    return receipt['completed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('measure', 'thaw')); parser.add_argument('campaign')
    parser.add_argument('--lock-fd', type=int)
    arguments = parser.parse_args()
    if arguments.operation == 'thaw':
        assert arguments.lock_fd is None; thaw(arguments.campaign)
    else:
        assert arguments.lock_fd is not None; raise SystemExit(0 if measure(arguments) else 1)
