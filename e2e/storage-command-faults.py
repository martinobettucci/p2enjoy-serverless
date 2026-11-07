# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
"""Real, bounded DEV process/filesystem faults for API-owned storage commands."""
from contextlib import closing, suppress
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shlex
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from uuid import UUID, uuid4
from control_database import control_owner, ControlWriter

assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
mode, function, namespace = sys.argv[1:4]
assert str(UUID(function)) == function and str(UUID(namespace)) == namespace
settings = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields = shlex.split(line, comments=True)
    if len(fields) == 1 and '=' in fields[0]:
        key, value = fields[0].split('=', 1)
        if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_DOCKER_SOCKET_HOST', 'SERVERLESS_STORAGE_SOCKET_DIR_HOST'):
            settings[key] = value
state = Path(settings['SERVERLESS_STATE_HOST_PATH'])
storage = Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
control, registry = state / 'control.sqlite3', storage / 'registry.sqlite3'
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]

def emit(value):
    print(json.dumps(value), flush=True)

def command(args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, timeout=30, **kwargs)
    assert result.returncode == 0, 'operator_command_failed'
    return result.stdout.strip()

def rows(path, sql, args=()):
    assert path in (control, registry)
    assert path.stat().st_uid == control.stat().st_uid and path.stat().st_gid == control.stat().st_gid
    with control_owner(control):
        with closing(sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True, timeout=2)) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(sql, args)]

owned = rows(control, '''SELECT f.id,n.name FROM functions f JOIN services s ON s.id=f.service_id
    JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?''', (function, namespace))
assert len(owned) == 1 and re.fullmatch(r'storage-recovery-[0-9a-f]{8}', owned[0]['name']), 'owned_campaign_required'
assert not rows(control, '''SELECT 1 FROM functions f JOIN services s ON s.id=f.service_id
    WHERE f.deleted_at IS NULL AND s.namespace_id!=?''', (namespace,)), 'foreign_active_function'

