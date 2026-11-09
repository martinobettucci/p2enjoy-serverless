// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues | docs/manual.md#adresses-d-appel
// Every helper follows this contract: real UI, normal HTTPS and native CLI only.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,stat} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium,request} from 'playwright';
import {enterNamespaces} from './console-navigation.mjs';

const base='https://serverless.lelabs.tech',root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const [mode,folder]=process.argv.slice(2);assert(['ui','cli'].includes(mode)&&process.argv.length===4,'mode_and_guard_folder_required');
const names=['serverless.lelabs.tech','functions.lelabs.tech',...Array.from({length:4},(_,i)=>`functions-pagination-${i+1}.lelabs.tech`)].sort();
const prefix=`invocation-pagination-${mode}-`+randomUUID().slice(0,8),checks=[],evidence=[],captures={},faults=[],pending=[],tokens=[],cleanupErrors=[];
let browser,context,page,session,namespace,service,fn,work,completed=false,cleanup=false,activeTask;
const digest=value=>createHash('sha256').update(value).digest('hex');
async function save(){await writeFile(new URL(`invocation-pagination-${mode}.json`,out),JSON.stringify({target:base,prefix,completed:completed&&cleanup&&!faults.length,cleanup,cleanup_errors:cleanupErrors,
  checks,skipped:0,evidence,captures,faults,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[]},null,2)+'\n',{mode:0o600});}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(e){checks.push({name,status:'failed',error:e.name});await save();throw e;}}
function watch(promise){const tracked=promise.then(value=>({value}),error=>({error}));pending.push(tracked);return tracked;}
async function observed(promise){const row=await promise;if(row.error)throw row.error;return row.value;}
async function api(path,{method='GET',body,status=200,headers={}}={}){const r=await context.request.fetch(base+path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers},timeout:120000});
  assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);return r.json();}
async function until(action,timeout=120000){const end=Date.now()+timeout;while(Date.now()<end){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,100));}assert.fail('real_lifecycle_deadline');}
async function created(path,action){const waiting=watch(page.waitForResponse(r=>r.url()===base+path&&r.request().method()==='POST'));await action();assert.equal((await observed(waiting)).status(),201);
  const kind=path.split('/').at(-1);await page.waitForURL(new RegExp('/console/'+kind+'/[0-9a-f-]{36}(?:/|$)'));return {id:new URL(page.url()).pathname.split('/')[3]};}
async function capture(name,fullPage=true){if(fullPage)await page.evaluate(()=>scrollTo(0,0));const file=new URL(`invocation-pagination-${name}.jpg`,out);
  const bytes=await page.screenshot({path:file.pathname,type:'jpeg',quality:85,fullPage});captures[file.pathname.split('/').at(-1)]={sha256:digest(bytes),viewport:page.viewportSize(),full_page:fullPage};}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'document_overflow');}
async function readyCode(){await page.waitForFunction(()=>{const b=document.querySelector('.publication-view button.primary');return b&&!b.disabled;});}
async function readyUrls(){await page.getByRole('heading',{name:'Adresses d’appel',exact:true}).waitFor();await page.waitForFunction(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent==='Actualiser');return b&&!b.disabled;});}
const cards=()=>page.locator('.observation-list>li');
async function pageNames(){return cards().locator('h3').allTextContents();}
async function credential(name,rights){const row=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights}});tokens.push(row);return row;}
async function invoke(url,token,hash,marker){const response=await context.request.get(url,{headers:{'X-Serverless-Token':token},timeout:120000});assert.equal(response.status(),200);assert.equal((await response.json()).revision,marker);
  assert.equal(response.headers()['x-serverless-code-hash'],hash);evidence.push({invoked_url:url,code_hash:hash,invocation_id:response.headers()['x-serverless-request-id']});await save();}
async function copyAndInvoke(item,token,hash,pinned){const domain=await item.locator('h3').innerText();const button=item.getByRole('button',{name:'Copier l’adresse',exact:true});await button.focus();await page.keyboard.press('Enter');
  await item.getByText('Adresse copiée.',{exact:true}).waitFor();const url=await page.evaluate(()=>navigator.clipboard.readText());assert.equal(new URL(url).origin,'https://'+domain);assert.equal(new URL(url).pathname,`/invoke/${fn.id}${pinned?'@'+hash:''}`);
  await invoke(url,token,hash,'pagination-ui');return url;}
