# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md#livraison-et-limites
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md
"""Serial real component/API regression, original reports preserved, native recoup."""
import hashlib,json,os,runpy,shutil,signal,subprocess,time
from pathlib import Path
from uuid import uuid4
r=runpy.run_path('e2e/execution-suite.py');b=Path('.local/e2e');name='function-version-cli-recovery-regressions008';report=b/(name+'.json');assert not report.exists(),'preserve_previous_regression_attempt'
value={'completed':False,'serial':True,'commands':[],'prerequisites':[],'started_at_ns':time.time_ns()}
def save():
 p=report.with_suffix('.pending');p.write_text(json.dumps(value,indent=2)+'\n');p.replace(report)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
LIVE=r'''
import hashlib,json,os,socket,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'));from control_database import read_control
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def cmd(args,timeout=90):return subprocess.check_output(args,text=True,timeout=timeout,cwd=root).strip()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
counts={}
with read_control(root/'state/control.sqlite3') as db:
 migrations=[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')];assert len(migrations)==8 and migrations[-1]=='008_function_versions.sql'
 for n,sql in {'active_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'uploads':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments','operations':'SELECT count(*) FROM function_operations'}.items():counts[n]=db.execute(sql).fetchone()[0]
 assert not any(counts.values()),'quiet_live_installation_required'
services=[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status']} for v in json.loads(cmd(D+['inspect','serverless-api','serverless-runtime-reference']))];assert all(v['health']=='healthy' for v in services)
for kind in ('validation','instance'):assert not cmd(D+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind='+kind]),'active_docker_consumer'
artifacts={str(p.relative_to(root/'state/artifacts')):sha(p) for p in sorted((root/'state/artifacts').rglob('*')) if p.is_file()}
state={'services':services,'global_counts':counts,'migrations':migrations,'official_sha256':{n:sha(n) for n in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},'original_artifacts':{'files':len(artifacts),'manifest_sha256':hashlib.sha256(json.dumps(artifacts,sort_keys=True).encode()).hexdigest()}}
'''
def native(program):
 p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=180)
 if p.returncode:
  (b/(name+'-native-error.log')).write_text(p.stdout+p.stderr);raise AssertionError('native_regression_recoup_failed')
 return json.loads(p.stdout)
save();baseline=native(LIVE+"\nprint(json.dumps(state))\n");previous=json.loads(Path('docs/evidence/function-version-publication-regressions-dev-2026-11-09.json').read_text());assert baseline['original_artifacts']==previous['native']['original_artifacts'] and baseline['official_sha256']==previous['native']['official_sha256']
value['live_before']=baseline;value['source_epoch']=r['source_hashes']();save()
archive=b/(name+'-prior-reports-'+uuid4().hex);archive.mkdir(mode=0o700);prior={}
for leaf in ('adapter-deploy.json','publication-recovery.json','dev-sso-sessions.json'):
 p=b/leaf
 if p.exists():
  target=archive/leaf;shutil.copyfile(p,target);prior[leaf]={'sha256':sha(target),'bytes':target.stat().st_size,'path':str(target)}
value['previous_reports']={'local':prior};save();credentials=r['private_credentials']();epoch=value['source_epoch'];image=None;adapter=None

