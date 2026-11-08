# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#garde-de-restauration-et-cycles-autorisés
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#garde-de-restauration-et-cycles-autorisés
"""Independent restoration through the existing console, for two authorized routes.

Only the principal's serial E2E pilot invokes this operator. No Forge command,
configuration replacement, DNS override or simulated response is involved.
"""
from contextlib import contextmanager
import argparse
import fcntl
import json
import os
from pathlib import Path
import runpy
import select
import stat
import subprocess
import sys
import time
from uuid import uuid4

C = runpy.run_path(str(Path(__file__).with_name('invocation-domain-console.py')))
api, console = C['api'], C['console']
ROOT, SPARK, SPARK_ID = C['ROOT'], C['SPARK'], C['SPARK_ID']
CANONICAL, ALIAS = C['CANONICAL'], C['ALIAS']
BASE = ROOT / '.local/e2e'


def process(pid):
    try:
        fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': pid, 'birth': fields[19], 'running': fields[0] != 'Z'}
    except (FileNotFoundError, ProcessLookupError):
        return None


def alive(identity):
    current = process(identity['pid'])
    return bool(current and current['running'] and current['birth'] == identity['birth'])


def folder_path(value):
    folder = Path(value)
    assert folder.parent == BASE and folder.name.startswith('invocation-route-guard-')
    info = folder.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700
    return folder


def load(folder):
    path = folder / 'identity.json'
    assert not path.is_symlink()
    return json.loads(path.read_text())


def save(folder, name, value):
    temporary = folder / (name + '.pending')
    with temporary.open('w') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    temporary.replace(folder / name)


