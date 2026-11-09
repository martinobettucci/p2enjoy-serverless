# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#scénario-et-assertions
"""Read-only native observations of one exact DEV upload-capacity campaign."""
import hashlib,http.client,json,os,re,shlex,shutil,socket,subprocess,sys,time
from pathlib import Path
from uuid import UUID
from control_database import read_control

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
mode,function,namespace=sys.argv[1:4]
assert all(str(UUID(v))==v for v in (function,namespace))
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
    parts=shlex.split(line,comments=True)
    if len(parts)==1 and '=' in parts[0]:
        key,value=parts[0].split('=',1)
        if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST','SERVERLESS_ARTIFACT_BUDGET_MIB'):settings[key]=value
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);assert state==Path('/srv/p2enjoy-serverless/state') and state.resolve()==state
docker=['runuser','-u','spark-docker','--','docker','--host','unix://'+settings['SERVERLESS_DOCKER_SOCKET_HOST']]
def command(args):return subprocess.check_output(args,text=True,timeout=25).strip()
with read_control(state/'control.sqlite3') as db:
    db.execute('BEGIN')
    owner=db.execute('SELECT n.name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?',(function,namespace)).fetchone()
    assert owner and re.fullmatch(r'version-upload-capacity-[0-9a-f]{8}',owner['name']),'owned_campaign_required'
    assert not db.execute('SELECT 1 FROM functions WHERE deleted_at IS NULL AND id!=?',(function,)).fetchone(),'foreign_active_function'
    installation=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
    candidates=[dict(v) for v in db.execute('SELECT id,state,error_code,reserved_bytes,revision_id,code_hash,code_changed,validation_json FROM deployments WHERE function_id=? ORDER BY created_at,id',(function,))]
    revisions=[dict(v) for v in db.execute('SELECT id,code_hash,stored_bytes,deleted_at FROM revisions WHERE function_id=?',(function,))]
    fn=dict(db.execute('SELECT active_revision_id,updated_at,config_json,environment_json,secrets_cipher FROM functions WHERE id=?',(function,)).fetchone())
    counts={name:db.execute(sql).fetchone()[0] for name,sql in {
        'instances':'SELECT count(*) FROM execution_instances',
        'active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
        'active_uploads':"SELECT count(*) FROM deployments WHERE state IN ('receiving','validating')",
        'operations':'SELECT count(*) FROM function_operations',
        'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments',
        'stored_bytes':'SELECT coalesce(sum(stored_bytes),0) FROM revisions'}.items()}
fn['configuration_sha256']=hashlib.sha256(json.dumps([fn.pop(k) for k in ('config_json','environment_json','secrets_cipher')]).encode()).hexdigest()
for row in candidates:
    validation=json.loads(row.pop('validation_json') or 'null')
    row['validation']={k:validation[k] for k in ('valid','error','container_removed','elapsed_seconds') if k in validation} if validation else None
paths={}
for identifier in {v['id'] for v in candidates+revisions}:
    path=state/'artifacts'/identifier
    paths[identifier]={'exists':path.exists(),'archive':(path/'archive.zip').is_file(),'code':(path/'code').is_dir()}
ids=command(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.kind=validation']).split()
class DockerConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.settimeout(self.timeout)
        self.sock.connect(settings['SERVERLESS_DOCKER_SOCKET_HOST'])
def inspect(identifier):
    connection=DockerConnection('localhost',timeout=5)
    try:
        connection.request('GET','/v1.45/containers/'+identifier+'/json');response=connection.getresponse();body=response.read()
        assert response.status in (200,404),'docker_inspect_failed'
        return json.loads(body) if response.status==200 else None
    finally:connection.close()
validators=[];disappeared=[]
for identifier in ids:
    item=inspect(identifier)
    if item is None:disappeared.append(identifier);continue
    assert item['Config']['Labels']['tech.p2enjoy.serverless.installation']==installation,'foreign_validator'
    mounts={m['Destination']:m['Source'] for m in item['Mounts']};code=Path(mounts['/code']);assert code.parent.parent==state/'artifacts'
    assert code.parent.name in paths,'foreign_candidate_validator'
    marker=None
    if mode=='observe-import' and item['State']['Running'] and (code/'storage-validation-delay.mjs').exists():
        program='const fs=require("node:fs"),p="/tmp/storage-validation-import.json";process.stdout.write(fs.existsSync(p)?fs.readFileSync(p,"utf8"):"null")'
        process=subprocess.run(docker+['exec',item['Id'],'node','-e',program],capture_output=True,text=True,timeout=25)
        if process.returncode:
            terminal=inspect(identifier)
            if terminal is None:disappeared.append(identifier);continue
            assert not terminal['State']['Running'],'marker_read_failed_for_running_validator'
            assert terminal['Id']==item['Id'] and terminal['Config']['Labels']==item['Config']['Labels']
            item=terminal
            marker=None
        else:marker=json.loads(process.stdout)
        if marker:assert marker['revision']==json.loads((code/'revision.json').read_text())['revision'] and marker['pid']>0
    validators.append({'id':item['Id'],'name':item['Name'],'candidate_id':code.parent.name,'running':item['State']['Running'],'state':item['State']['Status'],'image':item['Image'],'marker':marker})
result={'observed_at_ns':str(time.time_ns()),'candidates':candidates,'revisions':revisions,'function':fn,'paths':paths,'counts':counts,'validators':validators,'disappeared_during_observation':disappeared,'channels':[v.name for v in (state/'validation').iterdir()]}
reservation=64*1024**2+256*1024**2+(2*20000+2)*4096
if mode=='preflight':
    assert 'name=rootless' in json.loads(command(docker+['info','--format','{{json .SecurityOptions}}']))
    assert not validators and not result['channels'] and all(not counts[k] for k in ('instances','active_calls','active_uploads','operations','reserved_bytes'))
    budget=int(settings.get('SERVERLESS_ARTIFACT_BUDGET_MIB','4096'))*1024**2;free=shutil.disk_usage(state/'artifacts').free
    assert counts['stored_bytes']+4*reservation<=budget and free>=4*reservation+1024**3,'four_admissions_budget_required'
    result.update(ready=True,reservation_bytes=reservation,budget_bytes=budget,free_bytes=free,
        official_sha256={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ('/etc/spark/env','/run/spark/secrets','/etc/spark/routes')},
        services=[{'name':v['Name'],'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status']} for v in json.loads(command(docker+['inspect','serverless-api','serverless-runtime-reference']))])
    assert all(v['health']=='healthy' for v in result['services'])
elif mode=='history':
    start=int(sys.argv[4]);end=time.time_ns();assert 0<end-start<180*10**9
    events=[]
    raw=command(docker+['events','--since',str(start//10**9),'--until',str(end//10**9+1),'--filter','type=container','--filter','event=create','--filter','event=destroy','--filter','label=tech.p2enjoy.serverless.installation='+installation,'--filter','label=tech.p2enjoy.serverless.kind=validation','--format','{{json .}}'])
    for line in raw.splitlines():
        event=json.loads(line)
        if start<=event['timeNano']<=end:events.append({'action':event['Action'],'id':event['Actor']['ID'],'time_ns':str(event['timeNano'])})
    result['history']={'started_at_ns':str(start),'ended_at_ns':str(end),'events':events}
elif mode not in ('inspect','observe-import'):raise RuntimeError('unknown_mode')
print(json.dumps(result))
