// @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#installation-temporaire-réelle
// @verifies docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#scénarios-requis
// Real deployment and kernel signals; no application server or dependency substitute.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {mkdir,writeFile,rename} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';

const run=promisify(execFile),campaign=randomUUID(),mode=process.argv[2];
assert.equal(process.argv.length,3);
assert(['release','eof','sigterm','sigkill','deadline'].includes(mode),'explicit_scenario_required');
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py';
const output=new URL('../.local/e2e/',import.meta.url);
const report=new URL(`instance-limit-environment-${mode}-${campaign}.json`,output);
const events=[],checks=[];let child,ended=false,exitCode=null,completed=false,cleanup=false,failure=null,restoration;
async function remote(...args){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,...args],{timeout:60000,maxBuffer:2*1024*1024});return JSON.parse(stdout);}
async function save(){const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({campaign,mode,completed,cleanup,skipped:0,checks,events,exit_code:exitCode,failure,restoration},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function until(action,message,seconds=180){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(r=>setTimeout(r,500));}assert.fail(message);}
async function event(name){return until(()=>{const value=events.find(v=>v.event===name);assert(value||!ended,`driver_stopped_before_${name}`);return value;},`missing_${name}`);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
await mkdir(output,{recursive:true,mode:0o700});await save();
const http=await request.newContext({baseURL:'https://serverless.lelabs.tech',timeout:15000});
try{
 const command=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api'];
 const image=(await run('ssh',[...ssh,...command],{timeout:20000})).stdout.trim();assert.match(image,/^sha256:[a-f0-9]{64}$/);
 child=spawn('ssh',[...ssh,'python3','-B',helper,'instance-limit',campaign,image,'--guard-seconds=120'],{stdio:['pipe','pipe','pipe']});
 createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});
 // Remote diagnostic text never enters a public report or terminal.
 child.stderr.resume();child.stdin.on('error',()=>{});
 child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
 await check('Même image réellement déployée, plafond2, données neuves et HTTPS disponible',async()=>{
  const armed=await event('guard-armed'),ready=await event('instance-limit-ready');
  assert.equal(armed.current_image,image);assert.equal(ready.container.image,image);assert.notEqual(ready.container.id,armed.original_id);
  assert(ready.capacity.original_control_stopped&&ready.capacity.official_configuration_unchanged);
  assert.deepEqual(ready.capacity.budgets,{SERVERLESS_FUNCTION_INSTANCE_LIMIT:'2',SERVERLESS_FUNCTION_CPU_BUDGET:'1',SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB:'8192'});
  for(const name of ['functions','instances','invocations','firings','containers'])assert.deepEqual(ready.capacity[name],[]);
  const response=await http.get('/api/session');assert.equal(response.status(),200);assert.equal((await response.json()).authenticated,false);
  assert.equal((await http.get('/healthz')).status(),200);
 });
 await check('Restitution réelle après '+mode+', sans réécriture des variables officielles',async()=>{
  if(mode==='release')child.stdin.end(JSON.stringify({op:'restore'})+'\n');
  else if(mode==='eof')child.stdin.end();
  else if(mode==='sigterm'||mode==='sigkill'){
   const signal=await remote('signal-driver',campaign,mode==='sigterm'?'SIGTERM':'SIGKILL');
   assert(signal.driver_dead);assert.equal(signal.signal,mode==='sigterm'?15:9);events.push(signal);
  }
  restoration=await until(async()=>{const value=await remote('status',campaign);return value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state)?value:false;},'originals_not_restored',220);
  const value=restoration.restoration;
  assert(value.directories_identical&&value.databases_identical&&value.artifacts_identical&&value.configuration_unchanged);
  assert(value.agent_healthy&&value.control_healthy&&value.reference_unchanged&&value.temporary_directories_removed);
  assert.equal(value.independent,['sigterm','sigkill','deadline'].includes(mode));
  assert.equal(restoration.driver_alive,false);assert(['inactive','unknown'].includes(restoration.timer_state));assert(['inactive','unknown'].includes(restoration.service_state));
  await until(()=>ended,'ssh_driver_not_joined',20);
  if(mode==='release'||mode==='eof')assert.equal(exitCode,0);else assert.notEqual(exitCode,0);
  assert.equal((await http.get('/healthz')).status(),200);cleanup=true;
 });
 completed=true;
}catch(error){failure={type:error.name,...(error.name==='AssertionError'?{message:error.message}:{})};}
finally{
 if(!cleanup&&child){
  child.stdin.end();
  try{restoration=await remote('restore',campaign);cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}
  catch(error){failure={...failure,restoration_error:error.name};}
  await until(()=>ended,'failed_driver_not_joined',60).catch(()=>{cleanup=false;});
 }
 await http.dispose();await save();
}
assert(completed&&cleanup&&!failure,`instance_limit_environment_failed:${report.pathname}`);
console.log(JSON.stringify({completed:true,groups:checks.length,report:report.pathname}));
