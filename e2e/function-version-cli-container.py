# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#cli-conteneurisée-authentifiée
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
"""Run one genuine adapter command in its DEV image; private input is stdin only."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
from uuid import uuid4

MAX_INPUT = 2 * 1024 * 1024
DOCKER = ['docker', '--host', 'unix:///run/user/1001/docker.sock']
STAGE = 'startup'
IMAGES = {'cli': 'p2enjoy-adapter:dev', 'qualification': 'p2enjoy-adapter-e2e:dev'}

# This independent process lives inside Docker: loss of the SSH helper cannot
# remove its CLI deadline. It never imports a handler or replaces an HTTP call.
RUNNER = r'''
import hashlib,json,os,signal,subprocess,sys
from pathlib import Path
def expired(*_): raise TimeoutError('container_deadline')
signal.signal(signal.SIGALRM,expired);signal.alarm(180)
stage='private-input'
try:
 payload=json.loads(sys.stdin.buffer.read(2*1024*1024+1))
 stage='embedded-modules'
 modules={str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/adapter').glob('*.py')}
 modules['function_code_hash.py']=hashlib.sha256(Path('/app/function_code_hash.py').read_bytes()).hexdigest()
 assert modules==payload['modules'],'embedded_cli_sources_mismatch'
 stage='project-files'
 project=Path('/tmp/serverless-cli-project');project.mkdir(mode=0o700)
 files={}
 for name,text in payload['files'].items():
  assert name in ('serverless.yml','function-versions.cjs','version-marker.json')
  data=text.encode();p=project/name;p.write_bytes(data);p.chmod(0o600)
  files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 stage='official-origin'
 env=dict(os.environ);assert env['SERVERLESS_PUBLIC_URL']==payload['target']
 env.update(P2_SERVERLESS_URL=env['SERVERLESS_PUBLIC_URL'],P2_SERVERLESS_TOKEN=payload['token'],QUALIFICATION_SYNTHETIC_SECRET=payload['secret'])
 env.pop('UNRESOLVED_VERSION_PILOT_VALUE',None)
 stage='cli-process'
 result=subprocess.run([sys.executable,'-B','-m','adapter',*payload['args']],cwd='/app',env=env,capture_output=True,text=True,timeout=150)
 stage='private-output'
 assert len(result.stdout.encode())+len(result.stderr.encode())<=4*1024*1024,'cli_output_limit'
 assert all(value not in result.stdout and value not in result.stderr for value in (payload['token'],payload['secret'])),'cli_private_output'
 print(json.dumps({'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'modules':modules,'files':files,'python':sys.version.split()[0]}))
except BaseException as error:
 print(json.dumps({'protocol_error':type(error).__name__,'stage':stage}));sys.exit(2)
'''


def docker(*args, timeout=25):
    return subprocess.run(DOCKER + list(args), capture_output=True, text=True, timeout=timeout)


def interrupted(*_):
    raise TimeoutError('helper_deadline_or_signal')


def main():
    global STAGE
    STAGE = 'identity'
    assert socket.gethostname() == 'infra-serverless' and os.getuid() == 1001
    assert len(sys.argv) == 2 and sys.argv[1] in IMAGES
    STAGE = 'private-input'
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    assert len(raw) <= MAX_INPUT
    payload = json.loads(raw)
    assert set(payload) == {'args', 'target', 'token', 'secret', 'files', 'modules'}
    assert payload['target'] == 'https://serverless.lelabs.tech'
    assert all(isinstance(payload[k], str) and 1 <= len(payload[k]) <= 8192 for k in ('token', 'secret'))
    assert isinstance(payload['args'], list) and 1 <= len(payload['args']) <= 8
    assert all(isinstance(v, str) and len(v) <= 512 for v in payload['args'])
    assert payload['args'][0] in ('deploy', 'promote')
    assert set(payload['files']) == {'serverless.yml', 'function-versions.cjs', 'version-marker.json'}
    assert all(isinstance(v, str) for v in payload['files'].values())
    STAGE = 'image-inspection'
    inspected = docker('image', 'inspect', '--format', '{{.Id}}', IMAGES[sys.argv[1]])
    assert inspected.returncode == 0
    image = inspected.stdout.strip()
    assert image.startswith('sha256:') and len(image) == 71
    name = 'serverless-cli-version-command-' + uuid4().hex
    with tempfile.TemporaryDirectory(prefix='serverless-cli-compose-') as folder:
        definition = Path(folder) / 'compose.json'
        definition.write_text(json.dumps({'name': 'p2enjoy-cli-version-proof', 'services': {
            'cli-command': {'profiles': ['dev'], 'image': image,
                'env_file': ['/etc/spark/env', '/run/spark/secrets'],
                'labels': {'tech.p2enjoy.serverless.purpose': 'function-version-cli-proof'},
                'network_mode': 'bridge', 'read_only': True,
                'tmpfs': ['/tmp:size=128m,mode=1777,noexec,nosuid'],
                'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges:true'],
                'mem_limit': '256m', 'cpus': 1, 'pids_limit': 32}}}))
        definition.chmod(0o600)
        command = DOCKER + ['compose', '-f', str(definition), '--profile', 'dev',
            'run', '--rm', '--no-deps', '-T', '--name', name,
            '--entrypoint', 'python', 'cli-command', '-B', '-c', RUNNER]
        process = None
        try:
            signal.signal(signal.SIGALRM, interrupted)
            for event in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                signal.signal(event, interrupted)
            signal.alarm(210)
            STAGE = 'container-process'
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(raw.decode(), timeout=200)
            assert len(stdout.encode()) + len(stderr.encode()) <= 5 * 1024 * 1024
            assert all(value not in stdout and value not in stderr for value in (payload['token'], payload['secret']))
            STAGE = 'container-protocol'
            result = json.loads(stdout)
            if process.returncode != 0 or 'protocol_error' in result:
                inner = result.get('stage', 'unknown')
                assert inner in ('private-input', 'embedded-modules', 'project-files', 'official-origin', 'cli-process', 'private-output', 'unknown')
                STAGE = 'container-' + inner
                raise RuntimeError('container_cli_protocol_failed')
            result['compose_stderr'] = {'bytes': len(stderr.encode()), 'sha256': hashlib.sha256(stderr.encode()).hexdigest()}
        finally:
            signal.alarm(0)
            if process is not None and process.poll() is None:
                removed = docker('rm', '-f', '-v', name)
                process.communicate(timeout=25)
                assert removed.returncode == 0, 'owned_container_cleanup_failed'
            # Absence requires a successful inventory, not an inspect error.
            inventory = docker('ps', '-aq', '--filter', 'name=^/' + name + '$')
            assert inventory.returncode == 0, 'owned_container_inventory_failed'
            if inventory.stdout.strip():
                removed = docker('rm', '-f', '-v', name)
                assert removed.returncode == 0, 'owned_container_cleanup_failed'
                inventory = docker('ps', '-aq', '--filter', 'name=^/' + name + '$')
            assert inventory.returncode == 0 and not inventory.stdout.strip(), 'owned_container_retained'
    assert not Path(folder).exists()
    print(json.dumps({**result, 'image': image, 'container_name': name, 'container_absent': True, 'compose_definition_absent': True}))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print(json.dumps({'protocol_error': type(error).__name__, 'stage': STAGE}))
        sys.exit(2)
