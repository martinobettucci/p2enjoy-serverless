# @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#commandes-reproductibles-du-banc
# @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
import hashlib,json,runpy,shlex,shutil,subprocess,time,uuid
from pathlib import Path
r=runpy.run_path('e2e/execution-suite.py');b=Path('.local/e2e');target=json.loads((b/'validator-names-checkpoint.json').read_text());assert target['completed'] and target['report']['cleanup'];path=b/'validator-names-regressions.json';assert not path.exists();archive=b/('validator-names-related-before-'+str(time.time_ns()));archive.mkdir(mode=0o700);archived={}
for name in ['function-versions-api.json','function-versions-cli.json']:
 p=b/name;assert json.loads(p.read_text())['completed'];shutil.copyfile(p,archive/name);archived[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'archive':str(archive/name)}
program='suffix='+repr(uuid.uuid4().hex)+'\n'+'''
import hashlib,json,socket
from pathlib import Path
assert socket.gethostname()=='infra-serverless';root=Path('/srv/p2enjoy-serverless');source=root/'runtime/validation-proof.json';raw=source.read_bytes();backup=root/'qualification-history'/('validator-names-related-'+suffix);backup.mkdir(mode=0o700);(backup/source.name).write_bytes(raw);print(json.dumps({'path':str(backup/source.name),'sha256':hashlib.sha256(raw).hexdigest()}))
'''
p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=60);assert p.returncode==0,p.stderr[-1000:];archived['runtime-validation']=json.loads(p.stdout)
proof={'completed':False,'serial':True,'skipped':0,'campaigns':[],'previous_reports':archived,'started_at_ns':time.time_ns()}
def save():path.write_text(json.dumps(proof,indent=2)+'\n')
save();cases=[('runtime-validation',r['remote'](['env','DOCKER_HOST=unix:///run/user/1001/docker.sock','bash',r['REMOTE']+'runtime/dev.sh','test']),'runtime/validation-proof.json',True,36),('function-versions-api',['node','e2e/function-versions-api.mjs'],'.local/e2e/function-versions-api.json',False,12),('function-versions-cli',['node','e2e/function-versions-cli.mjs'],'.local/e2e/function-versions-cli.json',False,5)]
for name,command,report,remote,count in cases:
 before=r['snapshot'](report,remote,include_adapter=True);assert before['source_sha256']==target['after']['source_sha256'];assert before['image']==target['after']['image'] and before['adapter_images']==target['after']['adapter_images'];started=time.time_ns();record={'name':name,'completed':False,'before':before,'started_at_ns':started};proof['campaigns'].append(record);save();p=subprocess.run(command,capture_output=True,text=True,timeout=900);log=b/('validator-names-'+name+'.log');log.write_text(p.stdout+p.stderr);print(p.stdout,end='',flush=True);after=r['snapshot'](report,remote,include_adapter=True);record.update(after=after,exit_code=p.returncode,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());save()
 if remote:
  raw=subprocess.check_output(r['SSH']+['root@10.77.0.24','cat',r['REMOTE']+report]);(b/('validator-names-'+name+'.json')).write_bytes(raw);value=json.loads(raw)
 else:value=json.loads(Path(report).read_text())
 valid=p.returncode==0 and value['completed'] and value.get('failed',0)==0 and value['skipped']==0 and len(value['checks'])==count and all(v['status']=='passed' for v in value['checks']) and before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images'] and after['report']['mtime_ns']>started
 if not remote:valid=valid and value['cleanup'] and not value['cleanup_errors']
 record.update(completed=bool(valid),groups=len(value['checks']),report_sha256=after['report']['sha256']);save();assert valid,'related_campaign_failed_'+name
proof.update(completed=True,groups=53,finished_at_ns=time.time_ns());save();print(json.dumps({'completed':True,'groups':53,'campaigns':3,'source_files':len(target['after']['source_sha256'])}))
