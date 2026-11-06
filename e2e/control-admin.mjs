// @spec docs/CONTROL.md#preuves | docs/SCHEMA.md | docs/BACKLOG.md#sls-020
// @verifies docs/CONTROL.md#preuves | docs/SCHEMA.md | docs/BACKLOG.md#sls-020
// Uses a real admin session obtained by authorize.mjs and real scoped tokens.
import {purgeStorageArchive} from './storage-archives.mjs';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {randomUUID} from 'node:crypto';
import {request} from 'playwright';

const base = 'https://serverless.lelabs.tech';
const output = new URL('../.local/e2e/',import.meta.url);
await mkdir(output,{recursive:true,mode:0o700});
await writeFile(new URL('control-admin.json',output),JSON.stringify({completed:false,error:'Campagne non terminée'})+'\n');
const storageState = JSON.parse(await readFile(new URL('admin-session.json',output),'utf8'));
const admin = await request.newContext({baseURL:base,storageState});
const caller = await request.newContext({baseURL:base});
const stateResponse = await admin.get('/api/session');
const session = await stateResponse.json();
assert(session.authenticated,'Une vraie connexion administrateur est requise.');
const csrf = session.csrf_token;
const prefix = `qa-${randomUUID().slice(0,8)}`;
const storageArchives=[],deletedFunctions=[];
const checks = [], functions = new Map(), services = [], tokens = [];
let namespace, a, b, first, second, read, create, update, remove, full, restricted, completed=false;

async function call(path,{method='GET',body,token,headers={},status=200,anonymous=false}={}) {
  const client = token || anonymous ? caller : admin;
  const response = await client.fetch(path,{
    method,data:body,
    headers: token ? {'X-Serverless-Token':token,...headers} : anonymous ? headers : {'Origin':base,'X-CSRF-Token':csrf,...headers},
  });
  assert.equal(response.status(),status,`${method} ${path} : statut attendu ${status}`);
  return response.json();
}

async function check(name,action) {
  const started = Date.now();
  try {await action(); checks.push({name,status:'passed',duration_ms:Date.now()-started}); console.log('PASS',name);}
  catch (error) {checks.push({name,status:'failed',error:error.name}); throw error;}
}

async function makeFunction(service,name,token,configuration) {
  const row = await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,token,
    body:{name,config:{handler:'src/handlers.echo'},...(configuration ? {configuration} : {})}});
  functions.set(row.id,row); return row;
}

async function makeToken(service,name,rights,extra={}) {
  const row = await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights,...extra}});
  assert.match(row.token,/^p2s_[A-Za-z0-9_-]{43}$/);
  tokens.push(row);return row;
}

