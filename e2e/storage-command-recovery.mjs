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

const run=promisify(execFile),base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-command-faults.py';
const report=new URL('storage-command-recovery.json',output),checks=[],functions=[],gates=[],requests=[],restartGuards=[],evidence=[],cleanupErrors=[];
const prefix='storage-recovery-'+randomUUID().slice(0,8),secret='recovery-secret-'+randomUUID();
let admin,caller,session,namespace,service,readToken,work,completed=false,cleanup=false;
async function save(){const temporary=new URL('storage-command-recovery.pending',output);await writeFile(temporary,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,evidence,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,function_ids:functions.map(row=>row.id)},null,2)+'\n',{mode:0o600});await rename(temporary,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function call(path,{method='GET',body,bytes,token,headers={},status=200}={}){
  const response=await (token?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()} au lieu de ${status}`);
  const text=await response.text();assert(!text.includes(secret),'Secret exposé');
  if(method==='POST'&&/\/(cache-clear|purge)$/.test(path)&&[200,202].includes(response.status()))assert.equal(response.headers().location,'/api/storage-operations/'+body.operation_id);
  return JSON.parse(text);
}
async function until(action,message,timeout=90000){const end=Date.now()+timeout;while(Date.now()<end){const result=await action();if(result)return result;await new Promise(resolve=>setTimeout(resolve,150));}assert.fail(message);}
async function healthy(){await until(async()=>{try{return (await caller.get('/healthz',{timeout:2000})).status()===200;}catch{return false;}},'Contrôle non sain');}
async function current(fn){return call(`/api/functions/${fn.id}`);}
async function idle(fn){await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'Instance non éteinte');}
async function invoke(fn,body){const value=await call(`/invoke/${fn.id}`,{method:body?'POST':'GET',body,token:readToken});await idle(fn);return value;}
async function credential(rights){return call(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'storage-command-access',rights},status:201});}
async function create(name){const row=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'storage-console.handler',cpu:.2,memory_mib:256,idle_seconds:0,timeout_seconds:10,storage:{data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},configuration:{environment:{RECOVERY_LABEL:'retained'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}}});functions.push(row);return row;}
async function publish(fn,archive){const row=await current(fn);const deployment=await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:archive.handler}});await call(`/api/deployments/${deployment.id}/artifact`,{method:'PUT',bytes:archive.bytes});return deployment;}
function tracked(promise){const task=promise.then(value=>({value}),error=>({error}));requests.push(task);return task;}
async function finish(task){const result=await task;if(result.error)throw result.error;return result.value;}
async function remote(mode,fn,extra=[]){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...extra],{timeout:120000,maxBuffer:1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
async function gate(mode,fn,extra=[]){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...extra],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,exitCode=null;createInterface({input:child.stdout}).on('line',line=>events.push(JSON.parse(line)));child.stderr.resume();
  const done=new Promise(resolve=>{child.on('exit',code=>{ended=true;exitCode=code;resolve(code);});child.on('error',()=>{ended=true;exitCode=-1;resolve(-1);});});
  const handle={events,done,expectedTermination:false,async wait(name){return until(()=>{assert(!ended||events.some(row=>row.event===name),`Garde terminée : ${exitCode}`);return events.find(row=>row.event===name);},'Événement opérateur absent : '+name,30000);},async release(){if(ended){assert(handle.expectedTermination||exitCode===0,'Restauration opérateur échouée');return;}child.stdin.end('resume\n');assert.equal(await done,0,'Restauration opérateur échouée');},async kill(){handle.expectedTermination=true;child.stdin.end('kill-helper\n');assert.notEqual(await done,0);}};
  gates.push(handle);await handle.wait('fault-active');return handle;
}
async function killControl(fn,id,decision){const value=await remote('kill-control',fn,[id,decision]);restartGuards.push({fn,unit:value.guard_unit,done:false});evidence.push(value);return restartGuards.at(-1);}
async function startControl(guard){await remote('start-control',guard.fn,[guard.unit]);guard.done=true;}
async function command(fn,kind='clear-cache',token){const row=await call(kind==='purge'?`/api/archives/${fn.id}`:`/api/functions/${fn.id}`);return {path:kind==='purge'?`/api/archives/${fn.id}/purge`:`/api/functions/${fn.id}/cache-clear`,id:randomUUID(),version:row.updated_at,name:row.name,token,kind};}
function post(action,status=[200,202],overrides={}){return call(action.path,{method:'POST',status,token:action.token,headers:{'If-Match':String(action.version)},body:{operation_id:action.id,...(action.kind==='purge'?{confirm_name:action.name}:{})},...overrides});}
async function receipt(action,state='completed'){return until(async()=>{const value=await call(`/api/storage-operations/${action.id}`);return value.state===state?value:false;},'Reçu terminal absent');}
async function observed(fn,action,decision){return until(async()=>{const value=await remote('inspect',fn),row=value.guards.find(row=>row.id===action.id);return row?.decision===decision?value:false;},'Décision réelle absente',6000);}
async function archive(fn){await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Archivage non terminé');}

await mkdir(output,{recursive:true,mode:0o700});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',output),'utf8')),timeout:180000});caller=await request.newContext({baseURL:base,timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'Session SSO réelle requise');await healthy();
  namespace=await call('/api/namespaces',{method:'POST',body:{name:prefix},status:201});service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'storage-recovery'},status:201});readToken=(await credential(['read'])).token;
  work=await mkdtemp(new URL('storage-recovery-',output).pathname);const bundle=await publicationArchive(work,'storage','storage-console.handler');
  const fn=await create('cache-recovery'),peer=await create('preserved-neighbor');await publish(fn,bundle);await publish(peer,bundle);
  await invoke(fn,{data:'permanent',cache:'initial'});await invoke(peer,{data:'neighbor-data',cache:'neighbor-cache'});
  await check('Garde indépendante : helper tué et agent réellement repris',async()=>{
    const held=await gate('watchdog',fn);const unit=(await held.wait('guard-armed')).unit;await held.kill();
    const restored=await until(async()=>{const value=await remote('guard-evidence',fn,[unit]);return value.events.find(row=>row.was_stopped===true);},'Restauration indépendante non observée',20000);
    evidence.push({scenario:'watchdog',unit,...restored});await healthy();assert.equal((await invoke(fn)).cache,'initial');
  });
  await check('Agent suspendu : observation indisponible et abandon sans effet',async()=>{
    const action=await command(fn);const held=await gate('pause-agent',fn);let before;
    try{const pending=tracked(post(action,503));before=await observed(fn,action,'undecided');const view=await call(`/api/functions/${fn.id}/storage`);assert.equal(view.storage.available,false);await finish(pending);assert.equal((await receipt(action,'aborted')).result_version,null);}finally{await held.release();}
    await healthy();assert.equal((await current(fn)).updated_at,action.version);assert.equal((await invoke(fn)).cache,'initial');evidence.push({scenario:'agent-unavailable',operation_id:action.id,before});
  });
  await check('Révocation pendant préparation : autorisation relue avant décision',async()=>{
    const access=await credential(['update']),action=await command(fn,'clear-cache',access.token),held=await gate('pause-agent',fn);const pending=tracked(post(action,401));
    try{const before=await observed(fn,action,'undecided');assert.equal(before.commands.find(row=>row.id===action.id).result_version,null);await call(`/api/tokens/${access.id}/revoke`,{method:'POST'});}finally{await held.release();}
    await finish(pending);await receipt(action,'aborted');assert.equal((await current(fn)).updated_at,action.version);assert.equal((await invoke(fn)).cache,'initial');
    evidence.push({scenario:'revoked-before-decision',operation_id:action.id});
  });
  await check('UUID d’une autre garde : refus sans abandon de son propriétaire',async()=>{
    const before=await current(fn),target=await current(peer),held=await gate('pause-agent',fn);
    const pending=tracked(call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(before.updated_at)},body:{name:before.name,config:{...before.config,storage:{...before.config.storage,cache:{enabled:true,quota_mib:9}}}}}));
    let owner;
    try{owner=await until(async()=>{const value=await remote('inspect',fn);return value.guards.find(row=>row.kind==='configuration'&&row.decision==='undecided');},'Garde de configuration absente',6000);
      const action=await command(peer);action.id=owner.id;assert.equal(action.version,target.updated_at);await post(action,409);
      const retained=await remote('inspect',fn);assert.deepEqual(retained.guards.find(row=>row.id===owner.id),owner);assert(!(await remote('inspect',peer)).commands.some(row=>row.id===owner.id));
    }finally{await held.release();}
    await finish(pending);assert.equal((await current(fn)).config.storage.cache.quota_mib,9);assert.equal((await invoke(peer)).cache,'neighbor-cache');evidence.push({scenario:'active-uuid-collision',operation_id:owner.id});
  });
  await check('SIGKILL avant décision : abandon durable sans effacement',async()=>{
    const action=await command(fn),held=await gate('pause-agent',fn),pending=tracked(post(action));let restart;
    try{const before=await observed(fn,action,'undecided');assert.equal(before.commands.find(row=>row.id===action.id).state,'preparing');restart=await killControl(fn,action.id,'undecided');}finally{await held.release();}
    await startControl(restart);await healthy();assert((await pending).error,'La réponse doit réellement être interrompue');await receipt(action,'aborted');
    const result=await remote('inspect',fn);assert.equal(result.function.updated_at,action.version);assert.equal(result.guards.length,0);assert(!result.agent_receipts.some(row=>row.operation_id===action.id));assert.equal((await invoke(fn)).cache,'initial');assert.equal((await post(action,200)).state,'aborted');
  });
  await check('Après commit : panne du cache, révocation, SIGKILL et rejeu sans second effet',async()=>{
    const access=await credential(['update']),action=await command(fn,'clear-cache',access.token),held=await gate('deny-cache',fn);let stable;
    try{const answer=await post(action,202);assert.equal(answer.state,'pending');stable=await until(async()=>{const row=await call(`/api/storage-operations/${action.id}`);return row.state==='pending'&&row.error_code==='storage_io_error'?row:false;},'Panne physique du cache non observée');
      const observedState=await observed(fn,action,'commit');assert(observedState.guards[0].storage_version!==null);assert.equal(observedState.agent[0].pending.operation_id,action.id);
      await call(`/api/tokens/${access.id}/revoke`,{method:'POST'});await post(action,401);
      const restart=await killControl(fn,action.id,'commit');await startControl(restart);
      const after=await call(`/api/storage-operations/${action.id}`);assert.equal(after.state,'pending');assert.equal(after.result_version,stable.result_version);assert.equal(after.expected_function_version,action.version);
      assert.equal((await remote('inspect',fn)).files.cache.sha256,observedState.files.cache.sha256);
    }finally{await held.release();}
    const done=await receipt(action);assert.equal(done.result_version,stable.result_version);await healthy();const value=await invoke(fn);assert.equal(value.data,'permanent');assert.equal(value.cache,null);
    await invoke(fn,{cache:'rebuilt-after-recovery'});const replay=await post(action,200,{token:undefined});assert.equal(replay.result_version,done.result_version);assert.equal((await invoke(fn)).cache,'rebuilt-after-recovery');evidence.push({scenario:'committed-cache-recovery',receipt:done});
  });
  await check('Purge : artefacts refusés, budget conservé et reprise après SIGKILL',async()=>{
    const target=await create('archive-recovery'),revision=await publish(target,bundle);await invoke(target,{data:'archive-data',cache:'archive-cache'});await archive(target);
    const action=await command(target,'purge'),held=await gate('deny-artifact',target,[revision.id]);let restart,stable;
    try{assert.equal((await post(action,202)).state,'pending');stable=await until(async()=>{const value=await call(`/api/storage-operations/${action.id}`);return value.phase==='artifacts'&&value.error_code==='artifact_cleanup_pending'?value:false;},'Erreur physique des artefacts absente');
      const view=await call(`/api/archives/${target.id}`);assert.equal(view.purged_at,null);assert(view.artifact_bytes>0);assert.equal(view.storage_operation.decision,'commit');
      const physical=await remote('inspect',target);assert(physical.revisions.some(row=>row.id===revision.id&&row.stored_bytes>0));assert.equal(physical.agent[0].state,'purged');restart=await killControl(target,action.id,'commit');
    }finally{await held.release();}
    await startControl(restart);await healthy();const done=await receipt(action);assert.equal(done.result_version,stable.result_version);const view=await call(`/api/archives/${target.id}`);assert(view.purged_at&&view.artifact_bytes===0&&!view.storage_operation);assert.equal((await post(action,200)).state,'completed');
    const neighbor=await invoke(peer);assert.equal(neighbor.data,'neighbor-data');assert.equal(neighbor.cache,'neighbor-cache');evidence.push({scenario:'artifact-recovery',receipt:done});
  });
  completed=true;
}finally{
  for(const held of gates)try{await held.release();}catch(error){cleanupErrors.push({gate:true,error:error.name});}
  for(const guard of restartGuards)if(!guard.done)try{await startControl(guard);}catch(error){cleanupErrors.push({restart:true,error:error.name});}
  await Promise.all(requests);
  if(admin&&session?.authenticated) {
    try{await healthy();}catch(error){cleanupErrors.push({health:true,error:error.name});}
    for(const fn of functions)try{
      const response=await admin.get(`/api/functions/${fn.id}`);
      if(response.status()===200){await until(async()=>!(await current(fn)).storage_operation,'Garde active non terminée avant nettoyage');await archive(fn);}else assert.equal(response.status(),404);
      await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Garde d’archive non terminée avant nettoyage');
      const row=await call(`/api/archives/${fn.id}`);if(!row.purged_at){const action=await command(fn,'purge');await post(action);await receipt(action);}
      const final=await call(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);
    }catch(error){cleanupErrors.push({function_id:fn.id,error:error.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({service:true,error:error.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({namespace:true,error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert.deepEqual(cleanupErrors,[]);
}
