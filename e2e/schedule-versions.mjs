// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009
// Real HTTPS publications, promotions and UTC windows on the deployed DEV control.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rename,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';
const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),root=new URL('../',import.meta.url);
const prefix='scheduled-functions-'+randomUUID().slice(0,8),report=new URL(prefix+'.json',out);
const run=promisify(execFile),checks=[],functions=[],observations=[],decisions=[],cleanupErrors=[];
const events={http:[],schedules:[{cron:'*/5 * * * *',enabled:true,timezone:'UTC'}]};
let admin,session,namespace,service,work,archive,completed=false,firstWindow,nativeBeforePurge,nativeAfterPurge,disabledInventory;
const digest=value=>createHash('sha256').update(value).digest('hex');
async function save(){const pending=new URL(prefix+'.pending',out);await writeFile(pending,JSON.stringify({target:base,completed,skipped:0,checks,cleanup_errors:cleanupErrors,
  namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),first_window:firstWindow,
  fixture_sha256:archive?digest(archive):null,observations,decisions,native_before_purge:nativeBeforePurge,native_after_purge:nativeAfterPurge},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function native(purged=false){return JSON.parse((await run('python3',['-B','e2e/schedule-versions-inspect.py',JSON.stringify({namespace_id:namespace.id,function_ids:functions.map(v=>v.id)}),...(purged?['--purged']:[])],{cwd:root.pathname,timeout:120000,maxBuffer:4*1024*1024})).stdout);}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){
  const response=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,
    ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()}`);return response.json();
}
async function until(action,deadline=Date.now()+120000){while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,500));}assert.fail('real_schedule_version_deadline');}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name,message:error.message});await save();throw error;}}
async function publish(fn,handler,declarations=events){const row=await api(`/api/functions/${fn.id}`);
  const candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-versions.'+handler,events:declarations}});
  const result=await api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive});
  assert.equal(result.state,'published');assert.match(result.code_hash,/^[0-9a-f]{64}$/);return result;
}
async function decide(fn,hash,action='promote',body){const row=await api(`/api/functions/${fn.id}`);
  const result=await api(`/api/functions/${fn.id}/versions/${hash}/${action}`,{method:'POST',body,headers:{'If-Match':String(row.updated_at)}});
  decisions.push({function_id:fn.id,code_hash:hash,action,body:body??null,result,observed_at:Date.now()/1000});await save();return result;
}
async function history(fn){return api(`/api/functions/${fn.id}/schedule-firings?limit=100`);}
async function admitted(fn,window,hash){return until(async()=>{
  const firing=(await history(fn)).items.find(v=>v.window_at===window&&v.invocation_id);
  if(!firing)return false;
  assert.equal(firing.code_hash,hash);assert.equal(firing.state,'dispatched');
  const invocation=(await api(`/api/functions/${fn.id}/invocations?limit=100`)).items.find(v=>v.id===firing.invocation_id);
  if(!invocation?.handler_started)return false;
  assert.equal(invocation.state,'running');assert.equal(invocation.resolved_code_hash,hash);
  return {firing,invocation};
},window*1000+15000);}
async function finished(fn,window,hash,marker,decision){const firing=await until(async()=>{
  const value=(await history(fn)).items.find(v=>v.window_at===window&&v.completed_at);if(!value)return false;
  assert.equal(value.state,'succeeded');return value;
},window*1000+60000);
  const invocation=(await api(`/api/functions/${fn.id}/invocations?limit=100`)).items.find(v=>v.id===firing.invocation_id);
  assert.equal(firing.code_hash,hash);assert.equal(invocation.resolved_code_hash,hash);assert.equal(invocation.state,'succeeded');
  assert.equal(invocation.trigger,'schedule');assert.equal(firing.coalesced,1);assert.equal(firing.nominal_at,window);
  assert(firing.dispatched_at>=window&&firing.dispatched_at-window<=5);
  const witness=JSON.parse(invocation.logs.trim());assert.equal(witness.marker,marker);assert.deepEqual(witness.body,{});
  assert.equal(witness.method,'POST');assert.equal(witness.path,'/');assert.equal(witness.trigger,'schedule');assert.equal(Date.parse(witness.slot)/1000,window);
  assert(witness.completed_at_ms-witness.started_at_ms>=20000);
  if(decision){assert(witness.started_at_ms/1000<decision.result.function_version);assert(decision.observed_at<witness.completed_at_ms/1000);}
  observations.push({function_id:fn.id,firing,invocation});await save();return firing;
}
async function purge(fn){
  if(!fn.archived){await until(async()=>!(await api(`/api/functions/${fn.id}/instances`)).items.length);
    await api(`/api/functions/${fn.id}`,{method:'DELETE'});fn.archived=true;}
  await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation);
  const row=await api(`/api/archives/${fn.id}`);const command=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
  await until(async()=>{const state=await api(`/api/storage-operations/${command.id}`);assert.notEqual(state.state,'aborted');return state.state==='completed';});
  const result=await api(`/api/archives/${fn.id}`);assert.equal(result.artifact_bytes,0);assert.equal(result.revision_count,0);
}
await mkdir(out,{recursive:true});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});
  session=await api('/api/session');assert(session.authenticated,'real_sso_session_required');
  work=new URL((await mkdtemp(new URL(prefix+'-',out).pathname))+'/','file:');
  await writeFile(new URL('scheduled-versions.cjs',work),await readFile(new URL('../qualification/artifacts/scheduled-versions.cjs',import.meta.url)));
  await writeFile(new URL('serverless.yml',work),JSON.stringify({service:'scheduled-version-lifecycle',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'scheduled-versions.primary'}},package:{patterns:['!**','scheduled-versions.cjs']}}));
  await run('python3',['-B','-m','adapter','package','--config',new URL('serverless.yml',work).pathname],{cwd:root.pathname});
  const manifest=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',work),'utf8'));
  archive=await readFile(new URL('.serverless-p2/'+manifest.artifacts.probe.file,work));
  await check('Versions préparées, pilote conservé et objets prêts avant la frontière',async()=>{
    namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
    service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'scheduled-version-lifecycle'}});
    for(const name of ['promoted-hash-cycle','disabled-default','archived-function']){
      const fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'scheduled-versions.primary',cpu:0.125,memory_mib:128,timeout_seconds:45,idle_seconds:0,min_instances:0,max_instances:1,concurrency:1,queue_timeout_seconds:5}}});functions.push(fn);await save();
      fn.a=await publish(fn,'primary');await decide(fn,fn.a.code_hash);
    }
    const fn=functions[0];fn.b=await publish(fn,'secondary');assert.notEqual(fn.b.code_hash,fn.a.code_hash);
    fn.c=await publish(fn,'primary',{http:[],schedules:[]});assert.notEqual(fn.c.code_hash,fn.a.code_hash);
    assert.equal((await api(`/api/functions/${fn.id}/schedules`)).items[0].code_hash,fn.a.code_hash);
    firstWindow=(Math.floor(Date.now()/300000)+1)*300;if(firstWindow-Date.now()/1000<30)firstWindow+=300;
    assert(Date.now()/1000<firstWindow-20);
  });
  await check('A admise malgré B pilote ; promotion B pendant A, désactivation et archivage',async()=>{
    const fn=functions[0];await admitted(fn,firstWindow,fn.a.code_hash);
    await decide(fn,fn.b.code_hash);const decision=decisions.at(-1);
    assert.equal((await api(`/api/functions/${fn.id}/schedules`)).items[0].code_hash,fn.b.code_hash);
    await finished(fn,firstWindow,fn.a.code_hash,'scheduled-version-A',decision);
    for(const other of functions.slice(1))await finished(other,firstWindow,other.a.code_hash,'scheduled-version-A');
    const disabled=functions[1];await decide(disabled,disabled.a.code_hash,'archive',{disable_default:true});
    disabledInventory=(await history(disabled)).items.map(v=>v.id).sort();
    assert.equal((await api(`/api/functions/${disabled.id}/schedules`)).items.length,0);
    const archived=functions[2];await until(async()=>!(await api(`/api/functions/${archived.id}/instances`)).items.length);
    await api(`/api/functions/${archived.id}`,{method:'DELETE'});archived.archived=true;
    await api(`/api/functions/${archived.id}/schedules`,{status:404});
    assert(Date.now()/1000<firstWindow+300);
  });
  await check('B tirée puis archivée pendant son handler, retour explicite à A',async()=>{
    const fn=functions[0];await admitted(fn,firstWindow+300,fn.b.code_hash);
    await decide(fn,fn.b.code_hash,'archive',{replacement_code_hash:fn.a.code_hash});const decision=decisions.at(-1);
    assert.equal((await api(`/api/functions/${fn.id}/schedules`)).items[0].code_hash,fn.a.code_hash);
    await finished(fn,firstWindow+300,fn.b.code_hash,'scheduled-version-B',decision);
    assert.deepEqual((await history(functions[1])).items.map(v=>v.id).sort(),disabledInventory);
  });
  await check('A retirée des planifications pendant son handler, instantané terminé',async()=>{
    const fn=functions[0];await admitted(fn,firstWindow+600,fn.a.code_hash);
    await decide(fn,fn.c.code_hash);const decision=decisions.at(-1);
    assert.equal((await api(`/api/functions/${fn.id}/schedules`)).items.length,0);
    await finished(fn,firstWindow+600,fn.a.code_hash,'scheduled-version-A',decision);
  });
  await check('Fenêtre suivante sans tir après retrait, désactivation ou suppression',async()=>{
    await until(async()=>Date.now()/1000>=firstWindow+910,(firstWindow+915)*1000);
    const fn=functions[0];const rows=await history(fn);const selected=rows.items.filter(v=>v.window_at>=firstWindow);
    assert.deepEqual(selected.map(v=>[v.window_at,v.code_hash]).sort((a,b)=>a[0]-b[0]),[[firstWindow,fn.a.code_hash],[firstWindow+300,fn.b.code_hash],[firstWindow+600,fn.a.code_hash]]);
    assert.deepEqual((await history(functions[1])).items.map(v=>v.id).sort(),disabledInventory);
    assert.equal((await api(`/api/functions/${functions[1].id}/schedules`)).items.length,0);
    await api(`/api/functions/${functions[2].id}/schedule-firings`,{status:404});
    const health=await api('/healthz');assert.equal(health.status,'ok');
    nativeBeforePurge=await native();assert(nativeBeforePurge.cursor>=firstWindow+900);
    for(const other of functions.slice(1)){
      assert(!nativeBeforePurge.generations.some(v=>v.function_id===other.id&&v.retired_at===null));
      const fires=nativeBeforePurge.firings.filter(v=>v.function_id===other.id&&v.window_at>=firstWindow);
      assert.equal(fires.length,1);assert.equal(fires[0].window_at,firstWindow);assert.equal(fires[0].state,'succeeded');
      const calls=nativeBeforePurge.invocations.filter(v=>v.function_id===other.id&&v.created_at>=firstWindow);
      assert.equal(calls.length,1);assert.equal(calls[0].id,fires[0].invocation_id);
    }
    await save();
  });
  completed=true;
}finally{
  for(const fn of functions)try{await purge(fn);}catch(error){cleanupErrors.push({function_id:fn.id,error:error.name,message:error.message});}
  if(service&&!cleanupErrors.length)try{await api(`/api/services/${service.id}`,{method:'DELETE'});await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({parents:true,error:error.name,message:error.message});}
  if(namespace&&!service&&!cleanupErrors.length)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({namespace:true,error:error.name,message:error.message});}
  if(namespace&&functions.length===3&&!cleanupErrors.length)try{nativeAfterPurge=await native(true);}catch(error){cleanupErrors.push({native_cleanup:true,error:error.name,message:error.message});}
  if(cleanupErrors.length)completed=false;await save();await admin?.dispose();if(work)await rm(work,{recursive:true,force:true});
  console.log(JSON.stringify({completed,groups:checks.filter(v=>v.status==='passed').length,report:report.pathname,cleanup_errors:cleanupErrors.length}));
}
assert(completed);
