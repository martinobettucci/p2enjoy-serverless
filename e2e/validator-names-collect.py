# @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#commandes-reproductibles-du-banc
# @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
import hashlib,json,runpy,subprocess
from pathlib import Path
r=runpy.run_path('e2e/execution-suite.py');b=Path('.local/e2e');target=json.loads((b/'validator-names.json').read_text());api=json.loads((b/'function-versions-api.json').read_text());cli=json.loads((b/'function-versions-cli.json').read_text());reg=json.loads((b/'validator-names-regressions.json').read_text());assert reg['completed'] and all(v['completed'] for v in (target,api,cli))
reports=[target,api,cli];campaigns={v['namespace_id']:v['function_ids'] for v in reports};assert len(campaigns)==3;unit=target['guard_unit'];expected={str(p.relative_to(Path('control'))):hashlib.sha256(p.read_bytes()).hexdigest() for directory,pattern in [('control/app','*.py'),('control/migrations','*.sql')] for p in Path(directory).glob(pattern)};expected['function_code_hash.py']=hashlib.sha256(Path('function_code_hash.py').read_bytes()).hexdigest();build=json.loads((b/'validator-names-build.json').read_text());before=json.loads((b/'validator-names-before-build.json').read_text())
program='campaigns='+repr(campaigns)+'\nunit='+repr(unit)+'\nreports='+repr(reports)+'\n'+'''
import hashlib,json,os,socket,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless';root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'));from control_database import read_control
physical=json.loads(subprocess.check_output(['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps(campaigns)],text=True,timeout=90));assert physical['completed'] and all(physical['physical'].values())
result={'completed':False,'physical':physical,'global_counts':{},'target_invocations':[],'all_campaign_invocation_states':{}}
with read_control(root/'state/control.sqlite3') as db:
 result['migrations']=[x[0] for x in db.execute('SELECT version FROM schema_migrations ORDER BY version')];assert len(result['migrations'])==8
 for name,sql in {'active_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'active_deployments':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments','operations':'SELECT count(*) FROM function_operations'}.items():result['global_counts'][name]=db.execute(sql).fetchone()[0]
 assert not any(result['global_counts'].values())
 for report in reports:
  for function in report['function_ids']:
   assert not db.execute("SELECT 1 FROM function_versions WHERE function_id=? AND state!='deleted'",(function,)).fetchone()
   result['all_campaign_invocation_states'][function]={v[0]:v[1] for v in db.execute('SELECT state,count(*) FROM invocations WHERE function_id=? GROUP BY state',(function,))}
 for call in [x for x in reports[0]['evidence'] if 'invocation_id' in x]:
  row=db.execute('SELECT id,state,handler_started,requested_code_hash,resolved_code_hash FROM invocations WHERE id=? AND function_id=?',(call['invocation_id'],reports[0]['function_ids'][0])).fetchone();assert row and row['state']=='succeeded' and row['handler_started'] and row['requested_code_hash'] is None and row['resolved_code_hash']==call['code_hash'];result['target_invocations'].append(dict(row))
 assert len(result['target_invocations'])==5
folder=Path('/run')/unit;identity=json.loads((folder/'identity.json').read_text());restored=json.loads((folder/'restored.json').read_text());assert restored['completed'] and restored['trigger']=='explicit';assert hashlib.sha256((folder/'recover.py').read_bytes()).hexdigest()==identity['recover_sha256'];result['guard']={'identity':identity,'restored':restored,'restored_sha256':hashlib.sha256((folder/'restored.json').read_bytes()).hexdigest(),'states':{}}
for suffix in ('timer','service'):
 p=subprocess.run(['systemctl','show',unit+'.'+suffix,'--property=LoadState','--property=ActiveState','--property=SubState','--property=MainPID'],capture_output=True,text=True,timeout=10);v=dict(line.split('=',1) for line in p.stdout.splitlines());assert v.get('MainPID','0')=='0' and v.get('ActiveState')=='inactive';result['guard']['states'][suffix]=v
result['official_sha256']={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in identity['official_sha256']};assert result['official_sha256']==identity['official_sha256']
d=identity['docker'];result['all_installation_validation_containers']=subprocess.check_output(d+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind=validation'],text=True,timeout=30).split();assert not result['all_installation_validation_containers'];services=json.loads(subprocess.check_output(d+['inspect','serverless-api','serverless-runtime-reference'],text=True,timeout=30));result['containers']={v['Name']:{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status']} for v in services};assert all(v['health']=='healthy' for v in result['containers'].values());assert services[0]['Id']==restored['control_id'] and services[0]['Image']==identity['new_image'];assert [services[1]['Id'],services[1]['Image'],services[1]['State']['StartedAt']]==identity['reference']
inspection="""import hashlib,json
from pathlib import Path
r=Path('/app');files=[*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']
print(json.dumps({'backend':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'web':{str(p.relative_to(r/'web')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'web').rglob('*') if p.is_file()}}))
"""
result['embedded']=json.loads(subprocess.check_output(d+['exec','serverless-api','python','-B','-c',inspection],text=True,timeout=30));result['completed']=True;print(json.dumps(result))
'''
p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=180);assert p.returncode==0,p.stderr[-1800:];v=json.loads(p.stdout);assert v['embedded']['backend']==expected;assert v['embedded']==build['new_content'];assert v['official_sha256']==before['official_sha256'];assert v['containers']['/serverless-runtime-reference']['id']==before['containers']['/serverless-runtime-reference']['id'];assert v['containers']['/serverless-runtime-reference']['started_at']==before['containers']['/serverless-runtime-reference']['started_at'];assert v['containers']['/serverless-api']['image']==build['new_image']
for report in (target,):
 purge=next(x['purged'] for x in report['evidence'] if 'purged' in x);assert v['physical']['functions'][purge['function_id']]['operation_id']==purge['operation_id']
component=json.loads((b/'validator-names-runtime-validation.json').read_text());named=[x['named_validation'] for x in target['evidence'] if 'named_validation' in x];assert len(named)==3 and {x['validator']['image'] for x in named}=={component['image_id']}
path=b/'validator-names-native.json';assert not path.exists();path.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'completed':True,'functions_physically_purged':sum(map(len,campaigns.values())),'target_invocations':5,'backend_files':len(expected),'global_counts':v['global_counts'],'guard_inactive':True}))
