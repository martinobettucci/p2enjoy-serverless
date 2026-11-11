# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#essai-interrompu-et-pilote-durable
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#essai-interrompu-et-pilote-durable
"""Run the real long source-retention proof in a transient local user service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import stat
import struct
import subprocess
import sys
import time
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.local/e2e'
PREFIX = 'serverless-source-retention-proof-'


def atomic(path, value):
    pending = path.with_suffix('.pending')
    with open(pending, 'w', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    pending.replace(path)
    descriptor=os.open(path.parent,os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def context(identifier):
    assert str(UUID(identifier)) == identifier, 'canonical_worker_id_required'
    return PREFIX + identifier + '.service', OUT / ('source-retention-worker-' + identifier)


def unit_state(unit):
    result = subprocess.run(['systemctl','--user','show',unit,'--property=LoadState,ActiveState,SubState,MainPID,Result,ExecMainCode,ExecMainStatus,Type,RemainAfterExit,TimeoutStartUSec,TimeoutStopUSec,KillMode'],
                            capture_output=True,text=True,timeout=15)
    assert result.returncode in (0,1), 'user_unit_state_unavailable'
    return dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)


def peer(connection):
    return struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i')))


def address(identifier):
    return '\0p2enjoy-serverless-source-retention-' + str(os.getuid()) + '-' + identifier


def birth(pid):
    return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]


def receive_credentials(identifier):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as listener:
        listener.settimeout(45);listener.bind(address(identifier));listener.listen(1)
        connection,_ = listener.accept()
        with connection:
            connection.settimeout(15)
            assert peer(connection)[1] == os.getuid(), 'private_client_uid_mismatch'
            with connection.makefile('rb') as incoming:
                raw = incoming.readline(8194)
            assert raw.endswith(b'\n') and len(raw) <= 8192, 'private_input_invalid'
            value = json.loads(raw)
            assert isinstance(value,dict) and all(isinstance(value.get(key),str) and 0<len(value[key])<=2048 for key in ('username','password')), 'private_input_invalid'
            normalized = (json.dumps({key:value[key] for key in ('username','password')})+'\n').encode()
            connection.sendall(json.dumps({'accepted':True,'pid':os.getpid(),'worker_id':identifier}).encode()+b'\n')
            return normalized


def start():
    active = subprocess.run(['systemctl','--user','list-units','--state=active,activating','--type=service','--plain','--no-legend',PREFIX+'*.service'],
                            capture_output=True,text=True,timeout=15)
    assert active.returncode == 0 and not active.stdout.strip(), 'source_retention_worker_already_active'
    suite = runpy.run_path(str(ROOT/'e2e/execution-suite.py'))
    credentials = suite['private_credentials']()
    identifier = str(uuid4());unit,folder = context(identifier)
    OUT.mkdir(mode=0o700,parents=True,exist_ok=True);folder.mkdir(mode=0o700)
    node = Path(shutil.which('node')).resolve();python = Path(sys.executable).resolve()
    assert node.is_file() and os.access(node,os.X_OK)
    launch = ['systemd-run','--user','--quiet','--no-block','--unit='+unit,'--working-directory='+str(ROOT),
              '--property=Type=oneshot','--property=RemainAfterExit=yes','--property=TimeoutStartSec=3600',
              '--property=TimeoutStopSec=60','--property=KillMode=control-group','--property=UMask=0077',
              '--property=StandardOutput=append:'+str(folder/'worker.log'),
              '--property=StandardError=append:'+str(folder/'worker.log')]
    if os.environ.get('SSH_AUTH_SOCK'):launch += ['--setenv=SSH_AUTH_SOCK='+os.environ['SSH_AUTH_SOCK']]
    launch += [str(python),'-B','-u',str(Path(__file__).resolve()),'worker',identifier,'--node',str(node)]
    subprocess.run(launch,check=True,capture_output=True,timeout=20)
    deadline = time.monotonic()+40
    while True:
        value = unit_state(unit);pid = int(value.get('MainPID','0'))
        assert value.get('ActiveState') in ('active','activating','inactive'), 'source_retention_worker_not_active'
        if not pid:
            assert time.monotonic()<deadline,'worker_main_pid_missing'
            time.sleep(.1);continue
        try:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(10);connection.connect(address(identifier))
                server_pid,uid,_ = peer(connection)
                assert uid == os.getuid() and server_pid == pid and pid>0, 'private_worker_identity_mismatch'
                pinned_birth = birth(pid)
                connection.sendall(credentials);credentials=None
                with connection.makefile('rb') as incoming:accepted=json.loads(incoming.readline(1024))
                assert accepted == {'accepted':True,'pid':pid,'worker_id':identifier}, 'private_worker_ack_invalid'
                assert birth(pid) == pinned_birth, 'worker_identity_changed'
                atomic(folder/'launch.json',{'worker_id':identifier,'unit':unit,'main_pid':pid,'worker_birth':pinned_birth,
                    'controller_pid':os.getpid(),'controller_birth':birth(os.getpid()),'controller_cgroup':Path('/proc/self/cgroup').read_text(),
                    'accepted_at_ns':time.time_ns()})
                print(json.dumps({'started':True,'worker_id':identifier,'unit':unit,'main_pid':pid,'birth':pinned_birth,
                                  'checkpoint':str(folder/'checkpoint.json'),'log':str(folder/'worker.log')}))
                return
        except ConnectionRefusedError:
            assert time.monotonic()<deadline,'private_worker_not_listening'
            time.sleep(.1)


def worker(identifier,node):
    unit,folder = context(identifier)
    info = folder.lstat()
    assert folder.resolve() == folder and stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700
    checkpoint = folder/'checkpoint.json'
    state = {'completed':False,'worker_id':identifier,'unit':unit,'pid':os.getpid(),'birth':birth(os.getpid()),
             'parent_pid':os.getppid(),'cgroup':Path('/proc/self/cgroup').read_text(),'phase':'private_input',
             'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'started_at_ns':time.time_ns()}
    atomic(checkpoint,state)
    credentials = None;process = None
    try:
        credentials = receive_credentials(identifier)
        configuration=unit_state(unit)
        assert configuration.get('MainPID')==str(os.getpid()) and configuration.get('Type')=='oneshot'
        assert configuration.get('RemainAfterExit')=='yes' and configuration.get('TimeoutStartUSec')=='1h'
        assert configuration.get('TimeoutStopUSec')=='1min' and configuration.get('KillMode')=='control-group'
        state.update(credential_accepted=True,user_unit_configuration=configuration,phase='before_snapshot');atomic(checkpoint,state)
        suite = runpy.run_path(str(ROOT/'e2e/execution-suite.py'))
        before = suite['snapshot'](str(checkpoint),False,include_adapter=True)
        state['before']=before
        prior = set(OUT.glob('invocation-source-retention-volume-*.json'))
        node_path = Path(node)
        assert node_path.resolve()==node_path and node_path.is_file() and os.access(node_path,os.X_OK)
        with (folder/'client.log').open('wb') as output:
            os.fchmod(output.fileno(),0o600)
            process = subprocess.Popen([str(node_path),str(ROOT/'e2e/invocation-source-retention-volume.mjs')],
                stdin=subprocess.PIPE,stdout=output,stderr=subprocess.STDOUT,cwd=ROOT)
            state.update(node_pid=process.pid,node_birth=birth(process.pid),phase='real_e2e_running');atomic(checkpoint,state)
            process.stdin.write(credentials);process.stdin.flush();process.stdin.close();credentials=None
            code = process.wait(timeout=3000)
        state.update(node_exit_code=code,phase='after_snapshot');atomic(checkpoint,state)
        reports = set(OUT.glob('invocation-source-retention-volume-*.json'))-prior
        assert len(reports)==1,'exactly_one_real_report_required'
        path = reports.pop();report=json.loads(path.read_text())
        state.update(report_path=str(path),report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),report=report)
        after = suite['snapshot'](str(path),False,include_adapter=True);state['after']=after
        assert all(before[key]==after[key] for key in ('source_sha256','image','adapter_images')), 'proof_sources_changed'
        assert code==0 and report['completed'] and report['cleanup'] and not report['failure'] and report['skipped']==0,'real_e2e_not_completed'
        assert len(report['checks'])==3 and all(row['status']=='passed' for row in report['checks']) and len(report['responses'])==10001, 'real_e2e_groups_missing'
        state.update(completed=True,phase='completed')
    except BaseException as error:
        state.update(phase='failed',failure_type=type(error).__name__,failure_message_sha256=hashlib.sha256(str(error).encode()).hexdigest())
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=60)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=15)
    finally:
        credentials=None;state['finished_at_ns']=time.time_ns();atomic(checkpoint,state)
    print(json.dumps({'completed':state['completed'],'worker_id':identifier,'phase':state['phase'],'checkpoint':str(checkpoint)}))
    if not state['completed']:raise SystemExit(1)


def status(identifier):
    unit,folder = context(identifier)
    value = unit_state(unit)
    result = {'worker_id':identifier,'unit':unit,'systemd':value}
    if (folder/'checkpoint.json').exists():
        record=json.loads((folder/'checkpoint.json').read_text())
        result['checkpoint']={key:record[key] for key in ('completed','phase','pid','birth','parent_pid','cgroup','started_at_ns','finished_at_ns','report_path','node_exit_code','failure_type') if key in record}
        pid=int(value.get('MainPID','0'))
        if pid:
            assert pid==record['pid'] and birth(pid)==record['birth'],'worker_identity_changed'
            assert Path('/proc',str(pid),'cgroup').read_text()==record['cgroup'],'worker_cgroup_changed'
            launch=json.loads((folder/'launch.json').read_text())
            assert launch['worker_id']==identifier and launch['main_pid']==pid and launch['worker_birth']==record['birth']
            try:controller_alive=birth(launch['controller_pid'])==launch['controller_birth']
            except FileNotFoundError:controller_alive=False
            assert not controller_alive,'initial_controller_still_running'
            observer_cgroup=Path('/proc/self/cgroup').read_text()
            assert observer_cgroup!=record['cgroup'] and unit in record['cgroup'],'worker_not_in_independent_user_unit'
            result.update(real_process_confirmed=True,controller_ended=True,observer_pid=os.getpid(),observer_cgroup=observer_cgroup)
            atomic(folder/('live-observation-'+str(time.time_ns())+'.json'),result)
    print(json.dumps(result))


def finish(identifier):
    unit,folder=context(identifier)
    receipt_path=folder/'terminal-systemd.json'
    checkpoint=folder/'checkpoint.json';record=json.loads(checkpoint.read_text())
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text())
        assert receipt['worker_id']==identifier and receipt['main_process_ended'], 'worker_receipt_identity_mismatch'
        assert receipt['checkpoint_sha256']==hashlib.sha256(checkpoint.read_bytes()).hexdigest(), 'terminal_checkpoint_changed'
        if receipt['finalized']:
            print(json.dumps(receipt));return
    else:
        value=unit_state(unit)
        assert value.get('LoadState')=='loaded' and value.get('MainPID')=='0', 'worker_still_running_or_result_missing'
        assert (value.get('ActiveState'),value.get('SubState')) in (('active','exited'),('failed','failed')), 'worker_not_terminal'
        assert record['worker_id']==identifier,'worker_checkpoint_identity_mismatch'
        success=(value.get('Result')=='success' and value.get('ExecMainCode')=='1' and value.get('ExecMainStatus')=='0' and
                 record.get('finished_at_ns') and record['completed'] and record.get('node_exit_code')==0)
        receipt={'worker_id':identifier,'completed':bool(success),'finalized':False,'systemd_before_stop':value,
                 'checkpoint_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),'main_process_ended':True,
                 'observed_at_ns':time.time_ns()}
        atomic(receipt_path,receipt)
    current=unit_state(unit)
    assert current.get('MainPID','0')=='0','worker_process_reappeared'
    already_inactive=current.get('LoadState')=='not-found' and current.get('ActiveState')=='inactive'
    if already_inactive:
        stop_code=None
    else:
        stopped=subprocess.run(['systemctl','--user','stop',unit],capture_output=True,timeout=30)
        assert stopped.returncode==0,'worker_unit_not_stopped'
        stop_code=stopped.returncode
    after=unit_state(unit)
    if after.get('ActiveState')=='failed':
        reset=subprocess.run(['systemctl','--user','reset-failed',unit],capture_output=True,timeout=15)
        assert reset.returncode==0,'worker_failed_unit_not_released'
        after=unit_state(unit)
    assert after.get('MainPID','0')=='0' and after.get('ActiveState')=='inactive','worker_unit_retained'
    receipt.update(finalized=True,stop_exit_code=stop_code,already_inactive_on_resume=already_inactive,
                   systemd_after_stop=after,finished_at_ns=time.time_ns())
    atomic(receipt_path,receipt);print(json.dumps(receipt))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['start','worker','status','finish'])
    parser.add_argument('identifier',nargs='?')
    parser.add_argument('--node')
    args=parser.parse_args()
    if args.operation=='start':
        assert args.identifier is None and args.node is None
        start()
    elif args.operation=='status':
        assert args.identifier and args.node is None
        status(args.identifier)
    elif args.operation=='finish':
        assert args.identifier and args.node is None
        finish(args.identifier)
    else:
        assert args.identifier and args.node
        worker(args.identifier,args.node)


if __name__=='__main__':main()
