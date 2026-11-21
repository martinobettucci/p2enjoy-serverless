# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md#réalisation-du-passage-de-frontières
# @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md#frontières-du-paquet
"""Read-only exhaustive artifact checks, exported as canonical fingerprints."""
import json,subprocess,sys
from uuid import UUID
assert len(sys.argv) in (3,4)
namespace=str(UUID(sys.argv[1]));campaign=str(UUID(sys.argv[2]));function=str(UUID(sys.argv[3])) if len(sys.argv)==4 else None
program=r'''
import hashlib,json,os,socket,stat,sys,zipfile
from pathlib import Path
from uuid import UUID
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
namespace=NAMESPACE;campaign=CAMPAIGN;selected=FUNCTION
unit=Path('/run')/('serverless-archive-fixtures-'+UUID(campaign).hex)
info=unit.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
for name in ['identity.json','completed.json']:
 info=(unit/name).lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<131072
item=json.loads((unit/'identity.json').read_text());done=json.loads((unit/'completed.json').read_text());fixture=Path(item['output'])
assert done['completed'] and item['campaign']==campaign and fixture==root/'.qualification-archive-fixtures'/campaign

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(65536):h.update(b)
 return h.hexdigest()

def fingerprint(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
expected={}
for case in ['compressed','expanded','files','directories','recovery']:
 expected[case]={}
 for version in ['a','b']:
  name=case+'/inventory-'+version+'.json';p=fixture/name;assert sha(p)==done['files'][name]['sha256'];v=json.loads(p.read_text());expected[case][fingerprint(v)]=v
metadata=json.loads((fixture/'metadata.json').read_text());assert sha(fixture/'metadata.json')==done['metadata_sha256']
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN');assert db.execute('SELECT name FROM namespaces WHERE id=?',(namespace,)).fetchone()[0]=='code-editor-archive-limits-'+campaign[:8]
 functions=[dict(v) for v in db.execute('SELECT f.id,f.name,f.updated_at,f.active_revision_id,f.deleted_at,f.purged_at FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY f.id',(namespace,))]
 keys=[v['id'] for v in functions if selected is None or v['id']==selected];assert keys and (selected is None or len(keys)==1)
 marks=','.join('?' for _ in keys);cases={v['id']:v['name'].removeprefix('editor-archive-').removesuffix('-'+campaign[:8]) for v in functions};assert all(cases[k] in expected for k in keys)
 drafts=[]
 for v in db.execute('SELECT * FROM code_drafts WHERE function_id IN ('+marks+') ORDER BY id',keys):
  cipher=v['changes_cipher'].encode('ascii');drafts.append({k:v[k] for k in ['id','function_id','actor_kind','actor_id','version','handler','base_revision_id','change_bytes','created_at','updated_at','last_deployment_id','last_publication_version']}|{'cipher_bytes':len(cipher),'cipher_sha256':hashlib.sha256(cipher).hexdigest()})
 mutations=[dict(v) for v in db.execute("SELECT id,action,object_id,created_at FROM audit_events WHERE object_id IN ("+marks+") AND action IN ('code_draft.create','code_draft.save','code_draft.discard') ORDER BY id",keys)]
 revisions=[]
 for v in db.execute('SELECT * FROM revisions WHERE function_id IN ('+marks+') ORDER BY id',keys):
  directory=root/'state/artifacts'/str(UUID(v['id']));code=directory/'code';archive=directory/'archive.zip';inventory=json.loads(v['inventory_json']);row={k:v[k] for k in ['id','function_id','code_hash','stored_bytes','deleted_at']};row.update(artifact_directory_exists=directory.exists(),archive_exists=archive.exists(),inventory_count=len(inventory))
  if v['stored_bytes'] and v['deleted_at'] is None:
   normalized={e['path']:{'size':e['size'],'sha256':e['sha256'],'mode':int(e['mode'],8)} for e in inventory};digest=fingerprint(normalized);assert digest in expected[cases[v['function_id']]] and normalized==expected[cases[v['function_id']]][digest]
   expected_parents={'/'.join(p.split('/')[:i]) for p in normalized for i in range(1,len(p.split('/')))};actual_files=set();actual_parents=set()
   for p in code.rglob('*'):
    info=p.lstat();assert not stat.S_ISLNK(info.st_mode);name=str(p.relative_to(code))
    if stat.S_ISDIR(info.st_mode):actual_parents.add(name)
    else:
     assert stat.S_ISREG(info.st_mode) and name in normalized;e=normalized[name];assert info.st_size==e['size'] and stat.S_IMODE(info.st_mode)==e['mode'] and sha(p)==e['sha256'];actual_files.add(name)
   assert actual_files==set(normalized) and actual_parents==expected_parents
   assert archive.is_file() and not archive.is_symlink();archive_sha=sha(archive);assert archive_sha==v['archive_sha256']
   data=metadata['cases'][cases[v['function_id']]];label='a' if digest==data['a']['inventory_sha256'] else 'b'
   assert archive_sha==data['input_sha256' if label=='a' else 'predicted_zip_sha256'];archive_bytes=archive.stat().st_size;assert archive_bytes==data['input_bytes' if label=='a' else 'predicted_zip_bytes']
   with zipfile.ZipFile(archive) as z:
    members=z.infolist();assert len(members)==len(normalized) and {i.filename for i in members}==set(normalized)
    for i in members:assert not i.is_dir() and i.file_size==normalized[i.filename]['size'] and ((i.external_attr>>16)&0o777)==normalized[i.filename]['mode']
   row.update(inventory_sha256=digest,expected_version=label,files=len(actual_files),directories=len(actual_parents),expanded_bytes=sum(e['size'] for e in normalized.values()),archive_bytes=archive_bytes,archive_sha256=archive_sha,archive_members=len(members),all_files_checked=True)
  revisions.append(row)
 result={'operator_uid':os.geteuid(),'functions':functions,'drafts':drafts,'draft_mutations':mutations,'revisions':revisions,'deployments':[dict(v) for v in db.execute('SELECT id,function_id,state,revision_id FROM deployments WHERE function_id IN ('+marks+') ORDER BY id',keys)],'invocations':[dict(v) for v in db.execute('SELECT id,function_id,revision_id,state,handler_started,http_status FROM invocations WHERE function_id IN ('+marks+') ORDER BY id',keys)],'tokens':[dict(v) for v in db.execute('SELECT t.id,t.revoked_at FROM service_tokens t JOIN services s ON s.id=t.service_id WHERE s.namespace_id=? ORDER BY t.id',(namespace,))]}
 result['busy']={table:db.execute('SELECT count(*) FROM '+table+suffix).fetchone()[0] for table,suffix in [('execution_instances',''),('function_operations',''),('deployments'," WHERE state IN ('prepared','receiving','validating')"),('invocations'," WHERE completed_at IS NULL")]};result['reserved_bytes']=db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0];result['integrity']=db.execute('PRAGMA integrity_check').fetchone()[0];result['foreign_keys']=[list(v) for v in db.execute('PRAGMA foreign_key_check')];result['migrations']=[dict(v) for v in db.execute('SELECT * FROM schema_migrations ORDER BY version')];db.rollback()
print(json.dumps(result))
'''.replace('NAMESPACE',repr(namespace)).replace('CAMPAIGN',repr(campaign)).replace('FUNCTION',repr(function))
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,check=True,timeout=240)
print(json.dumps(json.loads(r.stdout)))