@contextmanager
def mutation_lock(folder):
    fd = os.open(folder / 'mutation.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def inspect(identity=None):
    servers = console('/api/servers')
    server = next(row for row in servers['servers'] if row['name'] == C['SERVER'])
    assert server['host'] == C['PUBLIC_IP'] and server['port'] == 22
    spark = api('/sparks/' + SPARK)
    assert spark['id'] == SPARK_ID and spark['ipv4_address'] == '10.77.0.24'
    assert spark['runtime'] == 'container' and not spark['protected'], 'spark_not_writable'
    matches = api('/ingress/match', 'POST', {'domains': [CANONICAL, ALIAS]})['matches']
    rows = api('/ingress')['routes']
    result = {}
    for domain in (CANONICAL, ALIAS):
        row = next((row for row in rows if row['domain'] == domain), None)
        if row is None:
            assert domain == ALIAS and matches[domain] is None, 'route_absent_or_conflicting'
            result[domain] = None
            continue
        assert matches[domain] == {'domain': domain, 'spark_name': SPARK}
        assert row['spark_id'] == SPARK_ID and row['spark_name'] == SPARK
        assert row['ipv4_address'] == '10.77.0.24' and row['tls'] == row['enabled'] == 1
        assert row['target_port'] in (18090, 18091)
        if identity:
            expected = [identity['canonical_id']] if domain == CANONICAL else identity['alias_ids']
            assert row['id'] in expected, 'route_identity_changed'
        result[domain] = C['route_view'](row)
    return result


def project():
    response = api('/sparks/' + SPARK + '/suggestions')
    assert response.get('cell_read') is True, 'projection_not_confirmed'
    del response


def correct_port(domain, identity, folder):
    rows = inspect(identity)
    row = rows[domain]
    if row is None:
        assert domain == ALIAS
        api('/ingress', 'POST', {'spark': SPARK, 'domain': ALIAS, 'port': 18090, 'tls': True})
        created = inspect()[ALIAS]
        assert created and created['target_port'] == 18090
        identity['alias_ids'].append(created['id'])
        save(folder, 'identity.json', identity)
    elif row['target_port'] != 18090:
        api('/ingress/' + domain, 'PATCH', {'port': 18090, 'tls': True})
    # A lost response escapes to an explicit failure; never blindly replay a write.
    rows = inspect(identity)
    assert rows[domain] and rows[domain]['target_port'] == 18090


def restore(folder, trigger):
    result = {'completed': False, 'trigger': trigger, 'started_at_ns': time.time_ns(),
              'mutations_retried': 0}
    with mutation_lock(folder):
        identity = load(folder)
        try:
            result['before'] = inspect(identity)
            correct_port(CANONICAL, identity, folder)
            correct_port(ALIAS, identity, folder)
            project()
            result['after'] = inspect(identity)
            assert all(row and row['target_port'] == 18090 for row in result['after'].values())
            result['canonical_https'] = C['public_health'](CANONICAL)
            result['alias_https'] = C['public_health'](ALIAS)
            result.update(completed=True, finished_at_ns=time.time_ns())
        except BaseException as error:
            result['failure_type'] = type(error).__name__
            result['automatic_mutation_retry_forbidden'] = True
            try:
                result['state_after_failure'] = inspect(identity)
            except BaseException as reread_error:
                result['reread_failure_type'] = type(reread_error).__name__
        save(folder, 'restored.json', result)
    assert result['completed'], 'restoration_not_confirmed'


def watch(folder):
    identity = load(folder)
    assert identity['guard'] == process(os.getpid())
    inspect(identity)
    try:
        descriptor = os.pidfd_open(identity['owner']['pid'])
    except ProcessLookupError:
        restore(folder, 'owner_gone_before_ready')
        return
    try:
        if not alive(identity['owner']) or select.select([descriptor], [], [], 0)[0]:
            restore(folder, 'owner_gone_before_ready')
            return
        save(folder, 'ready.json', {'ready': True, 'guard': identity['guard'], 'observed_at_ns': time.time_ns()})
        while True:
            if (folder / 'restore.request').exists():
                trigger = 'explicit'
                break
            if select.select([descriptor], [], [], .1)[0] or not alive(identity['owner']):
                trigger = 'owner_gone'
                break
            if time.monotonic_ns() >= identity['deadline_ns']:
                trigger = 'deadline'
                break
        restore(folder, trigger)
    finally:
        os.close(descriptor)


def arm(owner, seconds):
    assert 15 <= seconds <= 180 and owner != os.getpid()
    assert Path('/proc', str(owner)).stat().st_uid == os.getuid()
    owner_identity = process(owner)
    assert owner_identity and owner_identity['running']
    rows = inspect()
    assert all(row and row['target_port'] == 18090 for row in rows.values())
    BASE.mkdir(exist_ok=True)
    folder = BASE / ('invocation-route-guard-' + str(uuid4()))
    folder.mkdir(mode=0o700)
    (folder / 'mutation.lock').touch(mode=0o600)
    identity = {'owner': owner_identity, 'canonical_id': rows[CANONICAL]['id'],
                'alias_ids': [rows[ALIAS]['id']], 'initial': rows,
                'deadline_ns': time.monotonic_ns() + seconds * 1000000000,
                'events': [], 'guard': None}
    save(folder, 'identity.json', identity)
    # The child waits for identity publication before recognizing readiness.
    with (folder / 'guard.log').open('wb') as log:
        child = subprocess.Popen([sys.executable, '-B', __file__, 'watch', '--folder', str(folder)],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    identity['guard'] = process(child.pid)
    assert identity['guard'] and identity['guard']['running']
    save(folder, 'identity.json', identity)
    (folder / 'start.request').touch(mode=0o600)
    deadline = time.monotonic() + 15
    while not (folder / 'ready.json').exists():
        assert child.poll() is None and time.monotonic() < deadline, 'guard_not_ready'
        time.sleep(.05)
    assert alive(identity['guard'])
    return {'folder': str(folder), 'guard': identity['guard'], 'owner': owner_identity}


def change(folder, action):
    assert not (folder / 'restored.json').exists() and not (folder / 'restore.request').exists()
    with mutation_lock(folder):
        assert not (folder / 'restored.json').exists() and not (folder / 'restore.request').exists()
        identity = load(folder)
        assert alive(identity['owner']) and alive(identity['guard'])
        assert time.monotonic_ns() < identity['deadline_ns']
        before = inspect(identity)
        event = {'action': action, 'before': before, 'started_at_ns': time.time_ns(),
                 'completed': False, 'response_unknown_until_return': True}
        identity['events'].append(event); save(folder, 'identity.json', identity)
        if action in ('divert-alias', 'divert-both'):
            names = (ALIAS,) if action == 'divert-alias' else (ALIAS, CANONICAL)
            for domain in names:
                current = inspect(identity)[domain]
                assert current and current['target_port'] == 18090
                api('/ingress/' + domain, 'PATCH', {'port': 18091, 'tls': True})
        elif action == 'remove-alias':
            assert before[ALIAS] and before[ALIAS]['target_port'] == 18090
            api('/ingress/' + ALIAS, 'DELETE')
        elif action == 'recreate-alias':
            assert before[ALIAS] is None
            api('/ingress', 'POST', {'spark': SPARK, 'domain': ALIAS, 'port': 18090, 'tls': True})
            created = inspect()[ALIAS]; assert created and created['target_port'] == 18090
            identity['alias_ids'].append(created['id'])
            save(folder, 'identity.json', identity)
        else:
            raise AssertionError('invalid_route_action')
        project()
        event['after'] = inspect(identity)
        expected_canonical = 18091 if action == 'divert-both' else 18090
        assert event['after'][CANONICAL]['target_port'] == expected_canonical
        if action == 'remove-alias':
            assert event['after'][ALIAS] is None
        else:
            assert event['after'][ALIAS]['target_port'] == (18091 if action.startswith('divert') else 18090)
        event.update(completed=True, response_unknown_until_return=False, finished_at_ns=time.time_ns())
        save(folder, 'identity.json', identity)
        return event


def release(folder):
    (folder / 'restore.request').touch(mode=0o600)
    deadline = time.monotonic() + 240
    identity = load(folder)
    while not (folder / 'restored.json').exists() or alive(identity['guard']):
        assert time.monotonic() < deadline, 'guard_termination_not_confirmed'
        time.sleep(.1)
    result = json.loads((folder / 'restored.json').read_text())
    assert result['completed'], 'guard_restore_failed'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('arm', 'watch', 'release', 'inspect',
                        'divert-alias', 'divert-both', 'remove-alias', 'recreate-alias'))
    parser.add_argument('--folder')
    parser.add_argument('--owner', type=int)
    parser.add_argument('--seconds', type=int, default=90)
    args = parser.parse_args()
    if args.action == 'arm':
        result = arm(args.owner, args.seconds)
    elif args.action == 'inspect':
        result = inspect()
    else:
        folder = folder_path(args.folder)
        if args.action == 'watch':
            deadline = time.monotonic() + 5
            while not (folder / 'start.request').exists():
                assert time.monotonic() < deadline
                time.sleep(.01)
            watch(folder)
            return
        result = release(folder) if args.action == 'release' else change(folder, args.action)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        # Console/provider error bodies and pending suggestions never enter output.
        print(json.dumps({'completed': False, 'failure_type': type(error).__name__}), flush=True)
        raise SystemExit(1) from None
