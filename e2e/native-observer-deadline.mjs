// @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#mesure-de-lattente-native-sans-événement
// @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#mesure-de-lattente-native-sans-événement
// Real deployment and kernel signals; no application server or dependency substitute.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,writeFile,rename} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';

const run=promisify(execFile),campaign=randomUUID(),mode=process.argv[2];
assert.equal(process.argv.length,3);
assert(['reproduce','bounded'].includes(mode),'explicit_scenario_required');
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py';
const output=new URL('../.local/e2e/',import.meta.url);
const report=new URL(`native-observer-deadline-${mode}-${campaign}.json`,output);
const events=[],checks=[];let child,ended=false,exitCode=null,completed=false,cleanup=false,failure=null,restoration,measurement,driverStderr='';
async function remote(...args){try{const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,...args],{timeout:60000,maxBuffer:2*1024*1024});return JSON.parse(stdout);}catch(error){
 assert(['signal-driver','status','restore'].includes(args[0]));
 error.operator=args[0];error.stderr_sha256=createHash('sha256').update(String(error.stderr??'')).digest('hex');
 await writeFile(new URL(`native-observer-deadline-${mode}-${campaign}-${args[0]}.stderr`,output),String(error.stderr??''),{mode:0o600});throw error;
}}
async function save(){const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({campaign,mode,completed,cleanup,skipped:0,checks,events,exit_code:exitCode,failure,restoration,measurement,driver_stderr_sha256:createHash('sha256').update(driverStderr).digest('hex')},null,2)+'\n',{mode:0o600});await rename(pending,report);}
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
 child.stderr.on('data',value=>{driverStderr=(driverStderr+value.toString()).slice(-1000000);});child.stdin.on('error',()=>{});
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
 await check('Attente réelle sans événement, dégel indépendant et détachement mesurés',async()=>{
  child.stdin.write(JSON.stringify({op:'measure-native-deadline'})+'\n');
  measurement=(await until(()=>events.find(v=>v.event==='result'&&v.op==='measure-native-deadline'),'native_wait_measurement_missing',60)).value;
  assert(measurement.completed&&!measurement.cleanup_errors.length&&measurement.reader_closed&&measurement.memory_closed);
  assert.equal(measurement.pending_status.pid,0);assert(measurement.pause_confirmed.paused);
  assert.equal(measurement.after_attach.tracer_pid,measurement.operator.pid);
  assert.equal(measurement.after_detach.tracer_pid,0);
  assert.equal(measurement.after_detach.birth,measurement.control.birth);
  assert(measurement.thaw.completed&&measurement.thaw.was_paused&&!measurement.thaw.paused_after);
  assert.notEqual(measurement.thaw.actor.pid,measurement.operator.pid);assert.notEqual(measurement.thaw.actor.cgroup,measurement.operator.cgroup);
  assert(measurement.thaw_confirmed_monotonic<=measurement.detach_started_monotonic);
  assert.equal(measurement.thaw_terminal.Result,'success');assert.equal(measurement.thaw_terminal.ExecMainCode,'1');assert.equal(measurement.thaw_terminal.ExecMainStatus,'0');
  assert(Object.values(measurement.thaw_joined).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));
  const wait=measurement.wait;assert(!wait.returned);assert.equal(wait.exception.type,'AssertionError');assert.equal(wait.exception.message,'native_stop_not_observed');
  assert(wait.global_alarm_remaining>30&&measurement.thaw_deadline_monotonic-wait.entered_monotonic>26);
  if(mode==='reproduce'){
   assert(wait.duration>26&&wait.duration<33);
   assert(wait.finished_monotonic>=measurement.thaw_deadline_monotonic);
  }else assert(wait.duration>=25&&wait.duration<26);
  assert.equal((await http.get('/healthz')).status(),200);
 });
 await check('Restitution réelle après mesure, données et configuration originales conservées',async()=>{
  child.stdin.end(JSON.stringify({op:'restore'})+'\n');
  restoration=await until(async()=>{const value=await remote('status',campaign);return value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state)?value:false;},'originals_not_restored',220);
  const value=restoration.restoration;
  assert(value.directories_identical&&value.databases_identical&&value.artifacts_identical&&value.configuration_unchanged);
  assert(value.agent_healthy&&value.control_healthy&&value.reference_unchanged&&value.temporary_directories_removed);
  assert.equal(value.independent,false);
  assert.equal(restoration.driver_alive,false);assert(['inactive','unknown'].includes(restoration.timer_state));assert(['inactive','unknown'].includes(restoration.service_state));
  await until(()=>ended,'ssh_driver_not_joined',20);
  assert.equal(exitCode,0);
  assert.equal((await http.get('/healthz')).status(),200);cleanup=true;
 });
 completed=true;
}catch(error){failure={type:error.name,operator:error.operator,code:error.code,signal:error.signal,stderr_sha256:error.stderr_sha256,...(error.name==='AssertionError'?{message:error.message}:{})};}
finally{
 if(!cleanup&&child){
  child.stdin.end();
  try{restoration=await remote('restore',campaign);cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}
  catch(error){failure={...failure,restoration_error:error.name};}
  await until(()=>ended,'failed_driver_not_joined',60).catch(()=>{cleanup=false;});
 }
 await http.dispose();await writeFile(new URL(report.pathname+'.stderr','file:'),driverStderr,{mode:0o600});await save();
}
assert(completed&&cleanup&&!failure,`native_observer_deadline_failed:${report.pathname}`);
console.log(JSON.stringify({completed:true,groups:checks.length,report:report.pathname}));
