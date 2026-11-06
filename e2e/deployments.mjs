// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#préparation-validation-et-publication
// Uses the real SSO session, normal management API, adapter and Docker validation.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const run=promisify(execFile), root=fileURLToPath(new URL('../',import.meta.url));
const output=path.join(root,'.local/e2e'),base='https://serverless-dev.lelabs.tech';
await mkdir(output,{recursive:true,mode:0o700});
const report=path.join(output,'deployments.json');
await writeFile(report,JSON.stringify({completed:false,error:'Campagne non terminée'})+'\n');
let storageState;
try {storageState=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));}
catch(error) {
  await writeFile(report,JSON.stringify({completed:false,prerequisite_failed:true,
    error:'Session SSO administrateur réelle absente ou illisible',checks:[],skipped:0})+'\n');
  throw new Error('Session SSO administrateur réelle requise : lancer e2e/authorize.mjs.',{cause:error});
}
const admin=await request.newContext({baseURL:base,storageState,timeout:480000});
const caller=await request.newContext({baseURL:base,timeout:480000});
let session;
try {
  session=await (await admin.get('/api/session')).json();
  assert(session.authenticated,'Une session SSO administrateur réelle est requise.');
} catch(error) {
  await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({completed:false,prerequisite_failed:true,
    error:'Session SSO administrateur réelle indisponible',checks:[],skipped:0})+'\n');
  throw error;
}
const checks=[],functions=[],services=[],tokens=[],archives=[];
let namespace,work,completed=false,clean=false;
const prefix='deploy-'+randomUUID().slice(0,8),secret='qa-private-'+randomUUID();

async function call(url,{method='GET',body,bytes,token,headers={},status=200,anonymous=false}={}) {
  const client=token||anonymous?caller:admin;
  const response=await client.fetch(url,{method,data:bytes??body,
    headers:{...(token?{'X-Serverless-Token':token}:anonymous?{}:{Origin:base,'X-CSRF-Token':session.csrf_token}),
      ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert.equal(response.status(),status,`${method} ${url}: attendu ${status}, reçu ${response.status()}`);
  const text=await response.text();assert(!text.includes(secret),'Secret exposé dans une réponse');
  return JSON.parse(text);
}
async function check(name,action) {
  try {await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
function pendingUpload(promise) {
  return promise.then(value=>({value}),error=>({error}));
}
async function finishUpload(pending) {
  const result=await finishUpload(pending);if(result.error)throw result.error;return result.value;
}
async function token(service,name,rights) {
  const row=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights}});
  tokens.push(row);return row.token;
}
async function create(service,name) {
  const row=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,
    body:{name,config:{handler:'src/handlers.echo',memory_mib:128,timeout_seconds:2}}});
  functions.push(row);return row;
}
async function current(fn){return call(`/api/functions/${fn.id}`);}
async function prepare(fn,credential,overrides={}) {
  const row=await current(fn);
  return call(`/api/functions/${fn.id}/deployments`,{method:'POST',status:201,token:credential,
    headers:{'If-Match':String(row.updated_at)},body:{config:row.config,configuration:{environment:{PUBLIC_LABEL:'deployed'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}},...overrides}});
}
async function upload(candidate,bytes,credential,status=200) {
  return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes,token:credential,status});
}
async function waitValidating(candidate,credential) {
  const end=Date.now()+20000;
  while(Date.now()<end) {
    const row=await call(`/api/deployments/${candidate.id}`,{token:credential});
    if(row.state==='validating')return;
    assert(['prepared','receiving'].includes(row.state),`Candidat arrêté avant validation : ${row.state}`);
    await new Promise(resolve=>setTimeout(resolve,50));
  }
  assert.fail('Validation réelle non observée');
}
async function packageVariant(name,handler) {
  const project=path.join(work,name);await mkdir(project);
  await cp(path.join(root,'qualification/src'),path.join(project,'src'),{recursive:true});
  await cp(path.join(root,'qualification/package.json'),path.join(project,'package.json'));
  await writeFile(path.join(project,'src/revision.json'),JSON.stringify({revision:name})+'\n');
  await cp(path.join(root,'qualification/artifacts/deployment-delay.mjs'),path.join(project,'src/deployment-delay.mjs'));
  await cp(path.join(root,'qualification/artifacts/throws.cjs'),path.join(project,'src/throws.cjs'));
  const manifest={service:'qualification-deployment',provider:{name:'p2enjoy',runtime:'nodejs24.x'},
    functions:{probe:{handler}},package:{patterns:['!**','src/**','package.json']}};
  const config=path.join(project,'serverless.yml');await writeFile(config,JSON.stringify(manifest));
  await run('python3',['-B','-m','adapter','package','--config',config],{cwd:root});
  const descriptor=JSON.parse(await readFile(path.join(project,'.serverless-p2/deployment.json'),'utf8'));
  return readFile(path.join(project,'.serverless-p2',descriptor.artifacts.probe.file));
}

