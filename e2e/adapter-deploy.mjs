// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#commande-deploy
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#commande-deploy
// Genuine SSO session, service tokens, CLI processes and Docker publications.
// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),output=path.join(root,'.local/e2e');
await mkdir(output,{recursive:true,mode:0o700});
const report=path.join(output,'adapter-deploy.json'),base='https://serverless.lelabs.tech';
await writeFile(report,JSON.stringify({completed:false,error:'Campagne non terminée'})+'\n');
let storageState;
try {storageState=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));}
catch(error) {
  await writeFile(report,JSON.stringify({completed:false,prerequisite_failed:true,checks:[],skipped:0,
    error:'Session SSO administrateur réelle absente ou illisible'})+'\n');
  throw new Error('Session SSO administrateur réelle requise.',{cause:error});
}
const api=await request.newContext({baseURL:base,storageState,timeout:30000});
let session;
try {
  session=await (await api.get('/api/session')).json();assert(session.authenticated);
} catch(error) {
  await api.dispose();await writeFile(report,JSON.stringify({completed:false,prerequisite_failed:true,checks:[],skipped:0,
    error:'Session SSO administrateur réelle indisponible'})+'\n');throw error;
}
const checks=[],archives=[],storageArchives=[],functionIds=[],cleanupErrors=[],invocations=[],evidence=[];let namespace,service,work,completed=false,clean=false;
const prefix='cli-'+randomUUID().slice(0,8),secret='qualification-cli-'+randomUUID();
async function call(url,{method='GET',body,status=200}={}) {
  const response=await api.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token}});
  assert.equal(response.status(),status,method+' '+url);
  const raw=await response.text();assert(!raw.includes(secret));return JSON.parse(raw);
}
async function check(name,action) {
  try {await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:diagnostic(error)});throw error;}
}
async function credential(name,rights) {
  return (await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights}})).token;
}
function diagnostic(error){const safe=v=>typeof v==='string'&&/^[A-Za-z_][A-Za-z0-9_ :<>=!.-]{0,79}$/.test(v)?v:undefined;const location=String(error?.stack??'').match(/adapter-deploy\.mjs:(\d+):(\d+)/);return {name:safe(error?.name)??'UnknownError',code:safe(error?.code),operator:safe(error?.operator),source:location?{line:Number(location[1]),column:Number(location[2])}:undefined,message_sha256:createHash('sha256').update(String(error?.message??'')).digest('hex')};}
async function until(action,message){const end=Date.now()+30000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,100));}assert.fail(message);}
async function purgeArchive(fn){await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await call(`/api/archives/${fn.id}`);const result=await api.post(`/api/archives/${fn.id}/purge`,{headers:{Origin:base,'X-CSRF-Token':session.csrf_token,'If-Match':String(row.updated_at)},data:{operation_id:randomUUID(),confirm_name:row.name}});assert([200,202].includes(result.status()));const op=await result.json();await until(async()=>{const v=await call(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'public_purge_not_completed');const final=await call(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);return {function_id:fn.id,namespace_id:namespace.id,operation_id:op.id,purged:true,artifact_bytes:final.artifact_bytes};}
async function invoke(row,token,pinned){const tag=randomUUID();const response=await api.get(`/invoke/${row.function_id}${pinned?'@'+row.code_hash:''}`,{headers:{'X-Serverless-Token':token,'X-Qualification-Tag':tag}});assert.equal(response.status(),200);const text=await response.text();assert(!text.includes(secret));const value=JSON.parse(text);assert.equal(value.secretPresent,true);assert.equal(value.tag,tag);assert.equal(value.method,'GET');assert.equal(value.requestId,response.headers()['x-serverless-request-id']);assert.match(value.requestId,/^[0-9a-f-]{36}$/);assert.equal(response.headers()['x-serverless-code-hash'],row.code_hash);invocations.push({id:value.requestId,function_id:row.function_id,requested_code_hash:pinned?row.code_hash:null,resolved_code_hash:row.code_hash});}
async function promote(row,token){const result=await new Promise(resolve=>execFile('python3',['-B','-m','adapter','promote','--function',row.function_id,'--code-hash',row.code_hash],{cwd:root,timeout:120000,maxBuffer:1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:token}},(error,stdout,stderr)=>resolve({error,stdout,stderr})));assert.equal(result.error?.code??0,0);assert(!result.stderr.includes('Traceback'));for(const raw of [secret,token])assert(!result.stdout.includes(raw)&&!result.stderr.includes(raw));const value=JSON.parse(result.stdout);assert.equal(value.completed,true);assert.equal(value.state,'promoted');assert.equal(value.revision_id,row.revision_id);assert.equal((await current(row.function_id)).active_revision_id,row.revision_id);evidence.push({scenario:'explicit-cli-promotion',function_id:row.function_id,code_hash:row.code_hash,revision_id:row.revision_id});}
let manifest;
async function save() {await writeFile(path.join(work,'serverless.yml'),JSON.stringify(manifest));}
async function deploy(token,success) {
  const result=await new Promise(resolve=>execFile('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',service.id],
    {cwd:root,timeout:900000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:token,QUALIFICATION_SYNTHETIC_SECRET:secret}},
    (error,stdout,stderr)=>resolve({error,stdout,stderr})));
  assert.equal(result.error?.code??0,success?0:1,'Code de sortie CLI');
  assert(!result.stderr.includes('Traceback'));
  assert(!result.stdout.includes(secret)&&!result.stderr.includes(secret));
  assert(!result.stdout.includes(token)&&!result.stderr.includes(token));
  const parsed=JSON.parse(result.stdout);assert.equal(parsed.completed,success);
  const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));
  assert(!JSON.stringify(descriptor).includes(secret));
  return parsed;
}
async function current(id) {return call(`/api/functions/${id}`);}

