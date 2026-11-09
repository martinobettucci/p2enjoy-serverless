# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
"""Bounded ownership of four authorized routes and A records through normal console.

Every function shares the file contract. No system administration, credentials,
DNS override, TLS bypass or automatic mutation retry is performed here.
"""
from contextlib import contextmanager
import argparse
import fcntl
import json
import os
from pathlib import Path
import runpy
import re
import select
import stat
import subprocess
import sys
import time
import traceback
from uuid import uuid4

G = runpy.run_path(str(Path(__file__).with_name('invocation-route-guard.py')))
C = G['C']
console, api, process, alive = C['console'], C['api'], G['process'], G['alive']
ROOT, BASE = C['ROOT'], G['BASE']
NAMES = tuple(f'functions-pagination-{i}.lelabs.tech' for i in range(1, 5))
PERMANENT = (C['CANONICAL'], C['ALIAS'])
ZONE = 'lelabs.tech'


def folder_path(value):
    folder = Path(value)
    assert folder.parent == BASE and folder.name.startswith('invocation-pagination-domains-')
    info = folder.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700
    return folder


def save(folder, name, value):
    path = folder / (name + '.pending')
    fd = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    path.replace(folder / name)
    fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load(folder):
    assert not (folder / 'identity.json').is_symlink()
    return json.loads((folder / 'identity.json').read_text())


@contextmanager
def lock(folder):
    fd = os.open(folder / 'mutation.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
        deadline = time.monotonic() + 60
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                assert time.monotonic() < deadline, 'mutation_lock_deadline'
                time.sleep(.1)
        yield
    finally:
        os.close(fd)


def inspect():
    # Zone publication status may transition after a successful DNS mutation.
    # Ownership still comes from exact provider records and route identities.
    servers = console('/api/servers')
    assert servers['current'] == C['SERVER'], 'normal_console_server_changed'
    baseline = G['inspect']()
    for domain in PERMANENT:
        owned_route(baseline[domain], domain)
    assert baseline[PERMANENT[0]]['id'] == '2aedd847cd94ddf80ee9aa89'
    zones = console('/api/dns/zones')
    assert zones.get('configured') is True, 'dns_not_configured'
    zone = next(row for row in zones['zones'] if row['zone'] == ZONE)
    routes = api('/ingress')['routes']
    matches = api('/ingress/match', 'POST', {'domains': list(NAMES)})['matches']
    records = console('/api/dns/records?zone=' + ZONE)['records']
    assert len(records) + 4 < 100, 'provider_inventory_may_be_truncated'
    dns_keys = ('id', 'name', 'type', 'data', 'ttl')
    dns = {}
    for domain in (*PERMANENT, *NAMES):
        label = domain.removesuffix('.' + ZONE)
        dns[domain] = [{key: row.get(key) for key in dns_keys} for row in records if row['name'] == label]
    return {'permanent': baseline, 'zone_status': zone['status'],
            'permanent_dns': {name: dns[name] for name in PERMANENT},
            'routes': {name: C['route_view'](next(row for row in routes if row['domain'] == name))
                       if any(row['domain'] == name for row in routes) else None for name in NAMES},
            'matches': matches, 'dns': {name: dns[name] for name in NAMES}, 'dns_count': len(records)}


def same_permanent(current, initial):
    material = C['route_configuration']
    assert {n: material(v) for n, v in current['permanent'].items()} == {
        n: material(v) for n, v in initial['permanent'].items()}, 'permanent_routes_changed'
    assert current['permanent_dns'] == initial['permanent_dns'], 'permanent_dns_changed'


def owned_route(row, domain):
    assert row and row['domain'] == domain and row['spark_id'] == C['SPARK_ID']
    assert row['spark_name'] == C['SPARK'] and row['ipv4_address'] == '10.77.0.24'
    assert row['target_port'] == 18090 and row['tls'] == row['enabled'] == 1
    assert row['id'], 'route_identity_missing'


def known_dns(rows, domain):
    assert len(rows) == 1, 'unexpected_dns_types_or_cardinality'
    row = rows[0]
    assert row['id'] and row['name'] == domain.removesuffix('.' + ZONE)
    assert row['type'] == 'A' and row['data'] == C['PUBLIC_IP'] and row['ttl'] == 300
    return row


def diagnostic(error):
    reason = str(error) if isinstance(error, AssertionError) else ''
    return {'failure_type': type(error).__name__,
            'reason': reason if re.fullmatch(r'[a-z0-9_]{1,120}', reason) else 'inspect_failure_frames',
            'frames': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name}
                       for f in traceback.extract_tb(error.__traceback__)[-6:]]}


def permitted(folder, identity):
    assert not (folder / 'cleanup.request').exists() and not (folder / 'cleaned.json').exists()
    assert alive(identity['owner']) and alive(identity['guard'])
    assert time.monotonic_ns() < identity['deadline_ns'], 'campaign_deadline'


