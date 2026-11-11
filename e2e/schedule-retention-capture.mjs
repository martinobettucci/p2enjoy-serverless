// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-authentique-avant-vieillissement
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-authentique-avant-vieillissement
// Genuine HTTPS witnesses and a native read-only snapshot; no altered clock or rows.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rename,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';
const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const options=process.argv.slice(2),mode=options.length===0?'capture':options[0]==='--eof-after-gate'?'eof-after-gate':options[0]==='--observer-loss-after-gate'?'observer-loss-after-gate':null;
assert(mode&&(options.length===0||options.length===1),'one_known_capture_mode_required');
const prefix='scheduled-functions-'+randomUUID().slice(0,8),report=new URL('schedule-retention-'+mode+'-'+randomUUID()+'.json',out);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/schedule-recovery-operator.py';
const checks=[],events=[],cleanupErrors=[],observations=[];
let admin,session,namespace,service,fn,reader,version,work,child,ended=false,exitCode,stderr='',restored=false,unarmedJoinedHealthy=false,driverBefore,sourceAtGate,faultWindow,captureSourcesBefore,completed=false,cleanup=false;
const digest=value=>createHash('sha256').update(value).digest('hex');
async function save(){const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({target:base,mode,completed:completed&&cleanup,cleanup,skipped:0,checks,events,observations,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,function_ids:fn?[fn.id]:[],exit_code:exitCode,stderr_sha256:digest(stderr)},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function until(action,message,deadline=Date.now()+120000){while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(r=>setTimeout(r,150));}assert.fail(message);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name,message:error.message});throw error;}finally{await save();}}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){const response=await admin.fetch(base+path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()}`);return response.json();}
async function event(name,seconds=70){return until(()=>{const value=events.find(v=>v.event===name);assert(value||!ended,'capture_driver_ended_before_'+name);return value;},'capture_event_missing_'+name,Date.now()+seconds*1000);}
async function native(){return JSON.parse((await run('ssh',[...ssh,'python3','-B',helper,'inspect',fn.id,namespace.id],{timeout:40000,maxBuffer:4*1024*1024})).stdout);}
async function idle(){await until(async()=>!(await api(`/api/functions/${fn.id}/instances`)).items.length,'instances_not_released');}
async function finish(expectedCode=0){await until(()=>ended,'capture_driver_not_joined');assert.equal(exitCode,expectedCode);const receipt=events.find(v=>v.event==='restored'),guard=events.find(v=>v.event==='guard-finished');assert(receipt?.healthy&&receipt.reference_unchanged&&receipt.stop_mutator_joined);assert(guard&&Object.values(guard.states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));restored=true;return receipt;}
async function rescue(){if(!child||restored)return;child.stdin.end();const armed=events.find(v=>v.event==='guard-armed');if(!armed){await until(()=>ended,'unarmed_driver_not_joined');await until(async()=>{try{return(await admin.get(base+'/healthz')).status()===200;}catch{return false;}},'unarmed_control_not_healthy');const after=await native();assert.deepEqual(after.services,driverBefore.services);assert.deepEqual(after.official_sha256,driverBefore.official_sha256);unarmedJoinedHealthy=true;observations.push({scenario:'unarmed-driver-joined-original-healthy',native:after});return;}const result=JSON.parse((await run('ssh',[...ssh,'python3','-B',helper,'rescue',fn.id,namespace.id,armed.unit],{timeout:210000,maxBuffer:2*1024*1024})).stdout.trim().split('\n').at(-1));assert(result.healthy&&result.reference_unchanged);await until(()=>ended,'rescued_driver_not_joined');assert(Object.values(result.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));restored=true;observations.push({scenario:'emergency-restoration',receipt:result});}
async function captureSourceInventory(){
 const program=String.raw`
import hashlib,json,os,socket,stat
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
history=Path('/srv/p2enjoy-serverless/qualification-history')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while data:=f.read(1024*1024):h.update(data)
 return h.hexdigest()
result={'capture_directories':sorted(p.name for p in history.glob('schedule-retention-*') if p.is_dir()),'canonical':{}}
for name in ['schedule-retention-9a2a4cd1eb134c20b4e1c5a1a1bdc7c0','schedule-terminal-history-a3993b7d64f14650933cf03960c3d3b0']:
 folder=history/name;info=folder.lstat();assert folder.resolve()==folder and stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
 files={}
 for p in sorted(folder.rglob('*')):
  info=p.lstat();assert stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)
  if stat.S_ISREG(info.st_mode):files[str(p.relative_to(folder))]={'sha256':sha(p),'bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid}
 result['canonical'][name]={'files':len(files),'inventory_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),'metadata':{n:v for n,v in files.items() if '/' not in n}}
print(json.dumps(result))
`;
 return new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:80000,maxBuffer:2*1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});
}
async function observerAction(kill,attached=false){
 const armed=events.find(v=>v.event==='guard-armed');assert(armed);
 const expected={unit:armed.unit,function_id:fn.id,namespace_id:namespace.id,window:armed.identity.window,helper_pid:armed.identity.helper_pid,helper_birth:armed.identity.helper_birth,pid:armed.identity.pid,birth:armed.identity.birth,kill,attached};
 const program='import json\nexpected=json.loads('+JSON.stringify(JSON.stringify(expected))+')\n'+String.raw`
import hashlib,json,os,re,select,signal,socket,stat,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(25)
assert re.fullmatch('serverless-restore-schedule-[a-f0-9]{32}',expected['unit'])
folder=Path('/run')/expected['unit'];info=folder.lstat()
assert folder.resolve()==folder and stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
item=json.loads((folder/'identity.json').read_text())
assert item['mode']=='terminal-capture' and all(item[k]==expected[k] for k in ['function_id','namespace_id','window','helper_pid','helper_birth','pid','birth'])
assert hashlib.sha256((folder/'restore.py').read_bytes()).hexdigest()==item['restore_sha256']
assert hashlib.sha256(Path('/srv/p2enjoy-serverless/e2e/schedule-recovery-operator.py').read_bytes()).hexdigest()==item['operator_sha256']
assert {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in item['official_sha256']}==item['official_sha256']
def control():
 p=Path('/proc',str(item['pid']));birth=p.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]
 assert birth==item['birth'] and p.joinpath('cgroup').read_text()==item['cgroup']
 tracer=int(next(line.split(':',1)[1] for line in p.joinpath('status').read_text().splitlines() if line.startswith('TracerPid:')))
 assert p.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]==birth
 return {'pid':item['pid'],'birth':birth,'tracer_pid':tracer}
