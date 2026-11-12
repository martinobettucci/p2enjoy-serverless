# @spec docs/BACKLOG.md#sls-070 | docs/CODE_DRAFT_CAPACITY.md
# @verifies docs/CODE_DRAFT_CAPACITY.md#périmètre-et-observation
"""Passive native DEV observation: metadata only, no source/cipher/plaintext output."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

namespace = str(UUID(sys.argv[1])) if len(sys.argv) == 2 else None
program = r'''
import hashlib,json,os,shutil,socket,sys
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
namespace=NAMESPACE
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN')
 result={'global':dict(db.execute('SELECT count(*) count,coalesce(sum(length(changes_cipher)),0) cipher_bytes FROM code_drafts').fetchone()),
         'free_bytes':shutil.disk_usage(root/'state').free,'operator_uid':os.geteuid()}
 result['functions']=[];result['drafts']=[];result['draft_mutations']=[];result['revisions']=[];result['invocations']=[]
 if namespace:
  ns=db.execute('SELECT name FROM namespaces WHERE id=?',(namespace,)).fetchone()
  assert ns and ns['name'].startswith('code-draft-capacity-')
  result['functions']=[dict(v) for v in db.execute('SELECT f.id,f.name,f.deleted_at,f.purged_at FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY f.id',(namespace,))]
  keys=[v['id'] for v in result['functions']]
  if keys:
   marks=','.join('?' for _ in keys)
   for row in db.execute('SELECT * FROM code_drafts WHERE function_id IN ('+marks+') ORDER BY id',keys):
    data={k:row[k] for k in ('id','function_id','actor_kind','actor_id','base_revision_id','version','handler','change_bytes','created_at','updated_at','last_deployment_id','last_publication_version')}
    raw=row['changes_cipher'].encode('ascii');data.update(cipher_bytes=len(raw),cipher_sha256=hashlib.sha256(raw).hexdigest());result['drafts'].append(data)
   result['draft_mutations']=[dict(v) for v in db.execute("SELECT id,action,object_id,actor_kind,actor_id,created_at FROM audit_events WHERE object_id IN ("+marks+") AND action IN ('code_draft.create','code_draft.save','code_draft.discard') ORDER BY id",keys)]
   for row in db.execute('SELECT id,function_id,code_hash,stored_bytes,deleted_at FROM revisions WHERE function_id IN ('+marks+') ORDER BY id',keys):
    data=dict(row);data['artifact_directory_exists']=(root/'state/artifacts'/row['id']).exists();result['revisions'].append(data)
   result['invocations']=[dict(v) for v in db.execute('SELECT id,function_id,revision_id,state,handler_started,http_status FROM invocations WHERE function_id IN ('+marks+') ORDER BY id',keys)]
 result['busy']={table:db.execute('SELECT count(*) FROM '+table+suffix).fetchone()[0] for table,suffix in [
  ('execution_instances',''),('function_operations',''),('deployments'," WHERE state IN ('prepared','receiving','validating')"),
  ('invocations'," WHERE state IN ('receiving','queued','admitted','running')")]}
 result['reserved_bytes']=db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0]
 result['integrity']=db.execute('PRAGMA integrity_check').fetchone()[0]
 result['foreign_keys']=[list(v) for v in db.execute('PRAGMA foreign_key_check')]
 result['migrations']=[dict(v) for v in db.execute('SELECT * FROM schema_migrations ORDER BY version')]
 db.rollback()
print(json.dumps(result))
'''.replace('NAMESPACE', repr(namespace))
value = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                        '-J', 'ubuntu@51.158.54.202', 'root@10.77.0.24', 'python3 -B -'],
                       input=program, text=True, capture_output=True, check=True, timeout=60)
print(json.dumps(json.loads(value.stdout)))
