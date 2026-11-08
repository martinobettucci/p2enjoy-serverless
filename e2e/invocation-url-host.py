# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#preuve-native-du-host-et-des-clients-de-panne
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#preuve-native-du-host-et-des-clients-de-panne
"""Operator HTTP client of the real DEV control; credentials only on stdin."""
import http.client
import json
import os
import socket
import subprocess
import sys
from urllib.parse import urlencode, urlsplit
from uuid import UUID


def main():
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    value = json.loads(sys.stdin.readline(8194))
    key = str(UUID(value['function_id'])); token = value['token']
    assert key == value['function_id'] and isinstance(token, str) and 0 < len(token) <= 4096
    assert all(33 <= ord(c) <= 126 for c in token), 'invalid_private_token'
    docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix:///run/user/1001/docker.sock']

    def inspect():
        row = json.loads(subprocess.check_output(docker + ['inspect', 'serverless-api'], timeout=30))[0]
        assert row['State']['Running'] and row['State']['Health']['Status'] == 'healthy'
        assert row['HostConfig']['NetworkMode'] == 'host'
        assert any(m['Source'] == '/etc/spark' and m['Destination'] == '/spark' and not m['RW'] for m in row['Mounts'])
        return row['Id'], row['Image']

    before = inspect()
    # Only the public origin is read. No environment/secrets inventory is emitted.
    origin = subprocess.check_output(docker + ['exec', 'serverless-api', 'python', '-B', '-c',
        'import os;print(os.environ["SERVERLESS_PUBLIC_URL"])'], text=True, timeout=30).strip().rstrip('/')
    parsed = urlsplit(origin)
    assert parsed.scheme == 'https' and parsed.netloc and not parsed.path

    def get(path, host, authenticated=False):
        connection = http.client.HTTPConnection('127.0.0.1', 18090, timeout=30)
        try:
            headers = {'Host': host, 'Accept': 'application/json', 'X-Forwarded-Host': 'forwarded.invalid',
                       'X-Forwarded-Port': '18091'}
            if authenticated: headers['X-Serverless-Token'] = token
            connection.request('GET', path, headers=headers)
            response = connection.getresponse(); raw = response.read(1024 * 1024 + 1)
            assert len(raw) <= 1024 * 1024 and token.encode() not in raw
            return response.status, {name.lower(): value for name, value in response.getheaders()}, raw
        finally:
            connection.close()

    path = '/api/functions/' + key + '/invocation-urls?limit=20'
    status, _, body = get(path, 'untrusted.invalid:18091', True)
    assert status == 200
    catalogue = json.loads(body)
    assert catalogue['function_id'] == key and catalogue['source']['state'] == 'available'
    status, _, body = get(path, parsed.netloc, True)
    assert status == 200
    canonical = json.loads(body)
    assert catalogue['items'] == canonical['items'] and catalogue['source']['sha256'] == canonical['source']['sha256']
    assert catalogue['console_url'] == origin + '/console/functions/' + key + '/invocation-urls'
    assert get(path, 'untrusted.invalid')[0] == 401
    checks = [('/', origin + '/'), ('/auth/login?return_to=https://untrusted.invalid', origin + '/auth/login')]
    console = '/console/functions/' + key + '/code'
    query = urlencode({'deployment': key, 'operation': key, 'return_to': 'https://untrusted.invalid'})
    expected = urlencode({'deployment': key, 'operation': key})
    checks.append((console + '?' + query, origin + console + '?' + expected))
    checks.append((console + '?' + urlencode({f'field{i}': 'x' for i in range(33)}), origin + console))
    redirects = []
    for source, target in checks:
        status, headers, _ = get(source, 'untrusted.invalid:18091')
        assert status == 303 and headers.get('location') == target and 'set-cookie' not in headers
        redirects.append({'path': source, 'status': status, 'location': target, 'flow_cookie_created': False})
    assert inspect() == before, 'control_replaced_during_probe'
    print(json.dumps({'completed': True, 'transport': 'native-loopback-http', 'control_image': before[1],
                      'catalogue': catalogue, 'redirects': redirects, 'anonymous_status': 401}))


if __name__ == '__main__':
    try: main()
    except Exception:
        # Input includes a real scoped token: never emit exception text or buffers.
        print('invocation_url_native_host_failed', file=sys.stderr)
        sys.exit(1)
