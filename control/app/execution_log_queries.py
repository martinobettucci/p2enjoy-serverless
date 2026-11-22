# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#api-droits-et-snapshots
"""Finite read transactions, scoped snapshots and cursor-based journal queries."""
from contextlib import closing
from datetime import datetime,timezone
import hashlib
import json
import math
import re
import sqlite3
import time
from uuid import UUID

from cryptography.fernet import InvalidToken
from fastapi import HTTPException

from .execution_logs import encoded,policy,LEVELS,EVENT_LIMIT,PAYLOAD_LIMIT

RESPONSE_LIMIT=1024**2
READ_SECONDS=2
PERIOD_SECONDS=7*86400
SNAPSHOT_SECONDS=900
FILTERS=frozenset(('from','to','source','severity','state','invocation','instance','version','kind','q'))
PARAMETERS=FILTERS|{'limit','offset','snapshot','cursor','format'}
STATES=frozenset(('receiving','queued','admitted','running','succeeded','failed','rejected','disconnected',
    'interrupted','starting','ready','busy','draining','cleanup_failed','prepared','validating','published',
    'expired','preparing','pending','completed','aborted'))


def refused(code,status=422):
    raise HTTPException(status,code)


def parameters(query):
    items=list(query.multi_items())
    if len(items)>20 or len({key for key,_ in items})!=len(items):refused('log_query_duplicate_or_excess')
    if any(key not in PARAMETERS for key,_ in items):refused('log_query_unknown_parameter')
    values=dict(items)
    if any(len(value)>8192 for value in values.values()):refused('log_query_value_limit')
    if values.get('snapshot') and values.get('cursor'):refused('log_query_modes_conflict')
    return values


def timestamp(value):
    try:
        try:result=float(value)
        except ValueError:
            parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
            if parsed.tzinfo is None or parsed.utcoffset().total_seconds()!=0:raise ValueError
            result=parsed.timestamp()
        if not math.isfinite(result) or not 0<=result<=253402300799:raise ValueError
        return result
    except (ValueError,OverflowError,TypeError):refused('log_query_invalid_utc')


def bounded_integer(value,default,low,high):
    if value is None:return default
    if not re.fullmatch(r'[0-9]{1,5}',value):refused('log_query_invalid_integer')
    number=int(value)
    if not low<=number<=high:refused('log_query_integer_limit')
    return number


def filters(values,now,base=None):
    period=PERIOD_SECONDS if any(values.get(key) for key in ('invocation','instance','version')) else 3600
    result=dict(base) if base else {'from':now-period,'to':now,'source':'','severity':'','state':'','invocation':'',
                                   'instance':'','version':'','kind':'','q':''}
    for name in FILTERS:
        if name in values:result[name]=timestamp(values[name]) if name in ('from','to') else values[name]
    if result['from']>result['to'] or result['to']-result['from']>PERIOD_SECONDS:refused('log_query_period_limit')
    if result['source'] not in ('','application','platform'):refused('log_query_invalid_source')
    if result['severity'] not in LEVELS|{'','unknown'}:refused('log_query_invalid_severity')
    if result['state'] and result['state'] not in STATES:refused('log_query_invalid_state')
    for name in ('invocation','instance'):
        if result[name]:
            try:
                if str(UUID(result[name]))!=result[name]:raise ValueError
            except ValueError:refused('log_query_invalid_'+name)
    if result['version'] and not re.fullmatch(r'[0-9a-f]{64}',result['version']):refused('log_query_invalid_version')
    if result['kind'] and not re.fullmatch(r'[a-z][a-z0-9_.-]{0,63}',result['kind']):refused('log_query_invalid_kind')
    if len(result['q'])>200:refused('log_query_text_limit')
    if base is not None and result!=base:refused('log_snapshot_filters_changed')
    return result


def console_parameters(items):
    """Preserve valid shared filters on a canonical console redirect."""
    selected=[(key,value) for key,value in items if key!='catalogue']
    if len({key for key,_ in selected})!=len(selected) or any(key not in FILTERS|{'page'} for key,_ in selected):
        raise ValueError('invalid_console_log_query')
    values=dict(selected)
    if any(len(value)>8192 for value in values.values()):raise ValueError('console_log_query_limit')
    try:
        filters(values,time.time())
        bounded_integer(values.get('page'),1,1,2001)
    except HTTPException:raise ValueError('invalid_console_log_query') from None
    return values


def binding(actor,service_id,function_id):
    return hashlib.sha256(encoded({'actor':actor.kind,'id':actor.id,'service':service_id,'function':function_id,
        'rights':sorted(actor.rights),'functions':sorted(actor.functions) if actor.functions is not None else None}).encode()).hexdigest()


