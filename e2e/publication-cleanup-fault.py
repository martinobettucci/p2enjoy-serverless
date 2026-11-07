# @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#nettoyage-physique-refusé
# @verifies docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#nettoyage-physique-refusé
"""DEV-only permission failure on one owned inactive revision, with an independent guard."""
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shlex
import signal
import socket
import stat
import subprocess
import sys
import time
from uuid import UUID, uuid4
from control_database import read_control

ROOT = Path('/srv/p2enjoy-serverless')
DOCKER = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix:///run/user/1001/docker.sock']
assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
mode, namespace, function, revision = sys.argv[1:5]
assert all(str(UUID(value)) == value for value in (namespace, function, revision))
settings = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    words = shlex.split(line, comments=True)
    if len(words) == 1 and words[0].startswith('SERVERLESS_STATE_HOST_PATH='):
        settings['state'] = words[0].split('=', 1)[1]
STATE = Path(settings['state'])
assert STATE.parent == ROOT and STATE.resolve() == STATE
TARGET = STATE / 'artifacts' / revision
HELPER = str(ROOT / 'e2e/publication-cleanup-fault.py')


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, timeout=30, **kwargs)
    if result.returncode:
        raise RuntimeError('operator_command_failed')
    return result.stdout.strip()


def target_fd():
    fd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in ('artifacts', revision):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def identity(fd):
    info = os.fstat(fd)
    return [info.st_dev, info.st_ino, info.st_uid, info.st_gid]


def restore(expected, fd=None):
    owned = fd is None
    if owned:
        fd = target_fd()
    try:
        assert identity(fd) == expected['identity'], 'revision_inode_changed'
        previous = stat.S_IMODE(os.fstat(fd).st_mode)
        os.fchmod(fd, expected['mode'])
        assert stat.S_IMODE(os.fstat(fd).st_mode) == expected['mode'], 'mode_not_restored'
        return {'identity': identity(fd), 'previous_mode': previous, 'mode': expected['mode']}
    finally:
        if owned:
            os.close(fd)


