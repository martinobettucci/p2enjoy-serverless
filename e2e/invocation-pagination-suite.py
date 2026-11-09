# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
"""Serial real-console lifecycle, then six-domain UI/CLI proof and native cleanup.

All declarations share the file contract. No subordinate agent operates tests.
The lease owner is a real child; its loss triggers the independently armed guard.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import select
import signal
import socket
import subprocess
import sys
import time
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
R = runpy.run_path(str(ROOT / 'e2e/execution-suite.py'))
G = runpy.run_path(str(ROOT / 'e2e/invocation-pagination-domains.py'))
BASE, OPERATOR = G['BASE'], ROOT / 'e2e/invocation-pagination-domains.py'


def operator(*args):
    child = subprocess.run([sys.executable, '-B', str(OPERATOR), *args], capture_output=True, text=True, timeout=660)
    assert child.returncode == 0, 'normal_console_operator_failed:' + child.stdout[-3000:]
    return json.loads(child.stdout)


def owner():
    child = subprocess.Popen([sys.executable, '-B', __file__, '--lease-owner'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    assert select.select([child.stdout], [], [], 10)[0], 'lease_owner_not_ready'
    identity = json.loads(child.stdout.readline(4096))
    assert identity == G['process'](child.pid), 'lease_owner_identity'
    return child, identity


def await_cleaned(armed):
    folder = G['folder_path'](armed['folder']); deadline = time.monotonic() + 660
    while not (folder / 'cleaned.json').exists() or G['alive'](armed['guard']):
        assert time.monotonic() < deadline, 'independent_cleanup_not_finished'
        time.sleep(.1)
    result = json.loads((folder / 'cleaned.json').read_text())
    assert result['completed'], 'independent_cleanup_failed_inspect_private_receipt'
    assert not G['alive'](armed['guard'])
    return result


def native(reports):
    child = subprocess.run(R['SSH'] + ['root@10.77.0.24', 'python3 -B /srv/p2enjoy-serverless/e2e/invocation-pagination-native.py'],
                           input=json.dumps({'reports': reports}), capture_output=True, text=True, timeout=90)
    assert child.returncode == 0, 'native_correlation_failed:' + child.stderr[-1500:]
    result = json.loads(child.stdout)
    expected = {str(p.relative_to(ROOT / 'control')): hashlib.sha256(p.read_bytes()).hexdigest()
                for directory, pattern in [('control/app', '*.py'), ('control/migrations', '*.sql')] for p in (ROOT / directory).glob(pattern)}
    expected['function_code_hash.py'] = hashlib.sha256((ROOT / 'function_code_hash.py').read_bytes()).hexdigest()
    assert result['embedded_sha256'] == expected, 'embedded_backend_differs'
    return result


def fresh_snapshot(path):
    return R['snapshot'](str(path.relative_to(ROOT)), False, include_adapter=True)


def unchanged(before, after):
    assert before['source_sha256'] == after['source_sha256'], 'sources_changed_during_proof'
    assert before['image'] == after['image'] and before['adapter_images'] == after['adapter_images'], 'images_changed_during_proof'


def save(path, value):
    G['save'](path.parent, path.name, value)


def prerequisites():
    path = BASE / 'invocation-pagination-guard-prerequisites.json'
    assert not path.exists(), 'preserve_existing_receipt'
    result = {'completed': False, 'checks': [], 'skipped': 0, 'started_at_ns': time.time_ns(), 'temporary_mutations': 0}
    save(path, result)
    result['before'] = fresh_snapshot(path); save(path, result)
    for trigger in ('explicit', 'deadline', 'owner_gone'):
        child = armed = None
        try:
            child, identity = owner()
            armed = operator('arm', '--owner', str(child.pid), '--seconds', '15' if trigger == 'deadline' else '120')
            assert armed['owner'] == identity
            result.setdefault('guards', []).append(armed); save(path, result)
            if trigger == 'explicit':
                outcome = operator('release', '--folder', armed['folder'])
                assert G['alive'](identity)
            else:
                if trigger == 'owner_gone':
                    child.kill(); assert child.wait(timeout=10) == -signal.SIGKILL
                outcome = await_cleaned(armed)
                assert not (Path(armed['folder']) / 'cleanup.request').exists()
                assert G['alive'](identity) == (trigger == 'deadline')
            assert outcome['trigger'] == trigger and outcome['completed']
            recorded = G['load'](Path(armed['folder']))
            assert recorded['events'] == [] and not G['alive'](armed['guard'])
            result['checks'].append({'name': trigger, 'status': 'passed', 'armed': armed, 'cleanup': outcome})
            print('PASS garde sans objet ' + trigger, flush=True); save(path, result)
        finally:
            if child and child.poll() is None:
                child.stdin.close(); assert child.wait(timeout=10) == 0
            if armed and G['alive'](armed['guard']):
                result['failure_cleanup'] = operator('release', '--folder', armed['folder']); save(path, result)
    result['after'] = fresh_snapshot(path); unchanged(result['before'], result['after'])
    result.update(completed=True, finished_at_ns=time.time_ns()); save(path, result)


def campaign():
    prerequisite_path = BASE / 'invocation-pagination-guard-prerequisites.json'
    prerequisite = json.loads(prerequisite_path.read_text())
    assert prerequisite['completed'] and len(prerequisite['checks']) == 3
    path = BASE / 'invocation-pagination-campaign.json'
    assert not path.exists(), 'preserve_existing_campaign'
    result = {'completed': False, 'started_at_ns': time.time_ns(), 'checks': [], 'skipped': 0, 'cleanup': False,
              'prerequisite_sha256': hashlib.sha256(prerequisite_path.read_bytes()).hexdigest()}
    save(path, result)
    result['before'] = fresh_snapshot(path); unchanged(prerequisite['after'], result['before'])
    result['native_before'] = native([]); save(path, result)
    child = armed = None
    try:
        child, _ = owner(); armed = operator('arm', '--owner', str(child.pid), '--seconds', '1800')
        result['armed'] = armed; save(path, result)
        for name in G['NAMES']:
            result.setdefault('creations', []).append(operator('create', '--folder', armed['folder'], '--domain', name)); save(path, result)
        # Only now query native resolution; absent names were never prewarmed.
        for name in G['NAMES']:
            deadline = time.monotonic() + 420
            while True:
                try:
                    addresses = sorted({row[4][0] for row in socket.getaddrinfo(name, 443, type=socket.SOCK_STREAM)})
                    assert addresses == [G['C']['PUBLIC_IP']], 'native_dns_conflict'
                    https = G['C']['public_health'](name)
                    break
                except (socket.gaierror, urllib.error.URLError, TimeoutError):
                    assert time.monotonic() < deadline, 'native_dns_or_verified_tls_not_ready'
                    print(json.dumps({'waiting_native_https': name}), flush=True); time.sleep(3)
            result.setdefault('verified_aliases', []).append({'domain': name, 'addresses': addresses, 'https': https}); save(path, result)
        result['checks'].append({'name': 'Four authorized exact A records and TLS routes, native DNS/HTTPS', 'status': 'passed'}); save(path, result)
        reports = []
        for mode in ('ui', 'cli'):
            report_path = BASE / ('invocation-pagination-' + mode + '.json')
            assert not report_path.exists(), 'preserve_previous_client_report'
            before = fresh_snapshot(report_path); unchanged(result['before'], before); started = time.time_ns()
            output = subprocess.run(['node', str(ROOT / 'e2e/invocation-pagination.mjs'), mode, armed['folder']],
                                    capture_output=True, text=True, timeout=660)
            log = BASE / ('invocation-pagination-' + mode + '.log'); log.write_text(output.stdout + output.stderr)
            print(output.stdout, end='', flush=True)
            after = fresh_snapshot(report_path); unchanged(before, after)
            proof = json.loads(report_path.read_text())
            result.setdefault('clients', []).append({'mode': mode, 'before': before, 'after': after, 'exit_code': output.returncode,
                                                    'report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(), 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}); save(path, result)
            assert output.returncode == 0 and proof['completed'] and proof['cleanup'] and not proof['cleanup_errors']
            assert len(proof['checks']) == 3 and all(c['status'] == 'passed' for c in proof['checks']) and proof['skipped'] == 0
            assert after['report']['mtime_ns'] > started
            reports.append(proof)
        result['native_after_clients'] = native(reports); save(path, result)
        for field in ('containers', 'official_sha256', 'embedded_sha256', 'migrations', 'global_counts', 'storage_counts'):
            assert result['native_after_clients'][field] == result['native_before'][field], 'native_baseline_changed:' + field
        assert len(result['native_after_clients']['invocations']) == 14
        child.kill(); assert child.wait(timeout=10) == -signal.SIGKILL
        result['owner_sigkill'] = {'identity': armed['owner'], 'exit_code': child.returncode}; save(path, result)
        result['independent_cleanup'] = await_cleaned(armed)
        assert result['independent_cleanup']['trigger'] == 'owner_gone'
        assert not (Path(armed['folder']) / 'cleanup.request').exists()
        recorded = G['load'](Path(armed['folder']))
        assert len(recorded['events']) == 16 and all(e['response_known'] for e in recorded['events'])
        assert all(v['route_deleted'] and v['dns_deleted'] for v in recorded['objects'].values())
        result['object_receipt'] = recorded
        result['checks'].append({'name': 'SIGKILL réel du propriétaire puis retrait indépendant des huit objets connus', 'status': 'passed'})
        result['after'] = fresh_snapshot(path); unchanged(result['before'], result['after'])
        result.update(completed=True, cleanup=True, finished_at_ns=time.time_ns()); save(path, result)
        print('PASS retrait indépendant des quatre routes et des quatre A', flush=True)
    except BaseException as error:
        result['failure'] = {'type': type(error).__name__, 'reason': str(error) if isinstance(error, AssertionError) else 'campaign_failed'}
        save(path, result)
        raise
    finally:
        owner_error = None
        try:
            if child and child.poll() is None:
                child.stdin.close(); child.wait(timeout=10)
        except BaseException as join_error:
            owner_error = join_error
            result['completed'] = False
            result['owner_join_failure'] = {'type': type(join_error).__name__}
        try:
            if armed:
                result['failure_cleanup'] = await_cleaned(armed)
                result['cleanup'] = result['failure_cleanup']['completed']
        except BaseException as cleanup_error:
            result['cleanup_failure'] = {'type': type(cleanup_error).__name__, 'reason': str(cleanup_error) if isinstance(cleanup_error, AssertionError) else 'cleanup_failed'}
            raise
        finally:
            save(path, result)
        if owner_error:
            raise RuntimeError('lease_owner_join_failed_inspect_receipt') from None


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('--guard-prerequisites', '--campaign', '--lease-owner')
    if sys.argv[1] == '--lease-owner':
        print(json.dumps(G['process'](os.getpid())), flush=True)
        assert sys.stdin.buffer.read(1) == b''
    elif sys.argv[1] == '--guard-prerequisites':
        prerequisites()
    else:
        campaign()
