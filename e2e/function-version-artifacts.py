# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
"""Read actual artifact ownership for one exact function-versions API campaign."""
import json
import os
from pathlib import Path
import re
import shlex
import socket
import stat
import sys
from uuid import UUID

from control_database import read_control

assert os.getuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
function,namespace=sys.argv[1:]
assert all(str(UUID(value))==value for value in (function,namespace))
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields=shlex.split(line,comments=True)
    if len(fields)==1 and '=' in fields[0]:
        key,value=fields[0].split('=',1)
        if key=='SERVERLESS_STATE_HOST_PATH':settings[key]=value
root=Path(settings['SERVERLESS_STATE_HOST_PATH'])
with read_control(root/'control.sqlite3') as db:
    db.execute('BEGIN')
    row=db.execute('''SELECT n.name FROM functions f JOIN services s ON s.id=f.service_id
        JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?''',(function,namespace)).fetchone()
    assert row and re.fullmatch(r'function-versions-[0-9a-f]{8}',row['name']),'owned_api_campaign_required'
    revisions=[dict(row) for row in db.execute('''SELECT id,code_hash,stored_bytes,deleted_at FROM revisions
        WHERE function_id=? ORDER BY created_at,id''',(function,))]
    candidates=[dict(row) for row in db.execute('''SELECT id,state,revision_id,code_hash,code_changed,version_restored,
        reserved_bytes,configuration_cipher IS NOT NULL AS configuration_present FROM deployments
        WHERE function_id=? ORDER BY created_at,id''',(function,))]
paths={}
for identifier in {row['id'] for row in revisions+candidates}:
    assert str(UUID(identifier))==identifier
    path=root/'artifacts'/identifier
    try:info=path.lstat()
    except FileNotFoundError:paths[identifier]={'exists':False}
    else:
        assert stat.S_ISDIR(info.st_mode) and info.st_uid==1001,'artifact_ownership_mismatch'
        paths[identifier]={'exists':True,'device':info.st_dev,'inode':info.st_ino,'mode':info.st_mode&0o777,
                           'archive_exists':(path/'archive.zip').is_file(),'code_exists':(path/'code').is_dir()}
print(json.dumps({'function_id':function,'namespace_id':namespace,'revisions':revisions,'candidates':candidates,'paths':paths}))
