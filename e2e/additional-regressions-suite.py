# @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md
# @verifies docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
"""Run the 32 additional current DEV campaigns, serially and without replay."""
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import time
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/e2e'
REPORT = OUTPUT / 'additional-regressions.json'
SUITE = runpy.run_path(str(ROOT / 'e2e/execution-suite.py'))
from additional_regressions_contract import namespace_from_report
EDITORS = dict(zip(('code-draft-capacity', 'code-editor', 'code-editor-ui',
    'code-editor-source-limits', 'code-editor-source-access', 'code-editor-source-lifecycle',
    'code-editor-read-concurrency', 'code-editor-build-capacity', 'code-editor-ui-concurrency',
    'code-editor-publication-continuity', 'code-editor-control-interruption',
    'code-editor-archive-boundaries'), (17, 20, 18, 13, 7, 5, 9, 4, 11, 7, 4, 7), strict=True))
TESTERS = dict(zip(('function-http-client', 'function-http-client-ui',
    'function-http-client-admission', 'function-http-client-confidentiality',
    'function-http-client-loading', 'function-http-client-recovery',
    'function-http-client-source-access', 'function-http-client-task-exception',
    'function-http-client-token-loss'), (18, 16, 5, 10, 5, 7, 7, 6, 7), strict=True))
VERSIONS = {'function-code-hash': 7, 'function-version-state-transport': 9,
    'function-version-validation': 4, 'function-version-upload-capacity': 4,
    'function-version-duplicate-recovery': 4, 'function-versions-api': 12,
    'function-versions-ui': 6, 'function-versions-cli': 5,
    'function-versions-cli-docker-cli': 5, 'function-versions-cli-docker-qualification': 5}
COUNTS = EDITORS | TESTERS | VERSIONS | {'managed-invocation-watch': 12}
assert len(COUNTS) == 32 and sum(COUNTS.values()) == 276
VISUAL_EDITORS = {'code-editor-ui', 'code-editor-ui-concurrency',
                 'code-editor-publication-continuity', 'code-editor-control-interruption'}
CAPTURE_CASES = VISUAL_EDITORS | set(TESTERS) | {'function-versions-ui'}
WRAPPERS = {'function-version-state-transport', 'function-version-upload-capacity',
            'function-version-duplicate-recovery'}
