// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md#campagne-et-preuves
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,rename} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),root=new URL('../',import.meta.url),run=promisify(execFile);
const prefix='version-validation-'+randomUUID().slice(0,8),report=new URL('function-version-validation.json',out);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/function-version-validation-faults.py';
const checks=[],evidence=[],cleanupErrors=[],requestJoinErrors=[],pending=[],gates=[],secret='validation-version-private-'+randomUUID();
let admin,caller,session,namespace,service,fn,work,credential,stable,pilot,completed=false,cleanup=false,counter=0;
async function save(){const p=new URL('function-version-validation.pending',out);await writeFile(p,JSON.stringify({target:base,prefix,completed:completed&&cleanup,
  cleanup,cleanup_errors:cleanupErrors,request_join_errors:requestJoinErrors,skipped:0,checks,evidence,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[]},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name,message:error.message});throw error;}finally{await save();}}
async function call(path,{method='GET',body,bytes,status=200,headers={},token}={}){
  const r=await (token?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  const text=await r.text();assert(!text.includes(secret),'secret_exposed');assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);return JSON.parse(text);
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
  await writeFile(new URL('version-marker.json',folder),JSON.stringify({value:'pilot'}));
  const manifest=new URL('serverless.yml',folder);await writeFile(manifest,JSON.stringify({service:'validation-queue',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'function-versions.primary'}},package:{patterns:['!**','function-versions.cjs','version-marker.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',manifest.pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',folder),'utf8'));
  return {bytes:await readFile(new URL('.serverless-p2/'+descriptor.artifacts.probe.file,folder)),handler:'function-versions.primary'};
}
async function invoke(hash,marker){const r=await caller.get(base+`/invoke/${fn.id}${hash?'@'+hash:''}`,{headers:{'X-Serverless-Token':credential.token,Authorization:'Bearer validation-business'}});assert.equal(r.status(),200);
  const value=await r.json();assert.equal(value.marker,marker);assert.equal(value.common,'preserved-common');assert.equal(value.local,'preserved-local');assert(value.authorization_present);
  assert.equal(value.secret_sha256,createHash('sha256').update(secret).digest('hex'));counter++;assert.equal(value.counter,counter);assert.equal(value.cacheCounter,counter);
  const actual=r.headers()['x-serverless-code-hash'];assert.equal(actual,hash??stable.code_hash);
  evidence.push({invocation_id:r.headers()['x-serverless-request-id'],code_hash:actual,counter,marker});
  await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instance_not_stopped');
}
async function gate(first,second,kind,baseline){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,'fault',fn.id,namespace.id,first.id,second.id,kind],{stdio:['pipe','pipe','pipe']});
  const events=[],parseErrors=[];let ended=false,exitCode=null,stderr='';const lines=createInterface({input:child.stdout});
  lines.on('line',line=>{try{events.push(JSON.parse(line));}catch(error){parseErrors.push(error.name);}});child.stderr.on('data',chunk=>{stderr+=chunk;});child.stdin.on('error',error=>parseErrors.push(error.name));
  const done=new Promise(resolve=>{child.on('close',code=>{ended=true;exitCode=code;resolve(code);});child.on('error',error=>{parseErrors.push(error.name);ended=true;exitCode=-1;resolve(-1);});});
  const held={events,restored:false,killed:false,async wait(name){return until(()=>{assert(!parseErrors.length,'guard_stream_invalid');const value=events.find(e=>e.event===name);assert(value||!ended,'guard_ended_before_'+name);return value;},'guard_event_missing_'+name,35000);},
    async kill(){held.killed=true;assert(!ended,'helper_already_ended');child.stdin.end('kill-helper\n');await held.wait('helper-sigkill');await until(()=>ended,'helper_sigkill_not_observed',10000);assert.notEqual(await done,0);},
    async release(){
      if(held.restored)return;
      if(!ended&&!child.stdin.writableEnded)child.stdin.end('resume\n');
      await until(()=>ended,'helper_not_terminal',100000);await done;
      const armed=events.find(e=>e.event==='guard-armed');assert(armed,'independent_guard_missing');
      let restored=events.find(e=>e.event==='permission-restored');
      if(!restored)restored=await until(async()=>{const v=await remote('guard-evidence',[armed.unit]);return v.events.find(e=>e.docker_connected);},'independent_restore_missing',100000);
      const active=events.find(e=>e.event==='fault-active');assert(active,'fault_never_observed');
      assert.deepEqual(restored.identity,active.target.identity);assert.equal(restored.mode,active.target.mode);assert.equal(restored.uid,active.target.uid);assert.equal(restored.gid,active.target.gid);
      assert.equal(restored.kind,kind);assert.equal(restored.candidate_id,first.id);assert.equal(restored.previous_mode,0);assert.equal(restored.independent,held.killed);
      const socket=await remote('socket-status');assert.equal(socket.mode,baseline.mode);assert.deepEqual(socket.identity,baseline.identity);assert(socket.connection.connected);
      const units=await until(async()=>{const v=await remote('guard-evidence',[armed.unit]);return Object.values(v.unit_states).every(s=>['inactive','unknown'].includes(s))?v:false;},'guard_unit_retained');
      held.restored=true;evidence.push({permission_restored:restored,unit:armed.unit,unit_states:units.unit_states,helper_exit:exitCode,helper_sigkill:events.find(e=>e.event==='helper-sigkill')??null,stderr_sha256:createHash('sha256').update(stderr).digest('hex')});
      assert(held.killed||exitCode===0,'fault_helper_failed');assert(!parseErrors.length,'guard_stream_error');
    }};
  gates.push(held);await held.wait('fault-active');return held;
}

await mkdir(out,{recursive:true,mode:0o700});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});caller=await request.newContext({timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'real_sso_required');
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
  service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'validation-queue'}});await save();
  fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'retained-stable-code',
    config:{handler:'function-versions.primary',cpu:.05,memory_mib:128,timeout_seconds:5,idle_seconds:0,max_instances:1,storage:{concurrency:'shared',data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},
    configuration:{environment:{VERSIONS_COMMON:'preserved-common',VERSIONS_LOCAL:'preserved-local',VERSIONS_PERSIST:'yes'},secrets:{VERSIONS_SECRET:secret}}}});await save();
  credential=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-preserved-code',rights:['read'],function_ids:[fn.id]}});
  work=new URL((await mkdtemp(new URL('version-validation-',out).pathname))+'/','file:');const normal=await ordinaryBundle();
  // Stable uses the same original handler with a distinct real code marker.
  await writeFile(new URL('pilot/version-marker.json',work),JSON.stringify({value:'stable'}));
  await run('python3',['-B','-m','adapter','package','--config',new URL('pilot/serverless.yml',work).pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('pilot/.serverless-p2/deployment.json',work),'utf8'));
  const initial={handler:normal.handler,bytes:await readFile(new URL('pilot/.serverless-p2/'+descriptor.artifacts.probe.file,work))};
  stable=await upload(await prepare(initial.handler),initial);const before=await current();
  await call(`/api/functions/${fn.id}/versions/${stable.code_hash}/promote`,{method:'POST',headers:{'If-Match':String(before.updated_at)}});await invoke(undefined,'stable');
  evidence.push({prerequisite:'stable_published_promoted_invoked',code_hash:stable.code_hash,revision_id:stable.revision_id});
  const slow=await publicationArchive(work.pathname,'blocked-import','storage-validation-delay.handler',['storage-validation-delay.mjs']);
  for(const kind of ['socket','channel']){
    let held,first,second,baseline,originalFunction,retained;
    await check(kind==='socket'?'Conteneur non retiré : le second upload admis est refusé avant validation':'Canal refusé avec Docker accessible : aucun validateur du second upload',async()=>{
      const ready=await remote('preflight');baseline=ready.socket;originalFunction=await current();
      first=await prepare(slow.handler);second=await prepare(normal.handler);const third=await prepare(normal.handler);
      const a=tracked(upload(first,slow,kind==='socket'?422:503));
      await until(async()=>(await call(`/api/deployments/${first.id}`)).state==='validating','first_not_validating');
      const b=tracked(upload(second,normal,503));await until(async()=>(await call(`/api/deployments/${second.id}`)).state==='validating','second_not_admitted');
      held=await gate(first,second,kind,baseline);const active=await held.wait('fault-active');assert.equal(active.denied.errno,13);
      assert.equal(active.first.candidate.state,'validating');assert.equal(active.second.candidate.state,'validating');assert(active.second.code_present&&active.second.candidate.reserved_bytes>0);
      await observed(a);const refused=await observed(b);assert.equal(refused.error,'Un nettoyage de déploiement doit être repris avant validation.');
      const left=await remote('inspect',[first.id]),waiting=await remote('inspect',[second.id]);retained=left;
      assert.equal(left.candidate.state,'failed');assert.equal(waiting.candidate.state,'failed');assert.equal(waiting.candidate.error_code,'request_rejected');assert.equal(waiting.candidate.validation,null);
      assert.equal(waiting.candidate.reserved_bytes,0);assert(!waiting.code_present&&!waiting.archive_present&&!waiting.validators.length);
      assert(left.candidate.reserved_bytes>0&&left.code_present&&left.archive_present&&left.channels.length===1);
      if(kind==='socket'){assert.equal(left.candidate.validation.error,'cleanup_failed');assert.equal(left.candidate.validation.container_removed,false);assert.equal(left.global_validators.length,1);}
      else{assert.equal(left.candidate.validation,null);assert.equal(left.candidate.error_code,'deployment_failed');assert.equal(left.global_validators.length,0);assert.equal(left.channels[0].mode,0);}
      const rejected=await upload(third,normal,503);assert.equal(rejected.error,'Un nettoyage de déploiement doit être repris.');
      const untouched=await remote('inspect',[third.id]);assert.equal(untouched.candidate.state,'prepared');assert.equal(untouched.candidate.reserved_bytes,0);assert(!untouched.code_present&&!untouched.archive_present);
      await call(`/api/deployments/${third.id}`,{method:'DELETE'});assert.deepEqual(await current(),originalFunction);
      const history=await remote('history',[ready.observed_at_ns]);assert.equal(history.creates.length,1);assert.equal(history.creates[0].container_id,active.first.validators[0].id);
      evidence.push({fault:kind,first_id:first.id,second_id:second.id,third_id:third.id,active,retained:left,second:waiting,third_before_abandon:untouched,validation_creates:history});
      if(kind==='channel')await held.kill();
    });
    await check(kind==='socket'?'Restitution explicite, nettoyage normal puis nouveau pilote invocable':'SIGKILL du helper, restitution indépendante et réupload pilote dédupliqué',async()=>{
      await held.release();
      const cleaned=await until(async()=>{const value=await remote('inspect',[first.id]);return !value.global_validators.length&&!value.channels.length&&value.candidate.reserved_bytes===0&&!value.code_present&&!value.archive_present?value:false;},'normal_reconciliation_not_completed');
      assert.equal(cleaned.function.active_revision_id,retained.function.active_revision_id);assert.equal(cleaned.function.configuration_sha256,retained.function.configuration_sha256);
      assert.deepEqual(await current(),originalFunction);await invoke(undefined,'stable');
      const candidate=await prepare(normal.handler),published=await upload(candidate,normal);assert.equal(published.state,'published');assert(published.validation.valid&&published.validation.container_removed);
      assert.equal(published.default_code_hash_at_publication,stable.code_hash);
      if(pilot){assert.equal(published.code_hash,pilot.code_hash);assert.equal(published.revision_id,pilot.revision_id);assert.equal(published.code_changed,false);}else{pilot=published;assert(pilot.code_changed);}
      assert.deepEqual(await current(),originalFunction);await invoke(published.code_hash,'pilot');assert.equal((await call(`/api/functions/${fn.id}/versions`)).total,2);
      const waiting=await remote('inspect',[second.id]);assert.equal(waiting.candidate.reserved_bytes,0);assert(!waiting.code_present&&!waiting.archive_present);
      evidence.push({recovered:kind,first_id:first.id,cleanup:cleaned,publication_id:published.id,code_hash:published.code_hash,revision_id:published.revision_id,code_changed:published.code_changed});
    });
  }
  completed=true;
}finally{
  for(const held of gates)try{await held.release();}catch(error){cleanupErrors.push({step:'permission-restore',error:error.name});}
  for(const task of pending)try{await observed(task);}catch(error){requestJoinErrors.push({error:error.name});}
  if(admin&&session?.authenticated&&gates.every(g=>g.restored)){
    if(fn)try{
      await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instance_retained_before_purge');
      await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'archive_operation_pending');
      const archived=await call(`/api/archives/${fn.id}`),operation=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archived.updated_at)},body:{operation_id:randomUUID(),confirm_name:archived.name}});
      await until(async()=>{const v=await call(`/api/storage-operations/${operation.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'purge_not_completed');
      const final=await call(`/api/archives/${fn.id}`);assert.equal(final.artifact_bytes,0);assert(final.purged_at&&!final.storage_operation);evidence.push({purged_function_id:fn.id,operation_id:operation.id});
    }catch(error){cleanupErrors.push({step:'function-purge',error:error.name});}
    if(credential)try{await call(`/api/tokens/${credential.id}/revoke`,{method:'POST'});}catch(error){cleanupErrors.push({step:'token',error:error.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service',error:error.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace',error:error.name});}
  }else if(fn)cleanupErrors.push({step:'permission-not-confirmed'});
  if(work)await rm(work,{recursive:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert(cleanup,'campaign_cleanup_incomplete');
}
assert(completed&&!requestJoinErrors.length,'campaign_not_complete');
