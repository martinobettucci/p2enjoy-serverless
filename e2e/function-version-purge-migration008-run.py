# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#matrice-réelle
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#livraison-et-limites
"""Run one real historical purge window, with sources frozen and private SSO stdin."""
import hashlib,json,runpy,subprocess,sys,time
from pathlib import Path

r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');source,phase=sys.argv[1:3];options=sys.argv[3:]
assert source in ('006','007') and phase in ('volumes','artifacts') and options in ([],['--restore-with-guard'])
stem='function-version-purge-'+source+'-to-008-upgrade-'+phase+('-guard' if options else '')
report=folder/(stem+'.json');checkpoint=folder/(stem+'-checkpoint.json');assert not report.exists() and not checkpoint.exists(),'preserve_previous_purge_migration_campaign'
before=r['snapshot'](str(report),False,include_adapter=True);assert before['image']=='sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4'
credentials=r['private_credentials']();started=time.time_ns();checkpoint.write_text(json.dumps({'completed':False,'before':before,'started_at_ns':started},indent=2)+'\n')
command=['node','e2e/function-version-purge-upgrade.mjs','upgrade',phase,'--target-schema008']+(['--source-schema007'] if source=='007' else [])+options
p=subprocess.run(command,input=credentials,capture_output=True,timeout=1200);credentials=None
log=folder/(stem+'.log');log.write_bytes(p.stdout+p.stderr);print(p.stdout.decode(),end='')
after=r['snapshot'](str(report),False,include_adapter=True);value=json.loads(report.read_text()) if report.exists() else None;count=3 if options else 4
valid=p.returncode==0 and value and value['completed'] and value['cleanup'] and not value['cleanup_errors'] and value['skipped']==0 and value['source_schema']==source and value['target_schema']=='008' and len(value['checks'])==count and all(v['status']=='passed' for v in value['checks']) and before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started
checkpoint.write_text(json.dumps({'completed':bool(valid),'started_at_ns':started,'ended_at_ns':time.time_ns(),'exit_code':p.returncode,'before':before,'after':after,'report':value,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()},indent=2)+'\n');assert valid,'inspect_failed_purge_migration_report_no_automatic_replay'
print(json.dumps({'completed':True,'source_schema':source,'target_schema':'008','phase':phase,'groups':count,'source_files':len(after['source_sha256']),'image':after['image'],'original_installation_restored':True}))
