// @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#plan-séquentiel-avant-code
// @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
// All helpers exercise real HTTPS publications, Docker observations and storage.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,stat} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';

const root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile),base='https://serverless.lelabs.tech';
const prefix='validator-names-'+randomUUID().slice(0,8),secret='validator-name-private-'+randomUUID(),checks=[],evidence=[],pending=[],cleanupErrors=[];
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'],helper='/srv/p2enjoy-serverless/e2e/validator-names-operator.py';
let admin,caller,session,namespace,service,fn,work,credential,stable,baseline,guardUnit,restored,completed=false,cleanup=false,counter=0;
const report=new URL('validator-names.json',out),digest=v=>createHash('sha256').update(v).digest('hex');
async function save(){await writeFile(report,JSON.stringify({target:base,prefix,completed:completed&&cleanup,cleanup,cleanup_errors:cleanupErrors,checks,skipped:0,evidence,
  namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],guard_unit:guardUnit,guard_restored:restored??null},null,2)+'\n',{mode:0o600});}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(e){checks.push({name,status:'failed',error:e.name,message:e.message.split('\n')[0].replaceAll(secret,'[redacted]')});throw e;}finally{await save();}}
async function call(path,{method='GET',body,bytes,status=200,headers={}}={}){const response=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...(bytes?{'Content-Type':'application/zip'}:{}),...headers},timeout:120000,maxRetries:0});
  const text=await response.text();assert(!text.includes(secret),'secret_exposed');assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()}`);return JSON.parse(text);}
async function until(action,message,timeout=120000){const end=Date.now()+timeout;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(r=>setTimeout(r,120));}assert.fail(message);}
function track(promise){const safe=promise.then(value=>({value}),error=>({error}));pending.push(safe);return safe;}
async function observed(promise){const row=await promise;if(row.error)throw row.error;return row.value;}
async function remote(mode,args=[]){const p=await new Promise(resolve=>execFile('ssh',[...ssh,'python3','-B',helper,mode,fn.id,namespace.id,...args],{timeout:160000,maxBuffer:3*1024**2},(error,stdout,stderr)=>resolve({error,stdout,stderr})));
  assert(!p.stdout.includes(secret)&&!p.stderr.includes(secret),'operator_private_output');const lines=p.stdout.trim().split('\n').filter(Boolean);let last;
  for(const line of lines){const value=JSON.parse(line);if(value.event==='guard-armed'){assert.equal(guardUnit,value.unit);evidence.push(value);await save();}else last=value;}
  if(p.error){evidence.push({operator_failure:{mode,exit_code:p.error.code??null,stderr_sha256:digest(p.stderr)}});await save();}
  assert(!p.error,'operator_failed_'+mode);assert(last,'operator_terminal_receipt_missing');return last;}
const current=()=>call(`/api/functions/${fn.id}`);
async function prepare(){const v=await current();return call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(v.updated_at)},body:{deployment_id:randomUUID(),handler:'validator-observation.handler'}});}
async function zip(mode){await writeFile(work+'/validation-mode.json',JSON.stringify({mode}));const file=work+'/'+mode+'.zip';await run('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(sys.argv[2],'w');[z.write(p/n,n) for n in ('validator-observation.mjs','validation-mode.json')];z.close()",work,file]);return readFile(file);}
async function upload(candidate,bytes,status=200){return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes,status});}
async function invoke(){const r=await caller.get(`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':credential.token},timeout:30000,maxRetries:0});assert.equal(r.status(),200);const value=await r.json();counter++;
  assert.equal(value.mode,'success');assert.equal(value.public_value,'preserved-public');assert.equal(value.secret_sha256,digest(secret));assert.equal(value.data_count,counter);assert.equal(value.cache_count,counter);assert.equal(r.headers()['x-serverless-code-hash'],stable.code_hash);
  evidence.push({invocation_id:r.headers()['x-serverless-request-id'],code_hash:stable.code_hash,counter});await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instance_not_stopped');await save();}
