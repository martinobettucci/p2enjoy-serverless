// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues
// Real deployed cron validation, forecasts and Docker handlers on actual UTC windows.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rename,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';
const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),root=new URL('../',import.meta.url);
const prefix='scheduled-functions-'+randomUUID().slice(0,8),report=new URL(prefix+'.json',out),run=promisify(execFile);
const checks=[],functions=[],cleanupErrors=[],observations=[],forecasts=[],refusals=[];
let admin,session,namespace,service,work,completed=false,window,definitions,plan,nativeBeforePurge,nativeAfterPurge;
const digest=value=>createHash('sha256').update(value).digest('hex');
async function save(){const pending=new URL(prefix+'.pending',out);await writeFile(pending,JSON.stringify({target:base,completed,skipped:0,checks,cleanup_errors:cleanupErrors,
 namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),window,definitions,plan,observations,forecasts,refusals,native_before_purge:nativeBeforePurge,native_after_purge:nativeAfterPurge},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function native(purged=false){return JSON.parse((await run('python3',['-B','e2e/schedule-versions-inspect.py',JSON.stringify({namespace_id:namespace.id,function_ids:functions.map(v=>v.id)}),...(purged?['--purged']:[])],{cwd:root.pathname,timeout:120000,maxBuffer:4*1024*1024})).stdout);}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){
  const response=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,
    ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()}`);return response.json();
}
async function until(action,deadline=Date.now()+120000){while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,500));}assert.fail('real_schedule_version_deadline');}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name,message:error.message});await save();throw error;}}
async function purge(fn){
  if(!fn.archived){await until(async()=>!(await api(`/api/functions/${fn.id}/instances`)).items.length);
    await api(`/api/functions/${fn.id}`,{method:'DELETE'});fn.archived=true;}
  await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation);
  const row=await api(`/api/archives/${fn.id}`);const command=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
  await until(async()=>{const state=await api(`/api/storage-operations/${command.id}`);assert.notEqual(state.state,'aborted');return state.state==='completed';});
  const result=await api(`/api/archives/${fn.id}`);assert.equal(result.artifact_bytes,0);assert.equal(result.revision_count,0);
}

function declaration(cron,slots){return {cron,slots};}
async function history(fn){return api(`/api/functions/${fn.id}/schedule-firings?limit=100`);}
await mkdir(out,{recursive:true});await save();
try{
 admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});session=await api('/api/session');assert(session.authenticated,'real_sso_session_required');
 await check('Manifeste numérique réel : listes, plages, pas et déclarations avant leurs nominaux',async()=>{
  window=Math.ceil((Date.now()/1000+360)/300)*300;
  if(new Date(window*1000).getUTCMinutes()===0)window+=300;
  const date=new Date(window*1000),day=date.getUTCDate(),weekday=date.getUTCDay(),wrongDay=day===1?2:1,wrongWeekday=(weekday+1)%7,month=date.getUTCMonth()+1,hour=date.getUTCHours();
  const slots=Array.from({length:5},(_,i)=>window-240+i*60),minutes=slots.map(v=>new Date(v*1000).getUTCMinutes());
  const selected=[slots[1],slots[3]],list=selected.map(v=>new Date(v*1000).getUTCMinutes()).join(',');
  definitions=[
   {name:'minute-lists-ranges-steps',declarations:[declaration(`${list} * * * *`,selected),declaration('0-59/2 * * * *',slots.filter((_,i)=>minutes[i]%2===0)),declaration('1/2 * * * *',slots.filter((_,i)=>minutes[i]%2===1))]},
   {name:'day-or-weekday',declarations:[declaration(`*/5 * ${day} * ${wrongWeekday}`,[window]),declaration(`*/5 * ${wrongDay} * ${weekday}`,[window]),declaration(`*/5 * ${day} * ${weekday}`,[window]),declaration(`*/5 * ${wrongDay} * ${wrongWeekday}`,[]),declaration(`*/5 * ${wrongDay} * *`,[])]},
   {name:'calendar-forecasts',declarations:[declaration(`* ${hour}/24 * ${month}/12 *`,slots),declaration(`* ${hour},${(hour+1)%24} * 1-12 *`,slots),declaration('0 12 * * 0',[]),declaration('0 12 * * 7',[]),declaration('0 0 31 2 *',[]),declaration('0 0 29 2 *',[]),declaration(`*/5 * * ${month===1?2:1} *`,[])]}
  ];
  // The selected window never crosses an hour, so the Sunday-at-noon and
  // leap-day-at-midnight declarations cannot belong to it, on any calendar day.
  work=new URL((await mkdtemp(new URL(prefix+'-',out).pathname))+'/','file:');
  await writeFile(new URL('scheduled-event.cjs',work),await readFile(new URL('../qualification/artifacts/scheduled-event.cjs',import.meta.url)));
  const manifest={service:'numeric-schedule-calendar',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:Object.fromEntries(definitions.map(v=>[v.name,{handler:'scheduled-event.handler',events:v.declarations.map(d=>({schedule:{rate:d.cron,enabled:true}}))}])),package:{patterns:['!**','scheduled-event.cjs']}};
  await writeFile(new URL('serverless.yml',work),JSON.stringify(manifest));
  const result=await run('python3',['-B','-m','adapter','plan','--config',new URL('serverless.yml',work).pathname],{cwd:root.pathname});plan=JSON.parse(result.stdout);assert.equal(plan.functions.length,3);
  await run('python3',['-B','-m','adapter','package','--config',new URL('serverless.yml',work).pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',work),'utf8'));
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'numeric-schedule-calendar'}});
  for(const definition of definitions){
   const fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:definition.name,config:{handler:'scheduled-event.handler',cpu:0.125,memory_mib:128,timeout_seconds:20,idle_seconds:0,min_instances:0,max_instances:3,concurrency:3,queue_timeout_seconds:10}}});functions.push(fn);await save();
   const planned=plan.functions.find(v=>v.name===definition.name);assert.deepEqual(planned.events.schedules,definition.declarations.map(d=>({cron:d.cron,enabled:true,timezone:'UTC'})));
   const current=await api(`/api/functions/${fn.id}`),candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(current.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-event.handler',events:planned.events}});
   const bytes=await readFile(new URL('.serverless-p2/'+descriptor.artifacts[definition.name].file,work));const published=await api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes});assert.equal(published.state,'published');fn.hash=published.code_hash;
   const row=await api(`/api/functions/${fn.id}`);await api(`/api/functions/${fn.id}/versions/${fn.hash}/promote`,{method:'POST',headers:{'If-Match':String(row.updated_at)}});
  }
  assert(Date.now()/1000<window-240,'all_declarations_must_precede_full_target_window');
 });
 await check('Refus réels des bornes, listes, plages et pas invalides',async()=>{
  const fn=functions[0],row=await api(`/api/functions/${fn.id}`);
  for(const cron of ['-1 * * * *','60 * * * *','* 24 * * *','* * 0 * *','* * * 13 *','* * * * 8','1,,2 * * * *','5-1 * * * *','*/0 * * * *','*/61 * * * *','1/0 * * * *','0 * * * * *']){
   await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:422,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-event.handler',events:{http:[],schedules:[{cron,enabled:true,timezone:'UTC'}]}}});refusals.push({cron,status:422});
  }
 });
 await check('Prévisions réelles : dimanche0/7, date impossible et prochain29février',async()=>{
  const fn=functions[2],before=await native(),data=await api(`/api/functions/${fn.id}/schedules`),after=await native(),observedAt=Date.now()/1000;
  forecasts.push({before_cursor:before.cursor,after_cursor:after.cursor,observed_at:observedAt,data});
  // Bracket a real cursor advance during the API request. A nominal awaiting
  // its unprocessed boundary is eligible even when wall-clock time passed it.
  const anchors=index=>[Math.max(before.cursor,data.items[index].activated_at),Math.max(after.cursor,Math.floor(observedAt/300)*300,data.items[index].activated_at)];
  const followingSunday=anchor=>{const date=new Date(anchor*1000);let slot=Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate(),12)/1000+((7-date.getUTCDay())%7)*86400;if(slot<=anchor)slot+=7*86400;return slot;};
  const followingLeapDay=anchor=>{let year=new Date(anchor*1000).getUTCFullYear(),date;do{date=new Date(Date.UTC(year++,1,29));}while(date.getUTCMonth()!==1||date.getUTCDate()!==29||date.getTime()/1000<=anchor);return date.getTime()/1000;};
  assert.deepEqual(data.items[2].next,data.items[3].next);const sunday=data.items[2].next;assert(sunday);assert(anchors(2).map(followingSunday).includes(sunday.nominal_at));assert.equal(sunday.coalesced,1);assert.equal(sunday.window_at,sunday.nominal_at);
  assert.equal(data.items[4].next,null);
  assert(anchors(5).map(followingLeapDay).includes(data.items[5].next.nominal_at));assert.equal(data.items[5].next.coalesced,1);assert.equal(data.items[5].next.window_at,data.items[5].next.nominal_at);
 });
 await check('Fenêtre réelle : listes/plages/pas, OU des jours et fusion sans double tir',async()=>{
  for(let f=0;f<functions.length;f++){
   const fn=functions[f],definition=definitions[f],expected=definition.declarations.filter(d=>d.slots.length).length;
   const rows=await until(async()=>{const items=(await history(fn)).items.filter(v=>v.window_at===window);if(items.length<expected||items.some(v=>!v.completed_at))return false;assert.equal(items.length,expected);assert(items.every(v=>v.state==='succeeded'));return items;},window*1000+60000);
   const calls=(await api(`/api/functions/${fn.id}/invocations?limit=100`)).items;
   for(let index=0;index<definition.declarations.length;index++){
    const declaration=definition.declarations[index],firing=rows.find(v=>v.schedule_index===index);
    if(!declaration.slots.length){assert(!firing);continue;}
    assert(firing);assert.equal(firing.expression,declaration.cron);assert.equal(firing.coalesced,declaration.slots.length);assert.equal(firing.nominal_at,declaration.slots.at(-1));assert.equal(firing.code_hash,fn.hash);assert(firing.dispatched_at>=window&&firing.dispatched_at-window<=5);
    const call=calls.find(v=>v.id===firing.invocation_id);assert(call&&call.state==='succeeded');assert.equal(call.resolved_code_hash,fn.hash);assert.equal(call.trigger,'schedule');
    const witness=JSON.parse(call.logs.trim());assert.equal(witness.marker,'scheduled-original-A');assert.equal(witness.trigger,'schedule');assert.equal(Date.parse(witness.slot)/1000,firing.nominal_at);assert.deepEqual(witness.body,{});observations.push({function_id:fn.id,firing,invocation:call});await save();
   }
  }
  assert.equal(observations.length,8);
 });
 await check('Recoupement natif des huit tirs de la fenêtre et absence des déclarations exclues',async()=>{
  nativeBeforePurge=await native();assert(nativeBeforePurge.cursor>=window);const fires=nativeBeforePurge.firings.filter(v=>v.window_at===window);assert.equal(fires.length,8);
  assert.deepEqual(fires.map(v=>v.id).sort(),observations.map(v=>v.firing.id).sort());assert(fires.every(v=>v.state==='succeeded'));
  const calls=nativeBeforePurge.invocations.filter(v=>v.schedule_slot>=window-240&&v.schedule_slot<=window);assert.equal(calls.length,8);assert.deepEqual(calls.map(v=>v.id).sort(),observations.map(v=>v.invocation.id).sort());
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
