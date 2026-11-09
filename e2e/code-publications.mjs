// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md
// @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md
// @verifies docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url);
const report=new URL('code-publications.json',output),checks=[],cleanupErrors=[],pending=[],functions=[],services=[],retained=[],storageArchives=[],evidence=[],invocations=[];
const prefix='publication-api-'+randomUUID().slice(0,8),secret='publication-private-'+randomUUID();
let admin,caller,session,namespace,work,completed=false,cleanup=false;
async function save(){const temporary=new URL('code-publications.pending',output);await writeFile(temporary,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length,skipped:0,checks,cleanup,cleanup_errors:cleanupErrors,evidence,invocations,namespace_id:namespace?.id,function_ids:functions.map(row=>row.id),pre_purge_revisions:retained,storage_archives:storageArchives},null,2)+'\n');await rename(temporary,report);}
function diagnostic(error){const safe=v=>typeof v==='string'&&/^[A-Za-z_][A-Za-z0-9_ :<>=!.-]{0,79}$/.test(v)?v:undefined;const location=String(error?.stack??'').match(/(?:deployments|code-publications)\.mjs:(\d+):(\d+)/);return {name:safe(error?.name)??'UnknownError',code:safe(error?.code),operator:safe(error?.operator),source:location?{line:Number(location[1]),column:Number(location[2])}:undefined,message_sha256:createHash('sha256').update(String(error?.message??'')).digest('hex')};}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:diagnostic(error)});throw error;}}
async function response(url,{method='GET',body,bytes,token,anonymous=false,headers={}}={}){
  const client=token||anonymous?caller:admin;
  return client.fetch(url,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:anonymous?{}:{Origin:base,'X-CSRF-Token':session.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
}
async function call(url,options={}){const result=await response(url,options);assert.equal(result.status(),options.status??200,`${options.method??'GET'} ${url}: ${result.status()}`);const text=await result.text();assert(!text.includes(secret),'Secret exposé');return JSON.parse(text);}
async function purgeArchive(fn){await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await call(`/api/archives/${fn.id}`);const response=await admin.post(`/api/archives/${fn.id}/purge`,{headers:{Origin:base,'X-CSRF-Token':session.csrf_token,'If-Match':String(row.updated_at)},data:{operation_id:randomUUID(),confirm_name:row.name}});assert([200,202].includes(response.status()));const op=await response.json();await until(async()=>{const v=await call(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'aborted');return v.state==='completed';},'public_purge_not_completed');const final=await call(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);return {function_id:fn.id,namespace_id:namespace.id,operation_id:op.id,purged:true,artifact_bytes:final.artifact_bytes};}
async function promote(fn,published,credential){const row=await current(fn);return call(`/api/functions/${fn.id}/versions/${published.code_hash}/promote`,{method:'POST',token:credential,headers:{'If-Match':String(row.updated_at)}});}
async function invoke(fn,version,read,path,{method='GET',revision,label,memory,count}={}){const r=await response(`/invoke/${fn.id}${path}`,{method,token:read,body:method==='POST'?{}:undefined});assert.equal(r.status(),200);const text=await r.text();assert(!text.includes(secret));const value=JSON.parse(text);assert.equal(value.revision,revision);assert.equal(value.functionVersion,version.revision_id);assert.equal(value.label,label);assert.equal(String(value.memory),memory);assert.equal(value.count,count);assert.equal(value.secret_sha256,createHash('sha256').update(secret).digest('hex'));assert.equal(r.headers()['x-serverless-code-hash'],version.code_hash);invocations.push({id:r.headers()['x-serverless-request-id'],function_id:fn.id,requested_code_hash:path.startsWith('@')?version.code_hash:null,resolved_code_hash:version.code_hash});return value;}
async function current(fn){return call(`/api/functions/${fn.id}`);}
async function token(service,rights,extra={}){return call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:randomUUID(),rights,...extra}});}
async function prepare(fn,credential,handler='publication.handler',id=randomUUID()){
  const row=await current(fn);return call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',token:credential,status:201,headers:{'If-Match':String(row.updated_at)},body:{handler,deployment_id:id}});
}
async function upload(candidate,archive,credential,status=200){return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:archive.bytes,token:credential,status});}
async function until(action,message){const end=Date.now()+30000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,100));}assert.fail(message);}
function join(promise){const handled=promise.then(value=>({value}),error=>({error}));pending.push(handled);return handled;}
async function finish(promise){const result=await promise;if(result.error)throw result.error;return result.value;}
async function inspect(fn){const {stdout}=await promisify(execFile)('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/publication-state.py',namespace.id,fn.id],{timeout:30000});return JSON.parse(stdout);}

