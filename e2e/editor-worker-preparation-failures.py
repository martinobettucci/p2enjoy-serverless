# @spec docs/BACKLOG.md#sls-147 | docs/CODE_EDITOR_READ_CONCURRENCY.md#fautes-réelles-du-préparateur--sls-1473
# @verifies docs/BACKLOG.md#sls-147 | docs/SCHEMA_011_REGRESSIONS.md#préparation-des-workers--sls-147
"""Exercise real private-file, pipe and SSH failures; no substituted dependency."""
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import select
import signal
import stat
import subprocess
import sys
import threading
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/e2e'
HELPERS = runpy.run_path(str(ROOT / 'e2e/schedule_regressions.py'))
SUITE = runpy.run_path(str(ROOT / 'e2e/execution-suite.py'))
NativeObserver = runpy.run_path(str(ROOT / 'e2e/native_control_observer.py'))['NativeObserver']
MODES = ('read-denied', 'report-denied', 'print-closed', 'transport-timeout')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def diagnosis(error):
    return {'type': type(error).__name__, 'errno': getattr(error, 'errno', None),
            'message_sha256': sha(str(error).encode())}


def identity(pid):
    path = Path('/proc', str(pid))
    fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    namespace = (path / 'ns/pid').stat()
    status = dict(line.split(':', 1) for line in (path / 'status').read_text().splitlines() if ':' in line)
    return {'pid': pid, 'birth': fields[19], 'parent': int(fields[1]),
            'uid': path.stat().st_uid, 'state': fields[0], 'tracer_pid': int(status['TracerPid']),
            'process_group': int(fields[2]), 'session': int(fields[3]),
            'command_sha256': sha((path / 'cmdline').read_bytes()),
            'pid_namespace': {'device': namespace.st_dev, 'inode': namespace.st_ino}}


def same_process(expected):
    current = identity(expected['pid'])
    assert all(current[k] == expected[k] for k in ('birth', 'uid', 'command_sha256', 'pid_namespace'))
    return current


