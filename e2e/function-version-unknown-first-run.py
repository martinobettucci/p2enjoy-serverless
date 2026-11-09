# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UNKNOWN_FIRST.md#matrice-publique-et-marqueurs
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UNKNOWN_FIRST.md#livraison-et-limites
"""One guarded real historical window; credentials stay on private stdin."""
import hashlib,json,runpy,subprocess,sys,time
from pathlib import Path
r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');variant=sys.argv[1];options=sys.argv[2:]
assert variant in ('preserved-first','unknown-first-tombstone') and options in ([],['--restore-with-guard'])
assert not options or variant=='unknown-first-tombstone'
name='function-version-history-'+variant+('-guard' if options else '');report=folder/(name+'.json');checkpoint=folder/(name+'-checkpoint.json');assert not report.exists() and not checkpoint.exists(),'preserve_previous_history_attempt'
before=r['snapshot'](str(report),False,include_adapter=True);assert before['image']=='sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4'
credentials=r['private_credentials']();started=time.time_ns();checkpoint.write_text(json.dumps({'completed':False,'started_at_ns':started,'before':before},indent=2)+'\n')
p=subprocess.run(['node','e2e/function-version-unknown-first.mjs',variant,*options],input=credentials,capture_output=True,timeout=1200);credentials=None
log=folder/(name+'.log');log.write_bytes(p.stdout+p.stderr);print(p.stdout.decode(),end='')
after=r['snapshot'](str(report),False,include_adapter=True);value=json.loads(report.read_text()) if report.exists() else None;expected=3 if options else 7
valid=p.returncode==0 and value and value['completed'] and value['cleanup'] and not value['cleanup_errors'] and value['skipped']==0 and len(value['checks'])==expected and all(v['status']=='passed' for v in value['checks']) and before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started
checkpoint.write_text(json.dumps({'completed':bool(valid),'started_at_ns':started,'ended_at_ns':time.time_ns(),'exit_code':p.returncode,'before':before,'after':after,'report':value,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()},indent=2)+'\n');assert valid,'inspect_history_checkpoint_no_automatic_replay';print(json.dumps({'completed':True,'groups':expected,'variant':variant,'independent':bool(options),'source_files':len(after['source_sha256']),'image':after['image'],'original_installation_restored':True}))
