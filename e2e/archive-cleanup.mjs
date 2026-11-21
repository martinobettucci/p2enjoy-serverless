// @spec docs/BACKLOG.md#sls-106 | docs/REGRESSION_ARTIFACT_CLEANUP.md#diagnostic-recoupé-et-décision-avant-code
// @verifies docs/BACKLOG.md#sls-106 | docs/REGRESSION_ARTIFACT_CLEANUP.md#correction-bornée
// Actual code publication, Docker writes, HTTP archive and complete public purge.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';
import {purgeStorageArchive} from './storage-archives.mjs';
const root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),base='https://serverless.lelabs.tech',run=promisify(execFile);
const prefix='invocation-'+randomUUID().slice(0,8),report=new URL('archive-cleanup-'+randomUUID()+'.json',out),checks=[],evidence=[],cleanupErrors=[];
let admin,caller,session,namespace,service,fn,reader,work,completed=false,cleanup=false,archived=false,purgeStarted=false,purgeResult;
async function save(){const pending=new URL(report.pathname+'.pending','file:');const text=JSON.stringify({completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,evidence,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,service_id:service?.id,function_id:fn?.id,token_id:reader?.id},null,2)+'\n';if(reader)assert(!text.includes(reader.token));await writeFile(pending,text,{mode:0o600});await rename(pending,report);}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){const response=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});assert([status].flat().includes(response.status()),method+' '+path+':'+response.status());return response.json();}
async function until(action,label,seconds=90){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,250));}assert.fail(label);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function archive(){if(!archived){await until(async()=>!(await api('/api/functions/'+fn.id+'/instances')).total,'instances_not_retired');await api('/api/functions/'+fn.id,{method:'DELETE'});archived=true;}}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
 admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:120000});caller=await request.newContext({baseURL:base,timeout:120000});session=await api('/api/session');assert(session.authenticated);
 await check('Publication pilote puis promotion et fichiers data/cache écrits par le vrai handler Docker',async()=>{
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix},status:201});service=await api('/api/namespaces/'+namespace.id+'/services',{method:'POST',body:{name:'archive-cleanup-original'},status:201});await save();
  fn=await api('/api/services/'+service.id+'/functions',{method:'POST',status:201,body:{name:'code-data-cache-cleanup',config:{handler:'scheduled-storage.handler',runtime:'node24',cpu:.05,memory_mib:128,timeout_seconds:10,idle_seconds:0,min_instances:0,max_instances:1,concurrency:1,queue_timeout_seconds:5,storage:{concurrency:'exclusive',data:{enabled:true,quota_mib:2},cache:{enabled:true,quota_mib:2}}}}});await save();
  work=new URL((await mkdtemp(new URL('archive-cleanup-code-',out).pathname))+'/','file:');await cp(new URL('../qualification/artifacts/scheduled-storage.cjs',import.meta.url),new URL('scheduled-storage.cjs',work));
  await writeFile(new URL('serverless.yml',work),JSON.stringify({service:'archive-cleanup-original',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'scheduled-storage.handler'}},package:{patterns:['!**','scheduled-storage.cjs']}}));await run('python3',['-B','-m','adapter','package','--config',new URL('serverless.yml',work).pathname],{cwd:root.pathname});
  const manifest=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',work),'utf8')),bytes=await readFile(new URL('.serverless-p2/'+manifest.artifacts.probe.file,work));
  const current=await api('/api/functions/'+fn.id),candidate=await api('/api/functions/'+fn.id+'/code-deployments',{method:'POST',status:201,headers:{'If-Match':String(current.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-storage.handler',events:{http:[{path:'cleanup',methods:['POST'],implicit:true}]}}});
  const published=await api('/api/deployments/'+candidate.id+'/artifact',{method:'PUT',bytes});assert.equal(published.state,'published');assert.match(published.code_hash,/^[0-9a-f]{64}$/);assert(published.validation.valid&&published.validation.container_removed);assert.equal((await api('/api/functions/'+fn.id)).active_revision_id,null);
  const beforePromotion=await api('/api/functions/'+fn.id);await api('/api/functions/'+fn.id+'/versions/'+published.code_hash+'/promote',{method:'POST',headers:{'If-Match':String(beforePromotion.updated_at)}});
  reader=await api('/api/services/'+service.id+'/tokens',{method:'POST',status:201,body:{name:'write-cleanup-witness',rights:['read'],function_ids:[fn.id]}});
  const payload={data:'archive-cleanup-data-'+fn.id,cache:'archive-cleanup-cache-'+fn.id},response=await caller.post('/invoke/'+fn.id,{headers:{'X-Serverless-Token':reader.token},data:payload});assert.equal(response.status(),200);const value=await response.json();assert.equal(value.data,payload.data);assert.equal(value.cache,payload.cache);assert.equal(value.id,response.headers()['x-serverless-request-id']);assert.equal(value.trigger,'http');
  evidence.push({scenario:'docker-records-written',function_id:fn.id,revision_id:published.revision_id,code_hash:published.code_hash,validation:published.validation,invocation_id:value.id,response:value});
 });
 await check('Suppression HTTP : code et deux volumes conservés avant la purge complète',async()=>{
  await archive();const value=await api('/api/archives/'+fn.id);assert.equal(value.namespace_id,namespace.id);assert.equal(value.purged_at,null);assert(value.artifact_bytes>0&&value.revision_count===1);assert(value.storage.available&&value.storage.registered&&value.storage.state==='archived');assert(value.storage.volumes.data.enabled&&value.storage.volumes.cache.enabled);assert.equal(value.storage.leases,0);evidence.push({scenario:'archive-retains-code-and-volumes',archive:value});
 });
 await check('Helper : reçu public terminé, code/volumes physiquement absents et relecture idempotente',async()=>{
  purgeStarted=true;purgeResult=await purgeStorageArchive(fn.id,namespace.id);evidence.push({scenario:'public-purge',result:purgeResult});assert(purgeResult.purged&&purgeResult.physical.completed);assert.equal(purgeResult.physical.purge_commands,1);
  const repeated=await purgeStorageArchive(fn.id,namespace.id);assert.equal(repeated.operation_id,purgeResult.operation_id);assert.equal(repeated.physical.purge_commands,1);assert.deepEqual(repeated.physical.physical,purgeResult.physical.physical);evidence.push({scenario:'same-completed-purge',result:repeated});
 });
 completed=true;
}catch(error){evidence.push({scenario:'campaign-error',type:error.name,...(error.name==='AssertionError'?{message:error.message}:{})});process.exitCode=1;}
finally{
 if(fn&&!purgeResult&&!purgeStarted)try{await archive();purgeStarted=true;purgeResult=await purgeStorageArchive(fn.id,namespace.id);}catch(error){cleanupErrors.push({phase:'function',type:error.name});}
 if(fn&&!purgeResult)cleanupErrors.push({phase:'purge-result-unknown',function_id:fn.id});
 if(reader)try{await api('/api/tokens/'+reader.id+'/revoke',{method:'POST'});}catch(error){cleanupErrors.push({phase:'token',type:error.name});}
 if(!cleanupErrors.length)for(const [kind,id] of [['services',service?.id],['namespaces',namespace?.id]])if(id)try{await api('/api/'+kind+'/'+id,{method:'DELETE'});}catch(error){cleanupErrors.push({phase:kind,type:error.name});}
 await caller?.dispose();await admin?.dispose();if(work)await rm(work,{recursive:true,force:true});cleanup=!cleanupErrors.length;await save();if(!completed||!cleanup)process.exitCode=1;
}
console.log(JSON.stringify({completed:completed&&cleanup,groups:checks.filter(v=>v.status==='passed').length,report:report.pathname}));