def file_identity(path):
    info = path.lstat()
    assert not path.is_symlink() and info.st_uid == os.geteuid()
    return {'device': info.st_dev, 'inode': info.st_ino,
            'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid}


def check_file(path, expected):
    current = file_identity(path)
    assert all(current[k] == expected[k] for k in ('device', 'inode', 'uid'))
    return current


def open_stream_owner(child, folder):
    """Require both actual CLI-held file descriptors before changing a path."""
    same_process(child)
    paths = [folder / channel for channel in ('stdout', 'stderr')]
    if not all(p.exists() for p in paths):
        return None
    records = [file_identity(p) for p in paths]
    for p, record in zip(paths, records):
        assert stat.S_ISREG(p.stat().st_mode) and record['mode'] == 0o600
    held = set()
    for fd in Path('/proc', str(child['pid']), 'fd').iterdir():
        try:
            info = fd.stat()
        except FileNotFoundError:
            continue
        held.add((info.st_dev, info.st_ino))
    if all((r['device'], r['inode']) in held for r in records):
        return records
    return None


def payload_ssh(child, streams):
    expected = [os.fsencode(x) for x in HELPERS['SSH'] + ['python3 -B -']]
    children = Path('/proc', str(child['pid']), 'task', str(child['pid']), 'children').read_text().split()
    found = []
    for value in children:
        path = Path('/proc', value)
        try:
            if (path / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0') != expected:
                continue
            actual = [(path / 'fd' / str(n)).stat() for n in (1, 2)]
            if not all((a.st_dev, a.st_ino) == (b['device'], b['inode']) for a, b in zip(actual, streams)):
                continue
            item = identity(int(value))
        except FileNotFoundError:
            continue
        assert item['parent'] == child['pid'] and item['uid'] == child['uid']
        assert item['pid_namespace'] == child['pid_namespace']
        found.append(item)
    assert len(found) <= 1
    return found[0] if found else None


def atomic(path, value):
    pending = path.with_suffix('.pending')
    pending.write_text(json.dumps(value, indent=2) + '\n')
    pending.chmod(0o600)
    pending.replace(path)


class PayloadWriter(NativeObserver):
    """Observe only syscall metadata; never opens the SSH process memory."""
    def __init__(self, owner, descriptor):
        super().__init__(owner['pid'])
        self.owner, self.descriptor, self.last_status = owner, descriptor, None
        self.exit_code, self.write_events = None, []

    def wait(self, deadline):
        while time.monotonic() < deadline:
            pid, status = os.waitpid(self.pid, os.WNOHANG | 0x40000000)
            if pid:
                self.last_status = status
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    self.exit_code = os.waitstatus_to_exitcode(status)
                    self.attached, self.stopped = False, False
                assert os.WIFSTOPPED(status), 'owned_ssh_exited_during_observation'
                self.stopped = True
                return os.WSTOPSIG(status)
            time.sleep(.001)
        raise TimeoutError('owned_ssh_write_deadline')

    def delivered_signal(self):
        assert self.last_status is not None
        sig = os.WSTOPSIG(self.last_status)
        return sig if self.last_status >> 16 == 0 and sig != (signal.SIGTRAP | 0x80) else 0

    def matches_stdout(self, descriptor, expected):
        try:
            info = Path('/proc', str(self.pid), 'fd', str(descriptor)).stat()
        except FileNotFoundError:
            return False
        return (info.st_dev, info.st_ino, info.st_uid) == (
            expected['device'], expected['inode'], expected['uid']) and stat.S_ISREG(info.st_mode)

    def observation(self):
        return {'last_wait_status': self.last_status, 'observed_exit_code': self.exit_code,
                'write_events': self.write_events, 'attached': self.attached, 'stopped': self.stopped}

    def complete_then_stop(self, path, expected):
        owner = same_process(self.owner)
        assert owner['tracer_pid'] == 0 and owner['state'] not in ('T', 't')
        self.ptrace(0x4206, 0, 1)  # SEIZE/TRACESYSGOOD, no EXITKILL or memory FD.
        self.attached = True
        self.ptrace(0x4207)
        deadline = time.monotonic() + 30
        self.wait(deadline)
        pending = None
        while True:
            self.resume(self.delivered_signal())
            sig = self.wait(deadline)
            if sig != (signal.SIGTRAP | 0x80):
                continue
            op, args = self.info()
            if op == 1:
                pending = None
                if args[0] in (1, 20) and self.matches_stdout(args[1], expected):
                    assert len(self.write_events) < 64, 'owned_stdout_write_event_limit'
                    pending = {'syscall': args[0], 'fd': args[1],
                               'entry_monotonic_ns': time.monotonic_ns()}
                    self.write_events.append(pending)
                continue
            if op != 2 or pending is None:
                continue
            pending.update(returned_bytes=args, exit_monotonic_ns=time.monotonic_ns())
            assert self.matches_stdout(pending['fd'], expected), 'owned_stdout_fd_changed'
            if args <= 0:
                continue
            check_file(path, expected)
            assert path.stat().st_size <= 1024 ** 2, 'native_result_limit'
            raw = path.read_bytes()
            try:
                native = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue  # A later real write must complete this one bounded response.
            assert native['completed'] and native['restart_exit_code'] == 0
            assert native['failure'] is None and native['secondary_errors'] == []
            assert native['same_cid_image'] and native['reference_unchanged'] and native['protected_tables_unchanged']
            result = {'syscall': pending['syscall'], 'fd': pending['fd'],
                      'entry_monotonic_ns': pending['entry_monotonic_ns'],
                      'exit_monotonic_ns': pending['exit_monotonic_ns'],
                      'write_returned_bytes': args, 'bytes': len(raw),
                      'sha256': sha(raw), 'received_at_ns': time.time_ns(),
                      'native_result': native}
            # Establish a signal-delivery stop; DETACH from a syscall stop alone
            # does not guarantee injection of a new signal.
            signal.pidfd_send_signal(self.descriptor, signal.SIGSTOP)
            stop_deadline = time.monotonic() + 5
            while True:
                self.resume(self.delivered_signal())
                sig = self.wait(stop_deadline)
                if sig == signal.SIGSTOP and self.last_status >> 16 == 0:
                    break
            self.ptrace(17, 0, signal.SIGSTOP)
            self.attached, self.stopped = False, False
            while True:
                owner = same_process(self.owner)
                if owner['state'] == 'T' and owner['tracer_pid'] == 0:
                    break
                assert time.monotonic() < stop_deadline, 'owned_ssh_stop_not_confirmed'
                time.sleep(.001)
            result['detached_stopped_at_ns'] = time.time_ns()
            result['detached_stopped_monotonic_ns'] = time.monotonic_ns()
            return result

    def release_trace(self):
        if not self.attached:
            return
        if select.select([self.descriptor], [], [], 0)[0]:
            self.attached = False
            return
        same_process(self.owner)
        if not self.stopped:
            self.ptrace(0x4207)
            self.wait(time.monotonic() + 5)
        self.ptrace(17, 0, self.delivered_signal())
        self.attached, self.stopped = False, False


def kill_owned_session(child):
    """The unreaped, directly owned session leader reserves its process ID."""
    assert child.returncode is None and threading.active_count() == 1
    assert signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL
    descriptors, errors = [], []
    try:
        for path in Path('/proc').iterdir():
            fd = None
            try:
                if not path.name.isdecimal() or path.stat().st_uid != os.geteuid():
                    continue
                fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
                if int(fields[2]) != child.pid or int(fields[3]) != child.pid:
                    continue
                item = identity(int(path.name))
                fd = os.pidfd_open(item['pid'])
                same_process(item)
                descriptors.append((fd, item))
                fd = None
            except (FileNotFoundError, ProcessLookupError):
                continue
            finally:
                if fd is not None:
                    os.close(fd)
    except BaseException as error:
        errors.append(error)
    finally:
        # No wait/poll has reaped this Popen child: this PGID cannot have been
        # reused. Every member belongs to the session created by this launch.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # An exited but unreaped leader still reserves its identity.
        except BaseException as error:
            errors.append(error)
        try:
            child.wait(timeout=5)
        except BaseException as error:
            errors.append(error)
    try:
        for fd, item in descriptors:
            try:
                assert select.select([fd], [], [], 5)[0], 'owned_session_member_not_joined'
            except BaseException as error:
                errors.append(error)
        if errors:
            raise errors[0]
        return [item for fd, item in descriptors]
    finally:
        for fd, item in descriptors:
            os.close(fd)


def run_case(mode, work, source_commit):
    folder = work / mode
    folder.mkdir(mode=0o700)
    before = HELPERS['native_state']()
    prior = set(OUTPUT.glob('editor-worker-preparation-*'))
    value = {'mode': mode, 'completed': False, 'groups_added': 0,
             'native_before': before, 'started_at_ns': time.time_ns(),
             'failure': None, 'cleanup_errors': []}
    child = None
    stream_fd = ssh_fd = client_fd = None
    owned_dir = None
    ssh = None
    primary = None
    observer = None
    prepared_folder = None

    def cleanup_error(phase, error):
        nonlocal primary
        value['cleanup_errors'].append({'phase': phase, **diagnosis(error)})
        if primary is None:
            primary = error
            value['failure'] = diagnosis(error)

    try:
        with (folder / 'cli.stdout').open('xb') as stdout, (folder / 'cli.stderr').open('xb') as stderr:
            assert threading.active_count() == 1 and signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL
            original_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
            launch_error = None
            try:
                child = subprocess.Popen([sys.executable, '-B', 'e2e/prepare-editor-worker-control.py'],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE if mode == 'print-closed' else stdout,
                    stderr=stderr, start_new_session=True, cwd=ROOT,
                    preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, original_mask))
                client_fd = os.pidfd_open(child.pid)
                owner = identity(child.pid)
                assert owner['uid'] == os.geteuid() and owner['session'] == child.pid
                same_process(owner)
            except BaseException as error:
                launch_error = error
            finally:
                try:
                    signal.pthread_sigmask(signal.SIG_SETMASK, original_mask)
                except BaseException as error:
                    if launch_error is None:
                        launch_error = error
                    else:
                        value['cleanup_errors'].append({'phase': 'launch-mask', **diagnosis(error)})
            if launch_error is not None:
                raise launch_error
            value['client_identity'] = owner
            if mode == 'print-closed':
                info = os.fstat(child.stdout.fileno())
                value['closed_print_sink'] = {'device': info.st_dev, 'inode': info.st_ino,
                                             'closed_at_ns': time.time_ns()}
                child.stdout.close()
            deadline = time.monotonic() + 900
            next_heartbeat = time.monotonic() + 10
            injected = False
            while child.poll() is None:
                assert time.monotonic() < deadline, 'diagnostic_client_deadline'
                added = set(OUTPUT.glob('editor-worker-preparation-*')) - prior
                assert len(added) <= 1, 'ambiguous_preparation_folder'
                if added and prepared_folder is None:
                    candidate = next(iter(added))
                    assert re.fullmatch('editor-worker-preparation-[0-9a-f]{32}', candidate.name)
                    item = file_identity(candidate)
                    assert candidate.is_dir() and item['mode'] == 0o700 and candidate.resolve() == candidate
                    prepared_folder = candidate
                    value['preparation_folder'] = str(candidate.relative_to(ROOT))
                if prepared_folder is not None and not injected:
                    streams = open_stream_owner(owner, prepared_folder)
                    if streams:
                        ssh = payload_ssh(owner, streams)
                        if ssh is None:
                            time.sleep(.01)
                            continue
                        ssh_fd = os.pidfd_open(ssh['pid'])
                        same_process(ssh)
                        value['payload_ssh_identity'] = ssh
                        value['stream_identities'] = streams
                        if mode in ('read-denied', 'transport-timeout'):
                            if mode == 'transport-timeout':
                                observer = PayloadWriter(ssh, ssh_fd)
                                value['native_before_pause'] = observer.complete_then_stop(
                                    prepared_folder / 'stdout', streams[0])
                                value['stopped_ssh'] = ssh
                                value['ssh_stopped_at_ns'] = time.time_ns()
                            stream_fd = os.open(prepared_folder / 'stdout', os.O_RDONLY | os.O_NOFOLLOW)
                            info = os.fstat(stream_fd)
                            assert (info.st_dev, info.st_ino) == (streams[0]['device'], streams[0]['inode'])
                            os.fchmod(stream_fd, 0)
                            assert check_file(prepared_folder / 'stdout', streams[0])['mode'] == 0
                            value['read_denied_at_ns'] = time.time_ns()
                        elif mode == 'report-denied':
                            path = prepared_folder / 'report.json'
                            path.mkdir(mode=0o700)
                            owned_dir = (path, file_identity(path))
                            value['report_directory'] = {'path': str(path.relative_to(ROOT)), **owned_dir[1]}
                        injected = True
                        value['fault_observed_at_ns'] = time.time_ns()
                        atomic(folder / 'checkpoint.json', value)
                if time.monotonic() >= next_heartbeat:
                    print(json.dumps({'mode': mode, 'state': 'waiting', 'client_alive': True,
                                      'fault_applied': injected}), flush=True)
                    next_heartbeat = time.monotonic() + 10
                time.sleep(.01)
            value.update(actual_client_exit_code=child.wait(), client_joined=True)
            assert injected and prepared_folder is not None, 'diagnostic_fault_not_reached'
            if ssh_fd is not None:
                value['ssh_joined_by_preparer'] = bool(select.select([ssh_fd], [], [], 0)[0])
                assert value['ssh_joined_by_preparer'], 'preparer_did_not_join_ssh'
            assert value['actual_client_exit_code'] != 0, 'negative_client_became_success'
    except BaseException as error:
        primary = error
        value['failure'] = diagnosis(error)
    finally:
        # Independent cleanup attempts never replace the first failure.
        if observer is not None:
            try:
                observer.release_trace()
            except BaseException as error:
                cleanup_error('trace-detach', error)
            value['ssh_write_observation'] = observer.observation()
        if child is not None and child.returncode is None:
            try:
                value['session_members_joined'] = kill_owned_session(child)
                value['client_joined_on_failure'] = True
            except BaseException as error:
                cleanup_error('client-join', error)
            finally:
                if child.returncode is not None:
                    value['actual_client_exit_code'] = child.returncode
        if client_fd is not None:
            try:
                os.close(client_fd)
            except BaseException as error:
                cleanup_error('client-fd-close', error)
        if ssh_fd is not None:
            try:
                if not select.select([ssh_fd], [], [], 0)[0]:
                    same_process(ssh)
                    signal.pidfd_send_signal(ssh_fd, signal.SIGCONT)
                    signal.pidfd_send_signal(ssh_fd, signal.SIGKILL)
                    assert select.select([ssh_fd], [], [], 5)[0], 'owned_ssh_cleanup_not_joined'
                    value['ssh_rescue_used'] = True
            except BaseException as error:
                cleanup_error('ssh-join', error)
            finally:
                try:
                    os.close(ssh_fd)
                except BaseException as error:
                    cleanup_error('ssh-fd-close', error)
        if stream_fd is not None:
            try:
                os.fchmod(stream_fd, 0o600)
                assert check_file(prepared_folder / 'stdout', value['stream_identities'][0])['mode'] == 0o600
                value['read_permission_restored'] = True
            except BaseException as error:
                cleanup_error('permission', error)
            finally:
                try:
                    os.close(stream_fd)
                except BaseException as error:
                    cleanup_error('stream-fd-close', error)
        if owned_dir is not None:
            try:
                path, expected = owned_dir
                check_file(path, expected)
                path.rmdir()
                value['report_directory_removed'] = True
            except BaseException as error:
                cleanup_error('directory', error)
    # Retain each available stream and observe native state even when an earlier
    # assertion failed. These observations cannot turn a failed case into success.
    value['transports'] = {}
    paths = {'cli-stderr': folder / 'cli.stderr'}
    if prepared_folder is not None:
        paths.update({'native-stdout': prepared_folder / 'stdout',
                      'native-stderr': prepared_folder / 'stderr'})
    if mode != 'print-closed':
        paths['cli-stdout'] = folder / 'cli.stdout'
    else:
        value['cli_stdout_closed_without_reader'] = True
    for channel, path in paths.items():
        try:
            raw = path.read_bytes()
            value['transports'][channel] = {'path': str(path.relative_to(ROOT)),
                                            'bytes': len(raw), 'sha256': sha(raw)}
        except BaseException as error:
            cleanup_error(channel + '-retain', error)
    try:
        after = HELPERS['native_state']()
        value['native_after'] = after
        HELPERS['same_installation'](before, after)
    except BaseException as error:
        cleanup_error('native-after', error)
    try:
        if primary is not None:
            raise primary
        assert not value['cleanup_errors']
        terminal_path = prepared_folder / 'publication-errors.json'
        terminal = json.loads(terminal_path.read_bytes())
        value['terminal'] = {'path': str(terminal_path.relative_to(ROOT)),
                             'sha256': sha(terminal_path.read_bytes()), 'value': terminal}
        assert not terminal['completed'] and terminal['failure'] is not None
        assert terminal['source_commit'] == source_commit
        expected_secondary = {
            'read-denied': [('parse', 'PermissionError', 13)],
            'report-denied': [('save', 'IsADirectoryError', 21)],
            'print-closed': [('print', 'BrokenPipeError', 32)],
            'transport-timeout': [('stdout-retain', 'PermissionError', 13), ('parse', 'PermissionError', 13)],
        }[mode]
        assert [(x['phase'], x['type'], x['errno']) for x in terminal['secondary_errors']] == expected_secondary
        expected_error = {'read-denied': ('PermissionError', 13),
                          'report-denied': ('IsADirectoryError', 21),
                          'print-closed': ('BrokenPipeError', 32),
                          'transport-timeout': ('TimeoutExpired', None)}[mode]
        assert (terminal['failure']['type'], terminal['failure']['errno']) == expected_error
        if mode == 'transport-timeout':
            assert terminal['exit_code'] is None and terminal['transport_result'] == 'unknown'
            assert any(x['type'] == 'PermissionError' and x['errno'] == 13 for x in terminal['secondary_errors'])
            assert value['ssh_joined_by_preparer'] and not value.get('ssh_rescue_used')
        else:
            assert terminal['exit_code'] == 0 and terminal['transport_result'] == 'observed'
            native = json.loads((prepared_folder / 'stdout').read_bytes())
            assert native['completed'] and native['restart_exit_code'] == 0
            assert native['failure'] is None and native['secondary_errors'] == []
            assert native['same_cid_image'] and native['reference_unchanged'] and native['protected_tables_unchanged']
        if mode == 'print-closed':
            value['intermediate_report'] = json.loads((prepared_folder / 'report.json').read_bytes())
            assert value['intermediate_report']['completed']
        value['completed'] = True
    except BaseException as error:
        if primary is None:
            primary = error
            value['failure'] = diagnosis(error)
    value['finished_at_ns'] = time.time_ns()
    try:
        atomic(folder / 'checkpoint.json', value)
    except BaseException as error:
        cleanup_error('checkpoint-save', error)
    try:
        print(json.dumps({'mode': mode, 'completed': value['completed'] and primary is None, 'groups_added': 0,
                          'checkpoint': str((folder / 'checkpoint.json').relative_to(ROOT))}), flush=True)
    except BaseException as error:
        cleanup_error('result-print', error)
    if primary is not None:
        raise primary
    return value


def interrupted(signum, frame):
    raise InterruptedError('diagnostic_controller_interrupted:' + str(signum))


def main():
    assert sys.argv[1:] == []
    os.chdir(ROOT)
    os.umask(0o077)
    assert os.geteuid() != 0, 'unprivileged_private_file_refusals_required'
    assert not subprocess.check_output(['git', 'status', '--porcelain'])
    work = OUTPUT / ('editor-worker-failures-' + uuid4().hex)
    work.mkdir(mode=0o700)
    value = {'completed': False, 'groups_added': 0, 'cases': [], 'failure': None,
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
             'source_sha256': SUITE['source_hashes'](), 'started_at_ns': time.time_ns()}
    namespace = Path('/proc/self/ns/pid').stat()
    value['host_process_namespace'] = {'device': namespace.st_dev, 'inode': namespace.st_ino,
        'boot_id_sha256': sha(Path('/proc/sys/kernel/random/boot_id').read_bytes())}
    previous = signal.signal(signal.SIGTERM, interrupted)
    primary = None
    try:
        value['before'] = SUITE['snapshot'](str((work / 'report.json').relative_to(ROOT)), False, include_adapter=True)
        assert value['before']['source_sha256'] == value['source_sha256']
        for mode in MODES:
            value['cases'].append(run_case(mode, work, value['source_commit']))
            atomic(work / 'report.json', value)
            assert SUITE['source_hashes']() == value['source_sha256']
            assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == value['source_commit']
            assert not subprocess.check_output(['git', 'status', '--porcelain'])
        assert len(value['cases']) == 4
        value['after'] = SUITE['snapshot'](str((work / 'report.json').relative_to(ROOT)), False, include_adapter=True)
        assert all(value['before'][k] == value['after'][k] for k in ('source_sha256', 'image', 'adapter_images'))
        value['completed'] = True
    except BaseException as error:
        primary = error
        value['failure'] = diagnosis(error)
    finally:
        signal.signal(signal.SIGTERM, previous)
        value['finished_at_ns'] = time.time_ns()
        try:
            atomic(work / 'report.json', value)
        except BaseException as error:
            if primary is None:
                primary = error
        try:
            print(json.dumps({'completed': value['completed'] and primary is None, 'groups_added': 0,
                              'report': str((work / 'report.json').relative_to(ROOT))}), flush=True)
        except BaseException as error:
            if primary is None:
                primary = error
    if primary is not None:
        raise primary


if __name__ == '__main__':
    main()
