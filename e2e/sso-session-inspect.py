# @spec docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#qualification-réelle-et-données-de-test
# @verifies docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#qualification-réelle-et-données-de-test
"""Inspect only the caller's actual session; OAuth material never leaves Docker."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys


PROGRAM=r'''
import asyncio,hashlib,json,sqlite3,time
from contextlib import closing
import jwt
from app.auth import Identity
from app.config import Settings,Vault
from app.db import Database

async def inspect():
    settings=Settings.load()
    assert settings.public_url=='https://serverless.lelabs.tech'
    with closing(sqlite3.connect('file:/state/control.sqlite3?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        row=db.execute('SELECT * FROM sessions WHERE digest=?',(SESSION_DIGEST,)).fetchone()
    assert row and row['expires_at']>time.time(),'live_own_session_required'
    payload=Vault(settings.master_key).open(row['tokens_cipher'])
    assert 'pending_tokens' not in payload,'validated_session_required'
    identity=Identity(settings,Database(settings.state_dir),Vault(settings.master_key))
    try:
        access=await identity.claims(payload['tokens']['access_token'])
        identity.require_roles(access)
        id_token=payload['tokens'].get('id_token')
        id_claims=await identity.claims(id_token,id_token=True) if isinstance(id_token,str) else None
        assert access['sub']==row['subject']
        if id_claims is not None:assert access['sub']==id_claims['sub']
        assert row['access_expires_at']==access['exp']
        assert access['exp']-access['iat']==300,'actual_access_lifetime_must_be_300'
        header=jwt.get_unverified_header(payload['tokens']['access_token'])
        print(json.dumps({'verified':True,'sampled_at':time.time(),'iat':access['iat'],
            'exp':access['exp'],'lifetime_seconds':access['exp']-access['iat'],
            'access_azp_matches':access['azp']==settings.client_id,
            'id_token_present':id_claims is not None,
            'id_azp_present':id_claims is not None and 'azp' in id_claims,
            'id_azp_matches':id_claims.get('azp')==settings.client_id if id_claims is not None and 'azp' in id_claims else None,
            'algorithm':header['alg'],'kid_sha256':hashlib.sha256(header['kid'].encode()).hexdigest(),
            'subject_sha256':hashlib.sha256(access['sub'].encode()).hexdigest(),
            'session_created_at':row['created_at'],'session_expires_at':row['expires_at'],
            'pending':False}))
    finally:await identity.close()

asyncio.run(inspect())
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spark',action='store_true')
    parser.add_argument('session_digest')
    args=parser.parse_args()
    assert re.fullmatch('[0-9a-f]{64}',args.session_digest),'session_digest_required'
    if args.spark:
        assert socket.gethostname()=='infra-serverless' and os.geteuid()==0
        program=PROGRAM.replace('SESSION_DIGEST',repr(args.session_digest))
        command=['runuser','-u','spark-docker','--','docker','--host',
            'unix:///run/user/1001/docker.sock','exec','-i','serverless-api','python','-B','-']
        result=subprocess.run(command,input=program,text=True,capture_output=True,timeout=45)
    else:
        command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J',
            'ubuntu@51.158.54.202','root@10.77.0.24','python3','-B',
            '/srv/p2enjoy-serverless/e2e/sso-session-inspect.py','--spark',args.session_digest]
        result=subprocess.run(command,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,'session_inspection_failed'
    value=json.loads(result.stdout)
    assert value['verified'] and value['lifetime_seconds']==300
    print(json.dumps(value))


if __name__=='__main__':
    try:main()
    except Exception:
        print('sso_session_inspection_failed',file=sys.stderr)
        sys.exit(1)
