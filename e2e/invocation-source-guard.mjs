// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#trois-preuves-de-garde-avant-les-parcours-fonctionnels
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#trois-preuves-de-garde-avant-les-parcours-fonctionnels
// Real file permissions, Docker open, remote helper signals and independent systemd restoration.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const helper='/srv/p2enjoy-serverless/e2e/invocation-source-permissions.py';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const checks=[],observations=[],tasks=[],cleanupErrors=[],operatorErrors=[];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let completed=false,failure,client;
await mkdir(out,{recursive:true,mode:0o700});const report=path.join(out,'invocation-source-guard.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const image=JSON.parse(await readFile(path.join(root,'docs/evidence/invocation-alias-entry-dev-2026-11-09.json'),'utf8')).control_image;
async function until(action,code,seconds=50){
  const deadline=Date.now()+seconds*1000;
  while(true){const value=await action();if(value)return value;assert(Date.now()<deadline,code);await sleep(100);}
}
async function remote(mode,unit){
  const value=await new Promise(resolve=>{
    const child=execFile('ssh',[...ssh,'python3','-B',helper,mode,'--folder','/run/'+unit],{timeout:180000,maxBuffer:2*1024*1024},(error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr}));child.stdin.end();
  });
  if(value.code!==0)operatorErrors.push({mode,unit,...value});
  assert.equal(value.code,0,'permission_operator_failed');return JSON.parse(value.stdout);
}
async function health(){
  for(const origin of ['https://serverless.lelabs.tech','https://functions.lelabs.tech']){
    const response=await client.get(origin+'/healthz');assert.equal(response.status(),200);assert.equal((await response.json()).component,'control');
  }
}
function start(action){
  const events=[];let ended=false,exitCode,stderr='',invalid=false;
  const child=spawn('ssh',[...ssh,'python3','-B',helper,'supervise','--image',image,'--delay',action==='release'?'60':'12'],{stdio:['pipe','pipe','pipe']});
  createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{invalid=true;}});
  child.stderr.on('data',value=>{stderr+=value.toString();});child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{
    child.once('close',code=>{ended=true;exitCode=code;resolve(code);});
    child.once('error',()=>{ended=true;exitCode=-1;resolve(-1);});
  });
  const task={events,restored:false,receipt:null,
    async wait(name){return until(()=>{
      assert(!invalid,'permission_protocol_invalid');const value=events.find(v=>v.event===name);
      assert(value||!ended,'permission_helper_ended');return value;
    },'permission_event_missing:'+name);},
    send(value){child.stdin.write(value+'\n');},
    async finish(){
      const code=await done;
      assert.equal(code,0,'permission_supervisor_exit');
      const armed=events.find(v=>v.event==='guard-armed');assert(armed);
      const started=events.find(v=>v.event==='helper-started'),exited=events.find(v=>v.event==='helper-exited');
      assert.equal(started?.pid,armed.identity.helper_pid);assert.equal(exited?.pid,armed.identity.helper_pid);
      assert.equal(exited.returncode,action==='release'?0:-9);assert.equal(exited.signal,action==='release'?null:'SIGKILL');
      if(action!=='release')assert(events.some(v=>v.event==='helper-signal'&&v.signal===(action==='kill-helper'?'SIGKILL':'SIGSTOP')));
      if(action==='stop-helper')assert(events.some(v=>v.event==='helper-stopped'&&v.pid===armed.identity.helper_pid&&v.signal==='SIGSTOP'));
      const restored=await until(async()=>{
        const value=await remote('evidence',armed.unit);
        return value.completed&&value.event==='restored'&&['inactive','unknown'].includes(value.service_state)?value:false;
      },'permission_restore_missing');
      assert(restored.source_restored);assert.equal(restored.independent,action!=='release');
      if(action==='stop-helper')assert(restored.helper_killed&&restored.helper_absent);
      if(action==='kill-helper')assert(restored.helper_absent);
      const value=await remote('disarm',armed.unit);
      assert(['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state));
      assert.equal(value.source.after.mode,armed.identity.source.mode);assert.equal(value.source.after.sha256,armed.identity.source.sha256);
      assert.equal(value.current_installation.open.errno,0);assert(value.current_installation.local_health);
      task.restored=true;task.receipt={action,events,exit_code:code,restoration:value};return task.receipt;
    },
    async recover(){
      child.stdin.end();const armed=events.find(v=>v.event==='guard-armed');
      if(!armed){await done;assert.fail('permission_guard_identity_unknown');}
      const value=await remote('recover',armed.unit);await done;
      assert(value.completed&&value.source_restored&&value.current_installation.local_health);
      assert(['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state));task.restored=true;
    },
    diagnostic(){return {action,events,exit_code:exitCode,stderr,restored:task.restored};}
  };
  tasks.push(task);return task;
}
try{
  client=await request.newContext({timeout:30000,ignoreHTTPSErrors:false});
  for(const action of ['release','kill-helper','stop-helper']){
    const label={'release':'Vrai EACCES puis restitution explicite du fichier officiel','kill-helper':'SIGKILL du helper : restitution indépendante et nouvel open réussi','stop-helper':'SIGSTOP du helper : garde le tue et restitue le mode sans coopération'}[action];
    try{
      await health();const task=start(action),active=await task.wait('fault-active');
      assert.equal(active.control_open.errno,13);assert.equal(active.source.mode,0);
      await health();task.send(action);const receipt=await task.finish();await health();
      observations.push(receipt);checks.push({name:label,status:'passed'});console.log('PASS',label);
    }catch(error){checks.push({name:label,status:'failed',error:error.name});throw error;}
  }
  completed=true;
}catch(error){failure={name:error.name,message:error.message};throw error;}
finally{
  for(const task of tasks)if(!task.restored){try{await task.recover();}catch(error){cleanupErrors.push({resource:'permission-guard',error:error.name});}}
  await client?.dispose();
  await writeFile(report,JSON.stringify({completed:completed&&!cleanupErrors.length,cleanup:!cleanupErrors.length,checks,skipped:0,observations,
    tasks:tasks.map(v=>v.receipt??v.diagnostic()),failure,cleanup_errors:cleanupErrors,operator_errors:operatorErrors,route_changes:0,workloads_created:0},null,2)+'\n');
  assert.equal(cleanupErrors.length,0,'source_permission_cleanup_required');
}