def opened(vault,token,mode,context,collection,now):
    try:value=vault.open(token)
    except (InvalidToken,ValueError,UnicodeError,TypeError):refused('log_cursor_invalid')
    if not isinstance(value,dict) or value.get('purpose')!='execution_logs.v1' or value.get('mode')!=mode:
        refused('log_cursor_invalid')
    if value.get('context')!=context:refused('log_cursor_foreign',403)
    if value.get('collection')!=collection:refused('log_collection_changed',410)
    if value['expires_at']<=now:refused('follow_horizon_expired' if mode=='follow' else 'log_snapshot_expired',410)
    return value


def sealed(vault,mode,context,collection,**fields):
    return vault.seal({'purpose':'execution_logs.v1','mode':mode,'context':context,'collection':collection,**fields})


def predicates(service_id,function_id,actor,selected):
    where=['e.service_id=?',"(e.source='platform' OR (f.id IS NOT NULL AND f.deleted_at IS NULL AND f.purged_at IS NULL))"]
    args=[service_id]
    if function_id:where.append('e.function_id=?');args.append(function_id)
    if actor.functions is not None:
        where.append('e.function_id IN ('+','.join('?' for _ in actor.functions)+')');args.extend(actor.functions)
    for key in ('source','state','kind'):
        if selected[key]:where.append('e.'+key+'=?');args.append(selected[key])
    if selected['severity']=='unknown':where.append('e.severity IS NULL')
    elif selected['severity']:where.append('e.severity=?');args.append(selected['severity'])
    if selected['invocation']:
        where.append('(e.invocation_id=? OR e.request_id=?)');args.extend([selected['invocation']]*2)
    if selected['instance']:where.append('e.instance_id=?');args.append(selected['instance'])
    if selected['version']:where.append('e.code_hash=?');args.append(selected['version'])
    if selected['q']:where.append('instr(e.message,?)>0');args.append(selected['q'])
    return where,args


def public_event(row):
    result=dict(row)
    for key in ('sequence','observation_key','metadata_json','payload_bytes'):result.pop(key,None)
    result['metadata']=json.loads(row['metadata_json'])
    for key in ('message_truncated','collection_truncated','projection_truncated'):result[key]=bool(result[key])
    return result


def export_line(item,format):
    if format=='jsonl':return encoded(item)+'\n'
    moment=datetime.fromtimestamp(item['observed_at'],timezone.utc).isoformat()
    subject=' '.join(key+'='+str(item[key]) for key in ('function_id','invocation_id','instance_id','code_hash') if item[key])
    return moment+' '+item['source']+' '+(item['severity'] or 'unknown')+' '+item['kind']+' '+subject+' '+encoded(item['message'])+'\n'


