# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#trois-preuves-de-garde-avant-les-parcours-fonctionnels
"""Actual DEV route-file permission fault with a frozen, independent restorer.

All declarations implement the same bounded proof contract. The source contents
are never written, copied to a replacement registry, renamed or recreated.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib.request
from uuid import UUID, uuid4

ROOT = Path('/srv/p2enjoy-serverless')
HELPER = ROOT / 'e2e/invocation-source-permissions.py'
LOCK = Path('/run/serverless-route-permissions.lock')
PREFIX = 'serverless-restore-route-permissions-'
DOCKER = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix:///run/user/1001/docker.sock']


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, timeout=35, **options):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, **options)
    assert result.returncode == 0, 'permission_operator_command_failed'
    return result.stdout.strip()


def save(folder, name, value):
    pending = folder / (name + '.' + uuid4().hex + '.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(json.dumps(value) + '\n'); stream.flush(); os.fsync(stream.fileno())
    # Publish once: even a later recovery cannot replace an earlier receipt.
    os.link(pending, folder / name, follow_symlinks=False); pending.unlink()
    parent = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(parent)
    finally: os.close(parent)


def target():
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in ('etc', 'spark'):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent); parent = child
            info = os.fstat(parent)
            assert info.st_uid == 0 and not info.st_mode & stat.S_IWOTH, 'unsafe_source_parent'
        fd = os.open('routes', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        return fd, parent
    except BaseException:
        os.close(parent); raise


def attributes(info):
    assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1 and 0 < info.st_size <= 65536
    return {'device': info.st_dev, 'inode': info.st_ino, 'uid': info.st_uid, 'gid': info.st_gid,
            'bytes': info.st_size, 'mode': stat.S_IMODE(info.st_mode), 'mtime_ns': str(info.st_mtime_ns),
            'ctime_ns': str(info.st_ctime_ns), 'links': info.st_nlink}


def source(fd, parent):
    before = attributes(os.fstat(fd)); raw = os.pread(fd, 65537, 0)
    after = attributes(os.fstat(fd)); named = attributes(os.stat('routes', dir_fd=parent, follow_symlinks=False))
    assert before == after == named and len(raw) == before['bytes'], 'source_observation_changed'
    return {**before, 'sha256': hashlib.sha256(raw).hexdigest()}


def binding(value):
    return {k: v for k, v in value.items() if k not in ('mode', 'ctime_ns')}


def restore_file(expected, fd, parent):
    before = source(fd, parent)
    assert binding(before) == binding(expected), 'source_identity_or_content_changed'
    assert before['mode'] in (0, expected['mode']), 'source_permissions_changed_by_other_owner'
    if before['mode'] != expected['mode']: os.fchmod(fd, expected['mode'])
    after = source(fd, parent)
    assert binding(after) == binding(expected) and after['mode'] == expected['mode']
    return {'before': before, 'after': after}


def identity(name):
    value = json.loads(command(DOCKER + ['inspect', name]))[0]
    return value, [value['Id'], value['Image'], value['State']['StartedAt']]


def probe():
    program = '''import hashlib,json,os
from pathlib import Path
caps=next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('CapEff:'))
assert int(caps,16)==0
result={'uid':os.getuid(),'gid':os.getgid(),'cap_eff':caps}
try:
 fd=os.open('/spark/routes',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:raw=os.read(fd,65537)
 finally:os.close(fd)
 result.update(errno=0,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
except OSError as error:result['errno']=error.errno
print(json.dumps(result))
'''
    return json.loads(command(DOCKER + ['exec', '-i', 'serverless-api', 'python', '-B', '-'], input=program))


def validated_control(item):
    control, current = identity('serverless-api'); reference, peer = identity('serverless-runtime-reference')
    assert current == item['control'] and peer == item['reference'], 'installation_replaced'
    assert control['State']['Running'] and reference['State']['Running']
    assert control['State']['Health']['Status'] == reference['State']['Health']['Status'] == 'healthy'
    opened = probe()
    assert opened['errno'] == 0 and opened['sha256'] == item['source']['sha256'] and opened['bytes'] == item['source']['bytes']
    with urllib.request.urlopen('http://127.0.0.1:18090/healthz', timeout=5) as response:
        assert response.status == 200 and json.load(response)['status'] == 'ok'
    return {'control': current, 'reference': peer, 'open': opened, 'local_health': True}


def acquire(expected=None, seconds=0):
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o600
        pair = [info.st_dev, info.st_ino]
        if expected is not None: assert pair == expected, 'global_lock_replaced'
        deadline = time.monotonic() + seconds
        while True:
            try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); return fd, pair
            except BlockingIOError:
                assert time.monotonic() < deadline, 'permission_operator_busy'; time.sleep(.05)
    except BaseException:
        os.close(fd); raise


def load(folder):
    assert folder.parent == Path('/run') and re.fullmatch(PREFIX + r'[0-9a-f]{32}', folder.name)
    info = folder.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700
    for name in ('identity.json', 'operator.py'):
        value = (folder / name).lstat(); assert stat.S_ISREG(value.st_mode) and value.st_uid == 0
    item = json.loads((folder / 'identity.json').read_text())
    assert hashlib.sha256((folder / 'operator.py').read_bytes()).hexdigest() == item['operator_sha256']
    return item


def stop_timer(unit):
    stopped = subprocess.run(['systemctl', 'stop', unit + '.timer'], capture_output=True, timeout=10)
    values = dict(line.split('=', 1) for line in command(['systemctl', 'show', unit + '.timer', '--property=LoadState', '--property=ActiveState']).splitlines())
    absent = values == {'LoadState': 'not-found', 'ActiveState': 'inactive'}
    assert stopped.returncode == 0 or (stopped.returncode == 5 and absent), 'guard_timer_stop_failed'
    assert values.get('ActiveState') == 'inactive'
    deadline = time.monotonic() + 40
    while unit_state(unit + '.service') not in ('inactive', 'unknown'):
        assert time.monotonic() < deadline, 'guard_service_still_running'; time.sleep(.1)
    return {'stop_exit_code': stopped.returncode, 'native_state': values, 'absence_confirmed': absent}


def unit_state(unit):
    result = subprocess.run(['systemctl', 'is-active', unit], capture_output=True, text=True, timeout=10)
    assert result.returncode in (0, 3, 4), 'guard_state_unavailable'
    return result.stdout.strip()


def join_helper(item):
    result = {'helper_killed': False, 'helper_absent': True}
    try: fd = os.pidfd_open(item['helper_pid'])
    except ProcessLookupError: return result
    try:
        if select.select([fd], [], [], 0)[0]: return result
        try:
            row = Path('/proc', str(item['helper_pid']), 'stat').read_text().rsplit(')', 1)[1].split()
            if row[19] != item['helper_birth']:
                result['pid_reused_not_signalled'] = True; return result
            assert Path('/proc', str(item['helper_pid']), 'cmdline').read_bytes().split(b'\0')[:-1] == [v.encode() for v in item['helper_argv']]
            signal.pidfd_send_signal(fd, signal.SIGKILL)
            assert select.select([fd], [], [], 10)[0], 'helper_death_not_confirmed'
            result['helper_killed'] = True
        except (FileNotFoundError, ProcessLookupError): pass
        return result
    finally: os.close(fd)


def restore(folder, independent, held=None):
    item = load(folder); result = {'event': 'restored', 'completed': False, 'independent': independent,
                                  'source_restored': False, 'unit': folder.name, 'at_ns': str(time.time_ns()),
                                  'receipt_name': 'restoration-' + uuid4().hex + '.json'}
    lock = fd = parent = None
    try:
        if independent:
            result.update(join_helper(item)); lock, _ = acquire(item['lock_identity'], 10)
        if held is None: fd, parent = target()
        else: fd, parent = held
        result['source'] = restore_file(item['source'], fd, parent)
        result['source_restored'] = True
        # Source restoration must never wait for Docker or application health.
        result['installation'] = validated_control(item)
        result['completed'] = True
    except BaseException as error:
        result['failure_type'] = type(error).__name__
    finally:
        if held is None:
            if fd is not None: os.close(fd)
            if parent is not None: os.close(parent)
        result['finished_monotonic_ns'] = str(time.monotonic_ns())
        try: save(folder, result['receipt_name'], result)
        finally:
            if lock is not None: os.close(lock)
    return result


def last_receipt(folder):
    records = []
    for path in folder.glob('restoration-*.json'):
        info = path.lstat(); assert stat.S_ISREG(info.st_mode) and info.st_uid == 0
        value = json.loads(path.read_text())
        assert value['receipt_name'] == path.name and re.fullmatch(r'[0-9]+', value['finished_monotonic_ns'])
        records.append(value)
    return max(records, key=lambda value: int(value['finished_monotonic_ns'])) if records else {'event': 'pending'}


def owned_idle(scope):
    sys.path.insert(0, str(ROOT / 'e2e'))
    from control_database import read_control
    with read_control(ROOT / 'state/control.sqlite3') as db:
        expected = []
        if scope is not None:
            assert set(scope) == {'namespace_id', 'function_id', 'nonce'}
            for value in scope.values(): assert str(UUID(value)) == value
            row = db.execute('''SELECT n.name,n.description,s.name AS service_name,s.description AS service_description
                FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id
                WHERE f.id=? AND n.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL AND n.deleted_at IS NULL''',
                (scope['function_id'], scope['namespace_id'])).fetchone()
            assert row and row['name'] == 'source-access-' + scope['nonce'][:8] and row['description'] == scope['nonce']
            assert row['service_name'] == 'source-access-fixture' and row['service_description'] == scope['nonce']
            expected = [scope['function_id']]
        assert sorted(v[0] for v in db.execute('SELECT id FROM functions WHERE deleted_at IS NULL')) == expected, 'only_owned_function_required'
        for query in ("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
                      "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
                      'SELECT count(*) FROM execution_instances', 'SELECT count(*) FROM function_operations'):
            assert db.execute(query).fetchone()[0] == 0, 'quiet_installation_required'


def read_command(seconds):
    deadline = time.monotonic() + seconds; raw = bytearray()
    while True:
        left = deadline - time.monotonic()
        assert left > 0 and select.select([sys.stdin], [], [], left)[0], 'permission_command_timeout'
        value = os.read(0, 1); assert value, 'permission_command_eof'
        if value == b'\n':
            assert raw in (b'release', b'kill-helper', b'stop-helper'), 'permission_command_invalid'
            return raw.decode()
        raw.extend(value); assert len(raw) <= 11, 'permission_command_too_long'


def fault(args):
    assert Path(__file__) == HELPER and re.fullmatch(r'sha256:[0-9a-f]{64}', args.image or '')
    assert 12 <= args.delay <= 120
    scope = json.loads(args.scope) if args.scope else None
    global_fd, pair = acquire(); fd = parent = None; folder = None; armed = False
    try:
        owned_idle(scope); fd, parent = target(); before = source(fd, parent)
        assert before['mode'] != 0
        control, control_identity = identity('serverless-api'); reference, reference_identity = identity('serverless-runtime-reference')
        assert control['Image'] == args.image and control['State']['Running'] and reference['State']['Running']
        assert control['State']['Health']['Status'] == reference['State']['Health']['Status'] == 'healthy'
        assert 'ALL' in control['HostConfig']['CapDrop'] and any(v.startswith('no-new-privileges') for v in control['HostConfig']['SecurityOpt'])
        assert any(v['Source'] == '/etc/spark' and v['Destination'] == '/spark' and v['RW'] is False for v in control['Mounts'])
        opened = probe(); assert opened['errno'] == 0 and opened['sha256'] == before['sha256']
        folder = Path('/run') / (PREFIX + uuid4().hex); folder.mkdir(mode=0o700)
        raw = HELPER.read_bytes(); copy = folder / 'operator.py'; copy.write_bytes(raw); copy.chmod(0o400)
        helper_stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
        item = {'source': before, 'control': control_identity, 'reference': reference_identity, 'lock_identity': pair,
                'helper_pid': os.getpid(), 'helper_birth': helper_stat[19],
                'helper_argv': [v.decode() for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')[:-1]],
                'operator_sha256': hashlib.sha256(raw).hexdigest(), 'scope': scope}
        save(folder, 'identity.json', item)
        command(['systemd-run', '--quiet', '--collect', '--unit=' + folder.name, '--on-active=' + str(args.delay) + 's',
                 '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0', '--property=RuntimeMaxSec=120s',
                 '--property=TimeoutStopSec=5s', '/usr/bin/python3', '-I', str(copy), 'guard', '--folder', str(folder)])
        armed = True; assert unit_state(folder.name + '.timer') == 'active'
        emit({'event': 'guard-armed', 'unit': folder.name, 'identity': item})
        os.fchmod(fd, 0); denied = probe(); assert denied['errno'] == 13, 'control_open_not_denied'
        assert binding(source(fd, parent)) == binding(before)
        emit({'event': 'fault-active', 'unit': folder.name, 'source': source(fd, parent), 'control_open': denied})
        action = read_command(args.delay + 30)
        if action == 'kill-helper':
            emit({'event': 'helper-signal', 'signal': 'SIGKILL'}); os.kill(os.getpid(), signal.SIGKILL)
        if action == 'stop-helper':
            emit({'event': 'helper-signal', 'signal': 'SIGSTOP'}); os.kill(os.getpid(), signal.SIGSTOP)
            raise AssertionError('suspended_helper_resumed_without_guard')
    finally:
        result = restore(folder, False, (fd, parent)) if armed else None
        if fd is not None: os.close(fd)
        if parent is not None: os.close(parent)
        os.close(global_fd)
        if result is not None:
            if result['source_restored']: result['timer_stop'] = stop_timer(folder.name)
            emit(result); assert result['completed'], 'source_restoration_incomplete'


def supervise(args):
    assert Path(__file__) == HELPER
    command_line = [sys.executable, '-B', str(HELPER), 'fault', '--image', args.image, '--delay', str(args.delay)]
    if args.scope: command_line += ['--scope', args.scope]
    child = subprocess.Popen(command_line, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    emit({'event': 'helper-started', 'pid': child.pid})
    signal.alarm(600)
    while True:
        pid, observed = os.waitpid(child.pid, os.WUNTRACED)
        assert pid == child.pid
        if os.WIFSTOPPED(observed):
            emit({'event': 'helper-stopped', 'pid': pid, 'signal': signal.Signals(os.WSTOPSIG(observed)).name})
        else:
            assert os.WIFEXITED(observed) or os.WIFSIGNALED(observed)
            child.returncode = os.waitstatus_to_exitcode(observed)
            emit({'event': 'helper-exited', 'pid': pid, 'returncode': child.returncode,
                  'signal': signal.Signals(os.WTERMSIG(observed)).name if os.WIFSIGNALED(observed) else None})
            return


def main():
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    capabilities = int(next(v.split()[1] for v in Path('/proc/self/status').read_text().splitlines() if v.startswith('CapEff:')), 16)
    assert capabilities & 6, 'root_dac_open_capability_required'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('fault', 'supervise', 'guard', 'evidence', 'recover', 'disarm'))
    parser.add_argument('--image'); parser.add_argument('--scope'); parser.add_argument('--delay', type=int, default=60)
    parser.add_argument('--folder', type=Path); args = parser.parse_args()
    if args.mode == 'fault': fault(args); return
    if args.mode == 'supervise': supervise(args); return
    item = load(args.folder)
    if args.mode == 'guard':
        assert Path(__file__) == args.folder / 'operator.py'
        signal.alarm(115); result = restore(args.folder, True); emit(result)
        assert result['completed'], 'independent_restoration_incomplete'; return
    if args.mode == 'recover':
        command(['/usr/bin/python3', '-I', str(args.folder / 'operator.py'), 'guard', '--folder', str(args.folder)], timeout=125)
    result = last_receipt(args.folder)
    if args.mode in ('recover', 'disarm'):
        assert result.get('completed') and result.get('source_restored'), 'successful_restoration_required'
        result['timer_stop'] = stop_timer(args.folder.name)
        fd, parent = target()
        try:
            current = source(fd, parent); assert binding(current) == binding(item['source']) and current['mode'] == item['source']['mode']
        finally: os.close(fd); os.close(parent)
        result['current_installation'] = validated_control(item)
    result.update(identity=item, timer_state=unit_state(args.folder.name + '.timer'), service_state=unit_state(args.folder.name + '.service'))
    emit(result)


if __name__ == '__main__':
    try: main()
    except BaseException as error:
        emit({'completed': False, 'failure_type': type(error).__name__}); raise SystemExit(1)