result={'completed':False,'kill':expected['kill'],'helper_pid':item['helper_pid'],'helper_birth':item['helper_birth'],'before':control()}
if expected['kill']:
 assert result['before']['tracer_pid']==item['helper_pid'],'expected_tracer_required'
 assert subprocess.check_output(['systemctl','is-active',expected['unit']+'.timer'],text=True,timeout=5).strip()=='active'
 helper=Path('/proc',str(item['helper_pid']));fd=os.pidfd_open(item['helper_pid'])
 try:
  assert helper.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]==item['helper_birth']
  argv=[v.decode() for v in helper.joinpath('cmdline').read_bytes().split(b'\0') if v]
  assert argv==['python3','-B','/srv/p2enjoy-serverless/e2e/schedule-recovery-operator.py','terminal-capture',item['function_id'],item['namespace_id'],str(item['window'])],'unexpected_helper_argv'
  signal.pidfd_send_signal(fd,signal.SIGKILL)
  result['signal']=int(signal.SIGKILL);result['pidfd_readable']=bool(select.select([fd],[],[],10)[0]);assert result['pidfd_readable'],'observer_death_unconfirmed'
 finally:os.close(fd)
if expected['attached']:
 assert not expected['kill'] and result['before']['tracer_pid']==item['helper_pid'],'expected_tracer_required'
 result['after']=result['before']
