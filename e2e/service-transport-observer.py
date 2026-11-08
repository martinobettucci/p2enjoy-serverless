# @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
# @verifies docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli
"""Bounded native observation of the unchanged DEV control, with independent recovery.

All helpers implement the same transport-proof contract. No buffers, registers,
responses or application state are modified. Only the public request line is read.
Linux ABI reference: https://man7.org/linux/man-pages/man2/ptrace.2.html
"""
from contextlib import suppress
import ctypes
import fcntl
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


def emit(value):
    print(json.dumps(value), flush=True)


def command(args, timeout=35, **kwargs):
    value = subprocess.run(args, capture_output=True, text=True, timeout=timeout, **kwargs)
    assert value.returncode == 0, 'operator_command_failed'
    return value.stdout.strip()


def birth(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


def settings():
    result = {}
    for line in Path('/etc/spark/env').read_text().splitlines():
        fields = shlex.split(line, comments=True)
        if len(fields) == 1 and '=' in fields[0]:
            key, value = fields[0].split('=', 1)
            if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_DOCKER_SOCKET_HOST'):
                result[key] = value
    return result


# Frozen independent program: it survives the observer and the SSH connection.
RESTORE = '''import fcntl,json,os,select,signal,socket,stat,subprocess,sys,time,urllib.request
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(180)
folder=Path(sys.argv[1]);info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith(('serverless-restore-service-transport-','serverless-restore-invocation-url-'))
assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
item=json.loads((folder/'identity.json').read_text());independent=len(sys.argv)>2
result={'event':'restored','independent':independent,'container_id':item['container_id'],'image':item['image']}
if independent:
 try:fd=os.pidfd_open(item['helper_pid'])
 except ProcessLookupError:pass
 else:
  try:
   row=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()
   if row[19]==item['helper_birth']:
    signal.pidfd_send_signal(fd,signal.SIGKILL)
    ready,_,_=select.select([fd],[],[],10);assert ready,'observer_stop_unconfirmed'
    result['observer_killed']=True
  except (ProcessLookupError,FileNotFoundError):pass
  finally:os.close(fd)
 result['observer_gone']=True
lock=os.open(folder/'mutation.lock',os.O_RDWR|os.O_NOFOLLOW)
try:
 info=os.fstat(lock);assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']
 deadline=time.monotonic()+40
 while True:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   assert time.monotonic()<deadline,'stop_mutator_not_joined';time.sleep(.1)
 def inspect(name):
  return json.loads(subprocess.run(item['docker']+['inspect',name],check=True,capture_output=True,text=True,timeout=30).stdout)[0]
 current=inspect('serverless-api');assert current['Id']==item['container_id'] and current['Image']==item['image'],'control_replaced'
 reference=inspect('serverless-runtime-reference');assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'],'reference_replaced'
 try:fd=os.pidfd_open(item['pid'])
 except ProcessLookupError:pass
 else:
  try:
   row=Path('/proc',str(item['pid']),'stat').read_text().rsplit(')',1)[1].split()
   assert row[19]==item['birth'],'control_pid_reused'
   assert Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup'],'control_owner_changed'
   signal.pidfd_send_signal(fd,signal.SIGCONT)
  except (FileNotFoundError,ProcessLookupError):pass
  finally:os.close(fd)
 result['was_running']=current['State']['Running'];result['exit_code_before']=current['State']['ExitCode']
 if not current['State']['Running']:
  subprocess.run(item['docker']+['start',item['container_id']],check=True,capture_output=True,timeout=30)
 deadline=time.monotonic()+35
 while True:
  try:
   with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=2) as response:assert response.status==200
   current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')
   assert current['State']['Health']['Status']==reference['State']['Health']['Status']=='healthy'
   break
  except (OSError,AssertionError):
   assert time.monotonic()<deadline,'control_health_not_restored';time.sleep(.2)
 current=inspect('serverless-api');reference=inspect('serverless-runtime-reference')
 assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running']
 assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']
 result.update(healthy=True,reference_unchanged=True,stop_mutator_joined=True)
 name='restored-independent.json' if independent else 'restored.json'
 pending=folder/(name+'.pending');pending.write_text(json.dumps(result)+'\\n');pending.replace(folder/name)
 print(json.dumps(result),flush=True)
finally:os.close(lock)
'''


class NativeObserver:
    """Read syscall metadata and a bounded public request line, never credentials."""
    def __init__(self, pid):
        self.pid, self.attached, self.stopped = pid, False, False
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.libc.ptrace.restype = ctypes.c_long
        self.libc.ptrace.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        self.memory = None

    def ptrace(self, request, address=0, data=0):
        ctypes.set_errno(0)
        value = self.libc.ptrace(request, self.pid, address, data)
        if value == -1 and ctypes.get_errno():
            raise OSError(ctypes.get_errno(), 'native_observation_failed')
        return value

    def start(self):
        # SEIZE + INTERRUPT avoids sending SIGSTOP to the application group.
        self.ptrace(0x4206, 0, 1)  # PTRACE_SEIZE, TRACESYSGOOD; no EXITKILL.
        self.attached = True
        self.ptrace(0x4207)  # PTRACE_INTERRUPT
        self.wait(time.monotonic() + 5)
        self.memory = os.open(f'/proc/{self.pid}/mem', os.O_RDONLY)

    def wait(self, deadline):
        while True:
            value, status = os.waitpid(self.pid, os.WNOHANG)
            if value:
                assert os.WIFSTOPPED(status), 'control_exited_during_observation'
                self.stopped = True
                return os.WSTOPSIG(status)
            assert time.monotonic() < deadline, 'native_stop_not_observed'
            time.sleep(.001)

    def resume(self, delivered=0):
        self.ptrace(24, 0, delivered)  # PTRACE_SYSCALL
        self.stopped = False

    def info(self):
        buffer = ctypes.create_string_buffer(88)
        self.ptrace(0x420e, 88, ctypes.addressof(buffer))  # GET_SYSCALL_INFO
        raw = buffer.raw
        assert int.from_bytes(raw[4:8], 'little') == 0xc000003e, 'x86_64_syscall_required'
        op = raw[0]
        if op == 1:
            return op, [int.from_bytes(raw[i:i+8], 'little') for i in range(24, 80, 8)]
        if op == 2:
            return op, int.from_bytes(raw[24:32], 'little', signed=True)
        return op, None

    def match_line(self, pointer, count, expected, offset):
        # One byte at a time stops at CRLF, even when headers share this recv.
        while count and offset < len(expected):
            value = os.pread(self.memory, 1, pointer)
            if value != expected[offset:offset+1]:
                return None
            pointer, count, offset = pointer + 1, count - 1, offset + 1
        return offset

    def detach(self):
        if self.memory is not None:
            os.close(self.memory)
            self.memory = None
        if self.attached:
            try:
                if not self.stopped:
                    self.ptrace(0x4207)
                    self.wait(time.monotonic() + 5)
                self.ptrace(17)  # PTRACE_DETACH
            except (OSError, ProcessLookupError, ChildProcessError):
                pass  # Independent restorer still verifies the original owner.
            self.attached = False


assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
assert platform.machine() == 'x86_64', 'x86_64_required'
mode, service, namespace = sys.argv[1:4]
assert mode in ('before', 'after', 'watchdog', 'inspect', 'restore', 'evidence',
                'catalogue-before', 'catalogue-after', 'catalogue-watchdog')
assert str(UUID(service)) == service and str(UUID(namespace)) == namespace
values = settings()
control = Path(values['SERVERLESS_STATE_HOST_PATH']) / 'control.sqlite3'
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + values['SERVERLESS_DOCKER_SOCKET_HOST']]


