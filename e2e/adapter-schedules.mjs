// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_ADAPTER.md#campagne-réelle
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_ADAPTER.md#campagne-réelle
// Real CLI plan/deploy/promote, genuine scheduled invocation and disabled cron.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rename,rm,access} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';
const base='https://serverless.lelabs.tech',root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const prefix='scheduled-functions-'+randomUUID().slice(0,8),report=new URL(prefix+'.json',out),checks=[],functions=[],observations=[],cleanupErrors=[],knownInstances={};
const digest=value=>createHash('sha256').update(value).digest('hex');
let admin,session,namespace,service,reader,work,archive,window,completed=false,cleanup=false,nativeBeforePurge,nativeAfterPurge,campaignFailure;
function diagnostic(error){return {name:error.name,message_sha256:digest(String(error.message)),...(typeof error.actual==='number'&&typeof error.expected==='number'?{actual:error.actual,expected:error.expected}:{}),location:String(error.stack??'').match(/adapter-schedules\.mjs:\d+:\d+/)?.[0]};}
async function save(){const p=new URL(prefix+'.pending',out);await writeFile(p,JSON.stringify({completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,cleanup_errors:cleanupErrors,failure:campaignFailure,namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),functions:functions.map(v=>({id:v.id,name:v.name,config:v.config,code_hash:v.code_hash,disabled_hash:v.disabled_hash})),token_id:reader?.id,known_instances:knownInstances,window,fixture_sha256:archive?digest(archive):null,observations,native_before_purge:nativeBeforePurge,native_after_purge:nativeAfterPurge},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function until(action,message,deadline=Date.now()+60000){while(Date.now()<deadline){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:diagnostic(error)});throw error;}finally{await save();}}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){const r=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);const text=await r.text();if(reader)assert(!text.includes(reader.token),'private_token_exposed');return JSON.parse(text);}
async function native(purged=false){const v=JSON.parse((await run('python3',['-B','e2e/schedule-instance-reuse-inspect.py',JSON.stringify({namespace_id:namespace.id,function_ids:functions.map(v=>v.id),known_instances:knownInstances}),...(purged?['--purged']:[])],{cwd:root.pathname,timeout:120000,maxBuffer:8*1024*1024})).stdout);Object.assign(knownInstances,v.known_instances);observations.push({scenario:purged?'native-purged':'native-sample',native:v});await save();return v;}
const calls=async fn=>(await api(`/api/functions/${fn.id}/invocations?limit=100`)).items;
const firings=async fn=>(await api(`/api/functions/${fn.id}/schedule-firings?limit=100`)).items;
const instances=async fn=>(await api(`/api/functions/${fn.id}/instances`)).items;
async function idle(fn){await until(async()=>!(await instances(fn)).length,'instance_not_released');}
async function release(fn){if(fn.archived)return;const row=await api(`/api/functions/${fn.id}`);if(row.config.min_instances||row.config.idle_seconds){const config={...row.config,min_instances:0,idle_seconds:0};await api(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config,configuration:{environment:{},secrets:{}}}});fn.config=config;}await idle(fn);}
async function purge(fn){if(!fn.archived){await release(fn);await api(`/api/functions/${fn.id}`,{method:'DELETE'});fn.archived=true;}await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await api(`/api/archives/${fn.id}`);if(!row.purged_at){const op=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});await until(async()=>{const v=await api(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'purge_not_completed');}assert((await api(`/api/archives/${fn.id}`)).purged_at);}
function witness(call,fn){assert.equal(call.state,'succeeded');assert(call.handler_started&&call.admitted_at&&call.instance_id);assert.equal(call.resolved_code_hash,fn.code_hash);const result=call.logs.trim().split('\n').map(v=>JSON.parse(v)).find(v=>v.event==='completed');assert(result);assert.equal(result.id,call.id);assert.equal(result.trigger,call.trigger);assert.equal(result.method,'POST');assert(!result.authorization_present);if(call.trigger==='schedule'){assert.equal(result.path,'/');assert.deepEqual(result.body,{});assert.equal(Date.parse(result.slot)/1000,call.schedule_slot);}return result;}
async function scheduled(fn,slot){return until(async()=>(await firings(fn)).find(v=>v.window_at===slot&&v.state==='succeeded'),'schedule_not_succeeded',(slot+50)*1000);}
function noResources(state){assert.equal(state.instances.length,0);assert.equal(state.containers.length,0);assert.equal(state.leases.length,0);assert.equal(state.counts.instances,0);assert.equal(state.counts.active_calls,0);assert.equal(state.counts.waiting_calls,0);assert(!Object.values(state.channels).some(Boolean));assert(!Object.values(state.networks).some(v=>v.length));}
async function cli(args){
 const result=await run('python3',['-B','-m','adapter',...args],{cwd:root.pathname,timeout:180000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,...(reader?{P2_SERVERLESS_TOKEN:reader.token}:{})}});
 assert(!result.stderr.includes('Traceback'));for(const stream of [result.stdout,result.stderr])if(reader)assert(!stream.includes(reader.token),'private_cli_token_exposed');
 const value=JSON.parse(result.stdout);observations.push({scenario:'cli-command',command:args[0],result:value,stderr:result.stderr});await save();return {value,stderr:result.stderr};
}
function warningCheck(value){assert.equal(value.warnings.length,1);assert(value.warnings[0].startsWith('cron-enabled.privacy :'));assert(!value.warnings.some(v=>/planification|schedule/i.test(v)));}
async function discoverFunctions(){if(!service)return;for(const fn of (await api(`/api/services/${service.id}/functions`)).items)if(!functions.some(v=>v.id===fn.id))functions.push(fn);await save();}
await mkdir(out,{recursive:true,mode:0o700});let exists=true;try{await access(report);}catch(error){assert.equal(error.code,'ENOENT');exists=false;}assert(!exists);await save();
try{
 admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:90000});
 session=await api('/api/session');assert(session.authenticated,'real_sso_required');
 work=new URL((await mkdtemp(new URL(prefix+'-',out).pathname))+'/','file:');
 await writeFile(new URL('scheduled-capacity.cjs',work),await readFile(new URL('../qualification/artifacts/scheduled-capacity.cjs',import.meta.url)));
 const manifest={service:'adapter-scheduled-functions',provider:{name:'p2enjoy',runtime:'nodejs24.x',memorySize:128,timeout:10,minScale:0,maxScale:1,p2enjoy:{cpu:.05,idle_seconds:0,concurrency:1,queue_timeout_seconds:5,storage:{concurrency:'shared',data:{enabled:false,quota_mib:2},cache:{enabled:false,quota_mib:2}}}},
  functions:{'cron-enabled':{handler:'scheduled-capacity.handler',privacy:'private',events:[{schedule:{rate:'*/5 * * * *',enabled:true}}]},'cron-disabled':{handler:'scheduled-capacity.handler',events:[{schedule:{rate:'*/5 * * * *',enabled:false}}]}},package:{patterns:['!**','scheduled-capacity.cjs']}};
 const config=new URL('serverless.yml',work).pathname;await writeFile(config,JSON.stringify(manifest));
 const flags=['--config',config,'--accept-provider-differences'];let published,initial;
 await check('Plan réel conserve le cron et privacy, sans avertissement de moteur absent',async()=>{
  const {value,stderr}=await cli(['plan',...flags]);assert.equal(stderr,'');warningCheck(value);assert.equal(value.functions.length,2);
  for(const [i,fn] of value.functions.entries()){assert.equal(fn.name,i?'cron-disabled':'cron-enabled');assert.deepEqual(fn.events.schedules,[{cron:'*/5 * * * *',enabled:!i,timezone:'UTC'}]);}
  const manual=await readFile(new URL('../docs/manual.md',import.meta.url),'utf8');assert(!manual.includes('planification enregistrée, non déclenchée'));assert(manual.includes('Un upload pilote seul ne crée aucun déclenchement.'));assert(manual.includes('La plateforme\ncontrôle ces expressions aux frontières de cinq minutes'));
  observations.push({scenario:'manual-source',sha256:digest(manual)});
 });
 await check('Deploy réel publie les deux fonctions sans promotion implicite',async()=>{
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
  service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:manifest.service}});
  reader=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'publish-and-promote-scheduled-code',rights:['read','create','update']}});await save();
  const {value,stderr}=await cli(['deploy',...flags,'--service',service.id]);published=value;await discoverFunctions();assert(value.completed);assert.equal(value.mode,'complete');warningCheck(value);warningCheck(JSON.parse(stderr));assert.equal(value.results.length,2);assert.equal(functions.length,2);
  for(const fn of functions){const result=value.results.find(v=>v.function_id===fn.id);assert(result);assert.equal(result.state,'published');assert.equal(result.default_code_hash_at_publication,null);assert.equal(fn.active_revision_id,null);fn.code_hash=result.code_hash;assert.match(fn.code_hash,/^[a-f0-9]{64}$/);assert.equal((await api(`/api/functions/${fn.id}/schedules`)).items.length,0);assert.equal((await firings(fn)).length,0);assert.equal((await calls(fn)).length,0);}
  initial=await native();noResources(initial);assert.equal(initial.counts.functions,2);
 });
 await check('Promotion CLI puis un vrai tir du hash publié, déclaration désactivée sans appel',async()=>{
  window=(Math.floor(Date.now()/300000)+1)*300;
  if(window-Date.now()/1000<80){await until(()=>Date.now()/1000>=window+5,'wait_before_promotions',(window+10)*1000);window+=300;}
  for(const fn of functions){const {value}=await cli(['promote','--function',fn.id,'--code-hash',fn.code_hash]);assert(value.completed);assert.equal(value.state,'promoted');assert.equal(value.code_hash,fn.code_hash);const rows=(await api(`/api/functions/${fn.id}/schedules`)).items;assert.equal(rows.length,1);assert.equal(rows[0].enabled,fn.name==='cron-enabled');assert.equal(rows[0].cron,'*/5 * * * *');assert.equal(rows[0].code_hash,fn.code_hash);if(fn.name==='cron-disabled')assert.equal(rows[0].next,null);}
  const enabled=functions.find(v=>v.name==='cron-enabled'),disabled=functions.find(v=>v.name==='cron-disabled');
  const fire=await scheduled(enabled,window),call=(await calls(enabled)).find(v=>v.id===fire.invocation_id);assert(call);witness(call,enabled);assert.equal(call.schedule_slot,window);assert.equal(call.schedule_firing_id,fire.id);assert.equal(call.requested_code_hash,enabled.code_hash);assert.equal(fire.code_hash,enabled.code_hash);assert.equal(fire.nominal_at,window);
  await idle(enabled);const state=await native();assert(state.cursor>=window);assert.equal(state.firings.length,1);assert.equal(state.invocations.length,1);assert.equal(state.invocations[0].id,call.id);assert.equal((await firings(disabled)).length,0);assert.equal((await calls(disabled)).length,0);assert.deepEqual(state.services,initial.services);assert.deepEqual(state.official_sha256,initial.official_sha256);noResources(state);
  observations.push({scenario:'scheduled-cli-publication-executed',firing:fire,invocation:call,publication:published.results.find(v=>v.function_id===enabled.id),native:state});
 });
 await check('Deux purges publiques et code, volumes, conteneurs et canaux absents',async()=>{
  nativeBeforePurge=await native();await api(`/api/tokens/${reader.id}/revoke`,{method:'POST'});for(const fn of functions)await purge(fn);
  await api(`/api/services/${service.id}`,{method:'DELETE'});service.deleted=true;await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});namespace.deleted=true;
  nativeAfterPurge=await native(true);assert(nativeAfterPurge.physical.completed);noResources(nativeAfterPurge);assert.deepEqual(nativeAfterPurge.services,initial.services);assert.deepEqual(nativeAfterPurge.official_sha256,initial.official_sha256);cleanup=true;
 });completed=true;
}catch(error){campaignFailure=diagnostic(error);
}finally{
 if(!cleanup&&admin&&session?.authenticated){
  try{await discoverFunctions();}catch(error){cleanupErrors.push({stage:'function-discovery',error:diagnostic(error)});}
  for(const fn of functions)try{await purge(fn);}catch(error){cleanupErrors.push({function_id:fn.id,stage:'public-purge',error:diagnostic(error)});}
  if(reader)try{await api(`/api/tokens/${reader.id}/revoke`,{method:'POST',status:[200,404]});}catch(error){cleanupErrors.push({stage:'revoke',error:diagnostic(error)});}
  if(!cleanupErrors.length)try{
   if(service&&!service.deleted){await api(`/api/services/${service.id}`,{method:'DELETE'});service.deleted=true;}
   if(namespace&&!namespace.deleted){await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});namespace.deleted=true;}
   if(functions.length===2){nativeAfterPurge=await native(true);noResources(nativeAfterPurge);}cleanup=true;
  }catch(error){cleanupErrors.push({stage:'parents-or-physical',error:diagnostic(error)});}
 }
 await save();if(work)await rm(work,{recursive:true,force:true});await admin?.dispose();
}
assert(completed&&cleanup&&!cleanupErrors.length,'campaign_or_cleanup_not_completed');console.log(JSON.stringify({completed:true,groups:checks.length,functions_purged:2,report:report.pathname}));
