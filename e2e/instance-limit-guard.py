# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
# @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
"""Temporarily apply the real DEV cell limit through its console; restore on EOF."""
import json,select,shlex,signal,subprocess,sys,urllib.request
from uuid import UUID

namespace=sys.argv[1];assert str(UUID(namespace))==namespace
key='SERVERLESS_FUNCTION_INSTANCE_LIMIT'
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24']
base='http://127.0.0.1:5175/api/v1/sparks/infra-serverless/suggestions'
query='?server=spark-experiment'

def remote(program,payload=None):
    result=subprocess.run(ssh+['python3 -B -c '+shlex.quote(program)],input=payload,text=True,capture_output=True,timeout=60)
    if result.returncode:raise RuntimeError('cell_guard_remote_failed')
    return json.loads(result.stdout)

reader=r'''import json,re,shlex,socket,sys
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
sys.path.insert(0,'/srv/p2enjoy-serverless/e2e')
from control_database import read_control
proposal=Path('/etc/spark/env.?')
assert not proposal.exists() or not any(re.match(r'\s*(?:export\s+)?SERVERLESS_FUNCTION_INSTANCE_LIMIT\s*=',line) for line in proposal.read_text().splitlines()),'existing_limit_proposal_required_to_remain'
values={}
for line in Path('/etc/spark/env').read_text().splitlines():
 parts=shlex.split(line,comments=True)
 if len(parts)==1 and '=' in parts[0]:
  name,value=parts[0].split('=',1)
  if name in ('SERVERLESS_FUNCTION_INSTANCE_LIMIT','SERVERLESS_STATE_HOST_PATH'):values[name]=value
with read_control(Path(values['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3') as db:
 row=db.execute('SELECT name FROM namespaces WHERE id=? AND deleted_at IS NULL',(NAMESPACE,)).fetchone()
 assert row and re.fullmatch('invocation-[0-9a-f]{8}',row[0])
 assert db.execute('SELECT count(*) FROM functions f JOIN services s ON s.id=f.service_id WHERE f.deleted_at IS NULL AND s.namespace_id!=?',(NAMESPACE,)).fetchone()[0]==0,'foreign_function_present'
 assert db.execute('SELECT count(*) FROM execution_instances').fetchone()[0]==0
 assert db.execute("SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')").fetchone()[0]==0
print(json.dumps({'limit':values['SERVERLESS_FUNCTION_INSTANCE_LIMIT']}))
'''.replace('NAMESPACE',repr(namespace))
original=remote(reader)['limit'];assert original=='32','expected_cell_baseline_required'

writer='''import json,sys
from pathlib import Path
value=json.load(sys.stdin);path=Path('/etc/spark/env.?')
lines=path.read_text().splitlines() if path.exists() else []
lines=[line for line in lines if not line.startswith('SERVERLESS_FUNCTION_INSTANCE_LIMIT=')]
lines.append('SERVERLESS_FUNCTION_INSTANCE_LIMIT='+value)
path.write_text('\\n'.join(lines)+'\\n')
print('{}')
'''

def apply(value):
    remote(writer,json.dumps(value))
    with urllib.request.urlopen(base+query,timeout=30) as response:rows=json.load(response)['suggestions']
    proposal=next(row for row in rows if row['kind']=='variables')
    keep=[i+1 for i,line in enumerate(proposal['body'].splitlines()) if not line.startswith(key+'=')]
    request=urllib.request.Request(base+'/variables/apply'+query,method='POST',headers={'Content-Type':'application/json'},
        data=json.dumps({'sha256':proposal['sha256'],'entries':[{'name':key,'value':value,'secret':False}],'conserver':keep}).encode())
    with urllib.request.urlopen(request,timeout=30) as response:json.load(response)
    command="runuser -u spark-docker -- env DOCKER_HOST=unix:///run/user/1001/docker.sock bash /srv/p2enjoy-serverless/control/dev.sh up"
    result=subprocess.run(ssh+[command],text=True,capture_output=True,timeout=90)
    if result.returncode:raise RuntimeError('cell_guard_recreate_failed')
    actual=remote('''import json,shlex,subprocess
from pathlib import Path
values={};keys=('SERVERLESS_FUNCTION_INSTANCE_LIMIT','SERVERLESS_FUNCTION_CPU_BUDGET','SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB')
for line in Path('/etc/spark/env').read_text().splitlines():
 parts=shlex.split(line,comments=True)
 if len(parts)==1 and '=' in parts[0]:
  name,value=parts[0].split('=',1)
  if name in keys:values[name]=value
command=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','exec','serverless-api','python','-B','-c',"import os,json;print(json.dumps({key:os.environ[key] for key in "+repr(keys)+"}))"]
consumed=json.loads(subprocess.check_output(command,text=True,timeout=15));assert consumed==values
assert values['SERVERLESS_FUNCTION_CPU_BUDGET']=='1' and values['SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB']=='8192'
print(json.dumps({'official':values[keys[0]],'consumed':consumed[keys[0]],'cpu_budget':values[keys[1]],'memory_budget_mib':values[keys[2]],'budget_configuration_matches':True}))
''')
    assert actual['official']==actual['consumed']==value
    return actual

def emit(value):print(json.dumps(value),flush=True)
def interrupted(*_):raise SystemExit('guard_interrupted')
for number in (signal.SIGTERM,signal.SIGINT):signal.signal(number,interrupted)
try:
    applied=apply('2');emit({'event':'instance-limit-applied',**applied})
    ready,_,_=select.select([sys.stdin],[],[],180)
    assert ready and sys.stdin.readline().strip()=='restore','restore_required'
finally:
    restored=apply(original);emit({'event':'instance-limit-restored',**restored})
