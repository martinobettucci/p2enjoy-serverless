// @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle
// @verifies docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle | docs/ADMISSION.md#observation-durable-des-intentions-par-les-gardes
// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md
// @spec docs/BACKLOG.md#sls-146 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md#diagnostic-du-refus-de-commit-zip--sls-146
// @verifies docs/BACKLOG.md#sls-146 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md#diagnostic-du-refus-de-commit-zip--sls-146
// Real HTTPS administration, actual SSO session, host agent, Docker and process failures.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const run=promisify(execFile),root=fileURLToPath(new URL('../',import.meta.url));
const diagnosticInterruption=process.argv[2]==='--diagnose-guard-interruption';
assert(process.argv.length===2||(process.argv.length===3&&diagnosticInterruption),'Argument de campagne inconnu');
const output=path.join(root,'.local/e2e'),report=path.join(output,diagnosticInterruption?'function-storage-guard-interruption.json':'function-storage.json');
const base='https://serverless.lelabs.tech',prefix='storage-api-'+randomUUID().slice(0,8);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/function-storage-faults.py';
const expectedDataHash=createHash('sha256').update(Buffer.alloc(1280*1024,'K')).digest('hex');
await mkdir(output,{recursive:true,mode:0o700});
await writeFile(report,JSON.stringify({completed:false,cleanup:false,skipped:0})+'\n');
const state=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));
const admin=await request.newContext({baseURL:base,storageState:state,timeout:180000});
const caller=await request.newContext({baseURL:base,timeout:180000});
const checks=[],functions=[],tokens=[],faults=[],pending=[],storageArchives=[],cleanupErrors=[],requestOutcomes=[],invocations=[],publicationEvidence=[],finalizationFailures=[],diagnosticObservations=[];
let session,namespace,service,work,completed=false,needsStart=false,primaryFailure=null;

