# @spec docs/BACKLOG.md#sls-112 | docs/MANAGED_INVOCATION_WATCH.md#preuve-suspension-worker
# @verifies docs/BACKLOG.md#sls-112 | docs/MANAGED_INVOCATION_WATCH.md#preuve-suspension-worker
"""Observe a real release acknowledgement, then stop/resume only its E2E worker."""
from contextlib import contextmanager
import base64
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4


GUARD_PROGRAM = r'''
import asyncio,hashlib,json,os,signal,sys,time
from pathlib import Path
sys.path.insert(0,'/app')
from app.storage_client import StorageClient
from app.validator import Docker
v=json.loads(sys.argv[1]);root=Path(v['directory']);fd=None;stop_requested=False;failure=None;stopped_at=None;continued_at=None;acknowledged=False
def write(name,value):
 p=root/(name+'.pending');p.write_text(json.dumps(value,sort_keys=True)+'\n');p.chmod(0o600);p.replace(root/name)
def identity():
 p=Path('/proc',str(v['pid']));birth=p.joinpath('stat').read_text().rsplit(')',1)[1].split()[19];args=p.joinpath('cmdline').read_bytes().split(b'\0')
 assert birth==v['birth']and v['script'].encode()in args and b'--worker'in args and v['installation'].encode()in args
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==v['boot_id']
 return p
def interrupted(signum,frame):raise RuntimeError('guardian_interrupted')
signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGALRM,interrupted);signal.alarm(25)
try:
 fd=os.pidfd_open(v['pid']);identity()
 Docker('/docker.sock').call('GET','/containers/'+v['container_name']+'/json',allowed=(404,))
 leases=asyncio.run(StorageClient('/storage-agent/agent.sock',v['storage_root']).leases(v['installation']))
 assert not any(r['consumer_id']==v['consumer']for r in leases)
 armed_deadline=time.monotonic_ns()+10_000_000_000
 write('ready.json',{'nonce':v['nonce'],'pid':v['pid'],'birth':v['birth'],'helper_pid':os.getpid(),'arm_deadline_ns':armed_deadline,'docker_absent':True,'lease_absent':True})
 while not(root/'armed.json').exists():
  assert time.monotonic_ns()<armed_deadline,'guardian_arm_timeout';time.sleep(.005)
 arm=json.loads((root/'armed.json').read_text());assert arm['nonce']==v['nonce']and arm['pid']==v['pid'];identity()
 stop_requested=True;signal.pidfd_send_signal(fd,signal.SIGSTOP)
 deadline=time.monotonic_ns()+2_000_000_000
 while True:
  p=identity();state=p.joinpath('stat').read_text().rsplit(')',1)[1].split()[0]
  if state in ('T','t'):stopped_at=time.monotonic_ns();break
  assert time.monotonic_ns()<deadline,'guardian_stop_unobserved';time.sleep(.005)
 while time.monotonic_ns()<stopped_at+750_000_000:time.sleep(.01)
except BaseException as error:
 failure={'type':type(error).__name__,'message_sha256':hashlib.sha256(str(error).encode()).hexdigest()}
finally:
 signal.alarm(0)
 if stop_requested and fd is not None:
  try:
   identity();signal.pidfd_send_signal(fd,signal.SIGCONT);continued_at=time.monotonic_ns()
   write('continued.json',{'nonce':v['nonce'],'pid':v['pid'],'birth':v['birth'],'stopped_at_ns':stopped_at,'continued_at_ns':continued_at})
   deadline=time.monotonic_ns()+5_000_000_000
   while time.monotonic_ns()<deadline:
    if(root/'acknowledged.json').exists():
     ack=json.loads((root/'acknowledged.json').read_text());assert ack['nonce']==v['nonce']and ack['pid']==v['pid']and ack['observed_at_ns']>=continued_at;acknowledged=True;break
    time.sleep(.005)
  except BaseException as error:
   failure=failure or {'type':type(error).__name__,'message_sha256':hashlib.sha256(str(error).encode()).hexdigest()}
 if fd is not None:os.close(fd)
 completed=bool(failure is None and stopped_at and continued_at and continued_at-stopped_at>=750_000_000 and acknowledged)
 write('finished.json',{'completed':completed,'nonce':v['nonce'],'pid':v['pid'],'birth':v['birth'],'stopped_at_ns':stopped_at,'continued_at_ns':continued_at,'acknowledged':acknowledged,'failure':failure})
sys.exit(0 if completed else 1)
'''


def diagnostic(error):
    return {'type': type(error).__name__,
            'message_sha256': hashlib.sha256(str(error).encode(errors='replace')).hexdigest()}


def write(path, value):
    pending = path.with_suffix('.pending')
    pending.write_text(json.dumps(value, sort_keys=True) + '\n')
    pending.chmod(0o600)
    pending.replace(path)


def wait_json(path, deadline, process):
    while not path.exists():
        assert process.poll() is None, 'pause_guardian_exited'
        assert time.monotonic() < deadline, 'pause_guardian_receipt_timeout'
        time.sleep(.005)
    return json.loads(path.read_text())


