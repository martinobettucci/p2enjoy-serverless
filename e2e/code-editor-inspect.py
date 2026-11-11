# @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#persistance-concurrence-et-conservation
# @verifies docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#interface-et-preuves
"""Read only native metadata for this campaign namespace; never expose source or cipher."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

namespace=str(UUID(sys.argv[1]));root=Path(__file__).resolve().parent.parent
program=r'''
import hashlib,json,os,socket,sys
from pathlib import Path
from uuid import UUID
assert socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
namespace=NAMESPACE
with read_control(root/'state/control.sqlite3') as db:
 functions=[dict(v) for v in db.execute('SELECT f.id,f.deleted_at,f.purged_at FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=?',(namespace,))]
 keys=[v['id'] for v in functions];assert keys
 marks=','.join('?' for _ in keys)
 drafts=[dict(v) for v in db.execute('SELECT id,function_id,actor_kind,base_revision_id,version,change_bytes,length(changes_cipher) cipher_bytes,last_deployment_id,last_publication_version FROM code_drafts WHERE function_id IN ('+marks+')',keys)]
 revisions=[]
 for v in db.execute('SELECT * FROM revisions WHERE function_id IN ('+marks+') ORDER BY id',keys):
  item={k:v[k] for k in ('id','function_id','code_hash','stored_bytes','deleted_at')};files=json.loads(v['inventory_json']);path=root/'state/artifacts'/str(UUID(v['id']))/'code'
  if v['stored_bytes'] and v['deleted_at'] is None:
   for entry in files:
    file=path/entry['path'];assert file.is_file() and not file.is_symlink()
    assert file.stat().st_size==entry['size']
    assert hashlib.sha256(file.read_bytes()).hexdigest()==entry['sha256']
    assert bool(file.stat().st_mode&0o111)==bool(int(entry['mode'],8)&0o111)
  item.update(artifact_directory_exists=path.parent.exists(),inventory_count=len(files));revisions.append(item)
 versions=[dict(v) for v in db.execute('SELECT function_id,code_hash,state FROM function_versions WHERE function_id IN ('+marks+')',keys)]
 busy={table:db.execute('SELECT count(*) FROM '+table+' WHERE function_id IN ('+marks+')'+extra,keys).fetchone()[0] for table,extra in [('execution_instances',''),('function_operations',''),('deployments'," AND state IN ('prepared','receiving','validating')")]}
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
print(json.dumps({'functions':functions,'drafts':drafts,'revisions':revisions,'versions':versions,'busy':busy,'integrity':'ok'}))
'''.replace('NAMESPACE',repr(namespace))
value=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,check=True,timeout=60)
print(json.dumps(json.loads(value.stdout)))