async function advance(direction,expectedPage,count){const nav=page.getByRole('navigation',{name:'Domaines d’appel',exact:true});const button=nav.getByRole('button',{name:direction,exact:true});await button.focus();await page.keyboard.press('Enter');await readyUrls();
  await nav.getByText(`Page ${expectedPage} sur 2 · 6 domaines`,{exact:true}).waitFor();assert.equal(await cards().count(),count);assert.equal(await page.evaluate(()=>document.activeElement?.id),'invocation-urls-title');assert.equal(await page.locator('.notice.success').count(),0);await fits();}

async function ui(){let published,hash,reader;
  await check('Accueil, formulaires et promotion explicite : cinq domaines réels sur la première page',async()=>{
    await enterNamespaces(page,base);await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(prefix);
    namespace=await created('/api/namespaces',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());await save();await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('domain-pagination');
    service=await created(`/api/namespaces/${namespace.id}/services`,()=>dialog.getByRole('button',{name:'Enregistrer',exact:true}).click());await save();await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('invoke-through-paginated-domains');await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    fn=await created(`/api/services/${service.id}/functions`,()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());await save();
    await page.getByRole('button',{name:'Modifier l’exécution',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Inactivité avant extinction (s)',{exact:true}).fill('0');const changed=watch(page.waitForResponse(r=>r.url()===base+`/api/functions/${fn.id}`&&r.request().method()==='PUT'));
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();assert.equal((await observed(changed)).status(),200);await dialog.waitFor({state:'hidden'});
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Adresses d’appel',exact:true}).click();await readyUrls();
    await page.getByText('Aucune cible par défaut. Dans Code et révisions, choisissez les adresses d’un hash disponible ou promouvez une version.',{exact:true}).waitFor();assert.equal(await cards().count(),0);
    await page.getByRole('link',{name:'Choisir une version dans Code et révisions',exact:true}).click();await readyCode();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();dialog=page.getByRole('dialog');
    await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(work+'/function.zip');await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();
    const uploaded=watch(page.waitForResponse(r=>r.request().method()==='PUT'&&/^\/api\/deployments\/[0-9a-f-]{36}\/artifact$/.test(new URL(r.url()).pathname),{timeout:120000}));await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();const response=await observed(uploaded);assert.equal(response.status(),200);
    published=await api(new URL(response.url()).pathname.replace('/artifact',''));assert.equal(published.state,'published');assert(published.validation.valid&&published.validation.container_removed);hash=published.code_hash;assert.match(hash,/^[a-f0-9]{64}$/);
    await dialog.waitFor({state:'hidden'});await readyCode();await page.getByRole('region',{name:'Code de la fonction',exact:true}).getByText('Nouvelle version publiée.',{exact:true}).waitFor();assert.equal((await api(`/api/functions/${fn.id}`)).active_revision_id,null);
    const card=page.getByRole('article',{name:'Version '+hash,exact:true});await card.getByRole('button',{name:'Promouvoir cette version',exact:true}).first().click();const promotion=watch(page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}/promote`));
    await card.locator('.confirm').getByRole('button',{name:'Promouvoir cette version',exact:true}).click();assert.equal((await observed(promotion)).status(),200);await readyCode();await card.getByText('Cible par défaut',{exact:true}).waitFor();
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Adresses d’appel',exact:true}).click();await readyUrls();await page.getByText('Page 1 sur 2 · 6 domaines',{exact:true}).waitFor();assert.equal(await cards().count(),5);
    assert.deepEqual(await pageNames(),names.slice(0,5));const nav=page.getByRole('navigation',{name:'Domaines d’appel',exact:true});assert(await nav.getByRole('button',{name:'Précédente',exact:true}).isDisabled());assert(await nav.getByRole('button',{name:'Suivante',exact:true}).isEnabled());
    reader=await credential('invoke-paginated-addresses',['read']);await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});await fits();await capture('first-desktop');evidence.push({publication_id:published.id,revision_id:published.revision_id,code_hash:hash,first_page:await pageNames()});
  });
  await check('Seconde page réelle, retour clavier et copies natives : six domaines invoqués',async()=>{
    for(let i=0;i<5;i++)await copyAndInvoke(cards().nth(i),reader.token,hash,false);
    await advance('Suivante',2,1);assert.deepEqual(await pageNames(),names.slice(5));const nav=page.getByRole('navigation',{name:'Domaines d’appel',exact:true});assert(await nav.getByRole('button',{name:'Suivante',exact:true}).isDisabled());assert(await nav.getByRole('button',{name:'Précédente',exact:true}).isEnabled());await copyAndInvoke(cards().first(),reader.token,hash,false);
    await cards().first().getByRole('button',{name:'Copier l’exemple curl',exact:true}).click();await cards().first().getByText('Exemple copié.',{exact:true}).waitFor();const curl=await page.evaluate(()=>navigator.clipboard.readText());assert(curl.includes('VOTRE_JETON')&&!curl.includes(reader.token));assert(curl.includes('https://'+names[5]+'/invoke/'+fn.id));
    await cards().first().getByText('Exemple curl',{exact:true}).click();assert.equal(await cards().first().locator('pre').innerText(),curl);await capture('second-desktop');
    await page.getByRole('navigation',{name:'Domaines d’appel',exact:true}).scrollIntoViewIfNeeded();await capture('second-navigation-desktop',false);await advance('Précédente',1,5);assert.deepEqual(await pageNames(),names.slice(0,5));
  });
  await check('Hash explicite conservé sur deux pages mobiles et copie du dernier domaine',async()=>{
    await page.getByRole('link',{name:'Choisir une version dans Code et révisions',exact:true}).click();await readyCode();await page.getByRole('article',{name:'Version '+hash,exact:true}).getByRole('link',{name:'Adresses de cette version',exact:true}).click();await readyUrls();assert.equal(new URL(page.url()).searchParams.get('version'),hash);
    await page.setViewportSize({width:390,height:844});await fits();assert.equal(await cards().count(),5);await capture('first-mobile');await advance('Suivante',2,1);assert.equal(new URL(page.url()).searchParams.get('version'),hash);await copyAndInvoke(cards().first(),reader.token,hash,true);
    await capture('second-mobile');await cards().first().scrollIntoViewIfNeeded();await capture('second-card-mobile',false);await page.getByRole('navigation',{name:'Domaines d’appel',exact:true}).scrollIntoViewIfNeeded();await capture('second-navigation-mobile',false);
    await advance('Précédente',1,5);assert.deepEqual(await pageNames(),names.slice(0,5));assert.equal(new URL(page.url()).searchParams.get('version'),hash);await fits();assert.equal(faults.length,0);
  });
}

async function startCli(token,boundary){
  const manifest=work+'/serverless.yml',events=[];let stderr='',ended=false;
  const child=spawn('python3',['-B',new URL('e2e/adapter-catalogue-barrier.py',root).pathname,manifest,service.id,...(boundary===6?[]:[String(boundary)])],
    {cwd:root.pathname,detached:true,stdio:['pipe','pipe','pipe'],env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:token}});
  child.stdin.on('error',()=>{});const kill=()=>{try{process.kill(-child.pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')throw e;}};
  const timer=setTimeout(kill,300000);let bytes=0;
  createInterface({input:child.stdout}).on('line',line=>{bytes+=line.length;try{assert(bytes<4*1024**2);events.push(JSON.parse(line));}catch{events.push({event:'protocol-error'});kill();}});
  child.stderr.on('data',data=>{stderr+=data.toString();if(stderr.length>1024**2)kill();});
  const done=new Promise(resolve=>{child.once('error',()=>{ended=true;clearTimeout(timer);resolve(-1);});child.once('close',code=>{ended=true;clearTimeout(timer);resolve(code);});});
  const alive=()=>{try{process.kill(-child.pid,0);return true;}catch(e){if(e.code==='ESRCH')return false;throw e;}};
  const task={events,done,settled:false,async gate(){return until(()=>{assert(!events.some(e=>e.event==='protocol-error'));const v=events.find(e=>e.event==='gated');assert(v||!ended,'cli_ended_before_boundary');return v;});},release(){child.stdin.end('release\n');},async join(){
    const code=await done;await until(()=>!alive(),10000);task.settled=true;assert.equal(code,0,'native_tracer_exit');assert(!tokens.some(t=>stderr.includes(t.token)),'private_stderr');assert.equal(stderr,'');
    const finished=events.find(e=>e.event==='finished');assert(finished?.child_reaped);assert.equal(finished.exit_code,0);assert.equal(finished.https_connect_attempts,boundary);assert.equal(finished.connect_results.length,boundary);assert(finished.connect_results.every(v=>[0,-115].includes(v)));
    assert(!tokens.some(t=>finished.stdout.includes(t.token)||finished.stderr.includes(t.token)),'private_cli_output');const report=JSON.parse(finished.stdout);assert.equal(report.completed,true);evidence.push({native_cli:{boundary,events:events.filter(e=>e.event!=='finished'),exit_code:0,connect_results:finished.connect_results,group_gone:true,report}});await save();return report;
  },async abort(){if(alive())kill();await done;await until(()=>!alive(),10000);task.settled=true;}};activeTask=task;return task;
}
async function cli(){
  namespace=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await save();service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'domain-pagination'}});await save();
  fn=await api(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'invoke-paginated-domains',config:{handler:'handler.handler',idle_seconds:0}}});await save();
  await writeFile(work+'/serverless.yml',JSON.stringify({service:'domain-pagination',provider:{name:'p2enjoy',runtime:'node24'},functions:{'invoke-paginated-domains':{handler:'handler.handler',p2enjoy:{idle_seconds:0}}},package:{patterns:['!**','handler.cjs','revision.json']}}));
  let first;const publisher=await credential('publish-and-read-domains',['read','create','update']),reader=await credential('invoke-cli-domains',['read']);
  await check('CLI et deux vrais GET : six domaines épinglés, six invocations Docker',async()=>{
    const task=await startCli(publisher.token,7),gated=await task.gate();assert.equal(gated.boundary,'before-seventh-https-connect');assert.equal(gated.prior_connect_results.length,6);task.release();const result=await task.join();assert.equal(result.results.length,1);first=result.results[0];
    assert.equal(first.state,'published');assert.equal(first.function_id,fn.id);assert.equal(first.invocation_urls.state,'available');assert.equal(first.invocation_urls.total,6);assert.deepEqual(first.invocation_urls.items.map(i=>i.domain).sort(),names);assert.equal((await api(`/api/functions/${fn.id}`)).active_revision_id,null);
    for(const item of first.invocation_urls.items){assert(item.urls.length>0);for(const entry of item.urls)await invoke(entry.url,reader.token,first.code_hash,'pagination-cli');}
  });
  await check('Frontière historique avant six : vrai401 facultatif et publication dédupliquée conservée',async()=>{
    const disposable=await credential('publish-then-revoke',['read','create','update']);const task=await startCli(disposable.token,6);assert.equal((await task.gate()).boundary,'before-sixth-https-connect');await api(`/api/tokens/${disposable.id}/revoke`,{method:'POST'});task.release();const result=await task.join(),row=result.results[0];
    assert.equal(row.state,'published');assert.equal(row.function_id,fn.id);assert.equal(row.revision_id,first.revision_id);assert.equal(row.code_hash,first.code_hash);assert.equal(row.code_changed,false);assert.deepEqual(row.invocation_urls,{state:'unavailable',error:{code:'http_401',status:401}});assert(!row.error);
  });
  await check('Changement réel entre les pages : succès de publication conservé sans adresses partielles',async()=>{
    const before=await api(`/api/functions/${fn.id}/invocation-urls?version=${first.code_hash}&limit=5&offset=0`);assert.equal(before.total,6);assert.equal(before.items.length,5);
    const task=await startCli(publisher.token,7);await task.gate();const changed=await run('python3',['-B',new URL('e2e/invocation-pagination-domains.py',root).pathname,'remove-route','--folder',folder,'--domain','functions-pagination-4.lelabs.tech'],{timeout:90000,maxBuffer:1024**2});
    const receipt=JSON.parse(changed.stdout);assert(receipt.completed&&receipt.objects.route_deleted);task.release();const result=await task.join(),row=result.results[0];assert.equal(row.state,'published');assert.equal(row.function_id,fn.id);assert.equal(row.revision_id,first.revision_id);assert.equal(row.code_hash,first.code_hash);assert.equal(row.code_changed,false);assert(!row.error);
    assert.deepEqual(row.invocation_urls,{state:'unavailable',error:{code:'invocation_catalogue_changed'}});
    const after=await api(`/api/functions/${fn.id}/invocation-urls?version=${first.code_hash}&limit=5&offset=0`);assert.equal(after.total,5);assert.notEqual(after.source.sha256,before.source.sha256);assert.equal(after.revision_id,first.revision_id);
    evidence.push({route_removal:receipt,before,after});const pinned=first.invocation_urls.items.find(i=>i.domain==='serverless.lelabs.tech').urls[0].url;await invoke(pinned,reader.token,first.code_hash,'pagination-cli');
  });
}

await mkdir(out,{recursive:true,mode:0o700});assert(!(await stat(new URL(`invocation-pagination-${mode}.json`,out)).then(()=>true,()=>false)),'existing_report_requires_archiving');await save();
try{
  const state=JSON.parse(await readFile(new URL('admin-session.json',out),'utf8'));
  if(mode==='ui'){browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',e=>faults.push(e.name));}
  else{const client=await request.newContext({baseURL:base,storageState:state,timeout:120000});context={request:client,dispose:()=>client.dispose()};}
  session=await api('/api/session');assert(session.authenticated,'real_admin_sso_required');work=await mkdtemp(new URL(`invocation-pagination-${mode}-code-`,out).pathname);
  await cp(new URL('qualification/artifacts/invocation-addresses.cjs',root),work+'/handler.cjs');await writeFile(work+'/revision.json',JSON.stringify({name:'pagination-'+mode}));
  if(mode==='ui')await run('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(p/'function.zip','w');[z.write(p/n,n) for n in ('handler.cjs','revision.json')];z.close()",work]);
  if(mode==='ui')await ui();else await cli();completed=true;
}catch(error){evidence.push({failure:{type:error.name,message:error.message.split('\n')[0].replaceAll(tokens.map(t=>t.token).find(t=>error.message.includes(t))??'\u0000','[redacted]')}});if(page)try{await capture('failure-'+mode);}catch{}throw new Error('invocation_pagination_'+mode+'_failed');}
finally{
  if(activeTask&&!activeTask.settled)try{await activeTask.abort();}catch(e){cleanupErrors.push({resource:'cli-process-group',error:e.name});}
  await Promise.all(pending);
  if(context&&session?.authenticated&&!cleanupErrors.length){
    try{if(!namespace)namespace=(await api('/api/namespaces?limit=100')).items.find(r=>r.name===prefix);if(namespace&&!service)service=(await api(`/api/namespaces/${namespace.id}/services?limit=100`)).items.find(r=>r.name==='domain-pagination');
      if(service&&!fn)fn=(await api(`/api/services/${service.id}/functions?limit=100`)).items.find(r=>r.name===(mode==='ui'?'invoke-through-paginated-domains':'invoke-paginated-domains'));}catch(e){cleanupErrors.push({resource:'campaign-identity',error:e.name});}
    for(const t of tokens)try{await api(`/api/tokens/${t.id}/revoke`,{method:'POST'});}catch(e){cleanupErrors.push({resource:'token',error:e.name});}
    if(fn)try{await until(async()=>!(await api(`/api/functions/${fn.id}/instances`)).items.length);await api(`/api/functions/${fn.id}`,{method:'DELETE'});const archive=await api(`/api/archives/${fn.id}`),operation=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archive.updated_at)},body:{operation_id:randomUUID(),confirm_name:archive.name}});
      await until(async()=>{const v=await api(`/api/storage-operations/${operation.id}`);assert.notEqual(v.state,'failed');return v.state==='completed';});const final=await api(`/api/archives/${fn.id}`);assert(final.purged_at&&final.artifact_bytes===0);evidence.push({purged:{function_id:fn.id,operation_id:operation.id}});
    }catch(e){cleanupErrors.push({resource:'function',error:e.name});}
    if(service)try{await api(`/api/services/${service.id}`,{method:'DELETE'});}catch(e){cleanupErrors.push({resource:'service',error:e.name});}
    if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(e){cleanupErrors.push({resource:'namespace',error:e.name});}
  }
  if(work&&!cleanupErrors.length)await rm(work,{recursive:true,force:true});await browser?.close();if(mode==='cli')await context?.dispose();cleanup=!cleanupErrors.length;await save();assert(cleanup&&!faults.length,'cleanup_or_browser_fault');
}