def stop_timer(unit):
    # --collect may already have removed a guard that actually fired.
    subprocess.run(['systemctl', 'stop', unit + '.timer'], capture_output=True, timeout=10)
    result = subprocess.run(['systemctl', 'is-active', unit + '.timer'], capture_output=True, text=True, timeout=10)
    assert result.returncode in (3, 4) and result.stdout.strip() in ('inactive', 'unknown'), 'guard_timer_still_active'


def durable():
    with read_control(control) as db:
        row = db.execute('SELECT environment_json,updated_at FROM services WHERE id=? AND namespace_id=?', (service, namespace)).fetchone()
        assert row is not None, 'campaign_service_missing'
        result = {'environment_sha256': hashlib.sha256(row['environment_json'].encode()).hexdigest(), 'version': row['updated_at'],
                'mutations': db.execute("SELECT count(*) FROM audit_events WHERE action='service.configure' AND object_id=?", (service,)).fetchone()[0],
                'functions': db.execute('SELECT count(*) FROM functions WHERE service_id=?', (service,)).fetchone()[0],
                'candidates': db.execute('SELECT count(*) FROM deployments WHERE service_id=?', (service,)).fetchone()[0]}
        if catalogue_scope:
            function = db.execute('SELECT id,active_revision_id,deleted_at FROM functions WHERE id=? AND service_id=?', (function_id, service)).fetchone()
            assert function and function['deleted_at'] is None, 'owned_function_required'
            revisions = [dict(v) for v in db.execute('SELECT id,archive_sha256,deleted_at FROM revisions WHERE function_id=?', (function_id,))]
            candidates = [dict(v) for v in db.execute('SELECT id,state,revision_id,reserved_bytes FROM deployments WHERE function_id=?', (function_id,))]
            result['publication'] = {'function_id': function_id, 'active_revision_id': function['active_revision_id'],
                'revisions': revisions, 'candidates': candidates,
                'deploy_audits': db.execute("SELECT count(*) FROM audit_events WHERE action='function.deploy' AND object_id=?", (function_id,)).fetchone()[0],
                'storage_operations': db.execute('SELECT count(*) FROM function_operations WHERE function_id=?', (function_id,)).fetchone()[0]}
            if function['active_revision_id']:
                revision = str(UUID(function['active_revision_id']))
                folder = control.parent / 'artifacts' / revision
                assert folder.is_dir() and not folder.is_symlink(), 'real_artifact_directory_required'
                fd = os.open(folder / 'archive.zip', os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd, 'rb') as stream:
                    info = os.fstat(stream.fileno())
                    assert stat.S_ISREG(info.st_mode) and 0 < info.st_size <= 64*1024**2, 'real_archive_required'
                    result['publication']['archive_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
                    result['publication']['archive_bytes'] = info.st_size
                assert (folder / 'code').is_dir() and not (folder / 'code').is_symlink(), 'real_code_directory_required'
        return result


def published(value):
    """Require the exact one committed publication before disrupting its optional GET."""
    item = value['publication']
    assert value['functions'] == value['candidates'] == 1 and value['mutations'] == 0
    assert len(item['revisions']) == len(item['candidates']) == item['deploy_audits'] == 1
    revision, candidate = item['revisions'][0], item['candidates'][0]
    assert item['active_revision_id'] == revision['id'] == candidate['revision_id'] == candidate['id']
    assert revision['deleted_at'] is None and candidate['state'] == 'published' and candidate['reserved_bytes'] == 0
    assert item['archive_sha256'] == revision['archive_sha256'] and item['storage_operations'] == 0


with read_control(control) as db:
    owner = db.execute('SELECT name FROM namespaces WHERE id=?', (namespace,)).fetchone()
    assert owner and re.fullmatch(r'(?:service-transport|invocation-url-transport)-[0-9a-f]{8}', owner['name']), 'owned_campaign_required'
    catalogue_scope = owner['name'].startswith('invocation-url-transport-')
    assert db.execute('SELECT 1 FROM services WHERE id=? AND namespace_id=?', (service, namespace)).fetchone(), 'owned_service_required'

if mode not in ('restore', 'evidence'):
    assert catalogue_scope == mode.startswith('catalogue-') or mode == 'inspect', 'campaign_mode_mismatch'
    function_id = sys.argv[4] if catalogue_scope else None
    if function_id is not None:
        assert str(UUID(function_id)) == function_id, 'function_uuid_required'

if mode in ('restore', 'evidence'):
    unit = sys.argv[4]
    assert re.fullmatch(r'serverless-restore-(?:service-transport|invocation-url)-[0-9a-f]{32}', unit)
    folder = Path('/run') / unit
    identity = json.loads((folder / 'identity.json').read_text())
    assert identity['service_id'] == service and identity['namespace_id'] == namespace
    if mode == 'restore':
        emit(json.loads(command(['/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder)], timeout=190)))
        stop_timer(unit)
    else:
        evidence = folder / 'restored-independent.json'
        if not evidence.exists():
            evidence = folder / 'restored.json'
        emit(json.loads(evidence.read_text()) if evidence.exists() else {'event': 'pending'})
    sys.exit(0)

if mode == 'inspect':
    emit(durable())
    sys.exit(0)

with read_control(control) as db:
    if catalogue_scope:
        assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0] == 1, 'only_owned_function_required'
        assert db.execute('SELECT 1 FROM functions WHERE id=? AND service_id=? AND deleted_at IS NULL AND active_revision_id IS NULL',
                          (function_id, service)).fetchone(), 'owned_draft_required'
    for sql in (
        *(() if catalogue_scope else ('SELECT count(*) FROM functions WHERE deleted_at IS NULL',)),
        "SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
        "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
        'SELECT count(*) FROM function_operations', 'SELECT count(*) FROM execution_instances',
    ):
        assert db.execute(sql).fetchone()[0] == 0, 'quiet_installation_required'

current = json.loads(command(docker + ['inspect', 'serverless-api']))[0]
reference = json.loads(command(docker + ['inspect', 'serverless-runtime-reference']))[0]
assert current['State']['Running'] and reference['State']['Running'], 'running_installation_required'
assert current['State']['Health']['Status'] == reference['State']['Health']['Status'] == 'healthy', 'healthy_installation_required'
init = current['State']['Pid']
descendants = [init]
for parent in descendants:
    descendants.extend(int(value) for value in Path('/proc', str(parent), 'task', str(parent), 'children').read_text().split())
processes = [pid for pid in descendants
             if Path(os.readlink(f'/proc/{pid}/exe')).name.startswith('python')
             and Path('/proc', str(pid), 'cmdline').read_bytes().startswith(b'python\x00-B\x00-m\x00uvicorn\x00app.main:app\x00')]
assert len(processes) == 1, 'unique_control_process_required'
pid = processes[0]
assert Path('/proc', str(pid), 'cgroup').read_text() == Path('/proc', str(init), 'cgroup').read_text(), 'container_owner_required'
before = durable()
assert before['functions'] == (1 if catalogue_scope else 0) and before['candidates'] == 0, 'empty_campaign_required'
unit = ('serverless-restore-invocation-url-' if catalogue_scope else 'serverless-restore-service-transport-') + uuid4().hex
folder = Path('/run') / unit
folder.mkdir(mode=0o700)
lock = os.open(folder / 'mutation.lock', os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
info = os.fstat(lock)
item = {'service_id': service, 'namespace_id': namespace, 'container_id': current['Id'], 'image': current['Image'],
        'reference': [reference['Id'], reference['Image'], reference['State']['StartedAt']], 'docker': docker, 'pid': pid, 'birth': birth(pid),
        'cgroup': Path('/proc', str(pid), 'cgroup').read_text(), 'helper_pid': os.getpid(), 'helper_birth': birth(os.getpid()),
        'lock_identity': [info.st_dev, info.st_ino]}
(folder / 'identity.json').write_text(json.dumps(item))
(folder / 'restore.py').write_text(RESTORE)
observer, armed = NativeObserver(pid), False
try:
    command(['systemd-run', '--quiet', '--collect', '--unit=' + unit, '--on-active=' + ('12s' if mode.endswith('watchdog') else '70s'),
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '--property=RuntimeMaxSec=190s', '--property=TimeoutStopSec=5s',
             '/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder), 'guard'])
    armed = True
    assert command(['systemctl', 'is-active', unit + '.timer']) == 'active', 'guard_not_armed'
    emit({'event': 'guard-armed', 'unit': unit})
    observer.start()
    emit({'event': 'armed', 'unit': unit, 'container_id': current['Id'], 'image': current['Image'], 'before': before})
    if mode.endswith('watchdog'):
        emit({'event': 'suspended', 'unit': unit})
        # Intentional observer death proves independent detach/resume and health.
        assert select.select([sys.stdin], [], [], 8)[0], 'watchdog_command_missing'
        assert sys.stdin.readline().strip() == 'lose-observer'
        emit({'event': 'observer-loss', 'signal': 'SIGKILL', 'unit': unit})
        os.kill(os.getpid(), signal.SIGKILL)
    expected = (f'GET /api/functions/{function_id}/invocation-urls?limit=5&offset=0 HTTP/1.1\r\n' if catalogue_scope
                else f'PUT /api/services/{service}/configuration HTTP/1.1\r\n').encode('ascii')
    pending, offsets, target, gated = None, {}, None, False
    deadline = time.monotonic() + 45
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
            fd = args[0]
            if number == 3:  # close: clear identities before descriptor reuse.
                offsets.pop(fd, None)
                assert fd != target, 'target_connection_closed_before_gate'
            if target is not None and fd == target and number in (1, 20, 44, 46):
                assert mode.endswith('after'), 'unexpected_response_gate'
                after = durable()
                if catalogue_scope:
                    published(after)
                else:
                    assert after['mutations'] == before['mutations'] + 1 and after['environment_sha256'] != before['environment_sha256'], 'commit_not_observed'
                gated = True
                gate = {'boundary': 'before-send', 'syscall': number, 'durable': after}
        elif phase == 2 and pending:
            number, args = pending
            pending = None
            # CPython sockets use recvfrom; read is included for ABI completeness.
            if number in (0, 45) and data > 0:
                fd, pointer = args[:2]
                try:
                    link = os.readlink(f'/proc/{pid}/fd/{fd}')
                except FileNotFoundError:
                    link = ''
                if link.startswith('socket:[') and target is None and offsets.get(fd, 0) is not None:
                    # Require the actual upstream TCP socket listening on 18090.
                    inode = link[8:-1]
                    tcp = []
                    for name in ('tcp', 'tcp6'):
                        tcp.extend(line.split() for line in Path('/proc', str(pid), 'net', name).read_text().splitlines()[1:])
                    if any(row[9] == inode and row[1].endswith(':46AA') for row in tcp):
                        offset = observer.match_line(pointer, data, expected, offsets.get(fd, 0))
                        offsets[fd] = offset
                        if offset == len(expected):
                            target = fd
                            if mode.endswith('before'):
                                received = durable()
                                if catalogue_scope:
                                    published(received)
                                else:
                                    assert received == before, 'mutation_preceded_receive_gate'
                                gated = True
                                gate = {'boundary': 'after-receive', 'syscall': number, 'durable': received}
            if number in (1, 20, 44, 46) and data > 0:
                offsets.pop(args[0], None)
        if not gated:
            observer.resume()
    emit({'event': 'gated', **gate, 'service_id': service})
    assert select.select([sys.stdin], [], [], 8)[0], 'cut_command_missing'
    assert sys.stdin.readline().strip() == 'cut', 'cut_command_required'
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        stopped = subprocess.Popen(['timeout', '--signal=KILL', '25s', *docker, 'kill', '--signal', 'KILL', current['Id']],
                                   pass_fds=(lock,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Consume the traced death so tini/Docker can observe actual termination.
        end = time.monotonic() + 10
        while True:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited:
                assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL, 'control_death_unconfirmed'
                observer.attached = False
                break
            assert time.monotonic() < end, 'control_death_not_observed'
            time.sleep(.01)
        stopped.communicate(timeout=30)
        assert stopped.returncode == 0, 'control_kill_failed'
        killed = json.loads(command(docker + ['inspect', current['Id']]))[0]
        assert not killed['State']['Running'] and killed['State']['ExitCode'] == 137, 'control_crash_unconfirmed'
        emit({'event': 'cut', 'exit_code': 137, 'durable': durable()})
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
finally:
    observer.detach()
    os.close(lock)
    if armed:
        emit(json.loads(command(['/usr/bin/python3', '-I', str(folder / 'restore.py'), str(folder)], timeout=190)))
        stop_timer(unit)
