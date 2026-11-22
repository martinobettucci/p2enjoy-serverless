# @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
# @verifies docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
"""Start and observe the actual long DEV suite independently of its terminal."""
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import select
import shutil
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/e2e'
REPORT = OUTPUT / 'additional-regressions.json'
SUITE = runpy.run_path(str(ROOT / 'e2e/execution-suite.py'))


def atomic(path, value):
    pending = path.with_suffix('.pending')
    with pending.open('w') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno()); os.fchmod(stream.fileno(), 0o600)
    pending.replace(path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def process_identity(pid):
    root = Path('/proc', str(pid))
    return {'pid': pid, 'birth': root.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19],
            'cgroup': root.joinpath('cgroup').read_text()}


def unit_state(unit):
    command = ['systemctl', '--user', 'show', unit]
    command += ['--property=' + key for key in ('LoadState', 'ActiveState', 'SubState', 'MainPID',
        'ExecMainCode', 'ExecMainStatus', 'Result', 'ControlGroup', 'Type', 'RemainAfterExit',
        'TimeoutStartUSec', 'TimeoutStopUSec', 'KillMode', 'Restart')]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    value = dict(line.split('=', 1) for line in result.stdout.splitlines())
    assert result.returncode == 0 or result.returncode in (1, 4) and value.get('LoadState') == 'not-found'
    return value


def work_path(name):
    assert re.fullmatch(r'additional-regressions-worker-[0-9a-f]{32}', name)
    path = OUTPUT / name
    assert path.resolve() == path and path.stat().st_uid == os.geteuid() and path.stat().st_mode & 0o777 == 0o700
    return path


def start():
    os.chdir(ROOT); os.umask(0o077)
    assert not subprocess.check_output(['git', 'status', '--porcelain']), 'committed_clean_sources_required'
    OUTPUT.mkdir(mode=0o700, parents=True, exist_ok=True)
    name = 'additional-regressions-worker-' + uuid4().hex
    work = OUTPUT / name; work.mkdir(mode=0o700)
    unit = 'serverless-additional-regressions-' + name.rsplit('-', 1)[1]
    python = sys.executable; node = shutil.which('node'); assert node
    path_value = str(Path(node).parent) + ':' + str(Path(python).parent) + ':' + os.defpath
    state = {'completed': False, 'stage': 'prepared', 'created_at_ns': time.time_ns(), 'unit': unit,
             'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
             'source_sha256': SUITE['source_hashes'](), 'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    atomic(work / 'launch.json', state)
    credentials = SUITE['private_credentials']()
    try:
        with (work / 'service.stdout').open('xb') as stdout, (work / 'service.stderr').open('xb') as stderr:
            os.fchmod(stdout.fileno(), 0o600); os.fchmod(stderr.fileno(), 0o600)
            command = ['systemd-run', '--user', '--quiet', '--pipe', '--wait', '--unit=' + unit,
                '--property=Type=oneshot', '--property=RemainAfterExit=yes', '--property=Restart=no',
                '--property=TimeoutStartSec=21600', '--property=TimeoutStopSec=60',
                '--working-directory=' + str(ROOT), '--setenv=PATH=' + path_value,
                python, '-B', str(ROOT / 'e2e/additional-regressions-suite.py')]
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                     start_new_session=True, cwd=ROOT)
            state['client'] = process_identity(child.pid); atomic(work / 'launch.json', state)
            child.stdin.write(credentials); child.stdin.flush(); child.stdin.close()
    finally:
        credentials = None
    deadline = time.monotonic() + 20
    while True:
        current = unit_state(unit); pid = int(current.get('MainPID', '0'))
        if pid: break
        assert child.poll() is None and time.monotonic() < deadline, 'worker_start_not_confirmed'
        time.sleep(0.1)
    worker = process_identity(pid)
    assert current['ControlGroup'] and current['ControlGroup'] in worker['cgroup']
    assert current['Type'] == 'oneshot' and current['RemainAfterExit'] == 'yes' and current['Restart'] == 'no'
    state.update(stage='running', worker=worker, systemd=current, launch_returned_at_ns=time.time_ns())
    atomic(work / 'launch.json', state)
    print(json.dumps({'started': True, 'work': name, 'unit': unit, 'worker': worker,
                      'client': state['client'], 'systemd': current}), flush=True)


