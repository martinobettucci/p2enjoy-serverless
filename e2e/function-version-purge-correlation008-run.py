# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-de-corrélation-sur-copies007
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-de-corrélation-sur-copies007
"""Freeze sources and qualify one phase of actual schema007 purge-correlation refusals."""
import hashlib,json,runpy,subprocess,sys,time
from pathlib import Path

r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');phase=sys.argv[1];assert len(sys.argv)==2 and phase in ('volumes','artifacts')
name='function-version-purge-correlation008-'+phase;report_path='control/'+name+'.json';checkpoint=folder/(name+'-checkpoint.json');assert not checkpoint.exists(),'preserve_previous_checkpoint'
proof=json.loads(Path('docs/evidence/function-version-purge-migration008-dev-2026-11-09.json').read_text());assert proof['completed']
sources=[v['report']['campaign'] for v in proof['historical_campaigns'] if v['report']['source_schema']=='007' and v['report']['phase']==phase and not v['report']['guarded']];assert len(sources)==1
before=r['snapshot'](report_path,True,include_adapter=True);assert before['report']['sha256'] is None,'preserve_previous_remote_report';started=time.time_ns()
checkpoint.write_text(json.dumps({'completed':False,'before':before,'started_at_ns':started},indent=2)+'\n')
p=subprocess.run(r['SSH']+['root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/function-version-purge-correlation008.py',sources[0],phase,before['image']],capture_output=True,text=True,timeout=900)
log=folder/(name+'.log');log.write_text(p.stdout+p.stderr);print(p.stdout,end='')
after=r['snapshot'](report_path,True,include_adapter=True);report=None
if after['report']['sha256'] is not None:
    raw=subprocess.check_output(r['SSH']+['root@10.77.0.24','cat','/srv/p2enjoy-serverless/'+report_path],text=True,timeout=30);report=json.loads(raw);(folder/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
valid=p.returncode==0 and report is not None and report['completed'] and report['cleanup'] and not report['cleanup_errors'] and not report['unconfirmed_containers'] and report['skipped']==0 and len(report['checks'])==21 and all(v['status']=='passed' for v in report['checks']) and before['source_sha256']==after['source_sha256'] and before['image']==after['image']==report['image'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started
value={'completed':bool(valid),'started_at_ns':started,'ended_at_ns':time.time_ns(),'exit_code':p.returncode,'before':before,'after':after,'report':report,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()};checkpoint.write_text(json.dumps(value,indent=2)+'\n');assert valid,'inspect_purge_correlation_checkpoint_no_automatic_replay';print(json.dumps({'completed':True,'groups':21,'phase':phase,'source_files':len(after['source_sha256']),'image':after['image'],'served_installation_unchanged':report['live_before']==report['live_after']}))