def event(folder, identity, action, domain):
    value = {'action': action, 'domain': domain, 'response_known': False, 'started_at_ns': time.time_ns()}
    identity['events'].append(value); save(folder, 'identity.json', identity)
    return value


def project():
    assert api('/sparks/' + C['SPARK'] + '/suggestions').get('cell_read') is True


def change(folder, action, domain):
    assert domain in NAMES, 'unauthorized_name'
    with lock(folder):
        identity = load(folder); permitted(folder, identity)
        assert not any(e['domain'] == domain and not e['response_known'] for e in identity['events']), 'response_unknown_requires_review'
        current = inspect(); same_permanent(current, identity['initial'])
        permitted(folder, identity)
        item = identity['objects'][domain]
        if action == 'create':
            assert not any(e['domain'] == domain for e in identity['events']), 'creation_already_attempted'
            assert item == {'dns': None, 'route': None, 'route_deleted': False, 'dns_deleted': False}
            assert current['matches'][domain] is None and current['routes'][domain] is None and not current['dns'][domain]
            intent = event(folder, identity, 'create-dns', domain)
            console('/api/dns/record', 'POST', {'domain': domain, 'zone': ZONE, 'address': C['PUBLIC_IP']})
            intent['response_known'] = True; save(folder, 'identity.json', identity)
            fresh = inspect(); same_permanent(fresh, identity['initial'])
            item['dns'] = known_dns(fresh['dns'][domain], domain); save(folder, 'identity.json', identity)
            assert fresh['matches'][domain] is None and fresh['routes'][domain] is None
            permitted(folder, identity)
            intent = event(folder, identity, 'create-route', domain)
            api('/ingress', 'POST', {'spark': C['SPARK'], 'domain': domain, 'port': 18090, 'tls': True})
            intent['response_known'] = True; save(folder, 'identity.json', identity)
            fresh = inspect(); same_permanent(fresh, identity['initial'])
            owned_route(fresh['routes'][domain], domain)
            assert fresh['matches'][domain] == {'domain': domain, 'spark_name': C['SPARK']}
            item['route'] = fresh['routes'][domain]; save(folder, 'identity.json', identity)
            project()
        else:
            assert action == 'remove-route'
            remove_route(folder, identity, current, domain, running=True)
            project()
        return {'completed': True, 'action': action, 'domain': domain, 'objects': item}


def remove_route(folder, identity, current, domain, running=False):
    item = identity['objects'][domain]
    if item['route_deleted']:
        assert current['routes'][domain] is None and current['matches'][domain] is None
        return
    assert item['route'] is not None, 'route_creation_not_identified'
    assert C['route_configuration'](current['routes'][domain]) == C['route_configuration'](item['route']), 'route_ownership_changed'
    assert current['matches'][domain] == {'domain': domain, 'spark_name': C['SPARK']}
    if running:
        permitted(folder, identity)
    intent = event(folder, identity, 'delete-route', domain)
    api('/ingress/' + domain, 'DELETE')
    intent['response_known'] = True; item['route_deleted'] = True; save(folder, 'identity.json', identity)


def clean(folder, trigger):
    result = {'completed': False, 'trigger': trigger, 'started_at_ns': time.time_ns(), 'errors': [], 'mutation_retries': 0}
    try:
        with lock(folder):
            identity = load(folder)
            result['before'] = inspect(); same_permanent(result['before'], identity['initial'])
            unknown = [e for e in identity['events'] if not e['response_known']]
            result['unknown_responses'] = unknown
            for domain in NAMES:
                try:
                    assert not any(e['domain'] == domain for e in unknown), 'response_unknown_requires_review'
                    item = identity['objects'][domain]
                    current = inspect(); same_permanent(current, identity['initial'])
                    if item['route'] is not None:
                        remove_route(folder, identity, current, domain)
                        current = inspect()
                    else:
                        assert current['routes'][domain] is None and current['matches'][domain] is None
                        assert not any(e['domain'] == domain and e['action'] == 'create-route' for e in identity['events']), 'route_identity_unknown'
                    if item['dns'] is not None and not item['dns_deleted']:
                        assert current['dns'][domain] == [item['dns']], 'dns_ownership_changed'
                        assert current['routes'][domain] is None and current['matches'][domain] is None
                        intent = event(folder, identity, 'delete-dns', domain)
                        console('/api/dns/record', 'DELETE', {'zone': ZONE, 'name': item['dns']['name'], 'type': 'A'})
                        intent['response_known'] = True; item['dns_deleted'] = True; save(folder, 'identity.json', identity)
                    else:
                        assert not current['dns'][domain], 'unexpected_dns_remaining'
                        if item['dns'] is None:
                            assert not any(e['domain'] == domain and e['action'] == 'create-dns' for e in identity['events']), 'dns_identity_unknown'
                except BaseException as error:
                    result['errors'].append({'domain': domain, **diagnostic(error)})
            project()
            result['after'] = inspect(); same_permanent(result['after'], identity['initial'])
            assert not any(result['after']['routes'].values()) and not any(result['after']['matches'].values())
            assert not any(result['after']['dns'].values()), 'temporary_objects_remaining'
            result['permanent_https'] = {name: C['public_health'](name) for name in PERMANENT}
            assert not result['errors']
            result.update(completed=True, finished_at_ns=time.time_ns())
    except BaseException as error:
        result.update(diagnostic(error))
    save(folder, 'cleaned.json', result)
    assert result['completed'], 'cleanup_not_confirmed_inspect_receipt'


