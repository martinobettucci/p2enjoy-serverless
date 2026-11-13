// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md
// @verifies docs/CODE_EDITOR_ARCHIVE_LIMITS.md#clôture-et-portée
// Real SSO, HTTPS, immutable original artifacts, native read syscalls and Docker.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium,request} from 'playwright';
const exec=promisify(execFile),base='https://serverless.lelabs.tech',id=randomUUID(),out=new URL('../.local/e2e/',import.meta.url);
const report=new URL('code-editor-build-capacity-'+id+'.json',out),checks=[],observations=[],cleanupErrors=[],intents=[],functions=[],tokens=[],gates=[],pending=[],invocations=[];
const sha=v=>createHash('sha256').update(v).digest('hex'),match=v=>({'If-Match':String(v)}),ep=()=>'/api/functions/'+fn.id;
let credentials,browser,context,page,admin,caller,session,namespace,service,fn,work,pkg,image,peer,draftA,draftB,codeHash,gateText,completed=false,scenariosPassed=false,failure=null;
function diagnosis(error){return {type:error.name,message_sha256:sha(String(error.message)),source_line:String(error.stack??'').match(/code-editor-build-capacity\.mjs:(\d+)/)?.[1]};}
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
async function inspect(unit){return JSON.parse((await exec('python3',['-B','e2e/code-editor-build-inspect.py',namespace.id,...(unit?[unit]:[])],{timeout:75000,maxBuffer:4*1024**2})).stdout);}
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
async function healthWhileHeld(){const start=performance.now();const r=await caller.get(base+'/healthz');assert.equal(r.status(),200);assert(performance.now()-start<5000);assert.equal((await value(ep())).id,fn.id);return {status:200,elapsed_ms:performance.now()-start};}
async function invoke(row=fn,hash){const r=await caller.get(base+'/invoke/'+row.id+(hash?'@'+hash:''),{headers:{'X-Serverless-Token':tokens[0].token}});assert.equal(r.status(),200);const data=await r.json();assert.equal(data.marker,'editor-reader-lifecycle');assert.equal(data.sha256,pkg.files['reader-gate.txt'].sha256);assert.equal(data.bytes,pkg.files['reader-gate.txt'].bytes);invocations.push({id:r.headers()['x-serverless-request-id'],function_id:row.id,code_hash:r.headers()['x-serverless-code-hash']});await until(async()=>Object.values((await inspect()).busy).every(v=>v===0),'invocation_not_idle');}
async function purge(row){const r=await admin.get('/api/functions/'+row.id);if(r.status()===200)await value('/api/functions/'+row.id,{method:'DELETE'});else assert.equal(r.status(),404);await until(async()=>!(await value('/api/archives/'+row.id)).storage_operation,'archive_pending');const a=await value('/api/archives/'+row.id);if(!a.purged_at){const op=await value('/api/archives/'+row.id+'/purge',{method:'POST',status:[200,202],headers:match(a.updated_at),body:{operation_id:randomUUID(),confirm_name:a.name}});await until(async()=>{const s=await value('/api/storage-operations/'+op.id);assert.notEqual(s.state,'aborted');return s.state==='completed';},'purge_pending');}assert((await value('/api/archives/'+row.id)).purged_at);}
async function makeDraft(row,hash){return(await value('/api/functions/'+row.id+'/code-draft',{method:'POST',status:201,headers:match((await value('/api/functions/'+row.id)).updated_at),body:{base_code_hash:hash??null}})).draft;}
function stable(v){return Object.fromEntries(['functions','drafts','draft_mutations','revisions','deployments'].map(k=>[k,v[k]]));}
async function publish(row,draft,deployment_id,status=200){return api('/api/functions/'+row.id+'/code-draft/publish',{method:'POST',status,headers:match((await value('/api/functions/'+row.id)).updated_at),body:{deployment_id,draft_version:draft.version}});}
function startPublish(row,draft,deployment_id){const call={settled:false};call.promise=publish(row,draft,deployment_id).then(result=>{call.settled=true;return{result};},error=>{call.settled=true;return{error};});pending.push(call.promise);return call;}
async function joined(call){const v=await call.promise;if(v.error)throw v.error;return v.result;}
function summary(r){return Object.fromEntries(['id','state','revision_id','code_hash','code_changed'].filter(k=>r.data[k]!==undefined).map(k=>[k,r.data[k]]));}
async function main(){await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();assert(credentials.username&&credentials.password);browser=await chromium.launch({headless:true});context=await browser.newContext();page=await context.newPage();
 try{
  await check('Accueil et SSO administrateur réel',async()=>{await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);await page.locator('input[type=submit],button[type=submit]').first().click();credentials=null;await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();const state=await context.storageState();state.cookies=state.cookies.filter(v=>v.domain==='serverless.lelabs.tech'&&v.name==='__Host-p2-session');state.origins=[];assert.equal(state.cookies.length,1);admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});session=await(await admin.get('/api/session')).json();assert(session.authenticated);caller=await request.newContext({baseURL:base,timeout:120000});});
  await check('Une fonction originale publiée et brouillon prêt avant armement',async()=>{
   image='sha256:b452ef1622cf106a85e42c9b616c87c34fcc06123c9dfdfcfe89c48a49af5575';work=await mkdtemp(new URL('code-editor-build-capacity-'+id+'-',out).pathname);pkg=JSON.parse((await exec('python3',['-B','e2e/code-editor-read-package.py',work+'/source.zip'])).stdout);
   namespace=await create('namespace','/api/namespaces',{name:'code-editor-read-concurrency-'+id.slice(0,8),description:id});service=await create('service','/api/namespaces/'+namespace.id+'/services',{name:'editor-reconstruction-capacity',description:id});fn=await create('function','/api/services/'+service.id+'/functions',{name:'editor-reader-lifecycle-'+id.slice(0,8),config:{handler:'editor-reader-lifecycle.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,max_instances:1}});functions.push(fn);
   const candidate=await value(ep()+'/code-deployments',{method:'POST',status:201,headers:match(fn.updated_at),body:{deployment_id:randomUUID(),handler:'editor-reader-lifecycle.cjs.handler'}});const published=await value('/api/deployments/'+candidate.id+'/artifact',{method:'PUT',bytes:await readFile(work+'/source.zip')});assert.equal(published.state,'published');codeHash=published.code_hash;await value(ep()+'/versions/'+codeHash+'/promote',{method:'POST',headers:match((await value(ep())).updated_at)});
   tokens.push(await create('token','/api/services/'+service.id+'/tokens',{name:'editor-build-invoker-'+id.slice(0,8),rights:['read']}));draftA=await makeDraft(fn,codeHash);gateText=(await value(ep()+'/code-sources/file?path=reader-gate.txt')).file.text;assert.equal(sha(gateText),pkg.files['reader-gate.txt'].sha256);await invoke();
  });
  await check('Publication retenue, refus429 sur A et B puis capacité rendue',async()=>{
   const first=randomUUID();observations.push({publication_intent:{function_id:fn.id,deployment_id:first,draft_version:draftA.version}});await save();const g=await gate(1),call=startPublish(fn,draftA,first),held=await g.wait('held');assert(!call.settled);assert.equal(held.readers.length,1);const health=await healthWhileHeld();
   peer=await create('function','/api/services/'+service.id+'/functions',{name:'editor-peer-publication-'+id.slice(0,8),config:{handler:'editor-reader-lifecycle.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,max_instances:1}});functions.push(peer);draftB=await makeDraft(peer,null);
   for(const [path,text] of [['editor-reader-lifecycle.cjs',await readFile(new URL('../qualification/artifacts/editor-reader-lifecycle.cjs',import.meta.url),'utf8')],['reader-gate.txt',gateText]])draftB=(await value('/api/functions/'+peer.id+'/code-draft',{method:'PUT',headers:match(draftB.version),body:{file:{action:'write',path,text}}})).draft;
   const before=await inspect(g.unit);assert(before.gate.file.matches_identity&&before.gate.readers.every(v=>v.same_thread_alive&&v.fd_matches_target&&v.tracer_pid===before.gate.helper_pid));assert(!before.deployments.some(v=>v.id===first));assert(before.drafts.find(v=>v.id===draftA.id).last_deployment_id===null);
   const refused=[];
   for(const [row,draft] of [[fn,draftA],[peer,draftB]]){const uuid=randomUUID();observations.push({refused_publication_intent:{function_id:row.id,deployment_id:uuid,draft_version:draft.version}});await save();const started=performance.now(),r=await publish(row,draft,uuid,429),elapsed=performance.now()-started;assert(elapsed<5000);assert.equal(r.data.error,'Une publication de brouillon est déjà en cours.');assert.equal(r.headers['retry-after'],'5');await api('/api/deployments/'+uuid,{status:404});refused.push({function_id:row.id,deployment_id:uuid,status:r.status,retry_after:r.headers['retry-after'],elapsed_ms:elapsed,error:r.data.error});}
   const after=await inspect(g.unit);assert.deepEqual(stable(after),stable(before));assert(!call.settled);for(const r of refused)assert(!after.deployments.some(v=>v.id===r.deployment_id));assert.equal((await caller.get(base+'/healthz')).status(),200);
   const release=await g.release(),published=await joined(call);assert.equal(published.data.id,first);assert.equal(published.data.state,'published');assert.equal(published.data.code_hash,codeHash);assert.equal(published.data.code_changed,false);await invoke();
   const next=randomUUID();observations.push({publication_intent:{function_id:peer.id,deployment_id:next,draft_version:draftB.version}});await save();const second=await publish(peer,draftB,next);assert.equal(second.data.state,'published');await invoke(peer,second.data.code_hash);observations.push({scenario:'global-publication-capacity',held,health,before,refused,after,release,first:summary(published),second:summary(second)});
  });
  await check('Trois handlers et candidats sans rejeu recoupés nativement',async()=>{const native=await inspect();assert.equal(invocations.length,3);for(const item of invocations){const row=native.invocations.find(v=>v.id===item.id);assert(row&&row.state==='succeeded'&&row.handler_started===1&&row.http_status===200);assert.equal(native.revisions.find(v=>v.id===row.revision_id).code_hash,item.code_hash);}const refused=observations.filter(v=>v.refused_publication_intent).map(v=>v.refused_publication_intent.deployment_id);assert.equal(refused.length,2);assert(refused.every(id=>!native.deployments.some(v=>v.id===id)));const accepted=observations.filter(v=>v.publication_intent).map(v=>v.publication_intent);assert.equal(accepted.length,2);for(const v of accepted){assert(native.deployments.some(d=>d.id===v.deployment_id&&d.function_id===v.function_id&&d.state==='published'));assert(native.drafts.some(d=>d.function_id===v.function_id&&d.last_deployment_id===v.deployment_id));}assert.equal(native.deployments.length,3);assert(Object.values(native.busy).every(v=>v===0));observations.push({scenario:'native-candidates-and-handlers',native});});
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
main().catch(async error=>{credentials=null;completed=false;failure=diagnosis(error);await save().catch(()=>{});console.error('code_editor_build_capacity_e2e_failed');process.exitCode=1;});