def execute(case,private_input=None,count=True):
 global image,adapter
 label,command,path,is_remote=case;before=r['snapshot'](path,is_remote,include_adapter=True);assert before['source_sha256']==epoch
 if image is None:image=before['image'];adapter=before['adapter_images']
 assert before['image']==image and before['adapter_images']==adapter
 entry={'campaign':label,'command':command,'report_path':path,'report_remote':is_remote,'before':before,'started_at_ns':time.time_ns(),'exit_code':None};(value['commands'] if count else value['prerequisites']).append(entry);save();print(json.dumps({'campaign':label,'state':'running'}),flush=True)
 log=b/(name+'-'+label+'.log')
 capture_error=None
 with log.open('wb') as output:
  p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=10s','1200s',*command],cwd=r['ROOT'],stdin=subprocess.PIPE if private_input is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  entry['local_process_pid']=p.pid
  try:
   if private_input is not None:p.stdin.write(private_input);p.stdin.close();p.stdin=None
   for line in p.stdout:output.write(line);output.flush();print(line.decode(),end='',flush=True)
  except BaseException as error:
   capture_error=type(error).__name__;entry['capture_error']={'phase':'stdin-or-output','type':capture_error}
  finally:
   if p.stdin is not None:
    try:p.stdin.close()
    except BrokenPipeError as error:entry['stdin_close_error']=type(error).__name__;capture_error=capture_error or type(error).__name__
    p.stdin=None
   try:
    remaining,_=p.communicate(timeout=1220)
    if remaining:entry['remaining_output_sha256']=hashlib.sha256(remaining).hexdigest()
   except subprocess.TimeoutExpired:
    capture_error=capture_error or 'local_join_timeout';entry['join_outcome']='expired_unknown_remote_state'
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:entry['local_group_already_absent']=True
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:entry['local_process_joined']=False;save();raise AssertionError('local_process_not_joined_no_continuation') from None
   code=p.wait(timeout=10);entry['local_process_joined']=True
 entry.update(exit_code=code,ended_at_ns=time.time_ns(),log_sha256=sha(log));after=r['snapshot'](path,is_remote,include_adapter=True);entry['after']=after;save()
 assert capture_error is None and code==0,'campaign_or_capture_stopped_no_automatic_replay'
 assert after['source_sha256']==epoch and after['image']==image and after['adapter_images']==adapter
 assert before['report']['sampled_at_ns']<=after['report']['mtime_ns']<=after['report']['sampled_at_ns'],'fresh_report_required'
 d=r['read_report'](path,is_remote,after['report']['sha256']);entry['report']=d
 if count:entry['passed_groups']=r['verify_report'](label,path,is_remote,after['report']['sha256'])
 else:assert d['completed'] and d['authenticated'] and d['independent_sessions']==2 and d['platform_cookies_only'] and d['purpose']=='suite-start'
 entry['fresh_report_verified']=True;save()

