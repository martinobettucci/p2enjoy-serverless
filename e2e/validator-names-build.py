# @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#commandes-reproductibles-du-banc
# @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
import hashlib,json,runpy,subprocess,time
from pathlib import Path
r=runpy.run_path('e2e/execution-suite.py');base=Path('.local/e2e');path=base/'validator-names-build.json';assert not path.exists();before=r['snapshot'](str(path),False,include_adapter=True);initial=json.loads((base/'validator-names-before-build.json').read_text());assert before['image']==initial['old_control_image'];value={'completed':False,'before':before,'started_at_ns':time.time_ns()};path.write_text(json.dumps(value,indent=2)+'\n')
script='expected_image='+repr(before['image'])+'\n'+'''
import hashlib,json,socket,subprocess,time,uuid
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');d=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def cmd(a,timeout=30):return subprocess.check_output(a,text=True,timeout=timeout)
services=json.loads(cmd(d+['inspect','serverless-api','serverless-runtime-reference']));assert services[0]['Image']==expected_image and all(v['State']['Health']['Status']=='healthy' for v in services)
inspection="""import hashlib,json
from pathlib import Path
r=Path('/app');files=[*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']
print(json.dumps({'backend':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'web':{str(p.relative_to(r/'web')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'web').rglob('*') if p.is_file()}}))
"""
old=json.loads(cmd(d+['exec','serverless-api','python','-B','-c',inspection]))
print(json.dumps({'event':'before-build','old_content':old}),flush=True)
p=subprocess.run(['timeout','--signal=TERM','--kill-after=15s','780s','runuser','-u','spark-docker','--','env','DOCKER_HOST=unix:///run/user/1001/docker.sock','bash','control/dev.sh','build'],cwd=root)
assert p.returncode==0,'control_build_failed'
image=cmd(d+['image','inspect','p2enjoy-control:dev','--format','{{.Id}}']).strip();assert image!=expected_image
current=json.loads(cmd(d+['inspect','serverless-api','serverless-runtime-reference']));assert all([a['Id'],a['Image'],a['State']['StartedAt']]==[b['Id'],b['Image'],b['State']['StartedAt']] for a,b in zip(services,current))
name='serverless-validator-image-inspector-'+uuid.uuid4().hex
new=json.loads(cmd(d+['run','--rm','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','128m','--cpus','0.5','--pids-limit','32','--entrypoint','python',image,'-B','-c',inspection]))
expected={str(p.relative_to(root/'control')):hashlib.sha256(p.read_bytes()).hexdigest() for folder,pattern in [('app','*.py'),('migrations','*.sql')] for p in (root/'control'/folder).glob(pattern)};expected['function_code_hash.py']=hashlib.sha256((root/'function_code_hash.py').read_bytes()).hexdigest();assert new['backend']==expected
assert old['web']==new['web'],'compiled_web_changed';assert [n for n in old['backend'] if old['backend'][n]!=new['backend'][n]]==['app/validator.py']
assert not cmd(d+['ps','-aq','--filter','name=^/'+name+'$']).strip()
cmd(d+['tag',image,'p2enjoy-control:validator-names-candidate'])
print(json.dumps({'event':'build-complete','completed':True,'new_image':image,'old_image':expected_image,'services_unchanged':True,'compiled_web_unchanged':True,'only_backend_change':'app/validator.py','old_content':old,'new_content':new,'inspector_name':name,'inspector_absent':True}),flush=True)
'''
p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=script,text=True,capture_output=True,timeout=900);log=base/'validator-names-build.log';log.write_text(p.stdout+p.stderr);events=[]
for line in p.stdout.splitlines():
 try:
  v=json.loads(line)
  if isinstance(v,dict) and v.get('event'):events.append(v)
 except ValueError:pass
value.update(exit_code=p.returncode,finished_at_ns=time.time_ns(),events=events,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());after=r['snapshot'](str(path),False,include_adapter=True);value['after']=after
assert before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images']
if p.returncode==0 and events and events[-1].get('completed'):value.update(events[-1]);value['completed']=True
path.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'completed':value['completed'],'exit_code':p.returncode,'new_image':value.get('new_image'),'services_unchanged':value.get('services_unchanged'),'source_files':len(before['source_sha256']),'log_sha256':value['log_sha256']}));assert value['completed'],'inspect_build_log_no_automatic_restart'
