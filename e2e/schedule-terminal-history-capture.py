# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-des-tirs-terminaux-et-générations-retirées
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-des-tirs-terminaux-et-générations-retirées
"""Preserve authentic terminal/retired witnesses on DEV; never edit live data."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parent.parent
NATIVE = r'''
import hashlib,json,os,re,shlex,shutil,signal,socket,sqlite3,stat,subprocess,sys,time
from contextlib import closing
from pathlib import Path
from uuid import uuid4
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');control=root/'state/control.sqlite3'
sys.path.insert(0,str(root/'e2e'))
from control_database import read_control,control_owner
checks=[];folder=None;stage='preflight'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  while chunk:=stream.read(1024*1024):h.update(chunk)
 return h.hexdigest()
def inventory(directory):
 result={}
 for path in sorted(directory.rglob('*')):
  info=path.lstat();assert stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode),'artifact_type'
  if stat.S_ISREG(info.st_mode):result[str(path.relative_to(directory))]={'sha256':sha(path),'bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode)}
 return result
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def docker(*args):return subprocess.check_output(D+list(args),text=True,timeout=25)
def services():
 rows=json.loads(docker('inspect','serverless-api','serverless-runtime-reference'))
 result=[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'running':v['State']['Running'],'health':v['State']['Health']['Status']} for v in rows]
 assert all(v['running'] and v['health']=='healthy' for v in result),'services_not_healthy'
 return result
ids=expected['function_ids'];marks=','.join('?' for _ in ids)
def witnesses(db):
 def matching(table,rows):
  result=[]
  for row in rows:
   assert all(re.fullmatch('[a-z_]+',k) for k in row),'invalid_column_name'
   keys=list(row);query='SELECT '+','.join(keys)+' FROM '+table+' WHERE id=?'
   found=db.execute(query,(row['id'],)).fetchone();assert found and dict(found)==row,'witness_changed_'+table
   result.append(dict(found))
  return result
 result={name:matching(table,expected[name]) for name,table in [('functions','functions'),('generations','schedule_generations'),('firings','schedule_firings'),('invocations','invocations')]}
 assert all(v['purged_at'] and v['deleted_at'] for v in result['functions'])
 assert len(result['generations'])==2 and all(v['retired_at'] for v in result['generations'])
 assert len(result['firings'])==len(result['invocations'])==1
 firing=result['firings'][0];call=result['invocations'][0]
 assert firing['state']==call['state']=='succeeded' and firing['completed_at'] and call['handler_started'] and call['completed_at']
 assert firing['invocation_id']==call['id'] and call['schedule_firing_id']==firing['id'] and call['resolved_code_hash']==firing['code_hash']
 assert all(db.execute('SELECT count(*) FROM '+table+' WHERE function_id IN ('+marks+')',ids).fetchone()[0]==len(result[key]) for table,key in [('schedule_generations','generations'),('schedule_firings','firings'),('invocations','invocations')]),'extra_witness_rows'
 # Select the actual generation referenced by the firing, independent of row order.
 runtime=db.execute('SELECT r.image_id FROM schedule_generations g JOIN revisions r ON r.id=g.revision_id WHERE g.id=?',(firing['generation_id'],)).fetchone()
 assert runtime and runtime[0]==expected['images']['runtime']['image'],'runtime_image_mismatch'
 result['runtime_image']=runtime[0]
 return result

def quiet(db):
 for query in ["SELECT count(*) FROM functions WHERE deleted_at IS NULL", "SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'SELECT count(*) FROM execution_instances','SELECT count(*) FROM function_operations','SELECT coalesce(sum(reserved_bytes),0) FROM deployments']:
  assert db.execute(query).fetchone()[0]==0,'installation_not_quiet'

def main():
 global folder,stage
 signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('native_capture_deadline')));signal.alarm(180)
 before_services=services();assert before_services==expected['services'] and before_services[0]['image']==expected['images']['control']['image'],'services_changed_since_proof'
 official={n:sha(Path(n)) for n in ['/etc/spark/env','/run/spark/secrets','/etc/spark/routes']};assert official==expected['official_sha256']
 running=set(docker('ps','-q','--no-trunc').split());assert running=={v['id'] for v in before_services},'unexpected_running_container'
 with read_control(control) as db:
  db.execute('BEGIN');quiet(db);live=witnesses(db)
  namespace=db.execute('SELECT name FROM namespaces WHERE id=?',(expected['namespace_id'],)).fetchone()
  assert namespace and re.fullmatch('scheduled-functions-[0-9a-f]{8}',namespace[0])
  actual={v[0] for v in db.execute('SELECT f.id FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=?',(expected['namespace_id'],))};assert actual==set(ids)
 reference=root/'qualification-history'/expected['image_capture_id'];assert reference.is_dir() and not reference.is_symlink()
 preservation=json.loads((reference/'preservation.json').read_text());assert preservation['images']==expected['images']
 for role,row in expected['images'].items():
  path=reference/(role+'-image.tar');info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o400 and info.st_size==row['bytes'] and sha(path)==row['archive_sha256'],'image_archive_changed'
 values={}
 for line in Path('/etc/spark/env').read_text().splitlines():
  fields=shlex.split(line,comments=True)
  if len(fields)==1 and fields[0].startswith('SERVERLESS_STORAGE_ROOT_HOST='):values['storage_root']=fields[0].split('=',1)[1]
 registry=Path(values['storage_root'])/'registry.sqlite3'
 with control_owner(control),closing(sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True)) as db:assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0
 checks.append({'name':'Vrais témoins purgés et retirés identiques à la preuve, installation au repos','status':'passed'})
 stage='native-backups';folder=root/'qualification-history'/('schedule-terminal-history-'+uuid4().hex);folder.mkdir(mode=0o700);owner=control.stat();os.chown(folder,owner.st_uid,owner.st_gid)
 with read_control(control) as source,closing(sqlite3.connect(folder/'control.sqlite3')) as target:
  source.backup(target);assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok';target.row_factory=sqlite3.Row;quiet(target);assert witnesses(target)==live
 with control_owner(control),closing(sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(folder/'registry.sqlite3')) as target:
  assert source.execute('SELECT count(*) FROM leases').fetchone()[0]==0;source.backup(target);assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and target.execute('SELECT count(*) FROM leases').fetchone()[0]==0
 stage='artifact-copy';before=inventory(root/'state/artifacts');assert len(before)==5982
 assert shutil.disk_usage(folder).free>2*sum(v['bytes'] for v in before.values())+1024**3,'disk_margin'
 shutil.copytree(root/'state/artifacts',folder/'artifacts',copy_function=shutil.copy2)
 assert inventory(root/'state/artifacts')==before==inventory(folder/'artifacts'),'artifacts_changed'
 (folder/'artifacts.json').write_text(json.dumps(before,sort_keys=True)+'\n')
 checks.append({'name':'Sauvegardes natives intègres, témoins exacts et artefacts identiques','status':'passed'})
 stage='preservation'
 with read_control(control) as db:quiet(db);assert witnesses(db)==live
 assert services()==before_services and {n:sha(Path(n)) for n in official}==official
 with control_owner(control),closing(sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True)) as db:assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0
 for name in ['control.sqlite3','registry.sqlite3','artifacts.json']:os.chown(folder/name,0,0);os.chmod(folder/name,0o400)
 os.chown(folder,0,0);os.chmod(folder,0o700)
 checks.append({'name':'Copies privées protégées et originaux/services conservés','status':'passed'})
 eligible={'firings':{v['id']:v['completed_at']+604801 for v in live['firings']},'generations':{str(v['id']):v['retired_at']+604801 for v in live['generations']}}
 receipt={'completed':True,'capture_id':folder.name,'checks':checks,'source_evidence_sha256':expected['source_evidence_sha256'],'source_read_only':True,'dates_unchanged':True,'witnesses':live,'eligible_after':eligible,'all_eligible_after':max(v for group in eligible.values() for v in group.values()),'image_capture_id':expected['image_capture_id'],'images':expected['images'],'services':before_services,'official_sha256':official,'backup_sha256':sha(folder/'control.sqlite3'),'registry_sha256':sha(folder/'registry.sqlite3'),'artifact_inventory_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'artifact_files':len(before),'root_private_directory':True,'sqlite_read_only':True,'completed_at':time.time()}
 (folder/'capture.json').write_text(json.dumps(receipt)+'\n');os.chmod(folder/'capture.json',0o400);signal.alarm(0);return receipt
try:print(json.dumps(main()))
except BaseException as error:
 print(json.dumps({'completed':False,'checks':checks,'stage':stage,'failure':type(error).__name__,'capture_id':folder.name if folder else None}));sys.exit(1)
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',default='docs/evidence/adapter-schedules-dev-2026-11-11.json')
    args=parser.parse_args();source=(ROOT/args.evidence).resolve()
    assert source.is_relative_to(ROOT/'docs/evidence') and source.is_file()
    proof=json.loads(source.read_text());assert proof['completed'] and proof['criterion']=='SLS-078.7'
    campaign=proof['campaign'];native=campaign['native_after_purge']
    assert campaign['completed'] and campaign['cleanup'] and native['physical']['completed'] and not any(native['counts'].values())
    assert len(campaign['function_ids'])==len(set(campaign['function_ids']))==2 and all(str(UUID(v))==v for v in campaign['function_ids'])
    assert {v['name'] for v in native['functions']}=={'cron-enabled','cron-disabled'}
    images=json.loads((ROOT/'docs/evidence/schedule-retention-capture-dev-2026-11-11.json').read_text())['native_preservation']
    expected={'function_ids':campaign['function_ids'],'namespace_id':campaign['namespace_id'],'source_evidence_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'image_capture_id':images['capture_id'],'images':images['images'],'services':images['services'],'official_sha256':native['official_sha256'],**{k:native[k] for k in ['functions','generations','firings','invocations']}}
    assert [(v['id'],v['image'],v['started_at']) for v in images['services']]==[(v['id'],v['image'],v['started_at']) for v in native['services']]
    output=ROOT/'.local/e2e'/('schedule-terminal-history-'+uuid4().hex+'.json');output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    state={'completed':False,'source_evidence':str(source.relative_to(ROOT)),'operator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'started_at_ns':time.time_ns()}
    output.write_text(json.dumps(state,indent=2)+'\n');output.chmod(0o600)
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input='expected='+repr(expected)+'\n'+NATIVE,text=True,capture_output=True,timeout=210)
    receipt=json.loads(process.stdout) if process.stdout.strip().startswith('{') else {'completed':False,'failure':'native_protocol_failure'}
    state.update(receipt=receipt,exit_code=process.returncode,completed=process.returncode==0 and receipt['completed'],finished_at_ns=time.time_ns(),stderr_sha256=hashlib.sha256(process.stderr.encode()).hexdigest());output.write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps({'completed':state['completed'],'report':str(output),'receipt':receipt}));assert state['completed'],'native_capture_failed_no_automatic_replay'


if __name__=='__main__':main()
