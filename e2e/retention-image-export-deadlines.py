# @spec docs/BACKLOG.md#sls-132 | docs/RETENTION_SCHEMA_011.md#préservation-des-images-avant-la-capture-numérique
# @verifies docs/BACKLOG.md#sls-132 | docs/BACKLOG.md#sls-132
"""Real image-save/CLI deadlines; run in one DEV root systemd cgroup per case."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import subprocess
import sys
import time
from uuid import UUID

sys.path.insert(0, '/srv/p2enjoy-serverless/e2e')
import retention_current_images as exporter

ROOT = Path('/srv/p2enjoy-serverless')
IMAGE = 'sha256:f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0'
WALL = 0x40000000
ALRM_BIT = 1 << (signal.SIGALRM - 1)
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.ptrace.restype = ctypes.c_long
LIBC.ptrace.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]


def ptrace(request, pid, address=0, data=0):
    ctypes.set_errno(0)
    result = LIBC.ptrace(request, pid, address, data)
    if result == -1 and ctypes.get_errno():
        raise OSError(ctypes.get_errno(), 'native_export_observation_failed')
    return result


def identity(pid):
    path = Path('/proc', str(pid))
    fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'birth': fields[19], 'parent': int(fields[1]), 'group': int(fields[2]),
            'session': int(fields[3]), 'state': fields[0], 'cgroup': (path / 'cgroup').read_text(),
            'argv': (path / 'cmdline').read_bytes().split(b'\0')[:-1]}


def public_identity(item):
    return {k: v for k, v in item.items() if k not in ('argv', 'state')} | {
        'argv_sha256': hashlib.sha256(b'\0'.join(item['argv']) + b'\0').hexdigest()}


def unchanged(item):
    now = identity(item['pid'])
    assert all(now[k] == item[k] for k in ('birth', 'parent', 'group', 'session', 'cgroup', 'argv')), 'export_process_identity_changed'
    return now


def signal_owned(item, descriptor, number):
    unchanged(item)
    signal.pidfd_send_signal(descriptor, number)


def pending(pid):
    fields = dict(line.split(':', 1) for line in Path('/proc', str(pid), 'status').read_text().splitlines() if ':' in line)
    return {key: int(fields[key], 16) for key in ('SigBlk', 'SigPnd', 'ShdPnd')}


class Trace:
    def __init__(self, pid):
        self.pid = pid; self.memory = None; self.mode = 24
        self.descriptor = os.pidfd_open(pid)
        self.pinned = identity(pid)
        self.status = None; self.stopped = False; self.terminal = None

    def wait(self, deadline):
        while time.monotonic() < deadline:
            pid, status = os.waitpid(self.pid, os.WNOHANG | WALL)
            if pid:
                self.status = status
                if os.WIFEXITED(status) or os.WIFSIGNALED(status): self.terminal = status; return status
                assert os.WIFSTOPPED(status)
                self.stopped = True; return status
            time.sleep(.001)
        raise TimeoutError('export_trace_wait_deadline')

    def resume(self, delivered=0):
        assert self.stopped and self.terminal is None
        ptrace(self.mode, self.pid, 0, delivered); self.stopped = False

    def reopen_memory(self):
        if self.memory is not None: os.close(self.memory)
        self.memory = os.open('/proc/' + str(self.pid) + '/mem', os.O_RDONLY)

    def info(self):
        buffer = ctypes.create_string_buffer(88)
        ptrace(0x420e, self.pid, 88, ctypes.addressof(buffer))
        raw = buffer.raw
        assert int.from_bytes(raw[4:8], 'little') == 0xc000003e, 'x86_64_export_probe_required'
        if raw[0] == 1: return 1, [int.from_bytes(raw[i:i+8], 'little') for i in range(24, 80, 8)]
        if raw[0] == 2: return 2, int.from_bytes(raw[24:32], 'little', signed=True)
        return raw[0], None

    def literal(self, pointer, value):
        for offset, byte in enumerate(value):
            if os.pread(self.memory, 1, pointer + offset) != bytes([byte]): return False
        return True

    def close(self):
        if self.memory is not None: os.close(self.memory); self.memory = None
        os.close(self.descriptor)


def child(case, image_writer, output, image_reader):
    os.close(image_reader)
    ptrace(0, 0); os.kill(os.getpid(), signal.SIGSTOP)
    if case == 'cli90':
        os.dup2(output, 1); os.close(output); os.close(image_writer)
        os.execv(sys.executable, [sys.executable, '-B', str(ROOT / 'e2e/retention_current_images.py'), 'verify', IMAGE])
    assert LIBC.prctl(36, 1, 0, 0, 0) == 0
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('image_preservation_deadline')))
    signal.alarm(90)
    started = time.monotonic()
    value = {'completed': False}
    try:
        with os.fdopen(image_writer, 'wb') as stream:
            value['export'] = exporter.export_image(IMAGE, stream)
        value['completed'] = True
    except BaseException as error:
        value.update(failure_type=type(error).__name__, reason=str(error),
            cause_type=type(error.__cause__).__name__ if error.__cause__ else None,
            cause_timeout=getattr(error.__cause__, 'timeout', None),
            elapsed_seconds=time.monotonic()-started)
    finally:
        signal.alarm(0)
        os.write(output, (json.dumps(value) + '\n').encode()); os.close(output)
    os._exit(0 if value['completed'] else 1)


def setup(trace, case, record, deadline):
    trace.wait(time.monotonic() + 5)
    assert os.WSTOPSIG(trace.status) == signal.SIGSTOP and trace.status >> 16 == 0
    ptrace(0x4200, trace.pid, 0, 1 | 16)  # TRACESYSGOOD and TRACEEXEC.
    trace.reopen_memory(); trace.resume()
    last = None; timer = None; pointer = None
    while time.monotonic() < deadline:
        status = trace.wait(deadline)
        assert trace.terminal is None, 'export_helper_ended_before_gate'
        event, stopped = status >> 16, os.WSTOPSIG(status)
        if event == 4:
            trace.reopen_memory(); trace.pinned = identity(trace.pid)
            assert trace.pinned['argv'] == [v.encode() for v in [sys.executable, '-B', str(ROOT / 'e2e/retention_current_images.py'), 'verify', IMAGE]]
            trace.resume(); continue
        if stopped != signal.SIGTRAP | 0x80:
            assert event == 0
            trace.resume(stopped); continue
        op, info = trace.info()
        if op == 1:
            last = info[0]
            if last == 37: assert info[1] == 90
            if timer is not None and case == 'cli90' and last == 257 and trace.literal(info[2], b'/etc/spark/env\0'):
                held = public_identity(identity(trace.pid)); assert held['birth'] == trace.pinned['birth']
                while time.monotonic() < timer + 90.2: time.sleep(.02)
                signals = pending(trace.pid)
                assert (signals['SigPnd'] | signals['ShdPnd']) & ALRM_BIT
                record['global_alarm'] = {'armed_at_monotonic': timer, 'sample_at_monotonic': time.monotonic(), 'signals': signals, 'held': held}
                record['gate_released_at_monotonic'] = time.monotonic()
                trace.mode = 7; trace.resume(); return
            if timer is not None and case != 'cli90' and last == 36:
                assert info[1] == 0
                pointer = info[2]
                if case == 'alarm-join5':
                    while time.monotonic() < timer + 46: time.sleep(.02)
                record['remaining_capture_enter_monotonic'] = time.monotonic()
                assert pending(trace.pid)['SigBlk'] & ALRM_BIT
        elif op == 2:
            if last == 37:
                assert info == 0
                timer = time.monotonic(); record['timer_armed_at_monotonic'] = timer
            elif last == 36 and pointer is not None:
                assert info == 0
                fields = struct.unpack('qqqq', os.pread(trace.memory, 32, pointer))
                remaining = fields[2] + fields[3] / 1e6
                assert (0 < remaining < 45) if case == 'alarm-join5' else remaining > 45
                record['actual_remaining_alarm_seconds'] = remaining
                record['remaining_capture_exit_monotonic'] = time.monotonic()
                trace.mode = 7; trace.resume(); return
        trace.resume()
    raise TimeoutError('export_native_gate_not_reached')


def descendants(pid):
    return [int(v) for v in Path('/proc', str(pid), 'task', str(pid), 'children').read_text().split()]


def wait_exit(trace, deadline, *, runuser=None, record=None):
    while time.monotonic() < deadline:
        pid, status = os.waitpid(-1, os.WNOHANG | WALL)
        if not pid:
            if runuser is not None and record.get('exit_stop') and 'alarm_pending_during_join' not in record:
                signals = pending(trace.pid)
                if signals['SigBlk'] & ALRM_BIT and (signals['SigPnd'] | signals['ShdPnd']) & ALRM_BIT:
                    record['alarm_pending_during_join'] = {'signals': signals, 'at_monotonic': time.monotonic(), 'helper': public_identity(identity(trace.pid)), 'runuser': public_identity(identity(runuser['pid']))}
            time.sleep(.001); continue
        if pid == trace.pid:
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                trace.terminal = status; record['helper_terminal_at_monotonic'] = time.monotonic(); return
            assert os.WIFSTOPPED(status) and status >> 16 == 0
            trace.stopped = True; trace.resume(os.WSTOPSIG(status))
        elif runuser is not None and pid == runuser['pid']:
            assert os.WIFSTOPPED(status) and status >> 16 == 6 and os.WSTOPSIG(status) == signal.SIGTRAP, 'actual_exit_event_required'
            message = ctypes.c_ulong(); ptrace(0x4201, pid, 0, ctypes.addressof(message))
            assert os.WIFSIGNALED(message.value) and os.WTERMSIG(message.value) == signal.SIGKILL
            assert identity(pid)['birth'] == runuser['birth'] and identity(pid)['group'] == runuser['group']
            record['exit_stop'] = {'raw_status': status, 'event_message': message.value, 'at_monotonic': time.monotonic(), 'identity': public_identity(identity(pid))}
        else:
            assert os.WIFEXITED(status) or os.WIFSIGNALED(status), 'unexpected_owned_descendant_stop'
    raise TimeoutError('export_helper_deadline')


def run(case, record):
    assert LIBC.prctl(36, 1, 0, 0, 0) == 0
    image_reader, image_writer = os.pipe(); output_reader, output_writer = os.pipe()
    descriptor = None; wrapper = None; runuser = None; trace = None; released = False
    started = time.monotonic(); deadline = started + 150
    pid = os.fork()
    if pid == 0:
        os.close(output_reader); child(case, image_writer, output_writer, image_reader)
    os.close(image_writer); os.close(output_writer)
    try:
        trace = Trace(pid); assert trace.pinned['parent'] == os.getpid() and trace.pinned['cgroup'] == Path('/proc/self/cgroup').read_text()
        record['helper'] = public_identity(trace.pinned)
        setup(trace, case, record, deadline)
        if case != 'cli90':
            while time.monotonic() < deadline:
                children = descendants(pid)
                matches = []
                for value in children:
                    item = identity(value)
                    if item['argv'] and Path(os.fsdecode(item['argv'][0])).name == 'timeout': matches.append(item)
                if matches:
                    assert len(matches) == 1; wrapper = matches[0]; break
                # Forward a genuine SIGCHLD, if the helper has entered its stop.
                stopped, status = os.waitpid(pid, os.WNOHANG | WALL)
                if stopped:
                    assert os.WIFSTOPPED(status); trace.stopped = True; trace.resume(os.WSTOPSIG(status))
                time.sleep(.001)
            assert wrapper is not None and wrapper['group'] == wrapper['session'] == wrapper['pid']
            assert wrapper['argv'][1:] == [v.encode() for v in ['--foreground', '--signal=KILL', '40s', *exporter.DOCKER, 'image', 'save', IMAGE]]
            while time.monotonic() < deadline:
                children = descendants(wrapper['pid'])
                for value in children:
                    item = identity(value)
                    if item['argv'] and Path(os.fsdecode(item['argv'][0])).name == 'runuser': runuser = item; break
                if runuser: break
                time.sleep(.001)
            assert runuser and runuser['parent'] == wrapper['pid'] and runuser['group'] == wrapper['group'] and runuser['cgroup'] == wrapper['cgroup']
            assert runuser['argv'][1:] == [v.encode() for v in exporter.DOCKER[1:] + ['image', 'save', IMAGE]]
            # Observe genuine kernel backpressure of this image-save stdout pipe.
            pipe_inode = os.fstat(image_reader).st_ino; blocked = None
            while time.monotonic() < deadline:
                for docker_pid in descendants(runuser['pid']):
                    for task in Path('/proc', str(docker_pid), 'task').iterdir():
                        try:
                            if 'pipe_write' in (task / 'wchan').read_text():
                                assert os.readlink('/proc/' + str(docker_pid) + '/fd/1') == 'pipe:[' + str(pipe_inode) + ']'
                                assert identity(docker_pid)['cgroup'] == wrapper['cgroup'], 'image_save_must_remain_in_owned_unit'
                                blocked = {'thread': int(task.name), 'process': public_identity(identity(docker_pid)), 'pipe_inode': pipe_inode}; break
                        except FileNotFoundError: continue
                    if blocked: break
                if blocked: break
                time.sleep(.001)
            assert blocked, 'actual_image_save_pipe_backpressure_required'
            record['blocked_image_save'] = blocked
            descriptor = os.pidfd_open(wrapper['pid']); signal_owned(wrapper, descriptor, signal.SIGSTOP)
            while identity(wrapper['pid'])['state'] != 'T':
                assert time.monotonic() < deadline; time.sleep(.001)
            record['stopped_timeout'] = public_identity(unchanged(wrapper))
            unchanged(runuser); ptrace(0x4206, runuser['pid'], 0, 64)
            record['runuser'] = public_identity(runuser)
        wait_exit(trace, deadline, runuser=runuser, record=record)
        assert os.WIFEXITED(trace.terminal) and os.WEXITSTATUS(trace.terminal) == 1
        chunks = []
        while True:
            chunk = os.read(output_reader, 65536)
            if not chunk: break
            chunks.append(chunk)
        output = b''.join(chunks); result = json.loads(output)
        record.update(operator_result=result, operator_exit_code=1, operator_stdout_sha256=hashlib.sha256(output).hexdigest())
        if case == 'cli90':
            assert result['completed'] is False and result['failure_type'] == 'TimeoutError'
            assert 0 <= record['helper_terminal_at_monotonic'] - record['gate_released_at_monotonic'] <= 1
        else:
            assert result['completed'] is False and result['failure_type'] == 'AssertionError' and result['reason'] == 'image_export_group_not_joined'
            assert result['cause_type'] == 'TimeoutExpired' and record.get('exit_stop')
            assert abs(result['cause_timeout'] - min(45, record['actual_remaining_alarm_seconds'])) <= 1e-9
            record['join_after_exit_stop_seconds'] = record['helper_terminal_at_monotonic'] - record['exit_stop']['at_monotonic']
            assert 4.5 <= record['join_after_exit_stop_seconds'] <= 5.5
            assert result['elapsed_seconds'] >= (90 if case == 'alarm-join5' else 45) + 4.8
            if case == 'alarm-join5': assert record.get('alarm_pending_during_join')
            # The tracee finishes its genuine exit; a second SIGKILL is not used.
            ptrace(7, runuser['pid']); released = True
        joined = []
        while True:
            try:
                waited, status = os.waitpid(-1, os.WNOHANG | WALL)
                if waited:
                    assert os.WIFEXITED(status) or os.WIFSIGNALED(status)
                    joined.append({'pid': waited, 'status': status}); continue
            except ChildProcessError: break
            assert time.monotonic() < deadline, 'export_descendants_not_joined'; time.sleep(.002)
        if wrapper: assert exporter.group_members(wrapper['pid']) == []
        record.update(children_joined=True, child_terminal_statuses=joined, group_empty=True, elapsed_seconds=time.monotonic()-started)
    finally:
        if runuser and record.get('exit_stop') and not released:
            try: ptrace(7, runuser['pid'])
            except OSError: pass
        if trace is not None: trace.close()
        if descriptor is not None: os.close(descriptor)
        os.close(image_reader); os.close(output_reader)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('cli90', 'join5', 'alarm-join5'))
    parser.add_argument('run_id')
    args = parser.parse_args()
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
    assert str(UUID(args.run_id)) == args.run_id
    expected_unit = 'serverless-qualification-image-export-' + args.case + '-' + UUID(args.run_id).hex + '.service'
    assert expected_unit in Path('/proc/self/cgroup').read_text(), 'owned_deadline_unit_required'
    command = ['systemctl', 'show', expected_unit] + ['--property=' + key for key in (
        'LoadState', 'MainPID', 'Type', 'RemainAfterExit', 'Restart', 'TimeoutStartUSec', 'TimeoutStopUSec', 'KillMode')]
    configuration = dict(line.split('=', 1) for line in subprocess.check_output(command, text=True, timeout=10).splitlines())
    assert configuration == {'LoadState': 'loaded', 'MainPID': str(os.getpid()), 'Type': 'oneshot',
        'RemainAfterExit': 'yes', 'Restart': 'no', 'TimeoutStartUSec': '3min', 'TimeoutStopUSec': '30s', 'KillMode': 'control-group'}
    folder = ROOT / 'qualification-history' / ('image-export-deadline-' + args.case + '-' + UUID(args.run_id).hex)
    folder.mkdir(mode=0o700)
    value = {'completed': False, 'qualified_groups': 0, 'case': args.case, 'run_id': args.run_id,
             'image': IMAGE, 'started_at_ns': time.time_ns(), 'unit': expected_unit,
             'unit_configuration': configuration,
             'operator_sha256': exporter.sha(Path(__file__)), 'exporter_sha256': exporter.sha(Path(exporter.__file__))}
    path = folder / 'result.json'
    try:
        value['before'] = exporter.baseline(IMAGE)
        value['preservation_before'] = exporter.verify(IMAGE, value['before']['runtime_image'])
        run(args.case, value)
        value['after'] = exporter.baseline(IMAGE)
        value['preservation_after'] = exporter.verify(IMAGE, value['after']['runtime_image'])
        assert value['after'] == value['before'] and value['preservation_after'] == value['preservation_before']
        value['completed'] = True
    except BaseException as error:
        value['failure'] = {'type': type(error).__name__, 'message_sha256': hashlib.sha256(str(error).encode()).hexdigest()}
        raise
    finally:
        value['finished_at_ns'] = time.time_ns()
        with path.open('x') as stream:
            os.fchmod(stream.fileno(), 0o400); json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        print(json.dumps({'completed': value['completed'], 'qualified_groups': 0, 'case': args.case, 'report': str(path)}), flush=True)


if __name__ == '__main__': main()
