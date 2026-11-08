// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#lecture-et-périmètre
// @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// Real management API, real adapter publication, Docker invocation and public purges.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e'),base='https://serverless.lelabs.tech';
const prefix='function-catalogue-api-'+randomUUID().slice(0,8),secret='catalogue-secret-'+randomUUID(),variable='catalogue-variable-'+randomUUID(),run=promisify(execFile);
const namespaces=[],services=[],functions=[],archives=[],checks=[],observations=[],cleanupErrors=[],tokens=[];
let session,work,completed=false;
await mkdir(out,{recursive:true,mode:0o700});const report=path.join(out,'function-catalogue-api.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
const caller=await request.newContext({baseURL:base,timeout:120000});
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const r=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers}});
  assert((Array.isArray(status)?status:[status]).includes(r.status()),method+' '+url+': '+r.status());const text=await r.text(),data=JSON.parse(text);
  // A caller-supplied search literal is echoed in criteria; metadata must not reveal stored values.
  if(url.startsWith('/api/functions?'))assert(!JSON.stringify(data.items??[]).includes(secret));else assert(!text.includes(secret));
  return data;
}
async function query(values={}){return api('/api/functions?'+new URLSearchParams({q:prefix,...values}));}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function namespace(name,description=''){
  const row=await api('/api/namespaces',{method:'POST',body:{name,description},status:201});namespaces.push(row);return row;
}
async function service(parent,name,description=''){
  const row=await api(`/api/namespaces/${parent.id}/services`,{method:'POST',body:{name,description},status:201});services.push(row);return row;
}
async function credential(service,rights){const row=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'catalogue-access',rights},status:201});tokens.push(row.token);return row.token;}
async function until(action,label){const end=Date.now()+90000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(r=>setTimeout(r,100));}assert.fail(label);}
async function purge(row){
  let r=await admin.get(`/api/archives/${row.id}`);
  if(r.status()===404){await until(async()=>!(await api(`/api/functions/${row.id}/instances`)).items.length,'Instances actives');await api(`/api/functions/${row.id}`,{method:'DELETE'});r=await admin.get(`/api/archives/${row.id}`);}
  assert.equal(r.status(),200);let archived=await r.json();
  if(!archived.purged_at){
    row.purgeId??=randomUUID();let op=await api(`/api/storage-operations/${row.purgeId}`,{status:[200,404]});
    if(!op?.id)op=await api(`/api/archives/${row.id}/purge`,{method:'POST',body:{operation_id:row.purgeId,confirm_name:archived.name},status:[200,202],headers:{'If-Match':String(archived.updated_at)}});
    await until(async()=>{const v=await api(`/api/storage-operations/${op.id}`);assert.notEqual(v.state,'failed');return v.state==='completed';},'Purge inachevée');
    archived=await api(`/api/archives/${row.id}`);
  }
  assert(archived.purged_at&&archived.artifact_bytes===0&&!archived.storage_operation);
  if(!archives.some(v=>v.function_id===row.id))archives.push({function_id:row.id,namespace_id:row.namespace_id,operation_id:row.purgeId});
}
try{
  session=await api('/api/session');assert(session.authenticated);
  const first=await namespace(prefix+'-a','Été Café littéral_% "voyage"'),second=await namespace(prefix+'-b','Autre espace');
  const a=await service(first,'alpha','Description première'),b=await service(first,'beta','Service second'),c=await service(second,'alpha','Homonyme');
  for(let i=0;i<5;i++)await namespace(prefix+'-lookup-'+i);
  for(let i=0;i<5;i++)await service(first,'lookup-'+i);
  for(const [parent,count] of [[a,27],[b,3],[c,2]])for(let i=0;i<count;i++){
    const row=await api(`/api/services/${parent.id}/functions`,{method:'POST',status:201,body:{name:i?'entry-'+String(i).padStart(2,'0'):'same',config:{handler:i===26?'other.export':'handler.handler',idle_seconds:0}}});
    functions.push({...row,namespace_id:parent.namespace_id});
  }
  await api(`/api/services/${a.id}/configuration`,{method:'PUT',body:{environment:{NEVER_INDEX_VARIABLE:variable},secrets:{NEVER_INDEX_SECRET:secret}},headers:{'If-Match':String(a.updated_at)}});
  const full=await credential(a,['read','create','update']),read=await credential(a,['read']);
  await check('Session administrateur requise sur les trois catalogues, jetons techniques refusés',async()=>{
    for(const url of ['/api/functions','/api/catalogue/namespaces','/api/catalogue/services'])for(const token of [null,read,full,'invalid-token']){
      const response=await caller.get(url,{headers:token?{'X-Serverless-Token':token}:{}});assert.equal(response.status(),401);
      assert(!await response.text().then(text=>text.includes(prefix)));
    }
    assert.equal((await query()).total,32);
  });
  await check('Recherche globale avant pagination, homonymes et métadonnées minimales',async()=>{
    const page=await query();assert.equal(page.items.length,25);assert.equal(page.total,32);
    const next=await query({offset:25});assert.equal(next.items.length,7);
    assert.equal(new Set([...page.items,...next.items].map(v=>v.id)).size,32);
    const same=await query({q:prefix+' same'});assert.equal(same.total,3);assert.equal(new Set(same.items.map(v=>v.service.id)).size,3);
    for(const row of [...page.items,...next.items])assert.deepEqual(Object.keys(row).sort(),['handler','id','name','namespace','revision_id','service','state','updated_at']);
    observations.push({scenario:'pagination',first:page,second:next});
    const durations=[];for(let i=0;i<3;i++){const start=performance.now();assert.equal((await query({limit:100})).total,32);durations.push(Math.round((performance.now()-start)*1000)/1000);}
    observations.push({scenario:'catalogue-read-cost',active_functions:32,samples:3,https_roundtrip_milliseconds:durations,includes_network_authentication_and_json:true,isolated_sql_measurement:false});
  });
  await check('Unicode, descriptions, UUID, handler, mots ET, caractères littéraux et absence de secrets',async()=>{
    assert.equal((await query({q:'ETE CAFE '+prefix})).total,30);
    assert.equal((await query({q:'e\u0301te\u0301 CAFE '+prefix})).total,30);
    assert.equal((await query({q:'littéral_% '+prefix})).total,30);
    assert.equal((await query({q:'"voyage" '+prefix})).total,30);
    for(const [q,total] of [[functions[0].id,1],[a.id,27],[second.id,2],['other.export '+prefix,1],['never_index_secret',0],['never_index_variable',0],[secret,0],[variable,0],["' OR 1=1 --",0]])assert.equal((await query({q})).total,total);
    assert.equal((await query({q:prefix.toUpperCase()})).total,32);
    for(const values of [{q:'x'.repeat(201)},{q:'a b c d e f g h i'},{q:'nul\0'},{limit:0},{limit:101},{offset:-1},{offset:2147483648},{sort:'name;DROP TABLE functions'},{state:'invalid'},{namespace_id:'invalid'},{service_id:'invalid'}])await api('/api/functions?'+new URLSearchParams(values),{status:422});
    assert.equal((await query({offset:2147483647})).items.length,0);
  });
  await check('Filtres namespace/service/état combinés, UUID inconnus et aucun élargissement',async()=>{
    assert.equal((await query({namespace_id:first.id})).total,30);assert.equal((await query({service_id:b.id})).total,3);
    assert.equal((await query({namespace_id:first.id,service_id:b.id,state:'draft'})).total,3);
    assert.equal((await query({namespace_id:second.id,service_id:a.id})).total,0);
    assert.equal((await query({state:'published'})).total,0);
    const unknown=randomUUID(),page=await query({namespace_id:unknown});assert.equal(page.total,0);assert.deepEqual(page.selected.namespace,{id:unknown,available:false});
  });
  await check('Quatre tris stables et pagination sans doublon sous noms identiques',async()=>{
    for(const sort of ['name_asc','name_desc','updated_asc','updated_desc']){
      const page=await query({sort,limit:100}),again=await query({sort,limit:100});assert.deepEqual(page.items,again.items);
      const one=await query({sort,limit:17}),two=await query({sort,limit:17,offset:17});assert.deepEqual([...one.items,...two.items].map(v=>v.id),page.items.map(v=>v.id));
      const values=page.items.map(v=>sort.startsWith('name')?v.name.toLowerCase():v.updated_at);
      assert.deepEqual(values,[...values].sort((x,y)=>(x<y?-1:x>y?1:0)*(sort.endsWith('desc')?-1:1)));
    }
  });
  await check('Sélecteurs de parents recherchés et paginés sur toutes leurs données',async()=>{
    for(const kind of ['namespaces','services']){
      const endpoint='/api/catalogue/'+kind+'?',values={q:kind==='namespaces'?prefix:'lookup',...(kind==='services'?{namespace_id:first.id}:{})};
      const one=await api(endpoint+new URLSearchParams({...values,limit:5}));
      assert.equal(one.total,kind==='namespaces'?7:5);assert.equal(one.items.length,5);
      const two=await api(endpoint+new URLSearchParams({...values,limit:5,offset:5}));assert.equal(two.items.length,kind==='namespaces'?2:0);
      await api(endpoint+'limit=51',{status:422});await api(endpoint+'offset=-1',{status:422});await api(endpoint+'q='+encodeURIComponent('a b c d e f g h i'),{status:422});
    }
    assert.equal((await api('/api/catalogue/services?'+new URLSearchParams({namespace_id:first.id}))).total,7);
  });
  await check('Publication réelle A/B, catalogue de la révision active, invocation Docker et rollback',async()=>{
    work=await mkdtemp(path.join(out,'function-catalogue-code-'));await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
    await writeFile(path.join(work,'serverless.yml'),JSON.stringify({service:a.name,provider:{name:'p2enjoy',runtime:'node24',p2enjoy:{idle_seconds:0}},functions:{same:{handler:'handler.handler'}},package:{patterns:['!**','*.cjs','revision.json']}}));
    const revisions=[];
    for(const version of ['a','b']){
      await writeFile(path.join(work,'revision.json'),JSON.stringify({name:version}));
      const result=await run('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',a.id],{cwd:root,timeout:300000,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:full}});
      assert(!result.stdout.includes(secret)&&!tokens.some(v=>result.stdout.includes(v)));const published=JSON.parse(result.stdout);assert(published.completed);revisions.push(published.results[0].revision_id);
      const page=await query({q:functions[0].id,state:'published'});assert.equal(page.total,1);assert.equal(page.items[0].revision_id,revisions.at(-1));
      const response=await caller.get('/invoke/'+functions[0].id,{headers:{'X-Serverless-Token':read}});assert.equal(response.status(),200);assert.equal((await response.json()).revision,version);
    }
    const current=await api('/api/functions/'+functions[0].id);await api(`/api/functions/${current.id}/rollback`,{method:'POST',body:{revision_id:revisions[0]},headers:{'If-Match':String(current.updated_at)}});
    assert.equal((await query({q:current.id})).items[0].revision_id,revisions[0]);
    const response=await caller.get('/invoke/'+current.id,{headers:{'X-Serverless-Token':read}});assert.equal(response.status(),200);assert.equal((await response.json()).revision,'a');
    observations.push({scenario:'publication-and-rollback',function_id:current.id,revisions});
  });
  await check('Renommage et suppression relus sans index ni résultats obsolètes',async()=>{
    const row=await api('/api/functions/'+functions[1].id);await api('/api/functions/'+row.id,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:'renamed-entry',config:row.config}});
    assert.equal((await query({q:row.id})).items[0].name,'renamed-entry');await purge(functions[1]);assert.equal((await query({q:row.id})).total,0);
    const empty=namespaces.at(-1);await api('/api/namespaces/'+empty.id,{method:'DELETE'});empty.deleted=true;
    assert.equal((await api('/api/catalogue/namespaces?'+new URLSearchParams({q:empty.id}))).total,0);
    assert.equal((await query({namespace_id:empty.id})).total,0);
  });
  completed=true;
}catch{throw new Error('function_catalogue_api_failed');}
finally{
  for(const row of functions)try{await purge(row);}catch(error){cleanupErrors.push({function_id:row.id,error:error.name});}
  for(const row of services)try{
    const current=await api('/api/services/'+row.id);
    await api(`/api/services/${row.id}/configuration`,{method:'PUT',body:{environment:{},replace_secrets:true,secrets:{}},headers:{'If-Match':String(current.updated_at)}});
    await api('/api/services/'+row.id,{method:'DELETE'});
  }catch(error){cleanupErrors.push({service_id:row.id,error:error.name});}
  for(const row of namespaces)if(!row.deleted)try{await api('/api/namespaces/'+row.id,{method:'DELETE'});}catch(error){cleanupErrors.push({namespace_id:row.id,error:error.name});}
  if(work)await rm(work,{recursive:true,force:true});await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({completed:completed&&!cleanupErrors.length,checks,observations,cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,skipped:0,
    namespaces:namespaces.map(v=>v.id),service_ids:services.map(v=>v.id),function_ids:functions.map(v=>v.id),storage_archives:archives},null,2)+'\n');
}
assert(completed&&!cleanupErrors.length);