@contextmanager
def pause_after_release(item, storage, installation, work, record):
    from app.storage_client import StorageClient
    previous = sys.gettrace()
    assert previous is None, 'pause_preexisting_tracer'
    code = StorageClient.release_confirmed.__code__
    source = Path(code.co_filename)
    assert source == Path('/app/app/storage_client.py'), 'pause_source_path'
    lines = source.read_text().splitlines()
    wanted = "if any(row['consumer_id']==consumer for row in await self.leases(installation)):"
    matches = [index + 1 for index, line in enumerate(lines) if line.strip() == wanted]
    assert len(matches) == 1, 'pause_source_line'
    point = matches[0]
    record['pause'] = {'triggered': False, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                       'source_line': point, 'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       'guardian_program_sha256': hashlib.sha256(GUARD_PROGRAM.encode()).hexdigest()}

    def trace(frame, event, argument):
        if frame.f_code is not code:
            return None
        if event != 'line' or frame.f_lineno != point or frame.f_locals.get('consumer') != item.id:
            return trace
        if record['pause']['triggered']:
            return None
        record['pause']['triggered'] = True
        process = None
        communicated = False
        directory = work / ('paused-worker-guardian-' + uuid4().hex)
        nonce = uuid4().hex
        try:
            directory.mkdir(mode=0o700)
            assert frame.f_locals.get('self') is storage and frame.f_locals.get('function') == item.function_id
            assert frame.f_locals.get('installation') == installation
            released = frame.f_locals.get('released')
            assert released == {'released': True, 'already_released': False}, 'pause_release_unconfirmed'
            assert item.closing and item.removed, 'pause_consumer_not_removed'
            target = {'pid': os.getpid(), 'birth': Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
                      'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                      'script': str(Path(sys.argv[0]).resolve()), 'installation': installation,
                      'consumer': item.id, 'container_name': item.name, 'storage_root': str(storage.root),
                      'directory': str(directory), 'nonce': nonce}
            record['pause']['target'] = target
            record['pause']['release_reply'] = {'released': True, 'already_released': False}
            process = subprocess.Popen([sys.executable, '-B', '-c', GUARD_PROGRAM, json.dumps(target)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True, env={})
            record['pause']['helper_pid'] = process.pid
            ready = wait_json(directory / 'ready.json', time.monotonic() + 8, process)
            assert ready['nonce'] == nonce and ready['pid'] == target['pid'] and ready['birth'] == target['birth']
            assert ready['helper_pid'] == process.pid and ready['docker_absent'] and ready['lease_absent']
            assert time.monotonic_ns() < ready['arm_deadline_ns'] - 1_000_000_000, 'pause_arm_expired'
            write(directory / 'armed.json', {'nonce': nonce, 'pid': target['pid']})
            continued = wait_json(directory / 'continued.json', time.monotonic() + 20, process)
            assert continued['nonce'] == nonce and continued['pid'] == target['pid']
            write(directory / 'acknowledged.json', {'nonce': nonce, 'pid': target['pid'],
                                                    'observed_at_ns': time.monotonic_ns()})
            output, errors = process.communicate(timeout=10)
            communicated = True
            record['pause']['helper_transport'] = {'stdout_base64': base64.b64encode(output).decode(),
                'stderr_base64': base64.b64encode(errors).decode(),
                'stdout_sha256': hashlib.sha256(output).hexdigest(), 'stderr_sha256': hashlib.sha256(errors).hexdigest()}
            record['pause']['helper_exit_code'] = process.returncode
            finished = json.loads((directory / 'finished.json').read_text())
            assert process.returncode == 0 and not errors and finished['completed'], 'pause_guardian_failed'
            assert finished['nonce'] == nonce and finished['pid'] == target['pid'] and finished['birth'] == target['birth']
            record['pause']['completed'] = True
        except BaseException as error:
            record['pause']['failure'] = diagnostic(error)
        finally:
            sys.settrace(previous)
            try:
                if process is not None and not communicated:
                    if process.poll() is None:
                        process.terminate()
                    try:
                        output, errors = process.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        output, errors = process.communicate(timeout=3)
                    record['pause']['helper_transport'] = {'stdout_base64': base64.b64encode(output).decode(),
                        'stderr_base64': base64.b64encode(errors).decode(),
                        'stdout_sha256': hashlib.sha256(output).hexdigest(), 'stderr_sha256': hashlib.sha256(errors).hexdigest()}
                    record['pause']['helper_cleanup_exit_code'] = process.returncode
                record['pause']['helper_joined'] = process is not None and process.poll() is not None
                receipts = {}
                for name in ('ready.json', 'armed.json', 'continued.json', 'acknowledged.json', 'finished.json'):
                    path = directory / name
                    if path.exists():
                        raw = path.read_bytes()
                        receipts[name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'raw_utf8': raw.decode(),
                                          'value': json.loads(raw)}
                        if record['pause']['helper_joined']:
                            path.unlink()
                    if record['pause']['helper_joined']:
                        for pending in (directory / (name + '.pending'), path.with_suffix('.pending')):
                            if pending.exists():
                                pending.unlink()
                record['pause']['receipts'] = receipts
                if record['pause']['helper_joined']:
                    directory.rmdir()
            except BaseException as error:
                record['pause']['failure'] = record['pause'].get('failure') or diagnostic(error)
        return None

    sys.settrace(trace)
    try:
        yield
    finally:
        sys.settrace(previous)
