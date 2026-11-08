# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
"""Serial real adapter builds and immutable source recoup, without test groups."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/e2e/invocation-url-adapter-build.json'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-J', 'ubuntu@51.158.54.202',
       'root@10.77.0.24', 'python3 -B -']


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if OUTPUT.exists():
        previous = json.loads(OUTPUT.read_text())
        assert previous.get('remote_state') != 'unknown', 'inspect_actual_remote_build_and_archive_unknown_report_before_retry'
    OUTPUT.write_text(json.dumps({'completed': False}) + '\n')
    script = '''import hashlib,json,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
docker=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def control():return subprocess.check_output(docker+['inspect','--format','{{.Image}}','serverless-api'],text=True).strip()
before=control()
root=Path('/srv/p2enjoy-serverless')
subprocess.run(['timeout','--kill-after=15s','780s','runuser','-u','spark-docker','--','env','DOCKER_HOST=unix:///run/user/1001/docker.sock','bash',str(root/'adapter/dev.sh'),'build'],check=True,cwd=root,timeout=820)
code="import hashlib,json;from pathlib import Path;print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/adapter').glob('*.py')}))"
result={}
for image in ['p2enjoy-adapter:dev','p2enjoy-adapter-e2e:dev']:
 identifier=json.loads(subprocess.check_output(docker+['image','inspect',image],text=True,timeout=30))[0]['Id']
 sources=json.loads(subprocess.check_output(docker+['run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','16','--memory','128m','--entrypoint','python',identifier,'-B','-c',code],text=True,timeout=60))
 result[image]={'image':identifier,'embedded_sources':sources}
assert control()==before
tag=json.loads(subprocess.check_output(docker+['image','inspect','p2enjoy-control:dev'],text=True,timeout=30))[0]['Id']
assert tag==before
print(json.dumps({'completed':True,'remote_state':'completed','current_image':before,'current_tag_unchanged':True,'images':result}))
'''
    try:
        result = subprocess.run(SSH, input=script, text=True, capture_output=True, timeout=900)
    except (subprocess.TimeoutExpired, OSError):
        OUTPUT.write_text(json.dumps({'completed': False, 'remote_state': 'unknown',
            'error': 'remote_build_liveness_unconfirmed', 'automatic_retry': False}) + '\n')
        raise AssertionError('inspect_actual_remote_build_before_retry') from None
    OUTPUT.with_suffix('.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        OUTPUT.write_text(json.dumps({'completed': False, 'remote_state': 'unknown',
            'error': 'remote_build_failed_or_disconnected', 'automatic_retry': False}) + '\n')
        raise AssertionError('adapter_build_failed; inspect actual remote state before retry')
    value = json.loads(result.stdout.strip().splitlines()[-1])
    expected = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'adapter').glob('*.py')}
    assert len(expected) == 5
    assert all(row['embedded_sources'] == expected for row in value['images'].values()), 'embedded_cli_sources_differ'
    OUTPUT.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({'completed': True, 'images': {name: row['image'] for name, row in value['images'].items()}, 'embedded_files': len(expected)}))


if __name__ == '__main__': main()
