# @spec docs/BACKLOG.md#sls-135 | docs/INSTANCE_LIMIT_RESTORATION.md#décision1352--einval-et-fin-attestée
# @verifies docs/BACKLOG.md#sls-135 | docs/INSTANCE_LIMIT_RESTORATION.md#protocole1353--vrai-noyau-et-vraie-référence
"""DEV-only real procfs/probe lifecycle; supervisor is an owned root cgroup."""
import ctypes
import errno
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import select
import shlex
import signal
import socket
import stat
import sys
import time
from uuid import UUID, uuid4

ROOT = Path('/srv/p2enjoy-serverless')
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.ptrace.restype = ctypes.c_long
LIBC.ptrace.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
WALL = 0x40000000


def process(pid):
    proc = Path('/proc', str(pid))
    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'birth': fields[19], 'state': fields[0], 'parent': int(fields[1]),
            'cgroup': (proc / 'cgroup').read_text()}


def until(action, reason, seconds=5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        result = action()
        if result:
            return result
        time.sleep(.005)
    raise TimeoutError(reason)


def main():
    mode, campaign = sys.argv[1:]
    assert mode in ('before-fix', 'after-fix') and str(UUID(campaign)) == campaign
    assert socket.gethostname() == 'infra-serverless' and os.geteuid() == 0
    own_cgroup = Path('/proc/self/cgroup').read_text()
    unit = 'serverless-process-reference-' + campaign + '.service'
    assert unit in own_cgroup, 'owned_root_unit_required'
    work = ROOT / 'qualification-history' / ('process-reference-lifecycle-' + campaign)
    work.mkdir(mode=0o700)
    report = work / 'receipt.json'
    value = {'completed': False, 'cleanup': False, 'mode': mode, 'campaign': campaign,
             'unit': unit, 'kernel': list(os.uname()), 'checks': [], 'children': [],
             'started_at_ns': time.time_ns(), 'cgroup': own_cgroup,
             'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                         ('e2e/process-reference-lifecycle.py', 'e2e/storage-legacy-environment.py',
                          'e2e/control_database.py', 'storage/agent_system.py')}}
    def save():
        pending = report.with_suffix('.pending')
        with pending.open('w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        pending.replace(report)
    def emit(event):
        print(json.dumps({'event': event, 'campaign': campaign, 'receipt': str(report)}), flush=True)
    children = []
    lock = None
    helper = None
    save()
    try:
        emit('prepared')
        assert select.select([sys.stdin], [], [], 30)[0], 'supervisor_begin_deadline'
        assert sys.stdin.readline() == 'begin\n', 'explicit_supervisor_begin_required'
        spec = importlib.util.spec_from_file_location('real_storage_qualification', ROOT / 'e2e/storage-legacy-environment.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        settings = {}
        for line in Path('/etc/spark/env').read_text().splitlines():
            fields = shlex.split(line, comments=True)
            if len(fields) == 1 and '=' in fields[0]:
                key, content = fields[0].split('=', 1)
                if key.startswith('SERVERLESS_'):
                    settings[key] = content
        assert settings['SERVERLESS_PUBLIC_URL'] == 'https://serverless.lelabs.tech'
        account = pwd.getpwnam('spark-docker')
        paths = dict(zip(('state', 'storage', 'channel'), [settings[key] for key in
            ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_STORAGE_SOCKET_DIR_HOST')]))
        assert len(set(paths.values())) == 3
        for path in paths.values():
            assert Path(path).parent == ROOT and str(Path(path).resolve()) == path
        item = {'paths': paths, 'original_dirs': {k: helper.identity(p) for k, p in paths.items()},
                'docker': ['runuser', '-u', 'spark-docker', '--', 'docker', '--host',
                           'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]}
        item['original'] = helper.container(item, 'serverless-api')
        value['image'] = item['original']['image']
        assert value['image'] == 'sha256:f016a1b71cb055c4f4c4e2fb2a2622c67c93f7a6ec26b39ec7e663cd9de4c0c7'
        assert item['original']['running'] and item['original']['status'] == 'healthy'
        lock = os.open(helper.LOCK_PATH, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        info = os.fstat(lock)
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o600
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        helper.LOCK = lock
        def check_clear(name):
            helper.no_references(item, allow_original=True)
            value['checks'].append({'name': name, 'status': 'passed'}); save()
        def check_live(name):
            try:
                helper.no_references(item, allow_original=True)
            except AssertionError as error:
                assert str(error) == 'volume_process_retained', 'different_live_refusal'
                value['checks'].append({'name': name, 'status': 'passed', 'reason': str(error)}); save()
            else:
                raise AssertionError('real_live_reference_accepted')
        def spawn_probe():
            args = [sys.executable, '-I', '-B', str(ROOT / 'storage/agent_system.py'),
                    '--probe', str(Path(paths['storage']) / 'mounts'), str(uuid4())]
            pid = os.fork()
            if pid == 0:
                try:
                    null = os.open('/dev/null', os.O_RDWR)
                    for fd in (0, 1, 2): os.dup2(null, fd)
                    if null > 2: os.close(null)
                    if LIBC.ptrace(0, 0, None, None) == -1: os._exit(125)
                    os.execve(sys.executable, args, {})
                finally:
                    os._exit(126)
            child = {'pid': pid, 'descriptor': None, 'identity': None, 'reaped': False, 'public': {'pid': pid}}
            children.append(child); value['children'].append(child['public'])
            child['descriptor'] = os.pidfd_open(pid)
            def stopped():
                result = os.waitpid(pid, os.WNOHANG | os.WUNTRACED | WALL)
                return result if result[0] else None
            result = until(stopped, 'probe_exec_stop_missing')
            if os.WIFEXITED(result[1]) or os.WIFSIGNALED(result[1]):
                child['reaped'] = True; child['public']['unexpected_joined_status'] = result[1]
            assert result[0] == pid and os.WIFSTOPPED(result[1]) and os.WSTOPSIG(result[1]) == signal.SIGTRAP and result[1] >> 16 == 0
            pinned = process(pid); child['identity'] = pinned
            assert pinned['parent'] == os.getpid() and pinned['state'] in ('t', 'T') and pinned['cgroup'] == own_cgroup
            proc = Path('/proc', str(pid))
            assert (proc / 'exe').resolve() == Path(sys.executable).resolve()
            command = (proc / 'cmdline').read_bytes()
            assert command == b'\0'.join(os.fsencode(arg) for arg in args) + b'\0'
            public = pinned | {'exec_stop_status': result[1], 'command_sha256': hashlib.sha256(command).hexdigest(),
                               'probe_source_sha256': value['sources']['storage/agent_system.py']}
            child['public'].update(public); save()
            return child
        def kill_to_zombie(child):
            current = process(child['pid'])
            assert current['parent'] == os.getpid() and (child['identity'] is None or current['birth'] == child['identity']['birth'])
            if current['state'] != 'Z':
                signal.pidfd_send_signal(child['descriptor'], signal.SIGKILL)
            assert select.select([child['descriptor']], [], [], 5)[0], 'probe_pidfd_not_ready'
            ended = until(lambda: (now if (now := process(child['pid']))['state'] == 'Z' else None), 'probe_not_zombie')
            assert ended['birth'] == current['birth'] and ended['parent'] == os.getpid()
            child.setdefault('public', {})['zombie'] = ended
            return ended
        def reap(child):
            def waited():
                result = os.waitpid(child['pid'], os.WNOHANG | WALL)
                return result if result[0] else None
            waited = until(waited, 'probe_not_joined')
            assert os.WIFSIGNALED(waited[1]) and os.WTERMSIG(waited[1]) == signal.SIGKILL
            child['reaped'] = True
            assert not Path('/proc', str(child['pid'])).exists(), 'reaped_probe_still_present'
            child['public']['joined_status'] = waited[1]
        check_clear('real-baseline-clear')
        first = spawn_probe()
        check_live('real-live-probe-refused')
        kill_to_zombie(first)
        try:
            Path('/proc', str(first['pid']), 'mountinfo').read_text()
        except OSError as error:
            assert error.errno == errno.EINVAL and error.filename == '/proc/' + str(first['pid']) + '/mountinfo'
            first['public']['mountinfo_error'] = {'type': type(error).__name__, 'errno': error.errno}
        else:
            raise AssertionError('native_zombie_mountinfo_einval_required')
        save()
        if mode == 'before-fix':
            try:
                helper.no_references(item, allow_original=True)
            except OSError as error:
                assert error.errno == errno.EINVAL and error.filename == '/proc/' + str(first['pid']) + '/mountinfo'
                value['checks'].append({'name': 'real-old-guard-einval-reproduced', 'status': 'passed', 'errno': error.errno, 'pid': first['pid']})
            else:
                raise AssertionError('old_guard_failure_not_reproduced')
        else:
            check_clear('real-zombie-accepted')
            second = spawn_probe()
            check_live('real-live-probe-refused-with-zombie')
            kill_to_zombie(second); reap(second)
            check_clear('real-zombie-still-accepted')
            helper.LOCK = None; os.close(lock); lock = None
            value['held_zombie'] = process(first['pid']); save(); emit('zombie-held')
            assert select.select([sys.stdin], [], [], 240)[0], 'real_http_client_deadline'
            assert sys.stdin.readline() == 'release\n', 'explicit_http_release_required'
            assert process(first['pid'])['birth'] == first['identity']['birth'] and process(first['pid'])['state'] == 'Z'
            value['checks'].append({'name': 'zombie-retained-through-real-http-client', 'status': 'passed'})
        value['completed'] = True
    except BaseException as error:
        value['failure'] = {'type': type(error).__name__, 'message_sha256': hashlib.sha256(str(error).encode()).hexdigest(),
                            'errno': getattr(error, 'errno', None)}
        raise
    finally:
        failures = []
        for child in reversed(children):
            try:
                if not child['reaped']:
                    if child['descriptor'] is None: child['descriptor'] = os.pidfd_open(child['pid'])
                    kill_to_zombie(child); reap(child)
            except BaseException as error:
                failures.append({'pid': child['pid'], 'phase': 'kill-join', 'type': type(error).__name__, 'errno': getattr(error, 'errno', None)})
            finally:
                if child['descriptor'] is not None:
                    try:
                        descriptor = child['descriptor']; os.close(descriptor); child['descriptor'] = None
                        try: fcntl.fcntl(descriptor, fcntl.F_GETFD)
                        except OSError as error: assert error.errno == errno.EBADF
                        else: raise AssertionError('probe_pidfd_retained')
                        child['public']['pidfd_closed'] = True
                    except BaseException as error:
                        failures.append({'pid': child['pid'], 'phase': 'close-pidfd', 'type': type(error).__name__, 'errno': getattr(error, 'errno', None)})
        if lock is not None:
            helper.LOCK = None; os.close(lock)
        value['cleanup_failures'] = failures
        value['cleanup'] = not failures and all(child['reaped'] and child['descriptor'] is None for child in children)
        value['finished_at_ns'] = time.time_ns(); save(); emit('finished')
    assert value['completed'] and value['cleanup']


if __name__ == '__main__':
    main()
