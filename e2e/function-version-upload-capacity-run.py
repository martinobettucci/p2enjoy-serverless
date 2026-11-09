# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#preuves-et-limites
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#preuves-et-limites
"""Run one serial real campaign, freeze source identity, then recoup physical cleanup."""
import hashlib,json,runpy,subprocess,time
from pathlib import Path

r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');name='function-version-upload-capacity'
report=folder/(name+'.json');checkpoint=folder/(name+'-checkpoint.json')
assert not report.exists() and not checkpoint.exists(),'retain_prior_attempt_before_replay'
before=r['snapshot'](str(report),False,include_adapter=True);started=time.time_ns()
(folder/(name+'-before.json')).write_text(json.dumps(before,indent=2)+'\n')
process=subprocess.run(['node','e2e/'+name+'.mjs'],capture_output=True,text=True,timeout=480)
log=folder/(name+'.log');log.write_text(process.stdout+process.stderr);print(process.stdout,end='')
after=r['snapshot'](str(report),False,include_adapter=True)
(folder/(name+'-after.json')).write_text(json.dumps(after,indent=2)+'\n')
value=json.loads(report.read_text());valid=process.returncode==0 and value['completed'] and value['cleanup'] and not value['cleanup_errors'] and not value['request_join_errors'] and len(value['checks'])==4 and all(v['status']=='passed' for v in value['checks']) and value['skipped']==0 and before['image']==after['image'] and before['source_sha256']==after['source_sha256'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started
result={'completed':False,'started_at_ns':started,'ended_at_ns':time.time_ns(),'exit_code':process.returncode,'before':before,'after':after,'report':value,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
checkpoint.write_text(json.dumps(result,indent=2)+'\n');assert valid,'campaign_failed_see_private_report'
campaigns={value['namespace_id']:value['function_ids']}
program='campaigns='+repr(campaigns)+'\ncalls='+repr([v for v in value['evidence'] if 'invocation_id' in v])+'\n'+'''
import hashlib,json,os,socket,subprocess,sys,urllib.request
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'));from control_database import read_control
physical=json.loads(subprocess.check_output(['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps(campaigns)],text=True,timeout=90))
assert physical['completed'] and all(physical['physical'].values())
counts={};invocations=[]
with read_control(root/'state/control.sqlite3') as db:
 migrations=[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')];assert len(migrations)==8
 for name,sql in {'active_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'active_deployments':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments','operations':'SELECT count(*) FROM function_operations'}.items():counts[name]=db.execute(sql).fetchone()[0]
 assert not any(counts.values())
 function=next(iter(campaigns.values()))[0]
 assert db.execute('SELECT count(*) FROM invocations WHERE function_id=?',(function,)).fetchone()[0]==4
 for call in calls:
  row=db.execute('SELECT id,state,handler_started,requested_code_hash,resolved_code_hash FROM invocations WHERE id=? AND function_id=?',(call['invocation_id'],function)).fetchone()
  assert row and row['state']=='succeeded' and row['handler_started'] and row['resolved_code_hash']==call['code_hash']
  assert row['requested_code_hash']==(call['code_hash'] if call['marker']=='pilot' else None);invocations.append(dict(row))
 assert len(invocations)==4
command=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
assert not subprocess.check_output(command+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind=validation'],text=True,timeout=30).strip()
services=[{'name':v['Name'],'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status']} for v in json.loads(subprocess.check_output(command+['inspect','serverless-api','serverless-runtime-reference'],text=True,timeout=30))]
inspection="""import hashlib,json
from pathlib import Path
root=Path('/app');files=[*root.joinpath('app').glob('*.py'),*root.joinpath('migrations').glob('*.sql'),root/'function_code_hash.py']
print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))
"""
backend=json.loads(subprocess.check_output(command+['exec','serverless-api','python','-B','-c',inspection],text=True,timeout=30))
health={}
for domain in ('serverless.lelabs.tech','functions.lelabs.tech'):
 with urllib.request.urlopen('https://'+domain+'/healthz',timeout=15) as response:assert response.status==200;health[domain]=json.load(response)
print(json.dumps({'completed':True,'physical':physical,'global_counts':counts,'invocations':invocations,'migrations':migrations,'services':services,'backend_sha256':backend,'public_health':health,'official_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')}}))
'''
p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=180)
assert p.returncode==0,'native_collection_failed';native=json.loads(p.stdout)
expected={str(p.relative_to(Path('control'))):hashlib.sha256(p.read_bytes()).hexdigest() for directory,pattern in [('control/app','*.py'),('control/migrations','*.sql')] for p in Path(directory).glob(pattern)}
expected['function_code_hash.py']=hashlib.sha256(Path('function_code_hash.py').read_bytes()).hexdigest();assert native['backend_sha256']==expected
preserved=next(v['preserved'] for v in value['evidence'] if 'preserved' in v)
assert native['services']==preserved['services'] and native['official_sha256']==preserved['official_sha256']
result.update(completed=True,native=native,ended_at_ns=time.time_ns());checkpoint.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'completed':True,'groups':4,'invocations':4,'physically_purged':1,'source_files':len(before['source_sha256']),'image':after['image'],'global_counts':native['global_counts']}))
