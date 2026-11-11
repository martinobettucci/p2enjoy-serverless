// @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#parcours-réel
// @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#parcours-réel
// Real public HTTP, global retention by completed_at/id, and isolated data restoration.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,readFile,writeFile,rename,mkdtemp,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium,request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';
const run=promisify(execFile),campaign=randomUUID(),base='https://serverless.lelabs.tech';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py',out=new URL('../.local/e2e/',import.meta.url);
const options=process.argv.slice(2),observerRefusal=options.length===1&&options[0]==='--observer-refusal';
const observerDeadline=options.length===1&&options[0]==='--observer-global-deadline'?'global-alarm':options.length===1&&options[0]==='--observer-command-timeout'?'command-timeout':null;
const observerDiagnostic=observerRefusal||Boolean(observerDeadline);
assert(options.length===0||observerDiagnostic,'unknown_source_retention_options');
const report=new URL((observerDeadline?'invocation-source-observer-'+observerDeadline+'-':observerRefusal?'invocation-source-observer-refusal-':'invocation-source-retention-volume-')+campaign+'.json',out),events=[],checks=[],observations=[],functions=[],responses=[],producers=[];
const driverErrors=[];
let caller,stopProducing=false,saveQueue=Promise.resolve(),window,lastCall;
let child,ended=false,exitCode=null,browser,context,admin,session,namespace,service,reader,work,archive,completed=false,cleanup=false,failure=null,restoration;
function save(){saveQueue=saveQueue.then(async()=>{const p=new URL(report.pathname+'.pending','file:');await writeFile(p,JSON.stringify({campaign,mode:observerDeadline??(observerRefusal?'observer-refusal':'count'),completed:completed&&cleanup&&!failure,cleanup,skipped:0,checks,events,observations,responses,function_ids:functions.map(v=>v.id),namespace_id:namespace?.id,exit_code:exitCode,failure,restoration},null,2)+'\n',{mode:0o600});await rename(p,report);});return saveQueue;}
async function until(action,message,seconds=90){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,250));}assert.fail(message);}
async function event(name){return until(()=>{const v=events.find(v=>v.event===name);assert(v||!ended,'deployment_driver_stopped');return v;},'deployment_event_missing',150);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function operation(op,extra={}){const offset=events.length;assert(!ended);child.stdin.write(JSON.stringify({op,...extra})+'\n');const found=await until(()=>{const v=events.slice(offset).find(v=>v.event==='result'&&v.op===op);assert(v||!ended,'deployment_driver_stopped');return v;},'operator_observation_missing');const value=found.value;if(op==='capacity')found.value={installation_id:value.installation_id,instances:value.instances.length,containers:value.containers.length,invocations:value.invocations.length};return value;}
async function capacity(){return operation('capacity');}
async function remote(op,...args){try{const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,op,campaign,...args],{timeout:60000,maxBuffer:12*1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}catch(error){error.operator=op;await writeFile(new URL('source-retention-operator-'+campaign+'-'+op+'.stderr',out),String(error.stderr??''),{mode:0o600});throw error;}}

// @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#pannes-propres-de-lalarme35-et-de-la-commande40
async function deadlineConsumersBefore(initial){
 const expected={campaign,functions:functions.map(v=>v.id),instances:initial.instances,runtime_image:initial.containers[0].image};
 const program='expected='+JSON.stringify(JSON.stringify(expected))+'\nexpected=__import__("json").loads(expected)\n'+String.raw`
import json,os,socket,sqlite3,stat,subprocess,sys,time
from contextlib import closing
from pathlib import Path
from uuid import UUID
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless' and str(UUID(expected['campaign']))==expected['campaign']
work=Path('/srv/p2enjoy-serverless/qualification-history')/('instance-limit-'+expected['campaign']);info=work.lstat()
assert work.resolve()==work and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o750
item=json.loads((work/'restore.json').read_text());assert item['mode']=='instance-limit' and item['guard_seconds']==2700 and not item.get('restored')
installation=item['temporary_installation'];assert str(UUID(installation))==installation and installation!=item['installation']
def docker(*args):return subprocess.check_output(item['docker']+list(args),text=True,timeout=15)
identifiers=docker('ps','-aq','--no-trunc','--filter','label=tech.p2enjoy.serverless.installation='+installation).split();assert len(identifiers)==2
by_function={v['function_id']:v for v in expected['instances']};assert len(by_function)==2
containers=[];networks={};prefix='tech.p2enjoy.serverless.'
for value in json.loads(docker('inspect',*identifiers)):
 labels=value['Config']['Labels'];function,revision,consumer=(labels[prefix+k] for k in ('function','revision','instance'))
 assert labels[prefix+'installation']==installation and labels[prefix+'kind']=='instance' and function in expected['functions']
 assert value['Image']==expected['runtime_image'] and value['State']['Running']
 assert by_function[function]['id']==consumer and by_function[function]['revision_id']==revision
 network_ids=[v['NetworkID'] for v in value['NetworkSettings']['Networks'].values()];assert len(network_ids)==1
 containers.append({'id':value['Id'],'image':value['Image'],'function_id':function,'revision_id':revision,'consumer_id':consumer,'network_ids':network_ids})
 for identifier in network_ids:
  network=json.loads(docker('network','inspect',identifier))[0];labels=network['Labels']
  assert labels[prefix+'installation']==installation and labels[prefix+'kind']=='instance-network'
  assert labels[prefix+'function']==function and labels[prefix+'revision']==revision and labels[prefix+'instance']==consumer
  assert set(network['Containers'])=={value['Id']};networks[identifier]={'id':identifier,'function_id':function,'revision_id':revision,'consumer_id':consumer}
assert len(networks)==2 and len({v['consumer_id'] for v in containers})==2
sys.path.insert(0,'/srv/p2enjoy-serverless/e2e');from control_database import control_owner
with control_owner(Path(item['paths']['state'])/'control.sqlite3'),closing(sqlite3.connect('file:'+str(Path(item['paths']['storage'])/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
 db.row_factory=sqlite3.Row;leases=[dict(v) for v in db.execute('SELECT consumer_id,installation_id,function_id FROM leases WHERE installation_id=?',(installation,))]
assert len(leases)==2 and {v['consumer_id'] for v in leases}=={v['consumer_id'] for v in containers}
for lease in leases:assert lease['function_id']==next(v['function_id'] for v in containers if v['consumer_id']==lease['consumer_id'])
print(json.dumps({'completed':True,'installation_id':installation,'containers':containers,'networks':list(networks.values()),'leases':leases,'sampled_at':time.time()}))
`;
 return new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:60000,maxBuffer:2*1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});
}

