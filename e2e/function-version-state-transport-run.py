# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#livraison-et-limites
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#matrice-et-discriminants
"""Run the real nine-group campaign serially and independently recoup native state."""
import hashlib,json,runpy,subprocess,time
from pathlib import Path
r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');name='function-version-state-transport'
report=folder/(name+'.json');checkpoint=folder/(name+'-checkpoint.json');assert not report.exists() and not checkpoint.exists(),'retain_prior_attempt_before_replay'
before=r['snapshot'](str(report),False,include_adapter=True);credentials=r['private_credentials']();started=time.time_ns()
value={'completed':False,'started_at_ns':started,'before':before};checkpoint.write_text(json.dumps(value,indent=2)+'\n')
try:
 process=subprocess.run(['node','e2e/'+name+'.mjs'],input=credentials,capture_output=True,timeout=1200);credentials=None;output=process.stdout+process.stderr;exit_code=process.returncode
except subprocess.TimeoutExpired as error:
 credentials=None;output=(error.stdout or b'')+(error.stderr or b'');exit_code=None;value['failure']='campaign_timeout_no_automatic_replay'
log=folder/(name+'.log');log.write_bytes(output);print(output.decode(),end='')
after=r['snapshot'](str(report),False,include_adapter=True);campaign=json.loads(report.read_text()) if report.exists() else None
valid=exit_code==0 and campaign and campaign['completed'] and campaign['cleanup'] and not campaign['cleanup_errors'] and campaign['skipped']==0 and len(campaign['checks'])==9 and all(v['status']=='passed' for v in campaign['checks']) and len(campaign['calls'])==16 and len(campaign['gates'])==7 and all(v['restored'] for v in campaign['gates']) and before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started
value.update(ended_at_ns=time.time_ns(),exit_code=exit_code,after=after,report=campaign,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());checkpoint.write_text(json.dumps(value,indent=2)+'\n');assert valid,'inspect_state_transport_checkpoint_no_automatic_replay'
program='campaign='+repr(campaign)+'\n'+r'''
import hashlib,json,os,socket,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'));from control_database import read_control
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def cmd(args,timeout=90):return subprocess.check_output(args,text=True,timeout=timeout,cwd=root).strip()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
function,namespace=campaign['function_id'],campaign['namespace_id'];physical=json.loads(cmd(['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps({namespace:[function]})]));assert physical['completed'] and all(physical['physical'].values())
counts={};calls=[]
with read_control(root/'state/control.sqlite3') as db:
 assert len(list(db.execute('SELECT version FROM schema_migrations')))==8
 for label,sql in {'active_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'uploads':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments','operations':'SELECT count(*) FROM function_operations'}.items():counts[label]=db.execute(sql).fetchone()[0]
 assert not any(counts.values())
 expected=campaign['calls'];assert len(expected)==16 and db.execute("SELECT count(*) FROM invocations WHERE function_id=? AND state='succeeded'",(function,)).fetchone()[0]==16
 for v in expected:
  row=dict(db.execute('SELECT id,state,handler_started,requested_code_hash,resolved_code_hash FROM invocations WHERE id=? AND function_id=?',(v['id'],function)).fetchone());assert row['state']=='succeeded' and row['handler_started']==1 and row['requested_code_hash']==v['requested_code_hash'] and row['resolved_code_hash']==v['resolved_code_hash'];calls.append(row)
 initial=next(v['before'] for v in campaign['evidence'] if v['scenario']=='initial-versions');f=db.execute('SELECT first_published_code_hash,first_promoted_at FROM functions WHERE id=?',(function,)).fetchone();assert all(f[k]==initial['function'][k] for k in f.keys())
 rejected=[dict(v) for v in db.execute("SELECT id,state,error_code,requested_code_hash,resolved_code_hash FROM invocations WHERE function_id=? AND state!='succeeded'",(function,))];assert all(v['state']=='rejected' and v['error_code']=='version_unavailable' for v in rejected)
services=[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status']} for v in json.loads(cmd(D+['inspect','serverless-api','serverless-runtime-reference']))];assert all(v['health']=='healthy' for v in services)
official={n:sha(n) for n in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')};guards=[]
for g in campaign['gates']:
 unit=next(v['unit'] for v in g['events'] if v['event']=='guard-armed');p=Path('/run')/unit;identity=json.loads((p/'identity.json').read_text());assert identity['function_id']==function and identity['namespace_id']==namespace
 assert identity['container_id']==services[0]['id'] and identity['image']==services[0]['image'] and identity['reference']==[services[1][k] for k in ('id','image','started_at')] and identity['official_sha256']==official
 assert sha(p/'restore.py')==identity['restore_sha256'] and sha(p/'kill.py')==identity['kill_sha256'] and sha(root/'e2e/function-version-state-observer.py')==identity['operator_sha256'] and sha(root/'e2e/native_control_observer.py')==identity['native_observer_sha256']
 states={}
 for suffix in ('timer','service'):
  states[suffix]=dict(v.split('=',1) for v in cmd(['systemctl','show',unit+'.'+suffix,'--property=LoadState','--property=ActiveState','--property=MainPID']).splitlines());assert states[suffix]['ActiveState']=='inactive' and states[suffix].get('MainPID','0')=='0'
 try:current_birth=Path('/proc',str(identity['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:current_birth=None
 assert current_birth!=identity['helper_birth'],'native_observer_retained'
 restored=json.loads((p/('restored-independent.json' if g['mode']=='watchdog' else 'restored.json')).read_text());assert restored['healthy'] and restored['reference_unchanged'] and restored['stop_mutator_joined']
 proof={'unit':unit,'mode':g['mode'],'action':g['action'],'states':states,'identity':identity,'restored':restored,'helper_absent':True,'restore_sha256':sha(p/'restore.py'),'kill_program_sha256':sha(p/'kill.py')}
 if g['mode']=='watchdog':
  assert restored['independent'] and restored['observer_gone'] and restored['started_at']==identity['started_at'] and not (p/'kill-started.json').exists()
  journal=cmd(['journalctl','--no-pager','--output=cat','-u',unit+'.service','--lines=30']);assert '"independent": true' in journal and '"event": "restored"' in journal;proof['guard_journal']=journal
 else:
  kill=json.loads((p/'kill-result.json').read_text());assert kill['completed'] and kill['docker_client_joined'] and kill['container_id']==services[0]['id'] and kill['exit_code']==137
  assert restored['stop_receipt_sha256']==sha(p/'kill-result.json') and restored['started_at']!=identity['started_at'];proof['kill_receipt']=kill;proof['kill_receipt_sha256']=sha(p/'kill-result.json')
 guards.append(proof)
assert len(guards)==7 and len({v['unit'] for v in guards})==7 and sum(v['mode']=='watchdog' for v in guards)==1
assert {(v['action'],v['mode']) for v in guards if v['mode']!='watchdog'}=={(a,b) for a in ('promote','archive','delete') for b in ('before','after')}
assert guards[-1]['restored']['started_at']==services[0]['started_at']
inspection="""import hashlib,json
from pathlib import Path
r=Path('/app');files=[*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']
print(json.dumps({'backend':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'web':{str(p.relative_to(r/'web')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'web').rglob('*') if p.is_file()}}))
"""
embedded=json.loads(cmd(D+['exec','serverless-api','python','-B','-c',inspection]))
print(json.dumps({'completed':True,'physical':physical,'global_counts':counts,'calls':calls,'rejected_invocations':rejected,'services':services,'official_sha256':official,'guards':guards,'embedded':embedded}))
'''
p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=240)
if p.returncode:
 (folder/(name+'-native.log')).write_text(p.stdout+p.stderr);raise AssertionError('native_recoup_failed_see_private_log')
native=json.loads(p.stdout);assert native['completed'];previous=json.loads(Path('docs/evidence/function-version-unknown-first-dev-2026-11-09.json').read_text());assert native['embedded']==previous['native']['embedded'] and native['official_sha256']==previous['native']['official_sha256'] and all(native['services'][i][k]==previous['native']['services'][i][k] for i in range(2) for k in ('id','image','health')) and native['services'][1]['started_at']==previous['native']['services'][1]['started_at']
value.update(completed=True,native=native,native_collection_program=program,native_collection_program_sha256=hashlib.sha256(program.encode()).hexdigest());checkpoint.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'completed':True,'groups':9,'successful_invocations':16,'guards_finished':7,'control_cuts':6,'source_files':len(after['source_sha256']),'image':after['image'],'global_counts':native['global_counts']}))
