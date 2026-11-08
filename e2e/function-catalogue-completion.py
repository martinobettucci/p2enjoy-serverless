# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#continuation-après-correction-des-seuls-clients-de-preuve
# @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#continuation-après-correction-des-seuls-clients-de-preuve
"""Complete this DEV qualification from immutable successful campaign evidence.

No product/image change is accepted. Changed clients are always re-executed.
The failed and superseded results remain outside the active 37-campaign set.
"""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
R=runpy.run_path(str(ROOT/'e2e/execution-suite.py'))
PARENT=ROOT/'.local/e2e/function-catalogue-suite-navigation-incomplete'
OUTPUT=ROOT/'.local/e2e/function-catalogue-regressions.json'
EXPECTED={row[0] for row in R['CASES']}|{
    'login-ui','execution-ui','publication-ui','manual-ui','service-transport',
    'service-configuration','invocation-urls','invocation-urls-ui','adapter-docker',
    'adapter-public-docker','function-catalogue-api','function-catalogue-ui',
    'storage-discard','storage-agent','storage-limits','storage-preparations',
    'storage-console-api','storage-console-ui','storage-command-recovery',
    'storage-validation-recovery','storage-decision-recovery',
    'storage-legacy-partial','storage-legacy-recovery'}
REEXECUTE=('function-catalogue-ui','storage-console-ui','storage-command-recovery',
           'storage-validation-recovery','storage-decision-recovery',
           'storage-legacy-partial','storage-legacy-recovery')
