# @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#préconditions-et-historique
# @verifies docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md#réalisation-du-passage-de-frontières
# @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md#frontières-du-paquet
# @spec docs/BACKLOG.md#sls-114 | docs/CODE_EDITOR_ARCHIVE_RECOVERY.md#cause-native-et-décision-avant-code--22-novembre-2026
# @verifies docs/BACKLOG.md#sls-114 | docs/CODE_EDITOR_ARCHIVE_RECOVERY.md#cause-native-et-décision-avant-code--22-novembre-2026
"""Own a bounded data-generator container and its private DEV fixture directory."""
import hashlib,json,os,shutil,socket,stat,subprocess,sys,tempfile,time
from pathlib import Path
from uuid import UUID

ROOT=Path('/srv/p2enjoy-serverless');IMAGE='sha256:f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0'
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
assert len(sys.argv)==3 and sys.argv[1] in ('create','cleanup')
MODE=sys.argv[1];ID=str(UUID(sys.argv[2]));assert ID==sys.argv[2]
NAME='serverless-archive-fixtures-'+UUID(ID).hex
PARENT=ROOT/'.qualification-archive-fixtures';OUTPUT=PARENT/ID;UNIT=Path('/run')/NAME
CASES={'compressed','expanded','files','directories','recovery'}
NAMES={'input.zip','predicted.zip','inventory-a.json','inventory-b.json','marker-b.txt','marker-overflow.txt','payload.bin',*[f'payload-{i}.bin' for i in range(4)]}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(65536):h.update(b)
 return h.hexdigest()

def atomic(name,value):
 with tempfile.NamedTemporaryFile(dir=UNIT,prefix='.receipt-',delete=False) as f:
  p=Path(f.name);f.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno());os.fchmod(f.fileno(),0o600)
 p.replace(UNIT/name)

def container():
 r=subprocess.run(D+['inspect',NAME],capture_output=True,text=True,timeout=15)
 if r.returncode:
  error_message=r.stderr.lower()
  assert r.returncode==1 and ('no such object' in error_message or 'no such container' in error_message),r.stderr[-300:]
  return None
 v=json.loads(r.stdout)[0];assert v['Image']==IMAGE and v['Config']['Labels'].get('p2enjoy.archive-fixture.campaign')==ID
 return v

def stop_owned():
 row=container()
 if row:
  if row['State']['Running']:subprocess.run(D+['stop','--time','5',row['Id']],capture_output=True,text=True,check=True,timeout=15)
  row=container()
  if row:subprocess.run(D+['rm',row['Id']],capture_output=True,text=True,check=True,timeout=15)
 assert container() is None

def folder():
 info=OUTPUT.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==1001 and stat.S_IMODE(info.st_mode)==0o700
 return [info.st_dev,info.st_ino]

def files():
 result={};total=0
 for p in sorted(OUTPUT.rglob('*')):
  relative=p.relative_to(OUTPUT);info=p.lstat();assert info.st_uid==1001 and not p.is_symlink()
  if stat.S_ISDIR(info.st_mode):assert len(relative.parts)==1 and relative.parts[0] in CASES;continue
  assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=65*1024**2
  assert str(relative)=='metadata.json' or len(relative.parts)==2 and relative.parts[0] in CASES and relative.parts[1] in NAMES
  total+=info.st_size;assert total<=1024**3
  result[str(relative)]={'bytes':info.st_size,'sha256':sha(p)}
 return result

def create():
 if UNIT.exists():print(json.dumps({'completed':False,'error':'campaign_exists'}));return 2
 assert not OUTPUT.exists()
 assert container() is None
 control=json.loads(subprocess.check_output(D+['inspect','serverless-api'],text=True,timeout=15))[0]
 assert control['Image']==IMAGE and control['State']['Running'] and control['State']['Health']['Status']=='healthy'
 if not PARENT.exists():PARENT.mkdir(mode=0o700);os.chown(PARENT,1001,1001)
 info=PARENT.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==1001 and stat.S_IMODE(info.st_mode)==0o700
 OUTPUT.mkdir(mode=0o700);os.chown(OUTPUT,1001,1001);UNIT.mkdir(mode=0o700)
 sources=[ROOT/'e2e/code-editor-archive-fixtures.py',ROOT/'qualification/artifacts/editor-archive-limits.cjs']
 assert all(p.is_file() and not p.is_symlink() for p in sources)
 identity={'campaign':ID,'output':str(OUTPUT),'folder_identity':folder(),'image':IMAGE,'container_name':NAME,'source_sha256':{str(p):sha(p) for p in sources},'created_at_ns':time.time_ns()}
 atomic('identity.json',identity)
 command=D+['run','--rm','--name',NAME,'--label','p2enjoy.archive-fixture.campaign='+ID,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','512m','--cpus','1','--pids-limit','64','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m','--mount','type=bind,src='+str(OUTPUT)+',dst=/output','--mount','type=bind,src='+str(sources[0])+',dst=/fixture-source/generator.py,readonly','--mount','type=bind,src='+str(sources[1])+',dst=/fixture-source/editor-archive-limits.cjs,readonly','--entrypoint','/usr/bin/timeout',IMAGE,'--signal=TERM','--kill-after=5s','600s','python','-B','/fixture-source/generator.py','/output']
 try:
  r=subprocess.run(command,capture_output=True,text=True,timeout=630)
  for name,data in [('generator.stdout',r.stdout),('generator.stderr',r.stderr)]:
   assert len(data.encode())<=1024**2
   p=UNIT/name;p.write_text(data);p.chmod(0o600)
  atomic('generator-receipt.json',{'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest(),'finished_at_ns':time.time_ns()})
  assert r.returncode==0,'fixture_generator_failed:'+str(r.returncode)
  assert container() is None and folder()==identity['folder_identity']
  manifest=files();metadata=json.loads((OUTPUT/'metadata.json').read_text());assert metadata['completed'] and set(metadata['cases'])==CASES
  atomic('completed.json',{'completed':True,'files':manifest,'metadata_sha256':sha(OUTPUT/'metadata.json'),'finished_at_ns':time.time_ns(),'container_gone':True})
  print(json.dumps({'completed':True,'campaign':ID,'output':str(OUTPUT),'image':IMAGE,'metadata_sha256':sha(OUTPUT/'metadata.json'),'metadata':metadata,'container_gone':True}));return 0
 finally:stop_owned()

def cleanup():
 if not UNIT.exists():
  assert not OUTPUT.exists() and container() is None
  print(json.dumps({'completed':True,'already_absent':True,'campaign':ID,'output_removed':True,'container_gone':True}));return 0
 info=UNIT.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
 item=json.loads((UNIT/'identity.json').read_text());assert item['campaign']==ID and item['output']==str(OUTPUT) and item['image']==IMAGE and item['container_name']==NAME
 stop_owned()
 if OUTPUT.exists():
  assert folder()==item['folder_identity'];current=files()
  if (UNIT/'completed.json').exists():assert current==json.loads((UNIT/'completed.json').read_text())['files'],'fixture_files_changed'
  shutil.rmtree(OUTPUT)
 else:assert (UNIT/'cleanup.json').exists(),'fixture_output_missing_without_receipt'
 result={'completed':True,'campaign':ID,'output_removed':not OUTPUT.exists(),'container_gone':container() is None,'finished_at_ns':time.time_ns()};atomic('cleanup.json',result);print(json.dumps(result));return 0

if __name__=='__main__':sys.exit(create() if MODE=='create' else cleanup())
