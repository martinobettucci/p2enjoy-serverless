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
const report=new URL('invocation-source-retention-volume-'+campaign+'.json',out),events=[],checks=[],observations=[],functions=[],responses=[],producers=[];
let caller,stopProducing=false,saveQueue=Promise.resolve(),window,lastCall;
let child,ended=false,exitCode=null,browser,context,admin,session,namespace,service,reader,work,archive,completed=false,cleanup=false,failure=null,restoration;
function save(){saveQueue=saveQueue.then(async()=>{const p=new URL(report.pathname+'.pending','file:');await writeFile(p,JSON.stringify({campaign,completed:completed&&cleanup&&!failure,cleanup,skipped:0,checks,events,observations,responses,function_ids:functions.map(v=>v.id),namespace_id:namespace?.id,exit_code:exitCode,failure,restoration},null,2)+'\n',{mode:0o600});await rename(p,report);});return saveQueue;}
async function until(action,message,seconds=90){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,250));}assert.fail(message);}
async function event(name){return until(()=>{const v=events.find(v=>v.event===name);assert(v||!ended,'deployment_driver_stopped');return v;},'deployment_event_missing',150);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function operation(op,extra={}){const offset=events.length;assert(!ended);child.stdin.write(JSON.stringify({op,...extra})+'\n');const found=await until(()=>{const v=events.slice(offset).find(v=>v.event==='result'&&v.op===op);assert(v||!ended,'deployment_driver_stopped');return v;},'operator_observation_missing');const value=found.value;if(op==='capacity')found.value={installation_id:value.installation_id,instances:value.instances.length,containers:value.containers.length,invocations:value.invocations.length};return value;}
async function capacity(){return operation('capacity');}
async function remote(op,...args){try{const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,op,campaign,...args],{timeout:60000,maxBuffer:12*1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}catch(error){error.operator=op;await writeFile(new URL('source-retention-operator-'+campaign+'-'+op+'.stderr',out),String(error.stderr??''),{mode:0o600});throw error;}}

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
async function physicalCleanup(){
 const input={functions:functions.map(v=>v.id),artifacts:functions.flatMap(v=>[v.revision_id,v.deployment_id]),instances:observations.find(v=>v.scenario==='initial-warm-instances').native.instances.map(v=>v.id)};
 const program='expected='+JSON.stringify(input)+'\n'+String.raw`
import json,os,re,shlex,socket,subprocess
from pathlib import Path
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
assert all(result.values());print(json.dumps({'completed':True,'checks':result}))
`;
 const result=await new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:60000,maxBuffer:1024*1024},(error,stdout)=>error?reject(error):resolve(JSON.parse(stdout)));p.stdin.on('error',reject);p.stdin.end(program);});assert(result.completed);return result;
}
await mkdir(out,{recursive:true,mode:0o700});await save();let credentials;
try{
 assert(!process.stdin.isTTY,'private_pipe_required');const input=createInterface({input:process.stdin});credentials=await new Promise((resolve,reject)=>{input.once('line',line=>{try{assert(line.length<=8192);resolve(JSON.parse(line));}catch{reject(new Error('private_input_invalid'));}finally{input.close();}});input.once('close',()=>reject(new Error('private_input_missing')));});assert(credentials?.username&&credentials?.password);
 const image=(await run('ssh',[...ssh,'runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api'],{timeout:20000})).stdout.trim();assert.match(image,/^sha256:[a-f0-9]{64}$/);
 child=spawn('ssh',[...ssh,'python3','-B',helper,'instance-limit',campaign,image,'--guard-seconds=2700'],{stdio:['pipe','pipe','pipe']});createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});child.stderr.resume();child.stdin.on('error',()=>{});child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
 let initial,before,after;
 await check('SSO réel et deux instances préchauffées dans une installation isolée de même image',async()=>{
  const armed=await event('guard-armed'),ready=await event('instance-limit-ready');assert.equal(armed.guard_seconds,2700);assert(armed.timer_schedule.includes('OnActiveUSec=45min'));assert.equal(ready.container.image,image);assert.equal(ready.capacity.invocations.length,0);
  browser=await chromium.launch({headless:true});context=await browser.newContext({locale:'fr-FR'});const page=await context.newPage();await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);credentials=null;await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();admin=context.request;session=await api('/api/session');assert(session.authenticated);caller=await request.newContext({timeout:30000});
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:'instance-limit-'+campaign.slice(0,8)}});service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'protected-invocation-history'}});reader=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-history-observations',rights:['read']}});
  window=Math.floor(Date.now()/300000)*300+2100;
  work=await mkdtemp(new URL('retention-observation-code-',out).pathname);archive=(await publicationArchive(work,'retention-volume','protected-retention-observation.handler',['protected-retention-observation.cjs'])).bytes;
  for(const name of ['first-retention-stream','second-retention-stream']){const fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'protected-retention-observation.handler',cpu:.5,memory_mib:128,timeout_seconds:10,idle_seconds:0,min_instances:1,max_instances:1,concurrency:1,queue_timeout_seconds:30,storage:{concurrency:'shared',data:{enabled:false,quota_mib:2},cache:{enabled:false,quota_mib:2}}}}});functions.push(fn);if(functions.length===2){const date=new Date(window*1000);fn.schedules=[{cron:`${date.getUTCMinutes()} ${date.getUTCHours()} * * *`,enabled:true,timezone:'UTC'}];}await save();fn.hash=await publish(fn);await promote(fn,fn.hash);}
  initial=await until(async()=>{const s=await capacity();return s.instances.length===2&&s.instances.every(v=>v.state==='ready')?s:false;},'two_warm_instances_missing');terminal(initial,0);assert.equal(initial.instances.reduce((n,v)=>n+v.cpu_nanos,0),1000000000);assert.equal(initial.instances.reduce((n,v)=>n+v.memory_mib,0),256);assert.equal(initial.containers.length,2);for(const c of initial.containers)assert(c.running&&c.cpu_nanos===500000000&&c.memory_bytes===128*1024**2);observations.push({scenario:'initial-warm-instances',native:initial});
  await streams(0,5000);assert.equal(responses.length,10000);before=await capacity();terminal(before,10000);assert.deepEqual(before.invocations.map(v=>v.id).sort(),responses.map(v=>v.id).sort());for(const fn of functions)assert.equal(responses.filter(v=>v.function_id===fn.id).length,5000);assert(Date.now()/1000<window-60,'production_margin_before_cron_exhausted');observations.push({scenario:'ten-thousand-ordinary-invocations',window,native:before});await save();
 });
 await check('Source exclue avant clôture puis recomptée : trois ensembles exacts10002→10001→10000',async()=>{
  let heartbeat=0;
  await until(async()=>{assert(!ended,'guard_ended_before_cron');if(Date.now()-heartbeat>10000){assert((await api('/api/session')).authenticated);heartbeat=Date.now();}return Date.now()/1000>=window-1;},'real_cron_boundary_not_reached',2400);
  assert(Date.now()/1000<window-.2,'last_http_start_frontier_missed');
  lastCall=(async()=>{let response;try{response=await caller.post(base+`/invoke/${functions[0].id}`,{headers:{'X-Serverless-Token':reader.token},data:{sequence:5000,hold_until:(window+3)*1000},timeout:30000,maxRetries:0,maxRedirects:0});assert.equal(response.status(),200);const body=await response.json();assert.equal(body.marker,'protected-retention-observation');assert.equal(body.sequence,5000);assert.equal(body.trigger,'http');assert.equal(body.request_id,response.headers()['x-serverless-request-id']);assert.equal(response.headers()['x-serverless-code-hash'],functions[0].hash);return {id:body.request_id,function_id:functions[0].id,sequence:5000,code_hash:functions[0].hash};}finally{await response?.dispose();}})().then(value=>({value}),error=>({error}));
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
 });completed=true;
}catch(error){failure={type:error.name,operator:error.operator,code:error.code,signal:error.signal,source_line:String(error.stack??'').match(/invocation-source-retention-volume\.mjs:(\d+)/)?.[1],message_sha256:createHash('sha256').update(String(error.message)).digest('hex'),...(typeof error.actual==='number'&&typeof error.expected==='number'?{actual:error.actual,expected:error.expected}:{})};}
finally{
 credentials=null;stopProducing=true;await Promise.allSettled(producers);if(lastCall)await lastCall;
 if(!cleanup&&child){child.stdin.end();try{const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,'restore',campaign],{timeout:150000,maxBuffer:12*1024*1024});restoration=JSON.parse(stdout.trim().split('\n').at(-1));cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}catch(error){failure={...failure,restoration_error:error.name};}await until(()=>ended,'failed_deployment_not_joined',60).catch(()=>{cleanup=false;});}
 await caller?.dispose();await browser?.close();if(work)await rm(work,{recursive:true,force:true});await save();
}
assert(completed&&cleanup&&!failure,`invocation_retention_volume_failed:${report.pathname}`);console.log(JSON.stringify({completed:true,groups:checks.length,real_http_handlers:responses.length,report:report.pathname}));
