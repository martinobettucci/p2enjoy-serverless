# @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
# @verifies docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#parcours-et-conservation
"""Read-only operator evidence for the publication campaign's own namespace."""
import json,os,re,shlex,socket,sys
from pathlib import Path
from uuid import UUID
from control_database import read_control

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
namespace,function=sys.argv[1:3]
assert all(str(UUID(key))==key for key in (namespace,function))
values={}
for line in Path('/etc/spark/env').read_text().splitlines():
    parts=shlex.split(line,comments=True)
    if len(parts)==1 and parts[0].startswith('SERVERLESS_STATE_HOST_PATH='):
        values['state']=parts[0].split('=',1)[1]
with read_control(Path(values['state'])/'control.sqlite3') as db:
    owner=db.execute('SELECT n.id,n.name FROM namespaces n JOIN services s ON s.namespace_id=n.id JOIN functions f ON f.service_id=s.id WHERE f.id=?',(function,)).fetchone()
    assert owner and owner['id']==namespace and re.fullmatch(r'publication-(?:api|ui)-[0-9a-f]{8}',owner['name'])
    rows=[dict(row) for row in db.execute('SELECT id,state,error_code,reserved_bytes,configuration_cipher IS NOT NULL AS configuration_present FROM deployments WHERE function_id=?',(function,))]
    revisions=[dict(row) for row in db.execute('SELECT id,archive_sha256,stored_bytes,deleted_at FROM revisions WHERE function_id=?',(function,))]
print(json.dumps({'function_id':function,'candidates':rows,'revisions':revisions}))