try {
  await check('Namespace : création, lecture, conflit et modification',async () => {
    namespace = await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix,description:'Qualification réelle'}});
    assert.equal((await call(`/api/namespaces/${namespace.id}`)).name,prefix);
    await call('/api/namespaces',{method:'POST',status:409,body:{name:prefix}});
    namespace = await call(`/api/namespaces/${namespace.id}`,{method:'PUT',body:{name:prefix,description:'Persistée'},headers:{'If-Match':String(namespace.updated_at)}});
    assert.equal(namespace.description,'Persistée');
  });
  await check('Services : création et refus de suppression du parent occupé',async () => {
    for (const suffix of ['a','b']) services.push(await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:`${prefix}-${suffix}`}}));
    [a,b] = services;
    await call(`/api/namespaces/${namespace.id}`,{method:'DELETE',status:409});
  });
  await check('CSRF : jeton absent, incorrect et origine étrangère refusés',async () => {
    for (const headers of [{'X-CSRF-Token':''},{'X-CSRF-Token':'invalid'},{'Origin':'https://untrusted.invalid'}])
      await call(`/api/services/${a.id}`,{method:'PUT',status:403,headers,body:{name:a.name}});
    assert.equal((await call(`/api/services/${a.id}`)).name,a.name);
  });
  await check('Politique : origines exactes, IPv4/IPv6, ET/OU et données invalides',async () => {
    a = await call(`/api/services/${a.id}`,{method:'PUT',body:{name:a.name,policy:{origins:['https://app.example.com:443','https://app.example.com'],ips:['192.0.2.4/24','2001:db8::/32'],combination:'or'}}});
    assert.deepEqual(a.policy.origins,['https://app.example.com']);
    assert.deepEqual(a.policy.ips,['192.0.2.0/24','2001:db8::/32']);
    for (const policy of [{origins:['https://app.example.com/path']},{ips:['not-an-ip']},{origins:['https://*.example.com']},{combination:'xor'}])
      await call(`/api/services/${a.id}`,{method:'PUT',body:{name:a.name,policy},status:422});
  });
  await check('Concurrence : une modification obsolète ne rétablit pas la politique',async () => {
    const stale = a;
    a = await call(`/api/services/${a.id}`,{method:'PUT',headers:{'If-Match':String(a.updated_at)},body:{name:a.name,policy:{origins:['https://restricted.example.com']}}});
    await call(`/api/services/${a.id}`,{method:'PUT',headers:{'If-Match':String(stale.updated_at)},body:{name:a.name,description:'Stale',policy:stale.policy},status:409});
    assert.deepEqual((await call(`/api/services/${a.id}`)).policy.origins,['https://restricted.example.com']);
  });
  await check('Jetons : création de chaque droit et lecture sans valeur complète',async () => {
    read = await makeToken(a,'read',['read']); create = await makeToken(a,'create',['create']);
    update = await makeToken(a,'update',['update']); remove = await makeToken(a,'delete',['delete']);
    full = await makeToken(a,'all',['create','read','update','delete']);
    const listing = await call(`/api/services/${a.id}/tokens`);
    assert.equal(listing.items.length,5);
    assert(listing.items.every(row => !('token' in row) && !('digest' in row)));
    for (const token of tokens) assert(!JSON.stringify(listing).includes(token.token));
  });
  await check('Create : création seule, casse préservée et refus des autres opérations',async () => {
    first = await makeFunction(a,`${prefix}-CamelCase`,create.token);
    second = await makeFunction(a,`${prefix}-second`,full.token);
    assert.equal(first.name,`${prefix}-CamelCase`);
    await call(`/api/functions/${first.id}`,{token:create.token,status:403});
    await call(`/api/functions/${first.id}`,{method:'PUT',token:create.token,body:{name:first.name},status:403});
    await call(`/api/functions/${first.id}`,{method:'DELETE',token:create.token,status:403});
  });
  await check('Read : lectures autorisées, mutations et accès globaux refusés',async () => {
    assert.equal((await call(`/api/functions/${first.id}`,{token:read.token})).id,first.id);
    assert.equal((await call(`/api/services/${a.id}/functions`,{token:read.token})).items.length,2);
    await call(`/api/services/${a.id}/functions`,{method:'POST',token:read.token,body:{name:'forbidden'},status:403});
    await call(`/api/functions/${first.id}`,{method:'PUT',token:read.token,body:{name:first.name},status:403});
    await call(`/api/functions/${first.id}`,{method:'DELETE',token:read.token,status:403});
    await call('/api/namespaces',{token:read.token,status:401});
    await call(`/api/services/${a.id}/tokens`,{token:read.token,status:401});
    await call(`/api/services/${a.id}`,{method:'PUT',token:full.token,body:{name:a.name},status:401});
  });
  await check('Étanchéité : service et fonction étrangers refusés',async () => {
    const foreign = await makeFunction(b,`${prefix}-foreign`);
    await call(`/api/services/${b.id}`,{token:full.token,status:403});
    await call(`/api/services/${b.id}/functions`,{method:'POST',token:full.token,body:{name:'forbidden'},status:403});
    await call(`/api/functions/${foreign.id}`,{token:full.token,status:403});
    await call(`/api/functions/${foreign.id}`,{method:'DELETE',token:full.token,status:403});
  });
  await check('Update : configuration globale et secrets expurgés',async () => {
    const value = `secret-${randomUUID()}`;
    const configured = await call(`/api/services/${a.id}/configuration`,{method:'PUT',token:update.token,body:{environment:{PUBLIC_LABEL:'qualification'},secrets:{PRIVATE_VALUE:value}}});
    assert.deepEqual(configured.secret_names,['PRIVATE_VALUE']);
    assert(!JSON.stringify(configured).includes(value));
    const listed = await call(`/api/services/${a.id}`,{token:read.token});
    assert.equal(listed.environment.PUBLIC_LABEL,'qualification');
    assert(!JSON.stringify(listed).includes(value));
    await call(`/api/services/${a.id}/configuration`,{method:'PUT',token:update.token,body:{environment:{PRIVATE_VALUE:'collision'}},status:422});
    const deleted = await call(`/api/services/${a.id}/configuration`,{method:'PUT',token:update.token,body:{secrets:{PRIVATE_VALUE:null}}});
    assert.deepEqual(deleted.secret_names,[]);
    assert.equal(deleted.environment.PUBLIC_LABEL,'qualification');
  });
  await check('Fonction : ressources, variables, secrets et conflit de version',async () => {
    const before = await call(`/api/functions/${first.id}`,{token:read.token});
    const secret = `function-secret-${randomUUID()}`;
    first = await call(`/api/functions/${first.id}`,{method:'PUT',token:update.token,headers:{'If-Match':String(before.updated_at)},body:{name:first.name,
      config:{...first.config,timeout_seconds:2.5,memory_mib:384,cpu:.123,storage:{data:{enabled:true,quota_mib:4},cache:{enabled:true,quota_mib:2},concurrency:'exclusive'}},
      configuration:{environment:{FUNCTION_LABEL:'real'},secrets:{FUNCTION_SECRET:secret}}}});
    assert.equal(first.config.cpu,.123);assert.equal(first.config.timeout_seconds,2.5);
    assert.deepEqual(first.secret_names,['FUNCTION_SECRET']);assert(!JSON.stringify(first).includes(secret));
    await call(`/api/functions/${first.id}`,{method:'PUT',token:update.token,headers:{'If-Match':String(before.updated_at)},body:{name:first.name},status:409});
    assert.equal((await call(`/api/functions/${first.id}`,{token:read.token})).config.cpu,.123);
  });
  await check('Validation : bornes, stockage exclusif, handler et champ inconnu',async () => {
    for (const config of [{memory_mib:127},{memory_mib:8193},{cpu:0},{cpu:1.01},{timeout_seconds:0},{idle_seconds:-1},{concurrency:2,max_instances:1},
      {min_instances:3,max_instances:2},{concurrency:2,max_instances:2,storage:{data:{enabled:true},concurrency:'exclusive'}},{handler:'../escape.handler'},{runtime:'node20'},{unexpected:'value'}])
      await call(`/api/functions/${first.id}`,{method:'PUT',token:update.token,body:{name:first.name,config},status:422});
    await call(`/api/services/${a.id}/configuration`,{method:'PUT',token:update.token,body:{environment:{'bad-name':'value'}},status:422});
    const error = await call(`/api/services/${a.id}/configuration`,{method:'PUT',token:update.token,body:{secrets:{bad:'x'.repeat(16385)}},status:422});
    assert(!JSON.stringify(error).includes('x'.repeat(100)));
  });
  await check('Portée fonction : liste filtrée, opérations étrangères et globales refusées',async () => {
    restricted = await makeToken(a,'restricted',['read','update','delete'],{function_ids:[first.id]});
    assert.deepEqual((await call(`/api/services/${a.id}/functions`,{token:restricted.token})).items.map(row => row.id),[first.id]);
    await call(`/api/functions/${second.id}`,{token:restricted.token,status:403});
    await call(`/api/functions/${second.id}`,{method:'DELETE',token:restricted.token,status:403});
    await call(`/api/services/${a.id}/configuration`,{method:'PUT',token:restricted.token,body:{environment:{X:'y'}},status:403});
    for (const body of [{name:'invalid',rights:['create'],function_ids:[first.id]},{name:'invalid',rights:['read'],function_ids:[]},
      {name:'invalid',rights:[]},{name:'invalid',rights:['read','read']},{name:'invalid',rights:['read'],expires_at:1},
      {name:'invalid',rights:['read'],function_ids:[...functions.values()].filter(row => row.service_id===b.id).map(row => row.id)}])
      await call(`/api/services/${a.id}/tokens`,{method:'POST',body,status:422});
  });
  await check('Pagination et conflits concurrents réels',async () => {
    const listing = await call(`/api/services/${a.id}/functions?limit=1&offset=1`,{token:read.token});
    assert.equal(listing.items.length,1);
    const path = `/api/services/${a.id}/functions`, name = `${prefix}-concurrent`;
    const responses = await Promise.all([0,1].map(() => caller.post(path,{data:{name},headers:{'X-Serverless-Token':full.token}})));
    assert.deepEqual(responses.map(r => r.status()).sort(),[201,409]);
    for (const response of responses) if (response.status()===201) {const row=await response.json();functions.set(row.id,row);}
    await call(`/api/services/${a.id}/functions?limit=101`,{token:read.token,status:422});
  });
  await check('Delete : suppression autorisée et service occupé protégé',async () => {
    await call(`/api/services/${a.id}`,{method:'DELETE',status:409});
    const disposable = await makeFunction(a,`${prefix}-delete`,create.token);
    await call(`/api/functions/${disposable.id}`,{method:'DELETE',token:remove.token});functions.delete(disposable.id);deletedFunctions.push(disposable.id);
    await call(`/api/functions/${disposable.id}`,{token:read.token,status:403});
    await call(`/api/functions/${first.id}`,{token:remove.token,status:403});
  });
  await check('Audit : refus corrélés, pagination et portée fonction',async () => {
    const audit = await call(`/api/services/${a.id}/audit?limit=100`,{token:read.token});
    assert(audit.items.some(row => row.action==='request.denied' && row.actor_id===full.id));
    assert(audit.items.some(row => row.action==='function.create'));
    for (const token of tokens) assert(!JSON.stringify(audit).includes(token.token));
    const limited = await call(`/api/services/${a.id}/audit?limit=100`,{token:restricted.token});
    assert(limited.items.every(row => row.object_id===first.id));
  });
  await check('Rotation et révocation immédiates',async () => {
    const rotated = await call(`/api/tokens/${read.id}/rotate`,{method:'POST',status:201});tokens.push(rotated);
    await call(`/api/services/${a.id}`,{token:read.token,status:401});
    await call(`/api/services/${a.id}`,{token:rotated.token});
    await call(`/api/tokens/${read.id}/rotate`,{method:'POST',status:409});
    await call(`/api/tokens/${rotated.id}/revoke`,{method:'POST'});
    await call(`/api/services/${a.id}`,{token:rotated.token,status:401});
  });
  await check('Expiration réelle du jeton',async () => {
    const short = await makeToken(a,'expires',['read'],{expires_at:Date.now()/1000+3});
    await call(`/api/services/${a.id}`,{token:short.token});
    await new Promise(resolve => setTimeout(resolve,3200));
    await call(`/api/services/${a.id}`,{token:short.token,status:401});
    await call(`/api/tokens/${short.id}/rotate`,{method:'POST',status:409});
  });
  await check('Redémarrage Docker : session, CSRF, objets et secrets persistants',async () => {
    await promisify(execFile)('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','spark-docker@10.77.0.24',
      'docker restart serverless-api'],{timeout:45000});
    let ready=false;
    for (let attempt=0;attempt<60;attempt++) {try {const r=await caller.get('/healthz');if (r.ok()) {ready=true;break;}} catch {}
      await new Promise(resolve => setTimeout(resolve,500));}
    assert(ready,'Le contrôle doit reprendre après redémarrage.');
    const resumed=await call('/api/session');assert(resumed.authenticated);assert.equal(resumed.csrf_token,csrf);
    assert.equal((await call(`/api/namespaces/${namespace.id}`)).description,'Persistée');
    const row=await call(`/api/functions/${first.id}`,{token:full.token});assert.deepEqual(row.secret_names,['FUNCTION_SECRET']);assert.equal(row.config.cpu,.123);
  });
  completed=true;
} finally {
  const cleanupErrors=[];
  for (const [id] of functions) {try {await call(`/api/functions/${id}`,{method:'DELETE'});deletedFunctions.push(id);} catch {cleanupErrors.push(`function:${id}`);}}
  for(const id of deletedFunctions){try{storageArchives.push(await purgeStorageArchive(id,namespace.id));}catch{cleanupErrors.push('storage:'+id);}}
  for (const service of services) {try {await call(`/api/services/${service.id}`,{method:'DELETE'});} catch {cleanupErrors.push(`service:${service.id}`);}}
  if (namespace) {try {await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});} catch {cleanupErrors.push(`namespace:${namespace.id}`);}}
  await admin.dispose();await caller.dispose();
  await writeFile(new URL('control-admin.json',output),JSON.stringify({target:base,completed:completed && !cleanupErrors.length,checks,cleanupErrors,skipped:0,storage_archives:storageArchives,namespace_id:namespace?.id,function_ids:[...functions.keys(),...deletedFunctions]},null,2)+'\n');
  assert.deepEqual(cleanupErrors,[],'Nettoyage des objets de qualification requis.');
}
