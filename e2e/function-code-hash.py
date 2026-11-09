# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md#calcul-opérateur-et-preuve-réelle
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md#format-v1 | docs/FUNCTION_CODE_HASH.md#calcul-opérateur-et-preuve-réelle
"""Real packager, extracted files and runtime CLI; no service or handler replacement."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import tempfile
import time
from uuid import uuid4
import zipfile

ROOT = Path('/srv/p2enjoy-serverless')
REPORT = ROOT / 'control/function-code-hash-proof.json'
assert socket.gethostname() == 'infra-serverless' and os.getuid() == 1001, 'dev_spark_operator_required'
REPORT.parent.mkdir(parents=True, exist_ok=True)
installation = str(uuid4()); checks, observations, invocations, cleanup_errors, channels, runtime_errors = [], [], [], [], [], []
work = None; completed = False; cleanup_complete = False; counter = 0; client_counter = 0; failure = None; packages = {}; clients = []


def save():
    REPORT.write_text(json.dumps({'completed': completed and not cleanup_errors, 'cleanup': cleanup_complete and not cleanup_errors,
        'checks': checks, 'skipped': 0, 'installation': installation, 'observations': observations,
        'invocations': invocations, 'runtime_errors': runtime_errors, 'cleanup_errors': cleanup_errors, 'failure': failure,
        'channel_directories': [str(c) for c in channels],
        'clients': clients,
        'work': str(work) if work else None, 'images': globals().get('images'),
        'control_before': globals().get('control_before'), 'control_after': globals().get('control_after')}, indent=2) + '\n')


def run(args, *, input=None, timeout=90, success=True):
    value = subprocess.run(args, cwd=ROOT, input=input, text=True, capture_output=True, timeout=timeout)
    if success: assert value.returncode == 0, 'real_command_failed:' + args[0]
    return value


def docker(*args, **options):
    return run(['docker', '--host', 'unix:///run/user/1001/docker.sock', *args], **options)


def image(name):
    return docker('image', 'inspect', '--format', '{{.Id}}', name).stdout.strip()


def control():
    value = json.loads(docker('inspect', 'serverless-api').stdout)[0]
    assert value['State']['Running'] and value['State']['Health']['Status'] == 'healthy'
    return {'id': value['Id'], 'image': value['Image'], 'started': value['State']['StartedAt']}


def client(image_id, mounts, arguments, *, input=None, entrypoint=None, success=True):
    global client_counter
    client_counter += 1
    responsibility = 'serverless-code-packager' if image_id == images['adapter'] else 'serverless-code-identity'
    name = responsibility + '-' + installation[:8] + '-' + str(client_counter)
    clients.append({'name': name, 'image': image_id})
    args = ['run', '--rm', '--name', name, '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--memory', '256m', '--cpus', '1', '--pids-limit', '32', '--tmpfs', '/tmp:size=16m,mode=1777,noexec,nosuid',
            '--label', 'tech.p2enjoy.serverless.installation=' + installation,
            '--env-file', '/etc/spark/env', '--env-file', '/run/spark/secrets']
    for source, target, readonly in mounts:
        args += ['--mount', 'type=bind,src=' + str(source) + ',dst=' + target + (',readonly' if readonly else '')]
    if input is not None: args.append('-i')
    if entrypoint: args += ['--entrypoint', entrypoint]
    return docker(*args, image_id, *arguments, input=input, success=success)


def package():
    client(images['adapter'], [(project, '/project', False)], ['package', '--config', '/project/serverless.yml'])
    value = json.loads((project / '.serverless-p2/deployment.json').read_text())
    row = value['artifacts'][next(iter(manifest['functions']))]
    return project / '.serverless-p2' / row['file'], row


def calculate(archive, execution, *, raw=None, success=True, destination=None):
    global counter
    counter += 1
    spec = work / ('execution-' + str(counter) + '.json')
    spec.write_text(json.dumps(execution) if raw is None else raw)
    output = work / ('extracted-' + str(counter)); output.mkdir(mode=0o700)
    target = destination or output / 'code'
    result = client(images['hash'], [(archive.parent, '/archive', True), (spec, '/execution.json', True),
        (target.parent, '/output', False)], ['--archive', '/archive/' + archive.name, '--execution', '/execution.json',
        '--destination', '/output/' + target.name], success=success)
    value = json.loads(result.stdout)
    if success:
        assert result.returncode == 0 and len(value['code_hash']) == 64
        packages[str(target)] = value['code_hash']
        observations.append({'code_hash': value['code_hash'], 'canonical': value['canonical'], 'archive_sha256': value['extraction']['archive_sha256'], 'code_directory': str(target)})
    else:
        assert result.returncode == 1 and value == {'error': 'package_identity_rejected'}
        if destination is None: assert not target.exists(), 'rejected_extraction_published'
    return value, target


def invoke(code, execution, expected_handler='first', expected_dependency='one'):
    channel = Path(tempfile.mkdtemp(prefix='code-hash-ipc-', dir=ROOT / 'control')); channels.append(channel)
    args = ['python3', '-B', '-m', 'control.app.instances', '--image', execution['image_id'], '--code', str(code),
        '--work', str(channel), '--installation', installation, '--function-id', str(uuid4()), '--revision-id', str(uuid4()),
        '--handler', execution['handler'], '--function-name', 'code-hash-proof', '--network', 'none']
    payload = '\n'.join(json.dumps(v) for v in ({'environment': {}, 'secrets': {}}, {'operation': 'invoke', 'event': {}, 'timeout_seconds': 3}, {'operation': 'close'})) + '\n'
    process = subprocess.Popen(args, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try: stdout, stderr = process.communicate(payload, timeout=45)
    except subprocess.TimeoutExpired:
        process.terminate(); stdout, stderr = process.communicate(timeout=20); raise
    rows = [json.loads(line) for line in stdout.splitlines()]
    if process.returncode:
        runtime_errors.append({'exit_code': process.returncode, 'error_codes': [r['error'] for r in rows if 'error' in r],
            'stdout_sha256': hashlib.sha256(stdout.encode()).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest()})
    assert process.returncode == 0, 'real_runtime_cli_failed'
    assert len(rows) == 3 and rows[0]['ready'] and rows[1]['state'] == 'succeeded' and rows[2]['closed']
    response = rows[1]['response']; assert response['statusCode'] == 200
    assert json.loads(response['body']) == {'handler': expected_handler, 'dependency': expected_dependency}
    assert not list(channel.iterdir()); channel.rmdir()
    invocations.append({'container_id': rows[0]['container_id'], 'image': execution['image_id'], 'handler': execution['handler'],
        'code_directory': str(code), 'code_hash': packages[str(code)], 'result': json.loads(response['body']), 'closed': True})


def check(name, action):
    try: action(); checks.append({'name': name, 'status': 'passed'}); print('PASS', name, flush=True)
    except BaseException as error:
        checks.append({'name': name, 'status': 'failed', 'error': type(error).__name__}); raise
    finally: save()


save()
try:
    images = {'adapter': image('p2enjoy-adapter:dev'), 'hash': image('serverless-code-hash:dev'),
              'runtime': image('p2enjoy-runtime:dev'), 'other_runtime': image('p2enjoy-runtime-qualification:dev')}
    assert images['runtime'] != images['other_runtime']; control_before = control()
    work = Path(tempfile.mkdtemp(prefix='function-code-hash-', dir=ROOT / 'control')); project = work / 'project'; project.mkdir()
    for name in ('version-identity.cjs', 'version-dependency.cjs'):
        shutil.copyfile(ROOT / 'qualification/artifacts' / name, project / name)
    manifest = {'service': 'code-hash-fixture', 'provider': {'name': 'p2enjoy', 'runtime': 'node24'},
        'functions': {'hash-entry': {'handler': 'version-identity.first'}}, 'package': {'patterns': ['!**', '*.cjs', '*.txt', '*.bin']}}
    def write_manifest(): (project / 'serverless.yml').write_text(json.dumps(manifest))
    write_manifest()
    execution = {'handler': 'version-identity.first', 'runtime': 'node24', 'architecture': 'linux-x64', 'image_id': images['runtime'],
        'events': {'http': [{'path': 'hash-entry', 'implicit': True, 'methods': ['GET', 'POST']}], 'schedules': []}}
    baseline = baseline_archive = None
    def original():
        global baseline, baseline_archive
        archive, packaged = package(); baseline_archive = work / 'original.zip'; shutil.copyfile(archive, baseline_archive)
        baseline, code = calculate(archive, execution)
        payload = json.dumps({'inventory': packaged['inventory'], 'execution': execution})
        computed = client(images['hash'], [], ['-B', '-c', 'import json,sys;from function_code_hash import code_hash;v=json.load(sys.stdin);print(json.dumps(code_hash(v["inventory"],v["execution"])))'], input=payload, entrypoint='python')
        assert json.loads(computed.stdout) == {'code_hash': baseline['code_hash'], 'canonical': baseline['canonical']}
        assert baseline['extraction']['inventory'] == packaged['inventory']; invoke(code, execution)
    check('Packager réel et extracteur : même identité, code invoqué dans Docker', original)
    def recompressed():
        target = work / 'recompressed.zip'
        with zipfile.ZipFile(baseline_archive) as source, zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as dest:
            for name in reversed(source.namelist()):
                payload = source.read(name); item = copy.copy(source.getinfo(name))
                item.date_time = (2025, 4, 5, 6, 7, 8); item.compress_type = zipfile.ZIP_STORED
                dest.writestr(item, payload)
            dest.writestr('empty/', b'')
        value, code = calculate(target, execution); assert value['code_hash'] == baseline['code_hash']
        assert value['extraction']['archive_sha256'] != baseline['extraction']['archive_sha256']; invoke(code, execution)
    check('Réordre, recompression, dates et répertoire vide : hash conservé', recompressed)
    def renamed():
        manifest['functions']['renamed-entry'] = manifest['functions'].pop('hash-entry')
        manifest['provider']['environment'] = {'LABEL': 'other-configuration'}; write_manifest()
        descriptor = copy.deepcopy(execution); descriptor['events']['http'][0]['path'] = 'renamed-entry'
        value, code = calculate(package()[0], descriptor); assert value['code_hash'] == baseline['code_hash']; invoke(code, descriptor)
    check('Renommage implicite et configuration hors code : hash conservé', renamed)
    def changes():
        dependency = project / 'version-dependency.cjs'; dependency.write_text(dependency.read_text().replace("'one'", "'two'"))
        value, code = calculate(package()[0], execution); assert value['code_hash'] != baseline['code_hash']; invoke(code, execution, expected_dependency='two')
        previous = value['code_hash']; source = project / 'version-identity.cjs'; source.write_text(source.read_text() + '\n// Nouvelle source conservée.\n')
        value, code = calculate(package()[0], execution); assert value['code_hash'] != previous; invoke(code, execution, expected_dependency='two')
        previous = value['code_hash']; source.chmod(0o744)
        value, code = calculate(package()[0], execution); assert value['code_hash'] != previous; invoke(code, execution, expected_dependency='two')
    check('Dépendance, source et bit exécutable modifiés : trois nouveaux hashs', changes)
    def descriptors():
        descriptor = copy.deepcopy(execution); descriptor['handler'] = 'version-identity.second'
        value, code = calculate(baseline_archive, descriptor); assert value['code_hash'] != baseline['code_hash']; invoke(code, descriptor, expected_handler='second')
        descriptor = copy.deepcopy(execution); descriptor['events']['http'][0].update(implicit=False, path='orders/read')
        value, _ = calculate(baseline_archive, descriptor); assert value['code_hash'] != baseline['code_hash']
        descriptor = copy.deepcopy(execution); descriptor['image_id'] = images['other_runtime']
        value, code = calculate(baseline_archive, descriptor); assert value['code_hash'] != baseline['code_hash']; invoke(code, descriptor)
    check('Handler, événement explicite et vraie autre image : identité distincte', descriptors)
    def unicode_and_events():
        for name, data in [('é.txt', b'one'), ('e\u0301.txt', b'two'), ('empty.txt', b''), ('bytes.bin', bytes(range(256)))]:
            (project / name).write_bytes(data)
        value, code = calculate(package()[0], execution); assert {'é.txt', 'e\u0301.txt'}.issubset({f['path'] for f in value['canonical']['files']}); invoke(code, execution, expected_dependency='two')
        descriptor = copy.deepcopy(execution); descriptor['events']['http'] = [dict(descriptor['events']['http'][0], methods=['POST']), dict(descriptor['events']['http'][0], methods=['GET'])]
        same, _ = calculate(package()[0], descriptor); assert same['code_hash'] == value['code_hash']
        descriptor['events']['schedules'] = [{'cron': '*  * * * *', 'enabled': True, 'timezone': 'UTC'}]
        changed, _ = calculate(package()[0], descriptor); assert changed['code_hash'] != same['code_hash']
        descriptor['events']['schedules'] *= 2
        duplicated, _ = calculate(package()[0], descriptor); assert duplicated['code_hash'] == changed['code_hash']
    check('Unicode distinct, binaire, vide et normalisation des événements', unicode_and_events)
    def refusals():
        bad = work / 'truncated.zip'; bad.write_bytes(baseline_archive.read_bytes()[:-3]); calculate(bad, execution, success=False)
        for transform in (lambda v: v.update(image_id='latest'), lambda v: v.update(runtime='node99'),
                          lambda v: v.update(handler='../outside.handler'), lambda v: v.update(handler='/outside.handler'),
                          lambda v: v.update(handler='not-a-handler'),
                          lambda v: v.update(extra='forbidden'), lambda v: v['events']['http'][0].update(path='../bad'),
                          lambda v: v['events']['http'][0].update(methods=['OTHER'])):
            descriptor = copy.deepcopy(execution); transform(descriptor); calculate(baseline_archive, descriptor, success=False)
        for raw in ('{"handler":"one","handler":"two"}', '{"value":NaN}', '[]', '{}'):
            calculate(baseline_archive, execution, raw=raw, success=False)
        occupied = work / 'occupied'; occupied.mkdir(); (occupied / 'retained.txt').write_text('retained')
        calculate(baseline_archive, execution, success=False, destination=occupied)
        assert (occupied / 'retained.txt').read_text() == 'retained' and list(occupied.iterdir()) == [occupied / 'retained.txt']
    check('Vrais ZIP/descripteurs refusés et destination existante préservée', refusals)
    completed = True
except BaseException as error:
    failure = {'name': type(error).__name__}; raise
finally:
    try:
        for kind, args in [('container', ['ps', '-aq']), ('network', ['network', 'ls', '-q'])]:
            remaining = docker(*args, '--filter', 'label=tech.p2enjoy.serverless.installation=' + installation).stdout.split()
            if remaining: cleanup_errors.append({'resource': kind, 'ids': remaining})
        control_after = control(); assert control_before == control_after
        for channel in channels:
            if channel.exists():
                assert not list(channel.iterdir()), 'runtime_channel_retained'
                channel.rmdir()
        if work and not cleanup_errors:
            for folder, dirs, files in os.walk(work):
                Path(folder).chmod(0o700)
            shutil.rmtree(work); assert not work.exists()
        cleanup_complete = not cleanup_errors and all(not c.exists() for c in channels) and (work is None or not work.exists())
    except BaseException as error: cleanup_errors.append({'resource': 'native-cleanup', 'error': type(error).__name__})
    save()
    assert completed and not cleanup_errors, 'code_hash_qualification_incomplete'