try {
  work=await mkdtemp(path.join(output,'deployment-code-'));
  const ordinary=await packageVariant('ordinary','src/handlers.echo');
  const slow=await packageVariant('slow','src/deployment-delay.handler');
  const broken=await packageVariant('broken','src/throws.handler');
  const ordinaryHash=createHash('sha256').update(ordinary).digest('hex'),slowHash=createHash('sha256').update(slow).digest('hex');
  assert.notEqual(ordinaryHash,slowHash,'Les deux révisions doivent contenir des fichiers distincts');
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});
  const service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:prefix}});services.push(service);
  const fn=await create(service,'probe');
  const createOnly=await token(service,'create',['create']);
  const update=await token(service,'update',['update']);
  const other=await token(service,'another-update',['update']);
  const read=await token(service,'read',['read']);
  let first,second;
  await check('Préparation : identité, droits, If-Match et données invalides',async()=>{
    const url=`/api/functions/${fn.id}/deployments`,body={config:fn.config};
    await call(url,{method:'POST',body,anonymous:true,status:401});
    await call(url,{method:'POST',body,token:read,status:403});
    await call(url,{method:'POST',body,token:createOnly,status:428});
    await call(url,{method:'POST',body,token:createOnly,headers:{'If-Match':'0'},status:409});
    await call(url,{method:'POST',body:{...body,events:{schedules:[{cron:'* * * * * *'}]}},status:422});
  });
  await check('Archive invalide : échec et brouillon conservé',async()=>{
    const candidate=await prepare(fn,createOnly);
    await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:ordinary,token:read,status:403});
    await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:ordinary,token:createOnly,headers:{'Content-Type':'text/plain'},status:415});
    await upload(candidate,Buffer.from('invalid zip'),createOnly,422);
    assert.equal((await call(`/api/deployments/${candidate.id}`,{token:createOnly})).state,'failed');
    assert.equal((await current(fn)).active_revision_id,null);
    await upload(candidate,ordinary,createOnly,409);
  });
  await check('Première publication par Create, lecture expurgée et historique Read',async()=>{
    const candidate=await prepare(fn,createOnly);first=await upload(candidate,ordinary,createOnly);
    assert.equal(first.state,'published');assert(first.validation.valid&&first.validation.container_removed);
    const row=await current(fn);assert.equal(row.active_revision_id,first.revision_id);
    assert.deepEqual(row.secret_names,['QUALIFICATION_SYNTHETIC_SECRET']);
    const history=await call(`/api/functions/${fn.id}/revisions`,{token:read});
    assert.equal(history.items.length,1);assert(history.items[0].active);assert.equal(history.items[0].archive_sha256,ordinaryHash);assert(!('inventory_json' in history.items[0]));
    await call(`/api/functions/${fn.id}/deployments`,{method:'POST',body:{config:row.config},token:createOnly,
      headers:{'If-Match':String(row.updated_at)},status:403});
  });
  await check('Propriété du candidat et échec réel d’import avec secret expurgé',async()=>{
    const row=await current(fn),candidate=await prepare(fn,update,{config:{...row.config,handler:'src/throws.handler'}});
    await upload(candidate,broken,other,403);
    await upload(candidate,broken,update,422);
    const status=await call(`/api/deployments/${candidate.id}`,{token:update});
    assert.equal(status.state,'failed');assert.equal(status.validation.error,'import_failed');
    assert(status.validation.logs.includes('[redacted]'));assert.equal((await current(fn)).active_revision_id,first.revision_id);
  });
  await check('Révocation réelle pendant un chargement valide : publication refusée',async()=>{
    const disposable=await token(service,'during-validation',['update']);
    const row=await current(fn),candidate=await prepare(fn,disposable,{config:{...row.config,handler:'src/deployment-delay.handler'}});
    const pending=pendingUpload(upload(candidate,slow,disposable,401));
    try {
      await waitValidating(candidate,disposable);
      const issued=tokens.at(-1);await call(`/api/tokens/${issued.id}/revoke`,{method:'POST'});
    } finally {await finishUpload(pending);}
    assert.equal((await current(fn)).active_revision_id,first.revision_id);
  });
  await check('Configuration de service modifiée pendant la validation : conflit',async()=>{
    const row=await current(fn),candidate=await prepare(fn,update,{config:{...row.config,handler:'src/deployment-delay.handler'}});
    const pending=pendingUpload(upload(candidate,slow,update,409));
    try {
      await waitValidating(candidate,update);
      await call(`/api/services/${service.id}/configuration`,{method:'PUT',body:{environment:{SHARED:'changed'}}});
    } finally {await finishUpload(pending);}
    assert.equal((await current(fn)).active_revision_id,first.revision_id);
  });
  await check('Configuration de fonction modifiée pendant la validation : conflit',async()=>{
    const row=await current(fn),candidate=await prepare(fn,update,{config:{...row.config,handler:'src/deployment-delay.handler'}});
    const pending=pendingUpload(upload(candidate,slow,update,409));
    try {
      await waitValidating(candidate,update);
      await call(`/api/functions/${fn.id}`,{method:'PUT',body:{name:row.name,config:{...row.config,memory_mib:384}}});
    } finally {await finishUpload(pending);}
    const currentRow=await current(fn);assert.equal(currentRow.active_revision_id,first.revision_id);assert.equal(currentRow.config.memory_mib,384);
  });
  await check('Admission unique et état consultable pendant un véritable chargement',async()=>{
    const row=await current(fn),candidate=await prepare(fn,update,{config:{...row.config,handler:'src/deployment-delay.handler'}});
    const waiting=await prepare(fn,update);
    const pending=pendingUpload(upload(candidate,slow,update));
    try {await waitValidating(candidate,update);await upload(waiting,ordinary,update,429);}
    finally {second=await finishUpload(pending);}
    assert.equal(second.state,'published');await upload(waiting,ordinary,update,409);
  });
  await check('Handler immuable hors déploiement, rollback et configuration courante conservée',async()=>{
    let row=await current(fn);
    await call(`/api/functions/${fn.id}`,{method:'PUT',body:{name:row.name,config:{...row.config,handler:'src/handlers.binary'}},status:409});
    row=await call(`/api/functions/${fn.id}`,{method:'PUT',body:{name:row.name,config:{...row.config,cpu:.5},configuration:{environment:{CURRENT:'kept'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:null,CURRENT_SECRET:secret+'-current'}}}});
    await call(`/api/functions/${fn.id}/rollback`,{method:'POST',token:read,body:{revision_id:first.revision_id},headers:{'If-Match':String(row.updated_at)},status:403});
    await call(`/api/functions/${fn.id}/rollback`,{method:'POST',token:update,body:{revision_id:first.revision_id},headers:{'If-Match':String(row.updated_at)}});
    const restored=await current(fn);assert.equal(restored.active_revision_id,first.revision_id);assert.equal(restored.config.handler,'src/handlers.echo');
    assert.equal(restored.config.cpu,.5);assert.equal(restored.environment.CURRENT,'kept');assert.deepEqual(restored.secret_names,['CURRENT_SECRET']);
    const history=await call(`/api/functions/${fn.id}/revisions`,{token:read});
    assert.equal(history.items.find(row=>row.active).archive_sha256,ordinaryHash);
    assert.equal(history.items.find(row=>row.id===second.revision_id).archive_sha256,slowHash);
  });
  await check('Suppression explicite des seules révisions inactives',async()=>{
    await call(`/api/functions/${fn.id}/revisions/${first.revision_id}`,{method:'DELETE',token:update,status:409});
    await call(`/api/functions/${fn.id}/revisions/${second.revision_id}`,{method:'DELETE',token:update});
    const history=await call(`/api/functions/${fn.id}/revisions`,{token:read});assert.deepEqual(history.items.map(row=>row.id),[first.revision_id]);
  });
  await check('Huit candidats maximum par fonction',async()=>{
    const limited=await create(service,'limit');
    for(let i=0;i<8;i++)await prepare(limited,createOnly);
    const row=await current(limited);
    await call(`/api/functions/${limited.id}/deployments`,{method:'POST',body:{config:row.config},token:createOnly,
      headers:{'If-Match':String(row.updated_at)},status:429});
  });
  completed=true;
} finally {
  try {
    for(const fn of functions.reverse()) {
      const history=await call(`/api/functions/${fn.id}/revisions`);
      for(const row of history.items)archives.push({function_id:fn.id,revision_id:row.id});
      await call(`/api/functions/${fn.id}`,{method:'DELETE'});
    }
    for(const token of tokens)await call(`/api/tokens/${token.id}/revoke`,{method:'POST'});
    for(const service of services.reverse())await call(`/api/services/${service.id}`,{method:'DELETE'});
    if(namespace)await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});
    if(work)await rm(work,{recursive:true,force:true});
    clean=true;
  } finally {
    await admin.dispose();await caller.dispose();
    await writeFile(report,JSON.stringify({completed:completed&&clean,checks,cleanup:clean,skipped:0,
      retained_archives:archives,remaining_proofs:['Expiration, limites globales et révisions','Reprise après crash pendant upload/validation','Déconnexion admin concurrente','UI et déploiement CLI complet','Code exécuté après rollback et valeur secrète conservée sous le même nom','Arrêt pendant nettoyage et exclusivité du contrôle']},null,2)+'\n');
  }
}
assert(completed&&clean);
