// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#scénario-et-assertions
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,rename} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),root=new URL('../',import.meta.url),run=promisify(execFile);
const prefix='version-upload-capacity-'+randomUUID().slice(0,8),report=new URL('function-version-upload-capacity.json',out);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/function-version-upload-capacity-inspect.py';
const checks=[],evidence=[],cleanupErrors=[],requestJoinErrors=[],pending=[],secret='capacity-version-private-'+randomUUID();
let admin,caller,session,namespace,service,fn,work,credential,stable,pilot,completed=false,cleanup=false,counter=0,namespaceCreationAttempted=false,serviceCreationAttempted=false,functionCreationAttempted=false,tokenCreationAttempted=false;
async function save(){const p=new URL('function-version-upload-capacity.pending',out);await writeFile(p,JSON.stringify({target:base,prefix,completed:completed&&cleanup,
  cleanup,cleanup_errors:cleanupErrors,request_join_errors:requestJoinErrors,skipped:0,checks,evidence,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[]},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name,message:error.code??'scenario_assertion_failed'});throw error;}finally{await save();}}
async function call(path,{meta=false,method='GET',body,bytes,status=200,headers={},token}={}){
  const r=await (token?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}}).catch(()=>{throw new Error('https_request_failed');});
  const text=await r.text();assert(!text.includes(secret),'secret_exposed');assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);return meta?{body:JSON.parse(text),status:r.status(),headers:r.headers()}:JSON.parse(text);
}
async function exactNamed(path,name){
  const found=[];
  for(let offset=0;offset<=10000;offset+=100){
    const page=await call(`${path}?limit=100&offset=${offset}`);found.push(...page.items.filter(v=>v.name===name));
    if(page.items.length<100){assert(found.length<=1,'ambiguous_owned_name');return found[0];}
  }
  throw new Error('owned_inventory_not_exhausted');
}
async function until(action,message,timeout=120000){const end=Date.now()+timeout;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(r=>setTimeout(r,120));}assert.fail(message);}
async function remote(mode,extra=[]){const r=await run('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...extra],{timeout:35000,maxBuffer:2*1024*1024});return JSON.parse(r.stdout.trim().split('\n').at(-1));}
const current=()=>call(`/api/functions/${fn.id}`);
async function prepare(handler){const row=await current();return call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler}});}
function tracked(promise){const safe=promise.then(value=>({value}),error=>({error}));pending.push(safe);return safe;}
async function observed(promise){const r=await promise;if(r.error)throw r.error;return r.value;}
async function upload(candidate,bundle,status=200){return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:bundle.bytes,status});}
async function ordinaryBundle(){
  const folder=new URL('pilot/',work);await mkdir(folder);await cp(new URL('../qualification/artifacts/function-versions.cjs',import.meta.url),new URL('function-versions.cjs',folder));
  await writeFile(new URL('version-marker.json',folder),JSON.stringify({value:'pilot',validation_delay_ms:12000}));
  const manifest=new URL('serverless.yml',folder);await writeFile(manifest,JSON.stringify({service:'upload-capacity',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'function-versions.primary'}},package:{patterns:['!**','function-versions.cjs','version-marker.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',manifest.pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',folder),'utf8'));
  return {bytes:await readFile(new URL('.serverless-p2/'+descriptor.artifacts.probe.file,folder)),handler:'function-versions.primary'};
}
async function invoke(hash,marker){const r=await caller.get(base+`/invoke/${fn.id}${hash?'@'+hash:''}`,{headers:{'X-Serverless-Token':credential.token,Authorization:'Bearer capacity-business'}}).catch(()=>{throw new Error('https_invocation_failed');});assert.equal(r.status(),200);
  const value=await r.json();assert.equal(value.marker,marker);assert.equal(value.common,'preserved-common');assert.equal(value.local,'preserved-local');assert(value.authorization_present);
  assert.equal(value.secret_sha256,createHash('sha256').update(secret).digest('hex'));counter++;assert.equal(value.counter,counter);assert.equal(value.cacheCounter,counter);
  const actual=r.headers()['x-serverless-code-hash'];assert.equal(actual,hash??stable.code_hash);
  evidence.push({invocation_id:r.headers()['x-serverless-request-id'],code_hash:actual,counter,marker});
  await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instance_not_stopped');
}

function serialHistory(value,expected,observedIds){
  const live=new Set(),created=new Set();let peak=0;
  for(const event of value.history.events){
    if(event.action==='create'){assert(!created.has(event.id));created.add(event.id);live.add(event.id);peak=Math.max(peak,live.size);}
    else{assert(live.delete(event.id),'destroy_without_create');}
  }
  assert.equal(created.size,expected);assert.equal(live.size,0);assert.equal(peak,1);
  if(observedIds)assert.deepEqual([...created].sort(),[...observedIds].sort());
  return {events:value.history,peak_live:peak,created:[...created]};
}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});
  caller=await request.newContext({timeout:180000});session=await call('/api/session');assert(session.authenticated,'real_sso_required');
  assert(!await exactNamed('/api/namespaces',prefix),'namespace_collision');namespaceCreationAttempted=true;
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
  serviceCreationAttempted=true;service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'upload-capacity'}});await save();
  functionCreationAttempted=true;fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'stable-and-pilot-code',
    config:{handler:'function-versions.primary',cpu:.05,memory_mib:128,timeout_seconds:20,idle_seconds:0,min_instances:0,max_instances:1,storage:{concurrency:'shared',data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},
    configuration:{environment:{VERSIONS_COMMON:'preserved-common',VERSIONS_LOCAL:'preserved-local',VERSIONS_PERSIST:'yes'},secrets:{VERSIONS_SECRET:secret}}}});await save();
  tokenCreationAttempted=true;credential=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-stable-and-pilot',rights:['read'],function_ids:[fn.id]}});
  work=new URL((await mkdtemp(new URL('version-upload-capacity-',out).pathname))+'/','file:');
  const normal=await ordinaryBundle();await writeFile(new URL('pilot/version-marker.json',work),JSON.stringify({value:'stable'}));
  await run('python3',['-B','-m','adapter','package','--config',new URL('pilot/serverless.yml',work).pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('pilot/.serverless-p2/deployment.json',work),'utf8'));
  stable=await upload(await prepare(normal.handler),{bytes:await readFile(new URL('pilot/.serverless-p2/'+descriptor.artifacts.probe.file,work))});
  await call(`/api/functions/${fn.id}/versions/${stable.code_hash}/promote`,{method:'POST',headers:{'If-Match':String((await current()).updated_at)}});
  await invoke(undefined,'stable');
  const slow=await publicationArchive(work.pathname,'capacity-blocked-import','storage-validation-delay.handler',['storage-validation-delay.mjs']);
  const candidates=[];for(let i=0;i<5;i++)candidates.push(await prepare(i===0?slow.handler:normal.handler));
  const baseline=await remote('preflight'),originalFunction=await current(),tasks=[],seenValidators=new Map();
  const admittedAt=performance.now();let full,refused,late,joined,final,history;
  function observe(value){for(const item of value.validators){const previous=seenValidators.get(item.id);if(previous)assert.equal(previous.candidate_id,item.candidate_id);else seenValidators.set(item.id,item);}}
  await check('Quatre uploads admis, cinquième429 avant réception',async()=>{
    for(let i=0;i<4;i++){
      tasks.push(tracked(upload(candidates[i],i===0?slow:normal,i===0?422:200)));
      await until(async()=>(await call(`/api/deployments/${candidates[i].id}`)).state==='validating','candidate_not_admitted');
    }
    full=await remote('observe-import');observe(full);
    for(const candidate of candidates.slice(0,4)){
      const actual=full.candidates.find(v=>v.id===candidate.id);assert.equal(actual.state,'validating');assert.equal(actual.reserved_bytes,baseline.reservation_bytes);
      assert(full.paths[candidate.id].archive&&full.paths[candidate.id].code);
    }
    assert.equal(full.counts.reserved_bytes,4*baseline.reservation_bytes);assert.equal(full.validators.length,1);
    assert.equal(full.validators[0].candidate_id,candidates[0].id);assert(full.validators[0].running&&full.validators[0].marker);
    refused=await call(`/api/deployments/${candidates[4].id}/artifact`,{method:'PUT',bytes:normal.bytes,status:429,meta:true});
    assert.equal(refused.body.error,'La capacité de publication est occupée.');assert.equal(refused.headers['retry-after'],'5');
    const after=await remote('inspect');observe(after);const untouched=after.candidates.find(v=>v.id===candidates[4].id);
    assert.equal(untouched.state,'prepared');assert.equal(untouched.reserved_bytes,0);assert.equal(untouched.validation,null);assert(!after.paths[untouched.id].exists);
    assert.deepEqual(after.function,baseline.function);evidence.push({admitted:full,refusal:{status:refused.status,error:refused.body.error,retry_after:refused.headers['retry-after']},after_refusal:after});
  });
  await check('Attente supérieure30s, validation sérialisée et convergence canonique',async()=>{
    await until(async()=>{
      const observationStarted=performance.now();const value=await remote('inspect');observe(value);const elapsed=observationStarted-admittedAt;
      if(!late&&elapsed>31000){
        const active=value.validators.map(v=>v.candidate_id);
        const waiting=value.candidates.filter(v=>v.state==='validating'&&!active.includes(v.id));
        assert.equal(value.validators.length,1);assert(waiting.length>0,'no_waiter_after_maintenance_period');
        assert(waiting.every(v=>v.reserved_bytes===baseline.reservation_bytes&&value.paths[v.id].code));
        late={observation_started_elapsed_ms:elapsed,observation_completed_elapsed_ms:performance.now()-admittedAt,snapshot:value};assert.deepEqual(value.function,baseline.function);
        const started=performance.now();await call('/healthz');late.health_request_ms=performance.now()-started;assert(late.health_request_ms<5000);
      }
      return candidates.slice(0,4).every(v=>['failed','published'].includes(value.candidates.find(c=>c.id===v.id).state))?value:false;
    },'queued_uploads_not_finished',120000);
    joined=[];for(const task of tasks)joined.push(await observed(task));assert(late,'late_waiter_not_observed');
    assert.equal(joined[0].error,'Le chargement du handler a échoué : validation_timeout');
    const published=joined.slice(1);pilot=published.find(v=>v.code_changed);assert(pilot,'canonical_creator_missing');
    assert.equal(published.filter(v=>v.code_changed===true).length,1);assert.equal(published.filter(v=>v.code_changed===false).length,2);
    for(const result of published){assert.equal(result.state,'published');assert.equal(result.code_hash,pilot.code_hash);assert.equal(result.revision_id,pilot.id);assert.equal(result.default_code_hash_at_publication,stable.code_hash);assert(result.validation.valid&&result.validation.container_removed);}
    assert.notEqual(pilot.code_hash,stable.code_hash);final=await remote('history',[baseline.observed_at_ns]);observe(final);
    assert.equal(seenValidators.size,4);assert.deepEqual([...seenValidators.values()].map(v=>v.candidate_id).sort(),candidates.slice(0,4).map(v=>v.id).sort());
    history=serialHistory(final,4,seenValidators.keys());assert.equal(final.counts.reserved_bytes,0);assert.equal(final.validators.length,0);assert.equal(final.channels.length,0);
    const failed=final.candidates.find(v=>v.id===candidates[0].id);assert.equal(failed.state,'failed');assert.equal(failed.validation.error,'validation_timeout');assert(failed.validation.container_removed);assert(!final.paths[failed.id].exists);
    for(const result of published)assert.equal(final.paths[result.id].exists,result.id===pilot.id);
    assert.deepEqual(final.function,baseline.function);assert.deepEqual(await current(),originalFunction);assert.equal((await call(`/api/functions/${fn.id}/versions`)).total,2);
    evidence.push({late_waiter:late,publications:published.map(v=>({id:v.id,revision_id:v.revision_id,code_hash:v.code_hash,code_changed:v.code_changed})),validators:[...seenValidators.values()],serialized:history,converged:final});
  });
  await check('Relance explicite du même cinquième candidat après libération',async()=>{
    const before=await remote('inspect');const result=await upload(candidates[4],normal);
    assert.equal(result.id,candidates[4].id);assert.equal(result.state,'published');assert.equal(result.code_changed,false);assert.equal(result.code_hash,pilot.code_hash);assert.equal(result.revision_id,pilot.revision_id);assert(result.validation.valid&&result.validation.container_removed);
    const after=await remote('history',[before.observed_at_ns]);assert.equal(after.counts.reserved_bytes,0);assert(!after.paths[result.id].exists&&!after.validators.length&&!after.channels.length);
    assert.deepEqual(after.function,baseline.function);evidence.push({explicit_retry:{id:result.id,revision_id:result.revision_id,code_hash:result.code_hash,code_changed:result.code_changed},serialized:serialHistory(after,1)});
  });
  await check('Cible stable, configuration et compteurs conservés avec pilote épinglé',async()=>{
    assert.deepEqual(await current(),originalFunction);await invoke(undefined,'stable');await invoke(pilot.code_hash,'pilot');await invoke(undefined,'stable');
    const after=await remote('preflight');assert.deepEqual(after.function,baseline.function);assert.deepEqual(after.services,baseline.services);assert.deepEqual(after.official_sha256,baseline.official_sha256);
    assert.equal((await call(`/api/functions/${fn.id}/versions`)).total,2);evidence.push({preserved:after});
  });
  completed=true;
}finally{
  for(const task of pending)try{await observed(task);}catch(error){requestJoinErrors.push({error:error.name});}
  if(admin&&session?.authenticated){
    if(namespaceCreationAttempted)try{
      namespace??=await exactNamed('/api/namespaces',prefix);assert(namespace,'namespace_creation_outcome_unknown');
      if(namespace){service??=await exactNamed(`/api/namespaces/${namespace.id}/services`,'upload-capacity');
        if(serviceCreationAttempted)assert(service,'service_creation_outcome_unknown');
        if(service)fn??=await exactNamed(`/api/services/${service.id}/functions`,'stable-and-pilot-code');
        if(functionCreationAttempted)assert(fn,'function_creation_outcome_unknown');}
    }catch(error){cleanupErrors.push({step:'owned-inventory',error:error.name});}
    if(fn)try{
      for(const candidate of (await call(`/api/functions/${fn.id}/deployments`)).items)if(candidate.state==='prepared')await call(`/api/deployments/${candidate.id}`,{method:'DELETE'});
      await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instance_retained_before_purge');
      await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'archive_operation_pending');
      const archived=await call(`/api/archives/${fn.id}`),operation=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archived.updated_at)},body:{operation_id:randomUUID(),confirm_name:archived.name}});
      await until(async()=>{const v=await call(`/api/storage-operations/${operation.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'purge_not_completed');
      const final=await call(`/api/archives/${fn.id}`);assert.equal(final.artifact_bytes,0);assert(final.purged_at&&!final.storage_operation);evidence.push({purged_function_id:fn.id,operation_id:operation.id});
    }catch(error){cleanupErrors.push({step:'function-purge',error:error.name,message:error.code??'scenario_assertion_failed'});}
    if(service)try{
      const tokens=await call(`/api/services/${service.id}/tokens`);if(tokenCreationAttempted)assert(tokens.items.some(v=>v.name==='invoke-stable-and-pilot'),'token_creation_outcome_unknown');for(const token of tokens.items)if(!token.revoked_at)await call(`/api/tokens/${token.id}/revoke`,{method:'POST'});
    }catch(error){cleanupErrors.push({step:'token',error:error.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service',error:error.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace',error:error.name});}
  }
  if(work)await rm(work,{recursive:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert(cleanup,'campaign_cleanup_incomplete');
}
assert(completed&&!requestJoinErrors.length,'campaign_not_complete');