try {
  work=await mkdtemp(path.join(output,'cli-code-'));
  await cp(path.join(root,'qualification/src'),path.join(work,'src'),{recursive:true});
  await cp(path.join(root,'qualification/package.json'),path.join(work,'package.json'));
  await cp(path.join(root,'qualification/artifacts/throws.cjs'),path.join(work,'src/throws.cjs'));
  await writeFile(path.join(work,'src/revision.json'),JSON.stringify({version:1}));
  manifest={service:prefix,provider:{name:'p2enjoy',runtime:'nodejs24.x',p2enjoy:{idle_seconds:0},environment:{PUBLIC_REVISION:'one'},
    secret:{QUALIFICATION_SYNTHETIC_SECRET:'${env:QUALIFICATION_SYNTHETIC_SECRET}'}},
    functions:Object.fromEntries(Array.from({length:11},(_,i)=>['echo-pagination-'+String(i).padStart(2,'0'),{handler:'src/handlers.echo'}])),
    package:{patterns:['!**','src/**','package.json']}};
  await save();
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});
  service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:prefix}});
  const read=await credential('invocation-and-catalogue',['read']),create=await credential('first-publication-and-promotion',['read','create']),update=await credential('new-publication-and-promotion',['read','update']);
  const publisher=await credential('service-configuration-and-publication',['read','create','update']);
  await check('Nom de service contrôlé avant toute création',async()=>{
    manifest.service=prefix+'-wrong';await save();const result=await deploy(create,false);
    assert.equal(result.error.code,'service_mismatch');assert.deepEqual(result.results,[]);
    assert.deepEqual((await call(`/api/services/${service.id}/functions`)).items,[]);
    manifest.service=prefix;await save();
  });
  await check('Read seul : configuration commune refusée avant les créations',async()=>{
    const result=await deploy(read,false);assert.equal(result.results.length,0);
    assert.equal(result.error.status,403);assert.equal(result.service_configuration.state,'failed');
    assert.deepEqual((await call(`/api/services/${service.id}/functions`)).items,[]);
  });
  let first,second;
  await check('Onze premières publications avec configuration commune au service',async()=>{
    first=await deploy(publisher,true);assert.equal(first.results.length,11);
    for(const row of first.results) {
      assert(row.created);const fn=await current(row.function_id);
      assert.equal(fn.active_revision_id,null);assert.equal(row.code_changed,true);assert.match(row.code_hash,/^[0-9a-f]{64}$/);assert.deepEqual(fn.environment,{});
      assert.deepEqual(fn.secret_names,[]);
      const history=await call(`/api/functions/${fn.id}/revisions`);
      const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));
      const bytes=await readFile(path.join(work,'.serverless-p2',descriptor.artifacts[row.name].file));
      assert.equal(history.items[0].archive_sha256,createHash('sha256').update(bytes).digest('hex'));
      await invoke(row,read,true);await promote(row,create);await invoke(row,read,false);
    }
    const common=await call(`/api/services/${service.id}`);assert.equal(common.environment.PUBLIC_REVISION,'one');
    assert.deepEqual(common.secret_names,['QUALIFICATION_SYNTHETIC_SECRET']);
  });
  await check('Create ne republie pas une fonction déjà active',async()=>{
    delete manifest.provider.environment;delete manifest.provider.secret;await save();
    const result=await deploy(create,false);assert.equal(result.results.length,11);for(let i=0;i<11;i++){assert.equal(result.results[i].name,first.results[i].name);assert.equal(result.results[i].function_id,first.results[i].function_id);assert.equal(result.results[i].error.status,403);}
    for(const row of first.results)assert.equal((await current(row.function_id)).active_revision_id,row.revision_id);
  });
  await check('Pagination réelle puis nouvelles révisions avec UUID conservés',async()=>{
    manifest.provider.environment={PUBLIC_REVISION:'two'};await save();
    await writeFile(path.join(work,'src/revision.json'),JSON.stringify({version:2}));
    second=await deploy(update,true);assert.equal(second.results.length,11);
    for(let i=0;i<11;i++) {
      assert.equal(second.results[i].function_id,first.results[i].function_id);
      assert.notEqual(second.results[i].revision_id,first.results[i].revision_id);
      const after=await current(second.results[i].function_id);assert.deepEqual(after.environment,{});assert.equal(after.active_revision_id,first.results[i].revision_id);assert.equal(second.results[i].code_changed,true);assert.notEqual(second.results[i].code_hash,first.results[i].code_hash);
      await invoke(first.results[i],read,false);await invoke(second.results[i],read,true);await promote(second.results[i],update);await invoke(second.results[i],read,false);
    }
    assert.equal((await call(`/api/services/${service.id}`)).environment.PUBLIC_REVISION,'two');
  });
  await check('Import réellement défaillant : résultat partiel et poursuite des autres fonctions',async()=>{
    manifest.functions['echo-pagination-00'].handler='src/throws.handler';manifest.provider.environment.PUBLIC_REVISION='three';await save();
    const partial=await deploy(update,false);assert.equal(partial.results.length,11);
    assert.equal(partial.results[0].error.status,422);assert.equal(partial.results[0].state,'failed');
    assert(partial.results.slice(1).every(row=>row.state==='published'));
    const unchanged=await current(second.results[0].function_id);
    assert.equal(unchanged.active_revision_id,second.results[0].revision_id);assert.deepEqual(unchanged.environment,{});
    assert.equal(partial.service_configuration.state,'applied');
    assert.equal((await call(`/api/services/${service.id}`)).environment.PUBLIC_REVISION,'three');
    for(let i=1;i<partial.results.length;i++){const row=partial.results[i];assert.deepEqual((await current(row.function_id)).environment,{});assert.equal(row.code_changed,false);assert.equal(row.code_hash,second.results[i].code_hash);assert.equal(row.revision_id,second.results[i].revision_id);}
    for(const row of second.results)await invoke(row,read,false);
  });
  await check('Reprise du même brouillon après import refusé avec Read et Create',async()=>{
    delete manifest.provider.environment;await save();
    manifest.functions={retry:{handler:'src/throws.handler'}};await save();
    const failed=await deploy(create,false);assert.equal(failed.results[0].error.status,422);
    const id=failed.results[0].function_id;assert.equal((await current(id)).active_revision_id,null);
    manifest.functions.retry.handler='src/handlers.echo';await save();
    const recovered=await deploy(create,true);assert.equal(recovered.results[0].function_id,id);
    assert.equal((await current(id)).active_revision_id,null);await invoke(recovered.results[0],read,true);await promote(recovered.results[0],create);await invoke(recovered.results[0],read,false);
  });
  assert.equal(invocations.length,68);assert.equal(new Set(invocations.map(row=>row.id)).size,68);completed=true;
} catch(error){evidence.push({scenario:'campaign-error',diagnostic:diagnostic(error)});console.error(JSON.stringify(diagnostic(error)));process.exitCode=1;} finally {
  try {
    if(service) {
      let functions=[];
      try{functions=(await call(`/api/services/${service.id}/functions?limit=100`)).items;functionIds.push(...functions.map(f=>f.id));}
      catch(error){cleanupErrors.push('function_inventory:'+error.name);}
      for(const fn of functions) {
        try{
          for(const row of (await call(`/api/functions/${fn.id}/revisions`)).items)archives.push({function_id:fn.id,revision_id:row.id});
          await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instances_not_released');
          await call(`/api/functions/${fn.id}`,{method:'DELETE'});
          storageArchives.push(await purgeArchive(fn));
        }catch(error){cleanupErrors.push('function:'+fn.id+':'+error.name);}
      }
      try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push('service:'+service.id+':'+error.name);}
    }
    if(namespace){try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push('namespace:'+namespace.id+':'+error.name);}}
    if(work){try{await rm(work,{recursive:true,force:true});}catch(error){cleanupErrors.push('local_files:'+error.name);}}
    clean=cleanupErrors.length===0;
  } finally {
    await api.dispose();
    await writeFile(report,JSON.stringify({completed:completed&&clean,checks,cleanup:clean,skipped:0,invocations,evidence,pre_purge_revisions:archives,storage_archives:storageArchives,cleanupErrors,function_ids:functionIds,namespace_id:namespace?.id,
      remaining_proofs:['Rupture réelle après envoi et absence de double publication','Modification concurrente des fichiers après packaging','Réponses trop grandes et redirections réelles']},null,2)+'\n');
  }
}
assert(completed&&clean);