async function deadlineEvidence(){
 const program='campaign='+JSON.stringify(campaign)+'\n'+String.raw`
import hashlib,json,os,socket,stat
from pathlib import Path
from uuid import UUID
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless' and str(UUID(campaign))==campaign
work=Path('/srv/p2enjoy-serverless/qualification-history')/('instance-limit-'+campaign)
info=work.lstat();assert work.resolve()==work and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o750
item=json.loads((work/'restore.json').read_text());assert item['campaign']==campaign and item['mode']=='instance-limit' and item['guard_seconds']==2700 and item['restored']
result={'completed':True,'files':{},'metadata':{}}
for name in ('source-retention-observation.json','source-observer-command.json','source-observer-deadline-identity.json','source-observer-actor.json','source-observer-actor-ready.json'):
 p=work/name;info=p.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600
 raw=p.read_bytes();result['files'][name]=json.loads(raw);result['metadata'][name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid}
for name in ('source-observer-command.stdout','source-observer-command.stderr'):
 p=work/name;info=p.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600
 raw=p.read_bytes();result['metadata'][name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
print(json.dumps(result))
`;
 return new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:30000,maxBuffer:4*1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});
}
async function proveObserverDeadline(initial){
 let heartbeat=0;
 await until(async()=>{assert(!ended,'guard_ended_before_cron');if(Date.now()-heartbeat>10000){assert((await api('/api/session')).authenticated);heartbeat=Date.now();}return Date.now()/1000>=window-1;},'real_cron_boundary_not_reached',480);
 assert(Date.now()/1000<window-.2,'last_http_start_frontier_missed');startLastCall();
 child.stdin.write(JSON.stringify({op:'observe-source-retention',functions:functions.map(v=>v.id),window,deadline_fault:observerDeadline})+'\n');
 await until(()=>ended,'deadline_operator_and_driver_not_joined',100);
 const driverStderr=Buffer.concat(driverErrors);await writeFile(new URL('source-observer-'+observerDeadline+'-driver-'+campaign+'.stderr',out),driverStderr,{mode:0o600});
 assert.equal(exitCode,1);restoration=events.find(v=>v.event==='restored');
 assert(restoration&&restoration.databases_identical&&restoration.artifacts_identical&&restoration.configuration_unchanged&&restoration.reference_unchanged&&restoration.temporary_directories_removed&&restoration.control_healthy);assert.equal(restoration.independent,false);
 const evidence=await deadlineEvidence(),files=evidence.files,measured=files['source-retention-observation.json'],command=files['source-observer-command.json'],identity=files['source-observer-deadline-identity.json'],actor=files['source-observer-actor.json'];
 const status=await remote('status'),last=await lastCall;
 observations.push({scenario:'source-observer-deadline-terminal',deadline_mode:observerDeadline,evidence,terminal_status:status,last_http:last.error?{error_type:last.error.name}:{response:last.value}});await save();
 assert.equal(measured.completed,false);assert(measured.inherited_guard_lock);assert.deepEqual(measured.initial_counts,{total:2,terminal:0});assert.equal(measured.running.length,2);
 assert(measured.running.every(v=>v.handler_started&&v.state==='running'&&v.completed_at===null));assert.deepEqual(measured.running.map(v=>v.function_id).sort(),functions.map(v=>v.id).sort());
 const scheduled=measured.running.find(v=>v.function_id===functions[1].id),http=measured.running.find(v=>v.function_id===functions[0].id),firing=measured.initial.firing;
 assert.equal(http.trigger,'http');assert.equal(scheduled.trigger,'schedule');assert.deepEqual(measured.initial.invocations.map(v=>v.id).sort(),measured.running.map(v=>v.id).sort());
 assert(firing&&firing.function_id===functions[1].id&&firing.window_at===window&&firing.state==='dispatched'&&firing.completed_at===null&&firing.invocation_id===scheduled.id);
 assert.equal(measured.initial.invocations.find(v=>v.id===scheduled.id).schedule_firing_id,firing.id);
 const gate=measured.deadline_fault;assert.equal(gate.mode,observerDeadline);assert.equal(gate.operator.pid,measured.operator.pid);assert.equal(gate.operator.birth,measured.operator.birth);assert.equal(measured.after_attach.tracer_pid,gate.operator.pid);
 assert.equal(gate.control.pid,measured.pid);assert.equal(gate.control.birth,measured.birth);assert.equal(gate.container_id,measured.container_id);assert.equal(identity.operator_source_sha256,createHash('sha256').update(await readFile(new URL('invocation-source-retention-observer.py',import.meta.url))).digest('hex'));
 assert(gate.wrapper_deadline_monotonic-gate.alarm_deadline_monotonic-.5>=2);
 assert(actor.completed&&actor.pidfd_closed&&actor.operator_pidfd_readable);assert.equal(actor.mode,observerDeadline);assert.equal(actor.operator.birth,gate.operator.birth);assert.equal(actor.stopped.state,'T');assert.equal(actor.deadline_sample.state,'T');assert((actor.deadline_sample.pending|actor.deadline_sample.shared_pending)&8192);
 assert(actor.deadline_sample_monotonic>=gate.alarm_deadline_monotonic+.5);assert.notEqual(actor.actor.pid,gate.operator.pid);assert.notEqual(actor.actor.cgroup,gate.operator.cgroup);assert(actor.actor.cgroup.includes(gate.unit));
 assert.equal(actor.control_after_exit.pid,measured.pid);assert.equal(actor.control_after_exit.birth,measured.birth);assert.equal(actor.control_after_exit.tracer_pid,0);
 assert(command.completed&&!command.rescue_used&&command.wrapper_joined&&command.wrapper_pidfd_readable&&command.operator_absent);assert.equal(command.phase,'finished');assert.deepEqual(command.argv.slice(0,5),['timeout','--verbose','--foreground','--signal=KILL','40s']);
 assert(command.timeout_binary.path.startsWith('/'));assert.match(command.timeout_binary.sha256,/^[a-f0-9]{64}$/);assert(command.timeout_binary.version.startsWith('timeout '));assert.equal(command.timeout_signal,9);
 assert.equal(command.wrapper_executable_sha256,command.timeout_binary.sha256);
 assert.equal(command.control_before_restore.pid,measured.pid);assert.equal(command.control_before_restore.birth,measured.birth);assert.equal(command.control_before_restore.tracer_pid,0);
 assert.equal(command.stdout_sha256,evidence.metadata['source-observer-command.stdout'].sha256);assert.equal(command.stderr_sha256,evidence.metadata['source-observer-command.stderr'].sha256);
 assert.equal(command.actor_terminal.MainPID,'0');assert.equal(command.actor_terminal.Result,'success');assert.equal(command.actor_terminal.ExecMainCode,'1');assert.equal(command.actor_terminal.ExecMainStatus,'0');assert.equal(command.actor_joined.ActiveState,'inactive');assert.equal(command.actor_joined.MainPID,'0');
 if(observerDeadline==='global-alarm'){
  assert.equal(command.returncode,1);assert(command.duration>=35&&command.duration<40);assert(!command.timeout_kill_reported);assert.equal(actor.signals_sent.length,1);assert.equal(actor.signals_sent[0].signal,18);assert(actor.signals_sent[0].pidfd);
  assert.equal(measured.failure_type,'TimeoutError');assert.equal(measured.reason,'native_observation_deadline');assert.deepEqual(measured.primary_failure,{type:'TimeoutError',reason:'native_observation_deadline'});assert(!measured.cleanup_errors?.length);
  assert.equal(measured.after_detach.pid,measured.pid);assert.equal(measured.after_detach.birth,measured.birth);assert.equal(measured.after_detach.tracer_pid,0);assert(measured.reader_closed&&measured.observer_memory_closed);
  assert(driverStderr.includes(Buffer.from('source_retention_observation_failed:native_observation_deadline')));
 }else{
  assert.equal(command.returncode,124);assert(command.duration>=40&&command.duration<43);assert(command.timeout_kill_reported);assert.equal(actor.signals_sent.length,0);
  for(const key of ['after_detach','reader_closed','observer_memory_closed','failure_type'])assert(!(key in measured));assert.equal(evidence.metadata['source-observer-command.stdout'].bytes,0);
  assert(driverStderr.includes(Buffer.from('source_retention_command_exit:124')));
 }
 assert(status.restored&&!status.driver_alive&&['inactive','unknown'].includes(status.timer_state)&&['inactive','unknown'].includes(status.service_state));
 const before=observations.find(v=>v.scenario==='source-deadline-consumers-before').native,consumers=status.consumer_cleanup;assert(before.completed&&consumers);
 assert.equal(before.containers.length,2);assert.equal(before.networks.length,2);assert.equal(before.leases.length,2);
 for(const call of measured.initial.invocations){const prior=before.containers.find(v=>v.function_id===call.function_id);assert(prior);assert.equal(call.instance_id,prior.consumer_id);assert.equal(call.revision_id,prior.revision_id);}
 // @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#remplacements-après-suspension-et-inventaire-de-restitution
 // A minimum of one legitimately creates new instances after protocol deadlines expire.
 const native=consumers.native_identities;assert(native);assert.equal(consumers.installation_id,before.installation_id);
 const known=new Map(before.containers.map(v=>[v.function_id,v]));
 const sameFunction=value=>{const prior=known.get(value.function_id);assert(prior);assert.equal(value.revision_id,prior.revision_id);assert.match(value.consumer_id??value.id,/^[a-f0-9-]{36}$/);};
 for(const instance of native.instances)sameFunction(instance);
 for(const current of consumers.containers){
  const value=native.containers.find(v=>v.id===current.id);assert(value);sameFunction(value);
  assert.equal(value.installation_id,before.installation_id);assert.equal(current.consumer_id,value.consumer_id);
  assert.equal(current.image,known.get(value.function_id).image);assert.equal(value.image,current.image);assert.equal(current.kind,'instance');
  assert.equal(value.code_path,`/srv/p2enjoy-serverless/state/artifacts/${value.revision_id}/code`);
  assert(native.instances.some(v=>v.id===value.consumer_id&&v.function_id===value.function_id&&v.revision_id===value.revision_id));
  for(const id of value.network_ids)assert(native.networks.some(v=>v.id===id&&v.consumer_id===value.consumer_id&&v.function_id===value.function_id&&v.revision_id===value.revision_id));
 }
 assert.equal(native.containers.length,consumers.containers.length);assert.equal(new Set(native.containers.map(v=>v.id)).size,native.containers.length);
 assert.deepEqual(native.networks.map(v=>v.id).sort(),[...consumers.networks].sort());
 for(const network of native.networks){sameFunction(network);assert.equal(network.installation_id,before.installation_id);for(const id of network.container_ids)assert(native.containers.some(v=>v.id===id&&v.consumer_id===network.consumer_id));}
 for(const lease of consumers.leases){assert.equal(lease.installation_id,before.installation_id);assert(known.has(lease.function_id));assert(native.instances.some(v=>v.id===lease.consumer_id&&v.function_id===lease.function_id)||native.containers.some(v=>v.consumer_id===lease.consumer_id&&v.function_id===lease.function_id));}
 assert.deepEqual([...consumers.removed_containers].sort(),consumers.containers.map(v=>v.id).sort());assert.deepEqual([...consumers.removed_networks].sort(),[...consumers.networks].sort());assert.deepEqual([...consumers.released_consumers].sort(),consumers.leases.map(v=>v.consumer_id).sort());
 const physical=await physicalCleanup(),exact=await deadlineResourcesAbsent(before,consumers);
 observations.push({scenario:'physically-absent-after-deadline',physical,exact,helper_exit_code:exitCode,helper_stderr_sha256:createHash('sha256').update(driverStderr).digest('hex'),retention_qualified:false});cleanup=true;
}