def watch(folder):
    identity = load(folder)
    assert process(os.getpid()) == identity['guard']
    try:
        fd = os.pidfd_open(identity['owner']['pid'])
    except ProcessLookupError:
        clean(folder, 'owner_gone_before_ready'); return
    try:
        assert alive(identity['owner'])
        save(folder, 'ready.json', {'ready': True, 'guard': identity['guard'], 'at_ns': time.time_ns()})
        while True:
            if (folder / 'cleanup.request').exists():
                trigger = 'explicit'; break
            if select.select([fd], [], [], .1)[0] or not alive(identity['owner']):
                trigger = 'owner_gone'; break
            if time.monotonic_ns() >= identity['deadline_ns']:
                trigger = 'deadline'; break
        clean(folder, trigger)
    finally:
        os.close(fd)


def arm(owner, seconds):
    assert 15 <= seconds <= 1800 and owner != os.getpid()
    assert Path('/proc', str(owner)).stat().st_uid == os.getuid()
    owner_identity = process(owner); assert owner_identity and owner_identity['running']
    initial = inspect()
    assert initial['zone_status'] == 'active', 'initial_zone_not_active'
    assert all(row is None for row in initial['routes'].values()) and not any(initial['matches'].values())
    assert not any(initial['dns'].values()), 'temporary_name_not_free'
    for row in initial['permanent'].values():
        assert row and row['target_port'] == 18090
    BASE.mkdir(exist_ok=True)
    folder = BASE / ('invocation-pagination-domains-' + str(uuid4())); folder.mkdir(mode=0o700)
    (folder / 'mutation.lock').touch(mode=0o600)
    identity = {'owner': owner_identity, 'guard': None, 'initial': initial, 'events': [],
                'deadline_ns': time.monotonic_ns() + seconds * 1000000000,
                'objects': {name: {'dns': None, 'route': None, 'route_deleted': False, 'dns_deleted': False} for name in NAMES}}
    save(folder, 'identity.json', identity)
    with (folder / 'guard.log').open('wb') as log:
        child = subprocess.Popen([sys.executable, '-B', __file__, 'watch', '--folder', str(folder)],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    identity['guard'] = process(child.pid); assert identity['guard'] and identity['guard']['running']
    save(folder, 'identity.json', identity); (folder / 'start.request').touch(mode=0o600)
    deadline = time.monotonic() + 15
    while not (folder / 'ready.json').exists():
        assert child.poll() is None and time.monotonic() < deadline, 'guard_not_ready'
        time.sleep(.05)
    return {'folder': str(folder), 'owner': owner_identity, 'guard': identity['guard']}


def release(folder):
    (folder / 'cleanup.request').touch(mode=0o600)
    identity = load(folder); deadline = time.monotonic() + 600
    while not (folder / 'cleaned.json').exists() or alive(identity['guard']):
        assert time.monotonic() < deadline, 'cleanup_guard_termination_unconfirmed'
        time.sleep(.1)
    result = json.loads((folder / 'cleaned.json').read_text())
    assert result['completed'], 'cleanup_failed_inspect_receipt'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('arm', 'watch', 'release', 'inspect', 'create', 'remove-route'))
    parser.add_argument('--folder'); parser.add_argument('--owner', type=int)
    parser.add_argument('--seconds', type=int, default=1800); parser.add_argument('--domain', choices=NAMES)
    args = parser.parse_args()
    if args.action == 'inspect':
        result = inspect()
    elif args.action == 'arm':
        result = arm(args.owner, args.seconds)
    else:
        folder = folder_path(args.folder)
        if args.action == 'watch':
            deadline = time.monotonic() + 5
            while not (folder / 'start.request').exists():
                assert time.monotonic() < deadline
                time.sleep(.01)
            watch(folder); return
        result = release(folder) if args.action == 'release' else change(folder, args.action, args.domain)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print(json.dumps({'completed': False, **diagnostic(error)}), flush=True)
        raise SystemExit(1) from None
