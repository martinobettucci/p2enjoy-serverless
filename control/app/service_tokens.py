# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#gestion | docs/SCHEMA.md
# @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md#jetons-copie-et-corrélation
"""Single issuer and public projection for ordinary and temporary service tokens."""
import json
import secrets
import time
from uuid import uuid4

from fastapi import HTTPException

from .auth import digest
from .db import audit


def token_public(row):
    data=dict(row);data.pop('digest',None)
    data['rights']=json.loads(data.pop('rights_json'))
    restricted=data.pop('function_ids_json')
    data['function_ids']=json.loads(restricted) if restricted is not None else None
    return data


def create_token(db,service_id,data,actor):
    identifiers=[str(value) for value in data.function_ids] if data.function_ids is not None else None
    if identifiers is not None:
        for key in identifiers:
            if not db.execute('SELECT 1 FROM functions WHERE id=? AND service_id=? AND deleted_at IS NULL',(key,service_id)).fetchone():
                raise HTTPException(422,'La portée contient une fonction étrangère ou absente.')
    key=str(uuid4());value='p2s_'+secrets.token_urlsafe(32)
    row=(key,service_id,data.name,digest(value),value[:12],json.dumps(data.rights),
         json.dumps(identifiers) if identifiers is not None else None,data.expires_at,None,time.time(),None)
    db.execute('INSERT INTO service_tokens VALUES (?,?,?,?,?,?,?,?,?,?,?)',row)
    audit(db,actor,'token.create',key,service_id,{'rights':data.rights})
    result=token_public(db.execute('SELECT * FROM service_tokens WHERE id=?',(key,)).fetchone())
    result['token']=value
    return result