SESSION_CASES = set(VERSIONS) - {'function-code-hash', 'function-version-state-transport'}
IMAGE_ARGUMENT = {'function-http-client-loading', 'function-http-client-source-access',
                  'function-http-client-task-exception'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, value):
    pending = path.with_suffix('.pending')
    with pending.open('w') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    pending.replace(path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def local_blob(path):
    path = Path(path)
    assert path.is_absolute() and path.is_file() and not path.is_symlink()
    assert path.resolve() == path and path.is_relative_to(OUTPUT)
    return path.read_bytes(), path.stat().st_mtime_ns


def remote_blob(path, optional=False):
    # Only the DEV SPARK receives this program; FORGE is the SSH jump alone.
    program = 'path=' + repr('/srv/p2enjoy-serverless/' + path) + '\noptional=' + repr(optional) + '\n' + '''
import os,socket,sys
from pathlib import Path
assert socket.gethostname()=='infra-serverless' and os.geteuid()==0
p=Path(path)
assert str(p).startswith('/srv/p2enjoy-serverless/') and p.resolve()==p
if not p.exists():
 assert optional
else:
 assert p.is_file() and not p.is_symlink()
 sys.stdout.buffer.write(p.read_bytes())
'''
    return subprocess.check_output(SUITE['SSH'] + ['root@10.77.0.24', 'python3 -B -'],
                                   input=program.encode(), timeout=60)


class Archive:
    def __init__(self):
        self.id = uuid4().hex
        self.path = OUTPUT / ('additional-regressions-' + self.id)
        self.path.mkdir(mode=0o700)
        self.sequence = 0

    def blob(self, destination, name, raw):
        assert Path(name).name == name
        target = destination / name
        with target.open('xb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        return {'path': str(target.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}

    def wrapper_extras(self, name, destination):
        extras = {}
        suffixes = ['-checkpoint.json', '.log']
        suffixes += ['-native.log'] if name == 'function-version-state-transport' else ['-before.json', '-after.json']
        for suffix in suffixes:
            source = OUTPUT / (name + suffix)
            if not source.exists(): continue
            content, _ = local_blob(source)
            extras[source.name] = self.blob(destination, source.name, content)
        return extras

    def retain_wrapper_orphans(self, name):
        assert name in WRAPPERS
        destination = self.path / (f'{self.sequence:03d}-{name}-previous-orphans')
        destination.mkdir(mode=0o700); self.sequence += 1
        return {'path': None, 'sha256': None, 'extras': self.wrapper_extras(name, destination)}

    def retain(self, name, path, remote, stage, expected=None, window=None):
        assert name in COUNTS or name in ('dev-sso-sessions', 'additional-regressions')
        assert stage in ('previous', 'result')
        if remote:
            raw = remote_blob(path, optional=expected is None)
            if not raw:
                assert expected is None
                return None
        else:
            source = ROOT / path
            if not source.exists():
                assert expected is None
                return None
            raw, _ = local_blob(source)
        if expected is not None: assert digest(raw) == expected, 'report_changed_before_archive'
        destination = self.path / (f'{self.sequence:03d}-{name}-{stage}')
        destination.mkdir(mode=0o700); self.sequence += 1
        result = self.blob(destination, 'report.json', raw)
        value = json.loads(raw)
        result['captures'] = {}
        if stage == 'result' and name in CAPTURE_CASES and value.get('completed') is True:
            assert isinstance(value['captures'], dict)
            if name != 'function-http-client-admission': assert value['captures'], 'fresh_visual_captures_required'
        for key, declared in value.get('captures', {}).items():
            assert isinstance(declared, dict)
            source = Path(declared['path']) if name in TESTERS else OUTPUT / key
            assert source.suffix.lower() in ('.jpg', '.jpeg', '.png')
            image, mtime = local_blob(source)
            if stage == 'result':
                assert window is not None and window[0] <= mtime <= window[1], 'capture_outside_current_campaign'
            assert digest(image) == declared['sha256'], 'declared_capture_changed'
            if name in TESTERS: assert len(image) == declared['bytes']
            assert source.name not in result['captures'], 'duplicate_capture_basename'
            result['captures'][source.name] = self.blob(destination, source.name, image) | {
                'source_mtime_ns': mtime, 'logical_key': key, 'viewport': declared['viewport']}
        result['extras'] = {}
        if name in WRAPPERS:
            result['extras'] = self.wrapper_extras(name, destination)
        if name == 'managed-invocation-watch':
            for channel, declared in value.get('transport', {}).items():
                assert channel in ('stdout', 'stderr')
                installation = str(UUID(value['installation_id']))
                expected_path = '/srv/p2enjoy-serverless/runtime/invocation-watch-transport-' + UUID(installation).hex + '/' + channel
                assert declared['path'] == expected_path
                content = remote_blob(expected_path.removeprefix('/srv/p2enjoy-serverless/'))
                assert len(content) == declared['bytes'] and digest(content) == declared['sha256']
                result['extras'][channel] = self.blob(destination, channel, content)
        return result

    def prepare_wrapper(self, name, previous):
        """Move only the exact owned inputs already retained; never erase a proof."""
        assert name in WRAPPERS
        suffixes = ['.json', '-checkpoint.json', '.log', '-native.log'] if name == 'function-version-state-transport' else ['.json', '-checkpoint.json', '.log', '-before.json', '-after.json']
        paths = [OUTPUT / (name + suffix) for suffix in suffixes]
        if not any(p.exists() for p in paths): return
        destination = self.path / ('prior-wrapper-inputs-' + name)
        destination.mkdir(mode=0o700)
        for path in paths:
            if not path.exists(): continue
            raw, _ = local_blob(path)
            if path.name == name + '.json':
                assert previous and previous['sha256'] == digest(raw)
            else:
                assert previous and previous['extras'][path.name]['sha256'] == digest(raw)
            path.rename(destination / path.name)


def candidates(name):
    pattern = re.compile(re.escape(name) + r'-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.json')
    return {p for p in OUTPUT.glob(name + '-*.json') if pattern.fullmatch(p.name)}


def uuid(value):
    assert isinstance(value, str) and str(UUID(value)) == value
    return value


def verify(name, value):
    assert value['completed'] is True and value['skipped'] == 0
    assert len(value['checks']) == COUNTS[name]
    assert all(isinstance(v['name'], str) and v['name'] and v['status'] == 'passed' for v in value['checks'])
    assert value['cleanup_errors'] == []
    if name in EDITORS or name in TESTERS or name in ('function-code-hash', 'managed-invocation-watch'):
        assert value['failure'] is None
    if name == 'function-version-state-transport':
        assert not any(v.get('scenario') == 'campaign-error' for v in value['evidence'])
    if name in EDITORS or name in TESTERS:
        uuid(value['campaign']); uuid(value['namespace_id'])
        ids = value['function_ids']
        if name == 'code-editor-ui': assert value['cleanup'] is True
        else: assert 'cleanup' not in value
        if name in VISUAL_EDITORS: assert value['faults'] == []
        return {value['namespace_id']: unique_ids(ids)}
    assert value['cleanup'] is True
    if name == 'function-code-hash':
        uuid(value['installation']); assert value['runtime_errors'] == []
        return None
    if name == 'managed-invocation-watch':
        uuid(value['installation_id']); unique_ids(value['functions'])
        assert value['worker_exit_code'] == 0 and value['worker_joined'] is True
        assert value['script_removed'] is True and value['script_retained_for_reconciliation'] is False
        assert value['parent_failure'] is None and value['join_failure'] is None
        assert set(value['transport']) == {'stdout', 'stderr'}
        return None
    if name in ('function-version-validation', 'function-version-upload-capacity', 'function-version-duplicate-recovery'):
        assert value['request_join_errors'] == []
    if name == 'function-versions-ui': assert value['faults'] == []
    if name.startswith('function-versions-cli'):
        assert value['execution'] == {'function-versions-cli': 'host-python',
            'function-versions-cli-docker-cli': 'docker-cli',
            'function-versions-cli-docker-qualification': 'docker-qualification'}[name]
    uuid(value['namespace_id'])
    ids = [value['function_id']] if name in ('function-version-state-transport', 'function-versions-ui') else value['function_ids']
    return {value['namespace_id']: unique_ids(ids)}


def unique_ids(ids):
    assert isinstance(ids, list) and ids and len(ids) == len(set(ids))
    return [uuid(v) for v in ids]


def command_for(name, image):
    if name == 'function-code-hash':
        return SUITE['remote'](['bash', SUITE['REMOTE'] + 'control/code-hash-dev.sh', 'test']), 'control/function-code-hash-proof.json', True
    if name == 'managed-invocation-watch':
        return SUITE['remote'](['python3', '-B', SUITE['REMOTE'] + 'e2e/managed-invocation-watch.py'], 'root'), 'runtime/managed-invocation-watch-proof.json', True
    if name in WRAPPERS:
        return [sys.executable, '-B', 'e2e/' + name + '-run.py', '--target-schema011'], '.local/e2e/' + name + '.json', False
    args = ['node', 'e2e/' + ('function-versions-cli' if name.startswith('function-versions-cli') else name) + '.mjs']
    if name in IMAGE_ARGUMENT: args.append(image)
    if name.startswith('function-versions-cli-docker-'): args += ['--docker', name.removeprefix('function-versions-cli-docker-')]
    return args, '.local/e2e/' + name + '.json', False


def main():
    assert sys.argv[1:] == [], 'no_partial_suite_or_automatic_replay'
    os.chdir(ROOT); os.umask(0o077)
    assert not subprocess.check_output(['git', 'status', '--porcelain']), 'committed_clean_sources_required'
    OUTPUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    archive = Archive()
    previous_suite = archive.retain('additional-regressions', str(REPORT.relative_to(ROOT)), False, 'previous')
    baseline = SUITE['snapshot'](str(REPORT.relative_to(ROOT)), False, include_adapter=True)
    native_baseline = SUITE['native_state']()
    report = {'completed': False, 'serial': True, 'scope': 'additional-schema011',
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'run_id': archive.id, 'archive_path': str(archive.path.relative_to(ROOT)),
        'before': baseline, 'native_baseline': native_baseline, 'previous_suite': previous_suite,
        'commands': [], 'prerequisites': [], 'worker_preparations': [], 'failure': None}
    def save(): atomic(REPORT, report)
    def same_sources(state):
        for key in ('image', 'source_sha256', 'adapter_images'):
            assert state[key] == baseline[key], 'additional_suite_identity_changed:' + key
    save()
    credentials = SUITE['private_credentials']()
    owned_namespaces, owned_functions = set(), set()
    try:
        for name in COUNTS:
            before_native = SUITE['native_state'](); SUITE['same_installation'](native_baseline, before_native)
            # @spec docs/BACKLOG.md#sls-147 | docs/SCHEMA_011_REGRESSIONS.md#préparation-des-workers--sls-147
            if name == 'code-editor-read-concurrency':
                preparer = runpy.run_path(str(ROOT / 'e2e/prepare-editor-worker-control.py'))
                path = preparer['prepare']()
                raw = (ROOT / path).read_bytes(); preparation = json.loads(raw)
                assert preparation['completed'] and preparation['failure'] is None and not preparation['secondary_errors']
                assert preparation['source_commit'] == report['source_commit'] and preparation['exit_code'] == 0
                before_native = SUITE['native_state'](); SUITE['same_installation'](native_baseline, before_native)
                assert before_native['services'] == preparation['native_after']['services']
                report['worker_preparations'].append({'campaign': name, 'path': path,
                    'sha256': digest(raw), 'bytes': len(raw), 'groups_added': 0})
                save()
            if name in SESSION_CASES:
                path = '.local/e2e/dev-sso-sessions.json'
                prior = archive.retain('dev-sso-sessions', path, False, 'previous')
                before = SUITE['snapshot'](path, False, include_adapter=True); same_sources(before)
                row = {'campaign': 'dev-sso-before-' + name, 'previous_report': prior, 'before': before}
                report['prerequisites'].append(row); save()
                with (archive.path / ('sso-before-' + name + '.log')).open('xb') as stream:
                    process = subprocess.run(['node', 'e2e/dev-sso-sessions.mjs'], input=credentials, stdout=stream, stderr=subprocess.STDOUT)
                after = SUITE['snapshot'](path, False, include_adapter=True)
                row.update(exit_code=process.returncode, after=after,
                    report_archive=archive.retain('dev-sso-sessions', path, False, 'result', after['report']['sha256'])); save()
                same_sources(after)
                assert before['report']['sampled_at_ns'] <= after['report']['mtime_ns'] <= after['report']['sampled_at_ns']
                value = SUITE['read_report'](path, False, after['report']['sha256'])
                assert process.returncode == 0 and value['completed'] is True and value['authenticated'] is True
                assert value['independent_sessions'] == 2 and value['platform_cookies_only'] is True and value['purpose'] == 'suite-start'
                row['fresh_report_verified'] = True; save()
            command, path, remote = command_for(name, baseline['image'])
            dynamic = name in EDITORS or name in TESTERS
            existing = candidates(name) if dynamic else None
            previous = None if dynamic else archive.retain(name, path, remote, 'previous')
            if name in WRAPPERS:
                if previous is None: previous = archive.retain_wrapper_orphans(name)
                archive.prepare_wrapper(name, previous)
            if dynamic: path = str((archive.path / (name + '-awaiting.json')).relative_to(ROOT))
            before = SUITE['snapshot'](path, remote, include_adapter=True); same_sources(before)
            row = {'campaign': name, 'command': command, 'report_path': path, 'report_remote': remote,
                'before': before, 'native_before': before_native, 'previous_report': previous,
                'started_at_ns': time.time_ns(), 'exit_code': None}
            report['commands'].append(row); save()
            print(json.dumps({'campaign': name, 'state': 'running'}), flush=True)
            private_input = credentials if name in EDITORS or name in TESTERS or name == 'function-version-state-transport' else None
            with (archive.path / (name + '.log')).open('xb') as stream:
                options = {'input': private_input} if private_input is not None else {'stdin': subprocess.DEVNULL}
                process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, **options)
            row.update(exit_code=process.returncode, finished_at_ns=time.time_ns()); save()
            if dynamic:
                added = candidates(name) - existing
                assert len(added) == 1, 'exactly_one_fresh_client_report_required:' + name
                path = str(added.pop().relative_to(ROOT)); row['report_path'] = path
            after = SUITE['snapshot'](path, remote, include_adapter=True)
            row.update(after=after, report_archive=archive.retain(name, path, remote, 'result', after['report']['sha256'],
                window=(row['started_at_ns'], row['finished_at_ns']))); save()
            assert process.returncode == 0, 'nonzero_client_exit:' + name
            same_sources(after)
            assert before['report']['sampled_at_ns'] <= after['report']['mtime_ns'] <= after['report']['sampled_at_ns'], 'fresh_report_required'
            value = SUITE['read_report'](path, remote, after['report']['sha256'])
            mapping = verify(name, value)
            if dynamic: assert Path(path).name == name + '-' + value['campaign'] + '.json'
            if name in WRAPPERS:
                checkpoint = OUTPUT / (name + '-checkpoint.json')
                wrapped = json.loads(checkpoint.read_bytes())
                assert checkpoint.stat().st_mtime_ns >= row['started_at_ns'] and wrapped['completed'] is True and wrapped['exit_code'] == 0
                assert wrapped['report'] == value and wrapped['native']['completed'] is True
                extras = row['report_archive']['extras']
                assert extras[name + '.log']['sha256'] == wrapped['log_sha256']
                if name != 'function-version-state-transport':
                    for suffix, key in (('-before.json', 'before'), ('-after.json', 'after')):
                        assert json.loads((ROOT / extras[name + suffix]['path']).read_bytes()) == wrapped[key]
                for key in ('image', 'source_sha256', 'adapter_images'):
                    assert wrapped['before'][key] == baseline[key] == wrapped['after'][key]
            expected_namespace = None
            if mapping:
                namespace, functions = next(iter(mapping.items()))
                assert namespace not in owned_namespaces and owned_functions.isdisjoint(functions), 'campaign_ids_reused'
                expected_namespace = namespace_from_report(name, value, functions)
                row['namespace_name'] = expected_namespace
                owned_namespaces.add(namespace); owned_functions.update(functions)
            after_native = SUITE['native_state'](mapping, additional_client=name if mapping else None,
                additional_namespace=expected_namespace)
            SUITE['same_installation'](native_baseline, after_native)
            if mapping: assert after_native['physical']['completed'] is True
            row.update(native_after=after_native, passed_groups=COUNTS[name], fresh_report_verified=True); save()
        assert len(report['commands']) == 32 and sum(v['passed_groups'] for v in report['commands']) == 276
        assert len(owned_namespaces) == 30 and len(owned_functions) == 74
        assert len(report['prerequisites']) == 8 and all(v['fresh_report_verified'] for v in report['prerequisites'])
        report['native_after'] = SUITE['native_state']()
        SUITE['same_installation'](native_baseline, report['native_after'])
        report['completed'] = True; save()
    except BaseException as error:
        report['failure'] = {'type': type(error).__name__, 'at_ns': time.time_ns()}; save()
        raise
    finally:
        credentials = None


if __name__ == '__main__': main()
