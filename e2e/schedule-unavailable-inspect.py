# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_UNAVAILABLE.md#preuves-et-nettoyage
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_UNAVAILABLE.md#refus-et-reprise
"""Read-only DEV recoup of the exact API-created schedule storage unavailability campaign."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

campaign = json.loads(sys.argv[1])
assert set(campaign) == {'namespace_id', 'function_ids', 'known_instances', 'guard_units'}
assert str(UUID(campaign['namespace_id'])) == campaign['namespace_id']
assert len(campaign['function_ids']) == 1
assert len(set(campaign['function_ids'])) == 1
assert all(str(UUID(v)) == v for v in campaign['function_ids'])
assert isinstance(campaign['known_instances'], dict) and len(campaign['known_instances']) <= 32
assert all(str(UUID(k)) == k and v in campaign['function_ids'] for k,v in campaign['known_instances'].items())
assert isinstance(campaign['guard_units'], list) and len(campaign['guard_units']) <= 1
assert all(__import__('re').fullmatch('serverless-restore-storage-command-[0-9a-f]{32}',v) for v in campaign['guard_units'])
purged = len(sys.argv) == 3 and sys.argv[2] == '--purged'
assert len(sys.argv) == 2 or purged
program = 'campaign=' + repr(campaign) + '\npurged=' + repr(purged) + '\n' + r'''
import hashlib,json,re,socket,subprocess,sys,shlex,os,time
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
sample_started_at=time.time();root=Path('/srv/p2enjoy-serverless');settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
 fields=shlex.split(line,comments=True)
 if len(fields)==1 and fields[0].startswith('SERVERLESS_STORAGE_ROOT_HOST='):settings['storage_root']=fields[0].split('=',1)[1]
sys.path.insert(0,str(root/'e2e'))
from control_database import read_control,control_owner
from contextlib import closing
import sqlite3
ids=campaign['function_ids'];marks=','.join('?' for _ in ids)
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN')
 ns=db.execute('SELECT * FROM namespaces WHERE id=?',(campaign['namespace_id'],)).fetchone()
 assert ns and re.fullmatch('storage-recovery-[0-9a-f]{8}',ns['name'])
 actual={r[0] for r in db.execute('SELECT f.id FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=?',(ns['id'],))}
 assert actual==set(ids)
 functions=[dict(r) for r in db.execute('SELECT id,name,updated_at,config_json,active_revision_id,deleted_at,purged_at FROM functions WHERE id IN ('+marks+')',ids)]
 generations=[dict(r) for r in db.execute('SELECT * FROM schedule_generations WHERE function_id IN ('+marks+') ORDER BY id',ids)]
 firings=[dict(r) for r in db.execute('SELECT * FROM schedule_firings WHERE function_id IN ('+marks+') ORDER BY window_at,id',ids)]
 invocations=[dict(r) for r in db.execute('SELECT id,function_id,state,created_at,queued_at,admitted_at,dispatched_at,completed_at,handler_started,instance_id,error_code,http_status,requested_code_hash,resolved_code_hash,trigger,schedule_firing_id,schedule_slot,logs FROM invocations WHERE function_id IN ('+marks+') ORDER BY created_at,id',ids)]
 instances=[dict(v) for v in db.execute('SELECT id,function_id,revision_id,cpu_nanos,memory_mib,state,created_at,ready_at,last_used_at FROM execution_instances WHERE function_id IN ('+marks+') ORDER BY id',ids)]
 operations=[dict(v) for v in db.execute('SELECT id,function_id,kind,decision,storage_version,error_code FROM function_operations WHERE function_id=?',ids)]
 commands=[dict(v) for v in db.execute('SELECT id,function_id,kind,state,phase,expected_function_version,result_version,error_code FROM storage_commands WHERE function_id=? ORDER BY created_at,id',ids)]
 configuration={v['id']:hashlib.sha256(json.dumps(dict(v),sort_keys=True).encode()).hexdigest() for v in db.execute('SELECT id,config_json,environment_json,secrets_cipher FROM functions WHERE id=?',ids)}
 cursor=db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
 counts={n:db.execute(q).fetchone()[0] for n,q in {'functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','operations':'SELECT count(*) FROM function_operations','active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
services=json.loads(subprocess.check_output(D+['inspect','serverless-api','serverless-runtime-reference'],text=True));assert all(v['State']['Running'] for v in services) and services[1]['State']['Health']['Status']=='healthy'
if purged:assert services[0]['State']['Health']['Status']=='healthy'
containers=[]
for function_id in ids:
 keys=subprocess.check_output(D+['ps','-aq','--filter','label=tech.p2enjoy.serverless.function='+function_id,'--filter','label=tech.p2enjoy.serverless.kind=instance'],text=True).split()
 for key in keys:
  value=json.loads(subprocess.check_output(D+['inspect',key],text=True))[0]
  containers.append({'id':value['Id'],'name':value['Name'],'instance_id':value['Config']['Labels']['tech.p2enjoy.serverless.instance'],'function_id':function_id,'running':value['State']['Running'],'cpu_nanos':value['HostConfig']['NanoCpus'],'memory_bytes':value['HostConfig']['Memory'],'image':value['Image']})
with control_owner(root/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(Path(settings['storage_root'])/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
 db.row_factory=sqlite3.Row
 leases=[dict(v) for v in db.execute('SELECT consumer_id,function_id,config_json FROM leases WHERE function_id IN ('+marks+') ORDER BY consumer_id',ids)]
 agent=[dict(v) for v in db.execute('SELECT id,state,version,pending_json FROM functions WHERE id=?',ids)]
 for item in agent:
  pending=json.loads(item.pop('pending_json') or 'null');item['pending']={k:pending.get(k) for k in ('operation_id','kind','expected_version','phase','error_code')} if pending else None
 receipts=[dict(v) for v in db.execute('SELECT operation_id,kind,expected_version,version FROM discard_receipts WHERE function_id=?',ids)]
records={}
for kind in ('data','cache'):
 p=Path(settings['storage_root'])/'backings'/ids[0]/kind
 if p.exists():
  info=p.lstat();file=p/'record';records[kind]={'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'gid':info.st_gid,'mode':__import__('stat').S_IMODE(info.st_mode),'record_sha256':hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None}
 else:records[kind]=None
helpers=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  args=(p/'cmdline').read_bytes().split(b'\0');args=[x.decode(errors='replace') for x in args if x]
  if len(args)==6 and args[2]=='/srv/p2enjoy-serverless/e2e/storage-command-faults.py' and args[3]=='deny-cache' and args[4:]==[ids[0],campaign['namespace_id']]:
   fields=(p/'stat').read_text().rsplit(')',1)[1].split()
   if fields[0]!='Z':helpers.append({'pid':int(p.name),'birth':fields[19],'state':fields[0]})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
units={}
for unit in campaign['guard_units']:
 units[unit]={}
 for suffix in ('timer','service'):
  result=subprocess.run(['systemctl','is-active',unit+'.'+suffix],capture_output=True,text=True,timeout=10)
  assert result.returncode in (0,3,4);units[unit][suffix]=result.stdout.strip()
budgets=json.loads(subprocess.check_output(D+['exec','serverless-api','python','-B','-c',"import json;from app.config import Settings;s=Settings.load();print(json.dumps({n:getattr(s,n) for n in ('function_cpu_nanos','function_memory_mib','function_instance_limit','waiting_call_limit','function_waiting_call_limit')}))"],text=True))
networks={identifier:subprocess.check_output(D+['network','ls','-q','--filter','label=tech.p2enjoy.serverless.function='+identifier],text=True).split() for identifier in ids}
known=dict(campaign['known_instances']);known.update({v['id']:v['function_id'] for v in instances});known.update({v['instance_id']:v['function_id'] for v in invocations if v['instance_id']})
channels={key:os.path.lexists(root/'state/execution'/key) for key in known}
physical=None;artifacts=None;embedded=None
if purged:
 assert not any(counts.values()) and all(v['purged_at'] for v in functions)
 assert not any(v['retired_at'] is None for v in generations)
 physical=json.loads(subprocess.check_output(['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps({campaign['namespace_id']:ids})],text=True));assert physical['completed']
 inventory={str(p.relative_to(root/'state/artifacts')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'state/artifacts').rglob('*')) if p.is_file()}
 artifacts={'files':len(inventory),'manifest_sha256':hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()}
 source="import hashlib,json;from pathlib import Path;r=Path('/app');print(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']}))"
 embedded=json.loads(subprocess.check_output(D+['exec','serverless-api','python','-B','-c',source],text=True))
print(json.dumps({'completed':True,'functions':functions,'generations':generations,'firings':firings,'invocations':invocations,'cursor':cursor,'sample_started_at':sample_started_at,'sample_finished_at':time.time(),'networks':networks,'known_instances':known,'channels':channels,'instances':instances,'containers':containers,'leases':leases,'budgets':budgets,'counts':counts,'physical':physical,'operations':operations,'commands':commands,'configuration_sha256':configuration,'agent':agent,'agent_receipts':receipts,'records':records,'helpers':helpers,'guard_units':units,'service_health':{v['Name'].lstrip('/'):v['State']['Health']['Status'] for v in services},'original_artifacts':artifacts,'embedded_backend':embedded,'services':[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt']} for v in services],'official_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['/etc/spark/env','/run/spark/secrets','/etc/spark/routes']}}))
'''
result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                         '-J', 'ubuntu@51.158.54.202', 'root@10.77.0.24', 'python3 -B -'],
                        input=program, text=True, capture_output=True, timeout=120)
assert result.returncode == 0, result.stderr[-2000:]
value = json.loads(result.stdout)
if purged:
    assert value['original_artifacts'] == {'files':5982, 'manifest_sha256':'846904e1437a034d7fd95488f246cd5b3dc935a4723d20abf9bb419673e5d482'}
    sources = {str(p.relative_to(Path('control'))):__import__('hashlib').sha256(p.read_bytes()).hexdigest()
               for p in [*Path('control/app').glob('*.py'), *Path('control/migrations').glob('*.sql')]}
    sources['function_code_hash.py'] = __import__('hashlib').sha256(Path('function_code_hash.py').read_bytes()).hexdigest()
    assert value['embedded_backend'] == sources
print(json.dumps(value))
