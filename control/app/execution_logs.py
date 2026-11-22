# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md | docs/SCHEMA.md#journaux-dexécution--migration011-spécifiée-non-appliquée
"""Bounded public execution journal; producers share their decision transaction."""
import json
from datetime import datetime,timezone
import time
from uuid import uuid4

EVENT_LIMIT=10000
PAYLOAD_LIMIT=16*1024**2
MESSAGE_LIMIT=4096
METADATA_LIMIT=2048
LINE_LIMIT=1024
RETENTION_MINUTES=10080
LEVELS=frozenset(('trace','debug','info','warning','error','fatal'))
TERMINAL=frozenset(('succeeded','failed','rejected','disconnected','interrupted'))


def encoded(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'))


def bounded_text(value,limit):
    raw=value.encode('utf8')
    return raw[:limit].decode('utf8','ignore'),len(raw)>limit


def public_time(value):
    return datetime.fromtimestamp(value,timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z') if value is not None else None


def _unique_pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate_json_key')
        result[key]=value
    return result


def message_type(text):
    """Only explicit unambiguous levels, never inferred from stderr or status."""
    try:
        value=json.loads(text,object_pairs_hook=_unique_pairs,
                         parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite_json')))
        pending=[(value,0)]
        while pending:
            item,depth=pending.pop()
            if depth>16:return 'text',None
            if isinstance(item,dict):pending.extend((v,depth+1) for v in item.values())
            elif isinstance(item,list):pending.extend((v,depth+1) for v in item)
        supplied=[value[k] for k in ('level','severity') if k in value] if isinstance(value,dict) else []
        levels=[('warning' if v=='warn' else v) for v in supplied if isinstance(v,str)]
        level=(levels[0] if supplied and len(levels)==len(supplied) and
               all(v==levels[0] and v in LEVELS for v in levels) else None)
        return 'json',level
    except (ValueError,TypeError,RecursionError):return 'text',None


def policy(db,service_id,*,now=None,create=False):
    now=time.time() if now is None else now
    row=db.execute('SELECT * FROM service_log_policies WHERE service_id=?',(service_id,)).fetchone()
    if row is None and create:
        db.execute('INSERT INTO service_log_policies(service_id,updated_at) VALUES(?,?)',(service_id,now))
        row=db.execute('SELECT * FROM service_log_policies WHERE service_id=?',(service_id,)).fetchone()
    result=dict(row) if row else {'service_id':service_id,'retention_minutes':RETENTION_MINUTES,
        'version':1,'updated_at':None,'expiration_floor':0,'prune_generation':0,'pruned_sequence':0,
        'prune_reason':None,'capacity_evicted_sequence':0}
    result['effective_floor']=max(result['expiration_floor'],now-result['retention_minutes']*60)
    return result


def _remove(db,rows,*,capacity=False,reason='purge'):
    if not rows:return
    services={}
    for row in rows:
        services[row['service_id']]=max(services.get(row['service_id'],0),row['sequence'])
    db.executemany('DELETE FROM execution_log_events WHERE sequence=?',[(row['sequence'],) for row in rows])
    db.execute('UPDATE execution_log_state SET event_count=event_count-?,payload_bytes=payload_bytes-?,evicted_sequence=max(evicted_sequence,?) WHERE singleton=1',
        (len(rows),sum(row['payload_bytes'] for row in rows),max(row['sequence'] for row in rows) if capacity else 0))
    for service_id,sequence in services.items():
        db.execute('UPDATE service_log_policies SET prune_generation=prune_generation+1,pruned_sequence=max(pruned_sequence,?),prune_reason=? WHERE service_id=?',
            (sequence,'capacity' if capacity else reason,service_id))
        if capacity:db.execute('UPDATE service_log_policies SET capacity_evicted_sequence=max(capacity_evicted_sequence,?) WHERE service_id=?',(sequence,service_id))


def enforce_budget(db):
    state=db.execute('SELECT event_count,payload_bytes FROM execution_log_state WHERE singleton=1').fetchone()
    count=max(0,state['event_count']-EVENT_LIMIT);size=max(0,state['payload_bytes']-PAYLOAD_LIMIT)
    if not count and not size:return
    # At most one bounded projection has just been inserted. Read only fixed-size
    # accounting fields, never the full corpus of messages, to choose eviction.
    rows=[];recovered=0
    for row in db.execute('SELECT sequence,service_id,payload_bytes FROM execution_log_events ORDER BY sequence LIMIT ?',
                          (EVENT_LIMIT+LINE_LIMIT+1,)):
        rows.append(dict(row));recovered+=row['payload_bytes']
        if len(rows)>=count and recovered>=size:break
    _remove(db,rows,capacity=True)


def append(db,*,key,service_id,function_id=None,source='platform',kind,severity='info',state=None,
           observed_at=None,invocation_id=None,request_id=None,instance_id=None,revision_id=None,
           code_hash=None,deployment_id=None,operation_id=None,message='',metadata=None,
           message_format='text',collection_truncated=False,projection_truncated=False,budget=True):
    now=time.time() if observed_at is None else observed_at
    service=db.execute('SELECT deleted_at FROM services WHERE id=?',(service_id,)).fetchone()
    if service is None or service['deleted_at'] is not None:return
    policy(db,service_id,now=now,create=True)
    message,truncated=bounded_text(message,MESSAGE_LIMIT)
    if truncated:message_format='text'
    metadata_json=encoded(metadata or {})
    if len(metadata_json.encode())>METADATA_LIMIT:raise ValueError('execution_log_metadata_limit')
    size=len(message.encode())+len(metadata_json.encode())
    inserted=db.execute('''INSERT INTO execution_log_events
        (id,observation_key,service_id,function_id,source,kind,severity,state,observed_at,
         invocation_id,request_id,instance_id,revision_id,code_hash,deployment_id,operation_id,
         message,metadata_json,message_format,message_truncated,collection_truncated,projection_truncated,payload_bytes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(observation_key) DO NOTHING''',
        (str(uuid4()),key,service_id,function_id,source,kind,severity,state,now,
         invocation_id,request_id,instance_id,revision_id,code_hash,deployment_id,operation_id,
         message,metadata_json,message_format,int(truncated),int(collection_truncated),int(projection_truncated),size)).rowcount
    if inserted:
        db.execute('UPDATE execution_log_state SET event_count=event_count+1,payload_bytes=payload_bytes+? WHERE singleton=1',(size,))
        if budget:enforce_budget(db)


def classification(state,code):
    if state not in TERMINAL and code is None:return None
    if state=='succeeded':return 'application_response'
    if code=='invocation_timeout':return 'timeout'
    if state in ('rejected','disconnected') or code in ('queue_timeout','queue_full','schedule_capacity','network_policy_denied'):
        return 'admission'
    if code in ('handler_error','handler_exited','invalid_handler_response','invalid_handler','module_unreadable',
                'module_link','module_not_file','module_missing','module_ambiguous','dependency_missing',
                'import_failed','import_invalid_namespace','handler_not_callable'):
        return 'code'
    return 'infrastructure'


def invocation_event(db,identifier,kind,*,key_suffix=None):
    row=db.execute('SELECT * FROM invocations WHERE id=?',(identifier,)).fetchone()
    if row is None:return
    severity='error' if row['state'] in ('failed','interrupted') else 'warning' if row['state'] in ('rejected','disconnected') else 'info'
    metadata={k:row[k] for k in ('handler_started','error_code','http_status','created_at','queued_at',
        'admitted_at','dispatched_at','completed_at','trigger','schedule_firing_id','schedule_origin','schedule_slot')}
    for name in ('created_at','queued_at','admitted_at','dispatched_at','completed_at','schedule_slot'):
        metadata[name]=public_time(metadata[name])
    if metadata['handler_started'] is not None:metadata['handler_started']=bool(metadata['handler_started'])
    metadata.update(classification=classification(row['state'],row['error_code']),time_source='control',
                    logs_collection_state=row['logs_collection_state'])
    append(db,key='invocation:'+identifier+':'+(key_suffix or kind),service_id=row['service_id'],
        function_id=row['function_id'],kind=kind,severity=severity,state=row['state'],
        invocation_id=identifier,request_id=identifier,instance_id=row['instance_id'],
        revision_id=row['revision_id'],code_hash=row['resolved_code_hash'],message=kind,metadata=metadata)


def collect(db,identifier):
    row=db.execute('SELECT * FROM invocations WHERE id=?',(identifier,)).fetchone()
    if row is None or row['logs_collection_state']!='collected':return
    lines=row['logs'].splitlines();partial=len(lines)>LINE_LIMIT
    for index,text in enumerate(lines[:LINE_LIMIT]):
        form,level=message_type(text)
        append(db,key='application:'+identifier+':'+str(index),service_id=row['service_id'],
            function_id=row['function_id'],source='application',kind='application.message',severity=level,
            state=row['state'],observed_at=row['completed_at'],invocation_id=identifier,request_id=identifier,
            instance_id=row['instance_id'],revision_id=row['revision_id'],code_hash=row['resolved_code_hash'],
            message=text,message_format=form,collection_truncated=bool(row['logs_truncated']),
            projection_truncated=partial and index==LINE_LIMIT-1,
            metadata={'line':index+1,'time_source':'invocation_completion'},budget=False)
    enforce_budget(db)


def instance_event(db,identifier,kind,*,key_suffix=None):
    row=db.execute('''SELECT i.*,f.service_id,r.code_hash FROM execution_instances i
        JOIN functions f ON f.id=i.function_id JOIN revisions r ON r.id=i.revision_id WHERE i.id=?''',(identifier,)).fetchone()
    if row is None:return
    append(db,key='instance:'+identifier+':'+(key_suffix or kind),service_id=row['service_id'],
        function_id=row['function_id'],kind=kind,state=row['state'],instance_id=identifier,
        revision_id=row['revision_id'],code_hash=row['code_hash'],message=kind,
        severity='error' if kind=='instance.cleanup_failed' else 'info',
        metadata={'created_at':public_time(row['created_at']),'ready_at':public_time(row['ready_at']),
                  'error_code':row['error_code'],'time_source':'control'})


def deployment_event(db,identifier):
    row=db.execute('SELECT * FROM deployments WHERE id=?',(identifier,)).fetchone()
    if row is None:return
    kind='publication.'+row['state']
    append(db,key='deployment:'+identifier+':'+row['state'],service_id=row['service_id'],
        function_id=row['function_id'],kind=kind,state=row['state'],deployment_id=identifier,
        revision_id=row['revision_id'],code_hash=row['code_hash'],message=kind,
        severity='error' if row['state']=='failed' else 'info',
        metadata={'error_code':row['error_code'],'time_source':'control'})


def storage_event(db,identifier):
    row=db.execute('SELECT * FROM storage_commands WHERE id=?',(identifier,)).fetchone()
    if row is None:return
    kind='storage.'+row['state'];phase=row['phase']
    append(db,key='storage:'+identifier+':'+row['state']+':'+(phase or ''),service_id=row['service_id'],
        function_id=row['function_id'],kind=kind,state=row['state'],operation_id=identifier,message=kind,
        severity='warning' if row['state']=='aborted' else 'info',
        metadata={'command':row['kind'],'phase':phase,'time_source':'control'})


def audited_event(db,action,object_id,service_id,detail):
    """Allowlist public transitions, never copy arbitrary audit detail."""
    if action in ('deployment.prepare','function.deploy','deployment.abandon'):
        identifier=detail.get('deployment_id')
        if identifier:deployment_event(db,identifier)
    elif action in ('function.rollback','function.version_promote','version.archive','version.delete','version.restore'):
        fields={key:detail[key] for key in ('code_hash','revision_id','replacement_code_hash','disable_default') if key in detail}
        fields['time_source']='control'
        append(db,key='version:'+str(uuid4()),service_id=service_id,function_id=object_id,
            kind=action,code_hash=detail.get('code_hash'),revision_id=detail.get('revision_id'),
            message=action,metadata=fields)
    elif action=='service.delete':purge_service(db,service_id)
    elif action=='function.delete':
        policy(db,service_id,create=True)
        db.execute("UPDATE service_log_policies SET prune_generation=prune_generation+1,prune_reason='visibility' WHERE service_id=?",(service_id,))


# @spec docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#effacement-massif-des-anciens-logs--sls-128
def purge_function(db,function_id):
    rows=[dict(row) for row in db.execute('SELECT sequence,service_id,payload_bytes FROM execution_log_events WHERE function_id=?',(function_id,))]
    _remove(db,rows)
    db.execute("UPDATE OR ROLLBACK invocations SET logs='',logs_truncated=0,logs_collection_state='expired' WHERE function_id=?",(function_id,))


# @spec docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#effacement-massif-des-anciens-logs--sls-128
def purge_service(db,service_id):
    rows=[dict(row) for row in db.execute('SELECT sequence,service_id,payload_bytes FROM execution_log_events WHERE service_id=?',(service_id,))]
    _remove(db,rows)
    db.execute("UPDATE OR ROLLBACK invocations SET logs='',logs_truncated=0,logs_collection_state='expired' WHERE service_id=?",(service_id,))
    db.execute('DELETE FROM service_log_policies WHERE service_id=?',(service_id,))


def public_invocation(db,row,*,now=None):
    result=dict(row)
    if result['completed_at'] is not None and result['completed_at']<policy(db,result['service_id'],now=now)['effective_floor']:
        result.update(logs='',logs_truncated=0,logs_collection_state='expired')
    return result


def maintenance(db,*,limit=200):
    now=time.time()
    rows=[dict(row) for row in db.execute('''SELECT e.sequence,e.service_id,e.payload_bytes
        FROM execution_log_events e JOIN service_log_policies p ON p.service_id=e.service_id
        WHERE e.observed_at<max(p.expiration_floor,?-p.retention_minutes*60) ORDER BY e.sequence LIMIT ?''',(now,limit))]
    _remove(db,rows,reason='retention')
    calls=[dict(row) for row in db.execute('''SELECT i.id,i.service_id FROM invocations i JOIN service_log_policies p ON p.service_id=i.service_id
        WHERE i.completed_at<max(p.expiration_floor,?-p.retention_minutes*60) AND i.logs_collection_state<>'expired'
        ORDER BY i.completed_at,i.id LIMIT ?''',(now,limit))]
    db.executemany("UPDATE invocations SET logs='',logs_truncated=0,logs_collection_state='expired' WHERE id=?",[(row['id'],) for row in calls])
    for service_id in {row['service_id'] for row in rows+calls}:
        db.execute('UPDATE service_log_policies SET expiration_floor=max(expiration_floor,?-retention_minutes*60) WHERE service_id=?',(now,service_id))
