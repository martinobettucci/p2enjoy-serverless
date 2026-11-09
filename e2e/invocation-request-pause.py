# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#barrière-native-de-pause-et-libération
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#barrière-native-de-pause-et-libération
"""Pause one real catalogue GET after recv; detach/resume without killing control.

All declarations implement this bounded DEV-only proof contract. Only the public
request line is read; buffers, registers and system-call results stay untouched.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
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
from native_control_observer import NativeObserver


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, timeout=40):
    value = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    assert value.returncode == 0, 'pause_operator_command_failed'
    return value.stdout.strip()


def birth(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


def control_command(expected, seconds):
    deadline = time.monotonic() + seconds
    received = bytearray()
    while True:
        remaining = deadline - time.monotonic()
        assert remaining > 0 and select.select([sys.stdin], [], [], remaining)[0], 'release_command_timeout'
        value = os.read(sys.stdin.fileno(), 1)
        assert value, 'release_command_eof'
        if value == b'\n':
            assert received == expected, 'release_command_invalid'
            return
        received.extend(value)
        assert len(received) <= len(expected), 'release_command_too_long'


def status(unit):
    value = subprocess.run(['systemctl', 'is-active', unit], capture_output=True, text=True, timeout=10)
    assert value.returncode in (0, 3, 4), 'unexpected_guard_status'
    return value.stdout.strip()


def stop_timer(unit):
    stopped = subprocess.run(['systemctl', 'stop', unit + '.timer'], capture_output=True, text=True, timeout=10)
    observed = subprocess.run(['systemctl', 'show', unit + '.timer', '--property=LoadState', '--property=ActiveState'],
                              capture_output=True, text=True, timeout=10)
    assert observed.returncode == 0, 'timer_state_unavailable'
    fields = dict(line.split('=', 1) for line in observed.stdout.splitlines())
    absent = fields == {'LoadState': 'not-found', 'ActiveState': 'inactive'}
    assert stopped.returncode == 0 or (stopped.returncode == 5 and absent), 'timer_stop_failed'
    assert fields.get('ActiveState') == 'inactive', 'resume_timer_still_active'
    return {'stop_exit_code': stopped.returncode, 'absence_confirmed': absent, 'native_state': fields}


# Frozen independent resume program, armed before any ptrace attachment.
RESUME = r'''import fcntl,hashlib,json,os,select,signal,socket,stat,subprocess,sys,time,urllib.request
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(100)
folder=Path(sys.argv[1]);info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith('serverless-resume-invocation-request-')
assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
assert not (folder/'identity.json').is_symlink() and not (folder/'resume.py').is_symlink()
item=json.loads((folder/'identity.json').read_text());independent=len(sys.argv)>2
assert hashlib.sha256((folder/'resume.py').read_bytes()).hexdigest()==item['resume_sha256']
lock=os.open(folder/'resume.lock',os.O_RDWR|os.O_NOFOLLOW)
info=os.fstat(lock)
assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']
fcntl.flock(lock,fcntl.LOCK_EX)
result={'event':'resumed','independent':independent,'pid':item['pid'],'container_id':item['container_id'],'image':item['image']}
if independent:
 try:fd=os.pidfd_open(item['helper_pid'])
 except ProcessLookupError:pass
 else:
  try:
   row=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()
   assert row[19]==item['helper_birth'],'helper_pid_reused'
   signal.pidfd_send_signal(fd,signal.SIGKILL)
   assert select.select([fd],[],[],10)[0],'helper_death_unconfirmed'
   result['observer_killed_by_guard']=True
  except (ProcessLookupError,FileNotFoundError):pass
  finally:os.close(fd)
 result['observer_gone']=True
def inspect(name):
 return json.loads(subprocess.run(item['docker']+['inspect',name],capture_output=True,text=True,check=True,timeout=20).stdout)[0]
current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')
assert [current['Id'],current['Image'],current['State']['StartedAt']]==item['control'] and current['State']['Running'],'control_replaced_or_stopped'
assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running'],'reference_replaced_or_stopped'
fd=os.pidfd_open(item['pid'])
try:
 assert Path('/proc',str(item['pid']),'stat').read_text().rsplit(')',1)[1].split()[19]==item['birth'],'control_pid_reused'
 assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_owner_changed'
 deadline=time.monotonic()+8
 while True:
  tracer=next(line.split(':',1)[1].strip() for line in Path('/proc',str(item['pid']),'status').read_text().splitlines() if line.startswith('TracerPid:'))
  if tracer=='0':break
  assert time.monotonic()<deadline,'observer_still_attached';time.sleep(.02)
 signal.pidfd_send_signal(fd,signal.SIGCONT)
finally:os.close(fd)
deadline=time.monotonic()+30
while True:
 try:
  with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:assert response.status==200
  current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')
  assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'
  break
 except (OSError,AssertionError):
  assert time.monotonic()<deadline,'control_health_not_resumed';time.sleep(.2)
assert [current['Id'],current['Image'],current['State']['StartedAt']]==item['control']
assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference']
result.update(healthy=True,reference_unchanged=True,control_start_unchanged=True,tracer_absent=True)
name='resumed-independent.json' if independent else 'resumed.json'
pending=folder/(name+'.pending');pending.write_text(json.dumps(result)+'\n');pending.replace(folder/name)
print(json.dumps(result),flush=True)
'''


assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
assert platform.machine() == 'x86_64', 'x86_64_required'
mode, namespace, service, function, nonce, image = sys.argv[1:7]
assert mode in ('pause', 'loss', 'evidence', 'recover', 'disarm') and len(sys.argv) in (7, 8)
for value in (namespace, service, function, nonce):
    assert str(UUID(value)) == value, 'canonical_uuid_required'
assert re.fullmatch(r'sha256:[0-9a-f]{64}', image), 'exact_control_image_required'
settings = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields = shlex.split(line, comments=True)
    if len(fields) == 1 and '=' in fields[0]:
        key, value = fields[0].split('=', 1)
        if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_DOCKER_SOCKET_HOST'):
            settings[key] = value
control = Path(settings['SERVERLESS_STATE_HOST_PATH']) / 'control.sqlite3'
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]
with read_control(control) as db:
    owner = db.execute('SELECT name,description FROM namespaces WHERE id=? AND deleted_at IS NULL', (namespace,)).fetchone()
    assert owner and owner['name'] == 'invocation-route-pause-' + nonce[:8] and owner['description'] == nonce, 'owned_namespace_required'
    row = db.execute('SELECT name,description FROM services WHERE id=? AND namespace_id=? AND deleted_at IS NULL', (service, namespace)).fetchone()
    assert row and row['name'] == 'request-pause-fixture' and row['description'] == nonce, 'owned_service_required'
    row = db.execute('SELECT name,active_revision_id FROM functions WHERE id=? AND service_id=? AND deleted_at IS NULL', (function, service)).fetchone()
    assert row and row['name'] == 'route-entry' and row['active_revision_id'], 'owned_published_function_required'
    revision = row['active_revision_id']

if mode in ('evidence', 'recover', 'disarm'):
    assert len(sys.argv) == 8
    unit = sys.argv[7]
    assert re.fullmatch(r'serverless-resume-invocation-request-[0-9a-f]{32}', unit)
    folder = Path('/run') / unit
    assert not folder.is_symlink() and stat.S_IMODE(folder.stat().st_mode) == 0o700
    item = json.loads((folder / 'identity.json').read_text())
    assert [item['namespace_id'], item['service_id'], item['function_id'], item['nonce'], item['image']] == [namespace, service, function, nonce, image]
    if mode == 'recover':
        # Kill/join only the positively identified helper, never the control.
        command(['/usr/bin/python3', '-I', str(folder / 'resume.py'), str(folder), 'guard'], timeout=110)
    path = folder / 'resumed-independent.json'
    if not path.exists():
        path = folder / 'resumed.json'
    result = json.loads(path.read_text()) if path.exists() else {'event': 'pending'}
    if mode == 'disarm':
        assert result.get('healthy') and result.get('tracer_absent'), 'successful_resume_required'
    if mode in ('recover', 'disarm'):
        result['timer_stop'] = stop_timer(unit)
        deadline = time.monotonic() + 40
        while status(unit + '.service') not in ('inactive', 'unknown'):
            assert time.monotonic() < deadline, 'resume_guard_still_running'
            time.sleep(.1)
    result.update(unit=unit, timer_state=status(unit + '.timer'), service_state=status(unit + '.service'), identity=item)
    if mode in ('recover', 'disarm'):
        assert result['timer_state'] in ('inactive', 'unknown') and result['service_state'] in ('inactive', 'unknown')
    emit(result)
    sys.exit(0)

assert len(sys.argv) == 7
with read_control(control) as db:
    assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0] == 1, 'only_owned_function_required'
    for sql in ("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
                "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
                'SELECT count(*) FROM function_operations', 'SELECT count(*) FROM execution_instances'):
        assert db.execute(sql).fetchone()[0] == 0, 'quiet_installation_required'
current = json.loads(command(docker + ['inspect', 'serverless-api']))[0]
reference = json.loads(command(docker + ['inspect', 'serverless-runtime-reference']))[0]
assert current['Image'] == image and current['State']['Running'] and reference['State']['Running']
assert current['State']['Health']['Status'] == reference['State']['Health']['Status'] == 'healthy'
init = current['State']['Pid']
descendants = [init]
for parent in descendants:
    descendants.extend(int(v) for v in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
pids = [pid for pid in descendants if Path(os.readlink(f'/proc/{pid}/exe')).name.startswith('python')
        and Path('/proc', str(pid), 'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00')]
assert len(pids) == 1, 'unique_control_process_required'
pid = pids[0]
cgroup = Path('/proc', str(pid), 'cgroup').read_text()
assert cgroup == Path('/proc', str(init), 'cgroup').read_text()
assert re.search(r'^TracerPid:\s+0$', Path('/proc', str(pid), 'status').read_text(), re.M), 'existing_tracer_refused'
unit = 'serverless-resume-invocation-request-' + uuid4().hex
folder = Path('/run') / unit
folder.mkdir(mode=0o700)
lock = os.open(folder / 'resume.lock', os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
lock_info = os.fstat(lock)
os.close(lock)
item = {'namespace_id': namespace, 'service_id': service, 'function_id': function, 'nonce': nonce,
        'revision_id': revision, 'container_id': current['Id'], 'image': image, 'docker': docker,
        'control': [current['Id'], image, current['State']['StartedAt']],
        'reference': [reference['Id'], reference['Image'], reference['State']['StartedAt']],
        'pid': pid, 'birth': birth(pid), 'cgroup': cgroup, 'helper_pid': os.getpid(), 'helper_birth': birth(os.getpid()),
        'lock_identity': [lock_info.st_dev, lock_info.st_ino],
        'resume_sha256': hashlib.sha256(RESUME.encode()).hexdigest()}
(folder / 'identity.json').write_text(json.dumps(item))
(folder / 'resume.py').write_text(RESUME)
observer, armed = NativeObserver(pid), False
try:
    command(['systemd-run', '--quiet', '--collect', '--unit=' + unit, '--on-active=' + ('12s' if mode == 'loss' else '70s'),
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '--property=RuntimeMaxSec=110s', '--property=TimeoutStopSec=5s',
             '/usr/bin/python3', '-I', str(folder / 'resume.py'), str(folder), 'guard'])
    armed = True
    assert status(unit + '.timer') == 'active', 'resume_guard_not_armed'
    emit({'event': 'guard-armed', 'unit': unit, 'identity': item})
    observer.start()
    emit({'event': 'armed', 'unit': unit})
    expected = f'GET /api/functions/{function}/invocation-urls?limit=5&offset=0 HTTP/1.1\r\n'.encode('ascii')
    pending, offsets, gated = None, {}, False
    deadline = time.monotonic() + (8 if mode == 'loss' else 40)
    observer.resume()
    while not gated:
        stopped_signal = observer.wait(deadline)
        if stopped_signal != signal.SIGTRAP | 0x80:
            assert stopped_signal not in (signal.SIGSTOP, signal.SIGTRAP), 'unexpected_native_stop'
            observer.resume(stopped_signal)
            continue
        phase, data = observer.info()
        if phase == 1:
            number, *args = data
            pending = (number, args)
            if number == 3:
                offsets.pop(args[0], None)
        elif phase == 2 and pending:
            number, args = pending
            pending = None
            if number in (0, 45) and data > 0:
                fd, pointer = args[:2]
                try:
                    link = os.readlink(f'/proc/{pid}/fd/{fd}')
                except FileNotFoundError:
                    link = ''
                if link.startswith('socket:[') and offsets.get(fd, 0) is not None:
                    inode = link[8:-1]
                    tcp = [line.split() for name in ('tcp', 'tcp6') for line in Path('/proc', str(pid), 'net', name).read_text().splitlines()[1:]]
                    if any(row[9] == inode and row[1].endswith(':46AA') for row in tcp):
                        offset = observer.match_line(pointer, data, expected, offsets.get(fd, 0))
                        offsets[fd] = offset
                        if offset == len(expected):
                            gated = True
                            emit({'event': 'gated', 'unit': unit, 'boundary': 'after-receive-before-application', 'syscall': number, 'revision_id': revision})
            if number in (1, 20, 44, 46) and data > 0:
                offsets.pop(args[0], None)
        if not gated:
            observer.resume()
    control_command(b'lose-observer' if mode == 'loss' else b'release', 8 if mode == 'loss' else 25)
    if mode == 'loss':
        emit({'event': 'observer-loss', 'unit': unit, 'signal': 'SIGKILL'})
        os.kill(os.getpid(), signal.SIGKILL)
finally:
    observer.detach()
    if armed:
        emit(json.loads(command(['/usr/bin/python3', '-I', str(folder / 'resume.py'), str(folder)], timeout=110)))
        emit({'event': 'disarmed', 'unit': unit, 'timer_stop': stop_timer(unit)})
        assert status(unit + '.timer') in ('inactive', 'unknown'), 'resume_timer_still_active'
