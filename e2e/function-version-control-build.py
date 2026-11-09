# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#banc-historique-réel-et-borné
"""Rebuild the genuine schema006 control from its pinned Git tree, without deploying it."""
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

ROOT=Path(__file__).resolve().parent.parent
REVISION='f56d79ebe3d1d84731bfd262d1e6a9d5b5a680c0'
MIGRATIONS=['001_control.sql','002_login_limits.sql','003_deployments.sql','004_function_operations.sql','005_execution.sql','006_storage_commands.sql']
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24']
output=ROOT/'.local/e2e';output.mkdir(mode=0o700,parents=True,exist_ok=True)
report=output/'function-version-control-schema006-build.json'
report.write_text(json.dumps({'completed':False,'revision':REVISION})+'\n')
archive=subprocess.check_output(['git','archive',REVISION,'control','web','docs/manual.md'],cwd=ROOT)
hashes={}
with tarfile.open(fileobj=io.BytesIO(archive)) as source:
    for member in source:
        assert member.isfile() or member.isdir()
        assert not member.name.startswith('/') and '..' not in Path(member.name).parts
        if member.isfile():hashes[member.name]=hashlib.sha256(source.extractfile(member).read()).hexdigest()
assert sorted(Path(n).name for n in hashes if n.startswith('control/migrations/') and n.endswith('.sql'))==MIGRATIONS
baseline=json.loads((ROOT/'docs/evidence/function-code-hash-dev-2026-11-09.json').read_text())['source_sha256_at_delivery']
compared=[name for name in baseline if name.startswith(('control/app/','control/migrations/','web/')) or name in ('control/Dockerfile','control/Dockerfile.dockerignore','control/requirements.txt','docs/manual.md')]
assert compared and all(hashes.get(name)==baseline[name] for name in compared),'historical_product_source_mismatch'
expected={name.removeprefix('control/'):value for name,value in hashes.items()
          if name.startswith(('control/app/','control/migrations/')) or name=='control/requirements.txt'}
folder='/srv/p2enjoy-serverless/qualification-history/build-control-schema006-'+REVISION
prepare='''import os,socket
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless/qualification-history');root.mkdir(mode=0o755,exist_ok=True)
assert root.resolve()==root and root.stat().st_uid==0
path=root/NAME;path.mkdir(mode=0o755,exist_ok=True);assert path.resolve()==path and path.stat().st_uid==0
'''.replace('NAME',repr(Path(folder).name))
subprocess.run(SSH+['python3 -B -'],input=prepare,text=True,check=True,timeout=30)
subprocess.run(SSH+['tar --no-same-owner -xf - -C '+shlex.quote(folder)],input=archive,check=True,timeout=60)
program='import hashlib,json,os,socket,subprocess,tempfile,uuid\nfrom pathlib import Path\nfolder=Path('+repr(folder)+')\nhashes='+repr(hashes)+'\nexpected='+repr(expected)+'\nrevision='+repr(REVISION)+'\nmigrations='+repr(MIGRATIONS)+'\n'+'''
assert socket.gethostname()=='infra-serverless'
assert {name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in hashes}==hashes
docker=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def run(args):return subprocess.check_output(docker+args,text=True,timeout=120).strip()
original=run(['inspect','--format','{{.Image}}','serverless-api'])
tag_before=run(['image','inspect','--format','{{.Id}}','p2enjoy-control:dev']);assert tag_before==original
tag='p2enjoy-control:historical-schema-006'
subprocess.run(docker+['build','--tag',tag,'--file',str(folder/'control/Dockerfile'),str(folder)],check=True,timeout=900)
image=run(['image','inspect','--format','{{.Id}}',tag])
code="import hashlib,json;from pathlib import Path;p=Path('/app');files=[*p.glob('app/*.py'),*p.glob('migrations/*.sql'),p/'requirements.txt'];print(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}))"
name='serverless-schema006-source-inspection-'+uuid.uuid4().hex[:8]
embedded=json.loads(run(['run','--rm','--name',name,'--network','none','--read-only','--cap-drop','ALL',
    '--security-opt','no-new-privileges:true','--memory','128m','--pids-limit','32','--entrypoint','python',image,'-B','-c',code]))
assert embedded==expected,'historical_embedded_source_mismatch'
assert run(['inspect','--format','{{.Image}}','serverless-api'])==original
assert run(['image','inspect','--format','{{.Id}}','p2enjoy-control:dev'])==tag_before
value={'completed':True,'revision':revision,'image':image,'tag':tag,'schema_migrations':migrations,
       'embedded':embedded,'source_sha256':hashes,'current_image':original,'current_tag_unchanged':True}
attestation=folder.parent/'function-version-schema006-image.json'
if attestation.exists():assert not attestation.is_symlink() and attestation.stat().st_uid==0
with tempfile.NamedTemporaryFile(dir=folder.parent,prefix='.schema006-image-',delete=False) as stream:
 pending=Path(stream.name);stream.write((json.dumps(value)+'\\n').encode());stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o644)
pending.replace(attestation);assert attestation.stat().st_uid==0
print(json.dumps(value))
'''
started=time.time_ns()
result=subprocess.run(SSH+['python3 -B -'],input=program,text=True,capture_output=True,timeout=1200)
(output/'function-version-control-schema006-build.log').write_text(result.stdout+result.stderr)
assert result.returncode==0,'schema006_image_build_failed: see private build log'
value=json.loads(result.stdout.strip().splitlines()[-1]);assert value['completed'] and value['revision']==REVISION
value.update(compared_product_files=len(compared),started_at_ns=started,ended_at_ns=time.time_ns())
report.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'completed':True,'revision':REVISION,'image':value['image'],'compared_product_files':len(compared),'embedded_files':len(value['embedded']),'current_image_unchanged':True}))
