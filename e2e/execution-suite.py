# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
# @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
"""Serial DEV qualification with fresh reports bound to sources and deployed image."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

ROOT=Path(__file__).resolve().parent.parent
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202']
REMOTE='/srv/p2enjoy-serverless/'
REPORT=ROOT/'.local/e2e/execution-regressions.json'

def source_hashes():
    files=[p for folder,pattern in [('control/app','*.py'),('control/migrations','*.sql'),('storage','*.py'),('storage/migrations','*.sql'),('runtime','*.mjs')] for p in (ROOT/folder).glob(pattern)]
    files += [ROOT/p for p in ['control/Dockerfile','control/requirements.txt','control/compose.spark.yml','control/dev.sh','runtime/Dockerfile','runtime/compose.spark.yml','runtime/dev.sh','storage/main.go','storage/go.mod','storage/go.sum','storage/dev.sh','storage/Dockerfile','qualification/artifacts/volume-operations.cjs','qualification/artifacts/public-invocation.cjs','qualification/artifacts/invoke.cjs','web/package.json','web/package-lock.json','web/index.html']]
    files += [p for p in (ROOT/'web/src').glob('*') if p.is_file()]
    files += [p for p in (ROOT/'e2e').iterdir() if p.suffix in ('.py','.mjs')]
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}

def metadata(path):
    return {'sampled_at_ns':time.time_ns(),'mtime_ns':path.stat().st_mtime_ns,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} if path.exists() else {'sampled_at_ns':time.time_ns(),'mtime_ns':None,'sha256':None}

def snapshot(report_path,remote):
    sources=source_hashes()
    script="""import hashlib,json,subprocess,time
from pathlib import Path
assert Path('/etc/hostname').read_text().strip()=='infra-serverless'
image=subprocess.check_output(['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api'],text=True).strip()
result={'image':image,'source_sha256':{name:hashlib.sha256((Path('/srv/p2enjoy-serverless')/name).read_bytes()).hexdigest() for name in SOURCE_INDEX}}
path=Path(REPORT_PATH) if REMOTE_REPORT else None
if path:
 result['report']={'sampled_at_ns':time.time_ns(),'mtime_ns':path.stat().st_mtime_ns,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} if path.exists() else {'sampled_at_ns':time.time_ns(),'mtime_ns':None,'sha256':None}
print(json.dumps(result))
""".replace('REPORT_PATH',repr(REMOTE+report_path)).replace('REMOTE_REPORT',repr(remote)).replace('SOURCE_INDEX',repr(list(sources)))
    value=json.loads(subprocess.run(SSH+['root@10.77.0.24','python3 -B -'],input=script,text=True,capture_output=True,check=True).stdout)
    if not remote:value['report']=metadata(ROOT/report_path)
    assert value['source_sha256']==sources,'Sources distantes différentes du poste'
    return value

def remote(command,user='spark-docker'):
    return SSH+[user+'@10.77.0.24',shlex.join(command)]

CASES=[
 ('control-operations',remote(['python3','-B',REMOTE+'e2e/control-operations.py']),'control/.proof-control-operations.json',True),
 ('function-storage',['node','e2e/function-storage.mjs'],'.local/e2e/function-storage.json',False),
 ('runtime-instances',remote(['bash',REMOTE+'runtime/dev.sh','instances-test']),'runtime/instances-proof.json',True),
 ('instance-lifecycle',remote(['bash',REMOTE+'runtime/dev.sh','lifecycle-test']),'runtime/lifecycle-proof.json',True),
 ('runtime-validation',remote(['bash',REMOTE+'runtime/dev.sh','test']),'runtime/validation-proof.json',True),
 ('managed-storage',remote(['python3','-B',REMOTE+'e2e/managed-storage.py'],'root'),'runtime/managed-storage-proof.json',True),
 ('control-admin',['node','e2e/control-admin.mjs'],'.local/e2e/control-admin.json',False),
 ('control-ui',['node','e2e/control-ui.mjs'],'.local/e2e/control-ui.json',False),
 ('deployments',['node','e2e/deployments.mjs'],'.local/e2e/deployments.json',False),
 ('adapter-deploy',['node','e2e/adapter-deploy.mjs'],'.local/e2e/adapter-deploy.json',False),
 ('publication-recovery',['node','e2e/publication-recovery.mjs'],'.local/e2e/publication-recovery.json',False),
 ('public',['python3','-B','e2e/public.py'],'.local/e2e/public.json',False),
 ('public-invocations',['node','e2e/public-invocations.mjs'],'.local/e2e/public-invocations.json',False),
]

def main():
    records=[];baseline=None
    def save(done=False):
        temporary=REPORT.with_suffix('.tmp')
        temporary.write_text(json.dumps({'completed':done,'serial':True,'commands':records},ensure_ascii=False,indent=2)+'\n')
        temporary.replace(REPORT)
    REPORT.parent.mkdir(parents=True,exist_ok=True,mode=0o700);save()
    for name,command,path,is_remote in CASES:
        before=snapshot(path,is_remote)
        if baseline is None:baseline={k:before[k] for k in ('image','source_sha256')}
        assert all(before[k]==v for k,v in baseline.items()),'Image ou sources changées avant campagne'
        record={'campaign':name,'command':command,'report_path':path,'report_remote':is_remote,'before':before,'exit_code':None}
        records.append(record);save();print(json.dumps({'campaign':name,'state':'running'}),flush=True)
        started=time.monotonic()
        result=subprocess.run(command,cwd=ROOT)
        record.update(exit_code=result.returncode,duration_seconds=round(time.monotonic()-started,2));save()
        if result.returncode:raise SystemExit(result.returncode)
        after=snapshot(path,is_remote);record['after']=after;save()
        assert all(after[k]==v for k,v in baseline.items()),'Image ou sources changées pendant campagne'
        assert before['report']['sampled_at_ns']<=after['report']['mtime_ns']<=after['report']['sampled_at_ns'],'Rapport non régénéré par la campagne'
        record['fresh_report_verified']=True;save()
    save(True)

if __name__=='__main__':main()