CLIENT_DELTAS={'e2e/function-catalogue-ui.mjs','e2e/storage-console-ui.mjs'}
ALLOWED_DELTAS=CLIENT_DELTAS|{'docs/FUNCTION_CATALOGUE.md'}
ADDED={'e2e/function-catalogue-completion.py'}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert len(EXPECTED)==37 and len(REEXECUTE)==7
    original=json.loads((PARENT/'suite.json').read_text())
    receipt=json.loads((PARENT/'physical.json').read_text())
    assert receipt['completed'] and receipt['suite_sha256']==digest(PARENT/'suite.json')
    assert receipt['physical']['completed'] and receipt['groups_from_complete_campaigns']==461
    assert original['scope']=='function-catalogue' and original['serial'] and not original['completed']
    assert original['commands'][-1]['campaign']=='storage-console-ui' and original['commands'][-1]['exit_code']==1
    successful=[row for row in original['commands'] if row.get('passed_groups')]
    assert len(successful)==31 and sum(row['passed_groups'] for row in successful)==461
    records=[row for row in successful if row['campaign'] not in REEXECUTE]
    assert len(records)==30 and {row['campaign'] for row in records}==EXPECTED-set(REEXECUTE)
    assert sum(row['passed_groups'] for row in records)==447
    old_sources=records[0]['before']['source_sha256']
    old_image=records[0]['before']['image'];old_adapter=records[0]['before']['adapter_images']
    assert all(receipt[side]['source_sha256']==old_sources and receipt[side]['image']==old_image and
               receipt[side]['adapter_images']==old_adapter for side in ('before','after'))
    current=R['snapshot']('.local/e2e/function-catalogue-regressions.json',False,include_adapter=True)
    sources=current['source_sha256'];changed={p for p in old_sources if sources.get(p)!=old_sources[p]}
    assert set(sources)-set(old_sources)==ADDED and not set(old_sources)-set(sources),'unexpected_source_inventory_change'
    assert changed==ALLOWED_DELTAS,'unexpected_source_change'
    assert current['image']==old_image and current['adapter_images']==old_adapter,'product_or_cli_image_changed'
    for row in successful:
        assert row['exit_code']==0 and row['fresh_report_verified'] and row['report_content_verified']
        assert all(row[side]['source_sha256']==old_sources and row[side]['image']==old_image and
                   row[side]['adapter_images']==old_adapter for side in ('before','after'))
        archive=receipt['reports'][row['campaign']];path=ROOT/archive['path']
        assert digest(path)==archive['sha256']==row['after']['report']['sha256']
        if row['campaign'] in {r['campaign'] for r in records}:
            assert R['verify_report'](row['campaign'],row['report_path'],row['report_remote'],archive['sha256'])==row['passed_groups']
    prerequisites=original['prerequisites']
    assert len(prerequisites)==4
    for row in prerequisites:
        assert row['exit_code']==0 and row['fresh_report_verified'] and row['report_content_verified']
        archive=receipt['reports'][row['campaign']];assert digest(ROOT/archive['path'])==archive['sha256']==row['after']['report']['sha256']
        assert all(row[side]['source_sha256']==old_sources and row[side]['image']==old_image for side in ('before','after'))
    value={'completed':False,'serial':True,'scope':'function-catalogue',
           'qualification_mode':'continuation_after_client_only_changes',
           'parent_attempt':{'path':str((PARENT/'suite.json').relative_to(ROOT)),'sha256':digest(PARENT/'suite.json'),
                             'physical_receipt_path':str((PARENT/'physical.json').relative_to(ROOT)),
                             'physical_receipt_sha256':digest(PARENT/'physical.json')},
           'source_epochs':{'initial':old_sources,'continued':sources},
           'changed_sources':sorted(changed),'added_sources':sorted(ADDED),
           'product_sources_and_images_unchanged':True,
           'superseded_successful_campaigns':[row for row in successful if row['campaign'] in REEXECUTE],
           'excluded_failed_campaign':original['commands'][-1],
           'prerequisites':prerequisites,'commands':records}
    for row in records:row['source_epoch']='initial'
    for row in prerequisites:row['source_epoch']='initial'

    def save():
        temp=OUTPUT.with_suffix('.pending');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(OUTPUT)

    def execute(name,command,path,is_remote=False,*,prerequisite=False,private_input=None):
        before=R['snapshot'](path,is_remote,include_adapter=True)
        assert before['source_sha256']==sources and before['image']==old_image and before['adapter_images']==old_adapter
        row={'campaign':name,'command':command,'report_path':path,'report_remote':is_remote,
             'source_epoch':'continued','before':before,'exit_code':None}
        (prerequisites if prerequisite else records).append(row);save()
        print(json.dumps({'prerequisite' if prerequisite else 'campaign':name,'state':'running'}),flush=True)
        start=time.monotonic();options={'input':private_input} if private_input is not None else {'stdin':subprocess.DEVNULL}
        result=subprocess.run(command,cwd=ROOT,**options);row.update(exit_code=result.returncode,duration_seconds=round(time.monotonic()-start,3));save()
        after=R['snapshot'](path,is_remote,include_adapter=True);row['after']=after;save()
        assert after['source_sha256']==sources and after['image']==old_image and after['adapter_images']==old_adapter
        if result.returncode:raise SystemExit(result.returncode)
        assert before['report']['sampled_at_ns']<=after['report']['mtime_ns']<=after['report']['sampled_at_ns']
        if not prerequisite:row['passed_groups']=R['verify_report'](name,path,is_remote,after['report']['sha256'])
        else:
            report=R['read_report'](path,is_remote,after['report']['sha256']);assert report['completed']
            if name=='dev-sso-decision-sessions':
                assert report['purpose']=='storage-decisions' and report['authenticated'] and report['independent_sessions']==2 and report['platform_cookies_only']
            elif name=='storage-console-physical':
                assert report['campaign_count']==10 and report['function_count']==32 and report['physical']['completed']
                assert report['total_namespaces']==23 and report['total_functions']==91
                assert set(report['catalogue'])=={'function-catalogue-api','function-catalogue-ui'}
                assert all(r['physical']['completed'] and r['services_cleared'] for r in report['catalogue'].values())
            else:raise AssertionError('unexpected_prerequisite')
        row.update(fresh_report_verified=True,report_content_verified=True);save()

    credentials=R['private_credentials']()
    try:
        save()
        for name in REEXECUTE:
            if name=='storage-decision-recovery':
                execute('dev-sso-decision-sessions',['node','e2e/dev-sso-sessions.mjs','--for-storage-decisions'],
                        '.local/e2e/dev-sso-decision-sessions.json',prerequisite=True,private_input=credentials)
            command=['node','e2e/'+('storage-legacy-recovery' if name.startswith('storage-legacy-') else name)+'.mjs']
            if name.startswith('storage-legacy-'):command.append('--partial' if name.endswith('partial') else '--full')
            execute(name,command,'.local/e2e/'+name+'.json',private_input=credentials if name=='storage-legacy-recovery' else None)
        assert len(records)==37 and {r['campaign'] for r in records}==EXPECTED and sum(r['passed_groups'] for r in records)==489
        execute('storage-console-physical',['python3','-B','e2e/storage-suite-inspect.py',str(OUTPUT.relative_to(ROOT))],
                '.local/e2e/function-catalogue-physical.json',prerequisite=True)
        assert len(prerequisites)==6
        intervals=[(r['before']['report']['sampled_at_ns'],r['after']['report']['sampled_at_ns']) for r in records]
        assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])),'overlapping_campaigns'
        value.update(completed=True,passed_groups=489,skipped=0);save()
        print(json.dumps({'completed':True,'campaigns':37,'passed_groups':489,'prerequisites':6,
                          'retained_groups':447,'continued_groups':42,'source_epochs':[len(old_sources),len(sources)]}),flush=True)
    finally:credentials=None


if __name__=='__main__':main()
