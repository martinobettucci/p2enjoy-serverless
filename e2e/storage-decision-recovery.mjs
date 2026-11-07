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
const helper='/srv/p2enjoy-serverless/e2e/storage-command-faults.py',report=new URL('storage-decision-recovery.json',output);
const checks=[],functions=[],gates=[],tasks=[],restarts=[],evidence=[],cleanupErrors=[];
const prefix='storage-recovery-'+randomUUID().slice(0,8),secret='decision-secret-'+randomUUID();
let admin,purgeAdmin,caller,session,purgeSession,namespace,service,readToken,work,completed=false,cleanup=false;
async function save(){const pending=new URL('storage-decision-recovery.pending',output);await writeFile(pending,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,evidence,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,function_ids:functions.map(fn=>fn.id)},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name,message:error.message});throw error;}finally{await save();}}
async function call(path,{method='GET',body,bytes,token,headers={},status=200,context=admin,csrf=session?.csrf_token}={}){
  const response=await (token?caller:context).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':csrf}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()} au lieu de ${status}`);
  const text=await response.text();assert(!text.includes(secret),'Secret exposé');
  if(method==='POST'&&/\/(cache-clear|purge)$/.test(path)&&[200,202].includes(response.status()))assert.equal(response.headers().location,'/api/storage-operations/'+body.operation_id);
  return JSON.parse(text);
}
async function until(action,message,timeout=90000){const end=Date.now()+timeout;while(Date.now()<end){const result=await action();if(result)return result;await new Promise(resolve=>setTimeout(resolve,150));}assert.fail(message);}
async function healthy(){await until(async()=>{try{return (await caller.get('/healthz',{timeout:2000})).status()===200;}catch{return false;}},'Contrôle non sain');}
async function remote(mode,fn,extra=[]){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...extra],{timeout:120000,maxBuffer:1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
function tracked(promise){const task={settled:false,checked:false};task.done=promise.then(value=>({value}),error=>({error})).then(result=>{task.settled=true;return result;});tasks.push(task);return task;}
async function finish(task){const result=await task.done;task.checked=true;if(result.error)throw result.error;return result.value;}
async function gate(mode,fn,extra=[]){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...extra],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,exitCode=null;createInterface({input:child.stdout}).on('line',line=>events.push(JSON.parse(line)));child.stderr.resume();child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{child.on('close',code=>{ended=true;exitCode=code;resolve(code);});child.on('error',()=>{ended=true;exitCode=-1;resolve(-1);});});
  const held={events,restored:false,killed:false,async wait(name){return until(()=>{const row=events.find(item=>item.event===name);assert(row||!ended,`Garde terminée : ${exitCode}`);return row;},'Événement absent : '+name,30000);},
    async kill(){held.killed=true;child.stdin.end('kill-helper\n');await until(()=>ended,'Helper non terminé',12000);assert.notEqual(await done,0);},
    async release(){
      if(held.restored)return;
      if(!ended&&!child.stdin.writableEnded)child.stdin.end('resume\n');
      await until(()=>ended,'Fermeture SSH non confirmée',110000);await done;
      const armed=events.find(row=>row.event==='guard-armed');
      if(held.killed){
        assert(armed,'Garde indépendante absente');
        const restored=await until(async()=>{const result=await remote('guard-evidence',fn,[armed.unit]);return result.events.find(row=>row.independent);},'Restauration indépendante absente',65000);
        assert.equal(restored.function_id,fn.id);assert.equal(restored.kind,armed.kind);
        if(mode==='hold-control-writer'){assert.equal(restored.operation_id,extra[0]);assert.equal((await remote('writer-status',fn,extra)).event,'writer-released');}
        evidence.push({scenario:'independent-restoration',unit:armed.unit,...restored});
      }else assert.equal(exitCode,0,'Restauration opérateur échouée');
      held.restored=true;
    }};
  gates.push(held);await held.wait('fault-active');return held;
}
async function invoke(fn,body){const value=await call(`/invoke/${fn.id}`,{method:body?'POST':'GET',body,token:readToken});await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'Instance non éteinte');return value;}
async function create(name){const fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'storage-console.handler',cpu:.2,memory_mib:256,idle_seconds:0,timeout_seconds:10,storage:{data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},configuration:{environment:{DECISION_LABEL:'retained'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}}});functions.push(fn);return fn;}
async function publish(fn,bundle){const row=await call(`/api/functions/${fn.id}`),candidate=await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:bundle.handler}});await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:bundle.bytes});}
async function archive(fn){await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Archivage non terminé');}
async function command(fn,kind='clear-cache'){const row=await call(kind==='purge'?`/api/archives/${fn.id}`:`/api/functions/${fn.id}`);return {id:randomUUID(),fn,kind,version:row.updated_at,name:row.name,path:kind==='purge'?`/api/archives/${fn.id}/purge`:`/api/functions/${fn.id}/cache-clear`};}
function post(action,status=[200,202],options={}){return call(action.path,{method:'POST',status,headers:{'If-Match':String(action.version)},body:{operation_id:action.id,...(action.kind==='purge'?{confirm_name:action.name}:{})},...options});}
async function receipt(action,state='completed'){return until(async()=>{const row=await call(`/api/storage-operations/${action.id}`);return row.state===state?row:false;},'Reçu terminal absent');}
async function pendingCache(fn){const action=await command(fn),held=await gate('deny-cache',fn);const answer=await post(action,202);const pending=await until(async()=>{const row=await call(`/api/storage-operations/${action.id}`);return row.state==='pending'&&row.error_code==='storage_io_error'?row:false;},'Erreur physique cache absente');assert.equal(answer.result_version,pending.result_version);const physical=await remote('inspect',fn);assert(physical.guards.some(row=>row.id===action.id&&row.decision==='commit'));return {action,held,pending,physical};}
async function verifyCache(action,stable,value){const done=await receipt(action);assert.equal(done.result_version,stable.result_version);assert.equal(done.expected_function_version,action.version);await healthy();const result=await invoke(action.fn);assert.equal(result.data,'permanent');assert.equal(result.cache,null);await invoke(action.fn,{cache:value});assert.deepEqual(await post(action,200),done);assert.equal((await invoke(action.fn)).cache,value);return done;}

await mkdir(output,{recursive:true,mode:0o700});await save();
try{
  const mainState=JSON.parse(await readFile(new URL('admin-session.json',output),'utf8')),purgeState=JSON.parse(await readFile(new URL('purge-admin-session.json',output),'utf8'));
  const mainCookie=mainState.cookies.find(row=>row.name==='__Host-p2-session'),purgeCookie=purgeState.cookies.find(row=>row.name==='__Host-p2-session');
  assert(mainCookie&&purgeCookie&&mainCookie.value!==purgeCookie.value,'Deux connexions SSO indépendantes sont requises');
  admin=await request.newContext({baseURL:base,storageState:mainState,timeout:180000});purgeAdmin=await request.newContext({baseURL:base,storageState:purgeState,timeout:180000});caller=await request.newContext({baseURL:base,timeout:180000});
  session=await call('/api/session');purgeSession=await call('/api/session',{context:purgeAdmin});assert(session.authenticated&&purgeSession.authenticated,'Deux sessions SSO réelles requises');await healthy();
  namespace=await call('/api/namespaces',{method:'POST',body:{name:prefix},status:201});service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'storage-decisions'},status:201});
  readToken=(await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'observe-real-data',rights:['read']}})).token;
  work=await mkdtemp(new URL('storage-decisions-',output).pathname);const bundle=await publicationArchive(work,'decisions','storage-console.handler');
  const fn=await create('cache-after-decision'),peer=await create('preserved-neighbor'),target=await create('archive-revoked-session');
  for(const row of [fn,peer,target])await publish(row,bundle);
  await invoke(fn,{data:'permanent',cache:'initial'});await invoke(peer,{data:'neighbor-data',cache:'neighbor-cache'});await invoke(target,{data:'archive-data',cache:'archive-cache'});await archive(target);
  await check('Purge : session administrateur fermée pendant préparation, abandon sans effacement',async()=>{
    const action=await command(target,'purge'),before=await remote('inspect',target),held=await gate('pause-agent',target);
    const pending=tracked(post(action,401,{context:purgeAdmin,csrf:purgeSession.csrf_token}));let logout;
    try{
      await until(async()=>{const value=await remote('inspect',target);return value.guards.some(row=>row.id===action.id&&row.decision==='undecided');},'Préparation de purge absente',6000);
      logout=tracked(call('/auth/logout',{method:'POST',context:purgeAdmin,csrf:purgeSession.csrf_token}));
      await until(async()=>!(await call('/api/session',{context:purgeAdmin})).authenticated,'Session non fermée',6000);
      assert.equal(pending.settled,false,'Purge terminée avant observation du retrait de session');
    }finally{await held.release();}
    await finish(pending);assert((await finish(logout)).signed_out);const result=await receipt(action,'aborted');assert.equal(result.result_version,null);
    const after=await remote('inspect',target);for(const key of ['function','files','revisions','artifacts','agent'])assert.deepEqual(after[key],before[key]);
    assert.equal(after.guards.length,0);assert(!after.agent_receipts.some(row=>row.operation_id===action.id));assert((await call('/api/session')).authenticated);
    await post(action,401,{context:purgeAdmin,csrf:purgeSession.csrf_token});assert.equal((await post(action,200)).state,'aborted');
    evidence.push({scenario:'administrator-session-revoked',operation_id:action.id,before,after,receipt:result});
  });
  await check('Après décision : transport agent refusé, reçu conservé et reprise sans second vidage',async()=>{
    const blocked=await pendingCache(fn),transport=await gate('deny-agent-socket',fn,[blocked.action.id]);let failed;
    try{
      failed=await until(async()=>{const row=await call(`/api/storage-operations/${blocked.action.id}`);return row.state==='pending'&&row.error_code==='storage_transport'?row:false;},'Erreur transport absente');
      assert.equal(failed.result_version,blocked.pending.result_version);await blocked.held.release();
      const physical=await until(async()=>{const value=await remote('inspect',fn);return value.agent_receipts.some(row=>row.operation_id===blocked.action.id)?value:false;},'Agent non terminé pendant coupure transport');
      assert.equal(physical.commands.find(row=>row.id===blocked.action.id).state,'pending');assert.deepEqual(physical.files.data,blocked.physical.files.data);
      evidence.push({scenario:'agent-completed-control-disconnected',operation_id:blocked.action.id,receipt:failed,physical});
    }finally{await transport.release();await blocked.held.release();}
    await verifyCache(blocked.action,blocked.pending,'rebuilt-after-transport');
  });
  await check('Après décision : writer contrôle occupé, agent terminé et garde indépendante du writer',async()=>{
    const blocked=await pendingCache(fn),writer=await gate('hold-control-writer',fn,[blocked.action.id]);let retained,errors;
    try{
      const active=await writer.wait('fault-active');assert.equal(active.identity.effective_uid,active.identity.sidecar_uids['-wal']);
      await blocked.held.release();
      retained=await until(async()=>{const value=await remote('inspect',fn);return value.agent_receipts.some(row=>row.operation_id===blocked.action.id)?value:false;},'Reçu agent absent sous contention',25000);
      assert.equal(retained.commands.find(row=>row.id===blocked.action.id).state,'pending');assert(retained.guards.some(row=>row.id===blocked.action.id&&row.decision==='commit'));
      errors=await until(async()=>{const value=await remote('control-errors',fn,[blocked.action.id]);return value.events.some(row=>row.error_code==='control_database_unavailable')?value:false;},'Diagnostic SQLite réel absent',25000);
      await writer.kill();
    }finally{await writer.release();await blocked.held.release();}
    const done=await verifyCache(blocked.action,blocked.pending,'rebuilt-after-writer');
    evidence.push({scenario:'control-writer-contention',operation_id:blocked.action.id,retained,errors,receipt:done});
  });
  await check('Contrôle arrêté après décision : redémarrage effectif par garde indépendante',async()=>{
    const blocked=await pendingCache(fn);const stopped=await remote('kill-control-watchdog',fn,[blocked.action.id,'commit']);const guard={fn,unit:stopped.guard_unit,done:false};restarts.push(guard);
    try{
      const restarted=await until(async()=>{const value=await remote('guard-evidence',fn,[guard.unit]);return value.events.find(row=>row.kind==='control'&&row.independent);},'Redémarrage indépendant absent',20000);
      assert.equal(restarted.was_running,false);assert.equal(restarted.exit_code_before,137);assert.equal(restarted.running,true);assert(restarted.stop_mutator_joined&&restarted.lock_removed);guard.done=true;
      await until(async()=>{let response;try{response=await admin.get(`/api/storage-operations/${blocked.action.id}`,{timeout:3000});}catch{return false;}if([502,503].includes(response.status()))return false;assert.equal(response.status(),200);return true;},'API non rétablie après redémarrage',30000);
      const retained=await receipt(blocked.action,'pending');assert.equal(retained.result_version,blocked.pending.result_version);
      evidence.push({scenario:'independent-control-restart',operation_id:blocked.action.id,stopped,restarted});
    }finally{await blocked.held.release();}
    await verifyCache(blocked.action,blocked.pending,'rebuilt-after-independent-restart');
    const neighbor=await invoke(peer);assert.equal(neighbor.data,'neighbor-data');assert.equal(neighbor.cache,'neighbor-cache');
  });
  completed=true;
}finally{
  for(const held of gates)try{await held.release();}catch(error){cleanupErrors.push({gate:true,error:error.name});}
  for(const guard of restarts)if(!guard.done)try{await remote('start-control',guard.fn,[guard.unit]);guard.done=true;}catch(error){cleanupErrors.push({restart:true,error:error.name});}
  for(const task of tasks)if(!task.checked)try{await finish(task);}catch(error){cleanupErrors.push({request:true,error:error.name});}
  if(admin&&session?.authenticated&&gates.every(held=>held.restored)&&restarts.every(guard=>guard.done)){
    try{await healthy();}catch(error){cleanupErrors.push({health:true,error:error.name});}
    for(const fn of functions)try{
      const response=await admin.get(`/api/functions/${fn.id}`);if(response.status()===200){await until(async()=>!(await call(`/api/functions/${fn.id}`)).storage_operation,'Garde active avant nettoyage');await archive(fn);}else assert.equal(response.status(),404);
      await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Garde archive avant nettoyage');
      const row=await call(`/api/archives/${fn.id}`);if(!row.purged_at){const action=await command(fn,'purge');await post(action);await receipt(action);}
      const final=await call(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);
    }catch(error){cleanupErrors.push({function_id:fn.id,error:error.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({service:true,error:error.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({namespace:true,error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});await admin?.dispose();await purgeAdmin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert.deepEqual(cleanupErrors,[],'Nettoyage incomplet');
}