// @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#remplacements-après-suspension-et-inventaire-de-restitution
async function deadlineResourcesAbsent(before,consumers){
 const native=consumers.native_identities,input={installation:before.installation_id,
  containers:[...new Set([...before.containers,...native.containers].map(v=>v.id))],
  networks:[...new Set([...before.networks,...native.networks].map(v=>v.id))],
  instances:[...new Set([...before.containers.map(v=>v.consumer_id),...native.instances.map(v=>v.id),...native.containers.map(v=>v.consumer_id),...native.networks.map(v=>v.consumer_id),...consumers.leases.map(v=>v.consumer_id)])]};
 const program='expected='+JSON.stringify(JSON.stringify(input))+'\nexpected=__import__("json").loads(expected)\n'+String.raw`
import json,os,re,shlex,socket,sqlite3,subprocess,sys
from contextlib import closing
from pathlib import Path
from uuid import UUID
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
assert str(UUID(expected['installation']))==expected['installation']
assert all(re.fullmatch('[a-f0-9]{64}',v) for key in ('containers','networks') for v in expected[key])
assert all(str(UUID(v))==v for v in expected['instances'])
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
 fields=shlex.split(line,comments=True)
 if len(fields)==1 and '=' in fields[0]:
  k,v=fields[0].split('=',1)
  if k in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_STORAGE_ROOT_HOST'):settings[k]=v
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);storage=Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def docker(*args):return subprocess.check_output(D+list(args),text=True,timeout=15).split()
containers=set(docker('ps','-aq','--no-trunc'));networks=set(docker('network','ls','-q','--no-trunc'))
checks={'exact_containers_absent':not containers.intersection(expected['containers']),
 'exact_networks_absent':not networks.intersection(expected['networks']),
 'installation_containers_absent':not docker('ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+expected['installation']),
 'installation_networks_absent':not docker('network','ls','-q','--filter','label=tech.p2enjoy.serverless.installation='+expected['installation']),
 'all_instance_channels_absent':all(not os.path.lexists(state/'execution'/v) for v in expected['instances'])}
sys.path.insert(0,'/srv/p2enjoy-serverless/e2e');from control_database import control_owner
with control_owner(state/'control.sqlite3'),closing(sqlite3.connect('file:'+str(storage/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
 leases=list(db.execute('SELECT consumer_id,installation_id FROM leases'))
checks['all_instance_leases_absent']=not {v[0] for v in leases}.intersection(expected['instances'])
checks['installation_leases_absent']=all(v[1]!=expected['installation'] for v in leases)
print(json.dumps({'completed':all(checks.values()),'checks':checks,'expected':expected}))
`;
 const result=await new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:60000,maxBuffer:2*1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});
 observations.push({scenario:'deadline-exact-resource-absence',native:result});await save();assert(result.completed);return result;
}