def observe(name, finish):
    work = work_path(name); state = json.loads((work / 'launch.json').read_text())
    assert state['unit'] == 'serverless-additional-regressions-' + name.rsplit('-', 1)[1]
    if finish and (work / 'finalized.json').exists():
        result = json.loads((work / 'finalized.json').read_text())
        if result.get('report_sha256'): assert hashlib.sha256((work/'suite-result.json').read_bytes()).hexdigest() == result['report_sha256']
        print(json.dumps(result)); return
    current = unit_state(state['unit']); pid = int(current.get('MainPID', '0'))
    value = {'unit': state['unit'], 'work': name, 'systemd': current, 'worker_running': bool(pid)}
    report = None
    if REPORT.exists() and REPORT.stat().st_mtime_ns >= state['created_at_ns']:
        raw = REPORT.read_bytes(); report = json.loads(raw)
        assert report['scope'] == 'additional-schema011' and report['source_commit'] == state['source_commit']
        value.update(report_sha256=hashlib.sha256(raw).hexdigest(), suite_completed=report['completed'],
            groups=sum(row.get('passed_groups', 0) for row in report['commands']),
            campaigns_completed=sum(bool(row.get('fresh_report_verified')) for row in report['commands']),
            last_campaign=report['commands'][-1]['campaign'] if report['commands'] else None,
            prerequisites_completed=sum(bool(row.get('fresh_report_verified')) for row in report['prerequisites']))
    if pid:
        identity = process_identity(pid)
        assert identity == state['worker'] and current['ControlGroup'] in identity['cgroup']
        value['worker'] = identity
        assert not finish, 'worker_still_running'
    elif finish:
        assert current['SubState'] in ('exited', 'failed') and current['ExecMainCode'] != '0', 'terminal_result_required'
        value['completed'] = bool(report and report['completed'] and current['Result'] == 'success'
                                   and current['ExecMainCode'] == '1' and current['ExecMainStatus'] == '0')
        if report is not None:
            saved=work/'suite-result.json'
            if saved.exists():assert saved.read_bytes()==raw, 'terminal_report_changed'
            else:
                with saved.open('xb') as stream:
                    stream.write(raw);stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o600)
        atomic(work / 'terminal-systemd.json', value)
        client = state['client']; descriptor = None
        try:
            identity = process_identity(client['pid'])
            if identity['birth'] == client['birth']:
                descriptor = os.pidfd_open(client['pid'])
                assert process_identity(client['pid']) == client, 'client_identity_changed'
        except FileNotFoundError:
            pass
        try:
            subprocess.run(['systemctl', '--user', 'stop', state['unit']], check=True, capture_output=True, timeout=60)
            after = unit_state(state['unit'])
            if after['ActiveState'] == 'failed':
                subprocess.run(['systemctl', '--user', 'reset-failed', state['unit']], check=True, capture_output=True, timeout=15)
                after = unit_state(state['unit'])
            assert after['ActiveState'] == 'inactive' and after.get('MainPID', '0') == '0'
            if descriptor is not None:
                assert select.select([descriptor], [], [], 60)[0], 'launch_client_not_joined'
        finally:
            if descriptor is not None: os.close(descriptor)
        value.update(unit_stopped=True, launch_client_joined=True, terminal_observed_at_ns=time.time_ns())
        atomic(work / 'finalized.json', value)
    atomic(work / ('observation-' + str(time.time_ns()) + '.json'), value)
    print(json.dumps(value), flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'start': start()
    elif len(sys.argv) == 3 and sys.argv[1] in ('status', 'finish'): observe(sys.argv[2], sys.argv[1] == 'finish')
    else: raise SystemExit('Usage: additional-regressions-worker.py start | status NOM | finish NOM')
