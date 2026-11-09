// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md#deux-cycles-réels
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,rename} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),root=new URL('../',import.meta.url),run=promisify(execFile);
const prefix='version-duplicate-recovery-'+randomUUID().slice(0,8),report=new URL('function-version-duplicate-recovery.json',out);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/function-version-duplicate-recovery-operator.py';
const checks=[],evidence=[],cleanupErrors=[],requestJoinErrors=[],pending=[],gates=[],secret='duplicate-version-private-'+randomUUID();
let admin,caller,session,namespace,service,fn,work,credential,stable,completed=false,cleanup=false,counter=0,namespaceCreationAttempted=false,serviceCreationAttempted=false,functionCreationAttempted=false,tokenCreationAttempted=false;
async function save(){const p=new URL('function-version-duplicate-recovery.pending',out);await writeFile(p,JSON.stringify({target:base,prefix,completed:completed&&cleanup,
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
async function bundle(){
  const folder=new URL('stable-code/',work);await mkdir(folder);
  await cp(new URL('../qualification/artifacts/validator-observation.mjs',import.meta.url),new URL('validator-observation.mjs',folder));
  await writeFile(new URL('validation-mode.json',folder),JSON.stringify({mode:'success'}));
  const manifest=new URL('serverless.yml',folder);await writeFile(manifest,JSON.stringify({service:'duplicate-recovery',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'validator-observation.handler'}},package:{patterns:['!**','validator-observation.mjs','validation-mode.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',manifest.pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',folder),'utf8'));
  return {bytes:await readFile(new URL('.serverless-p2/'+descriptor.artifacts.probe.file,folder)),handler:'validator-observation.handler'};
}
async function invoke(){
  const response=await caller.get(base+`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':credential.token}}).catch(()=>{throw new Error('https_invocation_failed');});
  assert.equal(response.status(),200);const value=await response.json();assert.equal(value.mode,'success');assert.equal(value.public_value,'preserved-public');
  assert.equal(value.secret_sha256,createHash('sha256').update(secret).digest('hex'));counter++;assert.equal(value.data_count,counter);assert.equal(value.cache_count,counter);
  assert.equal(response.headers()['x-serverless-code-hash'],stable.code_hash);
  evidence.push({invocation_id:response.headers()['x-serverless-request-id'],code_hash:stable.code_hash,counter});
  await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instance_not_stopped');
}
function unitsFinished(states){return Object.entries(states).every(([kind,state])=>state.ActiveState==='inactive'&&(kind==='timer'?state.MainPID===undefined||state.MainPID==='0':state.MainPID==='0'||state.MainPID===undefined&&state.LoadState==='not-found'));}
async function fault(candidate,kind){
  const unit='serverless-restore-duplicate-code-'+randomUUID().replaceAll('-','');
  const child=spawn('ssh',[...ssh,'python3','-B',helper,'fault',fn.id,namespace.id,candidate.id,kind,unit],{stdio:['pipe','pipe','pipe']});
  const events=[],errors=[];let ended=false,exitCode=null;const lines=createInterface({input:child.stdout});
  lines.on('line',line=>{try{events.push(JSON.parse(line));}catch{errors.push('invalid_helper_event');}});child.stderr.on('data',()=>{});child.stdin.on('error',()=>errors.push('helper_input_failed'));
  const done=new Promise(resolve=>{child.on('close',code=>{ended=true;exitCode=code;resolve(code);});child.on('error',()=>{ended=true;exitCode=-1;errors.push('helper_spawn_failed');resolve(-1);});});
  const held={unit,restored:false,killed:false,async wait(name){return until(()=>{assert(!errors.length,'helper_stream_failed');const event=events.find(v=>v.event===name);assert(event||!ended,'helper_ended_before_'+name);return event;},'missing_helper_event_'+name,20000);},
    async kill(){assert(!ended);held.killed=true;child.stdin.end('kill-helper\n');const sent=await held.wait('helper-sigkill'),terminal=await held.wait('helper-terminated');assert(terminal.signaled&&terminal.signal===9);assert.equal(terminal.pid,sent.pid);assert.equal(terminal.birth,sent.birth);await until(()=>ended,'helper_sigkill_not_observed',15000);assert.equal(await done,1);},
    async finish(trigger){
      if(held.restored)return;
      const value=await until(async()=>{const value=await remote('evidence',[unit]);return value.restored?.completed?value:false;},'restoration_receipt_missing',150000);
      assert.equal(value.restored.trigger,trigger);assert.equal(value.restored.permission.previous_mode,0);assert.equal(value.restored.permission.mode,0o700);
      const active=events.find(v=>v.event==='fault-active');assert(active);assert.deepEqual(value.restored.permission.identity,active.artifact_identity);
      const terminal=await until(async()=>{const v=await remote('evidence',[unit]);return unitsFinished(v.states)?v:false;},'guard_units_not_terminal',30000);
      if(!held.killed){await until(()=>ended,'helper_not_terminal',15000);assert.equal(await done,0);}
      const death=events.find(v=>v.event==='helper-terminated');assert(death);assert.equal(death.pid,terminal.identity.helper_pid);assert.equal(death.birth,terminal.identity.helper_birth);
      if(held.killed)assert(death.signaled&&death.signal===9);else assert(!death.signaled&&death.exit_code===0);
      assert(!errors.length);held.restored=true;evidence.push({guard:{unit,kind,restored:value.restored,states:terminal.states,helper_exit:exitCode,helper_sigkill:events.find(v=>v.event==='helper-sigkill')??null,helper_termination:events.find(v=>v.event==='helper-terminated')??null,identity:terminal.identity}});
    },
    async release(){
      if(held.restored)return;
      if(!ended&&!child.stdin.writableEnded){child.stdin.end('release\n');await until(()=>ended,'fault_helper_not_terminal',150000);await done;}
      const v=await remote('release',[unit]);assert(v.restored?.completed);
      assert(unitsFinished(v.states));held.restored=true;evidence.push({fallback_recovery:{unit,restored:v.restored,states:v.states}});
    },async normal(){assert(!ended);child.stdin.end('release\n');await held.finish('explicit');}};
  gates.push(held);await held.wait('fault-active');return held;
}
async function refusedBeforeAdmission(candidate,normal){
  let response=await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:normal.bytes,status:[429,503],meta:true});
  const refusals=[{status:response.status,error:response.body.error,retry_after:response.headers['retry-after']??null}];
  if(response.status===429){
    assert.equal(response.headers['retry-after'],'5');const unchanged=await remote('inspect',[candidate.id]);assert.equal(unchanged.candidate.state,'prepared');assert.equal(unchanged.candidate.reserved_bytes,0);assert(!unchanged.paths[candidate.id].exists);
    await new Promise(resolve=>setTimeout(resolve,5000));
    response=await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:normal.bytes,status:503,meta:true});refusals.push({status:response.status,error:response.body.error,explicit_retry_after_known_refusal:true});
  }
  assert.equal(response.body.error,'Un nettoyage de déploiement doit être repris.');
  const untouched=await remote('inspect',[candidate.id]);assert.equal(untouched.candidate.state,'prepared');assert.equal(untouched.candidate.reserved_bytes,0);assert.equal(untouched.candidate.validation,null);assert(!untouched.paths[candidate.id].exists);
  await call(`/api/deployments/${candidate.id}`,{method:'DELETE'});evidence.push({refused_candidate_id:candidate.id,refusals,untouched});
}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});caller=await request.newContext({timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'real_sso_required');assert(!await exactNamed('/api/namespaces',prefix),'namespace_collision');namespaceCreationAttempted=true;
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
  serviceCreationAttempted=true;service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'duplicate-code-recovery'}});await save();
  functionCreationAttempted=true;fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'retained-canonical-code',
    config:{handler:'validator-observation.handler',cpu:.05,memory_mib:128,timeout_seconds:20,idle_seconds:0,min_instances:0,max_instances:1,storage:{concurrency:'shared',data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},
    configuration:{environment:{VALIDATOR_NAME_PUBLIC:'preserved-public'},secrets:{VALIDATOR_NAME_SECRET:secret}}}});await save();
  tokenCreationAttempted=true;credential=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-retained-canonical-code',rights:['read'],function_ids:[fn.id]}});
  work=new URL((await mkdtemp(new URL('version-duplicate-recovery-',out).pathname))+'/','file:');const normal=await bundle();
  stable=await upload(await prepare(normal.handler),normal);await call(`/api/functions/${fn.id}/versions/${stable.code_hash}/promote`,{method:'POST',headers:{'If-Match':String((await current()).updated_at)}});await invoke();
  const originalFunction=await current(),originalServices=await remote('preflight');
  for(const kind of ['normal','restart']){
    let held,duplicate,retained,original;
    await check(kind==='normal'?'Doublon publié200 sous EACCES avec responsabilité conservée':'Commit du doublon conservé après SIGKILL du contrôle',async()=>{
      original=await remote('preflight');duplicate=await prepare(normal.handler);const rejected=await prepare(normal.handler);
      const task=tracked(upload(duplicate,normal));await until(async()=>(await call(`/api/deployments/${duplicate.id}`)).state==='validating','duplicate_not_validating');
      held=await fault(duplicate,kind);const published=await observed(task);
      assert.equal(published.state,'published');assert.equal(published.code_changed,false);assert.equal(published.code_hash,stable.code_hash);assert.equal(published.revision_id,stable.revision_id);assert(published.validation.valid&&published.validation.container_removed);
      retained=await remote('inspect',[duplicate.id]);assert.equal(retained.candidate.state,'published');assert(retained.candidate.reserved_bytes>0&&retained.candidate.configuration_empty);assert.equal(retained.candidate.revision_id,stable.revision_id);
      const active=await held.wait('fault-active');assert.deepEqual(retained.paths[duplicate.id].identity,active.artifact_identity);
      assert.deepEqual(retained.paths[duplicate.id].files,active.before.paths[duplicate.id].files);
      assert.equal(retained.candidate.reserved_bytes,active.before.candidate.reserved_bytes);
      assert.deepEqual(retained.paths[stable.revision_id],active.before.paths[stable.revision_id]);
      assert.equal(retained.paths[stable.revision_id].files['archive.zip'],createHash('sha256').update(normal.bytes).digest('hex'));
      assert.equal(retained.paths[duplicate.id].mode,0);assert(retained.paths[duplicate.id].files['archive.zip']);assert.equal(retained.revisions.length,1);assert.equal(retained.versions.length,1);assert(!retained.validators.length&&!retained.channels.length);
      assert.deepEqual(await current(),originalFunction);assert.equal(retained.function.active_revision_id,stable.revision_id);
      const health=await call('/healthz',{status:503});assert.equal(health.error,'Le nettoyage des artefacts doit être repris.');await refusedBeforeAdmission(rejected,normal);
      if(kind==='normal')await invoke();else{
        const cut=await remote('interrupt',[held.unit]);assert.equal(cut.interrupted.exit_code,137);assert.equal(cut.interrupted.candidate.candidate.state,'published');assert(cut.interrupted.candidate.candidate.reserved_bytes>0);evidence.push({interruption:cut});
        await held.kill();
      }
      evidence.push({fault:kind,duplicate_id:duplicate.id,published:{id:published.id,revision_id:published.revision_id,code_hash:published.code_hash,code_changed:published.code_changed},retained});
    });
    await check(kind==='normal'?'Restitution explicite et maintenance sans redémarrage':'Garde indépendante, reprise du candidat publié et nouvelle déduplication',async()=>{
      if(kind==='normal')await held.normal();else await held.finish('independent');
      const cleaned=await until(async()=>{const v=await remote('inspect',[duplicate.id]);return v.candidate.reserved_bytes===0&&!v.paths[duplicate.id].exists?v:false;},'reused_artifact_not_cleaned');
      assert.equal(cleaned.candidate.state,'published');assert.equal(cleaned.candidate.error_code,null);assert.equal(cleaned.candidate.code_hash,stable.code_hash);assert.equal(cleaned.candidate.revision_id,stable.revision_id);
      assert.deepEqual(cleaned.paths[stable.revision_id],retained.paths[stable.revision_id]);assert.deepEqual(cleaned.function,retained.function);assert.deepEqual(await current(),originalFunction);
      const after=await remote('preflight');assert.deepEqual(after.official_sha256,original.official_sha256);assert.deepEqual(after.services[1],original.services[1]);assert.equal(after.services[0].id,original.services[0].id);assert.equal(after.services[0].image,original.services[0].image);assert.deepEqual(after.services[0].configuration,original.services[0].configuration);
      if(kind==='normal')assert.deepEqual(after.services,original.services);else assert.notEqual(after.services[0].started_at,original.services[0].started_at);
      await invoke();
      if(kind==='restart'){
        const candidate=await prepare(normal.handler),result=await upload(candidate,normal);assert.equal(result.code_changed,false);assert.equal(result.revision_id,stable.revision_id);assert.equal(result.code_hash,stable.code_hash);
        const native=await remote('inspect',[candidate.id]);assert.equal(native.candidate.reserved_bytes,0);assert(!native.paths[candidate.id].exists);await invoke();evidence.push({post_restart_duplicate:{id:result.id,revision_id:result.revision_id,code_hash:result.code_hash},native});
      }
      assert.equal((await call(`/api/functions/${fn.id}/versions`)).total,1);evidence.push({recovered:kind,duplicate_id:duplicate.id,cleaned,services:after.services});
    });
  }
  assert.deepEqual((await remote('preflight')).services[1],originalServices.services[1]);completed=true;
}finally{
  for(const gate of gates)try{await gate.release();}catch(error){cleanupErrors.push({step:'fault-restore',unit:gate.unit,error:error.name});}
  for(const task of pending)try{await observed(task);}catch(error){requestJoinErrors.push({error:error.name});}
  if(admin&&session?.authenticated&&gates.every(g=>g.restored)){
    if(namespaceCreationAttempted)try{
      namespace??=await exactNamed('/api/namespaces',prefix);assert(namespace,'namespace_creation_outcome_unknown');
      if(namespace){service??=await exactNamed(`/api/namespaces/${namespace.id}/services`,'duplicate-code-recovery');
        if(serviceCreationAttempted)assert(service,'service_creation_outcome_unknown');
        if(service)fn??=await exactNamed(`/api/services/${service.id}/functions`,'retained-canonical-code');
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
      const tokens=await call(`/api/services/${service.id}/tokens`);if(tokenCreationAttempted)assert(tokens.items.some(v=>v.name==='invoke-retained-canonical-code'),'token_creation_outcome_unknown');for(const token of tokens.items)if(!token.revoked_at)await call(`/api/tokens/${token.id}/revoke`,{method:'POST'});
    }catch(error){cleanupErrors.push({step:'token',error:error.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service',error:error.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace',error:error.name});}
  }
  if(gates.some(g=>!g.restored))cleanupErrors.push({step:'guard-not-confirmed'});
  if(work)await rm(work,{recursive:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert(cleanup,'campaign_cleanup_incomplete');
}
assert(completed&&!requestJoinErrors.length,'campaign_not_complete');
