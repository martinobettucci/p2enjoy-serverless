# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#résultats-et-régression
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#invariants-et-matrice-négative
"""Freeze sources and run an explicit schema008 rejection campaign on real DEV copies."""
import hashlib,json,runpy,subprocess,sys,time
from pathlib import Path

r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');name='function-version-migration008';selection=sys.argv[1] if len(sys.argv)>1 else 'all-rejections'
report_path='control/'+name+'.json';checkpoint=folder/(name+'-checkpoint.json');assert not checkpoint.exists(),'preserve_previous_checkpoint'
baseline=json.loads((folder/'function-versions-before008-backup.json').read_text());assert baseline['completed']
before=r['snapshot'](report_path,True,include_adapter=True);assert before['report']['sha256'] is None,'preserve_previous_remote_report'
image=sys.argv[2] if len(sys.argv)>2 else before['image'];started=time.time_ns()
(folder/(name+'-before.json')).write_text(json.dumps(before,indent=2)+'\n')
command=r['SSH']+['root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/function-version-migration008.py',Path(baseline['backup']).name,baseline['function_id'],selection,image]
process=subprocess.run(command,input=json.dumps({k:baseline[k] for k in ('control_tables',)}|{'source_image':baseline['control_image']}),capture_output=True,text=True,timeout=900)
log=folder/(name+'.log');log.write_text(process.stdout+process.stderr);print(process.stdout,end='')
after=r['snapshot'](report_path,True,include_adapter=True)
read=subprocess.run(r['SSH']+['root@10.77.0.24','cat','/srv/p2enjoy-serverless/'+report_path],capture_output=True,text=True,timeout=30);assert read.returncode==0,'remote_report_missing';report=json.loads(read.stdout);(folder/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
expected=9 if selection=='rejections-and-controls' else 6 if selection=='all-rejections' else 1
valid=process.returncode==0 and report['completed'] and report['cleanup'] and not report['cleanup_errors'] and report['skipped']==0 and len(report['checks'])==expected and all(v['status']=='passed' for v in report['checks']) and before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started and report['image']==image
value={'completed':bool(valid),'selection':selection,'target_image':image,'started_at_ns':started,'ended_at_ns':time.time_ns(),'exit_code':process.returncode,'before':before,'after':after,'report':report,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()};checkpoint.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'completed':bool(valid),'groups':len(report['checks']),'cleanup':report['cleanup'],'target_image':image,'served_image_unchanged':before['image']==after['image'],'source_files':len(before['source_sha256'])}));assert valid,'see_private_migration008_checkpoint'