else:
 end=time.monotonic()+5
 while True:
  result['after']=control()
  if result['after']['tracer_pid']==0:break
  assert time.monotonic()<end,'native_tracer_retained';time.sleep(.01)
assert not (folder/'kill-started.json').exists(),'control_must_not_be_killed'
result['completed']=True;print(json.dumps(result))
`;
 return new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:40000,maxBuffer:1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});
}
async function failedCapture(){
 if(mode==='eof-after-gate'){
  const traceBefore=await observerAction(false,true);observations.push({scenario:'capture-eof-attached-before-close',trace:traceBefore});await save();
  child.stdin.end();const receipt=await finish(1);assert(stderr.includes('capture_command_required'));
  const trace=await observerAction(false);assert(trace.completed&&trace.after.tracer_pid===0);
  observations.push({scenario:'capture-eof-refused-and-restored',helper_exit_code:exitCode,receipt,trace});
 }else{
  const trace=await observerAction(true);observations.push({scenario:'capture-observer-killed',trace});await save();assert(trace.completed&&trace.pidfd_readable&&trace.signal===9&&trace.after.tracer_pid===0);
  await until(()=>ended,'killed_capture_observer_not_joined',Date.now()+30000);assert([137,255].includes(exitCode));
  const armed=events.find(v=>v.event==='guard-armed');
  const receipt=await until(async()=>{const r=JSON.parse((await run('ssh',[...ssh,'python3','-B',helper,'evidence',fn.id,namespace.id,armed.unit],{timeout:40000,maxBuffer:2*1024*1024})).stdout);return r.event==='restored'?r:false;},'independent_capture_restoration_missing',Date.now()+100000);
  assert(receipt.independent&&receipt.observer_gone&&receipt.healthy&&receipt.reference_unchanged&&receipt.stop_mutator_joined);assert.equal(receipt.started_at,armed.identity.started_at);
  const joined=JSON.parse((await run('ssh',[...ssh,'python3','-B',helper,'restore',fn.id,namespace.id,armed.unit],{timeout:210000,maxBuffer:2*1024*1024})).stdout.trim().split('\n').at(-1));
  assert(Object.values(joined.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));restored=true;
  observations.push({scenario:'capture-loss-independent-restoration',helper_exit_code:exitCode,receipt,guard_states:joined.guard_states});
 }
 assert(!events.some(v=>['retention-captured','control-resumed-after-capture','cut'].includes(v.event)));
}
async function purge(){await idle();if(!fn.archived){await api(`/api/functions/${fn.id}`,{method:'DELETE'});fn.archived=true;}await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await api(`/api/archives/${fn.id}`);if(!row.purged_at){const op=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});await until(async()=>{const value=await api(`/api/storage-operations/${op.id}`);assert.notEqual(value.state,'aborted');return value.state==='completed';},'purge_not_completed');observations.push({scenario:'public-purge',operation_id:op.id});}const done=await api(`/api/archives/${fn.id}`);assert(done.purged_at&&done.artifact_bytes===0&&done.revision_count===0);if(reader)await api(`/api/tokens/${reader.id}/revoke`,{method:'POST'});await api(`/api/services/${service.id}`,{method:'DELETE'});await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});const value=JSON.parse((await run('ssh',[...ssh,'python3','-B','/srv/p2enjoy-serverless/e2e/storage-console-inspect.py',"'"+JSON.stringify({[namespace.id]:[fn.id]})+"'"],{timeout:120000,maxBuffer:4*1024*1024})).stdout);assert(value.completed&&Object.values(value.physical).every(Boolean));observations.push({scenario:'physical-purge-confirmed',physical:value});cleanup=true;}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
 admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});session=await api('/api/session');assert(session.authenticated,'real_sso_required');
 if(mode!=='capture'){await until(()=>{const second=Date.now()/1000%300;return second>=10&&second<=210;},'safe_setup_boundary_not_reached',Date.now()+310000);faultWindow=(Math.floor(Date.now()/300000)+1)*300;}
 await check('Fonction réelle publiée et témoin HTTP terminal avant le tir planifié',async()=>{
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'schedule-retention-witnesses'}});
  fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'protected-source-and-expiring-http',config:{handler:'scheduled-retention.handler',cpu:.125,memory_mib:128,timeout_seconds:10,idle_seconds:0,min_instances:0,max_instances:1,concurrency:1,queue_timeout_seconds:5}}});await save();reader=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-retention-witness',rights:['read']}});
  work=await mkdtemp(new URL('schedule-retention-code-',out).pathname);const archive=await publicationArchive(work,'retention','scheduled-retention.handler',['scheduled-retention.cjs']);
  const row=await api(`/api/functions/${fn.id}`),candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-retention.handler',events:{http:[{path:'witness',methods:['POST'],implicit:true}],schedules:[{cron:'*/5 * * * *',enabled:true,timezone:'UTC'}]}}});version=await api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive.bytes});assert.equal(version.state,'published');const current=await api(`/api/functions/${fn.id}`);await api(`/api/functions/${fn.id}/versions/${version.code_hash}/promote`,{method:'POST',headers:{'If-Match':String(current.updated_at)}});
  const result=await admin.post(base+`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':reader.token},data:{}});assert.equal(result.status(),200);const witness=await result.json();assert.equal(witness.marker,'scheduled-retention-source');const calls=(await api(`/api/functions/${fn.id}/invocations`)).items;const call=calls.find(v=>v.id===result.headers()['x-serverless-request-id']);assert(call?.state==='succeeded'&&call.handler_started&&call.completed_at&&call.trigger==='http');observations.push({scenario:'genuine-http-witness',invocation:call});await idle();if(mode!=='capture'){captureSourcesBefore=await captureSourceInventory();observations.push({scenario:'source-capture-inventory-before',native:captureSourcesBefore});assert(Date.now()/1000<faultWindow-30,'fault_setup_margin_exhausted');}
 });
 await check(mode==='capture'?'Capture native RO d’une invocation réussie et de son tir encore non clos':'Perte réelle après le succès observé et restitution du même contrôle',async()=>{
  let window=mode==='capture'?(Math.floor(Date.now()/300000)+1)*300:faultWindow;if(mode==='capture'&&window-Date.now()/1000<35){await until(()=>Date.now()/1000>window+10,'next_boundary_wait',(window+20)*1000);await idle();window+=300;}
  await until(()=>Date.now()/1000>=window-15,'capture_boundary_wait',window*1000);
  driverBefore=await native();child=spawn('ssh',[...ssh,'python3','-B',helper,'terminal-capture',fn.id,namespace.id,String(window)],{stdio:['pipe','pipe','pipe']});createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});child.stderr.on('data',v=>{stderr=(stderr+v.toString()).slice(-16000);});child.stdin.on('error',()=>{});child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});await event('armed');const gated=await event('gated');const firing=gated.checkpoint.firings[0],call=gated.checkpoint.invocations[0];assert.equal(firing.state,'dispatched');assert.equal(firing.completed_at,null);assert.equal(call.state,'succeeded');assert(call.completed_at&&call.handler_started&&call.id===firing.invocation_id);assert.equal(firing.code_hash,version.code_hash);assert(events.some(v=>v.event==='handler-running-before-observation'&&v.invocation.id===call.id));sourceAtGate=gated;observations.push({scenario:'terminal-source-before-command',gated});await save();if(mode!=='capture'){await failedCapture();return;}child.stdin.write('capture\n');
  const capture=await event('retention-captured');assert.deepEqual(capture.firing,firing);assert.deepEqual(Object.fromEntries(Object.keys(call).map(k=>[k,capture.invocation[k]])),call);assert.equal(capture.invocation.resolved_code_hash,version.code_hash);assert.equal(capture.invocation.schedule_slot,window);assert.equal(capture.invocation.trigger,'schedule');const received=JSON.parse(capture.invocation.logs.trim());assert.equal(received.marker,'scheduled-retention-source');assert.equal(received.request_id,call.id);assert.equal(received.trigger,'schedule');assert.equal(Date.parse(received.slot)/1000,window);assert.equal(received.method,'POST');assert.equal(received.path,'/');assert.deepEqual(received.body,{});assert(!received.authorization_present&&!received.platform_token_present);const http=observations[0].invocation;assert.equal(capture.http_witness.id,http.id);assert.equal(capture.http_witness.completed_at,http.completed_at);assert(capture.source_read_only&&capture.dates_unchanged&&capture.private_capture_preserved);assert.equal(capture.eligible_after,Math.max(call.completed_at,http.completed_at)+604801);assert(capture.eligible_after>Date.now()/1000);assert(capture.artifact_files>0);observations.push({scenario:'authentic-retention-capture',capture});await finish();
 });
 await check('Reprise immédiate du même contrôle et clôture normale sans rejeu',async()=>{
  const original=events.find(v=>v.event==='guard-armed').identity,after=await native(),capture=observations.find(v=>v.scenario==='authentic-retention-capture')?.capture;assert.equal(after.services[0].id,original.container_id);assert.equal(after.services[0].image,original.image);assert.equal(after.services[0].started_at,original.started_at);assert.deepEqual(after.official_sha256,original.official_sha256);const firing=after.firings.find(v=>v.id===(capture?.firing.id??sourceAtGate.checkpoint.firings[0].id));assert.equal(firing.state,'succeeded');assert(firing.completed_at);assert.equal(after.invocations.filter(v=>v.schedule_firing_id===firing.id).length,1);if(mode==='capture')assert(events.some(v=>v.event==='control-resumed-after-capture'));else{assert.equal(after.invocations.length,2);assert.equal(after.firings.length,1);assert(after.invocations.every(v=>v.state==='succeeded'&&v.handler_started&&v.completed_at));const source=sourceAtGate.checkpoint.invocations[0],http=observations.find(v=>v.scenario==='genuine-http-witness').invocation;
   assert.deepEqual(after.invocations.map(v=>v.id).sort(),[http.id,source.id].sort());
   assert.equal(after.invocations.find(v=>v.id===http.id).completed_at,http.completed_at);assert.equal(after.invocations.find(v=>v.id===source.id).completed_at,source.completed_at);
   const captureSourcesAfter=await captureSourceInventory();observations.push({scenario:'source-capture-inventory-after',native:captureSourcesAfter});assert.deepEqual(captureSourcesAfter,captureSourcesBefore);}assert(!events.some(v=>v.event==='cut'));observations.push({scenario:'same-control-resumed-and-firing-settled',native:after});
 });
 await check(mode==='capture'?'Purge publique de la fixture et conservation privée du témoin de vieillissement':'Purge publique de la fixture et absence physique après la perte',async()=>{await purge();});completed=true;
}finally{
 if(child&&!restored)try{await rescue();}catch(error){cleanupErrors.push({step:'capture-restoration',type:error.name});}
 if(!cleanup&&fn&&(!child||restored||unarmedJoinedHealthy))try{await purge();}catch(error){cleanupErrors.push({step:'public-cleanup',type:error.name});}
 if(!fn)try{if(service)await api(`/api/services/${service.id}`,{method:'DELETE'});if(namespace)await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});cleanup=true;}catch(error){cleanupErrors.push({step:'partial-cleanup',type:error.name});}
 await admin?.dispose();if(work)await rm(work,{recursive:true,force:true});if(cleanupErrors.length)completed=false;await save();
 if(stderr)await writeFile(new URL(report.pathname+'.stderr','file:'),stderr,{mode:0o600});
}
assert(completed&&cleanup&&!cleanupErrors.length,`retention_capture_failed:${report.pathname}`);console.log(JSON.stringify({completed:true,groups:checks.length,report:report.pathname}));
