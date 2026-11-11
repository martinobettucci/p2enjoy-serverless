// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation
// Real SSO, API publications, UTC window, inherited-lock native backups and public purges.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,writeFile,rename,mkdtemp,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const run=promisify(execFile),campaign=randomUUID(),base='https://serverless.lelabs.tech';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py',out=new URL('../.local/e2e/',import.meta.url);
const report=new URL('schedule-firing-volume-capture-'+campaign+'.json',out),events=[],checks=[],observations=[],functions=[];
let child,ended=false,exitCode=null,browser,admin,session,namespace,service,work,archive,window,capture;
let completed=false,cleanup=false,failure=null,restoration,saveQueue=Promise.resolve();
function save(){saveQueue=saveQueue.then(async()=>{const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({campaign,completed:completed&&cleanup&&!failure,cleanup,skipped:0,checks,events,observations,function_ids:functions.map(v=>v.id),namespace_id:namespace?.id,window,capture,exit_code:exitCode,failure,restoration},null,2)+'\n',{mode:0o600});await rename(pending,report);});return saveQueue;}
async function until(action,message,seconds=90){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,250));}assert.fail(message);}
async function event(name){return until(()=>{const value=events.find(v=>v.event===name);assert(value||!ended,'deployment_driver_stopped');return value;},'deployment_event_missing',150);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function operation(op,body={}){const offset=events.length;assert(!ended);child.stdin.write(JSON.stringify({op,...body})+'\n');return until(()=>{const value=events.slice(offset).find(v=>v.event==='result'&&v.op===op);assert(value||!ended,'deployment_driver_stopped');return value?.value;},'operator_observation_missing');}
async function capacity(){return operation('capacity');}
async function remote(op){try{const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,op,campaign],{timeout:150000,maxBuffer:8*1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}catch(error){await writeFile(new URL('firing-volume-'+campaign+'-'+op+'.stderr',out),String(error.stderr??''),{mode:0o600});throw error;}}
async function api(url,{method='GET',body,bytes,status=200,headers={}}={}){const response=await admin.fetch(base+url,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(response.status()),`${method} ${url}: ${response.status()}`);return response.json();}
async function publish(fn){const row=await api(`/api/functions/${fn.id}`),candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:fn.config.handler,events:{http:[],schedules:Array.from({length:16},()=>({cron:'*/5 * * * *',enabled:true,timezone:'UTC'}))}}});fn.deployment_id=candidate.id;const result=await api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive});assert.equal(result.state,'published');fn.revision_id=result.revision_id;return result.code_hash;}
async function promote(fn){const row=await api(`/api/functions/${fn.id}`);await api(`/api/functions/${fn.id}/versions/${fn.hash}/promote`,{method:'POST',headers:{'If-Match':String(row.updated_at)}});}
async function purge(fn){await api(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await api(`/api/archives/${fn.id}`),op=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});await until(async()=>{const value=await api(`/api/storage-operations/${op.id}`);assert.notEqual(value.state,'aborted');return value.state==='completed';},'purge_not_completed');assert((await api(`/api/archives/${fn.id}`)).purged_at);}
async function physicalCleanup(){
 const expected={functions:functions.map(v=>v.id),artifacts:functions.flatMap(v=>[v.revision_id,v.deployment_id]),instances:capture.witnesses.invocations.map(v=>v.instance_id)};
 const program='expected='+JSON.stringify(expected)+'\n'+String.raw`
import json,os,re,shlex,socket,subprocess
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
assert all(re.fullmatch('[a-f0-9-]{36}',v) for group in expected.values() for v in group)
settings={}
for line in Path('/etc/spark/env').read_text().splitlines():
 fields=shlex.split(line,comments=True)
 if len(fields)==1 and '=' in fields[0]:
  key,value=fields[0].split('=',1)
  if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_STORAGE_ROOT_HOST'):settings[key]=value
state=Path(settings['SERVERLESS_STATE_HOST_PATH']);storage=Path(settings['SERVERLESS_STORAGE_ROOT_HOST'])
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def absent(paths):return all(not os.path.lexists(path) for path in paths)
result={'artifacts_absent':absent(state/'artifacts'/v for v in expected['artifacts']),'channels_absent':absent(state/'execution'/v for v in expected['instances']),'backings_absent':absent(storage/'backings'/v for v in expected['functions']),'mount_directories_absent':absent(storage/'mounts'/v for v in expected['functions'])}
for identifier in expected['functions']:
 result['containers_absent_'+identifier]=not subprocess.check_output(D+['ps','-aq','--filter','label=tech.p2enjoy.serverless.function='+identifier],text=True).strip()
 result['networks_absent_'+identifier]=not subprocess.check_output(D+['network','ls','-q','--filter','label=tech.p2enjoy.serverless.function='+identifier],text=True).strip()
assert all(result.values());print(json.dumps({'completed':True,'checks':result}))
`;
 return new Promise((resolve,reject)=>{const process=execFile('ssh',[...ssh,'python3 -B -'],{timeout:60000,maxBuffer:1024*1024},(error,stdout)=>{if(error){reject(error);return;}try{resolve(JSON.parse(stdout));}catch(error){reject(error);}});process.stdin.on('error',reject);process.stdin.end(program);});
}

