// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_READ_CONCURRENCY.md
// @verifies docs/CODE_EDITOR_READ_CONCURRENCY.md#qualification-propre-à-linstrumentation
// Real SSO, HTTPS, immutable original artifacts, native read syscalls and Docker.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium,request} from 'playwright';
const exec=promisify(execFile),base='https://serverless.lelabs.tech',id=randomUUID(),out=new URL('../.local/e2e/',import.meta.url);
const report=new URL('code-editor-read-concurrency-'+id+'.json',out),checks=[],observations=[],cleanupErrors=[],intents=[],functions=[],tokens=[],gates=[],pending=[],invocations=[];
const sha=v=>createHash('sha256').update(v).digest('hex'),match=v=>({'If-Match':String(v)}),ep=()=>'/api/functions/'+fn.id;
let credentials,browser,context,page,admin,caller,session,namespace,service,fn,work,pkg,image,completed=false,scenariosPassed=false,failure=null;
function diagnosis(error){return {type:error.name,message_sha256:sha(String(error.message)),source_line:String(error.stack??'').match(/code-editor-read-concurrency\.mjs:(\d+)/)?.[1]};}
async function save(){const p=new URL(report.href+'.pending');await writeFile(p,JSON.stringify({campaign:id,target:base,completed,checks,observations,cleanup_errors:cleanupErrors,intents,namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),token_ids:tokens.map(v=>v.id),invocations,skipped:0,failure},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',...diagnosis(error)});throw error;}finally{await save();}}
async function privateInput(){const input=createInterface({input:process.stdin});try{return JSON.parse(await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));}));}finally{input.close();}}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){
 const r=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
 assert((Array.isArray(status)?status:[status]).includes(r.status()),`${method} ${path}: ${r.status()}`);return {data:await r.json(),status:r.status(),headers:r.headers()};
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
async function inspect(){return JSON.parse((await exec('python3',['-B','e2e/code-editor-read-inspect.py',namespace.id],{timeout:75000,maxBuffer:4*1024**2})).stdout);}
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
async function readSource(){const r=await admin.get(ep()+'/code-sources/file?path=reader-gate.txt');return {status:r.status(),data:await r.json(),headers:r.headers()};}
function startRead(){const p=readSource().then(result=>({result}),error=>({error}));pending.push(p);return p;}
async function joined(p){const v=await p;if(v.error)throw v.error;return v.result;}
function exact(r){assert.equal(r.status,200);const f=r.data.file;assert.equal(f.path,'reader-gate.txt');assert.equal(f.size,pkg.files['reader-gate.txt'].bytes);assert.equal(sha(f.text),pkg.files['reader-gate.txt'].sha256);}
async function healthWhileHeld(){const start=performance.now();const r=await caller.get(base+'/healthz');assert.equal(r.status(),200);assert(performance.now()-start<5000);assert.equal((await value(ep())).id,fn.id);return {status:200,elapsed_ms:performance.now()-start};}
async function invoke(){const r=await caller.get(base+'/invoke/'+fn.id,{headers:{'X-Serverless-Token':tokens[0].token}});assert.equal(r.status(),200);const data=await r.json();assert.equal(data.marker,'editor-reader-lifecycle');assert.equal(data.sha256,pkg.files['reader-gate.txt'].sha256);assert.equal(data.bytes,pkg.files['reader-gate.txt'].bytes);invocations.push({id:r.headers()['x-serverless-request-id'],function_id:fn.id,code_hash:r.headers()['x-serverless-code-hash']});await until(async()=>Object.values((await inspect()).busy).every(v=>v===0),'invocation_not_idle');}
async function purge(row){const r=await admin.get('/api/functions/'+row.id);if(r.status()===200)await value('/api/functions/'+row.id,{method:'DELETE'});else assert.equal(r.status(),404);await until(async()=>!(await value('/api/archives/'+row.id)).storage_operation,'archive_pending');const a=await value('/api/archives/'+row.id);if(!a.purged_at){const op=await value('/api/archives/'+row.id+'/purge',{method:'POST',status:[200,202],headers:match(a.updated_at),body:{operation_id:randomUUID(),confirm_name:a.name}});await until(async()=>{const s=await value('/api/storage-operations/'+op.id);assert.notEqual(s.state,'aborted');return s.state==='completed';},'purge_pending');}assert((await value('/api/archives/'+row.id)).purged_at);}
async function main(){await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();assert(credentials.username&&credentials.password);browser=await chromium.launch({headless:true});context=await browser.newContext();page=await context.newPage();
 try{
  await check('Accueil et SSO administrateur réel',async()=>{await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);await page.locator('input[type=submit],button[type=submit]').first().click();credentials=null;await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();const state=await context.storageState();state.cookies=state.cookies.filter(v=>v.domain==='serverless.lelabs.tech'&&v.name==='__Host-p2-session');state.origins=[];assert.equal(state.cookies.length,1);admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});session=await(await admin.get('/api/session')).json();assert(session.authenticated);caller=await request.newContext({timeout:120000});});
  await check('Paquet original publié, source exacte et véritable handler Docker',async()=>{
   image='sha256:b452ef1622cf106a85e42c9b616c87c34fcc06123c9dfdfcfe89c48a49af5575';work=await mkdtemp(new URL('code-editor-read-concurrency-'+id+'-',out).pathname);pkg=JSON.parse((await exec('python3',['-B','e2e/code-editor-read-package.py',work+'/source.zip'])).stdout);
   namespace=await create('namespace','/api/namespaces',{name:'code-editor-read-concurrency-'+id.slice(0,8),description:id});service=await create('service','/api/namespaces/'+namespace.id+'/services',{name:'editor-reader-lifecycle',description:id});fn=await create('function','/api/services/'+service.id+'/functions',{name:'editor-reader-lifecycle-'+id.slice(0,8),config:{handler:'editor-reader-lifecycle.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,max_instances:1}});functions.push(fn);
   const candidate=await value(ep()+'/code-deployments',{method:'POST',status:201,headers:match(fn.updated_at),body:{deployment_id:randomUUID(),handler:'editor-reader-lifecycle.cjs.handler'}});const published=await value('/api/deployments/'+candidate.id+'/artifact',{method:'PUT',bytes:await readFile(work+'/source.zip')});assert.equal(published.state,'published');await value(ep()+'/versions/'+published.code_hash+'/promote',{method:'POST',headers:match((await value(ep())).updated_at)});
   tokens.push(await create('token','/api/services/'+service.id+'/tokens',{name:'editor-reader-lifecycle-read-'+id.slice(0,8),rights:['read'],function_ids:[fn.id]}));exact(await readSource());await invoke();
  });
  for(const [mode,label] of [['release','Libération explicite'],['eof','EOF du propriétaire'],['kill','Perte SIGKILL du helper'],['suspend','Suspension et secours indépendant'],['recover-low-fds','Diagnostic du secours réellement refusé']])await check(label+' : vrai lecteur, HTTP disponible et même contrôle',async()=>{
   const g=await gate(1),p=startRead(),held=await g.wait('held');assert.equal(held.readers.length,1);assert.notEqual(held.readers[0].tid,held.process.pid);const health=await healthWhileHeld();let result;
   if(mode==='release'||mode==='eof')result=await g.release(mode==='eof');
   else {const signalled=await remote(mode,g.unit);if(mode==='recover-low-fds'){assert.equal(signalled.event,'restoration-failed');assert.equal(signalled.errno,24);assert(signalled.helper_gone&&signalled.own_nofile_restored);}else assert.equal(signalled.signal,mode==='kill'?9:19);const ended=await g.join();assert.notEqual(ended.exit_code,0);if(mode==='suspend'){const receipt=await until(async()=>{const r=await remote('evidence',g.unit);return r.event==='restored'?r:false;},'independent_restoration_missing',75);assert(receipt.completed&&receipt.independent&&receipt.helper_gone);result={signalled,ended,independent_receipt:receipt};}else result={signalled,ended};const receipt=await remote('finish',g.unit);assert(receipt.completed);g.restored=true;result.finish=receipt;}
   exact(await joined(p));exact(await readSource());observations.push({scenario:mode,held,health,result});await invoke();
  });
  await check('Quatre read retenus, cinquième429 borné puis capacité rendue',async()=>{
   const g=await gate(4),reads=Array.from({length:4},()=>startRead()),held=await g.wait('held');assert.equal(held.readers.length,4);assert.equal(new Set(held.readers.map(v=>v.tid)).size,4);assert.equal(new Set(held.readers.map(v=>v.fd)).size,4);const health=await healthWhileHeld(),start=performance.now();const fifth=await admin.get(ep()+'/code-sources/file?path=reader-gate.txt'),elapsed=performance.now()-start;assert.equal(fifth.status(),429);assert.equal(fifth.headers()['retry-after'],'2');assert(elapsed<5000);const result=await g.release();for(const p of reads)exact(await joined(p));exact(await readSource());observations.push({scenario:'four-readers',held,health,fifth_status:429,fifth_elapsed_ms:elapsed,result});await invoke();
  });
  await check('Handlers et artefacts natifs de campagne recoupés',async()=>{const native=await inspect();assert.equal(invocations.length,7);for(const item of invocations){const row=native.invocations.find(v=>v.id===item.id);assert(row&&row.state==='succeeded'&&row.handler_started===1&&row.http_status===200);assert.equal(native.revisions.find(v=>v.id===row.revision_id).code_hash,item.code_hash);}assert(native.revisions.length===1&&native.revisions[0].stored_bytes>0);assert(Object.values(native.busy).every(v=>v===0));observations.push({scenario:'before-cleanup',native});});
  scenariosPassed=true;
 }finally{
  credentials=null;
  for(const g of [...gates].reverse())if(!g.restored)try{observations.push({scenario:'recovery-after-error',result:await g.recover()});}catch(error){cleanupErrors.push({phase:'gate-recovery',...diagnosis(error)});}
  await Promise.allSettled(pending);
  if(admin&&session&&gates.every(v=>v.restored)){
   try{await reconcile();}catch(error){cleanupErrors.push({phase:'reconcile',...diagnosis(error)});}
   for(const row of [...functions].reverse())try{await purge(row);}catch(error){cleanupErrors.push({phase:'purge',...diagnosis(error)});}
   try{if(namespace){const native=await inspect();assert(native.functions.length===functions.length&&native.functions.every(v=>v.purged_at));assert(native.revisions.every(v=>v.stored_bytes===0&&!v.artifact_directory_exists));assert.equal(native.drafts.length,0);assert(Object.values(native.busy).every(v=>v===0));observations.push({scenario:'native-cleanup',native});}}catch(error){cleanupErrors.push({phase:'native-cleanup',...diagnosis(error)});}
   try{if(service){const rows=(await value('/api/services/'+service.id+'/tokens?limit=100')).items;assert(rows.length===tokens.length);for(const row of rows)if(!row.revoked_at)await value('/api/tokens/'+row.id+'/revoke',{method:'POST'});assert((await value('/api/services/'+service.id+'/tokens?limit=100')).items.every(v=>v.revoked_at));}}catch(error){cleanupErrors.push({phase:'token-revoke',...diagnosis(error)});}
   if(!cleanupErrors.length)try{if(service)await value('/api/services/'+service.id,{method:'DELETE'});if(namespace)await value('/api/namespaces/'+namespace.id,{method:'DELETE'});}catch(error){cleanupErrors.push({phase:'parents',...diagnosis(error)});}
   try{await value('/auth/logout',{method:'POST'});}catch(error){cleanupErrors.push({phase:'logout',...diagnosis(error)});}
  }
  for(const [phase,close] of [['caller',()=>caller?.dispose()],['admin',()=>admin?.dispose()],['context',()=>context?.close()],['browser',()=>browser?.close()],['work',()=>work?rm(work,{recursive:true,force:true}):null]])try{await close();}catch(error){cleanupErrors.push({phase,...diagnosis(error)});}
  completed=scenariosPassed&&cleanupErrors.length===0;await save();
 }
 assert(completed);console.log(JSON.stringify({completed,groups:checks.length,report:report.pathname}));}
main().catch(async error=>{credentials=null;completed=false;failure=diagnosis(error);await save().catch(()=>{});console.error('code_editor_read_concurrency_e2e_failed');process.exitCode=1;});
