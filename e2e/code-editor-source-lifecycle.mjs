// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_LIFECYCLE.md
// @verifies docs/CODE_EDITOR_SOURCE_LIFECYCLE.md#matrice-et-clôture-de-preuve
// Real SSO, HTTPS, immutable original artifacts, native read syscalls and Docker.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium,request} from 'playwright';
const exec=promisify(execFile),base='https://serverless.lelabs.tech',id=randomUUID(),out=new URL('../.local/e2e/',import.meta.url);
const report=new URL('code-editor-source-lifecycle-'+id+'.json',out),checks=[],observations=[],cleanupErrors=[],intents=[],functions=[],tokens=[],gates=[],pending=[],invocations=[];
const sha=v=>createHash('sha256').update(v).digest('hex'),match=v=>({'If-Match':String(v)}),ep=()=>'/api/functions/'+fn.id;
let credentials,browser,context,page,admin,caller,session,namespace,service,fn,work,pkg,image,readerA,readerB,draftA,draftB,codeHash,purgeOperation,completed=false,scenariosPassed=false,failure=null;
function diagnosis(error){return {type:error.name,message_sha256:sha(String(error.message)),source_line:String(error.stack??'').match(/code-editor-source-lifecycle\.mjs:(\d+)/)?.[1]};}
async function save(){const p=new URL(report.href+'.pending');await writeFile(p,JSON.stringify({campaign:id,target:base,completed,checks,observations,cleanup_errors:cleanupErrors,intents,namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),token_ids:tokens.map(v=>v.id),invocations,skipped:0,failure},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',...diagnosis(error)});throw error;}finally{await save();}}
async function privateInput(){const input=createInterface({input:process.stdin});try{return JSON.parse(await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));}));}finally{input.close();}}
async function api(path,{method='GET',body,bytes,status=200,headers={},owner}={}){
 const r=await (owner?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(owner?{'X-Serverless-Token':owner.token}:{Origin:base,'X-CSRF-Token':session.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
 assert((Array.isArray(status)?status:[status]).includes(r.status()),`${method} ${path}: ${r.status()}`);return {data:await r.json(),status:r.status(),headers:Object.fromEntries(['x-serverless-request-id','x-serverless-code-hash','retry-after'].filter(k=>r.headers()[k]!==undefined).map(k=>[k,r.headers()[k]]))};
}
async function value(path,options){return(await api(path,options)).data;}
async function create(kind,path,body){
 for(let offset=0;;offset+=100){const rows=(await value(path+'?limit=100&offset='+offset)).items;assert(!rows.some(v=>v.name===body.name));if(rows.length<100)break;}
 const intent={kind,path,name:body.name,absent_before_post:true};intents.push(intent);await save();
 const r=await admin.post(path,{data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token}});intent.response_status=r.status();await save();assert.equal(r.status(),201);const row=await r.json();intent.id=row.id;await save();return row;
}
async function reconcile(){for(const intent of intents){if(!intent.id&&!(intent.response_status>=400&&intent.response_status<500)){assert(intent.absent_before_post);for(let offset=0;;offset+=100){const rows=(await value(intent.path+'?limit=100&offset='+offset)).items,found=rows.filter(v=>v.name===intent.name);assert(found.length<=1);if(found.length){intent.id=found[0].id;break;}if(rows.length<100)break;}}
 if(intent.id){if(intent.kind==='namespace'&&!namespace)namespace={id:intent.id};if(intent.kind==='service'&&!service)service={id:intent.id};if(intent.kind==='function'&&!functions.some(v=>v.id===intent.id))functions.push({id:intent.id});if(intent.kind==='token'&&!tokens.some(v=>v.id===intent.id))tokens.push({id:intent.id});}}
 await save();}
async function until(action,label,seconds=90){const end=Date.now()+seconds*1000;while(Date.now()<end){const r=await action();if(r)return r;await new Promise(resolve=>setTimeout(resolve,100));}throw new Error(label);}
const SSH=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
async function remote(mode,unit){return JSON.parse((await exec('ssh',[...SSH,'python3','-B','/srv/p2enjoy-serverless/e2e/code-editor-read-operator.py',mode,fn.id,namespace.id,unit],{timeout:75000,maxBuffer:2*1024**2})).stdout);}
async function inspect(unit){return JSON.parse((await exec('python3',['-B','e2e/code-editor-source-lifecycle-inspect.py',namespace.id,...(unit?[unit]:[])],{timeout:75000,maxBuffer:4*1024**2})).stdout);}
async function gate(count){
 const unit='serverless-restore-editor-read-'+randomUUID().replaceAll('-',''),events=[],stderrHash=createHash('sha256');
 let child,lines,terminal=null,signal=null,closed=false,protocolError=null,stderrBytes=0,stdoutBytes=0;
 let resolveEnded;const ended=new Promise(resolve=>{resolveEnded=resolve;});
 const streamFailure=error=>{if(protocolError)return;protocolError=error;child?.stdin.end();};
 async function awaitClosed(milliseconds){let timer;try{return await Promise.race([ended.then(()=>true),new Promise(resolve=>{timer=setTimeout(()=>resolve(false),milliseconds);})]);}finally{clearTimeout(timer);}}
 async function closeTransport(){
  child?.stdin.end();
  if(!closed){child?.kill('SIGTERM');if(!await awaitClosed(2000)){child?.kill('SIGKILL');assert(await awaitClosed(5000),'local_SSH_not_joined');}}
 }
 const v={unit,events,restored:false,async wait(event,seconds=45){return until(async()=>{if(protocolError)throw protocolError;const found=events.find(x=>x.event===event);if(found)return found;assert(!closed,'native_helper_terminated');},'native_'+event+'_missing',seconds);},
  async join(){
   if(!await awaitClosed(75000)){
    try{const receipt=await remote('recover',unit);if(receipt.completed)this.restored=true;}
    finally{await closeTransport();}
    throw new Error('native_helper_join_timeout');
   }
   return {exit_code:terminal,signal,stderr_bytes:stderrBytes,stderr_sha256:stderrHash.copy().digest('hex'),protocol_error:protocolError?diagnosis(protocolError):null};
  },
  async release(eof=false){
   if(eof)child.stdin.end();else child.stdin.end('release\n');
   const result=await this.join();if(protocolError)throw protocolError;assert.equal(result.exit_code,0);
   const receipt=events.find(x=>x.event==='restored');assert(receipt?.completed);
   const finished=events.find(x=>x.event==='guard-finished');assert(finished);this.restored=true;
   return {result,receipt,states:finished.states};
  },
  async recover(){
   let receipt,result,error;child?.stdin.end();
   try{receipt=await remote('recover',unit);assert(receipt.completed);this.restored=true;}
   catch(e){error=e;}
   finally{try{result=await this.join();}finally{await closeTransport();}}
   if(error)throw error;return {receipt,result};
  },
 };
 gates.push(v);observations.push({gate_intent:{unit,count}});await save();
 child=spawn('ssh',[...SSH,'python3','-B','/srv/p2enjoy-serverless/e2e/code-editor-read-operator.py','hold',fn.id,namespace.id,image,String(count),unit],{stdio:['pipe','pipe','pipe']});
 child.stderr.on('data',chunk=>{stderrBytes+=chunk.length;stderrHash.update(chunk);if(stderrBytes>262144){streamFailure(new Error('native_stderr_limit'));child.stderr.pause();}});
 child.stdout.on('data',chunk=>{stdoutBytes+=chunk.length;if(stdoutBytes>2*1024**2){streamFailure(new Error('native_stdout_limit'));child.stdout.pause();lines?.close();}});
 child.stdout.on('error',streamFailure);child.stderr.on('error',streamFailure);child.stdin.on('error',streamFailure);
 lines=createInterface({input:child.stdout});lines.on('line',line=>{if(protocolError)return;try{assert(line.length<=2*1024**2);assert(events.length<1000);events.push(JSON.parse(line));}catch(error){streamFailure(error);}});lines.on('error',streamFailure);
 child.once('close',(code,s)=>{terminal=code;signal=s;closed=true;lines.close();resolveEnded();});child.once('error',streamFailure);
 const prepared=await v.wait('prepared',15);assert.equal(prepared.unit,unit);await v.wait('armed',15);return v;
}
async function readSource(owner){return api(ep()+'/code-sources/file?path=reader-gate.txt',{owner,status:[200,401,403,404]});}
function startRead(owner){const call={settled:false};call.promise=readSource(owner).then(result=>{call.settled=true;return {result};},error=>{call.settled=true;return {error};});pending.push(call.promise);return call;}
async function joined(call){const v=await call.promise;if(v.error)throw v.error;return v.result;}
function denied(r,status){assert.equal(r.status,status);assert.equal(typeof r.data.detail,'string');for(const k of ['file','text','tree','source','draft','diff'])assert(!(k in r.data));}
async function makeDraft(owner){return (await value(ep()+'/code-draft',{method:'POST',status:201,owner,headers:match((await value(ep())).updated_at),body:{base_code_hash:codeHash}})).draft;}
function exact(r){assert.equal(r.status,200);const f=r.data.file;assert.equal(f.path,'reader-gate.txt');assert.equal(f.size,pkg.files['reader-gate.txt'].bytes);assert.equal(sha(f.text),pkg.files['reader-gate.txt'].sha256);}
async function healthWhileHeld(){const start=performance.now();const r=await caller.get(base+'/healthz');assert.equal(r.status(),200);assert(performance.now()-start<5000);assert.equal((await value(ep())).id,fn.id);return {status:200,elapsed_ms:performance.now()-start};}
async function invoke(){const r=await caller.get(base+'/invoke/'+fn.id,{headers:{'X-Serverless-Token':tokens[0].token}});assert.equal(r.status(),200);const data=await r.json();assert.equal(data.marker,'editor-reader-lifecycle');assert.equal(data.sha256,pkg.files['reader-gate.txt'].sha256);assert.equal(data.bytes,pkg.files['reader-gate.txt'].bytes);invocations.push({id:r.headers()['x-serverless-request-id'],function_id:fn.id,code_hash:r.headers()['x-serverless-code-hash']});await until(async()=>Object.values((await inspect()).busy).every(v=>v===0),'invocation_not_idle');}
async function purge(row){const r=await admin.get('/api/functions/'+row.id);if(r.status()===200)await value('/api/functions/'+row.id,{method:'DELETE'});else assert.equal(r.status(),404);await until(async()=>!(await value('/api/archives/'+row.id)).storage_operation,'archive_pending');const a=await value('/api/archives/'+row.id);if(!a.purged_at){const op=await value('/api/archives/'+row.id+'/purge',{method:'POST',status:[200,202],headers:match(a.updated_at),body:{operation_id:randomUUID(),confirm_name:a.name}});await until(async()=>{const s=await value('/api/storage-operations/'+op.id);assert.notEqual(s.state,'aborted');return s.state==='completed';},'purge_pending');}assert((await value('/api/archives/'+row.id)).purged_at);}
async function main(){await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();assert(credentials.username&&credentials.password);browser=await chromium.launch({headless:true});context=await browser.newContext();page=await context.newPage();
 try{
  await check('Accueil et SSO administrateur réel',async()=>{await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);await page.locator('input[type=submit],button[type=submit]').first().click();credentials=null;await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();const state=await context.storageState();state.cookies=state.cookies.filter(v=>v.domain==='serverless.lelabs.tech'&&v.name==='__Host-p2-session');state.origins=[];assert.equal(state.cookies.length,1);admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});session=await(await admin.get('/api/session')).json();assert(session.authenticated);caller=await request.newContext({baseURL:base,timeout:120000});});
  await check('Paquet original Docker, source UpdateA et refus directs Read',async()=>{
   image='sha256:b452ef1622cf106a85e42c9b616c87c34fcc06123c9dfdfcfe89c48a49af5575';work=await mkdtemp(new URL('code-editor-source-lifecycle-'+id+'-',out).pathname);pkg=JSON.parse((await exec('python3',['-B','e2e/code-editor-read-package.py',work+'/source.zip'])).stdout);
   namespace=await create('namespace','/api/namespaces',{name:'code-editor-read-concurrency-'+id.slice(0,8),description:id});service=await create('service','/api/namespaces/'+namespace.id+'/services',{name:'editor-source-access-lifecycle',description:id});fn=await create('function','/api/services/'+service.id+'/functions',{name:'editor-reader-lifecycle-'+id.slice(0,8),config:{handler:'editor-reader-lifecycle.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,max_instances:1}});functions.push(fn);
   const candidate=await value(ep()+'/code-deployments',{method:'POST',status:201,headers:match(fn.updated_at),body:{deployment_id:randomUUID(),handler:'editor-reader-lifecycle.cjs.handler'}});const published=await value('/api/deployments/'+candidate.id+'/artifact',{method:'PUT',bytes:await readFile(work+'/source.zip')});assert.equal(published.state,'published');codeHash=published.code_hash;await value(ep()+'/versions/'+codeHash+'/promote',{method:'POST',headers:match((await value(ep())).updated_at)});
   tokens.push(await create('token','/api/services/'+service.id+'/tokens',{name:'editor-source-invoker-'+id.slice(0,8),rights:['read'],function_ids:[fn.id]}));readerA=await create('token','/api/services/'+service.id+'/tokens',{name:'editor-source-revoked-owner-'+id.slice(0,8),rights:['update'],function_ids:[fn.id]});tokens.push(readerA);
   exact(await readSource(readerA));draftA=await makeDraft(readerA);assert.equal(draftA.base.code_hash,codeHash);
   for(const path of ['/code-sources','/code-sources/file?path=reader-gate.txt','/code-draft','/code-draft/diff'])denied(await api(ep()+path,{owner:tokens[0],status:403}),403);
   await invoke();observations.push({scenario:'initial-rights',read_denied_paths:4,draft_A:{id:draftA.id,version:draftA.version,owner_id:readerA.id}});
  });
  await check('Révocation pendant le read, refus401 et nouveau propriétaire sans transfert',async()=>{
   const g=await gate(1),call=startRead(readerA),held=await g.wait('held');assert(!call.settled);const health=await healthWhileHeld(),before=await inspect(g.unit);assert(before.gate.file.exists&&before.gate.file.matches_identity);assert(before.gate.readers.every(v=>v.same_thread_alive&&v.fd_matches_target&&v.tracer_pid===before.gate.helper_pid));
   await value('/api/tokens/'+readerA.id+'/revoke',{method:'POST'});const revoked=await inspect(g.unit);assert(revoked.tokens.find(v=>v.id===readerA.id).revoked_at);assert(!call.settled);
   for(const path of ['/code-sources','/code-sources/file?path=reader-gate.txt','/code-draft','/code-draft/diff'])denied(await api(ep()+path,{owner:readerA,status:401}),401);
   const result=await g.release();denied(await joined(call),401);
   readerB=await create('token','/api/services/'+service.id+'/tokens',{name:'editor-source-replacement-owner-'+id.slice(0,8),rights:['update'],function_ids:[fn.id]});tokens.push(readerB);assert.notEqual(readerB.id,readerA.id);exact(await readSource(readerB));assert.equal((await value(ep()+'/code-draft',{owner:readerB})).draft,null);draftB=await makeDraft(readerB);assert.notEqual(draftB.id,draftA.id);
   const owners=await inspect();assert.equal(owners.drafts.length,2);assert(owners.drafts.some(v=>v.id===draftA.id&&v.actor_kind==='token'&&v.actor_id===readerA.id));assert(owners.drafts.some(v=>v.id===draftB.id&&v.actor_kind==='token'&&v.actor_id===readerB.id));
   await invoke();observations.push({scenario:'revoked-during-read',held,health,before,revoked,release:result,initial_response_status:401,new_owner_id:readerB.id,draft_B_id:draftB.id,owners});
  });
  await check('Purge durable en attente du FD vivant, refus puis effacement après jonction',async()=>{
   const g=await gate(1),call=startRead(readerB),held=await g.wait('held');assert(!call.settled);const health=await healthWhileHeld(),before=await inspect(g.unit);
   await value(ep(),{method:'DELETE'});await until(async()=>!(await value('/api/archives/'+fn.id)).storage_operation,'archive_pending',15);const archive=await value('/api/archives/'+fn.id);purgeOperation=randomUUID();observations.push({purge_intent:{id:purgeOperation,function_id:fn.id}});await save();
   const accepted=await api('/api/archives/'+fn.id+'/purge',{method:'POST',status:202,headers:match(archive.updated_at),body:{operation_id:purgeOperation,confirm_name:archive.name}});assert.equal(accepted.data.id,purgeOperation);
   const state=await until(async()=>{const s=await value('/api/storage-operations/'+purgeOperation);assert.notEqual(s.state,'aborted');assert.notEqual(s.state,'completed','purge_completed_while_reader_held');return s.state==='pending'&&s.phase==='artifacts'?s:false;},'purge_not_waiting_on_artifacts',15);
   const retained=await inspect(g.unit);assert(!call.settled);assert.equal(retained.drafts.length,0);assert(retained.functions[0].deleted_at&&!retained.functions[0].purged_at);assert(retained.revisions.every(v=>v.deleted_at&&v.stored_bytes>0&&v.artifact_directory_exists&&v.inventory_count===0));assert(retained.gate.file.exists&&retained.gate.file.matches_identity);assert.equal(retained.gate.file.inode,before.gate.file.inode);assert(retained.gate.readers.every(v=>v.fd_matches_target&&v.tracer_pid===retained.gate.helper_pid));assert(retained.storage_commands.some(v=>v.id===purgeOperation&&v.state==='pending'&&v.phase==='artifacts'));
   for(const path of ['/code-sources/file?path=reader-gate.txt','/code-draft']){denied(await api(ep()+path,{status:404}),404);denied(await api(ep()+path,{owner:readerB,status:403}),403);}const healthy=await caller.get(base+'/healthz');assert.equal(healthy.status(),200);
   const result=await g.release();denied(await joined(call),404);await until(async()=>{const s=await value('/api/storage-operations/'+purgeOperation);assert.notEqual(s.state,'aborted');return s.state==='completed';},'purge_not_completed');
   const erased=await inspect(g.unit),final=await value('/api/archives/'+fn.id);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);assert(erased.functions[0].purged_at);assert(erased.revisions.every(v=>v.stored_bytes===0&&!v.artifact_directory_exists));assert(!erased.gate.file.exists);assert(erased.gate.readers.every(v=>!v.fd_matches_target));assert(Object.values(erased.busy).every(v=>v===0));
   observations.push({scenario:'purge-with-live-reader',held,health,before,accepted_status:202,pending:state,retained,release:result,initial_response_status:404,erased});
  });
  await check('Deux handlers Docker et nettoyage physique recoupés nativement',async()=>{const native=await inspect();assert.equal(invocations.length,2);for(const item of invocations){const row=native.invocations.find(v=>v.id===item.id);assert(row&&row.state==='succeeded'&&row.handler_started===1&&row.http_status===200);assert.equal(native.revisions.find(v=>v.id===row.revision_id).code_hash,item.code_hash);}assert.equal(native.drafts.length,0);assert(native.revisions.every(v=>v.stored_bytes===0&&!v.artifact_directory_exists));assert(Object.values(native.busy).every(v=>v===0));observations.push({scenario:'before-final-cleanup',native});});
  scenariosPassed=true;
 }finally{
  credentials=null;
  for(const g of [...gates].reverse())if(!g.restored)try{observations.push({scenario:'recovery-after-error',result:await g.recover()});}catch(error){cleanupErrors.push({phase:'gate-recovery',...diagnosis(error)});}
  await Promise.allSettled(pending);
  if(admin&&session&&gates.every(v=>v.restored)){
   try{await reconcile();}catch(error){cleanupErrors.push({phase:'reconcile',...diagnosis(error)});}
   for(const row of [...functions].reverse())try{await purge(row);}catch(error){cleanupErrors.push({phase:'purge',...diagnosis(error)});}
   try{if(service){const rows=(await value('/api/services/'+service.id+'/tokens?limit=100')).items;assert(rows.length===tokens.length);for(const row of rows)if(!row.revoked_at)await value('/api/tokens/'+row.id+'/revoke',{method:'POST'});assert((await value('/api/services/'+service.id+'/tokens?limit=100')).items.every(v=>v.revoked_at));}}catch(error){cleanupErrors.push({phase:'token-revoke',...diagnosis(error)});}
   try{if(namespace){const native=await inspect();assert(native.functions.length===functions.length&&native.functions.every(v=>v.purged_at));assert(native.revisions.every(v=>v.stored_bytes===0&&!v.artifact_directory_exists));assert.equal(native.drafts.length,0);assert(native.tokens.every(v=>v.revoked_at));assert(Object.values(native.busy).every(v=>v===0));observations.push({scenario:'native-cleanup',native});}}catch(error){cleanupErrors.push({phase:'native-cleanup',...diagnosis(error)});}
   if(!cleanupErrors.length)try{if(service)await value('/api/services/'+service.id,{method:'DELETE'});if(namespace)await value('/api/namespaces/'+namespace.id,{method:'DELETE'});}catch(error){cleanupErrors.push({phase:'parents',...diagnosis(error)});}
   try{await value('/auth/logout',{method:'POST'});}catch(error){cleanupErrors.push({phase:'logout',...diagnosis(error)});}
  }
  for(const [phase,close] of [['caller',()=>caller?.dispose()],['admin',()=>admin?.dispose()],['context',()=>context?.close()],['browser',()=>browser?.close()],['work',()=>work?rm(work,{recursive:true,force:true}):null]])try{await close();}catch(error){cleanupErrors.push({phase,...diagnosis(error)});}
  completed=scenariosPassed&&cleanupErrors.length===0;await save();
 }
 assert(completed);console.log(JSON.stringify({completed,groups:checks.length,report:report.pathname}));}
main().catch(async error=>{credentials=null;completed=false;failure=diagnosis(error);await save().catch(()=>{});console.error('code_editor_source_lifecycle_e2e_failed');process.exitCode=1;});
