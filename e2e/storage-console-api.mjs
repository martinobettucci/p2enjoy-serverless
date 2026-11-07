// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md
// @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url);
const report=new URL('storage-console-api.json',output),checks=[],cleanupErrors=[],functions=[],services=[],operations=[],pending=[];
const prefix='storage-console-api-'+randomUUID().slice(0,8),secret='storage-private-'+randomUUID();
let admin,caller,session,namespace,work,completed=false,cleanup=false;
async function save(){const temporary=new URL('storage-console-api.pending',output);await writeFile(temporary,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length,skipped:0,checks,cleanup,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,function_ids:functions.map(row=>row.id),operation_ids:operations},null,2)+'\n');await rename(temporary,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function call(url,{method='GET',body,bytes,token,anonymous=false,headers={},status=200}={}){
  const result=await (token||anonymous?caller:admin).fetch(url,{method,data:bytes??body,headers:{
    ...(token?{'X-Serverless-Token':token}:anonymous?{}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),
    ...(bytes?{'Content-Type':'application/zip'}:{}),...headers,
  }});
  assert([status].flat().includes(result.status()),`${method} ${url.split('?')[0]}: ${result.status()} au lieu de ${status}`);
  const text=await result.text();assert(!text.includes(secret),'Secret exposé');return JSON.parse(text);
}
async function until(action,message){const end=Date.now()+120000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,200));}assert.fail(message);}
async function current(fn){return call(`/api/functions/${fn.id}`);}
async function token(service,rights,extra={}){return call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:randomUUID(),rights,...extra}});}
async function create(service,name,enabled=true){const row=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'storage-console.handler',cpu:.2,memory_mib:256,idle_seconds:30,timeout_seconds:10,storage:{data:{enabled,quota_mib:8},cache:{enabled,quota_mib:8}}},configuration:{environment:{PUBLIC_LABEL:'storage'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}}});functions.push(row);return row;}
async function publish(fn,archive){const row=await current(fn);const candidate=await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:archive.handler}});await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive.bytes});return candidate;}
async function command(fn,kind,credential,extra={}){
  const row=await call(kind==='purge'?`/api/archives/${fn.id}`:`/api/functions/${fn.id}`),identifier=randomUUID();operations.push(identifier);
  const options={method:'POST',status:[200,202],token:credential,body:{operation_id:identifier,...(kind==='purge'?{confirm_name:row.name}:{})},headers:{'If-Match':String(row.updated_at)},...extra};
  const result=await call(kind==='purge'?`/api/archives/${fn.id}/purge`:`/api/functions/${fn.id}/cache-clear`,options);
  return {result,options,identifier,version:row.updated_at};
}
async function terminal(id,token){return until(async()=>{const row=await call(`/api/storage-operations/${id}`,{token});if(row.state==='aborted')assert.fail('Commande abandonnée');return row.state==='completed'?row:null;},'Commande non terminée');}
async function settle(fn){await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'Archivage non confirmé');}

