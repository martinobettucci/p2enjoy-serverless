# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#pannes-propres-de-lalarme35-et-de-la-commande40
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#pannes-propres-de-lalarme35-et-de-la-commande40
"""Exercise the real source observer alarm and command cutoff in owned DEV windows."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
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
from schedule_firing_volume_replay import atomic

MODES = ('global-alarm', 'command-timeout')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def process(pid):
    path = Path('/proc', str(pid))
    values = path.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    status = dict(line.split(':', 1) for line in path.joinpath('status').read_text().splitlines() if ':' in line)
    return {'pid': pid, 'birth': values[19], 'parent_pid': int(values[1]), 'state': values[0],
            'cgroup': path.joinpath('cgroup').read_text(), 'tracer_pid': int(status['TracerPid']),
            'pending': int(status['SigPnd'], 16), 'shared_pending': int(status['ShdPnd'], 16),
            'blocked': int(status['SigBlk'], 16),
            'command_sha256': hashlib.sha256(path.joinpath('cmdline').read_bytes()).hexdigest()}


def command(args, timeout=5):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=timeout).strip()


def context(campaign):
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    assert str(UUID(campaign)) == campaign
    work = ROOT/'qualification-history'/('instance-limit-'+campaign)
    info = work.lstat()
    assert work.resolve() == work and info.st_uid == 0 and stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o750
    item = json.loads((work/'restore.json').read_text())
    assert item['campaign'] == campaign and item['mode'] == 'instance-limit' and item['guard_seconds'] == 2700 and not item.get('restored')
    assert info.st_gid == item['gid'] and not item.get('retention_replay') and not item.get('firing_replay')
    spec = importlib.util.spec_from_file_location('owned_window', ROOT/'e2e/storage-legacy-environment.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    assert helper.hashes() == item['configuration'] and not helper.container(item, item['original']['id'])['running']
    assert item['temporary_installation'] != item['installation']
    for name, path in item['paths'].items():
        assert helper.same(path, item['replacement_dirs'][name]) and not helper.same(path, item['original_dirs'][name])
    return work, item, helper


def unit_name(campaign):
    assert str(UUID(campaign)) == campaign
    return 'serverless-source-observer-deadline-'+campaign


def unit_state(unit):
    value = subprocess.run(['systemctl', 'show', unit, '--property=LoadState', '--property=ActiveState',
        '--property=SubState', '--property=MainPID', '--property=Result', '--property=ExecMainCode',
        '--property=ExecMainStatus', '--property=ControlGroup'], capture_output=True, text=True, timeout=5)
    state = dict(line.split('=', 1) for line in value.stdout.splitlines())
    assert value.returncode == 0 or state.get('LoadState') == 'not-found'
    return state


def same_control(item, helper, expected):
    current = helper.container(item, helper.temporary_control_name(item))
    assert current['running'] and current['id'] == expected['container_id'] and current['image'] == item['original']['image']
    native = process(expected['control']['pid'])
    assert all(native[k] == expected['control'][k] for k in ('pid', 'birth', 'cgroup'))
    return native


def arm(campaign, mode, receipt, target):
    """Start a bounded independent actor, persist the actual gate, then SIGSTOP self."""
    assert mode in MODES
    work, item, helper = context(campaign)
    wrapper = json.loads((work/'source-observer-command.json').read_text())
    assert wrapper['mode'] == mode and wrapper['campaign'] == campaign and wrapper['phase'] == 'running'
    own = process(os.getpid()); assert own['parent_pid'] == wrapper['wrapper']['pid']
    assert Path('/proc/self/cmdline').read_bytes() == b'\0'.join(v.encode() for v in wrapper['argv'][5:])+b'\0'
    parent = process(own['parent_pid']); assert parent['birth'] == wrapper['wrapper']['birth']
    control = process(receipt['pid']); assert control['birth'] == receipt['birth'] and control['tracer_pid'] == os.getpid()
    assert receipt['initial_counts'] == {'total': 2, 'terminal': 0} and len(receipt['running']) == 2
    assert all(v['state'] == 'running' and v['handler_started'] and v['completed_at'] is None for v in receipt['running'])
    sampled = time.monotonic(); remaining, interval = signal.getitimer(signal.ITIMER_REAL)
    assert interval == 0 and remaining > 0 and not own['blocked'] & (1 << (signal.SIGALRM-1))
    alarm_deadline = sampled+remaining
    assert wrapper['deadline_monotonic']-(alarm_deadline+.5) >= 2, 'source_deadline_cleanup_margin_missing'
    frozen = work/'source-observer-deadline-actor.py'; shutil.copyfile(__file__, frozen); os.chmod(frozen, 0o600)
    identity = {'campaign': campaign, 'mode': mode, 'operator': own, 'control': control,
        'window': receipt['window'], 'function_ids': sorted(v['function_id'] for v in receipt['running']),
        'container_id': receipt['container_id'], 'image': receipt['image'],
        'operator_source_sha256': sha(ROOT/'e2e/invocation-source-retention-observer.py'),
        'actor_source_sha256': sha(frozen), 'sampled_monotonic': sampled,
        'alarm_remaining': remaining, 'alarm_deadline_monotonic': alarm_deadline,
        'alarm_mask': sorted(int(v) for v in signal.pthread_sigmask(signal.SIG_BLOCK, set())),
        'wrapper_deadline_monotonic': wrapper['deadline_monotonic'], 'unit': unit_name(campaign)}
    atomic(work/'source-observer-deadline-identity.json', identity)
    command(['systemd-run', '--quiet', '--no-block', '--unit='+identity['unit'],
        '--property=Type=oneshot', '--property=RemainAfterExit=yes', '--property=TimeoutStartSec=42',
        '/usr/bin/python3', '-B', str(frozen), 'actor', campaign])
    end = time.monotonic()+3
    while not (work/'source-observer-actor-ready.json').exists():
        assert time.monotonic() < end, 'source_deadline_actor_not_ready'
        time.sleep(.01)
    ready = json.loads((work/'source-observer-actor-ready.json').read_text())
    assert ready['completed'] and ready['operator'] == own and ready['campaign'] == campaign
    actor = process(ready['actor']['pid']); assert actor['birth'] == ready['actor']['birth']
    assert actor['cgroup'] != own['cgroup'] and identity['unit'] in actor['cgroup']
    receipt['deadline_fault'] = {**identity, 'actor_ready': ready, 'stop_requested_monotonic': time.monotonic()}
    atomic(target, receipt)
    os.kill(os.getpid(), signal.SIGSTOP)
    # Only the real pending SIGALRM may abort the resumed operator. Returning
    # from this gate must still execute its unchanged history assertion.


def actor(campaign):
    work, item, helper = context(campaign)
    identity = json.loads((work/'source-observer-deadline-identity.json').read_text())
    assert identity['campaign'] == campaign and identity['mode'] in MODES and identity['actor_source_sha256'] == sha(__file__)
    assert identity['operator_source_sha256'] == sha(ROOT/'e2e/invocation-source-retention-observer.py')
    target = identity['operator']; current = process(target['pid'])
    assert all(current[k] == target[k] for k in ('pid', 'birth', 'cgroup', 'command_sha256'))
    same_control(item, helper, identity)
    receipt = {'completed': False, 'campaign': campaign, 'mode': identity['mode'],
               'actor': process(os.getpid()), 'operator': target, 'signals_sent': []}
    descriptor = os.pidfd_open(target['pid'])
    try:
        assert process(target['pid'])['birth'] == target['birth']
        atomic(work/'source-observer-actor-ready.json', {**receipt, 'completed': True})
        end = time.monotonic()+3
        while True:
            current = process(target['pid'])
            assert current['birth'] == target['birth']
            if current['state'] == 'T': break
            assert time.monotonic() < end, 'source_operator_not_stopped'
            time.sleep(.005)
        receipt['stopped'] = current; receipt['stopped_monotonic'] = time.monotonic()
        atomic(work/'source-observer-actor.json', receipt)
        resume_at = identity['alarm_deadline_monotonic']+.5
        remaining = resume_at-time.monotonic()
        assert remaining > 0
        assert not select.select([descriptor], [], [], remaining)[0], 'source_operator_exited_before_deadline'
        pending = process(target['pid']); alarm = 1 << (signal.SIGALRM-1)
        receipt.update(deadline_sample=pending, deadline_sample_monotonic=time.monotonic())
        assert pending['birth'] == target['birth'] and pending['state'] == 'T'
        assert (pending['pending']|pending['shared_pending']) & alarm, 'source_alarm_not_pending'
        if identity['mode'] == 'global-alarm':
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            receipt['signals_sent'].append({'signal': int(signal.SIGCONT), 'monotonic': time.monotonic(), 'pidfd': True})
        atomic(work/'source-observer-actor.json', receipt)
        until_exit = identity['wrapper_deadline_monotonic']+2-time.monotonic()
        assert until_exit > 0 and select.select([descriptor], [], [], until_exit)[0], 'source_operator_not_joined_before_actor_deadline'
        receipt['operator_pidfd_readable'] = True
        receipt['control_after_exit'] = same_control(item, helper, identity)
        assert receipt['control_after_exit']['tracer_pid'] == 0
        receipt['operator_exit_observed_monotonic'] = time.monotonic()
        receipt['completed'] = True
    except BaseException as error:
        receipt['failure'] = {'type': type(error).__name__, 'reason': str(error) if isinstance(error, AssertionError) else None}
    finally:
        os.close(descriptor); receipt['pidfd_closed'] = True
        atomic(work/'source-observer-actor.json', receipt)
    print(json.dumps(receipt), flush=True)
    return receipt['completed']


def join_actor(work, campaign, receipt):
    unit = unit_name(campaign)
    try:
        end = time.monotonic()+3
        while True:
            state = unit_state(unit+'.service')
            if state.get('MainPID', '0') == '0' and state['SubState'] in ('exited', 'failed', 'dead'): break
            assert time.monotonic() < end, 'source_actor_not_terminal'
            time.sleep(.01)
        receipt['actor_terminal'] = state
        atomic(work/'source-observer-command.json', receipt)
    finally:
        before = unit_state(unit+'.service'); receipt['actor_before_stop'] = before
        atomic(work/'source-observer-command.json', receipt)
        if before['LoadState'] != 'not-found': command(['systemctl', 'stop', unit+'.service'])
        after = unit_state(unit+'.service')
        if after['ActiveState'] == 'failed':
            receipt['actor_failed_state'] = after; atomic(work/'source-observer-command.json', receipt)
            command(['systemctl', 'reset-failed', unit+'.service']); after = unit_state(unit+'.service')
        assert after['ActiveState'] == 'inactive' and after.get('MainPID', '0') == '0'
        receipt['actor_joined'] = after; atomic(work/'source-observer-command.json', receipt)


def rescue_operator(child, expected_argv, receipt):
    """On an unexpected wrapper overrun, join only its exact owned Python child."""
    children = Path('/proc', str(child.pid), 'task', str(child.pid), 'children')
    pids = [int(v) for v in children.read_text().split()] if children.exists() else []
    expected = b'\0'.join(v.encode() for v in expected_argv)+b'\0'
    for pid in pids:
        native = process(pid)
        if Path('/proc', str(pid), 'cmdline').read_bytes() != expected:
            continue
        descriptor = os.pidfd_open(pid)
        try:
            assert process(pid)['birth'] == native['birth'] and process(pid)['parent_pid'] == child.pid
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            dead = bool(select.select([descriptor], [], [], 2)[0])
            receipt.setdefault('rescue_operator_signals', []).append({'identity': native,
                'signal': int(signal.SIGKILL), 'pidfd_readable': dead})
            assert dead, 'source_rescue_operator_not_joined'
        finally:
            os.close(descriptor)


def run_command(campaign, mode, lock, functions, window):
    """Capture the actual cutoff result and control release before helper restore."""
    assert mode in MODES
    work, item, helper = context(campaign)
    assert len(functions) == len(set(functions)) == 2 and all(str(UUID(v)) == v for v in functions)
    assert type(window) is int and window % 300 == 0
    held = os.fstat(lock); assert [held.st_dev, held.st_ino] == item['lock_identity']
    started = time.monotonic()
    path = work/'source-observer-command.json'
    receipt = {'completed': False, 'phase': 'prepared', 'campaign': campaign, 'mode': mode,
        'started_monotonic': started, 'deadline_monotonic': started+40, 'timeout_seconds': 40,
        'timeout_signal': int(signal.SIGKILL), 'rescue_used': False}
    atomic(path, receipt)
    args = ['timeout', '--verbose', '--foreground', '--signal=KILL', '40s',
        'python3', '-B', str(ROOT/'e2e/invocation-source-retention-observer.py'), campaign,
        ','.join(functions), str(window), '--lock-fd', str(lock), '--deadline-fault='+mode]
    child = subprocess.Popen(args, cwd=ROOT, pass_fds=(lock,), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    descriptor = os.pidfd_open(child.pid)
    receipt.update(phase='running', wrapper=process(child.pid), argv=args); atomic(path, receipt)
    primary_error = None
    try:
        try:
            stdout, stderr = child.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            receipt['rescue_used'] = True
            rescue_operator(child, args[5:], receipt)
            if child.poll() is None:
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            stdout, stderr = child.communicate(timeout=5)
        receipt.update(phase='native-returned', returncode=child.returncode,
            finished_monotonic=time.monotonic(), duration=time.monotonic()-started,
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            wrapper_pidfd_readable=bool(select.select([descriptor], [], [], 0)[0]),
            wrapper_joined=child.poll() is not None,
            timeout_kill_reported='sending signal KILL' in stderr)
        for name, content in [('source-observer-command.stdout', stdout), ('source-observer-command.stderr', stderr)]:
            with open(work/name, 'w', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
        observation_path = work/'source-retention-observation.json'
        if observation_path.exists():
            observed = json.loads(observation_path.read_text())
            if 'deadline_fault' in observed:
                expected = observed['deadline_fault']
                receipt['control_before_restore'] = same_control(item, helper, expected)
                try: alive = process(expected['operator']['pid'])
                except FileNotFoundError: alive = None
                receipt['operator_after_return'] = alive
                receipt['operator_absent'] = alive is None or alive['birth'] != expected['operator']['birth']
        atomic(path, receipt)
        join_actor(work, campaign, receipt)
        receipt['completed'] = receipt['wrapper_joined'] and receipt['wrapper_pidfd_readable'] and not receipt['rescue_used']
        receipt['phase'] = 'finished'; atomic(path, receipt)
        assert child.returncode in (0, 1), 'source_retention_command_exit:'+str(child.returncode)
        return json.loads(stdout)
    except BaseException as error:
        primary_error = error
        receipt['primary_error'] = {'type': type(error).__name__,
            'reason': str(error) if isinstance(error, AssertionError) else None}
        atomic(path, receipt)
        raise
    finally:
        try:
            if child.poll() is None:
                rescue_operator(child, args[5:], receipt)
                child.kill(); child.communicate(timeout=5)
        finally:
            os.close(descriptor)
            if 'actor_joined' not in receipt:
                try:
                    join_actor(work, campaign, receipt)
                except BaseException as error:
                    receipt['actor_join_error'] = {'type': type(error).__name__,
                        'reason': str(error) if isinstance(error, AssertionError) else None}
                    atomic(path, receipt)
                    if primary_error is None:
                        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('actor',)); parser.add_argument('campaign')
    arguments = parser.parse_args(); raise SystemExit(0 if actor(arguments.campaign) else 1)
