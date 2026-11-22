# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
# @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#conservation-par-service-et-budget
"""Read-only accounting of the real DEV journal and owned cleanup, under UID1001."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import sys
from uuid import UUID

from control_database import read_control,control_owner

ROOT=Path('/srv/p2enjoy-serverless')
CONTROL=ROOT/'state/control.sqlite3'
DOCKER=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']


def sha(value):return hashlib.sha256(value).hexdigest()


def native():
    process=subprocess.run(DOCKER+['inspect','serverless-api','serverless-runtime-reference'],capture_output=True,text=True,check=True,timeout=10)
    result={}
    for item in json.loads(process.stdout):
        state=item['State'];assert state['Running'] and state['Health']['Status']=='healthy'
        result[item['Name'].lstrip('/')]=dict(container_id=item['Id'],image=item['Image'],started_at=state['StartedAt'])
    return result


def snapshot(namespace=None):
    with read_control(CONTROL) as db:
        db.execute('BEGIN')
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        migrated='execution_log_events' in tables
        result={'migrations':[row[0] for row in db.execute('SELECT version FROM schema_migrations ORDER BY version')],
            'integrity':[row[0] for row in db.execute('PRAGMA integrity_check')],
            'foreign_keys':[list(row) for row in db.execute('PRAGMA foreign_key_check')],
            'counts':{key:db.execute(sql).fetchone()[0] for key,sql in {
                'live_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL',
                'instances':'SELECT count(*) FROM execution_instances',
                'active_invocations':'SELECT count(*) FROM invocations WHERE completed_at IS NULL',
                'function_operations':'SELECT count(*) FROM function_operations',
                'active_candidates':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')",
                'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()},
            'official_sha256':{str(path):sha(path.read_bytes()) for path in map(Path,('/etc/spark/env','/run/spark/secrets','/etc/spark/routes'))}}
        if migrated:
            state=dict(db.execute('SELECT * FROM execution_log_state WHERE singleton=1').fetchone())
            total,size,computed=db.execute('SELECT count(*),coalesce(sum(payload_bytes),0),coalesce(sum(length(cast(message AS BLOB))+length(cast(metadata_json AS BLOB))),0) FROM execution_log_events').fetchone()
            assert state['event_count']==total and state['payload_bytes']==size==computed,'journal_accounting_mismatch'
            assert 0<=total<=10000 and 0<=size<=16*1024**2,'journal_budget_exceeded'
            state.update(computed_event_count=total,computed_payload_bytes=computed)
            result['journal']=state
        if namespace:
            ns=db.execute('SELECT * FROM namespaces WHERE id=?',(namespace,)).fetchone();assert ns,'owned_namespace_missing'
            assert re.fullmatch('execution-journal-(api|ui)-[0-9a-f]{8}',ns['name'])
            assert str(UUID(ns['description']))==ns['description'] and ns['name'].endswith(ns['description'][:8]),'owned_namespace_required'
            services=[dict(row) for row in db.execute('SELECT id,name,description,deleted_at FROM services WHERE namespace_id=? ORDER BY id',(namespace,))]
            assert all(row['description']==ns['description'] for row in services),'owned_services_required'
            functions=[dict(row) for row in db.execute('SELECT f.id,f.service_id,f.name,f.active_revision_id,f.deleted_at,f.purged_at FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY f.id',(namespace,))]
            calls=[dict(row) for row in db.execute('''SELECT i.id,i.function_id,i.state,i.handler_started,i.http_status,i.error_code,i.instance_id,i.resolved_code_hash,
                i.created_at,i.dispatched_at,i.completed_at,i.logs_collection_state,length(cast(i.logs AS BLOB)) log_bytes,i.logs_truncated
                FROM invocations i JOIN services s ON s.id=i.service_id WHERE s.namespace_id=? ORDER BY i.created_at,i.id''',(namespace,))]
            result.update(namespace=dict(ns),services=services,functions=functions,invocations=calls)
            result['tokens']=[dict(row) for row in db.execute('SELECT t.id,t.revoked_at FROM service_tokens t JOIN services s ON s.id=t.service_id WHERE s.namespace_id=? ORDER BY t.id',(namespace,))]
            result['revisions']=[dict(row) for row in db.execute('SELECT r.id,r.function_id,r.code_hash,r.stored_bytes,r.deleted_at FROM revisions r JOIN functions f ON f.id=r.function_id JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY r.id',(namespace,))]
            result['audit_counts']={row[0]:row[1] for row in db.execute('SELECT a.action,count(*) FROM audit_events a JOIN services s ON s.id=a.service_id WHERE s.namespace_id=? GROUP BY a.action',(namespace,))}
            if migrated:
                events=[]
                for row in db.execute('SELECT e.* FROM execution_log_events e JOIN services s ON s.id=e.service_id WHERE s.namespace_id=? ORDER BY sequence',(namespace,)):
                    event=dict(row);message=event.pop('message').encode();metadata=event.pop('metadata_json').encode()
                    event.update(message_bytes=len(message),message_sha256=sha(message),metadata_bytes=len(metadata),metadata=json.loads(metadata))
                    events.append(event)
                result['events']=events
                result['policies']=[dict(row) for row in db.execute('SELECT p.* FROM service_log_policies p JOIN services s ON s.id=p.service_id WHERE s.namespace_id=? ORDER BY p.service_id',(namespace,))]
        db.rollback()
    assert result['integrity']==['ok'] and result['foreign_keys']==[]
    result['containers']=native()
    return result


def cleanup(namespace):
    result=snapshot(namespace)
    assert result['namespace']['deleted_at'] is not None
    assert all(row['deleted_at'] is not None for row in result['services'])
    assert all(row['deleted_at'] is not None and row['purged_at'] is not None for row in result['functions'])
    assert all(row['revoked_at'] is not None for row in result['tokens'])
    assert not result['events'] and not result['policies']
    assert all(row['stored_bytes']==0 for row in result['revisions'])
    for row in result['revisions']:
        assert not os.path.lexists(ROOT/'state/artifacts'/row['id']),'owned_artifact_not_removed'
    assert all(value==0 for key,value in result['counts'].items()),'platform_not_idle'
    registry=ROOT/'storage-state/registry.sqlite3'
    with control_owner(CONTROL),closing(sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('SELECT count(*) FROM leases').fetchone()[0]==0
        result['registry_leases']=0
    mapping={namespace:[row['id'] for row in result['functions']]}
    process=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('storage-console-inspect.py')),json.dumps(mapping)],
        capture_output=True,text=True,check=True,timeout=90)
    physical=json.loads(process.stdout)
    assert physical['completed'] and all(physical['physical'].values()) and physical['campaigns']==mapping
    result['physical']=physical
    result['physical_cleanup_confirmed']=True
    return result


if __name__=='__main__':
    assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','DEV_only'
    assert len(sys.argv) in (2,3) and sys.argv[1] in ('baseline','namespace','cleanup')
    mode=sys.argv[1]
    namespace=None if mode=='baseline' else str(UUID(sys.argv[2]))
    value=cleanup(namespace) if mode=='cleanup' else snapshot(namespace)
    print(json.dumps(value,separators=(',',':')),flush=True)