await mkdir(output,{recursive:true,mode:0o700});await save();
try{
  const storageState=JSON.parse(await readFile(new URL('admin-session.json',output),'utf8'));
  admin=await request.newContext({baseURL:base,storageState,timeout:480000});caller=await request.newContext({baseURL:base,timeout:480000});
  session=await (await admin.get('/api/session')).json();assert.equal(session.authenticated,true,'Session SSO réelle requise');
  work=await mkdtemp(new URL('publication-api-',output).pathname);
  const firstArchive=await publicationArchive(work,'first'),nextArchive=await publicationArchive(work,'next');
  const slow=await publicationArchive(work,'slow','deployment-delay.handler'),broken=await publicationArchive(work,'broken','log-secret-then-throw.handler');
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});
  const service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'publications'}});services.push(service);
  const peerService=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'peer'}});services.push(peerService);
  const fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'publication',config:{handler:'publication.handler',memory_mib:256,cpu:.2,timeout_seconds:5,idle_seconds:0,queue_timeout_seconds:3,storage:{data:{enabled:true,quota_mib:8}}},configuration:{environment:{PUBLIC_LABEL:'initial'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}}});functions.push(fn);
  const peer=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'peer'}});functions.push(peer);
  const create=await token(service,['create']),update=await token(service,['update']),read=await token(service,['read']),other=await token(service,['create','update']);
  const scoped=await token(service,['update'],{function_ids:[peer.id]}),wrong=await token(peerService,['create','update']);
  const endpoint=`/api/functions/${fn.id}/code-deployments`;
  let first;
  await check('Préparation : identité, CRUD, portée, CSRF, versions et modèle strict',async()=>{
    const options={method:'POST',body:{handler:'publication.handler',deployment_id:randomUUID()},headers:{'If-Match':String(fn.updated_at)}};
    await call(endpoint,{...options,anonymous:true,status:401});await call(endpoint,{...options,token:read.token,status:403});await call(endpoint,{...options,token:update.token,status:403});await call(endpoint,{...options,token:wrong.token,status:403});
    await call(endpoint,{...options,headers:{...options.headers,'X-CSRF-Token':'incorrect'},status:403});
    await call(endpoint,{...options,token:create.token,headers:{},status:428});await call(endpoint,{...options,token:create.token,headers:{'If-Match':'0'},status:409});
    for(const body of [{handler:'../outside.handler',deployment_id:randomUUID()},{handler:'publication.handler',deployment_id:'invalid'},{...options.body,configuration:{}}])await call(endpoint,{...options,body,status:422});
  });
  await check('UUID corrélé, doublon sans rejeu, créateur et liste administrateur',async()=>{
    const id=randomUUID();first=await prepare(fn,create.token,'publication.handler',id.toUpperCase());assert.equal(first.id,id);
    const found=await call(`/api/deployments/${id}`,{token:create.token});assert.equal(found.state,'prepared');
    await call(`/api/deployments/${id}`,{token:read.token,status:403});await call(`/api/deployments/${id}`,{token:other.token,status:403});
    await call(endpoint,{method:'POST',token:create.token,status:409,headers:{'If-Match':String(fn.updated_at)},body:{handler:'publication.handler',deployment_id:id}});
    await call(`/api/functions/${fn.id}/deployments`,{token:create.token,status:401});await call(`/api/functions/${fn.id}/deployments`,{anonymous:true,status:401});
    const list=await call(`/api/functions/${fn.id}/deployments`);assert.equal(list.total,1);assert.equal(list.items[0].id,id);
    for(const key of ['configuration','configuration_cipher','config','events_json'])assert.equal(key in list.items[0],false);
    await call(`/api/functions/${fn.id}/deployments?limit=0`,{status:422});await call(`/api/functions/${fn.id}/deployments?offset=10001`,{status:422});
  });
  await check('Première publication Create : secret, ressources et volume réellement invoqués',async()=>{
    const firstPublished=await upload(first,firstArchive,create.token);
    let row=await current(fn);assert.equal(row.active_revision_id,null);assert.deepEqual(row.config,fn.config);assert.deepEqual(row.environment,fn.environment);
    await call(`/invoke/${fn.id}`,{token:read.token,status:409});
    await invoke(fn,firstPublished,read.token,'@'+firstPublished.code_hash+'?mode=counter',{method:'POST',revision:'first',label:'initial',memory:'256',count:1});
    await promote(fn,firstPublished,create.token);row=await current(fn);assert.equal(row.active_revision_id,firstPublished.revision_id);
    await invoke(fn,firstPublished,read.token,'?mode=counter',{revision:'first',label:'initial',memory:'256',count:1});
    evidence.push({scenario:'first-code-with-explicit-create-promotion',code_hash:firstPublished.code_hash,revision_id:firstPublished.revision_id});
    await call(endpoint,{method:'POST',token:create.token,status:403,headers:{'If-Match':String(row.updated_at)},body:{handler:'publication.handler',deployment_id:randomUUID()}});
    await call(endpoint,{method:'POST',token:scoped.token,status:403,headers:{'If-Match':String(row.updated_at)},body:{handler:'publication.handler',deployment_id:randomUUID()}});
  });
  await check('Publication de code Update : configuration, événements et données conservés',async()=>{
    const before=await current(fn),events={http:[{path:'stable',methods:['GET','POST'],implicit:false}],schedules:[{cron:'0 1 * * *',enabled:false,timezone:'UTC'}]};
    const baseline=await call(`/api/functions/${fn.id}/deployments`,{method:'POST',status:201,headers:{'If-Match':String(before.updated_at)},body:{config:{...before.config,memory_mib:384},configuration:{environment:{PUBLIC_LABEL:'custom'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}},events}});
    const stable=await upload(baseline,firstArchive);assert.equal((await current(fn)).active_revision_id,before.active_revision_id);await promote(fn,stable);
    const snapshot=await current(fn),candidate=await prepare(fn,update.token),pilot=await upload(candidate,nextArchive,update.token);
    const after=await current(fn);assert.deepEqual(after.config,snapshot.config);assert.deepEqual(after.environment,snapshot.environment);assert.deepEqual(after.secret_names,snapshot.secret_names);assert.equal(after.active_revision_id,stable.revision_id);assert.equal(after.updated_at,snapshot.updated_at);
    const history=await call(`/api/functions/${fn.id}/revisions`);assert.deepEqual(history.items.find(row=>row.id===pilot.revision_id).events,events);
    await invoke(fn,stable,read.token,'/stable?mode=counter',{revision:'first',label:'custom',memory:'384',count:1});
    await invoke(fn,pilot,read.token,'@'+pilot.code_hash+'/stable?mode=counter',{revision:'next',label:'custom',memory:'384',count:1});
    await promote(fn,pilot,update.token);await invoke(fn,pilot,read.token,'/stable?mode=counter',{revision:'next',label:'custom',memory:'384',count:1});
    evidence.push({scenario:'code-only-pilot-preserves-default-and-configuration',stable_hash:stable.code_hash,pilot_hash:pilot.code_hash,stable_revision_id:stable.revision_id,pilot_revision_id:pilot.revision_id});
    await call(`/invoke/${fn.id}`,{token:read.token,status:404});
  });
  await check('Abandon après changement de configuration : propriété, secret effacé et sans rejeu',async()=>{
    const candidate=await prepare(fn,update.token),before=await current(fn);
    await call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(before.updated_at)},body:{name:before.name,config:before.config,configuration:{environment:{PUBLIC_LABEL:'changed'}}}});
    await call(`/api/deployments/${candidate.id}`,{method:'DELETE',token:other.token,status:403});await call(`/api/deployments/${candidate.id}`,{method:'DELETE',token:read.token,status:403});
    await call(`/api/deployments/${candidate.id}`,{method:'DELETE',headers:{'X-CSRF-Token':'incorrect'},status:403});
    const result=await call(`/api/deployments/${candidate.id}`,{method:'DELETE',token:update.token});assert.equal(result.error_code,'candidate_abandoned');assert.equal(result.state,'failed');
    await call(`/api/deployments/${candidate.id}`,{method:'DELETE',status:409});await upload(candidate,nextArchive,update.token,409);
    const privateState=(await inspect(fn)).candidates.find(row=>row.id===candidate.id);assert.equal(privateState.configuration_present,0);assert.equal(privateState.reserved_bytes,0);
    assert.equal((await current(fn)).active_revision_id,before.active_revision_id);
  });
  await check('Archive invalide et import réellement refusé : diagnostic expurgé, code actif conservé',async()=>{
    const before=await current(fn),invalid=await prepare(fn,update.token);await upload(invalid,{bytes:Buffer.from('invalid ZIP')},update.token,422);
    assert.equal((await call(`/api/deployments/${invalid.id}`)).state,'failed');
    const candidate=await prepare(fn,update.token,broken.handler);await upload(candidate,broken,update.token,422);
    const result=await call(`/api/deployments/${candidate.id}`);assert.equal(result.validation.valid,false);assert.equal(result.validation.error,'import_failed');assert(result.validation.logs.includes('qualification-import-secret=[redacted]'));
    assert.equal((await current(fn)).active_revision_id,before.active_revision_id);
  });
  await check('Conflit de version pendant la validation réelle',async()=>{
    const before=await current(fn),candidate=await prepare(fn,update.token,slow.handler),uploading=join(upload(candidate,slow,update.token,409));
    await until(async()=> (await call(`/api/deployments/${candidate.id}`)).state==='validating','Validation non observée');
    await call(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(before.updated_at)},body:{name:before.name,config:before.config,configuration:{environment:{PUBLIC_LABEL:'concurrent'}}}});
    await finish(uploading);assert.equal((await current(fn)).active_revision_id,before.active_revision_id);assert.equal((await current(fn)).environment.PUBLIC_LABEL,'concurrent');
    assert.equal((await call(`/api/deployments/${candidate.id}`)).state,'failed');
  });
  await check('Révocation pendant validation et refus d’abandon avec jeton révoqué',async()=>{
    const before=await current(fn),credential=await token(service,['update']),candidate=await prepare(fn,credential.token,slow.handler),uploading=join(upload(candidate,slow,credential.token,401));
    await until(async()=> (await call(`/api/deployments/${candidate.id}`)).state==='validating','Validation non observée');
    await call(`/api/tokens/${credential.id}/revoke`,{method:'POST'});await finish(uploading);
    assert.equal((await call(`/api/deployments/${candidate.id}`)).state,'failed');
    assert.equal((await current(fn)).active_revision_id,before.active_revision_id);
    assert(!(await call(`/api/functions/${fn.id}/revisions?limit=100`)).items.some(row=>row.id===candidate.id));
    const revoked=await token(service,['update']),prepared=await prepare(fn,revoked.token);await call(`/api/tokens/${revoked.id}/revoke`,{method:'POST'});
    await call(`/api/deployments/${prepared.id}`,{method:'DELETE',token:revoked.token,status:401});assert.equal((await call(`/api/deployments/${prepared.id}`)).state,'prepared');await call(`/api/deployments/${prepared.id}`,{method:'DELETE'});
  });
  await check('Course abandon et upload : un seul gagnant et aucune activation après abandon',async()=>{
    const candidate=await prepare(fn,update.token),before=await current(fn);
    const uploadResult=join(response(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:nextArchive.bytes,token:update.token}));
    const abandonResult=join(response(`/api/deployments/${candidate.id}`,{method:'DELETE',token:update.token}));
    const first=await finish(uploadResult),second=await finish(abandonResult);for(const response of [first,second])assert(!(await response.text()).includes(secret));assert.deepEqual([first.status(),second.status()].sort(),[200,409]);
    const state=await call(`/api/deployments/${candidate.id}`),after=await current(fn);
    if(second.status()===200){assert.equal(state.error_code,'candidate_abandoned');assert.equal(after.active_revision_id,before.active_revision_id);}
    else{assert.equal(state.state,'published');assert.equal(after.active_revision_id,before.active_revision_id);assert.equal(state.revision_id,before.active_revision_id);assert.equal(state.code_changed,false);}
    const slowCandidate=await prepare(fn,update.token,slow.handler),uploading=join(upload(slowCandidate,slow,update.token));
    await until(async()=> (await call(`/api/deployments/${slowCandidate.id}`)).state==='validating','Validation non observée');
    await call(`/api/deployments/${slowCandidate.id}`,{method:'DELETE',token:update.token,status:409});await finish(uploading);
  });
  await check('Pagination des tentatives et effacement terminal des configurations temporaires',async()=>{
    const candidates=[];for(let i=0;i<6;i++)candidates.push(await prepare(fn,update.token));
    const all=await call(`/api/functions/${fn.id}/deployments?limit=100`),one=await call(`/api/functions/${fn.id}/deployments?limit=5`),two=await call(`/api/functions/${fn.id}/deployments?limit=5&offset=5`);
    assert.equal(one.total,all.total);assert.equal(two.total,all.total);assert.deepEqual([...one.items,...two.items].map(row=>row.id),all.items.slice(0,10).map(row=>row.id));
    for(const row of candidates)await call(`/api/deployments/${row.id}`,{method:'DELETE',token:update.token});
    const state=await inspect(fn);assert.equal(all.total,state.candidates.length);assert.equal(all.items.length,state.candidates.length);assert.equal(one.items.length,5);assert.equal(two.items.length,5);
    assert.deepEqual(all.items.map(row=>row.id).sort(),state.candidates.map(row=>row.id).sort());
    const ordered=[...all.items].sort((a,b)=>b.created_at-a.created_at||a.id.localeCompare(b.id));assert.deepEqual(all.items.map(row=>row.id),ordered.map(row=>row.id));
    assert(state.candidates.every(row=>['failed','published'].includes(row.state)&&row.configuration_present===0&&row.reserved_bytes===0));
  });
  completed=true;
}catch(error){if(!checks.some(row=>row.status==='failed'))checks.push({name:'Préparation ou fin',status:'failed',error:error.name});evidence.push({scenario:'campaign-error',diagnostic:diagnostic(error)});console.error(JSON.stringify(diagnostic(error)));process.exitCode=1;}
finally{
  await Promise.all(pending);
  const failure=(step,id,error)=>cleanupErrors.push({step,id,diagnostic:diagnostic(error)});
  // Recover resources by exact names if a creation response was lost.
  if(session?.authenticated)try{
    if(!namespace)namespace=(await call('/api/namespaces?limit=100')).items.find(row=>row.name===prefix);
    if(namespace){
      for(const row of (await call(`/api/namespaces/${namespace.id}/services?limit=100`)).items)
        if(['publications','peer'].includes(row.name)&&!services.some(item=>item.id===row.id))services.push(row);
      for(const service of services)for(const row of (await call(`/api/services/${service.id}/functions?limit=100`)).items)
        if(['publication','peer'].includes(row.name)&&!functions.some(item=>item.id===row.id))functions.push(row);
    }
  }catch(error){failure('identification',namespace?.id,error);}
  for(const fn of functions){
    try{const revisions=await call(`/api/functions/${fn.id}/revisions?limit=100`);retained.push(...revisions.items.map(row=>({function_id:fn.id,id:row.id,archive_sha256:row.archive_sha256})));}catch(error){failure('historique',fn.id,error);}
    try{await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length,'instances_not_released_before_cleanup');await call(`/api/functions/${fn.id}`,{method:'DELETE'});}catch(error){failure('suppression',fn.id,error);}
    try{storageArchives.push(await purgeArchive(fn));}catch(error){failure('purge',fn.id,error);}
  }
  for(const row of services)try{await call(`/api/services/${row.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push('service:'+error.name);}
  if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push('namespace:'+error.name);}
  if(work)try{await rm(work,{recursive:true,force:true});}catch(error){failure('fichiers',null,error);}
  try{await admin?.dispose();}catch(error){failure('session-admin',null,error);}
  try{await caller?.dispose();}catch(error){failure('session-appels',null,error);}
  cleanup=cleanupErrors.length===0;await save();if(!completed||cleanupErrors.length)process.exitCode=1;
}
