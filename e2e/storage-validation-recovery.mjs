// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
// @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const base='https://serverless.lelabs.tech',run=promisify(execFile),output=new URL('../.local/e2e/',import.meta.url);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-validation-faults.py',report=new URL('storage-validation-recovery.json',output);
const checks=[],functions=[],gates=[],uploads=[],evidence=[],cleanupErrors=[],prefix='storage-validation-'+randomUUID().slice(0,8);
const secret='validation-secret-'+randomUUID();
let admin,caller,session,namespace,service,readToken,work,completed=false,cleanup=false;
async function save(){const pending=new URL('storage-validation-recovery.pending',output);await writeFile(pending,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,evidence,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,function_ids:functions.map(fn=>fn.id)},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name,message:error.message});throw error;}finally{await save();}}
async function call(path,{method='GET',body,bytes,headers={},token,status=200}={}){
  const response=await (token?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()} au lieu de ${status}`);
  const text=await response.text();assert(!text.includes(secret),'Secret exposé');
  if(method==='POST'&&path.endsWith('/purge'))assert.equal(response.headers().location,'/api/storage-operations/'+body.operation_id);
  return JSON.parse(text);
}
async function until(action,message,timeout=90000){const end=Date.now()+timeout;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,150));}assert.fail(message);}
async function healthy(){await until(async()=>{try{return (await caller.get('/healthz',{timeout:2000})).status()===200;}catch{return false;}},'Contrôle non rétabli');}
async function remote(mode,fn,extra=[]){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...extra],{timeout:120000,maxBuffer:1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
async function invoke(fn,body){const value=await call(`/invoke/${fn.id}`,{method:body?'POST':'GET',body,token:readToken});await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'Instance non éteinte');return value;}
async function create(name){const fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'storage-console.handler',cpu:.2,memory_mib:256,idle_seconds:0,timeout_seconds:10,storage:{data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},configuration:{environment:{VALIDATION_LABEL:'preserved'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}}});functions.push(fn);return fn;}
async function prepare(fn,bundle){const row=await call(`/api/functions/${fn.id}`);return call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:bundle.handler}});}
async function publish(fn,bundle){const row=await prepare(fn,bundle);await call(`/api/deployments/${row.id}/artifact`,{method:'PUT',bytes:bundle.bytes});return row;}
function upload(candidate,bundle){const task={settled:false};task.done=call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:bundle.bytes,status:422}).then(value=>({value}),error=>({error})).then(value=>{task.settled=true;return value;});uploads.push(task);return task;}
async function finish(task){const result=await task.done;if(result.error)throw result.error;return result.value;}
async function archive(fn){await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Archivage non terminé');}
async function purge(fn,status=[200,202]){const row=await call(`/api/archives/${fn.id}`),id=randomUUID();const answer=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status,headers:{'If-Match':String(row.updated_at)},body:{operation_id:id,confirm_name:row.name}});return {id,answer};}
async function terminal(id){return until(async()=>{const row=await call(`/api/storage-operations/${id}`);return row.state==='completed'?row:false;},'Purge non terminée');}
async function gate(mode,fn,candidate,original){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,candidate.id],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,code=null;const lines=createInterface({input:child.stdout});
  lines.on('line',line=>events.push(JSON.parse(line)));child.stderr.resume();child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{child.on('close',value=>{ended=true;code=value;resolve(value);});child.on('error',()=>{ended=true;code=-1;resolve(-1);});});
  const handle={events,restored:false,killed:false,async wait(name){return until(()=>{const row=events.find(item=>item.event===name);assert(row||!ended,`Garde interrompue : ${code}`);return row;},'Événement absent : '+name,35000);},
    async kill(){handle.killed=true;child.stdin.end('kill-helper\n');await until(()=>ended,'Helper non terminé',10000);assert.notEqual(await done,0);},
    async release(){
      if(handle.restored)return;
      if(!ended&&!child.stdin.writableEnded)child.stdin.end('resume\n');
      await until(()=>ended,'Garde non terminée',95000);await done;
      const active=events.find(row=>row.event==='fault-active'),armed=events.find(row=>row.event==='guard-armed');
      if(armed){
        let restoration=events.find(row=>row.event==='socket-restored');
        if(!restoration){assert(armed,'Garde indépendante absente');restoration=await until(async()=>{const found=await remote('guard-evidence',fn,[armed.unit]);return found.events.find(row=>row.control_connected);},'Restauration indépendante absente',95000);}
        evidence.push({scenario:'socket-restored',...restoration});
      }
      // Confirm the actual socket even if SSH lost every operator event.
      const observed=await until(async()=>{try{const value=await remote('socket-status',fn);return value.mode===original.mode&&value.connection.connected?value:false;}catch{return false;}},'Socket non rétabli',100000);
      assert.deepEqual(observed.identity,original.identity);assert.equal(observed.uid,original.uid);assert.equal(observed.gid,original.gid);
      handle.restored=true;assert(handle.killed||code===0,'Échec du helper de perturbation');
    }};
  gates.push(handle);await handle.wait('fault-active');return handle;
}

await mkdir(output,{recursive:true,mode:0o700});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',output),'utf8')),timeout:180000});caller=await request.newContext({baseURL:base,timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'Session SSO réelle requise');await healthy();
  namespace=await call('/api/namespaces',{method:'POST',body:{name:prefix},status:201});service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'validation-cleanup'},status:201});
  readToken=(await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'observe-preserved-functions',rights:['read']}})).token;
  work=await mkdtemp(new URL('storage-validation-',output).pathname);
  const normal=await publicationArchive(work,'preserved','storage-console.handler');
  const slow=await publicationArchive(work,'live-validation','storage-validation-delay.handler',['storage-validation-delay.mjs']);
  const fn=await create('archive-after-validation'),peer=await create('preserved-neighbor');
  const initial=await publish(fn,normal),neighbor=await publish(peer,normal);
  await invoke(fn,{data:'permanent',cache:'cache'});await invoke(peer,{data:'neighbor-data',cache:'neighbor-cache'});
  await check('Socket Docker : SIGKILL du helper puis restauration indépendante et nettoyage du vrai validateur',async()=>{
    const baseline=(await remote('preflight',fn)).socket,candidate=await prepare(fn,slow),pending=upload(candidate,slow);
    const held=await gate('watchdog-docker',fn,candidate,baseline);const active=await held.wait('fault-active');
    assert.equal(pending.settled,false);assert.equal(active.denied.errno,13);await held.kill();await held.release();
    const unit=(await held.wait('guard-armed')).unit,guard=await remote('guard-evidence',fn,[unit]);
    assert.equal(guard.events.length,1);assert.equal(guard.events[0].independent,true);assert.equal(guard.events[0].previous_mode,0);
    assert.equal(guard.events[0].candidate_id,candidate.id);assert.equal(guard.events[0].function_id,fn.id);assert.deepEqual(guard.events[0].identity,baseline.identity);
    await finish(pending);const result=await remote('inspect',fn,[candidate.id]);
    assert.equal(result.candidate.state,'failed');assert.equal(result.candidate.validation.error,'validation_timeout');assert.equal(result.candidate.validation.container_removed,true);
    assert.equal(result.candidate.reserved_bytes,0);assert.equal(result.validators.length,0);assert.equal(result.channels.length,0);assert.equal(result.code_present,false);assert.equal(result.archive_present,false);
    assert.equal((await call(`/api/functions/${fn.id}`)).active_revision_id,initial.id);assert.equal((await invoke(fn)).data,'permanent');
    evidence.push({scenario:'independent-socket-restoration',candidate_id:candidate.id,result});await healthy();
  });
  await check('Purge pendant import vivant : attente du nettoyage Docker et effacement du diagnostic tardif',async()=>{
    const baseline=(await remote('preflight',fn)).socket,candidate=await prepare(fn,slow),pending=upload(candidate,slow);
    const held=await gate('deny-docker',fn,candidate,baseline);let action,during,afterUpload;
    try{
      const active=await held.wait('fault-active');assert.equal(pending.settled,false);
      await archive(fn);assert.equal(pending.settled,false,'Upload terminé avant suppression');
      action=await purge(fn,202);assert.equal(action.answer.state,'pending');assert.equal(pending.settled,false,'Upload terminé avant décision de purge');
      during=await remote('inspect',fn,[candidate.id]);assert.equal(pending.settled,false,'Diagnostic arrivé avant le relevé de décision');
      assert.equal(during.candidate.validation,null);assert.equal(during.candidate.configuration_empty,1);assert.equal(during.function.purged_at,null);
      assert(during.guards.some(row=>row.id===action.id&&row.decision==='commit'));assert(during.validators[0].running&&during.validators[0].marker);
      assert(during.candidate.reserved_bytes>0&&during.revisions.some(row=>row.id===initial.id&&row.stored_bytes>0));
      assert.equal(during.archive_sha256,slow.sha256);assert.equal(during.validators[0].id,active.before.validators[0].id);
      await finish(pending);
      await until(async()=>{const row=await call(`/api/storage-operations/${action.id}`);return row.state==='pending'&&row.phase==='artifacts'&&row.error_code==='artifact_cleanup_pending';},'Purge non retenue après échec de nettoyage');
      afterUpload=await remote('inspect',fn,[candidate.id]);
      assert.equal(afterUpload.candidate.state,'failed');assert.equal(afterUpload.candidate.error_code,'request_rejected');assert.equal(afterUpload.candidate.revision_id,null);
      assert.equal(afterUpload.candidate.validation.error,'cleanup_failed');assert.equal(afterUpload.candidate.validation.container_removed,false);
      assert.equal(afterUpload.candidate.reserved_bytes,during.candidate.reserved_bytes);assert.deepEqual(afterUpload.revisions,during.revisions);
      assert.equal(afterUpload.archive_sha256,during.archive_sha256);assert(afterUpload.code_present&&afterUpload.validators[0].running&&afterUpload.validators[0].channel_present);
      assert.equal(afterUpload.function.purged_at,null);assert(afterUpload.guards.some(row=>row.id===action.id&&row.decision==='commit'));
    }finally{await held.release();}
    const done=await terminal(action.id);assert.equal(done.result_version,action.answer.result_version);
    const final=await remote('inspect',fn,[candidate.id]);assert(final.function.purged_at);assert.equal(final.candidate.validation,null);assert.equal(final.candidate.configuration_empty,1);
    assert.equal(final.candidate.reserved_bytes,0);assert(final.revisions.every(row=>row.stored_bytes===0&&row.deleted_at));assert.equal(final.validators.length,0);assert.equal(final.channels.length,0);
    assert.equal(final.code_present,false);assert.equal(final.archive_present,false);assert.equal(final.guards.length,0);
    await healthy();const preserved=await invoke(peer);assert.equal(preserved.data,'neighbor-data');assert.equal(preserved.cache,'neighbor-cache');assert.equal((await call(`/api/functions/${peer.id}`)).active_revision_id,neighbor.id);
    evidence.push({scenario:'live-validation-purge',candidate_id:candidate.id,operation_id:action.id,during,after_upload:afterUpload,terminal:done,final});
  });
  completed=true;
}finally{
  for(const held of gates)try{await held.release();}catch(error){cleanupErrors.push({gate:true,error:error.name});}
  for(const task of uploads)try{await finish(task);}catch(error){cleanupErrors.push({upload:true,error:error.name});}
  const socketsRestored=gates.every(held=>held.restored);
  if(!socketsRestored)cleanupErrors.push({socket_restoration_unconfirmed:true});
  if(admin&&session?.authenticated&&socketsRestored){
    try{await healthy();}catch(error){cleanupErrors.push({health:true,error:error.name});}
    for(const fn of functions)try{
      const response=await admin.get(`/api/functions/${fn.id}`);if(response.status()===200)await archive(fn);else assert.equal(response.status(),404);
      await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Garde non terminée avant nettoyage');
      const row=await call(`/api/archives/${fn.id}`);if(!row.purged_at)await terminal((await purge(fn)).id);
      const final=await call(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);
    }catch(error){cleanupErrors.push({function_id:fn.id,error:error.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({service:true,error:error.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({namespace:true,error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert.deepEqual(cleanupErrors,[],'Nettoyage incomplet');
}
