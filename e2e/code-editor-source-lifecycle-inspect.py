# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_LIFECYCLE.md#matrice-et-clôture-de-preuve
# @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_LIFECYCLE.md#purge-confirmée-face-à-un-lecteur-vivant
"""Read-only DEV metadata and complete file SHA/mode validation for the owned namespace."""
import json
import subprocess
import sys
from uuid import UUID

assert len(sys.argv) in (2,3)
namespace=str(UUID(sys.argv[1]));unit=sys.argv[2] if len(sys.argv)==3 else None
program=r'''
import hashlib,json,os,re,shutil,socket,stat,subprocess,sys
from pathlib import Path
from uuid import UUID
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
namespace=NAMESPACE
unit=GATE_UNIT
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN')
 result={'operator_uid':os.geteuid(),'free_bytes':shutil.disk_usage(root/'state').free,
         'global_drafts':db.execute('SELECT count(*) FROM code_drafts').fetchone()[0],
         'functions':[],'drafts':[],'draft_mutations':[],'revisions':[],'invocations':[],'tokens':[],'storage_commands':[]}
 if namespace:
  ns=db.execute('SELECT name FROM namespaces WHERE id=?',(namespace,)).fetchone()
  assert ns and ns['name'].startswith('code-editor-read-concurrency-')
  result['functions']=[dict(v) for v in db.execute('SELECT f.id,f.service_id,f.deleted_at,f.purged_at FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY f.id',(namespace,))]
  keys=[v['id'] for v in result['functions']]
  if keys:
   marks=','.join('?' for _ in keys)
   for v in db.execute('SELECT * FROM code_drafts WHERE function_id IN ('+marks+') ORDER BY id',keys):
    raw=v['changes_cipher'].encode('ascii')
    result['drafts'].append({k:v[k] for k in ('id','function_id','actor_kind','actor_id','version','handler','base_revision_id','change_bytes','created_at','updated_at','last_deployment_id','last_publication_version')}|{'cipher_bytes':len(raw),'cipher_sha256':hashlib.sha256(raw).hexdigest()})
   result['draft_mutations']=[dict(v) for v in db.execute("SELECT id,action,object_id,created_at FROM audit_events WHERE object_id IN ("+marks+") AND action IN ('code_draft.create','code_draft.save','code_draft.discard') ORDER BY id",keys)]
   for v in db.execute('SELECT * FROM revisions WHERE function_id IN ('+marks+') ORDER BY id',keys):
    path=root/'state/artifacts'/str(UUID(v['id']))/'code';items=json.loads(v['inventory_json'])
    if v['stored_bytes'] and v['deleted_at'] is None:
     for item in items:
      file=path/item['path'];assert file.is_file() and not file.is_symlink()
      assert file.stat().st_size==item['size'] and hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
      assert stat.S_IMODE(file.stat().st_mode)==int(item['mode'],8)
    result['revisions'].append({k:v[k] for k in ('id','function_id','code_hash','stored_bytes','deleted_at')}|{'artifact_directory_exists':path.parent.exists(),'inventory_count':len(items),'inventory':items})
   result['invocations']=[dict(v) for v in db.execute('SELECT id,function_id,revision_id,state,handler_started,http_status FROM invocations WHERE function_id IN ('+marks+') ORDER BY id',keys)]
   result['storage_commands']=[dict(v) for v in db.execute('SELECT id,function_id,kind,state,phase,created_at,completed_at,error_code FROM storage_commands WHERE function_id IN ('+marks+') ORDER BY id',keys)]
  result['tokens']=[dict(v) for v in db.execute('SELECT t.id,t.revoked_at FROM service_tokens t JOIN services s ON s.id=t.service_id WHERE s.namespace_id=? ORDER BY t.id',(namespace,))]
 result['busy']={table:db.execute('SELECT count(*) FROM '+table+suffix).fetchone()[0] for table,suffix in [('execution_instances',''),('function_operations',''),('deployments'," WHERE state IN ('prepared','receiving','validating')"),('invocations'," WHERE state IN ('receiving','queued','admitted','running')")]}
 result['reserved_bytes']=db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0]
 result['integrity']=db.execute('PRAGMA integrity_check').fetchone()[0];result['foreign_keys']=[list(v) for v in db.execute('PRAGMA foreign_key_check')]
 result['migrations']=[dict(v) for v in db.execute('SELECT * FROM schema_migrations ORDER BY version')]
 db.rollback()
if unit is not None:
 assert re.fullmatch('serverless-restore-editor-read-[0-9a-f]{32}',unit)
 folder=Path('/run')/unit;info=folder.lstat()
 assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
 identity=folder/'identity.json';info=identity.lstat()
 assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<32768
 item=json.loads(identity.read_text());held=json.loads((folder/'held.json').read_text())
 assert item['namespace_id']==namespace and item['function_id'] in keys
 revision=str(UUID(item['revision_id']));expected='/state/artifacts/'+revision+'/code/reader-gate.txt';assert item['container_path']==expected
 def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
 def process(tid):
  values=dict(v.split(':',1) for v in Path('/proc',str(tid),'status').read_text().splitlines() if ':' in v)
  return {'tracer_pid':int(values['TracerPid']),'tgid':int(values['Tgid']),'state':values['State'].split()[0]}
 assert birth(item['pid'])==item['birth'] and Path('/proc',str(item['pid']),'cgroup').read_text()==item['cgroup']
 D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
 control,reference=json.loads(subprocess.check_output(D+['inspect','serverless-api','serverless-runtime-reference'],text=True,timeout=5))
 assert [control['Id'],control['Image'],control['State']['StartedAt']]==[item['container_id'],item['image'],item['started_at']] and control['State']['Running']
 assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==item['reference'] and reference['State']['Running']
 file=root/'state/artifacts'/revision/'code/reader-gate.txt'
 data={'exists':file.exists(),'matches_identity':False}
 if data['exists']:
  info=file.lstat();assert stat.S_ISREG(info.st_mode)
  data.update(device=info.st_dev,inode=info.st_ino,size=info.st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),matches_identity=[info.st_dev,info.st_ino,info.st_size]==item['file_identity'])
 readers=[]
 for expected_reader in held['readers']:
  tid=expected_reader['tid'];row={k:expected_reader[k] for k in ['tid','birth','fd','device','inode']};row.update(same_thread_alive=False,fd_matches_target=False,tracer_pid=None,state=None)
  try:
   row['same_thread_alive']=birth(tid)==expected_reader['birth']
   if row['same_thread_alive']:
    current=process(tid);assert current['tgid']==item['pid'];row.update(current)
    fd=Path('/proc',str(tid),'fd',str(expected_reader['fd']))
    try:
     actual=fd.stat();row['fd_matches_target']=stat.S_ISREG(actual.st_mode) and [actual.st_dev,actual.st_ino,actual.st_size]==[expected_reader['device'],expected_reader['inode'],expected_reader['size']] and os.readlink(fd) in (expected,expected+' (deleted)')
    except FileNotFoundError:pass
  except FileNotFoundError:pass
  readers.append(row)
 result['gate']={'unit':unit,'helper_pid':item['helper_pid'],'revision_id':revision,'control_pid':item['pid'],'control_birth':item['birth'],'file':data,'readers':readers}
print(json.dumps(result))
'''.replace('NAMESPACE',repr(namespace)).replace('GATE_UNIT',repr(unit))
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,check=True,timeout=90)
print(json.dumps(json.loads(result.stdout)))
