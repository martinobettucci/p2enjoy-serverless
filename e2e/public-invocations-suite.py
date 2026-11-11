# @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#perte-avec-consommateur-et-raccordement--réalisation
# @verifies docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#scénarios-requis
# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
# @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
"""Run the real public HTTP and isolated count-limit campaigns serially."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/e2e'
REPORT=OUT/'public-invocations.json'
R=runpy.run_path(str(ROOT/'e2e/execution-suite.py'))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True,mode=0o700)
    archive=OUT/('public-invocations-run-'+uuid4().hex)
    archive.mkdir(mode=0o700)
    for name in ('public-invocations.json','public-invocations-http.json','dev-sso-public-sessions.json'):
        path=OUT/name
        if path.exists():shutil.copyfile(path,archive/name)
    state={'completed':False,'cleanup':False,'skipped':0,'failed':0,'checks':[],
           'cleanupErrors':[],'orchestration':{'serial':True,'attempt':archive.name,'phases':[]}}
    def save():
        pending=REPORT.with_suffix('.pending')
        pending.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        pending.chmod(0o600);pending.replace(REPORT)
    save()
    credentials=R['private_credentials']()
    baseline=None
    def execute(label,args,report_path,private_input=None):
        nonlocal baseline
        before=R['snapshot'](str(report_path.relative_to(ROOT)),False,include_adapter=True)
        frozen={key:before[key] for key in ('source_sha256','image','adapter_images')}
        if baseline is None:baseline=frozen
        assert frozen==baseline,'sources_or_images_changed_before_phase'
        record={'name':label,'command':args,'before':before,'started_at_ns':time.time_ns()}
        state['orchestration']['phases'].append(record);save()
        print(json.dumps({'phase':label,'state':'running'}),flush=True)
        options={'input':private_input} if private_input is not None else {'stdin':subprocess.DEVNULL}
        code=subprocess.run(args,cwd=ROOT,**options,timeout=1200).returncode
        record.update(exit_code=code,finished_at_ns=time.time_ns());save()
        assert code==0,'phase_failed_no_automatic_replay:'+label
        return record
    try:
        sso=OUT/'dev-sso-public-sessions.json'
        phase=execute('real-sso',['node','e2e/dev-sso-sessions.mjs','--for-public-invocations'],sso,credentials)
        auth=json.loads(sso.read_text());assert auth['completed'] and auth['authenticated'] and auth['independent_sessions']==2 and auth['purpose']=='public-invocations'
        phase['report_sha256']=sha(sso);phase['counted_groups']=0;save()
        http_path=OUT/'public-invocations-http.json'
        phase=execute('http',['node','e2e/public-invocations.mjs'],http_path)
        http=json.loads(http_path.read_text());assert http['completed'] and http['cleanup'] and http['skipped']==0 and not http['cleanupErrors']
        assert len(http['checks'])==30 and all(v['status']=='passed' for v in http['checks'])
        phase['report_sha256']=sha(http_path);phase['counted_groups']=30
        state.update(http);state.update(completed=False,cleanup=False,failed=0);save()
        previous=set(OUT.glob('instance-limit-admission-*.json'))
        phase=execute('isolated-instance-limit',['node','e2e/instance-limit-admission.mjs'],REPORT,credentials)
        produced=set(OUT.glob('instance-limit-admission-*.json'))-previous
        assert len(produced)==1,'unique_isolated_report_required'
        isolated_path=produced.pop();isolated=json.loads(isolated_path.read_text())
        assert isolated['completed'] and isolated['cleanup'] and isolated['skipped']==0 and isolated['failure'] is None
        assert len(isolated['checks'])==4 and all(v['status']=='passed' for v in isolated['checks'])
        after=R['snapshot'](str(isolated_path.relative_to(ROOT)),False,include_adapter=True)
        assert {key:after[key] for key in baseline}==baseline,'sources_or_images_changed_during_campaign'
        phase.update(report_path=str(isolated_path.relative_to(ROOT)),report_sha256=sha(isolated_path),after=after,counted_groups=1,detail_groups=4)
        state['checks'].append({'name':'Plafond global isolé : HTTP, minimum et planification réels','status':'passed','detail_groups':4})
        state['isolated_instance_limit']={'report_path':str(isolated_path.relative_to(ROOT)),'sha256':sha(isolated_path),'report':isolated}
        state['orchestration'].update(http_groups=30,isolated_detail_groups=4,reported_public_groups=31,source_files=len(baseline['source_sha256']))
        state.update(completed=True,cleanup=True);save()
        print(json.dumps({'completed':True,'groups':31,'isolated_detail_groups':4,'report':str(REPORT)}),flush=True)
    except BaseException as error:
        state.update(completed=False,failed=1,failure={'type':type(error).__name__})
        save();raise
    finally:credentials=None


if __name__=='__main__':main()