function unchanged(value){assert.deepEqual(value.function,baseline.function);assert.deepEqual(value.revisions,baseline.revisions);assert.deepEqual(value.versions,baseline.versions);}
function identity(value,expectedMode){assert.equal(value.validators.length,1);const v=value.validators[0];assert.match(v.name,/^serverless-code-validator-[a-f0-9]{32}$/);assert.equal(v.marker.mode,expectedMode);assert(v.running&&v.channel_present);
  assert.equal(v.isolation.NetworkMode,'none');assert.equal(v.isolation.ReadonlyRootfs,true);assert.deepEqual(v.isolation.CapDrop,['ALL']);assert(v.isolation.SecurityOpt.includes('no-new-privileges:true'));assert.equal(v.isolation.Memory,512*1024**2);assert.equal(v.isolation.MemorySwap,512*1024**2);assert.equal(v.isolation.NanoCpus,250000000);assert.equal(v.isolation.PidsLimit,64);assert.equal(v.isolation.Init,true);assert(v.mounts.every(m=>m.RW===false));return v;}
async function ensureRestored(){if(guardUnit&&!restored){restored=await remote('restore',[guardUnit]);assert(restored.completed&&restored.healthy&&restored.reference_unchanged&&restored.official_unchanged);await save();}}

await mkdir(out,{recursive:true,mode:0o700});assert(!(await stat(report).then(()=>true,()=>false)),'existing_receipt_requires_preserving');await save();
try{
  const build=JSON.parse(await readFile(new URL('validator-names-build.json',out),'utf8'));assert(build.completed&&build.new_image&&build.services_unchanged,'new_image_build_required');
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:120000});caller=await request.newContext({baseURL:base,timeout:120000});session=await call('/api/session');assert(session.authenticated,'real_sso_admin_required');
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'validator-code-lifecycle'}});await save();
  fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'preserve-code-through-validator-upgrade',config:{handler:'validator-observation.handler',cpu:.05,memory_mib:128,timeout_seconds:10,idle_seconds:0,max_instances:1,
    storage:{concurrency:'shared',data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},configuration:{environment:{VALIDATOR_NAME_PUBLIC:'preserved-public'},secrets:{VALIDATOR_NAME_SECRET:secret}}}});await save();
  credential=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-preserved-validator-code',rights:['read'],function_ids:[fn.id]}});
  work=await mkdtemp(new URL('validator-names-code-',out).pathname);await cp(new URL('qualification/artifacts/validator-observation.mjs',root),work+'/validator-observation.mjs');const normal=await zip('success'),rejected=await zip('reject'),slow=await zip('timeout');
  const first=await prepare();stable=await upload(first,normal);assert(stable.validation.valid&&stable.validation.container_removed);const v=await current();await call(`/api/functions/${fn.id}/versions/${stable.code_hash}/promote`,{method:'POST',headers:{'If-Match':String(v.updated_at)}});await invoke();baseline=await remote('inspect',[first.id]);assert.equal(baseline.revisions.length,1);assert.equal(baseline.versions.length,1);evidence.push({stable_preparation:baseline});await save();
  await check('Vrai ancien validateur interrompu, puis reprise par la nouvelle image et données conservées',async()=>{
    const candidate=await prepare();guardUnit='serverless-validator-names-'+randomUUID().replaceAll('-','');evidence.push({interruption_intent:{candidate_id:candidate.id,unit:guardUnit,new_image:build.new_image}});await save();
    const sending=track(admin.put(`/api/deployments/${candidate.id}/artifact`,{data:slow,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,'Content-Type':'application/zip'},timeout:120000,maxRetries:0}).then(async r=>({status:r.status(),body_sha256:digest(await r.body())})));
    const cut=await remote('interrupt',[candidate.id,build.new_image,guardUnit]);assert.equal(cut.control_exit_code,137);assert.match(cut.before.validators[0].name,/^p2-v-[a-f0-9]{32}$/);assert.equal(cut.before.validators[0].id,cut.orphan.validators[0].id);assert.equal(cut.orphan.candidate.state,'validating');evidence.push({legacy_interrupted:cut});await save();
    await ensureRestored();assert.equal(restored.image,build.new_image);const sent=await sending;if(sent.value)assert.notEqual(sent.value.status,200);evidence.push({interrupted_request:sent.value??{transport_error:sent.error.name}});
    const after=await until(async()=>{const value=await remote('inspect',[candidate.id]);return value.candidate.reserved_bytes===0&&!value.global_validators.length&&!value.channels.length&&!value.code_present&&!value.archive_present?value:false;},'legacy_validator_not_reconciled');
    assert.equal(after.candidate.state,'failed');assert.equal(after.candidate.error_code,'control_interrupted');assert.equal(after.candidate.revision_id,null);assert.equal(after.candidate.configuration_empty,1);unchanged(after);evidence.push({legacy_reconciled:after});await invoke();
  });
  for(const [kind,bytes,error] of [['success',normal,null],['reject',rejected,'import_failed'],['timeout',slow,'validation_timeout']]){
    await check(`Nouveau nom et isolation, import ${kind}, suppression confirmée et stable conservé`,async()=>{
      const candidate=await prepare(),sending=track(upload(candidate,bytes,error?422:200));const active=await remote('observe',[candidate.id]);const validator=identity(active,kind);const result=await observed(sending);
      const after=await until(async()=>{const value=await remote('inspect',[candidate.id]);return value.candidate.reserved_bytes===0&&!value.global_validators.length&&!value.channels.length?value:false;},'validator_cleanup_not_confirmed');
      assert.equal(after.candidate.validation.container_removed,true);assert.equal(after.candidate.validation.valid,!error);
      if(error){assert.equal(after.candidate.state,'failed');assert.equal(after.candidate.validation.error,error);assert(!after.code_present&&!after.archive_present);if(kind==='timeout')assert(after.candidate.validation.elapsed_seconds>=14.5&&after.candidate.validation.elapsed_seconds<=25);}
      else{assert.equal(result.code_hash,stable.code_hash);assert.equal(result.revision_id,stable.revision_id);assert.equal(result.code_changed,false);assert.equal(result.state,'published');}
      unchanged(after);evidence.push({named_validation:{kind,validator,result_candidate:after.candidate,code_present:after.code_present,archive_present:after.archive_present}});await invoke();
    });
  }
  completed=true;
}catch(e){evidence.push({failure:{type:e.name,message:e.message.split('\n')[0].replaceAll(secret,'[redacted]')}});await save();throw new Error('validator_names_proof_failed');}
finally{
  try{await ensureRestored();}catch(e){cleanupErrors.push({resource:'control-recovery',error:e.name});}
  const joined=await Promise.all(pending);evidence.push({request_joins:joined.map(v=>({fulfilled:!v.error,error:v.error?.name}))});
  if(admin&&session?.authenticated&&!cleanupErrors.length){
    try{
      if(!namespace)namespace=(await call('/api/namespaces?limit=100')).items.find(row=>row.name===prefix);
      if(namespace&&!service)service=(await call(`/api/namespaces/${namespace.id}/services?limit=100`)).items.find(row=>row.name==='validator-code-lifecycle');
      if(service&&!fn)fn=(await call(`/api/services/${service.id}/functions?limit=100`)).items.find(row=>row.name==='preserve-code-through-validator-upgrade');
    }catch(e){cleanupErrors.push({resource:'campaign-identity',error:e.name});}
    if(credential)try{await call(`/api/tokens/${credential.id}/revoke`,{method:'POST'});}catch(e){cleanupErrors.push({resource:'token',error:e.name});}
    if(fn)try{await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'cleanup_instance_pending');await call(`/api/functions/${fn.id}`,{method:'DELETE'});const archive=await call(`/api/archives/${fn.id}`),operation=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archive.updated_at)},body:{operation_id:randomUUID(),confirm_name:archive.name}});
      await until(async()=>{const row=await call(`/api/storage-operations/${operation.id}`);assert.notEqual(row.state,'failed');return row.state==='completed';},'purge_not_finished');evidence.push({purged:{function_id:fn.id,operation_id:operation.id}});
    }catch(e){cleanupErrors.push({resource:'function',error:e.name});}
    if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(e){cleanupErrors.push({resource:'service',error:e.name});}
    if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(e){cleanupErrors.push({resource:'namespace',error:e.name});}
  }
  if(work&&!cleanupErrors.length)await rm(work,{recursive:true,force:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert(cleanup,'cleanup_required');
}
