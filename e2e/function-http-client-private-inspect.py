# @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER_FAILURES.md#échéances-ui-et-confidentialité
# @verifies docs/CONSOLE_TESTER_FAILURES.md#échéances-ui-et-confidentialité
"""Bounded private sentinel search in real DEV logs; never return their contents."""
import base64
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

mode=sys.argv[1];namespace=str(UUID(sys.argv[2]));assert mode in ('begin','inspect')
private=None
if mode=='inspect':
    raw=sys.stdin.buffer.read(65537);assert len(raw)<=65536,'private_input_limit'
    private=json.loads(raw)
    assert isinstance(private,dict) and set(private)=={'since','sentinels','expected_refusals'}
    assert isinstance(private['sentinels'],list) and 1<=len(private['sentinels'])<=16
    assert all(isinstance(v,str) and 1<=len(v)<=4096 for v in private['sentinels'])
    assert isinstance(private['expected_refusals'],list) and len(private['expected_refusals'])<=64
    private['expected_refusals']=[str(UUID(v)) for v in private['expected_refusals']]
program='mode='+repr(mode)+'\nnamespace='+repr(namespace)+'\nprivate='+repr(private)+'\n'+r'''
import base64,datetime,hashlib,json,math,os,signal,socket,subprocess,sys,time
from pathlib import Path
from urllib.parse import quote,quote_plus
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'));from control_database import read_control
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
limit=4*1024**2
def expired(signum,frame):raise TimeoutError('native_inspection_deadline')
signal.signal(signal.SIGALRM,expired);signal.alarm(40)
with read_control(root/'state/control.sqlite3') as db:
 db.execute('BEGIN')
 ns=db.execute('SELECT id,name FROM namespaces WHERE id=?',(namespace,)).fetchone()
 assert ns and ns['name'].startswith('function-http-client-confidentiality-'),'owned_namespace_required'
 functions=[v[0] for v in db.execute('SELECT f.id FROM functions f JOIN services s ON s.id=f.service_id WHERE s.namespace_id=? ORDER BY f.id',(namespace,))]
 assert 1<=len(functions)<=4,'bounded_scope_required'
 if mode=='inspect':
  assert type(private['since']) in (int,float) and math.isfinite(private['since']) and 0<=time.time()-private['since']<=900,'recent_server_time_required'
  categories={'invocation_logs':[],'audit':[]};sizes={k:0 for k in categories};counts={k:0 for k in categories}
  marks=','.join('?' for _ in functions)
  queries={'invocation_logs':('SELECT logs FROM invocations WHERE function_id IN ('+marks+') ORDER BY id',functions),
   'audit':('SELECT a.detail_json FROM audit_events a JOIN services s ON s.id=a.service_id WHERE s.namespace_id=? ORDER BY a.id',(namespace,))}
  for name,(sql,args) in queries.items():
   for row in db.execute(sql,args):
    text=row[0] or '';raw=text.encode('utf8');sizes[name]+=len(raw);counts[name]+=1
    assert sizes[name]<=limit and counts[name]<=1000,'native_log_read_limit'
    categories[name].append(text)
 db.rollback()
metadata=json.loads(subprocess.check_output(D+['inspect','--format','{"id":{{json .Id}},"image":{{json .Image}},"running":{{json .State.Running}}}','serverless-api'],text=True,timeout=10))
assert metadata['running'],'running_control_required'
if mode=='begin':
 print(json.dumps({'sampled_at':time.time(),'namespace_id':namespace,'control':metadata}))
else:
 since=datetime.datetime.fromtimestamp(private['since']-1,datetime.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
 process=subprocess.Popen(D+['logs','--since',since,'serverless-api'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 try:
  raw=process.stdout.read(limit+1)
  assert len(raw)<=limit,'docker_log_read_limit'
  code=process.wait(timeout=15);assert code==0,'docker_logs_failed'
 finally:
  if process.poll() is None:process.kill();process.wait(timeout=10)
  process.stdout.close()
 categories['control_logs']=[raw.decode('utf8',errors='replace')];sizes['control_logs']=len(raw);counts['control_logs']=len(raw.splitlines())
 results=[]
 for name,texts in categories.items():
  content='\n'.join(texts);findings=[]
  for index,value in enumerate(private['sentinels']):
   variants={value,json.dumps(value,ensure_ascii=True)[1:-1],base64.b64encode(value.encode()).decode(),quote(value,safe=''),quote_plus(value,safe='')}
   if any(v in content for v in variants):findings.append({'sentinel_index':index,'value_sha256':hashlib.sha256(value.encode()).hexdigest()})
  results.append({'category':name,'bytes':sizes[name],'records':counts[name],'sha256':hashlib.sha256(content.encode()).hexdigest(),'exposures':findings})
 events=[]
 for line in categories['control_logs'][0].splitlines():
  start=line.find('{')
  if start<0:continue
  try:event=json.loads(line[start:])
  except (ValueError,UnicodeError):continue
  if isinstance(event,dict) and event.get('event')=='request.refused' and event.get('request_id') in private['expected_refusals']:
   status=event.get('status');route=event.get('route')
   status_valid=type(status) is int and 400<=status<=599
   route_valid=isinstance(route,str) and route in {'/api/functions/{key}/test-invocation','/api/functions/{key}/invocations/{identifier}'}
   events.append({'event':'request.refused','request_id':event['request_id'],'status':status if status_valid else None,
    'status_valid':status_valid,'route_sha256':hashlib.sha256(json.dumps(route,sort_keys=True).encode()).hexdigest(),'expected_route_template':route_valid})
 assert set(v['request_id'] for v in events)==set(private['expected_refusals']),'expected_refusal_log_missing'
 assert counts['invocation_logs']>0 and any(categories['invocation_logs']) and counts['audit']>0 and counts['control_logs']>0,'nonempty_real_logs_required'
 print(json.dumps({'completed':True,'namespace_id':namespace,'control':metadata,'sentinels_checked':len(private['sentinels']),'categories':results,'refusals':events,'exposure_detected':any(v['exposures'] for v in results)}))
'''
value=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=60)
if value.returncode:raise SystemExit('private_native_inspection_failed')
print(json.dumps(json.loads(value.stdout)))
