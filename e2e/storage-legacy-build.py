# @spec docs/BACKLOG.md#sls-104 | docs/STORAGE_LEGACY_PROOF.md#compatibilité-courante-et-preuves104
# @verifies docs/BACKLOG.md#sls-104 | docs/STORAGE_LEGACY_PROOF.md#compatibilité-courante-et-preuves104
# @spec docs/BACKLOG.md#sls-140 | docs/STORAGE_LEGACY_PROOF.md#attestation-courante-du-constructeur--sls-140
# @verifies docs/BACKLOG.md#sls-140 | docs/STORAGE_LEGACY_PROOF.md#attestation-courante-du-constructeur--sls-140
# @spec docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#versions-et-configuration
# @verifies docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#versions-et-configuration
"""Build the genuine pre-storage control without changing the deployed image tag."""
# @spec docs/BACKLOG.md#sls-077 | docs/GIT_HISTORY_REWRITE.md#sources-historiques-et-preuves
# @verifies docs/BACKLOG.md#sls-077 | docs/GIT_HISTORY_REWRITE.md#vérifications-requises
import hashlib
import gzip
import io
import json
from pathlib import Path
import subprocess
import tarfile
from uuid import uuid4

REVISION = '93f88e5c543be4ad41e4ca22d08cbedbabec73c5'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-J',
       'ubuntu@51.158.54.202', 'root@10.77.0.24']
ROOT = Path(__file__).resolve().parents[1]
# REVISION remains the historical attestation identity; read the rewritten Git tree.
SOURCE_REVISION='eb6cbf328d56a68f4f6f565a2cc7818b917c5c9f'


# @spec docs/BACKLOG.md#sls-140 | docs/STORAGE_LEGACY_PROOF.md#attestation-courante-du-constructeur--sls-140
# @verifies docs/BACKLOG.md#sls-140 | docs/STORAGE_LEGACY_PROOF.md#attestation-courante-du-constructeur--sls-140
def current_authorization_proof(authentication, current_auth):
    path = ROOT / 'docs/evidence/execution-journal-complete-schema011-query-dev-2026-11-23.json'
    manifest_raw = path.read_bytes()
    manifest = json.loads(manifest_raw)
    assert (manifest['completed'] and manifest['functional_groups'] == 47
            and manifest['qualified_groups'] == 47 and manifest['api_groups'] == 12
            and manifest['ui_groups'] == 10 and manifest['common_groups'] == 25), 'incomplete_current_authorization_proof'
    assert hashlib.sha256(current_auth).hexdigest() == manifest['source_sha256'][authentication], 'unattested_current_authentication'
    raw_name = manifest['raw']['path']
    assert Path(raw_name).name == raw_name, 'authorization_proof_basename_required'
    compressed = path.with_name(raw_name).read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == manifest['raw']['sha256'], 'authorization_proof_gzip_changed'
    raw = gzip.decompress(compressed)
    assert (len(raw) == manifest['raw']['uncompressed_bytes']
            and hashlib.sha256(raw).hexdigest() == manifest['raw']['uncompressed_sha256']), 'authorization_proof_raw_changed'
    phases = json.loads(raw)['phases']
    assert [phase['phase'] for phase in phases] == ['api', 'ui', 'common'], 'authorization_proof_phases_changed'
    api = phases[0]
    client = api['client']
    assert (api['bank']['before']['source_sha256'] == api['bank']['after']['source_sha256']
            == manifest['source_sha256']), 'authorization_proof_sources_changed'
    assert (api['controller']['returncode'] == 0 and api['bank']['node_exit_code'] == 0
            and client['completed'] and client['cleanup'] and client['skipped'] == 0
            and not client['cleanup_errors'] and len(client['checks']) == 12
            and all(check['status'] == 'passed' for check in client['checks'])
            and sum(check['name'].startswith('API 02 — ') for check in client['checks']) == 1), 'authorization_api_rights_unproven'
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(manifest_raw).hexdigest(),
            'raw_gzip_sha256': hashlib.sha256(compressed).hexdigest(),
            'raw_sha256': hashlib.sha256(raw).hexdigest(), 'api_groups': 12,
            'current_auth_sha256': manifest['source_sha256'][authentication]}


