// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#autorité-persistante-et-migration
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles | docs/SCHEMA.md#autorité-des-versions-et-promotions
// Prepare on the genuine deployed 007, then observe the real 008 migration.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,rename} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';

const run=promisify(execFile),base='https://serverless.lelabs.tech',root=new URL('../',import.meta.url);
const out=new URL('../.local/e2e/',import.meta.url),privateFile=new URL('function-versions-upgrade-private.json',out);
const phase=process.argv[2];assert(['prepare','verify','persist','cleanup'].includes(phase),'explicit_upgrade_phase_required');
const reportFile=new URL(`function-versions-upgrade-${phase}.json`,out),checks=[],evidence=[],cleanupErrors=[];
let state,admin,caller,session,completed=false;
await mkdir(out,{recursive:true,mode:0o700});
async function persist(){const pending=new URL('function-versions-upgrade-private.pending',out);await writeFile(pending,JSON.stringify(state)+'\n',{mode:0o600});await rename(pending,privateFile);}
async function save(){await writeFile(reportFile,JSON.stringify({target:base,phase,completed,skipped:0,checks,evidence,cleanup_errors:cleanupErrors,
  namespace_id:state?.namespace?.id,function_ids:state?.functions?.map(row=>row.id)},null,2)+'\n',{mode:0o600});}
