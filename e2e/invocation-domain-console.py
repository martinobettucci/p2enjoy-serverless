# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-normale-et-mise-en-service-de-lalias-autorisé
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#qualification-réelle-et-autorité
"""Operate the existing normal console for the one explicitly authorized alias.

This client never edits an infrastructure registry, reads credentials, replaces
DNS answers or disables TLS. A lost mutation response requires operator review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = 'http://127.0.0.1:5175'
SERVER = 'spark-experiment'
SPARK = 'infra-serverless'
SPARK_ID = '77dd528d87a0b1edcdad87ad'
CANONICAL = 'serverless.lelabs.tech'
ALIAS = 'functions.lelabs.tech'
PUBLIC_IP = '51.158.54.202'
REPORT = ROOT / '.local/e2e/invocation-domain-installation.json'


def console(path, method='GET', body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {'Content-Type': 'application/json'} if method != 'GET' else {}
    request = urllib.request.Request(CONSOLE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read(1024 * 1024 + 1)
            assert len(raw) <= 1024 * 1024, 'console_response_limit'
            assert response.status in (200, 201, 202), 'console_status'
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        raise RuntimeError('console_http_' + str(error.code)) from None
    except urllib.error.URLError:
        raise RuntimeError('console_transport_unknown') from None


def api(path, method='GET', body=None):
    separator = '&' if '?' in path else '?'
    return console('/api/v1' + path + separator + 'server=' + SERVER, method, body)


def route_view(row):
    return {key: row.get(key) for key in ('id', 'domain', 'spark_id', 'spark_name',
            'ipv4_address', 'target_port', 'tls', 'enabled', 'applied_at')}


def route_configuration(row):
    return {key: value for key, value in row.items() if key != 'applied_at'}


def inspect():
    servers = console('/api/servers')
    server = next(row for row in servers['servers'] if row['name'] == SERVER)
    assert servers['current'] == SERVER and server['host'] == PUBLIC_IP and server['port'] == 22
    spark = api('/sparks/' + SPARK)
    assert spark['id'] == SPARK_ID and spark['ipv4_address'] == '10.77.0.24'
    assert spark['name'] == SPARK and spark['runtime'] == 'container' and not spark['protected']
    matches = api('/ingress/match', 'POST', {'domains': [CANONICAL, ALIAS]})['matches']
    assert matches[CANONICAL] == {'domain': CANONICAL, 'spark_name': SPARK}
    assert matches[ALIAS] in (None, {'domain': ALIAS, 'spark_name': SPARK}), 'alias_owned_elsewhere'
    routes = api('/ingress')['routes']
    canonical = next(row for row in routes if row['domain'] == CANONICAL)
    assert canonical['id'] == '2aedd847cd94ddf80ee9aa89'
    assert canonical['spark_id'] == SPARK_ID and canonical['target_port'] == 18090
    assert canonical['tls'] == 1 and canonical['enabled'] == 1
    alias = next((row for row in routes if row['domain'] == ALIAS), None)
    if alias:
        assert alias['spark_id'] == SPARK_ID and alias['target_port'] == 18090
        assert alias['tls'] == 1 and alias['enabled'] == 1
    zones = console('/api/dns/zones')
    assert zones.get('configured') is True
    assert any(row['zone'] == 'lelabs.tech' and row['status'] == 'active' for row in zones['zones'])
    preview = console('/api/dns/preview', 'POST',
                      {'domain': ALIAS, 'zone': 'lelabs.tech', 'address': PUBLIC_IP})
    assert all(preview[key] == value for key, value in
               {'zone': 'lelabs.tech', 'name': 'functions', 'type': 'A',
                'data': PUBLIC_IP, 'ttl': 300, 'apex': False}.items())
    # The console exposes only this exact A record in the preview; never overwrite a conflict.
    current = preview['current']
    if current is not None:
        assert current['data'] == PUBLIC_IP, 'dns_value_conflict'
    return {'spark': {'id': SPARK_ID, 'name': SPARK, 'ipv4_address': '10.77.0.24'},
            'server': {'name': SERVER, 'host': PUBLIC_IP, 'port': 22},
            'canonical': route_view(canonical), 'alias': route_view(alias) if alias else None,
            'dns_preview': preview}


def save(value):
    REPORT.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = REPORT.with_suffix('.pending')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(REPORT)


def public_health(domain):
    with urllib.request.urlopen('https://' + domain + '/healthz', timeout=15) as response:
        raw = response.read(4096)
        assert response.status == 200 and response.url == 'https://' + domain + '/healthz'
        assert json.loads(raw)['status'] == 'ok'
        assert json.loads(raw)['component'] == 'control'
        return {'url': response.url, 'status': 200, 'tls_verified': True,
                'body_sha256': hashlib.sha256(raw).hexdigest()}


def await_https(domain):
    deadline = time.monotonic() + 360
    while True:
        try:
            return public_health(domain)
        except (urllib.error.URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise RuntimeError('verified_https_not_ready') from None
            print(json.dumps({'stage': 'waiting_verified_https', 'domain': domain}), flush=True)
            time.sleep(5)


def verify_installed():
    previous_raw = REPORT.read_bytes()
    previous = json.loads(previous_raw)
    assert previous['stage'] == 'route_declared' and previous['completed'] is False
    assert previous['official_projection_cell_read'] is True
    assert previous['before']['alias'] is None and previous['after']['alias'] is not None
    current = inspect()
    assert route_configuration(current['canonical']) == route_configuration(previous['before']['canonical'])
    assert route_configuration(current['alias']) == route_configuration(previous['after']['alias'])
    assert current['dns_preview']['effet'] == 'inchange'
    assert current['dns_preview']['current'] == previous['after']['dns_preview']['current']
    addresses = sorted({row[4][0] for row in socket.getaddrinfo(ALIAS, 443, type=socket.SOCK_STREAM)})
    assert addresses == [PUBLIC_IP]
    result = {'completed': False, 'read_only': True, 'mutation_count': 0,
              'initial_attempt_sha256': hashlib.sha256(previous_raw).hexdigest(),
              'initial_attempt_still_incomplete': True, 'started_at_ns': time.time_ns(),
              'configuration': current, 'native_dns': addresses}
    target = REPORT.with_name('invocation-domain-verification.json')
    assert not target.exists(), 'existing_verification_receipt_requires_inspection'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    result['alias_https'] = await_https(ALIAS)
    result['canonical_https'] = await_https(CANONICAL)
    assert REPORT.read_bytes() == previous_raw, 'original_attempt_changed'
    result.update(completed=True, finished_at_ns=time.time_ns())
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'completed': True, 'read_only': True, 'mutation_count': 0,
                      'alias': ALIAS, 'tls_verified': True}))


def apply():
    assert not REPORT.exists(), 'existing_receipt_requires_inspection_not_automatic_mutation_retry'
    result = {'completed': False, 'target': SPARK, 'started_at_ns': time.time_ns(),
              'canonical_route_mutated': False, 'mutation_retries': 0, 'events': []}
    save(result)
    try:
        before = inspect()
        result['before'] = before
        assert before['alias'] is None, 'alias_already_exists_use_inspect'
        assert before['dns_preview']['current'] is None, 'dns_already_exists_use_inspect'
        result['stage'] = 'dns_write_response_unknown_until_return'
        save(result)
        written = console('/api/dns/record', 'POST',
                          {'domain': ALIAS, 'zone': 'lelabs.tech', 'address': PUBLIC_IP})
        # Whitelist only ordinary record metadata; no provider or configuration object is retained.
        result['dns_write'] = {k: written[k] for k in
                               ('zone', 'name', 'type', 'data', 'ttl', 'action', 'effect', 'effet') if k in written}
        result['stage'] = 'dns_written'
        save(result)
        deadline = time.monotonic() + 360
        while True:
            try:
                addresses = sorted({row[4][0] for row in socket.getaddrinfo(ALIAS, 443, type=socket.SOCK_STREAM)})
                assert addresses == [PUBLIC_IP], 'dns_destination_conflict'
                break
            except socket.gaierror:
                if time.monotonic() >= deadline:
                    raise RuntimeError('native_dns_not_ready') from None
                print(json.dumps({'stage': 'waiting_native_dns'}), flush=True)
                time.sleep(5)
        result['native_dns'] = {'domain': ALIAS, 'addresses': addresses, 'observed_at_ns': time.time_ns()}
        fresh = inspect()
        assert fresh['alias'] is None and route_configuration(fresh['canonical']) == route_configuration(before['canonical'])
        result['stage'] = 'route_write_response_unknown_until_return'
        save(result)
        api('/ingress', 'POST', {'spark': SPARK, 'domain': ALIAS, 'port': 18090, 'tls': True})
        result['stage'] = 'route_declared'
        save(result)
        projected = api('/sparks/' + SPARK + '/suggestions')
        assert projected.get('cell_read') is True, 'official_projection_unavailable'
        result['official_projection_cell_read'] = True
        del projected
        result['after'] = inspect()
        assert result['after']['alias'] is not None
        assert route_configuration(result['after']['canonical']) == route_configuration(before['canonical']), 'canonical_changed'
        save(result)
        result['alias_https'] = await_https(ALIAS)
        result['canonical_https'] = await_https(CANONICAL)
        result.update(completed=True, stage='ready', finished_at_ns=time.time_ns())
        save(result)
        print(json.dumps({'completed': True, 'alias': ALIAS, 'port': 18090,
                          'tls_verified': True, 'canonical_route_mutated': False}))
    except BaseException as error:
        result['failure_type'] = type(error).__name__
        result['automatic_mutation_retry_forbidden'] = True
        save(result)
        raise RuntimeError('alias_installation_incomplete_inspect_receipt_and_normal_console') from None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'apply-authorized-alias', 'verify-installed-alias'))
    args = parser.parse_args()
    if args.action == 'inspect':
        print(json.dumps(inspect(), ensure_ascii=False))
    elif args.action == 'verify-installed-alias':
        verify_installed()
    else:
        apply()