await mkdir(out,{recursive:true,mode:0o700});await save();let credentials;
try{
 assert(!process.stdin.isTTY,'private_pipe_required');const input=createInterface({input:process.stdin});credentials=await new Promise((resolve,reject)=>{input.once('line',line=>{try{assert(line.length<=8192);resolve(JSON.parse(line));}catch{reject(new Error('private_input_invalid'));}finally{input.close();}});input.once('close',()=>reject(new Error('private_input_missing')));});assert(credentials?.username&&credentials?.password);
 const image=(await run('ssh',[...ssh,'runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api'],{timeout:20000})).stdout.trim();assert.match(image,/^sha256:[a-f0-9]{64}$/);
 child=spawn('ssh',[...ssh,'python3','-B',helper,'instance-limit',campaign,image],{stdio:['pipe','pipe','pipe']});createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});child.stderr.resume();child.stdin.on('error',()=>{});child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
 await check('SSO réel et16 publications/promotions avant la même frontière UTC',async()=>{
  const armed=await event('guard-armed'),ready=await event('instance-limit-ready');assert.equal(armed.guard_seconds,900);assert(armed.timer_schedule.includes('OnActiveUSec=15min'));assert.equal(ready.container.image,image);assert.equal(ready.capacity.invocations.length,0);assert.equal(ready.capacity.firings.length,0);
  browser=await chromium.launch({headless:true});const context=await browser.newContext({locale:'fr-FR'}),page=await context.newPage();await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);credentials=null;await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();admin=context.request;session=await api('/api/session');assert(session.authenticated);
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:'instance-limit-'+campaign.slice(0,8)}});service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'scheduled-firing-history-limit'}});
  work=await mkdtemp(new URL('firing-retention-code-',out).pathname);archive=(await publicationArchive(work,'firing-history-volume','scheduled-capacity.handler',['scheduled-capacity.cjs'])).bytes;
  for(let number=1;number<=16;number++){const fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'firing-retention-'+String(number).padStart(2,'0'),config:{handler:'scheduled-capacity.handler',cpu:.05,memory_mib:128,timeout_seconds:60,idle_seconds:0,min_instances:0,max_instances:1,concurrency:1,queue_timeout_seconds:30,storage:{concurrency:'shared',data:{enabled:false,quota_mib:2},cache:{enabled:false,quota_mib:2}}}}});functions.push(fn);await save();fn.hash=await publish(fn);}
  window=(Math.floor(Date.now()/300000)+1)*300;if(window-Date.now()/1000<90){await until(()=>Date.now()/1000>=window+1,'next_preparation_boundary_missing',95);window+=300;}
  for(const fn of functions){await promote(fn);assert(Date.now()/1000<window-30,'promotion_too_late');}
  const state=await capacity();assert.equal(state.instances.length,0);assert.equal(state.containers.length,0);assert.equal(state.firings.length,0);assert.equal(state.invocations.length,0);observations.push({scenario:'promoted-before-window',native:state});console.log(JSON.stringify({event:'waiting-real-window',window}));
 });
 await check('256 tirs authentiques dont deux handlers réussis et254 refus de capacité',async()=>{
  const state=await until(async()=>{const value=await capacity();assert(value.firings.every(v=>v.window_at===window),'unexpected_window');return value.firings.length===256&&value.firings.every(v=>['succeeded','refused_capacity'].includes(v.state))&&value.instances.length===0&&value.containers.length===0?value:false;},'first_window_not_terminal',400);
  assert.equal(state.invocations.length,2);assert(state.invocations.every(v=>v.state==='succeeded'&&v.handler_started&&v.completed_at));assert.equal(state.firings.filter(v=>v.state==='succeeded').length,2);assert.equal(state.firings.filter(v=>v.state==='refused_capacity'&&v.error_code==='schedule_capacity'&&!v.invocation_id).length,254);
  for(const fn of functions){const firings=await api(`/api/functions/${fn.id}/schedule-firings?limit=100`);assert.equal(firings.total,16);assert.equal(firings.items.length,16);assert(firings.items.every(v=>v.window_at===window&&v.code_hash===fn.hash));assert.deepEqual(firings.items.map(v=>v.schedule_index).sort((a,b)=>a-b),Array.from({length:16},(_,n)=>n));}
  observations.push({scenario:'first-window-terminal',native:state});
 });
 await check('Sauvegarde native RO, générations actives et images conservées vérifiées',async()=>{
  capture=await operation('capture-firing-history',{function_ids:functions.map(v=>v.id),window});assert(capture.completed&&capture.source_read_only&&capture.dates_unchanged&&capture.root_private_directory&&capture.sqlite_read_only);assert.equal(capture.witnesses.cursor,window);assert.equal(capture.witnesses.namespace.id,namespace.id);assert.equal(capture.initial_firings,256);assert.equal(capture.required_missed_windows,39);assert.equal(capture.eligible_after,window+11700);assert.equal(capture.count_retention_qualified,false);assert.equal(capture.seven_day_retention_qualified,false);
  for(const fn of functions){const generation=capture.witnesses.generations.find(v=>v.function_id===fn.id);assert(generation&&!generation.retired_at&&generation.code_hash===fn.hash);assert.equal(generation.revision_id,fn.revision_id);}
  console.log(JSON.stringify({event:'private-capture-preserved',capture_id:capture.capture_id,eligible_after:capture.eligible_after}));
 });
 await check('16 purges publiques puis restitution des originaux et gardes jointes',async()=>{
  for(const fn of functions)await purge(fn);await api(`/api/services/${service.id}`,{method:'DELETE'});await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});const state=await capacity();assert.equal(state.instances.length,0);assert.equal(state.containers.length,0);assert(state.functions.every(v=>v.deleted_at));const physical=await physicalCleanup();assert(physical.completed);observations.push({scenario:'purged-before-restoration',physical});
  child.stdin.end(JSON.stringify({op:'restore'})+'\n');restoration=await event('restored');assert(restoration.databases_identical&&restoration.artifacts_identical&&restoration.configuration_unchanged&&restoration.reference_unchanged&&restoration.temporary_directories_removed);assert.equal(restoration.independent,false);await until(()=>ended,'deployment_not_joined',30);assert.equal(exitCode,0);const status=await remote('status');assert(status.restored&&!status.driver_alive&&['inactive','unknown'].includes(status.timer_state)&&['inactive','unknown'].includes(status.service_state));observations.push({scenario:'restore-joined',restored:true,driver_alive:status.driver_alive,timer_state:status.timer_state,service_state:status.service_state});cleanup=true;
 });completed=true;
}catch(error){failure={type:error.name,code:error.code,signal:error.signal,source_line:String(error.stack??'').match(/schedule-firing-volume-capture\.mjs:(\d+)/)?.[1],message_sha256:createHash('sha256').update(String(error.message)).digest('hex'),...(typeof error.actual==='number'&&typeof error.expected==='number'?{actual:error.actual,expected:error.expected}:{})};}
finally{
 credentials=null;if(!cleanup&&child){child.stdin.end();try{restoration=await remote('restore');cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}catch(error){failure={...failure,restoration_error:error.name};}await until(()=>ended,'failed_deployment_not_joined',60).catch(()=>{cleanup=false;});}
 await browser?.close();if(work)await rm(work,{recursive:true,force:true});await save();
}
assert(completed&&cleanup&&!failure,`schedule_firing_volume_capture_failed:${report.pathname}`);console.log(JSON.stringify({completed:true,groups:checks.length,capture_id:capture.capture_id,eligible_after:capture.eligible_after,report:report.pathname}));