def inspect():
    fn = rows(control, 'SELECT id,updated_at,deleted_at,purged_at FROM functions WHERE id=?', (function,))[0]
    configuration = rows(control, 'SELECT config_json,environment_json,secrets_cipher FROM functions WHERE id=?', (function,))[0]
    fn['configuration_sha256'] = hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()
    guards = rows(control, 'SELECT id,kind,decision,storage_version,error_code FROM function_operations WHERE function_id=?', (function,))
    receipts = rows(control, 'SELECT id,kind,state,phase,expected_function_version,result_version,error_code FROM storage_commands WHERE function_id=? ORDER BY created_at,id', (function,))
    agent = rows(registry, 'SELECT state,version,pending_json FROM functions WHERE id=?', (function,))
    if agent:
        agent[0]['pending'] = json.loads(agent[0].pop('pending_json') or 'null')
    files = {}
    for kind in ('data', 'cache'):
        path = storage / 'backings' / function / kind / 'record'
        if path.is_file():
            files[kind] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    revisions = rows(control, 'SELECT id,stored_bytes,deleted_at FROM revisions WHERE function_id=?', (function,))
    artifacts = {}
    for revision in revisions:
        folder = state / 'artifacts' / revision['id']
        archive = folder / 'archive.zip'
        artifacts[revision['id']] = {'code_present': (folder / 'code').is_dir(),
            'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest() if archive.is_file() else None}
    return {'function': fn, 'guards': guards, 'commands': receipts, 'agent': agent,
            'files': files, 'revisions': revisions, 'artifacts': artifacts,
            'agent_receipts': rows(registry, 'SELECT operation_id,kind,expected_version,version FROM discard_receipts WHERE function_id=?', (function,))}

# This program runs independently under systemd, even if SSH/the test dies.
RESTORE = '''import fcntl,json,os,select,signal,socket,stat,subprocess,sys,time
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
item=json.loads(sys.argv[1]);independent=len(sys.argv)>2 and sys.argv[2]=='guard'
result={'event':'restored','kind':item['kind'],'function_id':item['function_id'],'independent':independent}
if independent and 'helper_pid' in item:
 try:fd=os.pidfd_open(item['helper_pid'])
 except ProcessLookupError:pass
 else:
  try:
   birth=Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]
   if birth==item['helper_birth']:
    signal.pidfd_send_signal(fd,signal.SIGKILL)
    ready,_,_=select.select([fd],[],[],10);assert ready,'helper_stop_unconfirmed'
  except (ProcessLookupError,FileNotFoundError):pass
  finally:os.close(fd)
if item['kind']=='agent':
 try:
  fd=os.pidfd_open(item['pid'])
  try:
   row=Path('/proc',str(item['pid']),'stat').read_text().rsplit(')',1)[1].split()
   assert row[19]==item['birth'],'pid_reused'
   result['was_stopped']=row[0] in ('T','t');signal.pidfd_send_signal(fd,signal.SIGCONT)
  finally:os.close(fd)
 except (FileNotFoundError,ProcessLookupError):result['already_exited']=True
elif item['kind']=='directory':
 try:fd=os.open(item['path'],os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 except FileNotFoundError:result['already_absent']=True
 else:
  try:
   value=os.fstat(fd);assert [value.st_dev,value.st_ino]==item['identity'],'directory_replaced'
   os.fchown(fd,item['uid'],item['gid']);os.fchmod(fd,item['mode']);os.fsync(fd)
  finally:os.close(fd)
elif item['kind']=='control':
 path=Path(item['lock_path']);fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW)
 try:
  info=os.fstat(fd)
  assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity'],'restart_lock_replaced'
  deadline=time.monotonic()+40
  while True:
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
   except BlockingIOError:
    assert time.monotonic()<deadline,'stop_mutator_not_joined';time.sleep(.1)
  before=json.loads(subprocess.run(item['docker']+['inspect','--format','{{json .State}}','serverless-api'],check=True,capture_output=True,text=True,timeout=30).stdout)
  result.update(was_running=before['Running'],exit_code_before=before['ExitCode'],stop_mutator_joined=True)
  subprocess.run(item['docker']+['start','serverless-api'],check=True,capture_output=True,timeout=30)
  result['running']=subprocess.run(item['docker']+['inspect','--format','{{.State.Running}}','serverless-api'],check=True,capture_output=True,text=True,timeout=30).stdout.strip()=='true'
  assert result['running'],'control_restart_failed'
  current=path.lstat();assert [current.st_dev,current.st_ino]==item['lock_identity'],'restart_lock_replaced'
  path.unlink();result['lock_removed']=True
 finally:os.close(fd)
elif item['kind']=='agent-socket':
 path=Path(item['path']);before=path.lstat()
 assert stat.S_ISSOCK(before.st_mode) and [before.st_dev,before.st_ino]==item['identity'],'socket_replaced'
 assert (before.st_uid,before.st_gid)==(item['uid'],item['gid']),'socket_owner_changed'
 os.chmod(path,item['mode'],follow_symlinks=False)
 result.update(previous_mode=stat.S_IMODE(before.st_mode),mode=stat.S_IMODE(path.lstat().st_mode),identity=item['identity'])
 assert result['mode']==item['mode'],'socket_restore_failed'
elif item['kind']=='writer':
 assert independent,'writer_release_requires_owner'
 result['operation_id']=item['operation_id']
else:raise RuntimeError('invalid_restore_kind')
print(json.dumps(result),flush=True)
'''

def arm(item, delay=100, unit=None):
    unit = unit or 'serverless-restore-storage-command-' + uuid4().hex
    command(['systemd-run', '--quiet', '--collect', '--unit=' + unit, '--on-active=' + str(delay) + 's',
             '--timer-property=AccuracySec=100ms', '--timer-property=RandomizedDelaySec=0',
             '/usr/bin/python3', '-I', '-c', RESTORE, json.dumps(item), 'guard'])
    assert command(['systemctl', 'is-active', unit + '.timer']) == 'active', 'independent_guard_not_armed'
    emit({'event': 'guard-armed', 'unit': unit, 'kind': item['kind']})
    return unit

def restore(item):
    value = json.loads(command(['/usr/bin/python3', '-I', '-c', RESTORE, json.dumps(item)]))
    emit(value)
    return value

if mode == 'inspect':
    emit(inspect())
elif mode == 'guard-evidence':
    unit = sys.argv[4]
    assert re.fullmatch(r'serverless-restore-storage-command-[0-9a-f]{32}', unit)
    events = []
    for line in command(['journalctl', '--no-pager', '-o', 'cat', '-u', unit + '.service']).splitlines():
        if line.startswith('{'):
            event = json.loads(line)
            if event.get('event') == 'restored' and event.get('function_id') == function:
                events.append(event)
    emit({'events': events})
elif mode in ('kill-control', 'kill-control-watchdog'):
    operation, decision = sys.argv[4:6]
    assert str(UUID(operation)) == operation and decision in ('undecided', 'commit')
    observed = rows(control, 'SELECT id,decision,storage_version FROM function_operations WHERE id=? AND function_id=?', (operation, function))
    assert observed and observed[0]['decision'] == decision, 'decision_not_observed'
    unit = 'serverless-restore-storage-command-' + uuid4().hex
    lock_path = Path('/run') / (unit + '.lock')
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    armed = False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        info = os.fstat(fd)
        item = {'kind': 'control', 'function_id': function, 'docker': docker, 'helper_pid': os.getpid(),
                'helper_birth': Path('/proc', str(os.getpid()), 'stat').read_text().rsplit(')', 1)[1].split()[19],
                'lock_path': str(lock_path), 'lock_identity': [info.st_dev, info.st_ino]}
        os.write(fd, json.dumps(item).encode());os.fsync(fd)
        arm(item, 5 if mode == 'kill-control-watchdog' else 45, unit);armed = True
        # GNU timeout owns the inherited flock until its bounded CLI has ended,
        # even when the Python parent is killed by the independent restorer.
        result = subprocess.run(['timeout', '--signal=KILL', '30s', *docker, 'kill', '--signal', 'KILL', 'serverless-api'],
                                pass_fds=(fd,), capture_output=True, text=True, timeout=40)
        assert result.returncode == 0, 'control_stop_failed'
    finally:
        os.close(fd)
        if not armed:
            lock_path.unlink()
    stopped = json.loads(command(docker + ['inspect', '--format', '{{json .State}}', 'serverless-api']))
    assert stopped['Status'] == 'exited' and stopped['ExitCode'] == 137, 'control_crash_unconfirmed'
    emit({'event': 'control-killed', 'operation': observed[0], 'exit_code': 137, 'guard_unit': unit})
elif mode == 'start-control':
    unit = sys.argv[4]
    assert re.fullmatch(r'serverless-restore-storage-command-[0-9a-f]{32}', unit)
    lock_path = Path('/run') / (unit + '.lock')
    if lock_path.exists():
        info = lock_path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o600
        item = json.loads(lock_path.read_text())
        assert item['kind'] == 'control' and item['function_id'] == function and item['lock_path'] == str(lock_path)
        restore(item)
    else:
        command(docker + ['start', 'serverless-api'])
    assert command(docker + ['inspect', '--format', '{{.State.Running}}', 'serverless-api']) == 'true'
    deadline = time.monotonic() + 30
    while True:
        try:
            with urllib.request.urlopen('http://127.0.0.1:18090/healthz', timeout=2) as response:
                assert response.status == 200
            break
        except urllib.error.HTTPError as error:
            if error.code == 503:
                break  # API running, with the deliberately unresolved storage fault.
            raise
        except (OSError, TimeoutError):
            assert time.monotonic() < deadline, 'control_start_not_observed'
            time.sleep(.2)
    command(['systemctl', 'stop', unit + '.timer'])
    emit({'event': 'control-started'})
elif mode == 'control-errors':
    operation = str(UUID(sys.argv[4]))
    assert rows(control, 'SELECT 1 FROM storage_commands WHERE id=? AND function_id=?', (operation, function))
    result = subprocess.run(docker + ['logs', '--since', '10m', 'serverless-api'], capture_output=True, text=True, timeout=20, check=True)
    events = []
    for line in (result.stdout + '\n' + result.stderr).splitlines():
        start = line.find('{')
        if start < 0:
            continue
        try:
            event = json.loads(line[start:])
        except ValueError:
            continue
        if event.get('event') == 'function.storage_pending' and event.get('operation_id') == operation:
            events.append({key: event[key] for key in ('event', 'operation_id', 'error_code')})
    emit({'events': events})
elif mode in ('hold-control-writer', 'writer-status'):
    operation = str(UUID(sys.argv[4]))
    if mode == 'hold-control-writer':
        assert rows(control, "SELECT 1 FROM function_operations WHERE id=? AND function_id=? AND decision='commit'", (operation, function)), 'committed_operation_required'
    else:
        assert rows(control, 'SELECT 1 FROM storage_commands WHERE id=? AND function_id=?', (operation, function)), 'owned_command_required'
    writer = None
    signals = {signal.SIGHUP, signal.SIGTERM, signal.SIGINT}
    item = {'kind': 'writer', 'function_id': function, 'operation_id': operation, 'helper_pid': os.getpid(),
            'helper_birth': Path('/proc', str(os.getpid()), 'stat').read_text().rsplit(')', 1)[1].split()[19]}
    guard = arm(item, 45) if mode == 'hold-control-writer' else None
    def interrupted(signum, frame):
        raise InterruptedError('operator_interrupted')
    for signum in signals:
        signal.signal(signum, interrupted)
    try:
        previous = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
        try:
            writer = ControlWriter(control, timeout=10)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        observed = writer.rows('SELECT id,state,result_version FROM storage_commands WHERE id=? AND function_id=?', (operation, function))
        assert len(observed) == 1, 'owned_command_required'
        if mode == 'hold-control-writer':
            assert observed[0]['state'] == 'pending', 'pending_command_required'
        emit({'event': 'fault-active' if guard else 'writer-available', 'mode': mode, 'identity': writer.identity, 'command': observed[0]})
        if guard:
            readable, _, _ = select.select([sys.stdin], [], [], 40)
            assert readable, 'fault_release_timeout'
            action = sys.stdin.readline().strip()
            if action == 'kill-helper':
                os.kill(os.getpid(), signal.SIGKILL)
            assert action == 'resume', 'invalid_fault_action'
    finally:
        previous = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
        try:
            if writer is not None:
                writer.close()
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        if guard:
            command(['systemctl', 'stop', guard + '.timer'])
        emit({'event': 'writer-released', 'operator_uid': os.geteuid(), 'operation_id': operation})
elif mode in ('pause-agent', 'watchdog', 'deny-cache', 'deny-artifact', 'deny-agent-socket'):
    assert not rows(control, 'SELECT 1 FROM execution_instances WHERE function_id=?', (function,)), 'idle_function_required'
    assert not rows(registry, 'SELECT 1 FROM leases WHERE function_id=?', (function,)), 'lease_free_function_required'
    item = {'function_id': function}
    pidfd = None
    if mode in ('pause-agent', 'watchdog'):
        pid = int(command(['systemctl', 'show', '-p', 'MainPID', '--value', 'p2enjoy-storage-dev.service']))
        pidfd = os.pidfd_open(pid)
        item.update(kind='agent', pid=pid, birth=Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19])
    elif mode == 'deny-agent-socket':
        operation = str(UUID(sys.argv[4]))
        assert rows(control, "SELECT 1 FROM function_operations WHERE id=? AND function_id=? AND decision='commit'", (operation, function)), 'committed_operation_required'
        path = Path(settings['SERVERLESS_STORAGE_SOCKET_DIR_HOST']) / 'agent.sock'
        info = path.lstat()
        mounts = json.loads(command(docker + ['inspect', '--format', '{{json .Mounts}}', 'serverless-api']))
        assert any(row['Destination'] == '/storage-agent' and row['Source'] == str(path.parent) for row in mounts), 'agent_socket_mount_mismatch'
        assert stat.S_ISSOCK(info.st_mode) and info.st_uid == control.stat().st_uid, 'owned_socket_required'
        item.update(kind='agent-socket', path=str(path), identity=[info.st_dev, info.st_ino], uid=info.st_uid, gid=info.st_gid,
                    mode=stat.S_IMODE(info.st_mode), helper_pid=os.getpid(),
                    helper_birth=Path('/proc', str(os.getpid()), 'stat').read_text().rsplit(')', 1)[1].split()[19])
    else:
        path = storage / 'backings' / function / 'cache'
        if mode == 'deny-artifact':
            revision = str(UUID(sys.argv[4]))
            assert rows(control, 'SELECT 1 FROM revisions WHERE id=? AND function_id=?', (revision, function)), 'owned_revision_required'
            path = state / 'artifacts' / revision
        info = path.lstat()
        assert stat.S_ISDIR(info.st_mode) and info.st_uid == control.stat().st_uid, 'owned_directory_required'
        item.update(kind='directory', path=str(path), identity=[info.st_dev, info.st_ino], uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode))
    guard = arm(item, 5 if mode == 'watchdog' else 100)
    def interrupted(signum, frame):
        raise InterruptedError('operator_interrupted')
    for signum in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    try:
        if pidfd is not None:
            signal.pidfd_send_signal(pidfd, signal.SIGSTOP)
            deadline = time.monotonic() + 2
            while Path('/proc', str(item['pid']), 'stat').read_text().rsplit(')', 1)[1].split()[0] not in ('T', 't'):
                assert time.monotonic() < deadline, 'agent_stop_not_observed'
                time.sleep(.01)
        elif item['kind'] == 'agent-socket':
            os.chmod(item['path'], 0, follow_symlinks=False)
            probe = "import socket;s=socket.socket(socket.AF_UNIX);s.connect('/storage-agent/agent.sock')"
            refused = subprocess.run(docker + ['exec', 'serverless-api', 'python', '-B', '-c', probe], capture_output=True, text=True, timeout=10)
            assert refused.returncode != 0 and 'PermissionError' in refused.stderr, 'agent_transport_not_denied'
        else:
            fd = os.open(item['path'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                value = os.fstat(fd)
                assert [value.st_dev, value.st_ino] == item['identity']
                os.fchown(fd, 0, 0)
                os.fchmod(fd, 0)
            finally:
                os.close(fd)
        emit({'event': 'fault-active', 'mode': mode})
        readable, _, _ = select.select([sys.stdin], [], [], 85)
        assert readable, 'fault_release_timeout'
        action = sys.stdin.readline().strip()
        if action == 'kill-helper':
            os.kill(os.getpid(), signal.SIGKILL)
        assert action == 'resume', 'invalid_fault_action'
    finally:
        try:
            restore(item)
            command(['systemctl', 'stop', guard + '.timer'])
        finally:
            if pidfd is not None:
                os.close(pidfd)
else:
    raise RuntimeError('unknown_fault_mode')