def configure_sql(db,deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:refused('log_read_timeout',503)
    db.execute('PRAGMA busy_timeout='+str(max(1,min(500,int(remaining*1000)))))
    db.set_progress_handler(lambda:time.monotonic()>deadline,1000)


def read(database,vault,service_id,function_id,actor,values,*,export=False,deadline=None):
    deadline=time.monotonic()+READ_SECONDS if deadline is None else deadline
    now=time.time();context=binding(actor,service_id,function_id)
    def check():
        if time.monotonic()>deadline:refused('log_read_timeout',503)
    with closing(database.connect()) as db:
        configure_sql(db,deadline)
        db.execute('BEGIN')
        collection=dict(db.execute('SELECT * FROM execution_log_state WHERE singleton=1').fetchone())
        current=policy(db,service_id,now=now)
        counter=db.execute("SELECT seq FROM sqlite_sequence WHERE name='execution_log_events'").fetchone()
        maximum=counter[0] if counter else 0
        mode='follow' if values.get('cursor') else 'history'
        token=values.get('cursor') or values.get('snapshot')
        old=opened(vault,token,'follow' if mode=='follow' else 'snapshot',context,collection['collection_id'],now) if token else None
        selected=filters(values,now,old['filters'] if old else None)
        if export and mode=='follow':refused('log_export_follow_not_supported')
        limit=bounded_integer(values.get('limit'),1000 if export else 100 if mode=='follow' else 20,1,1000 if export else 100 if mode=='follow' else 20)
        offset=bounded_integer(values.get('offset'),0,0,10000)
        if mode=='follow' and offset:refused('log_follow_offset_not_supported')
        format=values.get('format','jsonl')
        if format not in ('jsonl','text') or ('format' in values and not export):refused('log_export_invalid_format')
        ceiling=maximum if old is None or mode=='follow' else old['ceiling']
        if old:
            if old['policy_version']!=current['version']:refused('log_policy_changed',410)
            if mode=='history' and old['prune_generation']!=current['prune_generation']:
                refused('log_snapshot_incomplete_'+(current['prune_reason'] or 'retention'),410)
            if mode=='follow' and current['pruned_sequence']>old['sequence']:
                refused('log_follow_incomplete_'+(current['prune_reason'] or 'retention'),410)
        where,args=predicates(service_id,function_id,actor,selected)
        floor=max(current['effective_floor'],old.get('available_from',0) if old else 0)
        where.extend(('e.observed_at>=?','e.sequence<=?'));args.extend((floor,ceiling))
        if mode=='history':
            where.extend(('e.observed_at>=?','e.observed_at<=?'));args.extend((selected['from'],selected['to']))
        else:where.append('e.sequence>?');args.append(old['sequence'])
        clause=' AND '.join(where)
        joins=' FROM execution_log_events e LEFT JOIN functions f ON f.id=e.function_id WHERE '+clause
        if old and mode=='history':
            # Detect expiry before physical GC, including rows outside this page.
            expired_where,expired_args=predicates(service_id,function_id,actor,selected)
            expired_where.extend(('e.observed_at>=?','e.observed_at<?','e.observed_at>=?','e.observed_at<=?','e.sequence<=?'))
            expired_args.extend((old['available_from'],floor,selected['from'],selected['to'],ceiling))
            lost=db.execute('SELECT 1 FROM execution_log_events e LEFT JOIN functions f ON f.id=e.function_id WHERE '+
                ' AND '.join(expired_where)+' LIMIT 1',expired_args).fetchone()
            if lost:refused('log_snapshot_incomplete_retention',410)
        elif old and mode=='follow':
            expired_where,expired_args=predicates(service_id,function_id,actor,selected)
            expired_where.extend(('e.sequence>?','e.sequence<=?','e.observed_at<?'))
            expired_args.extend((old['sequence'],ceiling,floor))
            if db.execute('SELECT 1 FROM execution_log_events e LEFT JOIN functions f ON f.id=e.function_id WHERE '+
                          ' AND '.join(expired_where)+' LIMIT 1',expired_args).fetchone():
                refused('log_follow_incomplete_retention',410)
        aggregate=db.execute('SELECT count(*),min(e.observed_at)'+joins,args).fetchone()
        total,earliest=aggregate
        order='e.sequence' if mode=='follow' else 'e.observed_at DESC,e.sequence DESC'
        rows=db.execute('''SELECT e.*,CASE WHEN f.deleted_at IS NULL AND f.purged_at IS NULL THEN f.name END AS function_name'''+
            joins+' ORDER BY '+order+' LIMIT ? OFFSET ?',args+[limit,offset]).fetchall()
        check()
        base={'filters':selected,'policy_version':current['version'],'prune_generation':current['prune_generation']}
        snapshot=(values.get('snapshot') if old and mode=='history' else sealed(vault,'snapshot',context,collection['collection_id'],
            **base,ceiling=ceiling,created_at=now,expires_at=now+SNAPSHOT_SECONDS,available_from=floor))
        started=old['created_at'] if old and mode=='follow' else now
        def cursor(sequence):
            return sealed(vault,'follow',context,collection['collection_id'],**base,sequence=sequence,
                          created_at=started,expires_at=started+PERIOD_SECONDS)
        items=[];lines=[];byte_count=0;last_emitted_sequence=None
        for row in rows:
            check();item=public_event(row)
            if export:
                line=export_line(item,format);size=len(line.encode())
            else:size=len(encoded(item).encode())+1
            # Leave finite space for response metadata and encrypted tokens.
            if byte_count+size>(RESPONSE_LIMIT if export else RESPONSE_LIMIT-16384):break
            byte_count+=size;items.append(item);last_emitted_sequence=row['sequence']
            if export:lines.append(line)
        if rows and not items:refused('log_event_response_limit',503)
        next_offset=offset+len(items) if offset+len(items)<total else None
        last_sequence=last_emitted_sequence if items else (old['sequence'] if mode=='follow' else ceiling)
        # Once every matching item has been consumed, move past unmatched events.
        if mode=='follow' and next_offset is None:last_sequence=maximum
        follow=cursor(last_sequence if mode=='follow' else ceiling)
        check()
        result={'items':items,'total':total,'limit':limit,'offset':offset,'next_offset':next_offset,
            'snapshot':snapshot,'follow_cursor':follow,'partial':next_offset is not None,'mode':mode,
            'filters':selected,'period':{'from':started if mode=='follow' else selected['from'],'to':now if mode=='follow' else selected['to'],
                'time_source':'sequence_observation' if mode=='follow' else 'control_utc'},
            'collection':{'id':collection['collection_id'],'started_at':collection['started_at'],
                'prune_generation':current['prune_generation'],
                'period_precedes_collection':selected['from']<collection['started_at'],
                'retention_minutes':current['retention_minutes'],'available_from':floor,
                'capacity_loss':current['capacity_evicted_sequence']>0},
            'limits':{'events':EVENT_LIMIT,'payload_bytes':PAYLOAD_LIMIT,'response_bytes':RESPONSE_LIMIT,'read_seconds':READ_SECONDS,
                'export_events':1000,'query_days':7,'follow_entries':200}}
        if not export and len(encoded(result).encode())>RESPONSE_LIMIT:refused('log_response_limit',503)
        body=(''.join(lines) if export else encoded(result)).encode('utf8')
        check()
        return {'data':result,'body':body,'format':format,
                'policy_version':current['version'],'prune_generation':current['prune_generation'],
                'earliest':earliest,'context':context,'started_at':now}
