// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
// All mutations use HTTPS; packages run in the actual DEV Docker runtime.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,rename} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';

const run=promisify(execFile),root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url);
const base='https://serverless.lelabs.tech',prefix='function-versions-'+randomUUID().slice(0,8),checks=[],evidence=[],cleanupErrors=[],pending=[];
const functions=[],services=[],tokens=[];let admin,caller,session,namespace,service,fn,work,completed=false,cleanup=false;
const secret='versions-private-'+randomUUID(),reportFile=new URL('function-versions-api.json',out);
let a,b,aFile,bFile,createToken,readToken,updateToken,otherToken;
const pilotEvents={http:[{path:'pilot',methods:['GET','OPTIONS'],implicit:false}],schedules:[]};
async function save(){const p=new URL('function-versions-api.pending',out);await writeFile(p,JSON.stringify({target:base,prefix,completed:completed&&cleanup&&!cleanupErrors.length,
  cleanup,cleanup_errors:cleanupErrors,skipped:0,checks,evidence,namespace_id:namespace?.id,function_ids:functions.map(row=>row.id)},null,2)+'\n',{mode:0o600});await rename(p,reportFile);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
function tracked(promise){const safe=promise.then(value=>({value}),error=>({error}));pending.push(safe);return safe;}
async function observed(promise){const result=await promise;if(result.error)throw result.error;return result.value;}
async function call(path,{method='GET',body,bytes,token,headers={},status=200}={}){
  const r=await (token?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),
    ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()} au lieu de ${status}`);
  const text=await r.text();assert(!text.includes(secret),'secret_exposed');return JSON.parse(text);
}
async function until(action){const end=Date.now()+120000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,100));}assert.fail('real_lifecycle_deadline');}
async function current(){return call(`/api/functions/${fn.id}`);}
async function artifacts(){const {stdout}=await run('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202',
  'root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/function-version-artifacts.py',fn.id,namespace.id],{timeout:30000,maxBuffer:2*1024*1024});return JSON.parse(stdout);}
async function versions(){return call(`/api/functions/${fn.id}/versions?limit=100`);}
async function mutate(hash,action,body={},token=updateToken.token,status=200){const row=await current();return call(`/api/functions/${fn.id}/versions/${hash}${action==='delete'?'':'/'+action}`,
  {method:action==='delete'?'DELETE':'POST',headers:{'If-Match':String(row.updated_at)},...(action==='archive'||action==='delete'?{body}:{}),token,status});}
async function configure(change){const row=await current();return call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,...change}}});}
async function bundle(value,delay=0){const folder=new URL(`code-${value}-${randomUUID().slice(0,8)}/`,work);await mkdir(folder);
  await cp(new URL('../qualification/artifacts/function-versions.cjs',import.meta.url),new URL('function-versions.cjs',folder));
  await writeFile(new URL('version-marker.json',folder),JSON.stringify({value,validation_delay_ms:delay}));
  const config=new URL('serverless.yml',folder);await writeFile(config,JSON.stringify({service:'version-api',provider:{name:'p2enjoy',runtime:'nodejs24.x'},
    functions:{probe:{handler:'function-versions.primary'}},package:{patterns:['!**','function-versions.cjs','version-marker.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',config.pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',folder),'utf8'));
  return new URL('.serverless-p2/'+descriptor.artifacts.probe.file,folder).pathname;
}
async function prepare({handler='primary',events,restore,token=updateToken.token}={}){const row=await current();return call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,
  token,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:'function-versions.'+handler,...(events?{events}:{}),...(restore?{restore_code_hash:restore}:{})}});}
async function upload(candidate,file,{token=updateToken.token,status=200}={}){return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:await readFile(file),token,status});}
async function publish(file,options={}){const candidate=await prepare(options);return upload(candidate,file,options);}
async function invoke({hash,path='',status=200,marker,handler,delay=0,token=readToken.token}={}){
  const address=`/invoke/${fn.id}${hash===undefined?'':'@'+hash}${path?'/'+path:''}${delay?'?delay_ms='+delay:''}`;
  const r=await caller.get(address,{headers:{'X-Serverless-Token':token,Authorization:'Bearer qualification-business-identity'}});assert.equal(r.status(),status,address);
  const body=await r.json();assert(!JSON.stringify(body).includes(secret));
  if(status===200){assert.equal(body.marker,marker);assert.equal(body.handler,handler);assert(body.authorization_present);
    assert.equal(body.common,'service-value');assert.equal(body.local,'function-value');assert.equal(body.secret_sha256,createHash('sha256').update(secret).digest('hex'));
    assert.match(r.headers()['x-serverless-code-hash'],/^[0-9a-f]{64}$/);if(hash!==undefined)assert.equal(r.headers()['x-serverless-code-hash'],hash);
    return {...body,executed_hash:r.headers()['x-serverless-code-hash'],invocation_id:r.headers()['x-serverless-request-id']};}
  return body;
}
async function token(target,name,rights,extra={}){const row=await call(`/api/services/${target.id}/tokens`,{method:'POST',status:201,body:{name,rights,...extra}});tokens.push(row);return row;}
async function purge(owned){let row=await call(`/api/functions/${owned.id}`);await call(`/api/functions/${owned.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,min_instances:0,idle_seconds:0}}});
  await until(async()=>!(await call(`/api/functions/${owned.id}/instances`)).items.length);await call(`/api/functions/${owned.id}`,{method:'DELETE'});
  await until(async()=>!(await call(`/api/archives/${owned.id}`)).storage_operation);row=await call(`/api/archives/${owned.id}`);
  const op=await call(`/api/archives/${owned.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
  await until(async()=>{const state=await call(`/api/storage-operations/${op.id}`);assert.notEqual(state.state,'aborted');return state.state==='completed';});
  const archive=await call(`/api/archives/${owned.id}`);assert.equal(archive.artifact_bytes,0);assert.equal(archive.revision_count,0);evidence.push({purged_function_id:owned.id,operation_id:op.id});
}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});caller=await request.newContext({baseURL:base,timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'real_sso_session_required');work=new URL((await mkdtemp(new URL('function-versions-api-',out).pathname))+'/','file:');
  await check('Droits Create : premier upload préparé, doublon et refus d’un autre code',async()=>{
    namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
    service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'version-api'}});services.push(service);await save();
    await call(`/api/services/${service.id}/configuration`,{method:'PUT',body:{environment:{VERSIONS_COMMON:'service-value'},secrets:{VERSIONS_SECRET:secret}}});
    createToken=await token(service,'initial-code',['create']);readToken=await token(service,'invoke-code',['read']);updateToken=await token(service,'manage-code',['update']);
    fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,token:createToken.token,body:{name:'release-flow',
      config:{handler:'function-versions.primary',cpu:.05,memory_mib:128,timeout_seconds:10,idle_seconds:300,max_instances:2,concurrency:2,queue_timeout_seconds:10,
        storage:{concurrency:'shared',data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},configuration:{environment:{VERSIONS_LOCAL:'function-value',VERSIONS_PERSIST:'yes'}}}});functions.push(fn);await save();
    aFile=await bundle('A');bFile=await bundle('B');const initial=await current();
    const first=await prepare({token:createToken.token}),same=await prepare({token:createToken.token}),different=await prepare({token:createToken.token,handler:'secondary'});
    a=await upload(first,aFile,{token:createToken.token});assert(a.code_changed&&!a.version_restored);assert.match(a.code_hash,/^[0-9a-f]{64}$/);
    const duplicate=await upload(same,aFile,{token:createToken.token});assert(!duplicate.code_changed);assert.equal(duplicate.revision_id,a.revision_id);
    await upload(different,bFile,{token:createToken.token,status:403});const row=await current();assert.equal(row.active_revision_id,null);assert.equal(row.updated_at,initial.updated_at);
    assert.equal(row.first_published_code_hash,a.code_hash);assert.equal(row.first_promoted_at,null);await invoke({status:409});await invoke({hash:a.code_hash,marker:'A',handler:'primary'});
    evidence.push({first_hash:a.code_hash,revision_id:a.revision_id,duplicate_revision_id:duplicate.revision_id});
  });
  await check('Première promotion : seul A bénéficie de Create, stable et pilote distincts',async()=>{
    b=await publish(bFile,{handler:'secondary',events:pilotEvents});assert(b.code_changed);assert.equal((await current()).active_revision_id,null);
    await mutate(b.code_hash,'promote',{},createToken.token,403);await mutate(a.code_hash,'promote',{},readToken.token,403);
    await mutate(a.code_hash,'promote',{},createToken.token);assert.equal((await current()).active_revision_id,a.revision_id);
    const stable=await invoke({marker:'A',handler:'primary'}),pilot=await invoke({hash:b.code_hash,path:'pilot',marker:'B',handler:'secondary'});
    assert.equal(stable.executed_hash,a.code_hash);assert.equal(pilot.executed_hash,b.code_hash);assert(pilot.counter>stable.counter&&pilot.cacheCounter>stable.cacheCounter);
    const instances=(await call(`/api/functions/${fn.id}/instances`)).items;assert.equal(instances.length,2);assert.deepEqual(new Set(instances.map(row=>row.code_hash)),new Set([a.code_hash,b.code_hash]));
    evidence.push({stable_hash:a.code_hash,pilot_hash:b.code_hash,instances:instances.map(row=>({id:row.id,hash:row.code_hash,revision_id:row.revision_id}))});
  });
  await check('Sélecteurs, portée et événements : refus constants et préflight sans invocation',async()=>{
    const peer=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'peer-access'}});services.push(peer);otherToken=await token(peer,'foreign-service',['read','update']);
    for(const hash of ['',a.code_hash.slice(0,12),a.code_hash.toUpperCase(),a.code_hash+'@'+b.code_hash,'0'.repeat(64)])assert.equal((await invoke({hash,status:404})).error,'version_unavailable');
    await invoke({hash:a.code_hash,token:otherToken.token,status:403});await mutate(a.code_hash,'promote',{},otherToken.token,403);
    const anonymous=await caller.get(`/invoke/${fn.id}@${'0'.repeat(64)}`);assert.equal(anonymous.status(),401);
    await invoke({hash:b.code_hash,status:404});await invoke({hash:a.code_hash,path:'pilot',status:404});
    const before=(await call(`/api/functions/${fn.id}/invocations`)).total;
    const r=await caller.fetch(`/invoke/${fn.id}@${b.code_hash}/pilot`,{method:'OPTIONS',headers:{Origin:'https://app.qualification.invalid','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'x-serverless-token,authorization'}});
    assert.equal(r.status(),204);assert.equal((await call(`/api/functions/${fn.id}/invocations`)).total,before);
    const urls=await call(`/api/functions/${fn.id}/invocation-urls?version=${b.code_hash}`,{token:readToken.token});assert.equal(urls.code_hash,b.code_hash);assert.equal(urls.default_code_hash,a.code_hash);
    assert.equal(urls.total,2);assert.equal(urls.items.length,2);
    assert(urls.items.every(row=>row.urls.length>0&&row.urls.every(entry=>entry.url.endsWith('@'+b.code_hash+'/pilot'))));
  });
  await check('Déduplication : paquet recompressé et renommage sans nouvelle version',async()=>{
    const before=await current(),instances=(await call(`/api/functions/${fn.id}/instances`)).items.map(row=>row.id).sort();
    const file=new URL('recompressed.zip',work).pathname;
    await run('python3',['-B','-c',"import copy,sys,zipfile\nwith zipfile.ZipFile(sys.argv[1]) as source,zipfile.ZipFile(sys.argv[2],'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as target:\n for entry in reversed(source.infolist()):\n  value=copy.copy(entry);value.date_time=(2025,1,1,0,0,0);value.compress_type=zipfile.ZIP_DEFLATED;target.writestr(value,source.read(entry.filename))",aFile,file]);
    assert.notEqual(createHash('sha256').update(await readFile(file)).digest('hex'),a.validation?.archive_sha256 || createHash('sha256').update(await readFile(aFile)).digest('hex'));
    const same=await publish(file);assert(!same.code_changed);assert.equal(same.code_hash,a.code_hash);assert.equal(same.revision_id,a.revision_id);
    assert.equal((await current()).updated_at,before.updated_at);assert.deepEqual((await call(`/api/functions/${fn.id}/instances`)).items.map(row=>row.id).sort(),instances);
    await call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(before.updated_at)},body:{name:'renamed-release-flow',config:before.config}});
    const renamed=await publish(aFile);assert.equal(renamed.code_hash,a.code_hash);assert(!renamed.code_changed);assert.equal((await versions()).total,2);
  });
  await check('Promotion et rollback : descripteur sélectionné, marqueur initial inchangé',async()=>{
    await mutate(b.code_hash,'promote');const promoted=await current();assert.equal(promoted.config.handler,'function-versions.secondary');
    await invoke({path:'pilot',marker:'B',handler:'secondary'});await invoke({hash:a.code_hash,marker:'A',handler:'primary'});
    await mutate(a.code_hash,'promote');await invoke({marker:'A',handler:'primary'});const before=await current();
    const same=await mutate(a.code_hash,'promote');assert.equal(same.changed,false);assert.equal((await current()).updated_at,before.updated_at);
    assert.equal((await current()).first_promoted_at,promoted.first_promoted_at);
  });
  await check('Minimum=maximum=1 : une instance prête cède sa place au pilote',async()=>{
    await mutate(b.code_hash,'promote');await configure({min_instances:1,max_instances:1,concurrency:1,idle_seconds:300});
    await until(async()=>{const rows=(await call(`/api/functions/${fn.id}/instances`)).items;return rows.length===1&&rows[0].code_hash===b.code_hash&&rows[0].state==='ready';});
    const pilot=await invoke({hash:a.code_hash,marker:'A',handler:'primary'});assert.equal(pilot.executed_hash,a.code_hash);
    await until(async()=>{const rows=(await call(`/api/functions/${fn.id}/instances`)).items;assert(rows.length<=1);return rows.length===1&&rows[0].code_hash===b.code_hash&&rows[0].state==='ready';});
  });
  await check('Archivage, remplacement et désactivation : Create ne retrouve pas sa promotion',async()=>{
    const stamp=(await current()).first_promoted_at;
    await mutate(b.code_hash,'archive',{},updateToken.token,409);await mutate(b.code_hash,'archive',{replacement_code_hash:a.code_hash});
    assert.equal((await invoke({hash:b.code_hash,path:'pilot',status:404})).error,'version_unavailable');await mutate(b.code_hash,'restore');
    await invoke({hash:b.code_hash,path:'pilot',marker:'B',handler:'secondary'});
    await mutate(a.code_hash,'archive',{disable_default:true});assert.equal((await current()).active_revision_id,null);await mutate(a.code_hash,'restore');
    await mutate(a.code_hash,'promote',{},createToken.token,403);assert.equal((await current()).first_promoted_at,stamp);await invoke({status:409});
    await mutate(b.code_hash,'promote');
  });
  await check('Attente et appel admis : archive refuse la file, delete attend le consommateur',async()=>{
    await configure({min_instances:0,idle_seconds:0,max_instances:1,concurrency:1});
    const running=tracked(invoke({hash:b.code_hash,path:'pilot',marker:'B',handler:'secondary',delay:5000}));
    await until(async()=>(await call(`/api/functions/${fn.id}/invocations`)).items.some(row=>row.resolved_code_hash===b.code_hash&&row.state==='running'&&row.handler_started));
    const queued=tracked(invoke({hash:a.code_hash,status:404}));
    await until(async()=>(await call(`/api/functions/${fn.id}/invocations`)).items.some(row=>row.requested_code_hash===a.code_hash&&row.state==='queued'));
    await mutate(a.code_hash,'archive');assert.equal((await observed(queued)).error,'version_unavailable');
    const removed=await mutate(b.code_hash,'delete',{disable_default:true});assert(removed.cleanup_pending);await invoke({hash:b.code_hash,path:'pilot',status:404});
    const admitted=await observed(running);assert.equal(admitted.executed_hash,b.code_hash);
    await until(async()=>(await versions()).items.find(row=>row.code_hash===b.code_hash).stored_bytes===0);
    await mutate(a.code_hash,'restore');evidence.push({completed_admitted_invocation:admitted.invocation_id,deleted_hash:b.code_hash});
  });
  await check('Réimportation explicite : même tag, nouvelle conservation, date initiale',async()=>{
    const before=(await versions()).items.find(row=>row.code_hash===b.code_hash);
    await publish(bFile,{handler:'secondary',events:pilotEvents,status:409});
    await publish(bFile,{handler:'secondary',events:pilotEvents,restore:a.code_hash,status:422});
    const restored=await publish(bFile,{handler:'secondary',events:pilotEvents,restore:b.code_hash});assert(!restored.code_changed&&restored.version_restored);assert.equal(restored.code_hash,b.code_hash);assert.notEqual(restored.revision_id,b.revision_id);
    const after=(await versions()).items.find(row=>row.code_hash===b.code_hash);assert.equal(after.created_at,before.created_at);assert.equal(after.revision_count,2);
    await invoke({hash:b.code_hash,path:'pilot',marker:'B',handler:'secondary'});assert.equal((await current()).active_revision_id,null);
  });
  await check('Vingt hashes conservés : doublon admis, nouveau contenu refusé',async()=>{
    for(const name of 'CDEFGHIJKLMNOPQRST'){const file=await bundle(name);const result=await publish(file);assert(result.code_changed);}
    assert.equal((await versions()).items.filter(row=>row.state!=='deleted').length,20);
    const duplicate=await publish(aFile);assert(!duplicate.code_changed);assert.equal(duplicate.code_hash,a.code_hash);
    await publish(await bundle('U'),{status:409});assert.equal((await current()).active_revision_id,null);
    const disposable=(await versions()).items.find(row=>row.code_hash!==a.code_hash&&row.code_hash!==b.code_hash&&row.state==='available');await mutate(disposable.code_hash,'delete');
  });
  await check('Uploads identiques réellement concurrents : un seul hash et artefact conservé',async()=>{
    const file=await bundle('concurrent',3000),first=await prepare(),second=await prepare();
    const one=tracked(upload(first,file)),two=tracked(upload(second,file));
    const observedStates=await until(async()=>{const rows=[await call(`/api/deployments/${first.id}`),await call(`/api/deployments/${second.id}`)];return rows.every(row=>row.state==='validating')?rows.map(row=>({id:row.id,state:row.state})):null;});
    const results=[await observed(one),await observed(two)];assert.equal(results.filter(row=>row.code_changed).length,1);assert.equal(results[0].code_hash,results[1].code_hash);assert.equal(results[0].revision_id,results[1].revision_id);
    const version=(await versions()).items.find(row=>row.code_hash===results[0].code_hash);assert.equal(version.revision_count,1);evidence.push({simultaneous_validating:observedStates,code_hash:version.code_hash,revision_id:version.revision_id});
    const native=await artifacts();
    for(const candidate of [first,second]){
      const row=native.candidates.find(row=>row.id===candidate.id);assert(row);assert.equal(row.reserved_bytes,0);assert.equal(row.configuration_present,0);assert.equal(row.state,'published');
      assert.equal(native.paths[candidate.id].exists,candidate.id===version.revision_id);
    }
    assert(native.paths[version.revision_id].archive_exists&&native.paths[version.revision_id].code_exists);
    evidence.push({deduplication_native:native,canonical_revision_id:version.revision_id});
  });
  await check('Import réel refusé : aucune version supplémentaire ni activation',async()=>{
    const before=await versions();await publish(aFile,{handler:'missing',status:422});const after=await versions();assert.equal(after.total,before.total);assert.equal(after.active_code_hash,null);
    const history=(await call(`/api/functions/${fn.id}/invocations?limit=100`)).items;
    assert(history.some(row=>row.requested_code_hash===a.code_hash&&row.resolved_code_hash===a.code_hash&&row.state==='succeeded'));
    assert(history.some(row=>row.requested_code_hash===a.code_hash&&row.state==='rejected'&&row.error_code==='version_unavailable'));
  });
  completed=true;
}catch(error){if(!checks.some(row=>row.status==='failed'))checks.push({name:'Préparation ou fin',status:'failed',error:error.name});console.error(error.name,error.message);process.exitCode=1;}
finally{
  await Promise.all(pending);
  for(const owned of functions)try{await purge(owned);}catch(error){cleanupErrors.push({step:'function-purge',id:owned.id,error:error.name,message:error.message});}
  for(const row of tokens)try{await call(`/api/tokens/${row.id}/revoke`,{method:'POST'});}catch(error){cleanupErrors.push({step:'token-revoke',id:row.id,error:error.name});}
  for(const row of services)try{await call(`/api/services/${row.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service-delete',id:row.id,error:error.name});}
  if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace-delete',id:namespace.id,error:error.name});}
  if(work)try{await rm(work,{recursive:true});}catch(error){cleanupErrors.push({step:'local-files',error:error.name});}
  await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();if(!completed||!cleanup)process.exitCode=1;
}
