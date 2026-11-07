# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
# @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
"""Serial DEV qualification with fresh reports bound to sources and deployed image."""
import argparse
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
    files=[p for folder,pattern in [('control/app','*.py'),('control/migrations','*.sql'),('storage','*.py'),('storage/migrations','*.sql'),('runtime','*.mjs'),('adapter','*.py')] for p in (ROOT/folder).glob(pattern)]
    files += [ROOT/p for p in ['control/Dockerfile','control/requirements.txt','control/compose.spark.yml','control/dev.sh','runtime/Dockerfile','runtime/compose.spark.yml','runtime/dev.sh','storage/main.go','storage/go.mod','storage/go.sum','storage/dev.sh','storage/Dockerfile','qualification/artifacts/volume-operations.cjs','qualification/artifacts/public-invocation.cjs','qualification/artifacts/invoke.cjs','web/package.json','web/package-lock.json','web/index.html']]
    files += [ROOT/'qualification/artifacts/observation.cjs']
    # @spec docs/BACKLOG.md#sls-062 | docs/CONSOLE_MANUAL.md#preuves-attendues
    files += [ROOT/name for name in ['docs/manual.md','web/vite.config.mjs','control/Dockerfile.dockerignore']]
    # @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
    files += [p for p in (ROOT/'qualification/artifacts').iterdir() if p.is_file()]
    files += [ROOT/name for name in ['docs/CONSOLE_PUBLICATION.md','docs/DESIGN_SYSTEM_APP.md','qualification/serverless.platform.yml','qualification/src/handlers.cjs','adapter/requirements.txt']]
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
 ('code-publications',['node','e2e/code-publications.mjs'],'.local/e2e/code-publications.json',False),
 ('adapter-deploy',['node','e2e/adapter-deploy.mjs'],'.local/e2e/adapter-deploy.json',False),
 ('publication-recovery',['node','e2e/publication-recovery.mjs'],'.local/e2e/publication-recovery.json',False),
 ('public',['python3','-B','e2e/public.py'],'.local/e2e/public.json',False),
 ('public-invocations',['node','e2e/public-invocations.mjs'],'.local/e2e/public-invocations.json',False),
]

def verify_report(name,path,is_remote,expected_hash):
    if is_remote:
        script='from pathlib import Path;import sys;sys.stdout.buffer.write(Path('+repr(REMOTE+path)+').read_bytes())'
        contents=subprocess.check_output(remote(['python3','-B','-c',script],'root'))
    else:contents=(ROOT/path).read_bytes()
    assert hashlib.sha256(contents).hexdigest()==expected_hash,'Rapport changé après le relevé'
    result=json.loads(contents)
    assert result['completed'] is True and result['skipped']==0,'Campagne incomplète ou ignorée'
    expected={'control-operations':55,'function-storage':14,'runtime-instances':31,'instance-lifecycle':11,
              'runtime-validation':36,'managed-storage':14,'control-admin':19,'control-ui':11,
              'deployments':11,'adapter-deploy':7,'publication-recovery':4,'public':8,
              'public-invocations':31,'login-ui':9,'execution-ui':12,'manual-ui':8,
              'code-publications':10,'publication-ui':21}
    checks=result.get('checks',result.get('results'))
    assert isinstance(checks,list) and len(checks)==expected[name],'Nombre de groupes inattendu'
    if name=='login-ui':assert all(isinstance(row,str) and row for row in checks)
    else:assert all(row['status']=='passed' for row in checks),'Groupe échoué'
    assert not result.get('failed') and not result.get('failures') and not result.get('cleanupErrors') and not result.get('cleanup_errors')
    if name not in ('runtime-validation','public','login-ui','control-ui','control-admin','manual-ui'):
        assert result['cleanup'] is True,'Nettoyage incomplet'
    if name in ('control-ui','execution-ui'):assert result['faults']==[] and result['cleanupErrors']==[]
    if name=='manual-ui':assert result['faults']==[]
    if name=='publication-ui':assert result['faults']==[]
    return len(checks)

def main():
    # @verifies docs/BACKLOG.md#sls-061 | docs/CONSOLE_EXECUTION.md#preuves-attendues
    # @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope',choices=('engine','console','publication'),default='engine')
    scope=parser.parse_args().scope
    report={'engine':REPORT,'console':ROOT/'.local/e2e/console-execution-regressions.json','publication':ROOT/'.local/e2e/publication-regressions.json'}[scope]
    console_cases=[
        next(row for row in CASES if row[0]=='public'),
        ('login-ui',['node','e2e/login-ui.mjs'],'.local/e2e/login-ui.json',False),
        next(row for row in CASES if row[0]=='control-ui'),
        ('execution-ui',['node','e2e/execution-ui.mjs'],'.local/e2e/execution-ui.json',False),
        ('publication-ui',['node','e2e/publication-ui.mjs'],'.local/e2e/publication-ui.json',False),
        ('manual-ui',['node','e2e/manual-ui.mjs'],'.local/e2e/manual-ui.json',False),
    ]
    cases=CASES if scope=='engine' else console_cases
    if scope=='publication':
        cases=CASES+[row for row in console_cases if row[0] not in {case[0] for case in CASES}]
    records=[];baseline=None
    def save(done=False):
        temporary=report.with_suffix('.tmp')
        temporary.write_text(json.dumps({'completed':done,'serial':True,'scope':scope,'commands':records},ensure_ascii=False,indent=2)+'\n')
        temporary.replace(report)
    report.parent.mkdir(parents=True,exist_ok=True,mode=0o700);save()
    for name,command,path,is_remote in cases:
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
        record['passed_groups']=verify_report(name,path,is_remote,after['report']['sha256'])
        record['fresh_report_verified']=True;record['report_content_verified']=True;save()
    save(True)

if __name__=='__main__':main()