async function check(name,action){try{await action();checks.push({name,status:'passed'});await save();console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function call(path,{method='GET',body,bytes,token,headers={},status=200}={}){
  const r=await (token?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),
    ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);
  const text=await r.text();assert(!state?.secret || !text.includes(state.secret),'secret_exposed');return JSON.parse(text);
}
async function until(action){const deadline=Date.now()+120000;while(Date.now()<deadline){const row=await action();if(row)return row;await new Promise(resolve=>setTimeout(resolve,200));}assert.fail('real_lifecycle_deadline');}
async function idle(fn){await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length);}
async function bundle(value){const folder=new URL(`code-${value}/`,state.work);await mkdir(folder);
  await cp(new URL('../qualification/artifacts/function-versions.cjs',import.meta.url),new URL('function-versions.cjs',folder));
  await writeFile(new URL('version-marker.json',folder),JSON.stringify({value}));
  const config=new URL('serverless.yml',folder);await writeFile(config,JSON.stringify({service:'version-upgrade',provider:{name:'p2enjoy',runtime:'nodejs24.x'},
    functions:{probe:{handler:'function-versions.primary'}},package:{patterns:['!**','function-versions.cjs','version-marker.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',config.pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',folder),'utf8'));
  return new URL('.serverless-p2/'+descriptor.artifacts.probe.file,folder).pathname;
}
async function publish(fn,file){const current=await call(`/api/functions/${fn.id}`),prepared=await call(`/api/functions/${fn.id}/code-deployments`,
  {method:'POST',status:201,headers:{'If-Match':String(current.updated_at)},body:{deployment_id:randomUUID(),handler:'function-versions.primary'}});
  const result=await call(`/api/deployments/${prepared.id}/artifact`,{method:'PUT',bytes:await readFile(file)});
  assert.equal(result.state,'published');assert(result.validation.valid&&result.validation.container_removed);
  const revision=(await call(`/api/functions/${fn.id}/revisions?limit=100`)).items.find(row=>row.id===result.revision_id);assert(revision);
  state.revisions.push(revision);await persist();return revision;
}
async function invoke(fn,marker,{hash,handler='primary',expectedHeader=false}={}){
  const r=await caller.get(`/invoke/${fn.id}${hash?'@'+hash:''}`,{headers:{'X-Serverless-Token':state.read.token}});assert.equal(r.status(),200);
  const body=await r.json();assert.equal(body.marker,marker);assert.equal(body.handler,handler);
  assert.equal(body.common,'service-value');assert.equal(body.local,'function-value');
  assert.equal(body.secret_sha256,createHash('sha256').update(state.secret).digest('hex'));
  if(expectedHeader)assert.equal(r.headers()['x-serverless-code-hash'],hash || state.hashA);
  return body;
}
async function purge(fn){
  await idle(fn);await call(`/api/functions/${fn.id}`,{method:'DELETE'});
  await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation);
  const row=await call(`/api/archives/${fn.id}`),op=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],
    headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
  await until(async()=>{const operation=await call(`/api/storage-operations/${op.id}`);assert.notEqual(operation.state,'aborted');return operation.state==='completed';});
  const archive=await call(`/api/archives/${fn.id}`);assert.equal(archive.artifact_bytes,0);assert.equal(archive.revision_count,0);
  evidence.push({purged_function_id:fn.id,operation_id:op.id});
}
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});
  caller=await request.newContext({baseURL:base,timeout:180000});session=await call('/api/session');assert.equal(session.authenticated,true,'real_sso_session_required');
  if(phase==='prepare'){
    await assert.rejects(readFile(privateFile),error=>error.code==='ENOENT','existing_upgrade_fixture_must_not_be_overwritten');
    state={secret:'version-upgrade-private-'+randomUUID(),functions:[],revisions:[],tokens:[],work:new URL((await mkdtemp(new URL('function-versions-upgrade-',out).pathname))+'/','file:').href};await persist();
    await check('007 : vrais alias A/A/B, rollback, données et cache avant migration',async()=>{
      state.namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:'version-upgrade-'+randomUUID().slice(0,8)}});await persist();
      state.service=await call(`/api/namespaces/${state.namespace.id}/services`,{method:'POST',status:201,body:{name:'version-upgrade'}});await persist();
      state.service=await call(`/api/services/${state.service.id}/configuration`,{method:'PUT',body:{environment:{VERSIONS_COMMON:'service-value'},secrets:{VERSIONS_SECRET:state.secret}}});
      state.read=await call(`/api/services/${state.service.id}/tokens`,{method:'POST',status:201,body:{name:'observe-upgrade-code',rights:['read']}});state.tokens.push(state.read);await persist();
      state.fn=await call(`/api/services/${state.service.id}/functions`,{method:'POST',status:201,body:{name:'persistent-version-history',
        config:{handler:'function-versions.primary',memory_mib:128,idle_seconds:0,timeout_seconds:10,storage:{data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}},
        configuration:{environment:{VERSIONS_LOCAL:'function-value',VERSIONS_PERSIST:'yes'}}}});state.functions.push(state.fn);await persist();
      state.aFile=await bundle('A');state.bFile=await bundle('B');
      const a=await publish(state.fn,state.aFile),alias=await publish(state.fn,state.aFile),b=await publish(state.fn,state.bFile);
      assert.notEqual(a.id,alias.id);assert.equal(a.code_hash,alias.code_hash);assert.notEqual(a.code_hash,b.code_hash);
      state.hashA=a.code_hash;state.hashB=b.code_hash;state.active=alias.id;await persist();
      const before=await invoke(state.fn,'B'),current=await call(`/api/functions/${state.fn.id}`);
      await call(`/api/functions/${state.fn.id}/rollback`,{method:'POST',headers:{'If-Match':String(current.updated_at)},body:{revision_id:alias.id}});
      const after=await invoke(state.fn,'A');assert.equal(after.counter,before.counter+1);assert.equal(after.cacheCounter,before.cacheCounter+1);
      state.counter=after.counter;state.cacheCounter=after.cacheCounter;await idle(state.fn);await persist();
      evidence.push({revision_ids:[a.id,alias.id,b.id],hash_a:state.hashA,hash_b:state.hashB,active_revision_id:state.active,counter:state.counter,cache_counter:state.cacheCounter});
    });
  }else{
    state=JSON.parse(await readFile(privateFile,'utf8'));
    if(phase==='verify')await check('008 : cible et alias conservés, états et première promotion historiques durables',async()=>{
      const fn=await call(`/api/functions/${state.fn.id}`);assert.equal(fn.active_revision_id,state.active);assert.equal(fn.first_published_code_hash,state.hashA);assert(fn.first_promoted_at>0);
      const versions=await call(`/api/functions/${fn.id}/versions`);assert.equal(versions.total,2);assert.equal(versions.active_code_hash,state.hashA);
      const a=versions.items.find(row=>row.code_hash===state.hashA);assert.equal(a.revision_count,2);assert.equal(a.revision_id,state.active);assert(a.active&&a.state==='available');
      const revisions=(await call(`/api/functions/${fn.id}/revisions?limit=100`)).items;
      for(const previous of state.revisions){const actual=revisions.find(row=>row.id===previous.id);assert(actual);assert.deepEqual(actual,{...previous,active:previous.id===state.active});}
      const first=await invoke(fn,'A',{expectedHeader:true}),second=await invoke(fn,'B',{hash:state.hashB,expectedHeader:true});
      assert.equal(first.counter,state.counter+1);assert.equal(second.counter,first.counter+1);assert.equal(second.cacheCounter,state.cacheCounter+2);
      state.counter=second.counter;state.cacheCounter=second.cacheCounter;await idle(fn);await persist();
      evidence.push({versions,first_promoted_at:fn.first_promoted_at,counter:state.counter,cache_counter:state.cacheCounter});
    });
    if(phase==='persist')await check('008 : redémarrage réel, code épinglé et données/cache conservés',async()=>{
      const fn=await call(`/api/functions/${state.fn.id}`);assert.equal(fn.active_revision_id,state.active);
      const body=await invoke(fn,'A',{hash:state.hashA,expectedHeader:true});assert.equal(body.counter,state.counter+1);assert.equal(body.cacheCounter,state.cacheCounter+1);
      await idle(fn);evidence.push({active_revision_id:fn.active_revision_id,counter:body.counter,cache_counter:body.cacheCounter});
    });
    if(phase==='cleanup')await check('Nettoyage public : purge confirmée et parents supprimés',async()=>{
      for(const fn of state.functions)await purge(fn);
      await call(`/api/services/${state.service.id}`,{method:'DELETE'});await call(`/api/namespaces/${state.namespace.id}`,{method:'DELETE'});
      const work=new URL(state.work);assert.equal(new URL('../',work).href,out.href);assert.match(work.pathname.split('/').filter(Boolean).at(-1),/^function-versions-upgrade-[A-Za-z0-9]+$/);
      await rm(work,{recursive:true});state.cleaned=true;await persist();
    });
  }
  completed=true;
}catch(error){if(!checks.some(row=>row.status==='failed'))checks.push({name:'Préparation ou fin',status:'failed',error:error.name});console.error(error.name,error.message);process.exitCode=1;}
finally{await admin?.dispose();await caller?.dispose();await save();if(!completed)process.exitCode=1;}