async function call(url,{method='GET',body,bytes,token,headers={},status=200}={}) {
  const response=await (token?caller:admin).fetch(url,{method,data:bytes??body,
    headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session.csrf_token}),
      ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  const bodyBytes=await response.body(),text=bodyBytes.toString('utf8');
  const identifier=name=>{const value=response.headers()[name];return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value??'')?value:null;};
  const diagnostic={method,path:url.split('?')[0],status:response.status(),expected_status:status,
    request_id:identifier('x-request-id'),operation_id:identifier('x-serverless-operation-id'),function_id:identifier('x-serverless-function-id'),
    mutation_committed:response.headers()['x-serverless-mutation-committed']??null,
    response_bytes:bodyBytes.length,response_sha256:createHash('sha256').update(bodyBytes).digest('hex')};
  requestOutcomes.push(diagnostic);
  if(response.status()===503){
    let message;try{message=JSON.parse(text).error;}catch{diagnostic.failure='invalid_json';}
    if(diagnostic.failure!=='invalid_json')
    diagnostic.failure=message==='Le stockage du contrôle est temporairement indisponible.'?'control_database_unavailable':
      message==='Un nettoyage de déploiement doit être repris.'?'deployment_cleanup_pending':'other';
  }
  assert.equal(response.status(),status,`${method} ${url}: attendu ${status}, reçu ${response.status()}`);
  return {data:JSON.parse(text),headers:response.headers()};
}
async function object(url,options){return (await call(url,options)).data;}
async function current(fn){return object(`/api/functions/${fn.id}`);}
function tracked(promise){const task=promise.then(value=>({value}),error=>({error}));pending.push(task);return task;}
async function finish(task){const result=await task;if(result.error)throw result.error;return result.value;}
async function remote(mode,fn,extra=[]){
  const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,mode,...(fn?[fn.id]:[]),...extra],{timeout:120000,maxBuffer:1024*1024});
  return JSON.parse(stdout.trim().split('\n').at(-1));
}
function diagnostic(error){const location=String(error?.stack??'').match(/function-storage\.mjs:(\d+):(\d+)/);return {name:error?.name??'UnknownError',operator:error?.operator,source:location?{line:Number(location[1]),column:Number(location[2])}:undefined,message_sha256:createHash('sha256').update(String(error?.message??'')).digest('hex')};}
async function finalizing(action,finalizer,scope){
  let primary=null;
  try{return await action();}catch(error){primary=error;throw error;}
  finally{try{await finalizer();}catch(error){finalizationFailures.push({scope,error:diagnostic(error),primary:primary?diagnostic(primary):null});if(!primary)throw error;}}
}
function captureStream(stream){
  const hash=createHash('sha256');let bytes=0,tail=Buffer.alloc(0),finished=false,digest;
  stream.on('data',chunk=>{bytes+=chunk.length;hash.update(chunk);tail=Buffer.concat([tail,chunk]);if(tail.length>65536)tail=tail.subarray(tail.length-65536);});
  return ()=>{if(!finished){digest=hash.digest('hex');finished=true;}return {bytes,sha256:digest,retained_bytes:tail.length,truncated:bytes>tail.length,encoding:'base64',suffix:tail.toString('base64')};};
}
async function until(action,message){const end=Date.now()+45000;while(Date.now()<end){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function invokeCode(fn,published,credential,pinned=false){const tag=randomUUID(),response=await caller.get(`/invoke/${fn.id}${pinned?'@'+published.code_hash:''}`,{headers:{'X-Serverless-Token':credential,'X-Qualification-Tag':tag}});assert.equal(response.status(),200);const value=await response.json();assert.equal(value.tag,tag);assert.equal(value.secretPresent,false);assert.equal(value.requestId,response.headers()['x-serverless-request-id']);assert.equal(response.headers()['x-serverless-code-hash'],published.code_hash);invocations.push({id:value.requestId,function_id:fn.id,requested_code_hash:pinned?published.code_hash:null,resolved_code_hash:published.code_hash});await until(async()=>!(await object(`/api/functions/${fn.id}/instances`)).items.length,'runtime_instances_not_released');}
async function promoteCode(fn,published){const row=await current(fn);await object(`/api/functions/${fn.id}/versions/${published.code_hash}/promote`,{method:'POST',headers:{'If-Match':String(row.updated_at)}});assert.equal((await current(fn)).active_revision_id,published.revision_id);}
async function purgeArchive(fn){await until(async()=>!(await object(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await object(`/api/archives/${fn.id}`);const response=await admin.post(`/api/archives/${fn.id}/purge`,{headers:{Origin:base,'X-CSRF-Token':session.csrf_token,'If-Match':String(row.updated_at)},data:{operation_id:randomUUID(),confirm_name:row.name}});assert([200,202].includes(response.status()));const op=await response.json();await until(async()=>{const v=await object(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'public_purge_not_completed');const after=await object(`/api/archives/${fn.id}`);assert(after.purged_at&&after.artifact_bytes===0&&!after.storage_operation);return {function_id:fn.id,namespace_id:namespace.id,operation_id:op.id,purged:true,artifact_bytes:after.artifact_bytes};}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:diagnostic(error)});throw error;}
}
async function token(rights){
  const value=await object(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:rights.length===1&&rights[0]==='read'?'invoke-published-storage-code':'storage-mutation',rights}});
  tokens.push(value);return value;
}
const volumes=(data=2,cache=2)=>({data:{enabled:true,quota_mib:data},cache:{enabled:true,quota_mib:cache},concurrency:'exclusive'});
async function create(name,storage=volumes()){
  const fn=await object(`/api/services/${service.id}/functions`,{method:'POST',status:201,
    body:{name,config:{handler:'src/handlers.echo',idle_seconds:0,storage}}});functions.push(fn);return fn;
}
async function update(fn,storage,{credential,status=200}={}){
  const row=await current(fn);
  return call(`/api/functions/${fn.id}`,{method:'PUT',status,token:credential,
    headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,storage}}});
}
async function healthy(){
  const end=Date.now()+90000;
  while(Date.now()<end){
    try{const r=await caller.get('/healthz',{timeout:3000});if(r.status()===200)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  assert.fail('Contrôle non rétabli');
}
async function restoreControl(){
  await run('ssh',[...ssh,'runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','start','serverless-api'],{timeout:30000});
  await healthy();needsStart=false;
}
async function crashControl(held){
  needsStart=true;
  await finalizing(()=>held.release('kill-control'),restoreControl,'control_restart');
}
async function fault(mode,fn){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,fn.id],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,code=null,signal=null,spawnError=null,protocolError=null,inputError=null;
  child.stdin.on('error',error=>{inputError=diagnostic(error);});
  const stdout=captureStream(child.stdout),stderr=captureStream(child.stderr);
  let line=Buffer.alloc(0),overflow=false;
  function append(part){
    if(overflow)return;
    if(line.length+part.length>65536){protocolError??=diagnostic(new Error('fault_line_limit'));line=Buffer.alloc(0);overflow=true;return;}
    line=Buffer.concat([line,part]);
  }
  function finishLine(){
    if(!overflow){try{assert(events.length<128,'fault_event_limit');const value=JSON.parse(line.toString('utf8'));assert(value&&typeof value==='object'&&!Array.isArray(value)&&typeof value.event==='string','fault_event_invalid');events.push(value);}
      catch(error){protocolError??=diagnostic(error);}}
    line=Buffer.alloc(0);overflow=false;
  }
  child.stdout.on('data',chunk=>{
    let start=0;
    for(let index=0;index<chunk.length;index++)if(chunk[index]===10){append(chunk.subarray(start,index));finishLine();start=index+1;}
    append(chunk.subarray(start));
  });
  child.stdout.on('end',()=>{if(line.length||overflow)finishLine();});
  const done=new Promise(resolve=>{child.on('close',(value,terminated)=>{ended=true;code=value;signal=terminated;resolve(value);});child.on('error',error=>{spawnError=diagnostic(error);});});
  const handle={child,done,events,mode,functionId:fn.id,expectedTermination:false,get exitCode(){return code;},get ended(){return ended;},
    validateTransport(){assert(!protocolError,'fault_protocol_error');assert(!spawnError,'fault_spawn_error');assert(!inputError,'fault_input_error');},
    transport(){assert(ended,'fault_transport_still_running');return {signal,spawn_error:spawnError,input_error:inputError,protocol_error:protocolError,stdout:stdout(),stderr:stderr()};},async wait(event){
    const end=Date.now()+35000;
    while(Date.now()<end){assert(!protocolError,'fault_protocol_error');const value=events.find(row=>row.event===event);if(value)return value;
      assert(!ended,`Garde de panne interrompue : ${code}`);await new Promise(resolve=>setTimeout(resolve,10));}
    assert.fail('Phase réelle non observée : '+event);
  },async release(command='resume'){
    if(!ended)child.stdin.end(command+'\n');assert.equal(await done,0,'Échec de restauration de la garde');handle.validateTransport();
    if(['commit','commit-database-busy'].includes(mode)){
      const identities=events.filter(row=>row.event==='control-writer-identity');
      assert.equal(identities.length,mode==='commit'?1:2);
      const registryIdentities=events.filter(row=>row.event==='registry-writer-identity');
      assert.equal(registryIdentities.length,1);identities.push(...registryIdentities);
      const observers=events.filter(row=>row.event==='control-observer-ready');assert.equal(observers.length,1);
      assert.equal(observers[0].autocommit,true);identities.push(...observers);
      for(const row of identities){assert(row.effective_uid>0);assert(row.effective_gid>0);assert.equal(row.operator_uid,0);
        assert(Object.values(row.sidecar_uids).every(uid=>uid===row.effective_uid));}
    }
  }};
  faults.push(handle);await handle.wait(mode==='hold-lease'?'leased':'watching');return handle;
}

try{
  session=await (await admin.get('/api/session')).json();assert(session.authenticated,'Session SSO réelle requise');
  await healthy();const initial=await remote('health');assert.equal(initial.allocated_bytes,0);assert.equal(initial.leases,0);
  namespace=await object('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});
  service=await object(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'function-storage'}});
  let fn;
  if(diagnosticInterruption){
    fn=await create('guard-interruption');const before=await remote('inspect',fn);
    const held=await fault('commit',fn);held.expectedTermination=true;
    const armed=held.events.find(v=>v.event==='recovery-guard');assert(armed?.helper);
    const interrupted=await remote('interrupt-guard',fn,[Buffer.from(JSON.stringify(armed.helper)).toString('hex')]);
    assert.equal(interrupted.signal,'SIGTERM');assert.deepEqual(interrupted.helper,armed.helper);
    assert.equal(await held.done,1);
    const primary=held.events.find(v=>v.event==='fault-primary'),final=held.events.find(v=>v.event==='fault-finalization');
    assert.equal(primary.type,'InterruptedError');assert.equal(primary.reason,'operator_interrupted');
    assert.equal(final.completed,true);assert.deepEqual(final.errors,[]);
    assert.equal(held.events.at(-1).event,'fault-failed');assert.equal(held.events.at(-1).reason,'operator_interrupted');
    assert(!held.events.some(v=>v.event==='preparation-observed'||v.event==='paused'));
    const after=await remote('inspect',fn);assert.deepEqual(after.receipt,before.receipt);assert.equal(after.operation,null);assert.deepEqual(after.storage,before.storage);
    diagnosticObservations.push({scenario:'real-guard-sigterm-without-mutation',status:'passed',native_exit:held.exitCode,primary_retained:true,finalization_completed:true,configuration_unchanged:true});
    completed=true;
  }else{
  await check('Création HTTPS : quotas réellement publiés avant réponse et intention terminée',async()=>{
    fn=await create('durable-data');const actual=await remote('inspect',fn);
    assert.equal(fn.storage_operation,null);assert.equal(actual.operation,null);assert.equal(actual.receipt.decision,'committed');
    assert.equal(actual.storage.volumes.data.quota_bytes,2*1024**2);assert.equal(actual.storage.volumes.cache.quota_bytes,2*1024**2);
    assert.equal(actual.storage.leases,0);assert(!actual.storage.pending);
  });
  await check('Pilote embarqué : résolution sans mutation de volumes sous un vrai verrou écrivain SQLite',async()=>{
    const evidence=await remote('empty-resolution-busy',fn);
    assert.equal(evidence.writer_lock_held,true);assert.equal(evidence.resolved,true);
    assert(evidence.writer_identity.effective_uid>0);assert.equal(evidence.operator_uid,0);
    assert(Object.values(evidence.writer_identity.sidecar_uids).every(uid=>uid===evidence.writer_identity.effective_uid));
    await healthy();assert.equal((await remote('inspect',fn)).operation,null);
  });
  await check('SIGTERM réel pendant la fermeture du registre : identité conservée et verrou libéré',async()=>{
    const evidence=await remote('registry-close-interruption',fn);
    assert.equal(evidence.interruption_deferred,true);assert.equal(evidence.writer_closed,true);
    assert.equal(evidence.writer_reacquired,true);assert.equal(evidence.operator_uid,0);
    assert(evidence.observer_interruption_deferred&&evidence.observer_closed&&evidence.observer_reopened&&evidence.observer_autocommit);
    for(const identity of [evidence.writer_identity,evidence.replacement_identity,evidence.observer_identity,evidence.replacement_observer_identity]){
      assert(identity.effective_uid>0);assert(identity.effective_gid>0);
      assert(Object.values(identity.sidecar_uids).every(uid=>uid===identity.effective_uid));
    }
    requestOutcomes.push({registry_close_interruption:evidence});
    await healthy();assert.equal((await remote('inspect',fn)).operation,null);
  });
  await check('Garde indépendante : SIGKILL du helper suspendant l’agent puis reprise réelle par le timer',async()=>{
    const held=await fault('watchdog',fn);await held.wait('paused');
    held.expectedTermination=true;held.child.stdin.end('kill-helper\n');assert.notEqual(await held.done,0);
    // The agent, not a cached control health response, must answer again.
    let resumed=false;const deadline=Date.now()+25000;
    while(Date.now()<deadline){try{if((await remote('health')).ready){resumed=true;break;}}catch{}
      await new Promise(resolve=>setTimeout(resolve,100));}
    assert(resumed,'Le timer indépendant doit rétablir le vrai agent');await healthy();
    const guard=held.events.find(row=>row.event==='recovery-guard');
    const evidence=await remote('guard-evidence',fn,[guard.unit]);
    assert.equal(evidence.events.length,1);assert.equal(evidence.events[0].was_stopped,true);
    held.events.push(...evidence.events);
  });
  await check('Écriture Docker réelle puis quota inférieur à l’usage refusé sans changer la fonction',async()=>{
    await remote('write',fn);const before=await current(fn);
    await update(fn,volumes(1,2),{status:422});const after=await current(fn),actual=await remote('inspect',fn);
    assert.deepEqual(after.config,before.config);assert.equal(after.updated_at,before.updated_at);
    assert.equal(actual.operation,null);assert.equal(actual.receipt.decision,'aborted');
    const data=JSON.parse((await remote('read',fn)).result);assert.equal(data.bytes,1310720);assert.equal(data.sha256,expectedDataHash);
  });
  await check('Modification des quotas et désactivation/réactivation conservant les données',async()=>{
    await update(fn,volumes(3,3));const disabled=volumes(3,3);disabled.data.enabled=false;
    await update(fn,disabled);let actual=await remote('inspect',fn);
    assert.equal(actual.storage.volumes.data.enabled,false);assert.equal(actual.storage.volumes.data.quota_bytes,3*1024**2);
    await update(fn,volumes(3,3));assert.equal(JSON.parse((await remote('read',fn)).result).cache,'cached');
    actual=await remote('inspect',fn);assert.equal(actual.operation,null);
  });
  await check('Bail d’un vrai conteneur : modification et suppression refusées sans retirer le consommateur',async()=>{
    const held=await fault('hold-lease',fn);
    await finalizing(async()=>{await update(fn,volumes(4,3),{status:409});await call(`/api/functions/${fn.id}`,{method:'DELETE',status:409});},()=>held.release('release'),'hold_lease_release');
    assert.equal((await remote('inspect',fn)).storage.leases,0);assert.equal((await current(fn)).config.storage.data.quota_mib,3);
  });
  await check('Deux créations de même nom : une publication, aucune allocation du perdant',async()=>{
    const body={name:'same-name',config:{storage:volumes(1,1)}};
    const results=await Promise.all([1,2].map(()=>admin.post(`/api/services/${service.id}/functions`,
      {data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token}})));
    assert.deepEqual(results.map(r=>r.status()).sort(),[201,409]);
    const duplicate=await results.find(r=>r.status()===201).json();functions.push(duplicate);
    assert.equal((await remote('health')).allocated_bytes,8*1024**2);
    assert.equal((await remote('health')).pending_functions,0);
  });
  await check('Révocation pendant prepare observé : refus de commit et ancienne configuration intacte',async()=>{
    const credential=await token(['read','update']);const held=await fault('prepare',fn);
    const request=tracked(update(fn,volumes(4,3),{credential:credential.token,status:401}));
    await finalizing(async()=>{
      await held.wait('paused');
      const pendingState=(await current(fn)).storage_operation;assert.equal(pendingState.decision,'undecided');
      await call(`/api/services/${service.id}/configuration`,{method:'PUT',body:{environment:{MUST_NOT_APPLY:'yes'}},status:409});
      await call(`/api/functions/${fn.id}`,{method:'DELETE',status:409});
      await call(`/api/tokens/${credential.id}/revoke`,{method:'POST'});
    },()=>held.release(),'revocation_guard_release');
    await finish(request);assert.equal((await current(fn)).config.storage.data.quota_mib,3);
    const actual=await remote('inspect',fn);assert.equal(actual.receipt.decision,'aborted');assert.equal(actual.operation,null);
  });
  await check('SIGKILL avant décision : abandon repris et données acquittées conservées',async()=>{
    const held=await fault('prepare',fn);const request=tracked(update(fn,volumes(4,3)));
    await finalizing(async()=>{await held.wait('paused');await crashControl(held);},async()=>{if(!held.child.stdin.writableEnded)await held.release();},'prepare_crash_guard_release');
    const result=await request;assert(result.error,'La connexion interrompue ne doit pas annoncer un succès');
    await healthy();assert.equal((await current(fn)).config.storage.data.quota_mib,3);
    const actual=await remote('inspect',fn);assert.equal(actual.receipt.decision,'aborted');assert.equal(actual.operation,null);
    assert.equal(JSON.parse((await remote('read',fn)).result).bytes,1310720);
  });
  await check('SIGKILL après décision : nouveau quota conservé et commit confirmé au redémarrage',async()=>{
    const held=await fault('commit',fn);const request=tracked(update(fn,volumes(4,3)));
    await finalizing(async()=>{await held.wait('paused');await crashControl(held);},async()=>{if(!held.child.stdin.writableEnded)await held.release();},'commit_crash_guard_release');
    assert((await request).error);await healthy();const row=await current(fn),actual=await remote('inspect',fn);
    assert.equal(row.config.storage.data.quota_mib,4);assert.equal(actual.storage.volumes.data.quota_bytes,4*1024**2);
    assert.equal(actual.receipt.decision,'committed');assert.equal(actual.operation,null);
  });
  await check('Confirmation indisponible après commit : 503 explicite puis reprise sans compensation',async()=>{
    const held=await fault('commit',fn);const request=tracked(update(fn,volumes(5,3),{status:503}));
    await finalizing(async()=>{
      const phase=await held.wait('paused');const response=await finish(request);
      assert.equal(response.headers['x-serverless-mutation-committed'],'true');
      assert.equal(response.headers['x-serverless-operation-id'],phase.operation_id);
      assert.equal(response.headers['x-serverless-function-id'],fn.id);assert.match(response.data.error,/enregistrée/);
      assert.equal((await current(fn)).config.storage.data.quota_mib,5);
    },()=>held.release(),'commit_guard_release');
    await healthy();assert.equal((await remote('inspect',fn)).operation,null);
  });
  await check('Confirmation perdue et écrivain SQLite occupé : audit en panne sans masquer le 503 ni la décision',async()=>{
    const held=await fault('commit-database-busy',fn);const request=tracked(update(fn,volumes(5,4),{status:503}));
    await finalizing(async()=>{
      const phase=await held.wait('paused');const response=await finish(request);
      assert.equal(response.headers['x-serverless-mutation-committed'],'true');
      assert.equal(response.headers['x-serverless-operation-id'],phase.operation_id);
      assert.equal(response.headers['x-serverless-function-id'],fn.id);assert.match(response.data.error,/enregistrée/);
      const evidence=await remote('audit-failure',fn,[response.headers['x-request-id']]);
      assert.equal(evidence.audit_unavailable,1);held.events.push({event:'audit-failure-confirmed',...evidence});
    },()=>held.release(),'busy_guard_release');
    await healthy();assert.equal((await current(fn)).config.storage.cache.quota_mib,4);
    assert.equal((await remote('inspect',fn)).operation,null);
  });
  await check('Publication ZIP : décision commune, confirmation perdue conservant la publication et rollback gardant les ressources',async()=>{
    work=await mkdtemp(path.join(root,'.local/storage-publication-'));
    await cp(path.join(root,'qualification/src'),path.join(work,'src'),{recursive:true});
    await cp(path.join(root,'qualification/package.json'),path.join(work,'package.json'));
    await writeFile(path.join(work,'src/storage-version.json'),JSON.stringify({revision:'A'}));
    const invokeToken=(await token(['read'])).token;
    const manifest={service:'storage-publication',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'src/handlers.echo'}},package:{patterns:['!**','src/**','package.json']}};
    await writeFile(path.join(work,'serverless.yml'),JSON.stringify(manifest));
    await run('python3',['-B','-m','adapter','package','--config',path.join(work,'serverless.yml')],{cwd:root});
    const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));
    const bytes=await readFile(path.join(work,'.serverless-p2',descriptor.artifacts.probe.file));
    const before=await current(fn);
    const candidate=await object(`/api/functions/${fn.id}/deployments`,{method:'POST',status:201,headers:{'If-Match':String(before.updated_at)},
      body:{config:{...before.config,storage:volumes(6,3)}}});
    const published=await object(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes});assert.equal(published.state,'published');
    let row=await current(fn),actual=await remote('inspect',fn);
    assert.equal(row.active_revision_id,null);assert.equal(published.code_changed,true);assert.equal(actual.storage.volumes.data.quota_bytes,6*1024**2);
    await invokeCode(fn,published,invokeToken,true);await promoteCode(fn,published);await invokeCode(fn,published,invokeToken);row=await current(fn);
    assert.equal(actual.operation,null);
    const next=await object(`/api/functions/${fn.id}/deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},
      body:{config:{...row.config,storage:volumes(7,3)}}});
    const held=await fault('commit',fn);
    const upload=tracked(call(`/api/deployments/${next.id}/artifact`,{method:'PUT',bytes,status:503}));
    await finalizing(async()=>{
      const phase=await held.wait('paused');const response=await finish(upload);
      assert.equal(response.headers['x-serverless-mutation-committed'],'true');
      assert.equal(response.headers['x-serverless-operation-id'],phase.operation_id);
      const candidateState=await object(`/api/deployments/${next.id}`);
      assert.equal(candidateState.state,'published');assert(candidateState.revision_id);
      assert.equal(candidateState.code_changed,false);assert.equal(candidateState.code_hash,published.code_hash);assert.equal(candidateState.revision_id,published.revision_id);
      row=await current(fn);assert.equal(row.active_revision_id,published.revision_id);publicationEvidence.push({scenario:'quota-commit-with-duplicate-code',candidate_id:next.id,canonical_revision_id:published.revision_id,code_hash:published.code_hash,operation_id:phase.operation_id});
    },()=>held.release(),'zip_commit_guard_release');
    await healthy();actual=await remote('inspect',fn);const receipt=actual.receipt.operation_id;
    assert.equal(actual.operation,null);assert.equal(actual.storage.volumes.data.quota_bytes,7*1024**2);
    await invokeCode(fn,published,invokeToken);
    await writeFile(path.join(work,'src/storage-version.json'),JSON.stringify({revision:'B'}));await run('python3',['-B','-m','adapter','package','--config',path.join(work,'serverless.yml')],{cwd:root});const nextDescriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8')),nextBytes=await readFile(path.join(work,'.serverless-p2',nextDescriptor.artifacts.probe.file));
    row=await current(fn);const pilotCandidate=await object(`/api/functions/${fn.id}/deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{config:row.config}});const pilot=await object(`/api/deployments/${pilotCandidate.id}/artifact`,{method:'PUT',bytes:nextBytes});assert.equal(pilot.code_changed,true);assert.notEqual(pilot.code_hash,published.code_hash);assert.equal((await current(fn)).active_revision_id,published.revision_id);await invokeCode(fn,published,invokeToken);await invokeCode(fn,pilot,invokeToken,true);await promoteCode(fn,pilot);await invokeCode(fn,pilot,invokeToken);row=await current(fn);
    await call(`/api/functions/${fn.id}/rollback`,{method:'POST',headers:{'If-Match':String(row.updated_at)},body:{revision_id:published.revision_id}});
    actual=await remote('inspect',fn);assert.equal(actual.receipt.operation_id,receipt);
    row=await current(fn);assert.equal(row.active_revision_id,published.revision_id);assert.equal(row.config.storage.data.quota_mib,7);await invokeCode(fn,published,invokeToken);assert.equal(invocations.length,7);publicationEvidence.push({scenario:'distinct-code-promotion-and-legacy-rollback',stable_hash:published.code_hash,pilot_hash:pilot.code_hash,storage_operation_id:receipt});
    assert.equal(JSON.parse((await remote('read',fn)).result).bytes,1310720);
  });
  await check('Suppression HTTPS : archive réelle conservant les données et l’allocation',async()=>{
    await call(`/api/functions/${fn.id}`,{method:'DELETE'});await call(`/api/functions/${fn.id}`,{status:404});
    const actual=await remote('inspect',fn);assert.equal(actual.storage.state,'archived');assert.equal(actual.operation,null);
    assert.equal(actual.storage.volumes.data.quota_bytes,7*1024**2);assert.equal(actual.storage.volumes.data.enabled,false);
    assert.equal(actual.storage.leases,0);assert(Object.values(actual.storage.volumes).every(v=>v.phase==='unmounted'));
    assert.equal(actual.retained_files.data.sha256,expectedDataHash);assert.equal(actual.retained_files.data.bytes,1310720);
    assert.equal(actual.retained_files.cache.sha256,createHash('sha256').update('cached').digest('hex'));
  });
  completed=true;
  }
}catch(error){primaryFailure=error;}finally{
  for(const held of faults){
    try{if(!held.ended&&!held.child.stdin.writableEnded)held.child.stdin.end('resume\n');
      if(held.expectedTermination)assert.notEqual(await held.done,0);else assert.equal(await held.done,0);held.validateTransport();}
    catch(error){cleanupErrors.push('fault:'+error.name);}
  }
  if(needsStart){try{await restoreControl();}catch(error){cleanupErrors.push('control_restart:'+error.name);}}
  const pendingResults=await Promise.all(pending);
  if(session?.authenticated&&service){
    try{
      await healthy();
      const rows=await object(`/api/services/${service.id}/functions?limit=100`);
      for(const fn of rows.items)if(!functions.some(f=>f.id===fn.id))functions.push(fn);
    }catch(error){cleanupErrors.push('function_inventory:'+error.name);}
    for(const fn of functions){
      try{
        await remote('cleanup-clients',fn);
        const response=await admin.get(`/api/functions/${fn.id}`);
        if(response.status()===200)await call(`/api/functions/${fn.id}`,{method:'DELETE'});
        else assert.equal(response.status(),404);
        storageArchives.push(await purgeArchive(fn));
      }catch(error){cleanupErrors.push('function:'+fn.id+':'+error.name);}
    }
    for(const credential of tokens){try{await call(`/api/tokens/${credential.id}/revoke`,{method:'POST'});}catch(error){cleanupErrors.push('token:'+error.name);}}
    try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push('service:'+error.name);}
  }
  if(namespace){try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push('namespace:'+error.name);}}
  if(work){try{await rm(work,{recursive:true,force:true});}catch(error){cleanupErrors.push('workspace:'+error.name);finalizationFailures.push({scope:'workspace',error:diagnostic(error)});}}
  let finalHealth=null;
  try{finalHealth=await remote('health');assert.equal(finalHealth.allocated_bytes,0);assert.equal(finalHealth.leases,0);assert.equal(finalHealth.pending_functions,0);assert.equal(finalHealth.mounted_or_reserved,0);}
  catch(error){cleanupErrors.push('health:'+error.name);}
  for(const [scope,context]of [['admin_dispose',admin],['caller_dispose',caller]]){
    try{await context.dispose();}catch(error){cleanupErrors.push(scope+':'+error.name);finalizationFailures.push({scope,error:diagnostic(error)});}
  }
  try{await writeFile(report,JSON.stringify({completed:completed&&!primaryFailure&&!cleanupErrors.length&&!finalizationFailures.length,cleanup:!cleanupErrors.length&&!finalizationFailures.length,
    failed:Number(!completed||Boolean(primaryFailure)||Boolean(cleanupErrors.length)||Boolean(finalizationFailures.length)),skipped:0,checks,cleanup_errors:cleanupErrors,functions:functions.map(f=>f.id),
    namespace_id:namespace?.id,service_id:service?.id,requests:requestOutcomes,invocations,publication_evidence:publicationEvidence,
    failure:primaryFailure?diagnostic(primaryFailure):null,finalization_failures:finalizationFailures,
    scope:diagnosticInterruption?'guard-interruption-diagnostic':'function-storage',functional_groups:diagnosticInterruption?0:checks.filter(v=>v.status==='passed').length,diagnostic_observations:diagnosticObservations,
    pending_request_errors:pendingResults.filter(v=>v.error).map(v=>diagnostic(v.error)),
    storage_archives:storageArchives,faults:faults.map(f=>({mode:f.mode,function_id:f.functionId,expected_termination:f.expectedTermination,exit_code:f.exitCode,events:f.events,transport:f.transport()})),final_health:finalHealth},null,2)+'\n');}
  catch(error){finalizationFailures.push({scope:'report_save',error:diagnostic(error)});console.error(JSON.stringify({event:'report-save-failed',error:diagnostic(error),primary:primaryFailure?diagnostic(primaryFailure):null}));if(!primaryFailure)primaryFailure=error;}
  if(primaryFailure)throw primaryFailure;
  assert.deepEqual(cleanupErrors,[],'Nettoyage de campagne incomplet');assert.deepEqual(finalizationFailures,[],'Finalisation de campagne incomplète');
}
console.log(JSON.stringify({completed:true,passed:checks.length,cleanup:true,failed:0,skipped:0}));
