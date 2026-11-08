# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#garde-de-restauration-et-cycles-autorisés
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#garde-de-restauration-et-cycles-autorisés
"""Serial real-console proof of the route guard; no replacement dependencies."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / 'e2e/invocation-route-guard.py'
R = runpy.run_path(str(GUARD))


def call(*arguments):
    child = subprocess.run([sys.executable, '-B', str(GUARD), *arguments],
                           capture_output=True, text=True, timeout=260)
    assert child.returncode == 0, 'real_guard_command_failed'
    return json.loads(child.stdout)


def main():
    if sys.argv[1:] == ['--guard-owner-pilot']:
        armed = call('arm', '--owner', str(os.getpid()), '--seconds', '90')
        print(json.dumps({'event': 'armed', **armed}), flush=True)
        # A real process waits here, then the outer proof sends it SIGKILL.
        assert sys.stdin.buffer.readline() == b'explicit-owner-release\n'
        call('release', '--folder', armed['folder'])
        return
    scopes = {'--guard-baseline-only': 'baseline', '--guard-owner-loss-only': 'owner-loss',
              '--guard-deadline-only': 'deadline'}
    assert len(sys.argv) == 2 and sys.argv[1] in scopes, 'explicit_scope_required'
    scope = scopes[sys.argv[1]]
    out = ROOT / ('.local/e2e/invocation-route-guard-' + scope + '.json')
    assert not out.exists(), 'existing_evidence_requires_archiving'
    result = {'completed': False, 'scope': 'guard-' + scope + '-only', 'serial': True,
              'checks': [], 'skipped': 0, 'started_at_ns': time.time_ns(),
              'route_perturbations': 0, 'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [GUARD, Path(__file__), ROOT/'e2e/invocation-domain-console.py', ROOT/'docs/INVOCATION_URLS.md']}}
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    armed, pilot = None, None
    try:
        result['before'] = call('inspect')
        if scope in ('baseline', 'deadline'):
            armed = call('arm', '--owner', str(os.getpid()), '--seconds', '15' if scope == 'deadline' else '90')
        else:
            pilot = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--guard-owner-pilot'],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     start_new_session=True)
            assert select.select([pilot.stdout], [], [], 30)[0], 'real_owner_not_ready'
            armed = json.loads(pilot.stdout.readline(8192))
            assert armed['event'] == 'armed' and armed['owner'] == R['process'](pilot.pid)
        result['armed'] = armed
        folder = R['folder_path'](armed['folder'])
        assert R['alive'](armed['guard']) and R['alive'](armed['owner'])
        arguments = Path('/proc', str(armed['guard']['pid']), 'cmdline').read_bytes().split(b'\0')
        assert str(GUARD).encode() in arguments and str(folder).encode() in arguments
        result['ready'] = json.loads((folder/'ready.json').read_text())
        assert result['ready']['ready'] and result['ready']['guard'] == armed['guard']
        if scope == 'baseline':
            result['restoration'] = call('release', '--folder', str(folder))
            assert result['restoration']['trigger'] == 'explicit'
        else:
            if scope == 'owner-loss':
                pilot.kill()
                assert pilot.wait(timeout=10) == -signal.SIGKILL
                result['pilot_exit_code'] = pilot.returncode
                assert not R['alive'](armed['owner'])
            else:
                assert R['alive'](armed['owner'])
            deadline = time.monotonic() + 240
            while not (folder/'restored.json').exists() or R['alive'](armed['guard']):
                assert time.monotonic() < deadline, 'independent_restoration_not_confirmed'
                time.sleep(.1)
            result['restoration'] = json.loads((folder/'restored.json').read_text())
            assert result['restoration']['trigger'] == ('owner_gone' if scope == 'owner-loss' else 'deadline')
            if scope == 'deadline':
                assert R['alive'](armed['owner'])
            result['explicit_restore_requested'] = (folder/'restore.request').exists()
            assert not result['explicit_restore_requested']
        assert result['restoration']['completed']
        assert not R['alive'](armed['guard'])
        result['after'] = call('inspect')
        material = R['C']['route_configuration']
        assert {n: material(v) for n,v in result['before'].items()} == {n: material(v) for n,v in result['after'].items()}, 'baseline_routes_changed'
        result['identity'] = R['load'](folder)
        assert result['identity']['events'] == []
        names = {'baseline': 'Garde réelle prête puis restauration explicite sans perturbation, deux HTTPS et fin confirmée',
                 'owner-loss': 'SIGKILL réel du pilote, restauration indépendante sans demande explicite, deux HTTPS et fin confirmée',
                 'deadline': 'Échéance réelle avec pilote vivant, restauration indépendante sans demande explicite, deux HTTPS et fin confirmée'}
        name = names[scope]
        result['checks'].append({'name': name, 'status': 'passed'})
        result.update(completed=True, cleanup=True, finished_at_ns=time.time_ns())
        print('PASS garde indépendante ' + scope + ' sans perturbation', flush=True)
    except BaseException as error:
        result['failure_type'] = type(error).__name__
        if pilot and pilot.poll() is None:
            pilot.kill(); pilot.wait(timeout=10)
        if armed:
            try:
                result['failure_restoration'] = call('release', '--folder', armed['folder'])
            except BaseException as restore_error:
                result['restoration_failure_type'] = type(restore_error).__name__
        raise RuntimeError('guard_proof_failed_inspect_private_receipt') from None
    finally:
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
