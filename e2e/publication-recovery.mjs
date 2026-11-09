// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#limites-et-reprise-des-publications
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#limites-et-reprise-des-publications
// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md
import assert from 'node:assert/strict';
import {readFile,writeFile,rename,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {randomUUID,randomBytes,createHash} from 'node:crypto';
import https from 'node:https';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';
const run=promisify(execFile),root=fileURLToPath(new URL('../',import.meta.url)),output=path.join(root,'.local/e2e'),base='https://serverless.lelabs.tech';
const report=path.join(output,'publication-recovery.json'),helper='/srv/p2enjoy-serverless/e2e/publication-recovery-operator.py';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const checks=[],observations=[],gates=[],invocations=[],functions=new Map(),archives=[],storageArchives=[],functionIds=[],deletedFunctions=new Set(),cleanupErrors=[],pending=[];
let admin,caller,session,namespace,service,work,credential,before,completed=false,cleanup=false;
const prefix='publication-recovery-'+randomUUID().slice(0,8),applicationSecret='publication-recovery-private-'+randomUUID();
const digest=value=>createHash('sha256').update(value).digest('hex');
function diagnostic(error){const safe=v=>typeof v==='string'&&/^[A-Za-z_][A-Za-z0-9_ :<>=!.-]{0,79}$/.test(v)?v:undefined;const location=String(error?.stack??'').match(/publication-recovery\.mjs:(\d+):(\d+)/);return {name:safe(error?.name)??'UnknownError',code:safe(error?.code),operator:safe(error?.operator),source:location?{line:Number(location[1]),column:Number(location[2])}:undefined,message_sha256:digest(String(error?.message??''))};}
async function save(){const temporary=report+'.pending';await writeFile(temporary,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,cleanupErrors,before,observations,invocations,namespace_id:namespace?.id,function_ids:functionIds,pre_purge_revisions:archives,storage_archives:storageArchives,gates:gates.map(g=>({mode:g.mode,events:g.events,restored:g.restored,exit_code:g.exitCode,stderr_sha256:digest(g.stderr)})),remaining_proofs:['Expiration réelle','Budget et marge disque','Déconnexion administrateur concurrente','Interruption pendant nettoyage','Pannes propres des gardes et processus']},null,2)+'\n',{mode:0o600});await rename(temporary,report);}
async function until(action,message,seconds=60){const end=Date.now()+seconds*1000;while(Date.now()<end){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function call(url,{method='GET',body,bytes,token=false,status=200,headers={}}={}){const response=await(token?caller:admin).fetch(url,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':credential}:{Origin:base,'X-CSRF-Token':session.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(response.status()),method+' '+url+': '+response.status());const raw=await response.text();assert(!raw.includes(applicationSecret));return JSON.parse(raw);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:diagnostic(error)});throw error;}finally{await save();}}
async function remote(mode,fn,extra=[]){const value=await run('ssh',[...ssh,'python3','-B',helper,mode,namespace.id,...(fn?[fn.id]:[]),...extra],{timeout:210000,maxBuffer:8*1024*1024});return JSON.parse(value.stdout.trim().split('\n').at(-1));}
async function current(fn){return call(`/api/functions/${fn.id}`,{token:true});}
async function idle(fn){await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instances_not_released');}
async function create(name){const row=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'publication-recovery.handler',memory_mib:128,cpu:.05,timeout_seconds:10,idle_seconds:0,min_instances:0,max_instances:1}}});functions.set(row.id,row);functionIds.push(row.id);return row;}
async function prepare(fn,status=201){const row=await current(fn);return call(`/api/functions/${fn.id}/deployments`,{method:'POST',token:true,status,headers:{'If-Match':String(row.updated_at)},body:{config:row.config,configuration:{environment:{REVISION_LABEL:'stable'},secrets:{PUBLICATION_RECOVERY_SECRET:applicationSecret}}}});}
async function upload(candidate,bytes,status=200){return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',token:true,bytes,status});}
async function publish(fn,bytes){const value=await upload(await prepare(fn),bytes);assert.equal(value.state,'published');assert(value.validation.valid&&value.validation.container_removed);return value;}
async function promote(fn,row){return call(`/api/functions/${fn.id}/versions/${row.code_hash}/promote`,{method:'POST',token:true,headers:{'If-Match':String((await current(fn)).updated_at)}});}
async function invoke(fn,row,marker,pinned=false){const response=await caller.get(`/invoke/${fn.id}${pinned?'@'+row.code_hash:''}`,{headers:{'X-Serverless-Token':credential}});assert.equal(response.status(),200);const raw=await response.text();assert(!raw.includes(applicationSecret));const value=JSON.parse(raw);assert.equal(value.marker,marker);assert.equal(value.label,'stable');assert.equal(value.secret_sha256,digest(applicationSecret));assert.equal(value.request_id,response.headers()['x-serverless-request-id']);assert.equal(response.headers()['x-serverless-code-hash'],row.code_hash);invocations.push({id:value.request_id,function_id:fn.id,requested_code_hash:pinned?row.code_hash:null,resolved_code_hash:row.code_hash,marker});await idle(fn);}
async function remove(fn){await idle(fn);if(!deletedFunctions.has(fn.id)){await call(`/api/functions/${fn.id}`,{method:'DELETE'});deletedFunctions.add(fn.id);}await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await call(`/api/archives/${fn.id}`);const op=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});await until(async()=>{const v=await call(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'public_purge_not_completed');const final=await call(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);storageArchives.push({function_id:fn.id,namespace_id:namespace.id,operation_id:op.id,purged:true,artifact_bytes:final.artifact_bytes});functions.delete(fn.id);}
async function bundle(marker,delay=0){await writeFile(path.join(work,'publication-marker.json'),JSON.stringify({value:marker,validation_delay_ms:delay}));await run('python3',['-B','-m','adapter','package','--config',path.join(work,'serverless.yml')],{cwd:root,timeout:30000});const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));const bytes=await readFile(path.join(work,'.serverless-p2',descriptor.artifacts.publication.file));assert(bytes.length>192*1024);return bytes;}
async function deleteRevision(fn,row){await call(`/api/functions/${fn.id}/revisions/${row.revision_id}`,{method:'DELETE',token:true,headers:{'If-Match':String((await current(fn)).updated_at)}});await until(async()=>{const v=await remote('inspect',fn);return v.revisions.some(v=>v.id===row.revision_id&&v.deleted_at&&v.stored_bytes===0)&&!v.archives[row.revision_id].directory_exists;},'revision_not_physically_deleted');await call(`/invoke/${fn.id}@${row.code_hash}`,{token:true,status:404});}
async function gate(mode,fn,candidate){
 const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,namespace.id,fn.id,candidate.id],{stdio:['pipe','pipe','pipe']});
 const g={mode,events:[],restored:false,ended:false,stderr:'',exitCode:null};gates.push(g);
 createInterface({input:child.stdout}).on('line',line=>{try{g.events.push(JSON.parse(line));}catch(error){g.events.push({event:'invalid-native-output',diagnostic:diagnostic(error)});}});
 child.stderr.on('data',v=>{g.stderr=(g.stderr+v.toString()).slice(-16000);});child.stdin.on('error',error=>g.events.push({event:'native-stdin-error',diagnostic:diagnostic(error)}));
 const done=new Promise(resolve=>{child.on('close',code=>{g.ended=true;g.exitCode=code;resolve(code);});child.on('error',error=>{g.events.push({event:'native-process-error',diagnostic:diagnostic(error)});g.ended=true;g.exitCode=-1;resolve(-1);});});
 g.wait=async name=>until(()=>{const v=g.events.find(v=>v.event===name);assert(v||!g.ended,'native_driver_ended_before_'+name);return v;},'native_event_missing_'+name,70);
 g.send=value=>child.stdin.write(value+'\n');
 g.join=async(seconds=70)=>{await until(()=>g.ended,'native_ssh_join_timeout',seconds);return done;};
 g.finish=async()=>{assert.equal(await g.join(),0);const value=g.events.find(v=>v.event==='restored');assert(value?.healthy&&value.reference_unchanged&&value.stop_mutator_joined);assert(!g.events.some(v=>v.event==='invalid-native-output'));const joined=g.events.find(v=>v.event==='guard-finished');assert(joined&&Object.values(joined.states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));g.restored=true;return value;};
 g.recover=async()=>{if(!g.ended)child.stdin.end();const armed=g.events.find(v=>v.event==='guard-armed');assert(armed,'native_restoration_identity_unknown');const value=await remote(g.ended?'restore':'rescue',fn,[armed.unit]);assert(value.healthy&&value.reference_unchanged&&Object.values(value.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));try{await g.join(20);}catch(error){g.events.push({event:'local-ssh-join-expired',diagnostic:diagnostic(error)});child.kill('SIGKILL');await g.join(10);}assert(g.ended);g.restored=true;return value;};
 g.independent=async()=>{assert([137,255].includes(await g.join(30)));assert(g.events.some(v=>v.event==='observer-loss'&&v.signal==='SIGKILL'));const armed=g.events.find(v=>v.event==='armed');assert(armed);const receipt=await until(async()=>{const v=await remote('evidence',fn,[armed.unit]);return v.event==='restored'?v:false;},'independent_receipt_missing',50);assert(receipt.independent&&receipt.observer_gone&&receipt.healthy&&receipt.reference_unchanged&&receipt.stop_mutator_joined);const joined=await remote('restore',fn,[armed.unit]);assert(Object.values(joined.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));g.restored=true;return {...receipt,guard_states:joined.guard_states};};
 await g.wait('armed');return g;
}
function interruptedUpload(candidate,bytes,partial) {
  let client;
  const outcome=new Promise(resolve=>{
    client=https.request(base+`/api/deployments/${candidate.id}/artifact`,{method:'PUT',headers:{
      'Content-Type':'application/zip','Content-Length':bytes.length,'X-Serverless-Token':credential}},response=>{
      response.resume();response.on('end',()=>resolve({status:response.statusCode}));
      response.on('error',error=>resolve({error:error.code??error.name}));
    });
    client.on('error',error=>resolve({error:error.code??error.name}));
    client.setTimeout(30000,()=>client.destroy(new Error('Upload timeout')));
    if(partial)client.write(bytes.subarray(0,192*1024));else client.end(bytes);
  });
  pending.push(outcome);return {outcome,close:()=>client.destroy()};
}
async function interrupt(fn,bytes,phase){
 await until(async()=>{const value=await remote('inspect',fn);return value.counts.active_candidates===0&&value.counts.reserved_bytes===0&&!value.validation_containers.length&&!value.validation_channels.length;},'uploads_not_settled_before_guard');const previous=await current(fn),privateBefore=await remote('inspect',fn),candidate=await prepare(fn);let g,uploading,outcome;
 try{
  g=await gate(phase,fn,candidate);uploading=interruptedUpload(candidate,bytes,phase==='receiving');g.send('observe');
  const observed=await g.wait('gated');assert.equal(observed.phase,phase);g.send('interrupt');const cut=await g.wait('cut');assert.equal(cut.native_signal,9);assert.equal(cut.exit_code,137);
  const restored=phase==='validating'?await g.independent():await g.finish();
  uploading.close();outcome=await uploading.outcome;assert(outcome.error||outcome.status>=500);
  const resumed=await call(`/api/deployments/${candidate.id}`,{token:true});assert.equal(resumed.state,'failed');assert.equal(resumed.error_code,'control_interrupted');assert.equal(resumed.revision_id,null);assert.deepEqual(await current(fn),previous);
  const after=await remote('inspect',fn,[candidate.id]);assert.deepEqual(after.function,privateBefore.function);assert.deepEqual(after.versions,privateBefore.versions);assert.deepEqual(after.revisions,privateBefore.revisions);assert.deepEqual(after.archives,privateBefore.archives);assert.equal(after.control.Id,privateBefore.control.Id);assert.equal(after.control.Image,privateBefore.control.Image);assert.notEqual(after.control.started_at,privateBefore.control.started_at);
  assert.equal(after.candidate.reserved_bytes,0);assert.equal(after.candidate.payload_erased,1);assert.equal(after.candidate.directory_exists,false);assert.equal(after.counts.reserved_bytes,0);assert.equal(after.counts.active_candidates,0);assert.deepEqual(after.validation_containers,[]);assert.deepEqual(after.validation_channels,[]);
  observations.push({scenario:'guarded-'+phase,candidate_id:candidate.id,cut,restored,after,transport:outcome});
 }finally{if(uploading){uploading.close();await uploading.outcome;}if(g&&!g.restored)await g.recover();}
}
await mkdir(output,{recursive:true,mode:0o700});await save();
try{
 const state=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));admin=await request.newContext({baseURL:base,storageState:state,timeout:180000});caller=await request.newContext({baseURL:base,timeout:180000});session=await(await admin.get('/api/session')).json();assert(session.authenticated);
 work=await mkdtemp(path.join(output,'publication-recovery-'));await cp(path.join(root,'qualification/artifacts/publication-recovery.cjs'),path.join(work,'publication-recovery.cjs'));await writeFile(path.join(work,'upload-payload.bin'),randomBytes(256*1024));await writeFile(path.join(work,'serverless.yml'),JSON.stringify({service:prefix,provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{publication:{handler:'publication-recovery.handler'}},package:{patterns:['!**','publication-recovery.cjs','publication-marker.json','upload-payload.bin']}}));
 namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:prefix}});credential=(await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'publication-limits-and-recovery',rights:['create','read','update','delete']}})).token;
 before=await remote('inspect');assert.equal(before.counts.active_candidates,0);assert.equal(before.counts.reserved_bytes,0);assert.deepEqual(before.validation_containers,[]);assert.deepEqual(before.validation_channels,[]);
 await check('64 candidats globaux : refus du65e puis places libérées',async()=>{
  const limited=[];for(let i=0;i<9;i++)limited.push(await create('candidate-capacity-'+i));for(const fn of limited.slice(0,8))for(let i=0;i<8;i++)await prepare(fn);await prepare(limited[8],429);assert.equal((await remote('inspect')).counts.active_candidates,64);await remove(limited[0]);await prepare(limited[8]);assert.equal((await remote('inspect')).counts.active_candidates,57);for(const fn of limited.slice(1))await remove(fn);assert.equal((await remote('inspect')).counts.active_candidates,0);
 });
 const fn=await create('publication-history-recovery'),revisions=[];let stable;
 await check('Vingt hashes distincts : doublon admis, dépassement refusé puis place libérée',async()=>{
  const packages=[];for(let i=1;i<=20;i++){const bytes=await bundle('version-'+i);packages.push(bytes);const row=await publish(fn,bytes);assert.equal(row.code_changed,true);revisions.push(row);if(i===1){stable=row;await promote(fn,row);}assert.equal((await current(fn)).active_revision_id,stable.revision_id);}
  assert.equal(new Set(revisions.map(row=>row.code_hash)).size,20);assert.equal(new Set(revisions.map(row=>row.revision_id)).size,20);
  const snapshot=await remote('inspect',fn),duplicate=await publish(fn,packages[19]);assert.equal(duplicate.code_changed,false);assert.equal(duplicate.code_hash,revisions[19].code_hash);assert.equal(duplicate.revision_id,revisions[19].revision_id);assert.deepEqual((await remote('inspect',fn)).versions,snapshot.versions);await invoke(fn,stable,'version-1');await invoke(fn,duplicate,'version-20',true);
  const previous=await current(fn),extra=await prepare(fn);await upload(extra,await bundle('version-21'),409);assert.deepEqual(await current(fn),previous);await until(async()=>{const value=await remote('inspect',fn,[extra.id]);return value.candidate.state==='failed'&&!value.candidate.directory_exists&&value.candidate.reserved_bytes===0&&value.candidate.payload_erased===1&&value.candidate.error_code==='request_rejected';},'refused_hash_not_cleaned');assert.equal((await call(`/api/functions/${fn.id}/revisions?limit=100`,{token:true})).items.length,20);
  await deleteRevision(fn,revisions[1]);const next=await publish(fn,await bundle('version-21'));assert.equal(next.code_changed,true);assert(!revisions.some(row=>row.code_hash===next.code_hash));assert.equal((await call(`/api/functions/${fn.id}/revisions?limit=100`,{token:true})).items.length,20);assert.equal((await remote('inspect',fn)).versions.length,21);await invoke(fn,next,'version-21',true);await invoke(fn,stable,'version-1');for(const row of revisions.slice(2,4))await deleteRevision(fn,row);
  observations.push({scenario:'capacity-and-duplicate',distinct_code_hashes:revisions.map(v=>v.code_hash),duplicate_hash:duplicate.code_hash,new_hash:next.code_hash});
 });
 await check('SIGKILL pendant réception partielle : reprise et upload explicite',async()=>{await interrupt(fn,await bundle('receiving-interrupted'),'receiving');await invoke(fn,stable,'version-1');const next=await publish(fn,await bundle('receiving-recovered'));await invoke(fn,next,'receiving-recovered',true);assert.equal((await current(fn)).active_revision_id,stable.revision_id);});
 await check('SIGKILL pendant validation Docker puis perte helper : reprise indépendante',async()=>{await interrupt(fn,await bundle('validating-interrupted',8000),'validating');await invoke(fn,stable,'version-1');const next=await publish(fn,await bundle('validating-recovered'));await invoke(fn,next,'validating-recovered',true);assert.equal((await current(fn)).active_revision_id,stable.revision_id);});
 assert.equal(invocations.length,8);assert.equal(new Set(invocations.map(v=>v.id)).size,8);completed=true;
}catch(error){if(!checks.some(v=>v.status==='failed'))checks.push({name:'Préparation ou fin',status:'failed',error:diagnostic(error)});observations.push({scenario:'campaign-error',diagnostic:diagnostic(error)});console.error(JSON.stringify(diagnostic(error)));process.exitCode=1;}
finally{
 await Promise.all(pending);for(const g of gates)if(!g.restored)try{await g.recover();}catch(error){cleanupErrors.push({step:'guard-recovery',error:diagnostic(error)});}
 if(gates.every(g=>g.restored)){
  for(const fn of functions.values())try{const history=await call(`/api/functions/${fn.id}/revisions?limit=100`);for(const row of history.items)archives.push({function_id:fn.id,revision_id:row.id,archive_sha256:row.archive_sha256});await remove(fn);}catch(error){cleanupErrors.push({step:'function',id:fn.id,error:diagnostic(error)});}
  if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service',error:diagnostic(error)});}if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace',error:diagnostic(error)});}
  if(work)await rm(work,{recursive:true,force:true});
 }else cleanupErrors.push({step:'fixtures-retained-unconfirmed-restoration'});
 await admin?.dispose();await caller?.dispose();cleanup=cleanupErrors.length===0;await save();if(!completed||!cleanup)process.exitCode=1;
}
