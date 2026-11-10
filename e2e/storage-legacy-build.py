# @spec docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#versions-et-configuration
# @verifies docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#versions-et-configuration
"""Build the genuine pre-storage control without changing the deployed image tag."""
# @spec docs/BACKLOG.md#sls-077 | docs/GIT_HISTORY_REWRITE.md#sources-historiques-et-preuves
# @verifies docs/BACKLOG.md#sls-077 | docs/GIT_HISTORY_REWRITE.md#vérifications-requises
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

REVISION = '93f88e5c543be4ad41e4ca22d08cbedbabec73c5'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-J',
       'ubuntu@51.158.54.202', 'root@10.77.0.24']
ROOT = Path(__file__).resolve().parents[1]
# REVISION remains the historical attestation identity; read the rewritten Git tree.
SOURCE_REVISION='eb6cbf328d56a68f4f6f565a2cc7818b917c5c9f'


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
    compared = ['control/requirements.txt', 'control/app/auth.py',
                'runtime/loader.mjs', 'runtime/validate-supervisor.mjs']
    identical = {}
    for name in compared:
        old = subprocess.check_output(['git', 'show', SOURCE_REVISION + ':' + name], cwd=ROOT)
        assert old == (ROOT / name).read_bytes(), 'historical_protocol_changed: ' + name
        identical[name] = hashlib.sha256(old).hexdigest()
    validator = 'control/app/validator.py'
    old = subprocess.check_output(['git', 'show', SOURCE_REVISION + ':' + validator], cwd=ROOT)
    current = (ROOT / validator).read_bytes()
    expected = old.replace(b'allowed=(200,201,204)):', b'allowed=(200,201,204),max_bytes=LIMIT):')
    expected = expected.replace(b"'/v1.45'+path,body,timeout)", b"'/v1.45'+path,body,timeout,max_bytes)")
    assert current == expected, 'unexpected_historical_validator_difference'
    validator_comparison = {'historical_sha256': hashlib.sha256(old).hexdigest(),
                            'current_sha256': hashlib.sha256(current).hexdigest(),
                            'only_optional_max_bytes': True}
    folder = '/srv/p2enjoy-serverless/qualification-history/build-' + REVISION
    prepare = "import os,socket;from pathlib import Path;assert socket.gethostname()=='infra-serverless';p=Path(" + repr(folder) + ");p.mkdir(parents=True,exist_ok=True);os.chmod(p,0o755)"
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
print(json.dumps({'historical_image':built,'current_image':original,'current_tag_unchanged':True,'sources':actual}))
'''.replace('FOLDER', repr(folder)).replace('HASHES', repr(hashes))
    # Build output is retained separately; it contains no cell configuration.
    result = subprocess.run(SSH + ['python3 -B -'], input=remote, text=True,
                            capture_output=True, timeout=900)
    (output / 'storage-legacy-build.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, 'historical_build_failed; see .local/e2e/storage-legacy-build.log'
    report = json.loads(result.stdout.strip().splitlines()[-1])
    report.update(revision=REVISION, source_revision=SOURCE_REVISION, identical_protocols=identical,
                  validator_comparison=validator_comparison, completed=True)
    (output / 'storage-legacy-build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('revision', 'historical_image', 'current_image', 'completed')}))


if __name__ == '__main__':
    main()