def snapshot_once():
    with read_control(STATE / 'control.sqlite3') as db:
        row = db.execute('''SELECT r.id,r.archive_sha256,r.stored_bytes,r.deleted_at,
            f.active_revision_id,f.deleted_at AS function_deleted,n.name,n.id AS namespace_id,
            s.deleted_at AS service_deleted,n.deleted_at AS namespace_deleted
            FROM revisions r JOIN functions f ON f.id=r.function_id
            JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id
            WHERE r.id=? AND f.id=?''', (revision, function)).fetchone()
        assert row and row['namespace_id'] == namespace and re.fullmatch(r'publication-ui-[0-9a-f]{8}', row['name']), 'owned_revision_required'
        result = dict(row)
        result['instances'] = db.execute('SELECT count(*) FROM execution_instances WHERE revision_id=?', (revision,)).fetchone()[0]
        result['live_candidates'] = db.execute("SELECT count(*) FROM deployments WHERE state IN ('receiving','validating')").fetchone()[0]
        result['pending_operations'] = db.execute('SELECT count(*) FROM function_operations').fetchone()[0]
        result['pending_cleanup'] = db.execute('SELECT count(*) FROM revisions WHERE deleted_at IS NOT NULL AND stored_bytes>0').fetchone()[0]
    result['present'] = TARGET.exists()
    result['files'] = {}
    if result['present']:
        fd = target_fd()
        try:
            result['identity'] = identity(fd)
            result['mode'] = stat.S_IMODE(os.fstat(fd).st_mode)
            for path in sorted(TARGET.rglob('*')):
                info = path.lstat()
                assert stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'unexpected_artifact_entry'
                item = {'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid, 'gid': info.st_gid}
                if stat.S_ISREG(info.st_mode):
                    with path.open('rb') as stream:
                        item.update(bytes=info.st_size, sha256=hashlib.file_digest(stream, 'sha256').hexdigest())
                result['files'][str(path.relative_to(TARGET))] = item
        finally:
            os.close(fd)
    return result


def snapshot():
    # Maintenance may unlink the target between exists(), rglob() and open().
    # Retry that real observation; never turn other I/O errors into success.
    for attempt in range(50):
        try:
            return snapshot_once()
        except FileNotFoundError:
            if attempt == 49:
                raise
            time.sleep(.02)


def container_open():
    program = '''import errno,json,os,sys
from pathlib import Path
caps=[line for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('CapEff:')][0].split()[1]
assert int(caps,16)==0
result={'uid':os.getuid(),'cap_eff':caps,'uid_map':Path('/proc/self/uid_map').read_text().strip()}
try:
 fd=os.open('/state/artifacts/'+sys.argv[1],os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);os.close(fd);result['errno']=0
except OSError as error:result['errno']=error.errno
print(json.dumps(result))
'''
    return json.loads(command(DOCKER + ['exec', '-i', 'serverless-api', 'python', '-B', '-', revision], input=program))


if mode == 'guard':
    expected = json.loads(sys.argv[5])
    pid, birth = int(sys.argv[6]), sys.argv[7]
    killed = False
    try:
        process = os.pidfd_open(pid)
        try:
            current = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            if current == birth:
                args = Path('/proc', str(pid), 'cmdline').read_bytes().split(b'\0')
                assert [HELPER.encode(), b'fault', namespace.encode(), function.encode(), revision.encode()] == args[2:7], 'foreign_helper_process'
                signal.pidfd_send_signal(process, signal.SIGKILL)
                assert select.select([process], [], [], 5)[0], 'helper_not_terminated'
                killed = True
        finally:
            os.close(process)
    except (ProcessLookupError, FileNotFoundError):
        pass
    try:
        restored = restore(expected)
        emit({'event': 'guard-restored', 'revision': revision, 'helper_killed': killed, **restored})
    except FileNotFoundError:
        # Normal release may have restored the mode just before this guard ran;
        # maintenance can then remove the inode. Never recreate that directory.
        current = snapshot()
        assert current['deleted_at'] and current['stored_bytes'] == 0 and not current['present'], 'revision_disappearance_unconfirmed'
        emit({'event': 'guard-already-cleaned', 'revision': revision, 'helper_killed': killed})
elif mode == 'inspect':
    emit(snapshot())
elif mode == 'guard-evidence':
    snapshot()
    unit = sys.argv[5]
    assert re.fullmatch(r'serverless-restore-revision-[0-9a-f]{32}', unit)
    events = [json.loads(line) for line in command(['journalctl', '--no-pager', '-o', 'cat', '-u', unit + '.service']).splitlines() if line.startswith('{')]
    emit({'unit': unit, 'events': events})
elif mode == 'fault':
    delay = int(sys.argv[5])
    assert 8 <= delay <= 110
    baseline = snapshot()
    assert not any(baseline[key] for key in ('function_deleted', 'service_deleted', 'namespace_deleted', 'deleted_at', 'instances', 'live_candidates', 'pending_operations', 'pending_cleanup')), 'revision_not_idle'
    assert baseline['active_revision_id'] and baseline['active_revision_id'] != revision and baseline['stored_bytes'] > 0 and baseline['present']
    inspected = json.loads(command(DOCKER + ['inspect', 'serverless-api']))[0]
    assert inspected['State']['Running'] and 'ALL' in inspected['HostConfig']['CapDrop']
    assert any(value.startswith('no-new-privileges') for value in inspected['HostConfig']['SecurityOpt'])
    assert any(item['Source'] == str(STATE) and item['Destination'] == '/state' for item in inspected['Mounts'])
    assert container_open()['errno'] == 0
    fd = target_fd()
    expected = {'identity': identity(fd), 'mode': stat.S_IMODE(os.fstat(fd).st_mode)}
    assert expected == {key: baseline[key] for key in ('identity', 'mode')}
    unit = 'serverless-restore-revision-' + uuid4().hex
    pid = os.getpid()
    birth = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
    armed = False
    try:
        def interrupted(signum, frame):
            raise InterruptedError('operator_interrupted')
        for signum in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, interrupted)
        command(['systemd-run', '--quiet', '--collect', '--on-active=' + str(delay) + 's', '--unit', unit,
                 '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0', '--property=Type=oneshot',
                 '/usr/bin/python3', '-B', HELPER, 'guard', namespace, function, revision, json.dumps(expected), str(pid), birth])
        armed = True
        assert command(['systemctl', 'is-active', unit + '.timer']) == 'active'
        os.fchmod(fd, 0)
        denied = container_open()
        assert denied['errno'] == 13, 'control_open_not_denied'
        emit({'event': 'fault-active', 'unit': unit, 'revision': revision, 'baseline': baseline, 'control': denied, 'image': inspected['Image']})
        assert select.select([sys.stdin], [], [], delay - 2)[0], 'operator_command_timeout'
        action = sys.stdin.readline().strip()
        if action == 'kill-helper':
            os.kill(pid, signal.SIGKILL)
        if action == 'stop-helper':
            os.kill(pid, signal.SIGSTOP)
        assert action in ('release', ''), 'operator_command_invalid'
    finally:
        restored = restore(expected, fd)
        if armed:
            command(['systemctl', 'stop', unit + '.timer'])
        os.close(fd)
        emit({'event': 'fault-restored', 'revision': revision, **restored})
else:
    raise ValueError('unknown_operator_mode')