async function api(url,{method='GET',body,bytes,status=200,headers={}}={}){const r=await admin.fetch(base+url,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(r.status()),`${method} ${url}: ${r.status()}`);return r.json();}
async function publish(fn){const row=await api(`/api/functions/${fn.id}`),candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:fn.config.handler,events:{http:[{path:'probe',methods:['POST'],implicit:true}],schedules:fn.schedules??[]}}});const result=await api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive});assert.equal(result.state,'published');fn.revision_id=result.revision_id;fn.deployment_id=candidate.id;return result.code_hash;}
async function promote(fn,hash){const row=await api(`/api/functions/${fn.id}`);await api(`/api/functions/${fn.id}/versions/${hash}/promote`,{method:'POST',headers:{'If-Match':String(row.updated_at)}});}
async function purge(fn){if(!fn.archived){await api(`/api/functions/${fn.id}`,{method:'DELETE'});fn.archived=true;}await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await api(`/api/archives/${fn.id}`);if(!row.purged_at){const op=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});await until(async()=>{const v=await api(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'purge_not_completed');}assert((await api(`/api/archives/${fn.id}`)).purged_at);}
function terminal(state,count){assert.equal(state.invocations.length,count);assert(state.invocations.every(v=>v.state==='succeeded'&&v.handler_started&&v.completed_at&&v.instance_id));assert.equal(state.firings.length,0);}
async function streams(first,last){
 stopProducing=false;producers.length=0;
 for(const [index,fn] of functions.entries())producers.push((async()=>{try{
  for(let sequence=first;sequence<last&&!stopProducing;sequence++){
   let response;try{
    assert(!ended,'guard_ended_during_production');assert(Date.now()/1000<window-60,'production_margin_before_cron_exhausted');response=await caller.post(base+`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':reader.token},data:{sequence},timeout:30000,maxRetries:0,maxRedirects:0});
    assert.equal(response.status(),200);const body=await response.json();assert.equal(body.marker,'protected-retention-observation');assert.equal(body.sequence,sequence);assert.equal(body.request_id,response.headers()['x-serverless-request-id']);assert.match(body.request_id,/^[a-f0-9-]{36}$/);assert.equal(response.headers()['x-serverless-code-hash'],fn.hash);
    responses.push({id:body.request_id,function_id:fn.id,sequence,code_hash:fn.hash});
    if(index===0&&sequence%256===255){const alive=await api('/api/session');assert(alive.authenticated);console.log(JSON.stringify({event:'real-invocations-progress',successful:responses.length,sequence}));await save();}
   }finally{await response?.dispose();}
  }
 }catch(error){stopProducing=true;throw error;}})());
 const results=await Promise.allSettled(producers);for(const r of results)if(r.status==='rejected')throw r.reason;
}
function startLastCall(){lastCall=(async()=>{let response;try{response=await caller.post(base+`/invoke/${functions[0].id}`,{headers:{'X-Serverless-Token':reader.token},data:{sequence:5000,hold_until:(window+3)*1000},timeout:30000,maxRetries:0,maxRedirects:0});assert.equal(response.status(),200);const body=await response.json();assert.equal(body.marker,'protected-retention-observation');assert.equal(body.sequence,5000);assert.equal(body.trigger,'http');assert.equal(body.request_id,response.headers()['x-serverless-request-id']);assert.equal(response.headers()['x-serverless-code-hash'],functions[0].hash);return {id:body.request_id,function_id:functions[0].id,sequence:5000,code_hash:functions[0].hash};}finally{await response?.dispose();}})().then(value=>({value}),error=>({error}));}
async function physicalCleanup(){
 const input={functions:functions.map(v=>v.id),artifacts:functions.flatMap(v=>[v.revision_id,v.deployment_id]),instances:observations.find(v=>v.scenario==='initial-warm-instances').native.instances.map(v=>v.id)};
 const program='expected='+JSON.stringify(input)+'\n'+String.raw`
import json,os,re,shlex,socket,sqlite3,subprocess,sys
from contextlib import closing
from pathlib import Path
sys.path.insert(0,"/srv/p2enjoy-serverless/e2e")
from control_database import control_owner
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
assert all(re.fullmatch('[a-f0-9-]{36}',v) for group in expected.values() for v in group)
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
 fields=shlex.split(line,comments=True)
 if len(fields)==1 and '=' in fields[0]:
  k,v=fields[0].split('=',1)
  if k in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_STORAGE_ROOT_HOST'):settings[k]=v
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);storage=Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def absent(paths):return all(not os.path.lexists(p) for p in paths)
result={'artifacts_absent':absent(state/'artifacts'/v for v in expected['artifacts']),'channels_absent':absent(state/'execution'/v for v in expected['instances']),'backings_absent':absent(storage/'backings'/v for v in expected['functions']),'mount_directories_absent':absent(storage/'mounts'/v for v in expected['functions'])}
for identifier in expected['functions']:
 result['containers_absent_'+identifier]=not subprocess.check_output(D+['ps','-aq','--filter','label=tech.p2enjoy.serverless.function='+identifier],text=True).strip()
 result['networks_absent_'+identifier]=not subprocess.check_output(D+['network','ls','-q','--filter','label=tech.p2enjoy.serverless.function='+identifier],text=True).strip()
with control_owner(state/'control.sqlite3'):
 with closing(sqlite3.connect('file:'+str(storage/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
  leases={row[0] for row in db.execute('SELECT consumer_id FROM leases')}
result['consumer_leases_absent']=not leases.intersection(expected['instances'])
assert all(result.values());print(json.dumps({'completed':True,'checks':result}))
`;
 const result=await new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:60000,maxBuffer:1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});assert(result.completed);return result;
}
await mkdir(out,{recursive:true,mode:0o700});await save();let credentials;
try{
 assert(!process.stdin.isTTY,'private_pipe_required');const input=createInterface({input:process.stdin});credentials=await new Promise((resolve,reject)=>{input.once('line',line=>{try{assert(line.length<=8192);resolve(JSON.parse(line));}catch{reject(new Error('private_input_invalid'));}finally{input.close();}});input.once('close',()=>reject(new Error('private_input_missing')));});assert(credentials?.username&&credentials?.password);
 const image=(await run('ssh',[...ssh,'runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api'],{timeout:20000})).stdout.trim();assert.match(image,/^sha256:[a-f0-9]{64}$/);
 child=spawn('ssh',[...ssh,'python3','-B',helper,'instance-limit',campaign,image,'--guard-seconds=2700'],{stdio:['pipe','pipe','pipe']});createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});child.stderr.on('data',chunk=>{if(observerDiagnostic)driverErrors.push(chunk);});child.stdin.on('error',()=>{});child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
 let initial,before,after;
 await check('SSO réel et deux instances préchauffées dans une installation isolée de même image',async()=>{
  const armed=await event('guard-armed'),ready=await event('instance-limit-ready');assert.equal(armed.guard_seconds,2700);assert(armed.timer_schedule.includes('OnActiveUSec=45min'));assert.equal(ready.container.image,image);assert.equal(ready.capacity.invocations.length,0);
  browser=await chromium.launch({headless:true});context=await browser.newContext({locale:'fr-FR'});const page=await context.newPage();await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);credentials=null;await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();admin=context.request;session=await api('/api/session');assert(session.authenticated);caller=await request.newContext({timeout:30000});
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:'instance-limit-'+campaign.slice(0,8)}});service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'protected-invocation-history'}});reader=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-history-observations',rights:['read']}});
  window=observerDiagnostic?Math.ceil((Date.now()/1000+120)/300)*300:Math.floor(Date.now()/300000)*300+2100;
  work=await mkdtemp(new URL('retention-observation-code-',out).pathname);archive=(await publicationArchive(work,'retention-volume','protected-retention-observation.handler',['protected-retention-observation.cjs'])).bytes;
  for(const name of ['first-retention-stream','second-retention-stream']){const fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'protected-retention-observation.handler',cpu:.5,memory_mib:128,timeout_seconds:10,idle_seconds:0,min_instances:1,max_instances:1,concurrency:1,queue_timeout_seconds:30,storage:{concurrency:'shared',data:{enabled:false,quota_mib:2},cache:{enabled:false,quota_mib:2}}}}});functions.push(fn);if(functions.length===2){const date=new Date(window*1000);fn.schedules=[{cron:`${date.getUTCMinutes()} ${date.getUTCHours()} * * *`,enabled:true,timezone:'UTC'}];}await save();fn.hash=await publish(fn);await promote(fn,fn.hash);}
  initial=await until(async()=>{const s=await capacity();return s.instances.length===2&&s.instances.every(v=>v.state==='ready')?s:false;},'two_warm_instances_missing');terminal(initial,0);assert.equal(initial.instances.reduce((n,v)=>n+v.cpu_nanos,0),1000000000);assert.equal(initial.instances.reduce((n,v)=>n+v.memory_mib,0),256);assert.equal(initial.containers.length,2);for(const c of initial.containers)assert(c.running&&c.cpu_nanos===500000000&&c.memory_bytes===128*1024**2);observations.push({scenario:'initial-warm-instances',native:initial});if(observerDeadline){const consumers=await deadlineConsumersBefore(initial);observations.push({scenario:'source-deadline-consumers-before',native:consumers});}
  if(observerDiagnostic){assert(Date.now()/1000<window-30,'preparation_margin_before_cron_exhausted');assert.equal(responses.length,0);observations.push({scenario:'underfilled-history-before-boundary',window,native:initial});await save();return;}
  await streams(0,5000);assert.equal(responses.length,10000);before=await capacity();terminal(before,10000);assert.deepEqual(before.invocations.map(v=>v.id).sort(),responses.map(v=>v.id).sort());for(const fn of functions)assert.equal(responses.filter(v=>v.function_id===fn.id).length,5000);assert(Date.now()/1000<window-60,'production_margin_before_cron_exhausted');observations.push({scenario:'ten-thousand-ordinary-invocations',window,native:before});await save();
 });
 if(!observerDiagnostic){
 await check('Source exclue avant clôture puis recomptée : trois ensembles exacts10002→10001→10000',async()=>{
  let heartbeat=0;
  await until(async()=>{assert(!ended,'guard_ended_before_cron');if(Date.now()-heartbeat>10000){assert((await api('/api/session')).authenticated);heartbeat=Date.now();}return Date.now()/1000>=window-1;},'real_cron_boundary_not_reached',2400);
  assert(Date.now()/1000<window-.2,'last_http_start_frontier_missed');
  startLastCall();
  const measured=await operation('observe-source-retention',{functions:functions.map(v=>v.id),window});observations.push({scenario:'protected-and-recounted-native',native:measured});await save();assert(measured.completed&&measured.inherited_guard_lock);const last=await lastCall;if(last.error)throw last.error;responses.push(last.value);
  assert.equal(measured.before.invocations.length,10002);assert.equal(measured.protected.invocations.length,10001);assert.equal(measured.final.invocations.length,10000);const source=measured.before.invocations.find(v=>v.id===measured.before.firing.invocation_id);assert(source&&source.trigger==='schedule'&&source.handler_started&&source.state==='succeeded');assert.equal(source.function_id,functions[1].id);assert.equal(source.resolved_code_hash,functions[1].hash);assert.equal(source.schedule_slot,window);const logged=JSON.parse(source.logs.trim());assert.equal(logged.marker,'protected-retention-observation');assert.equal(logged.request_id,source.id);assert.equal(logged.trigger,'schedule');assert.equal(Date.parse(logged.slot)/1000,window);assert.equal(logged.sequence,null);
  const all=[...before.invocations.map(v=>v.id),last.value.id,source.id].sort();assert.equal(new Set(all).size,10002);assert.deepEqual(measured.before.invocations.map(v=>v.id).sort(),all);assert.equal(measured.before.firing.completed_at,null);assert.deepEqual(measured.protected.firing,measured.before.firing);assert.equal(measured.final.firing.state,'succeeded');assert.equal(measured.final.firing.id,measured.before.firing.id);
  const ordered=measured.before.invocations.filter(v=>v.id!==source.id).sort((a,b)=>b.completed_at-a.completed_at||(a.id<b.id?1:a.id>b.id?-1:0));assert.equal(measured.removed_while_protected,ordered.at(-1).id);assert.equal(measured.removed_after_close,ordered.at(-2).id);assert.deepEqual(measured.protected.invocations.map(v=>v.id).sort(),[source.id,...ordered.slice(0,10000).map(v=>v.id)].sort());assert.deepEqual(measured.final.invocations.map(v=>v.id).sort(),[source.id,...ordered.slice(0,9999).map(v=>v.id)].sort());
  after=await capacity();assert.equal(after.invocations.length,10000);assert.equal(after.firings.length,1);assert.equal(after.firings[0].id,source.schedule_firing_id);assert.equal(after.firings[0].state,'succeeded');assert.equal(responses.length,10001);for(const fn of functions)assert(after.invocations.filter(v=>v.function_id===fn.id).length<10000);
 });
 await check('Deux purges publiques puis restitution complète des originaux et gardes jointes',async()=>{
  for(const fn of functions){const row=await api(`/api/functions/${fn.id}`);await api(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,min_instances:0,idle_seconds:0}}});}
  await until(async()=>{const s=await capacity();return !s.instances.length&&!s.containers.length;},'warm_instances_not_released');await api(`/api/tokens/${reader.id}/revoke`,{method:'POST'});for(const fn of functions)await purge(fn);
  await api(`/api/services/${service.id}`,{method:'DELETE'});await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});const state=await capacity();assert.equal(state.instances.length,0);assert.equal(state.containers.length,0);assert(state.functions.every(v=>v.deleted_at));const physical=await physicalCleanup();observations.push({scenario:'purged-before-restoration',physical,invocations_preserved:state.invocations.length});
  child.stdin.end(JSON.stringify({op:'restore'})+'\n');restoration=await event('restored');assert(restoration.databases_identical&&restoration.artifacts_identical&&restoration.configuration_unchanged&&restoration.reference_unchanged&&restoration.temporary_directories_removed);assert.equal(restoration.independent,false);await until(()=>ended,'deployment_not_joined',30);assert.equal(exitCode,0);const status=await remote('status');assert(status.restored&&!status.driver_alive&&['inactive','unknown'].includes(status.timer_state)&&['inactive','unknown'].includes(status.service_state));observations.push({scenario:'restore-joined',restored:true,driver_alive:status.driver_alive,timer_state:status.timer_state,service_state:status.service_state});cleanup=true;
 });
 }else if(observerDeadline){
 await check('Borne réelle '+observerDeadline+' après attache et restitution jointe',()=>proveObserverDeadline(initial));
 }else{
 await check('Historique insuffisant après attache : refus réel, détachement et lecteur fermé, restitution jointe',async()=>{
  let heartbeat=0;
  await until(async()=>{assert(!ended,'guard_ended_before_cron');if(Date.now()-heartbeat>10000){assert((await api('/api/session')).authenticated);heartbeat=Date.now();}return Date.now()/1000>=window-1;},'real_cron_boundary_not_reached',480);
  assert(Date.now()/1000<window-.2,'last_http_start_frontier_missed');startLastCall();
  child.stdin.write(JSON.stringify({op:'observe-source-retention',functions:functions.map(v=>v.id),window})+'\n');
  await until(()=>ended,'refused_operator_and_driver_not_joined',100);
  const driverStderr=Buffer.concat(driverErrors);await writeFile(new URL('source-observer-refusal-driver-'+campaign+'.stderr',out),driverStderr,{mode:0o600});
  assert(driverStderr.includes(Buffer.from('source_retention_observation_failed:retention_history_incomplete')),'expected_helper_refusal_missing');
  assert.equal(exitCode,1);restoration=events.find(v=>v.event==='restored');
  assert(restoration&&restoration.databases_identical&&restoration.artifacts_identical&&restoration.configuration_unchanged&&restoration.reference_unchanged&&restoration.temporary_directories_removed&&restoration.control_healthy);
  assert.equal(restoration.independent,false);
  const result=await run('ssh',[...ssh,'cat','/srv/p2enjoy-serverless/qualification-history/instance-limit-'+campaign+'/source-retention-observation.json'],{timeout:20000,maxBuffer:1024*1024});
  const measured=JSON.parse(result.stdout),status=await remote('status');
  const last=await lastCall;observations.push({scenario:'underfilled-observer-refusal',native:measured,terminal_status:status,last_http:last.error?{error_type:last.error.name}:{response:last.value}});await save();
  assert.equal(measured.completed,false);assert.equal(measured.failure_type,'AssertionError');assert.equal(measured.reason,'retention_history_incomplete');assert(measured.inherited_guard_lock);
  assert.deepEqual(measured.initial_counts,{total:2,terminal:0});assert.equal(measured.running.length,2);
  assert(measured.running.every(v=>v.handler_started&&v.state==='running'&&v.completed_at===null));
  assert.deepEqual(measured.running.map(v=>v.function_id).sort(),functions.map(v=>v.id).sort());
  const heldHttp=measured.running.find(v=>v.function_id===functions[0].id),scheduled=measured.running.find(v=>v.function_id===functions[1].id),firing=measured.initial.firing;
  assert.equal(heldHttp.trigger,'http');assert.equal(scheduled.trigger,'schedule');
  assert.deepEqual(measured.initial.invocations.map(v=>v.id).sort(),measured.running.map(v=>v.id).sort());
  assert(firing&&firing.function_id===functions[1].id&&firing.window_at===window&&firing.state==='dispatched'&&firing.completed_at===null&&firing.invocation_id===scheduled.id);
  assert.equal(measured.initial.invocations.find(v=>v.id===scheduled.id).schedule_firing_id,firing.id);
  assert.equal(measured.after_attach.pid,measured.pid);assert.equal(measured.after_attach.birth,measured.birth);assert.equal(measured.after_attach.tracer_pid,measured.operator.pid);
  assert.equal(measured.after_detach.pid,measured.pid);assert.equal(measured.after_detach.birth,measured.birth);assert.equal(measured.after_detach.tracer_pid,0);assert(measured.reader_closed&&measured.observer_memory_closed);
  assert(status.restored&&!status.driver_alive&&['inactive','unknown'].includes(status.timer_state)&&['inactive','unknown'].includes(status.service_state));
  const consumers=status.consumer_cleanup,instances=initial.instances.map(v=>v.id).sort();
  assert(consumers&&consumers.containers.length===2&&consumers.networks.length===2&&consumers.leases.length===2);
  assert.deepEqual(consumers.containers.map(v=>v.consumer_id).sort(),instances);assert.deepEqual(consumers.leases.map(v=>v.consumer_id).sort(),instances);
  assert.deepEqual(consumers.containers.map(v=>v.id).sort(),initial.containers.map(v=>v.id).sort());
  const physical=await physicalCleanup();observations.push({scenario:'physically-absent-after-refusal',physical,helper_exit_code:exitCode,helper_stderr_sha256:createHash('sha256').update(driverStderr).digest('hex'),retention_qualified:false});cleanup=true;
 });
 }completed=true;
}catch(error){failure={type:error.name,operator:error.operator,code:error.code,signal:error.signal,source_line:String(error.stack??'').match(/invocation-source-retention-volume\.mjs:(\d+)/)?.[1],message_sha256:createHash('sha256').update(String(error.message)).digest('hex'),...(typeof error.actual==='number'&&typeof error.expected==='number'?{actual:error.actual,expected:error.expected}:{})};}
finally{
 credentials=null;stopProducing=true;await Promise.allSettled(producers);if(lastCall)await lastCall;
 if(!cleanup&&child){child.stdin.end();try{const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,'restore',campaign],{timeout:150000,maxBuffer:12*1024*1024});restoration=JSON.parse(stdout.trim().split('\n').at(-1));cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}catch(error){failure={...failure,restoration_error:error.name};}await until(()=>ended,'failed_deployment_not_joined',60).catch(()=>{cleanup=false;});}
 await caller?.dispose();await browser?.close();if(work)await rm(work,{recursive:true,force:true});await save();
}
assert(completed&&cleanup&&!failure,`invocation_retention_volume_failed:${report.pathname}`);console.log(JSON.stringify({completed:true,groups:checks.length,real_http_handlers:responses.length,report:report.pathname}));
