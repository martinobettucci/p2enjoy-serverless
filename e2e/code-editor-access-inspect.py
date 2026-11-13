# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_ACCESS.md#preuve-et-clôture
# @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_ACCESS.md#matrice-des-droits
"""Read-only DEV metadata and complete file SHA/mode validation for the owned namespace."""
import json
import subprocess
import sys
from uuid import UUID

assert len(sys.argv)==2
namespace=str(UUID(sys.argv[1]))
program=r'''
import hashlib,json,os,re,shutil,socket,stat,subprocess,sys
from pathlib import Path
from uuid import UUID
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
namespace=NAMESPACE
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN')
 result={'operator_uid':os.geteuid(),'free_bytes':shutil.disk_usage(root/'state').free,
         'global_drafts':db.execute('SELECT count(*) FROM code_drafts').fetchone()[0],
         'functions':[],'drafts':[],'draft_mutations':[],'revisions':[],'invocations':[],'tokens':[],'storage_commands':[],'versions':[],'deployments':[]}
 if namespace:
  ns=db.execute('SELECT name FROM namespaces WHERE id=?',(namespace,)).fetchone()
  assert ns and ns['name'].startswith('code-editor-source-access-')
  result['functions']=[dict(v) for v in db.execute('SELECT f.id,f.service_id,f.updated_at,f.active_revision_id,f.first_published_code_hash,f.first_promoted_at,f.deleted_at,f.purged_at FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY f.id',(namespace,))]
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
   result['versions']=[dict(v) for v in db.execute('SELECT function_id,code_hash,revision_id,state,created_at,updated_at FROM function_versions WHERE function_id IN ('+marks+') ORDER BY function_id,code_hash',keys)]
   result['deployments']=[dict(v) for v in db.execute('SELECT id,function_id,state,revision_id FROM deployments WHERE function_id IN ('+marks+') ORDER BY id',keys)]
   result['invocations']=[dict(v) for v in db.execute('SELECT id,function_id,revision_id,state,handler_started,http_status FROM invocations WHERE function_id IN ('+marks+') ORDER BY id',keys)]
   result['storage_commands']=[dict(v) for v in db.execute('SELECT id,function_id,kind,state,phase,created_at,completed_at,error_code FROM storage_commands WHERE function_id IN ('+marks+') ORDER BY id',keys)]
  result['tokens']=[dict(v) for v in db.execute('SELECT t.id,t.revoked_at FROM service_tokens t JOIN services s ON s.id=t.service_id WHERE s.namespace_id=? ORDER BY t.id',(namespace,))]
 result['busy']={table:db.execute('SELECT count(*) FROM '+table+suffix).fetchone()[0] for table,suffix in [('execution_instances',''),('function_operations',''),('deployments'," WHERE state IN ('prepared','receiving','validating')"),('invocations'," WHERE state IN ('receiving','queued','admitted','running')")]}
 result['reserved_bytes']=db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0]
 result['integrity']=db.execute('PRAGMA integrity_check').fetchone()[0];result['foreign_keys']=[list(v) for v in db.execute('PRAGMA foreign_key_check')]
 result['migrations']=[dict(v) for v in db.execute('SELECT * FROM schema_migrations ORDER BY version')]
 db.rollback()
print(json.dumps(result))
'''.replace('NAMESPACE',repr(namespace))
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,check=True,timeout=90)
print(json.dumps(json.loads(result.stdout)))