def main():
    output = ROOT / '.local/e2e'
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    (output / 'storage-legacy-build.json').write_text(json.dumps({'completed': False, 'revision': REVISION, 'source_revision': SOURCE_REVISION}) + '\n')
    # The old application, its frontend and dependency locks come from one Git tree.
    archive = subprocess.check_output(['git', 'archive', SOURCE_REVISION, 'control', 'web'], cwd=ROOT)
    hashes = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for item in source:
            if item.isfile():
                hashes[item.name] = hashlib.sha256(source.extractfile(item).read()).hexdigest()
    compared = ['control/requirements.txt', 'runtime/loader.mjs', 'runtime/validate-supervisor.mjs']
    identical = {}
    for name in compared:
        old = subprocess.check_output(['git', 'show', SOURCE_REVISION + ':' + name], cwd=ROOT)
        assert old == (ROOT / name).read_bytes(), 'historical_protocol_changed: ' + name
        identical[name] = hashlib.sha256(old).hexdigest()
    authentication = 'control/app/auth.py'
    authentication_reference = ROOT / 'docs/evidence/sso-session-recovery-dev-2026-11-11.json'
    reference = json.loads(authentication_reference.read_text())
    historical_auth = subprocess.check_output(['git', 'show', SOURCE_REVISION + ':' + authentication], cwd=ROOT)
    current_auth = (ROOT / authentication).read_bytes()
    assert reference['completed'], 'incomplete_historical_sso_proof'
    sso_auth = subprocess.check_output(['git', 'show', reference['source_commit'] + ':' + authentication], cwd=ROOT)
    assert hashlib.sha256(sso_auth).hexdigest() == reference['source_sha256'][authentication], 'historical_sso_proof_sources_changed'
    authorization_proof = current_authorization_proof(authentication, current_auth)
    authentication_comparison = {
        'historical_sha256': hashlib.sha256(historical_auth).hexdigest(),
        'current_sha256': hashlib.sha256(current_auth).hexdigest(),
        'byte_identical': historical_auth == current_auth,
        'current_proof': authorization_proof['path'],
        'current_proof_sha256': authorization_proof['sha256'],
        'authorization_recheck_proof': authorization_proof,
        'historical_sso_proof': str(authentication_reference.relative_to(ROOT)),
        'historical_sso_proof_sha256': hashlib.sha256(authentication_reference.read_bytes()).hexdigest(),
        'historical_sso_auth_sha256': reference['source_sha256'][authentication],
        'historical_code_unchanged': True,
        'reviewed_changes': ['pending_roles', 'id_token_azp', 'jwks_backoff', 'pending_refresh_tokens',
                             'execution_log_authorization_recheck'],
        'real_sso_upgrade_replay_required': True,
    }
    validator = 'control/app/validator.py'
    old = subprocess.check_output(['git', 'show', SOURCE_REVISION + ':' + validator], cwd=ROOT)
    current = (ROOT / validator).read_bytes()
    expected = old.replace(b'allowed=(200,201,204)):', b'allowed=(200,201,204),max_bytes=LIMIT):')
    expected = expected.replace(b"'/v1.45'+path,body,timeout)", b"'/v1.45'+path,body,timeout,max_bytes)")
    assert old.count(b"name='p2-v-'") == 1, 'historical_validator_name_changed'
    expected = expected.replace(b"name='p2-v-'", b"name='serverless-code-validator-'")
    heading = old.splitlines(keepends=True)[0]
    expected = expected.replace(heading, heading + b'# @spec docs/BACKLOG.md#sls-076 | docs/DEPLOYMENT_NAMES.md#conteneurs-de-validation | docs/VALIDATOR_NAMES.md\n', 1)
    assert current == expected, 'unexpected_historical_validator_difference'
    validator_comparison = {'historical_sha256': hashlib.sha256(old).hexdigest(),
                            'current_sha256': hashlib.sha256(current).hexdigest(),
                            'only_optional_max_bytes': False,
                            'reviewed_changes': ['optional_max_bytes', 'validator_container_name', 'validator_spec_comment']}
    folder = '/srv/p2enjoy-serverless/qualification-history/build-archive-migration-' + REVISION + '-' + uuid4().hex
    prepare = "import os,socket;from pathlib import Path;assert socket.gethostname()=='infra-serverless';p=Path(" + repr(folder) + ");p.mkdir(mode=0o755,parents=True,exist_ok=False)"
    subprocess.run(SSH + ['python3 -B -'], input=prepare, text=True, check=True, timeout=30)
    subprocess.run(SSH + ['tar --no-same-owner -xf - -C ' + folder], input=archive, check=True, timeout=30)
    remote = '''import hashlib,json,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
folder=Path(FOLDER);expected=HASHES
actual={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in expected}
assert actual==expected,'historical_source_mismatch'
docker=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def image(name):return subprocess.check_output(docker+['inspect','--format','{{.Image}}',name],text=True).strip()
original=image('serverless-api')
tag='p2enjoy-control:historical-93f88e5'
subprocess.run(docker+['build','--tag',tag,'--file',str(folder/'control/Dockerfile'),str(folder)],check=True)
built=subprocess.check_output(docker+['image','inspect','--format','{{.Id}}',tag],text=True).strip()
assert image('serverless-api')==original,'running_image_changed'
current_tag=subprocess.check_output(docker+['image','inspect','--format','{{.Id}}','p2enjoy-control:dev'],text=True).strip()
assert current_tag==original,'current_tag_changed'
print(json.dumps({'historical_image':built,'current_image':original,'current_tag_unchanged':True,'sources':actual,'source_snapshot':str(folder)}))
'''.replace('FOLDER', repr(folder)).replace('HASHES', repr(hashes))
    # Build output is retained separately; it contains no cell configuration.
    result = subprocess.run(SSH + ['python3 -B -'], input=remote, text=True,
                            capture_output=True, timeout=900)
    (output / 'storage-legacy-build.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, 'historical_build_failed; see .local/e2e/storage-legacy-build.log'
    report = json.loads(result.stdout.strip().splitlines()[-1])
    report.update(revision=REVISION, source_revision=SOURCE_REVISION, identical_protocols=identical,
                  validator_comparison=validator_comparison, authentication_comparison=authentication_comparison, completed=True)
    (output / 'storage-legacy-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('revision', 'historical_image', 'current_image', 'completed')}))


if __name__ == '__main__':
    main()
