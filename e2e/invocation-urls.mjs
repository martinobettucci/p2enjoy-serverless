// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#qualification-réelle-et-autorité
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#api-et-calcul-commun
// Focused API/CLI checkpoint on actual currently assigned domains, not the full route lifecycle proof.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',prefix='invocation-addresses-'+randomUUID().slice(0,8);
const report=path.join(out,'invocation-urls.json');
await mkdir(out,{recursive:true,mode:0o700});
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
const caller=await request.newContext({baseURL:base,timeout:120000});
const session=await (await admin.get('/api/session')).json();assert(session.authenticated,'real_admin_session_required');
const checks=[],observations=[],tokens=[],functions=[],archives=[],cleanupErrors=[];
let namespace,service,foreign,work,manifest,full,read,completed=false;
const codeSecret=randomUUID();
const canonical = page => {const item=page.items.find(row=>row.origin===base);assert(item,'canonical_domain_required');return item;};
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),method+' '+url+': '+response.status());
  const raw=await response.text();assert(!raw.includes(codeSecret));return JSON.parse(raw);
}
async function asToken(url,credential,status=200,headers={}){
  const response=await caller.get(url,{headers:{...(credential?{'X-Serverless-Token':credential}:{}),...headers}});
  assert.equal(response.status(),status,'token GET '+url);
  const raw=await response.text();assert(!raw.includes(codeSecret));
  for(const token of tokens)assert(!raw.includes(token));
  return JSON.parse(raw);
}
async function token(name,rights,extra={},target=service){
  const result=await api(`/api/services/${target.id}/tokens`,{method:'POST',body:{name,rights,...extra},status:201});
  tokens.push(result.token);return result;
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
async function deploy(){
  await writeFile(path.join(work,'serverless.yml'),JSON.stringify(manifest));
  const result=await new Promise(resolve=>execFile('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',service.id],
    {cwd:root,timeout:300000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:full}},
    (error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr})));
  assert.equal(result.code,0,'real_deployment_exit');
  for(const value of [codeSecret,...tokens])assert(!result.stdout.includes(value)&&!result.stderr.includes(value));
  const value=JSON.parse(result.stdout);assert(value.completed);return value;
}
async function catalogue(id,query=''){
  const endpoint=`/api/functions/${id}/invocation-urls`;
  if(query)return asToken(endpoint+query,read);
  const first=await asToken(endpoint+'?limit=20',read),items=[...first.items];
  for(let offset=20;offset<first.total;offset+=20){
    const page=await asToken(endpoint+`?limit=20&offset=${offset}`,read);
    assert.equal(page.source.sha256,first.source.sha256);assert.equal(page.revision_id,first.revision_id);assert.equal(page.total,first.total);
    items.push(...page.items);
  }
  return {...first,items};
}
async function invoke(url,method='GET',expected='one'){
  const response=await caller.fetch(url,{method,headers:{'X-Serverless-Token':read}});
  assert.equal(response.status(),200,'real_docker_invocation');
  if(method!=='HEAD')assert.equal((await response.json()).revision,expected);
}
async function purge(row){
  const archived=await api(`/api/archives/${row.id}`);
  let op=await api(`/api/archives/${row.id}/purge`,{method:'POST',body:{operation_id:randomUUID(),confirm_name:archived.name},
    status:[200,202],headers:{'If-Match':String(archived.updated_at)}});
  const deadline=Date.now()+90000;
  while(op.state!=='completed'&&Date.now()<deadline){assert.notEqual(op.state,'failed');await new Promise(resolve=>setTimeout(resolve,200));op=await api(`/api/storage-operations/${op.id}`);}
  assert.equal(op.state,'completed');return {function_id:row.id,namespace_id:namespace.id,operation_id:op.id};
}
try{
  work=await mkdtemp(path.join(out,'invocation-addresses-code-'));
  await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
  await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'one'}));
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix},status:201});
  service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:prefix},status:201});
  service=await api(`/api/services/${service.id}/configuration`,{method:'PUT',body:{secrets:{ADDRESS_SECRET:codeSecret}},headers:{'If-Match':String(service.updated_at)}});
  foreign=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:prefix+'-other'},status:201});
  full=(await token('publication',['read','create','update'])).token;
  read=(await token('invocation',['read'])).token;
  let draft=await api(`/api/services/${service.id}/functions`,{method:'POST',body:{name:'implicit-entry',config:{handler:'handler.handler'}},status:201});functions.push(draft.id);
  const endpoint=`/api/functions/${draft.id}/invocation-urls`;
  await check('Brouillon : domaines réels mais aucune URL appelable',async()=>{
    const page=await catalogue(draft.id);assert.equal(page.function_state,'draft');assert.equal(page.revision_id,null);
    assert.equal(page.source.state,'available');assert(page.total>=1);assert(page.items.every(row=>row.urls.length===0));
    assert.equal(page.console_url,base+`/console/functions/${draft.id}/invocation-urls`);
    observations.push({scenario:'draft',catalogue:page});
  });
  await check('Read requis : anonymat, droits CRUD seuls, portée, service et révocation',async()=>{
    await asToken(endpoint,null,401);
    for(const id of [draft.id,randomUUID()]){await asToken(`/api/functions/${id}/invocation-urls`,null,401);await asToken(`/api/functions/${id}/invocation-urls`,'invalid-token',401);}
    for(const right of ['create','update','delete'])await asToken(endpoint,(await token(right,[right])).token,403);
    await asToken(endpoint,(await token('wrong-service',['read'],{},foreign)).token,403);
    const other=await api(`/api/services/${service.id}/functions`,{method:'POST',body:{name:'other-entry',config:{handler:'handler.handler'}},status:201});functions.push(other.id);
    const scoped=await token('scoped',['read'],{function_ids:[other.id]});await asToken(endpoint,scoped.token,403);
    await asToken(`/api/functions/${other.id}/invocation-urls`,scoped.token);
    const revoked=await token('revoked',['read']);await api(`/api/tokens/${revoked.id}/revoke`,{method:'POST'});await asToken(endpoint,revoked.token,401);
    const allowed=await token('allowed',['read'],{function_ids:[draft.id]});await asToken(endpoint,allowed.token);
  });
  await check('Validation des bornes et X-Forwarded-Host étranger sans influence sur les domaines',async()=>{
    for(const query of ['?limit=0','?limit=21','?limit=abc','?offset=-1','?offset=10001'])await asToken(endpoint+query,read,422);
    const normal=await catalogue(draft.id),spoofed=await asToken(endpoint,read,200,{'X-Forwarded-Host':'untrusted.invalid'});
    assert.deepEqual(normal.items,spoofed.items);assert.equal(normal.source.sha256,spoofed.source.sha256);
    const end=await catalogue(draft.id,'?limit=20&offset=10000');assert.deepEqual(end.items,[]);assert.equal(end.total,normal.total);
    const first=await catalogue(draft.id,'?limit=1');assert.equal(first.items.length,1);assert.equal(first.total,normal.total);
    await asToken(`/api/functions/${randomUUID()}/invocation-urls`,read,403);
    await api(`/api/functions/${randomUUID()}/invocation-urls`,{status:404});
  });
  manifest={service:prefix,provider:{name:'p2enjoy',runtime:'node24'},functions:{'implicit-entry':{handler:'handler.handler'},
    'explicit-entry':{handler:'handler.handler',events:[{http:{path:'Orders/submit',method:'post'}},{http:{path:'Orders/read',method:'get'}}]}},package:{patterns:['!**','*.cjs','revision.json']}};
  let first,second,explicit;
  await check('CLI : publication et catalogue identique à celui de la console',async()=>{
    const result=await deploy();first=result.results[0];explicit=result.results[1];functions.push(explicit.function_id);
    for(const row of result.results){
      assert.equal(row.state,'published');assert.equal(row.invocation_urls.state,'available');
      const page=await catalogue(row.function_id,'?limit=20');
      assert.deepEqual(row.invocation_urls.items,page.items);assert.equal(row.invocation_urls.source_sha256,page.source.sha256);
      assert.equal(row.invocation_urls.revision_id,row.revision_id);observations.push({scenario:'published',catalogue:page});
    }
    const page=await catalogue(first.function_id);assert.equal(canonical(page).urls[0].url,base+'/invoke/'+first.function_id);
    const paths=canonical(await catalogue(explicit.function_id)).urls;
    assert.deepEqual(paths.map(row=>[row.url,row.methods]),[[base+'/invoke/'+explicit.function_id+'/Orders/read',['GET']],[base+'/invoke/'+explicit.function_id+'/Orders/submit',['POST']]]);
  });
  await check('Appels des vraies adresses : entrée implicite, casse, chemins et méthodes',async()=>{
    for(const item of (await catalogue(first.function_id)).items)await invoke(item.urls[0].url);
    for(const item of (await catalogue(explicit.function_id)).items)for(const entry of item.urls)await invoke(entry.url,entry.methods[0]);
    const wrong=await caller.get('/invoke/'+explicit.function_id+'/Orders/submit',{headers:{'X-Serverless-Token':read}});assert.equal(wrong.status(),405);
    const wrongCase=await caller.get('/invoke/'+explicit.function_id+'/orders/read',{headers:{'X-Serverless-Token':read}});assert.equal(wrongCase.status(),404);
  });
  await check('Renommage : l’adresse implicite conserve son UUID',async()=>{
    const row=await api(`/api/functions/${first.function_id}`);
    await api(`/api/functions/${row.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:'implicit-renamed',config:row.config}});
    const page=await catalogue(row.id);assert.equal(canonical(page).urls[0].url,base+'/invoke/'+row.id);await invoke(canonical(page).urls[0].url);
    manifest.functions['implicit-renamed']=manifest.functions['implicit-entry'];delete manifest.functions['implicit-entry'];
  });
  await check('Nouvelle révision puis rollback : événements et code de la même révision',async()=>{
    await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'two'}));
    manifest.functions['explicit-entry'].events=[{http:{path:'Revised/read',method:'get'}}];
    const result=await deploy();second=result.results.find(row=>row.name==='explicit-entry');
    const page=await catalogue(explicit.function_id);assert.equal(page.revision_id,second.revision_id);
    assert.equal(canonical(page).urls[0].url,base+'/invoke/'+explicit.function_id+'/Revised/read');await invoke(canonical(page).urls[0].url,'GET','two');
    const row=await api(`/api/functions/${explicit.function_id}`);
    await api(`/api/functions/${row.id}/rollback`,{method:'POST',body:{revision_id:explicit.revision_id},headers:{'If-Match':String(row.updated_at)}});
    const rollback=await catalogue(row.id);assert.equal(rollback.revision_id,explicit.revision_id);
    assert(canonical(rollback).urls.every(entry=>entry.url.includes('/Orders/')));await invoke(canonical(rollback).urls[0].url);
    observations.push({scenario:'rollback',catalogue:rollback});
  });
  await check('Suppression : catalogue refusé sans ancienne adresse conservée',async()=>{
    const other=functions.find(id=>id!==draft.id&&id!==explicit.function_id);
    await api(`/api/functions/${other}`,{method:'DELETE'});await api(`/api/functions/${other}/invocation-urls`,{status:404});
    await asToken(`/api/functions/${other}/invocation-urls`,read,403);
    archives.push(await purge({id:other}));functions.splice(functions.indexOf(other),1);
  });
  completed=true;
}catch{
  throw new Error('invocation_url_campaign_failed');
}finally{
  if(service){
    try{
      const remaining=(await api(`/api/services/${service.id}/functions?limit=100`)).items.map(row=>row.id);
      for(const id of remaining)if(!functions.includes(id))functions.push(id);
      for(const id of remaining){try{const row=await api(`/api/functions/${id}`);await api(`/api/functions/${id}`,{method:'DELETE'});archives.push(await purge(row));}catch(error){cleanupErrors.push({function_id:id,error:error.name});}}
      await api(`/api/services/${service.id}`,{method:'DELETE'});
    }catch(error){cleanupErrors.push({resource:'service',error:error.name});}
  }
  if(foreign)try{await api(`/api/services/${foreign.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'foreign-service',error:error.name});}
  if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'namespace',error:error.name});}
  if(work)await rm(work,{recursive:true,force:true});
  await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({completed:completed&&!cleanupErrors.length,scope:'assigned-domains-api-cli-checkpoint',checks,observations,skipped:0,
    cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,service_id:service?.id,function_ids:[...new Set([...functions,...archives.map(row=>row.function_id)])],storage_archives:archives},null,2)+'\n');
  assert.equal(cleanupErrors.length,0,'cleanup_required');
}