await mkdir(output,{recursive:true,mode:0o700});await save();
try {
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',output),'utf8')),timeout:180000});
  caller=await request.newContext({baseURL:base,timeout:180000});session=await call('/api/session');assert(session.authenticated,'Session SSO réelle requise');
  work=await mkdtemp(new URL('storage-console-api-',output).pathname);const archive=await publicationArchive(work,'storage','storage-console.handler');
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});
  const service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'storage'}});services.push(service);
  const foreign=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'foreign'}});services.push(foreign);
  const fn=await create(service,'storage-files'),peer=await create(service,'preserved-files'),empty=await create(service,'without-volumes',false);
  const read=await token(service,['read']),update=await token(service,['update']),createOnly=await token(service,['create']),remove=await token(service,['delete']);
  const scoped=await token(service,['read','update'],{function_ids:[peer.id]}),other=await token(foreign,['read','update']);
  const invoke=(fn,body)=>call(`/invoke/${fn.id}`,{method:body?'POST':'GET',body,token:read.token});
  let candidate,cleared;
  await check('Stockage et archives : authentification, CRUD, portée et CSRF',async()=>{
    await call(`/api/functions/${fn.id}/storage`,{anonymous:true,status:401});
    await call('/api/archives',{anonymous:true,status:401});
    for(const credential of [createOnly,update,remove])await call(`/api/functions/${fn.id}/storage`,{token:credential.token,status:403});
    for(const credential of [read,update,createOnly,remove,scoped,other])await call('/api/archives',{token:credential.token,status:403});
    for(const credential of [scoped,other])await call(`/api/functions/${fn.id}/storage`,{token:credential.token,status:403});
    assert((await call(`/api/functions/${fn.id}/storage`,{token:read.token})).storage.available);
    const options={method:'POST',body:{operation_id:randomUUID()},headers:{'If-Match':String(fn.updated_at)}};
    for(const credential of [read,createOnly,remove,scoped,other])await call(`/api/functions/${fn.id}/cache-clear`,{...options,token:credential.token,status:403});
    await call(`/api/functions/${fn.id}/cache-clear`,{...options,headers:{...options.headers,'X-CSRF-Token':'invalid'},status:403});
  });
  await check('Versions obligatoires, schéma strict et prérequis de purge',async()=>{
    const path=`/api/functions/${fn.id}/cache-clear`;
    await call(path,{method:'POST',body:{operation_id:randomUUID()},status:428});
    await call(path,{method:'POST',body:{operation_id:randomUUID()},headers:{'If-Match':'0'},status:409});
    for(const body of [{operation_id:randomUUID(),unknown:true},{},{operation_id:'not-an-uuid'},{operation_id:42},[]])
      await call(path,{method:'POST',body,headers:{'If-Match':String(fn.updated_at)},status:422});
    assert.equal((await current(fn)).updated_at,fn.updated_at);
    const unchanged=await call(`/api/functions/${fn.id}/storage`);assert.equal(unchanged.storage_operation,null);assert.equal(unchanged.command,null);
    await call(`/api/archives/${fn.id}/purge`,{method:'POST',body:{operation_id:randomUUID(),confirm_name:fn.name},headers:{'If-Match':String(fn.updated_at)},status:409});
  });
  await check('Vrais fichiers Docker : cache vidé, données et révision conservées',async()=>{
    candidate=await publish(fn,archive);await publish(peer,archive);
    const before=await invoke(fn,{data:'permanent-record',cache:'old-cache'});await invoke(peer,{data:'peer-data',cache:'peer-cache'});
    const observed=await call(`/api/functions/${fn.id}/storage`);assert(observed.storage.volumes.cache.quota_bytes===8*1024**2);
    cleared=await command(fn,'clear-cache',update.token);const done=await terminal(cleared.identifier,update.token);
    assert(done.result_version>cleared.version);const after=await invoke(fn);assert.equal(after.data,before.data);assert.equal(after.cache,null);assert.equal(after.revision,before.revision);
    const untouched=await invoke(peer);assert.equal(untouched.data,'peer-data');assert.equal(untouched.cache,'peer-cache');
    await call(`/api/storage-operations/${cleared.identifier}`,{token:read.token,status:403});
  });
  await check('Rejeu corrélé après reconstruction et conflits de commande',async()=>{
    await invoke(fn,{cache:'rebuilt-cache'});
    const replay=await call(`/api/functions/${fn.id}/cache-clear`,{...cleared.options,status:200});assert.equal(replay.state,'completed');
    assert.equal((await invoke(fn)).cache,'rebuilt-cache');
    await call(`/api/functions/${peer.id}/cache-clear`,{...cleared.options,headers:{'If-Match':String((await current(peer)).updated_at)},status:409});
    assert.equal((await invoke(peer)).cache,'peer-cache');
    await call(`/api/functions/${fn.id}/cache-clear`,{...cleared.options,headers:{'If-Match':String((await current(fn)).updated_at)},status:409});
  });
  await check('Invocation active : refus et abandon durable sans effacement',async()=>{
    const invocation=invoke(fn,{delay_ms:4000}).then(value=>({value}),error=>({error}));pending.push(invocation);
    await until(async()=>(await call(`/api/functions/${fn.id}/invocations`)).items.some(row=>row.state==='running'),'Invocation active non observée');
    const rejected=await command(fn,'clear-cache',update.token,{status:409});
    const outcome=await invocation;if(outcome.error)throw outcome.error;
    assert.equal((await call(`/api/storage-operations/${rejected.identifier}`,{token:update.token})).state,'aborted');
    assert.equal((await invoke(fn)).cache,'rebuilt-cache');assert.equal((await current(fn)).storage_operation,null);
  });
  await check('Cache absent et cache désactivé conservant son allocation',async()=>{
    const absent=await command(empty,'clear-cache',update.token);await terminal(absent.identifier,update.token);
    let row=await current(fn);await call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,storage:{...row.config.storage,cache:{...row.config.storage.cache,enabled:false}}}}});
    const disabled=await command(fn,'clear-cache',update.token);await terminal(disabled.identifier,update.token);
    const snapshot=await call(`/api/functions/${fn.id}/storage`);assert.equal(snapshot.storage.volumes.cache.enabled,false);assert.equal(snapshot.storage.volumes.cache.quota_bytes,8*1024**2);
    row=await current(fn);await call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,storage:{...row.config.storage,cache:{...row.config.storage.cache,enabled:true}}}}});
    assert.equal((await invoke(fn)).cache,null);assert.equal((await invoke(fn)).data,'permanent-record');
  });
  await check('Archivage consultable et purge réservée à l’administrateur',async()=>{
    await call(`/api/functions/${fn.id}`,{method:'DELETE'});await settle(fn);
    const row=await call(`/api/archives/${fn.id}`);assert.equal(row.storage.state,'archived');assert(row.artifact_bytes>0);assert.equal(row.revision_count,1);
    for(const credential of [read,update,remove,createOnly])await call(`/api/archives/${fn.id}`,{token:credential.token,status:403});
    const options={method:'POST',body:{operation_id:randomUUID(),confirm_name:row.name},headers:{'If-Match':String(row.updated_at)}};
    for(const credential of [read,update,remove,createOnly])await call(`/api/archives/${fn.id}/purge`,{...options,token:credential.token,status:403});
    await call(`/api/archives/${fn.id}/purge`,{...options,headers:{...options.headers,'X-CSRF-Token':'invalid'},status:403});
    await call(`/api/archives/${fn.id}/purge`,{...options,headers:{},status:428});
    await call(`/api/archives/${fn.id}/purge`,{...options,body:{...options.body,confirm_name:'wrong'},status:422});
  });
  await check('Purge réelle du code et des volumes, reçu terminal et voisin intact',async()=>{
    const purged=await command(fn,'purge');await terminal(purged.identifier);
    const row=await call(`/api/archives/${fn.id}`);assert(row.purged_at);assert.equal(row.artifact_bytes,0);assert.equal(row.revision_count,0);assert.equal(row.storage.state,'purged');assert.deepEqual(row.storage.volumes,{});
    assert.equal((await call(`/api/deployments/${candidate.id}`)).validation,null);
    await call(`/api/functions/${fn.id}`,{status:404});
    assert.equal((await call(`/api/archives/${fn.id}/purge`,{...purged.options,status:200})).id,purged.identifier);
    await command(fn,'purge',undefined,{status:409});
    assert.equal((await invoke(peer)).data,'peer-data');assert.equal((await invoke(peer)).cache,'peer-cache');
  });
  await check('Catalogue paginé et conservation après suppression des parents',async()=>{
    for(const row of [peer,empty]){await call(`/api/functions/${row.id}`,{method:'DELETE'});await settle(row);}
    const first=await call(`/api/archives?service_id=${service.id}&state=all&limit=2`),second=await call(`/api/archives?service_id=${service.id}&state=all&limit=2&offset=2`);
    assert.equal(first.total,3);assert.equal(first.items.length,2);assert.equal(second.items.length,1);assert.equal(new Set([...first.items,...second.items].map(row=>row.id)).size,3);
    for(const row of services)await call(`/api/services/${row.id}`,{method:'DELETE'});
    await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});
    const kept=await call(`/api/archives/${peer.id}`);assert.equal(kept.namespace_id,namespace.id);assert.equal(kept.service_id,service.id);assert.equal(kept.name,peer.name);
    const operation=await command(peer,'purge');await terminal(operation.identifier);
    assert.equal((await call(`/api/storage-operations/${cleared.identifier}`)).state,'completed');
  });
  completed=true;
} finally {
  await Promise.all(pending);
  if(admin&&session?.authenticated) {
    for(const fn of functions)try{
      const response=await admin.get(`/api/functions/${fn.id}`);
      if(response.status()===200)await call(`/api/functions/${fn.id}`,{method:'DELETE'});else assert.equal(response.status(),404);
      await settle(fn);const row=await call(`/api/archives/${fn.id}`);
      if(!row.purged_at){const action=await command(fn,'purge');await terminal(action.identifier);}
      const finished=await call(`/api/archives/${fn.id}`);assert(finished.purged_at&&finished.artifact_bytes===0&&!finished.storage_operation);
    }catch(error){cleanupErrors.push({function_id:fn.id,error:error.name});}
    for(const service of services)try{const response=await admin.get(`/api/services/${service.id}`);if(response.status()===200)await call(`/api/services/${service.id}`,{method:'DELETE'});else assert.equal(response.status(),404);}catch(error){cleanupErrors.push({service_id:service.id,error:error.name});}
    if(namespace)try{const response=await admin.get(`/api/namespaces/${namespace.id}`);if(response.status()===200)await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});else assert.equal(response.status(),404);}catch(error){cleanupErrors.push({namespace_id:namespace.id,error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});await admin?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();assert.deepEqual(cleanupErrors,[]);
}