execute(('dev-sso-sessions',['node','e2e/dev-sso-sessions.mjs'],'.local/e2e/dev-sso-sessions.json',False),credentials,False);credentials=None
for label in ('adapter-deploy','publication-recovery'):execute(next(v for v in r['CASES'] if v[0]==label))
assert len(value['commands'])==2 and sum(v['passed_groups'] for v in value['commands'])==11 and len(value['prerequisites'])==1
campaigns={v['report']['namespace_id']:v['report']['function_ids'] for v in value['commands']};calls=[c for v in value['commands'] for c in v['report']['invocations']];assert len(campaigns)==2 and sum(map(len,campaigns.values()))==22 and len(calls)==len({v['id'] for v in calls})==76
gates=next(v['report']['gates'] for v in value['commands'] if v['campaign']=='publication-recovery');assert len(gates)==2
program='campaigns='+repr(campaigns)+'\ncalls='+repr(calls)+'\ngates='+repr(gates)+'\n'+LIVE+r'''
physical=json.loads(cmd(['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps(campaigns)]));assert physical['completed'] and all(physical['physical'].values())
records=[]
with read_control(root/'state/control.sqlite3') as db:
 for v in calls:
  row=dict(db.execute('SELECT id,function_id,state,handler_started,requested_code_hash,resolved_code_hash FROM invocations WHERE id=? AND function_id=?',(v['id'],v['function_id'])).fetchone());assert row['state']=='succeeded' and row['handler_started']==1 and row['requested_code_hash']==v['requested_code_hash'] and row['resolved_code_hash']==v['resolved_code_hash'];records.append(row)
 identifiers=[k for values in campaigns.values() for k in values];marks=','.join('?' for _ in identifiers);assert db.execute('SELECT count(*) FROM invocations WHERE state=\'succeeded\' AND function_id IN ('+marks+')',identifiers).fetchone()[0]==76
 proof_containers=[]
for identifier in cmd(D+['ps','-aq','--filter','label=com.docker.compose.service=control']).split():
 row=json.loads(cmd(D+['inspect',identifier]))[0]
 if row['Config']['Labels'].get('com.docker.compose.project','').startswith('p2enjoy-control-proof-'):proof_containers.append(identifier)
assert not proof_containers,'component_proof_container_retained'
guards=[]
for gate in gates:
 assert gate['restored'] and gate['mode'] in ('receiving','validating')
 armed=next(v for v in gate['events'] if v['event']=='guard-armed');unit=armed['unit'];assert __import__('re').fullmatch('serverless-restore-publication-upload-[0-9a-f]{32}',unit)
 folder=Path('/run')/unit;item=json.loads((folder/'identity.json').read_text());assert item['namespace_id'] in campaigns and item['function_id'] in campaigns[item['namespace_id']]
 for leaf,key in [('restore.py','restore_sha256'),('kill.py','kill_sha256')]:assert sha(folder/leaf)==item[key]
 assert sha(root/'e2e/publication-recovery-operator.py')==item['operator_sha256'] and sha(root/'e2e/native_control_observer.py')==item['native_observer_sha256']
 cut=json.loads((folder/'interrupted.json').read_text());kill=json.loads((folder/'kill-result.json').read_text());assert cut['native_signal']==9 and cut['exit_code']==137 and kill['completed'] and kill['docker_client_joined'] and kill['exit_code']==137
 receipt=json.loads((folder/('restored-independent.json' if gate['mode']=='validating' else 'restored.json')).read_text());assert receipt['healthy'] and receipt['reference_unchanged'] and receipt['stop_mutator_joined'] and receipt['stop_receipt_sha256']==sha(folder/'kill-result.json')
 if gate['mode']=='validating':assert receipt['independent'] and receipt['observer_gone']
 states={}
 for suffix in ('timer','service'):
  p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=ActiveState','--property=LoadState','--property=MainPID'],capture_output=True,text=True,timeout=10);v=dict(line.split('=',1) for line in p.stdout.splitlines());assert v.get('ActiveState')=='inactive' and v.get('MainPID','0')=='0';states[suffix]=v
 try:assert Path('/proc',str(item['helper_pid']),'stat').read_text().rsplit(')',1)[1].split()[19]!=item['helper_birth'],'helper_still_alive'
 except FileNotFoundError:pass
 journal=cmd(['journalctl','-u',unit+'.service','--no-pager','-o','cat']);guards.append({'unit':unit,'phase':gate['mode'],'cut':cut,'stop':kill,'restore':receipt,'states':states,'journal_sha256':hashlib.sha256(journal.encode()).hexdigest(),'identity_sha256':sha(folder/'identity.json'),'helper_gone':True})
assert len(guards)==2 and {v['phase'] for v in guards}=={'receiving','validating'}
inspection="""import hashlib,json
from pathlib import Path
r=Path('/app');files=[*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']
print(json.dumps({'backend':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'web':{str(p.relative_to(r/'web')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'web').rglob('*') if p.is_file()}}))
"""
embedded=json.loads(cmd(D+['exec','serverless-api','python','-B','-c',inspection]));state.update(completed=True,physical=physical,guards=guards,invocations=records,embedded=embedded,component_containers_retained=proof_containers);print(json.dumps(state))
'''
final=native(program)
for old,new in zip(baseline['services'],final['services']):
 assert old['id']==new['id'] and old['image']==new['image'] and old['health']==new['health']=='healthy'
 if old['id']==baseline['services'][0]['id']:assert old['started_at']!=new['started_at']
 else:assert old==new
assert final['official_sha256']==baseline['official_sha256'] and final['original_artifacts']==baseline['original_artifacts'] and final['embedded']==previous['native']['embedded']
value.update(completed=True,ended_at_ns=time.time_ns(),groups=11,native=final,native_collection_program=program,native_collection_program_sha256=hashlib.sha256(program.encode()).hexdigest());save();print(json.dumps({'completed':True,'groups':11,'successful_invocations':76,'functions_purged':22,'source_files':len(epoch),'image':image,'same_control_image_and_id':True}),flush=True)
