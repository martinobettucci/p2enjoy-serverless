// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues | docs/SCHEDULES.md#facette-planifications | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues
// @verifies docs/BACKLOG.md#sls-096 | docs/CONSOLE_MANUAL.md#preuves-attendues
// Actual UTC boundaries and HTTPS/Docker; no clock, network or dependency substitution.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rename,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request,chromium} from 'playwright';
const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),root=new URL('../',import.meta.url);
const run=promisify(execFile),checks=[],captures={},functions=[],cleanupErrors=[],firings=[];
let admin,caller,session,namespace,service,token,updateToken,work,browser,context,page,completed=false;
const prefix='scheduled-functions-'+randomUUID().slice(0,8),report=new URL(prefix+'.json',out);
async function save(){const pending=new URL(prefix+'.pending',out);await writeFile(pending,JSON.stringify({completed,skipped:0,checks,captures,cleanup_errors:cleanupErrors,
  namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),firings},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function call(path,{method='GET',body,bytes,credential,status=200,headers={}}={}){
  const response=await (credential?caller:admin).fetch(path,{method,data:bytes??body,headers:{...(credential?{'X-Serverless-Token':credential}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()}`);return response.json();
}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name});await save();throw error;}}
async function until(action,deadline=Date.now()+120000){while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,500));}assert.fail('real_lifecycle_deadline');}
async function publish(fn,events){const current=await call(`/api/functions/${fn.id}`);
  const candidate=await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(current.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-event.handler',events}});
  const result=await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:await readFile(new URL('.serverless-p2/probe.zip',work))});
  assert.match(result.code_hash,/^[0-9a-f]{64}$/);return result;
}
async function promote(fn,hash){const row=await call(`/api/functions/${fn.id}`);return call(`/api/functions/${fn.id}/versions/${hash}/promote`,{method:'POST',headers:{'If-Match':String(row.updated_at)}});}
async function capture(name){const file=new URL(prefix+'-'+name+'.jpg',out);await page.screenshot({path:file.pathname,type:'jpeg',quality:85});captures[file.pathname.split('/').at(-1)]=createHash('sha256').update(await readFile(file)).digest('hex');}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
async function purge(fn){let row=await call(`/api/functions/${fn.id}`);await call(`/api/functions/${fn.id}`,{method:'PUT',body:{name:row.name,config:{...row.config,min_instances:0,idle_seconds:0}},headers:{'If-Match':String(row.updated_at)}});
  await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length);
  await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation);
  row=await call(`/api/archives/${fn.id}`);const command=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
  await until(async()=>{const state=await call(`/api/storage-operations/${command.id}`);assert.notEqual(state.state,'aborted');return state.state==='completed';});
  const archive=await call(`/api/archives/${fn.id}`);assert.equal(archive.artifact_bytes,0);assert.equal(archive.revision_count,0);
}
await mkdir(out,{recursive:true});await save();
try {
  const state=JSON.parse(await readFile(new URL('admin-session.json',out),'utf8'));
  admin=await request.newContext({baseURL:base,storageState:state,timeout:180000});caller=await request.newContext({baseURL:base,timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'real_sso_session_required');
  work=new URL((await mkdtemp(new URL(prefix+'-',out).pathname))+'/','file:');
  await writeFile(new URL('scheduled-event.cjs',work),await readFile(new URL('../qualification/artifacts/scheduled-event.cjs',import.meta.url)));
  await writeFile(new URL('serverless.yml',work),JSON.stringify({service:'scheduled-original',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'scheduled-event.handler'}},package:{patterns:['!**','scheduled-event.cjs']}}));
  await run('python3',['-B','-m','adapter','package','--config',new URL('serverless.yml',work).pathname],{cwd:root.pathname});
  const manifest=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',work),'utf8'));
  await rename(new URL('.serverless-p2/'+manifest.artifacts.probe.file,work),new URL('.serverless-p2/probe.zip',work));
  await check('Création réelle, pilote inactif, droits des lectures et validation des crons',async()=>{
    namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();
    service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'scheduled-original',policy:{origins:['https://blocked.invalid'],ips:['192.0.2.1/32'],combination:'and'}}});
    token=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'observe-schedules',rights:['read']}});
    updateToken=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'update-only',rights:['update']}});
    for(const name of ['five-minute','coalesced-minute','specific-utc']){
      const fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'scheduled-event.handler',cpu:0.125,memory_mib:128,timeout_seconds:10,idle_seconds:0,min_instances:0,max_instances:1,concurrency:1,queue_timeout_seconds:5}}});functions.push(fn);await save();
      await call(`/api/functions/${fn.id}/schedules`,{credential:updateToken.token,status:403});await call(`/api/functions/${fn.id}/schedules`,{status:401,credential:'p2s_'+randomUUID()});
      assert.equal((await call(`/api/functions/${fn.id}/schedules`,{credential:token.token})).items.length,0);
    }
    const fn=functions[0];const row=await call(`/api/functions/${fn.id}`);
    for(const cron of ['61 * * * *','* * * *','1-0 * * * *','*/0 * * * *','* * * * SUN']){
      await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:422,headers:{'If-Match':String(row.updated_at)},body:{deployment_id:randomUUID(),handler:'scheduled-event.handler',events:{http:[],schedules:[{cron,enabled:true,timezone:'UTC'}]}}});
    }
    const published=await publish(fn,{http:[],schedules:[{cron:'*/5 * * * *',enabled:true,timezone:'UTC'}]});fn.hash=published.code_hash;
    assert.equal((await call(`/api/functions/${fn.id}/schedules`)).items.length,0);assert.equal((await call(`/api/functions/${fn.id}/schedule-firings`)).total,0);
    await promote(fn,fn.hash);
  });
  let boundary;
  await check('Déclarations UTC, absence de HTTP, planification désactivée et préparation avant frontière',async()=>{
    // Complete all mutations before choosing the first fully eligible window.
    const second=functions[1];let result=await publish(second,{http:[],schedules:[{cron:'* * * * *',enabled:true,timezone:'UTC'}]});second.hash=result.code_hash;await promote(second,second.hash);
    const third=functions[2];boundary=(Math.floor(Date.now()/300000)+1)*300;
    if(boundary-Date.now()/1000<45) boundary+=300;
    const nominal=new Date(boundary*1000);const expression=`${nominal.getUTCMinutes()} ${nominal.getUTCHours()} * * ${nominal.getUTCDay()}`;
    result=await publish(third,{http:[],schedules:[{cron:expression,enabled:true,timezone:'UTC'},{cron:'* * * * *',enabled:false,timezone:'UTC'}]});third.hash=result.code_hash;await promote(third,third.hash);
    for(const fn of functions){const data=await call(`/api/functions/${fn.id}/schedules`,{credential:token.token});assert(data.items.length);assert.equal(data.items[0].code_hash,fn.hash);assert(data.items[0].next.nominal_at*1000>Date.now()-1000);}
    assert.equal((await call(`/api/functions/${third.id}/schedules`)).items[1].next,null);
    assert(Date.now()/1000<boundary,'fixtures_must_precede_boundary');
  });
  await check('Horloge réelle : premier tir, POST /, corps JSON, jetons absents et politique HTTP non appliquée',async()=>{
    for(const fn of functions){
      const firing=await until(async()=>{const rows=(await call(`/api/functions/${fn.id}/schedule-firings`)).items;return rows.find(v=>v.window_at===boundary&&v.state==='succeeded');},boundary*1000+45000);
      assert.equal(firing.coalesced,fn===functions[1]?Math.min(5,Math.floor((boundary-(await call(`/api/functions/${fn.id}/schedules`)).items[0].activated_at)/60)+1):1);
      assert(firing.dispatched_at>=firing.nominal_at);assert(firing.dispatched_at-boundary<=5);assert.equal(firing.code_hash,fn.hash);
      const invocation=(await call(`/api/functions/${fn.id}/invocations`)).items.find(v=>v.id===firing.invocation_id);assert(invocation);assert.equal(invocation.trigger,'schedule');assert.equal(invocation.schedule_slot,firing.nominal_at);assert.equal(invocation.resolved_code_hash,fn.hash);
      const witness=JSON.parse(invocation.logs.trim());assert.equal(witness.marker,'scheduled-original-A');assert.equal(witness.method,'POST');assert.equal(witness.path,'/');assert.deepEqual(witness.body,{});assert.equal(witness.trigger,'schedule');assert.equal(Date.parse(witness.slot)/1000,firing.nominal_at);assert(!witness.authorization_present&&!witness.platform_token_present);firings.push(firing);await save();
    }
  });
  await check('Deux frontières consécutives, fusion de cinq créneaux, instant précis non répété',async()=>{
    for(const fn of functions.slice(0,2)){const firing=await until(async()=>{const data=await call(`/api/functions/${fn.id}/schedule-firings`);return data.items.find(v=>v.window_at===boundary+300&&v.state==='succeeded');},(boundary+300)*1000+45000);assert.equal(firing.coalesced,fn===functions[1]?5:1);assert(firing.dispatched_at>=firing.nominal_at&&firing.dispatched_at-firing.window_at<=5);firings.push(firing);}
    const specific=await call(`/api/functions/${functions[2].id}/schedule-firings`);assert.equal(specific.total,1);assert.equal(specific.items[0].schedule_index,0);
  });
  await check('Parcours réel depuis accueil, facette, mobile et manuel conforme',async()=>{
    browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});page=await context.newPage();const faults=[];page.on('pageerror',e=>faults.push(e.name));
    await page.goto(base);await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
    await page.getByLabel('Rechercher une fonction').fill(functions[1].id);
    await page.getByRole('link',{name:functions[1].name,exact:true}).click();
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Planifications',exact:true}).click();
    await page.getByRole('heading',{name:'Planifications du manifeste',exact:true}).waitFor();
    await page.getByText('* * * * *',{exact:true}).first().waitFor();await fits();await capture('desktop');
    await page.setViewportSize({width:390,height:844});await fits();await capture('mobile');
    const menu=page.getByRole('button',{name:'Menu',exact:true});if(await menu.isVisible())await menu.click();
    await page.getByRole('link',{name:'Manuel d’usage',exact:true}).click();await page.getByRole('article',{name:'Guide d’utilisation'}).waitFor();
    const article=page.getByRole('article',{name:'Guide d’utilisation'});const bytes=await readFile(new URL('../docs/manual.md',import.meta.url));assert.equal(await article.getAttribute('data-manual-sha256'),createHash('sha256').update(bytes).digest('hex'));
    await page.getByRole('navigation',{name:'Sommaire',exact:true}).getByRole('link',{name:'Planifications du manifeste',exact:true}).click();await capture('manual-mobile');assert.deepEqual(faults,[]);
  });
  completed=true;
} finally {
  await context?.close();await browser?.close();
  for(const fn of functions){try{await purge(fn);}catch(error){cleanupErrors.push({function_id:fn.id,error:error.name});}}
  if(service&&!cleanupErrors.length){try{await call(`/api/services/${service.id}`,{method:'DELETE'});await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({parents:true,error:error.name});}}
  if(cleanupErrors.length)completed=false;await save();await admin?.dispose();await caller?.dispose();if(work)await rm(work,{recursive:true,force:true});
  console.log(JSON.stringify({completed,groups:checks.filter(v=>v.status==='passed').length,report:report.pathname,cleanup_errors:cleanupErrors.length}));
}
assert(completed);
