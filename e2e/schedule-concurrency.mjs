// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_CONCURRENCY.md#campagne-réelle
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_CONCURRENCY.md#nettoyage-et-portée
// Real HTTP and cron share concurrency; maximum and storage exclusivity do not bind.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rename,rm,access} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';
const base='https://serverless.lelabs.tech',root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const prefix='scheduled-functions-'+randomUUID().slice(0,8),report=new URL(prefix+'.json',out),checks=[],functions=[],observations=[],cleanupErrors=[],knownInstances={},pending=[];
const digest=value=>createHash('sha256').update(value).digest('hex');
let admin,caller,session,namespace,service,reader,work,archive,window,completed=false,cleanup=false,nativeBeforePurge,nativeAfterPurge,campaignFailure;
function diagnostic(error){return {name:error.name,message_sha256:digest(String(error.message)),...(typeof error.actual==='number'&&typeof error.expected==='number'?{actual:error.actual,expected:error.expected}:{}),location:String(error.stack??'').match(/schedule-concurrency\.mjs:\d+:\d+/)?.[0]};}
async function save(){const p=new URL(prefix+'.pending',out);await writeFile(p,JSON.stringify({completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,cleanup_errors:cleanupErrors,failure:campaignFailure,namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),functions:functions.map(v=>({id:v.id,name:v.name,config:v.config,code_hash:v.code_hash,disabled_hash:v.disabled_hash})),token_id:reader?.id,known_instances:knownInstances,window,fixture_sha256:archive?digest(archive):null,observations,native_before_purge:nativeBeforePurge,native_after_purge:nativeAfterPurge},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function until(action,message,deadline=Date.now()+60000){while(Date.now()<deadline){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:diagnostic(error)});throw error;}finally{await save();}}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){const r=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);const text=await r.text();if(reader)assert(!text.includes(reader.token),'private_token_exposed');return JSON.parse(text);}
async function native(purged=false){const v=JSON.parse((await run('python3',['-B','e2e/schedule-instance-reuse-inspect.py',JSON.stringify({namespace_id:namespace.id,function_ids:functions.map(v=>v.id),known_instances:knownInstances}),...(purged?['--purged']:[])],{cwd:root.pathname,timeout:120000,maxBuffer:8*1024*1024})).stdout);Object.assign(knownInstances,v.known_instances);observations.push({scenario:purged?'native-purged':'native-sample',native:v});await save();return v;}
const calls=async fn=>(await api(`/api/functions/${fn.id}/invocations?limit=100`)).items;
const firings=async fn=>(await api(`/api/functions/${fn.id}/schedule-firings?limit=100`)).items;
const instances=async fn=>(await api(`/api/functions/${fn.id}/instances`)).items;
async function idle(fn){await until(async()=>!(await instances(fn)).length,'instance_not_released');}
async function publish(fn,enabled){const row=await api(`/api/functions/${fn.id}`),candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:fn.config.handler,events:{http:[{path:'probe',methods:['POST'],implicit:true}],schedules:enabled?[{cron:'*/5 * * * *',enabled:true,timezone:'UTC'}]:[]}}});const result=await api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive});assert.equal(result.state,'published');return result.code_hash;}
async function promote(fn,hash){const row=await api(`/api/functions/${fn.id}`),decision=await api(`/api/functions/${fn.id}/versions/${hash}/promote`,{method:'POST',headers:{'If-Match':String(row.updated_at)}});observations.push({scenario:'promotion',function_id:fn.id,code_hash:hash,decision});await save();}
async function release(fn){if(fn.archived)return;const row=await api(`/api/functions/${fn.id}`);if(row.config.min_instances||row.config.idle_seconds){const config={...row.config,min_instances:0,idle_seconds:0};await api(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config,configuration:{environment:{},secrets:{}}}});fn.config=config;}await idle(fn);}
async function purge(fn){if(!fn.archived){await release(fn);await api(`/api/functions/${fn.id}`,{method:'DELETE'});fn.archived=true;}await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await api(`/api/archives/${fn.id}`);if(!row.purged_at){const op=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});await until(async()=>{const v=await api(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'purge_not_completed');}assert((await api(`/api/archives/${fn.id}`)).purged_at);}
function http(fn,body){const task=caller.post(`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':reader.token},data:body}).then(async r=>({status:r.status(),hash:r.headers()['x-serverless-code-hash'],body:await r.json()})).then(value=>({value}),error=>({error}));pending.push(task);return task;}
function witness(call,fn){assert.equal(call.state,'succeeded');assert(call.handler_started&&call.admitted_at&&call.instance_id);assert.equal(call.resolved_code_hash,fn.code_hash);const result=call.logs.trim().split('\n').map(v=>JSON.parse(v)).find(v=>v.event==='completed');assert(result);assert.equal(result.id,call.id);assert.equal(result.trigger,call.trigger);assert.equal(result.method,'POST');assert(!result.authorization_present);if(call.trigger==='schedule'){assert.equal(result.path,'/');assert.deepEqual(result.body,{});assert.equal(Date.parse(result.slot)/1000,call.schedule_slot);}return result;}
async function scheduled(fn,slot){return until(async()=>(await firings(fn)).find(v=>v.window_at===slot&&v.state==='succeeded'),'schedule_not_succeeded',(slot+50)*1000);}
function noResources(state){assert.equal(state.instances.length,0);assert.equal(state.containers.length,0);assert.equal(state.leases.length,0);assert.equal(state.counts.instances,0);assert.equal(state.counts.active_calls,0);assert.equal(state.counts.waiting_calls,0);assert(!Object.values(state.channels).some(Boolean));assert(!Object.values(state.networks).some(v=>v.length));}
await mkdir(out,{recursive:true,mode:0o700});let exists=true;try{await access(report);}catch(error){assert.equal(error.code,'ENOENT');exists=false;}assert(!exists);await save();
try{
 admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:90000});
 caller=await request.newContext({baseURL:base,timeout:90000});session=await api('/api/session');assert(session.authenticated,'real_sso_required');
 work=new URL((await mkdtemp(new URL(prefix+'-',out).pathname))+'/','file:');
 await writeFile(new URL('scheduled-concurrency.cjs',work),await readFile(new URL('../qualification/artifacts/scheduled-concurrency.cjs',import.meta.url)));
 await writeFile(new URL('serverless.yml',work),JSON.stringify({service:'scheduled-concurrency',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'scheduled-concurrency.handler'}},package:{patterns:['!**','*.cjs']}}));
 await run('python3',['-B','-m','adapter','package','--config',new URL('serverless.yml',work).pathname],{cwd:root.pathname});
 const manifest=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',work),'utf8'));archive=await readFile(new URL('.serverless-p2/'+manifest.artifacts.probe.file,work));
 let tasks,httpCalls,initial,waitingCall,parallelCall;
 await check('Deux HTTP actifs, maximum3 et budgets libres, seule la concurrence diffère',async()=>{
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
  service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'scheduled-concurrency'}});
  for(const [name,concurrency] of [['serialized-http-and-schedule',1],['parallel-http-and-schedule',2]]){
   const fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'scheduled-concurrency.handler',cpu:.05,memory_mib:128,timeout_seconds:60,idle_seconds:60,min_instances:0,max_instances:3,concurrency,queue_timeout_seconds:30,storage:{concurrency:'shared',data:{enabled:false,quota_mib:2},cache:{enabled:false,quota_mib:2}}}}});
   functions.push(fn);await save();fn.code_hash=await publish(fn,true);fn.disabled_hash=await publish(fn,false);assert.notEqual(fn.code_hash,fn.disabled_hash);
  }
  assert.deepEqual({...functions[0].config,concurrency:2},functions[1].config);
  reader=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'occupy-http-concurrency',rights:['read'],function_ids:functions.map(v=>v.id)}});await save();
  window=(Math.floor(Date.now()/300000)+1)*300;
  if(window-Date.now()/1000<80){await until(()=>Date.now()/1000>=window+5,'wait_before_promotions',(window+10)*1000);window+=300;}
  for(const fn of functions)await promote(fn,fn.code_hash);
  await until(()=>Date.now()/1000>=window-20,'http_boundary_wait',window*1000);
  tasks=functions.map(fn=>http(fn,{release_at_ms:(window+20)*1000}));httpCalls=[];
  for(const fn of functions)httpCalls.push(await until(async()=>(await calls(fn)).find(v=>v.state==='running'&&v.handler_started),'http_not_running',(window-6)*1000));
  initial=await native();assert(initial.sample_finished_at<window);assert.equal(initial.counts.functions,2);assert.equal(initial.counts.instances,2);assert.equal(initial.counts.active_calls,2);assert.equal(initial.counts.waiting_calls,0);
  assert.deepEqual(initial.budgets,{function_cpu_nanos:1000000000,function_memory_mib:8192,function_instance_limit:32,waiting_call_limit:128,function_waiting_call_limit:16});
  assert.equal(initial.instances.reduce((n,v)=>n+v.cpu_nanos,0),100000000);assert.equal(initial.instances.reduce((n,v)=>n+v.memory_mib,0),256);
  for(const [i,fn] of functions.entries()){
   const rows=initial.instances.filter(v=>v.function_id===fn.id);assert.equal(rows.length,1);assert.equal(rows[0].state,'busy');assert.equal(rows[0].id,httpCalls[i].instance_id);
   const container=initial.containers.find(v=>v.instance_id===rows[0].id);assert(container?.running&&container.cpu_nanos===50000000&&container.memory_bytes===128*1024**2);
  }
  observations.push({scenario:'before-boundary',http_calls:httpCalls,native:initial});
 });
 await check('Concurrence1 en file et concurrence2 réussie pendant les mêmes HTTP actifs',async()=>{
  waitingCall=await until(async()=>(await calls(functions[0])).find(v=>v.trigger==='schedule'&&v.schedule_slot===window&&v.state==='queued'),'serialized_schedule_not_queued',(window+8)*1000);
  assert(!waitingCall.handler_started&&!waitingCall.admitted_at&&!waitingCall.instance_id);
  parallelCall=await until(async()=>(await calls(functions[1])).find(v=>v.trigger==='schedule'&&v.schedule_slot===window&&v.state==='running'&&v.handler_started),'parallel_schedule_not_running',(window+8)*1000);
  const during=await native();assert(during.sample_finished_at<window+20);assert.deepEqual(during.functions,initial.functions);assert.deepEqual(during.generations,initial.generations);assert.equal(during.counts.instances,3);assert.equal(during.counts.active_calls,4);assert.equal(during.counts.waiting_calls,1);
  for(const call of httpCalls){const row=during.invocations.find(v=>v.id===call.id);assert.equal(row.state,'running');assert(row.handler_started&&!row.completed_at);}
  const waiting=during.invocations.find(v=>v.id===waitingCall.id);assert.equal(waiting.state,'queued');assert(!waiting.admitted_at&&!waiting.handler_started&&!waiting.instance_id);
  const queuedFire=during.firings.find(v=>v.invocation_id===waiting.id);assert(queuedFire);assert.equal(queuedFire.state,'dispatched');assert.equal(queuedFire.window_at,window);
  assert.equal(during.instances.filter(v=>v.function_id===functions[0].id).length,1);assert.equal(during.instances.filter(v=>v.function_id===functions[1].id).length,2);
  assert.notEqual(parallelCall.instance_id,httpCalls[1].instance_id);const executing=during.invocations.find(v=>v.id===parallelCall.id);assert.equal(executing.state,'running');assert(executing.handler_started&&!executing.completed_at);
  for(const instance of during.instances){const container=during.containers.find(v=>v.instance_id===instance.id);assert(container?.running);assert.equal(container.cpu_nanos,50000000);assert.equal(container.memory_bytes,128*1024**2);}
  assert.equal(during.containers.length,3);assert.equal(during.firings.length,2);assert.equal(during.invocations.length,4);
  observations.push({scenario:'different-concurrency-same-boundary',queued_call:waitingCall,parallel_call:parallelCall,native:during});await save();
  const fire=await scheduled(functions[1],window);parallelCall=(await calls(functions[1])).find(v=>v.id===fire.invocation_id);witness(parallelCall,functions[1]);assert(parallelCall.completed_at<window+20);
  for(const [i,fn] of functions.entries()){const row=(await calls(fn)).find(v=>v.id===httpCalls[i].id);assert.equal(row.state,'running');assert(!row.completed_at);}
  observations.push({scenario:'parallel-finished-before-http',parallel_firing:fire,parallel_call:parallelCall});
 });
 await check('Tir sérialisé réussi après libération, quatre appels et aucun rejeu',async()=>{
  const responses=[];for(const task of tasks){const result=await task;if(result.error)throw result.error;responses.push(result.value);}
  for(const [i,response] of responses.entries()){assert.equal(response.status,200);assert.equal(response.hash,functions[i].code_hash);assert(response.body.started_at_ms<window*1000&&response.body.completed_at_ms>=(window+19)*1000);}
  const fire=await scheduled(functions[0],window),state=await native();
  assert.deepEqual(state.functions,initial.functions);assert.deepEqual(state.generations,initial.generations);
  assert.equal(state.firings.length,2);assert(state.firings.every(v=>v.state==='succeeded'));assert.equal(state.invocations.length,4);assert(state.invocations.every(v=>v.state==='succeeded'));
  const serial=state.invocations.find(v=>v.id===waitingCall.id),httpDone=state.invocations.find(v=>v.id===httpCalls[0].id);
  assert.equal(fire.invocation_id,serial.id);assert(serial.admitted_at>=httpDone.completed_at);assert.equal(serial.instance_id,httpDone.instance_id);
  const parallelHttp=state.invocations.find(v=>v.id===httpCalls[1].id);assert(parallelCall.completed_at<parallelHttp.completed_at);
  for(const fn of functions)for(const call of state.invocations.filter(v=>v.function_id===fn.id)){
   witness(call,fn);if(call.trigger==='schedule'){assert.equal(call.requested_code_hash,fn.code_hash);assert.equal(call.schedule_slot,window);const firing=state.firings.find(v=>v.id===call.schedule_firing_id);assert.equal(firing.invocation_id,call.id);assert.equal(firing.code_hash,fn.code_hash);assert.equal(firing.nominal_at,window);}
  }
  observations.push({scenario:'all-finished-without-replay',http_responses:responses,native:state});
  for(const fn of functions){await release(fn);await promote(fn,fn.disabled_hash);assert.equal((await api(`/api/functions/${fn.id}/schedules`)).items.length,0);}
  const released=await native();noResources(released);observations.push({scenario:'resources-released',native:released});
 });
 await check('Deux purges publiques et absence physique des ressources',async()=>{
  nativeBeforePurge=await native();await api(`/api/tokens/${reader.id}/revoke`,{method:'POST'});
  for(const fn of functions)await purge(fn);
  await api(`/api/services/${service.id}`,{method:'DELETE'});service.deleted=true;await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});namespace.deleted=true;
  nativeAfterPurge=await native(true);assert(nativeAfterPurge.physical.completed);noResources(nativeAfterPurge);
  assert.deepEqual(nativeAfterPurge.services,initial.services);assert.deepEqual(nativeAfterPurge.official_sha256,initial.official_sha256);cleanup=true;
 });completed=true;
}catch(error){campaignFailure=diagnostic(error);
}finally{
 await Promise.all(pending);
 if(!cleanup&&admin&&session?.authenticated){
  for(const fn of functions)try{await purge(fn);}catch(error){cleanupErrors.push({function_id:fn.id,stage:'public-purge',error:diagnostic(error)});}
  if(reader)try{await api(`/api/tokens/${reader.id}/revoke`,{method:'POST',status:[200,404]});}catch(error){cleanupErrors.push({stage:'revoke',error:diagnostic(error)});}
  if(!cleanupErrors.length)try{
   if(service&&!service.deleted){await api(`/api/services/${service.id}`,{method:'DELETE'});service.deleted=true;}
   if(namespace&&!namespace.deleted){await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});namespace.deleted=true;}
   if(functions.length===2){nativeAfterPurge=await native(true);noResources(nativeAfterPurge);}cleanup=true;
  }catch(error){cleanupErrors.push({stage:'parents-or-physical',error:diagnostic(error)});}
 }
 await save();if(work)await rm(work,{recursive:true,force:true});await caller?.dispose();await admin?.dispose();
}
assert(completed&&cleanup&&!cleanupErrors.length,'campaign_or_cleanup_not_completed');console.log(JSON.stringify({completed:true,groups:checks.length,functions_purged:2,report:report.pathname}));
