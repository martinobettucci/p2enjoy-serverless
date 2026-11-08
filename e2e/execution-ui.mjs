// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// @spec docs/BACKLOG.md#sls-061 | docs/CONSOLE_EXECUTION.md
// @verifies docs/BACKLOG.md#sls-061 | docs/CONSOLE_EXECUTION.md#preuves-attendues
// Real browser, SSO session, packaged original handler and Docker observations.
import {enterNamespaces} from './console-navigation.mjs';
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {chromium} from 'playwright';
import {purgeStorageArchive} from './storage-archives.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),output=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',prefix='invocation-'+randomUUID().slice(0,8),run=promisify(execFile);
const report=path.join(output,'execution-ui.json'),checks=[],faults=[],cleanupErrors=[],captures={},evidence=[],guards=[],pending=[];
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/execution-faults.py';
let browser,context,page,session,lastInstances,namespaceId,serviceId,functionId,work,token,revisionId,completed=false,cleanupCompleted=false,deleted=false,storageArchive;
const functionName='observer-'+randomUUID().replaceAll('-','')+'x'.repeat(22);
const secret='observation-secret-'+randomUUID();
async function save() {
  const value={target:base,completed:completed&&!cleanupErrors.length&&!faults.length,cleanup:cleanupCompleted&&!cleanupErrors.length,skipped:0,checks,faults,cleanupErrors,
    namespace_id:namespaceId,service_id:serviceId,function_id:functionId,revision_id:revisionId,last_instances:lastInstances,storage_archive:storageArchive,captures,evidence};
  const text=JSON.stringify(value,null,2);assert(!text.includes(secret));
  await writeFile(report+'.pending',text+'\n',{mode:0o600});await rename(report+'.pending',report);
}
async function check(name,action) {try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}
  catch(error){checks.push({name,status:'failed',error:error.name});await save();throw error;}}
async function until(action,message,seconds=60) {const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const result=await action();if(result)return result;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function manage(url,{method='GET',body,bytes,status=200,headers={}}={}) {
  const response=await context.request.fetch(base+url,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers},timeout:60000});
  assert.equal(response.status(),status,`Réponse ${method} ${url}: ${response.status()}`);
  const text=await response.text();assert(!text.includes(secret));return JSON.parse(text);
}
async function find(url,name){for(let offset=0;offset<=10000;offset+=100){const result=await manage(url+`?limit=100&offset=${offset}`);const found=result.items.find(row=>row.name===name);if(found)return found.id;if(result.items.length<100)return null;}throw new Error('cleanup_lookup_limit');}
async function update(config={},environment={}) {
  const fn=await manage(`/api/functions/${functionId}`);
  return manage(`/api/functions/${functionId}`,{method:'PUT',body:{name:fn.name,config:{...fn.config,...config},configuration:{environment,secrets:{OBSERVATION_SECRET:secret}}},headers:{'If-Match':String(fn.updated_at)}});
}
async function history(){return (await manage(`/api/functions/${functionId}/invocations?limit=100`)).items;}
function start(body={}) {
  const result=context.request.post(base+`/invoke/${functionId}`,{data:body,headers:{'X-Serverless-Token':token},timeout:60000})
    .then(async response=>({status:response.status(),id:response.headers()['x-serverless-request-id']}));
  pending.push(result.catch(()=>null));return result;
}
async function invoke(body={},expected=200){const value=await start(body);assert.equal(value.status,expected);evidence.push({invocation_id:value.id,http_status:value.status});return value.id;}
const rows=()=>page.locator('.observation-list>li');
const region=()=>page.getByRole('region',{name:/^(Instances|Invocations)$/});
async function loaded(){await page.waitForFunction(()=>document.querySelector('.panel [aria-busy]')?.getAttribute('aria-busy')==='false');}
async function observationAction(action) {
  const response=page.waitForResponse(value=>value.request().method()==='GET'&&new RegExp(`/api/functions/${functionId}/(instances|invocations)\\?`).test(value.url()));
  const [result]=await Promise.all([response,Promise.resolve().then(action)]);const data=await result.json();
  if(!result.ok())await page.getByRole('alert').waitFor();
  else await page.waitForFunction(ids=>document.querySelector('.panel [aria-busy]')?.getAttribute('aria-busy')==='false'&&JSON.stringify([...document.querySelectorAll('.observation-list h3')].map(node=>node.textContent))===JSON.stringify(ids),data.items.map(row=>row.id));
  return data;
}
async function tab(name){const action=()=>page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name,exact:true}).click();if(name==='Configuration'){await action();await page.getByRole('button',{name:'Modifier l’exécution',exact:true}).waitFor();}else return observationAction(action);}
async function refresh(){await observationAction(()=>region().getByRole('button',{name:/^(Actualiser|Réessayer)$/}).click());}
async function changePage(name){await observationAction(()=>region().getByRole('button',{name,exact:true}).click());await until(()=>region().getByRole('heading',{level:2}).evaluate(node=>document.activeElement===node),'Focus de pagination absent',5);}
const item=id=>page.getByRole('article',{name:`Invocation ${id}`,exact:true});
async function open(id){const row=item(id);await row.locator('summary').click();return row;}
async function capture(name){await page.evaluate(()=>window.scrollTo(0,0));const filename='execution-ui-'+name+'.jpg';const bytes=await page.screenshot({path:path.join(output,filename),type:'jpeg',quality:85,fullPage:true});captures[filename]=createHash('sha256').update(bytes).digest('hex');}
async function operator(mode,extra=[]){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,mode,functionId,...extra],{timeout:90000,maxBuffer:1024*1024});const value=JSON.parse(stdout.trim());evidence.push({operator:mode,value});return value;}
async function writer(){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,'hold-database',functionId],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false;createInterface({input:child.stdout}).on('line',line=>events.push(JSON.parse(line)));child.stderr.resume();
  const done=new Promise(resolve=>{child.on('exit',code=>{ended=true;resolve(code);});child.on('error',()=>{ended=true;resolve(-1);});});
  const guard={async release(){if(!ended)child.stdin.end('release\n');assert.equal(await done,0);}};guards.push(guard);
  await until(async()=>{assert(!ended,'Garde SQLite interrompue');return events.some(row=>row.event==='writer-locked');},'Verrou non observé',20);return guard;
}
await mkdir(output,{recursive:true,mode:0o700});await save();
try {
  const state=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});
  page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',error=>faults.push(error.name));
  session=await(await context.request.get(base+'/api/session')).json();assert(session.authenticated,'Session administrateur réelle requise');
  await check('Accueil, création réelle et facettes partageables vides',async()=>{
    await enterNamespaces(page,base);await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();
    let dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(prefix);const namespaceCreated=page.waitForResponse(response=>response.url()===base+'/api/namespaces'&&response.request().method()==='POST').then(response=>response.status());const [namespaceStatus]=await Promise.all([namespaceCreated,dialog.getByRole('button',{name:'Créer',exact:true}).click()]);assert.equal(namespaceStatus,201);namespaceId=await until(()=>find('/api/namespaces',prefix),'Création non retrouvée par API');
    await page.waitForURL(/\/console\/namespaces\//);await save();
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('observations');const serviceCreated=page.waitForResponse(response=>response.url()===base+`/api/namespaces/${namespaceId}/services`&&response.request().method()==='POST').then(response=>response.status());const [serviceStatus]=await Promise.all([serviceCreated,dialog.getByRole('button',{name:'Enregistrer',exact:true}).click()]);assert.equal(serviceStatus,201);serviceId=await until(()=>find(`/api/namespaces/${namespaceId}/services`,'observations'),'Création non retrouvée par API');
    await page.waitForURL(/\/console\/services\//);await save();
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(functionName);await dialog.getByLabel('Handler',{exact:true}).fill('observation.handler');const functionCreated=page.waitForResponse(response=>response.url()===base+`/api/services/${serviceId}/functions`&&response.request().method()==='POST').then(response=>response.status());const [functionStatus]=await Promise.all([functionCreated,dialog.getByRole('button',{name:'Créer',exact:true}).click()]);assert.equal(functionStatus,201);functionId=await until(()=>find(`/api/services/${serviceId}/functions`,functionName),'Création non retrouvée par API');
    await page.waitForURL(/\/console\/functions\//);await save();
    await tab('Instances');assert.equal(new URL(page.url()).pathname,`/console/functions/${functionId}/instances`);await page.getByText('Aucune instance réservée.',{exact:true}).waitFor();
    await tab('Invocations');await page.getByText('Aucune invocation enregistrée.',{exact:true}).waitFor();
    await page.reload();await loaded();assert(await page.getByRole('heading',{name:functionName,exact:true}).isVisible());await capture('empty');
  });
  await check('Publication réelle et six instances mesurées sur deux pages',async()=>{
    work=await mkdtemp(path.join(output,'observation-code-'));await cp(path.join(root,'qualification/artifacts/observation.cjs'),path.join(work,'observation.cjs'));
    const config=path.join(work,'serverless.yml');await writeFile(config,JSON.stringify({service:'observations',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{observer:{handler:'observation.handler'}},package:{patterns:['!**','observation.cjs']}}));
    await run('python3',['-B','-m','adapter','package','--config',config],{cwd:root});
    const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));const bytes=await readFile(path.join(work,'.serverless-p2',descriptor.artifacts.observer.file));
    const fn=await manage(`/api/functions/${functionId}`);
    const candidate=await manage(`/api/functions/${functionId}/deployments`,{method:'POST',status:201,headers:{'If-Match':String(fn.updated_at)},body:{config:{...fn.config,cpu:.05,memory_mib:128,min_instances:6,max_instances:6,concurrency:6,idle_seconds:30,timeout_seconds:30,queue_timeout_seconds:0},configuration:{secrets:{OBSERVATION_SECRET:secret}},events:{http:[{path:'observe',methods:['POST'],implicit:true}]}}});
    revisionId=(await manage(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes})).revision_id;
    token=(await manage(`/api/services/${serviceId}/tokens`,{method:'POST',status:201,body:{name:'invoke-observer',rights:['read']}})).token;
    const data=await until(async()=>{const value=await manage(`/api/functions/${functionId}/instances?limit=100`);lastInstances=value;return value.total===6&&value.items.every(row=>row.state==='ready')&&value;},'Six instances prêtes requises');
    assert(data.items.every(row=>row.cpu_nanos===50000000&&row.memory_mib===128));assert(data.items.some(row=>row.metrics?.memory_usage_bytes>0),'Mesure mémoire réelle requise');evidence.push({instances:data.items.map(row=>({id:row.id,cpu_nanos:row.cpu_nanos,memory_mib:row.memory_mib,metrics:row.metrics}))});
    const observed=await tab('Instances');assert.equal(await rows().count(),5);
    for(const measured of observed.items){const displayed=page.getByRole('article',{name:`Instance ${measured.id}`,exact:true});const memory=displayed.locator('dl>div').filter({has:page.getByText('Mémoire consommée',{exact:true})}).locator('dd');
      assert.equal(await memory.innerText(),measured.metrics?.memory_usage_bytes==null?'Indisponible':new Intl.NumberFormat('fr-FR',{maximumFractionDigits:3}).format(measured.metrics.memory_usage_bytes/1024**2)+' Mio');}
    assert(observed.items.some(row=>row.metrics?.memory_usage_bytes>0),'Mesure rendue positive requise');const first=await rows().locator('h3').allTextContents();
    assert.equal(await page.getByText('0,05 CPU',{exact:true}).count(),5);assert.equal(await page.getByText('128 Mio',{exact:true}).count(),5);await capture('instances-desktop');await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await capture('instances-mobile');await page.setViewportSize({width:1440,height:1000});
    await changePage('Suivante');assert.equal(await rows().count(),1);assert(!first.includes(await rows().locator('h3').innerText()));
    assert(await region().getByRole('heading',{name:'Instances',exact:true}).evaluate(node=>document.activeElement===node));
    assert.equal(await region().getByRole('button',{name:'Suivante',exact:true}).getAttribute('aria-disabled'),'true');
  });
  await check('Chargement et erreur réseau réels, reprise et focus conservé',async()=>{
    const cdp=await context.newCDPSession(page);await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:800,downloadThroughput:1000000,uploadThroughput:1000000});
    try{await region().getByRole('button',{name:'Actualiser',exact:true}).click();await page.getByText('Chargement des instances…',{exact:true}).waitFor();await capture('loading');await loaded();}
    finally{await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.detach();}
    assert(await region().getByRole('button',{name:'Actualiser',exact:true}).evaluate(node=>document.activeElement===node));
    await context.setOffline(true);
    try{await region().getByRole('button',{name:'Actualiser',exact:true}).click();await page.getByRole('alert').waitFor();assert.equal(await rows().count(),0);await capture('network-error');}
    finally{await context.setOffline(false);}
    await refresh();assert.equal(await rows().count(),1);assert(await region().getByRole('button',{name:'Actualiser',exact:true}).evaluate(node=>document.activeElement===node));
  });
  await check('Extinction réelle et recalage de page sans perte de focus',async()=>{
    await update({min_instances:0,max_instances:1,concurrency:1,idle_seconds:1});
    await until(async()=>(await manage(`/api/functions/${functionId}/instances`)).total===0,'Instances non éteintes');
    await refresh();await page.getByText('Aucune instance réservée.',{exact:true}).waitFor();
    assert(await region().getByRole('button',{name:'Actualiser',exact:true}).evaluate(node=>document.activeElement===node));
    assert.equal(await page.getByRole('navigation',{name:'Pagination des instances'}).count(),0);
    await update({idle_seconds:30});
  });
  let logId,longId,errorId,businessId;
  await check('Historique réel : page pleine, journal vide, erreur et HTTP métier séparés',async()=>{
    await invoke();logId=await invoke({action:'logs'});errorId=await invoke({action:'error'},502);businessId=await invoke({status:503},503);longId=await invoke({action:'many-logs'});
    await tab('Invocations');assert.equal(await rows().count(),5);assert.equal(await region().getByRole('button',{name:'Suivante',exact:true}).getAttribute('aria-disabled'),'true');
    const business=await open(businessId);assert(await business.getByText('Terminée',{exact:true}).isVisible());assert((await business.innerText()).includes('HTTP 503'));await business.getByText('Aucun journal collecté.',{exact:true}).waitFor();
    const error=await open(errorId);await error.getByText('Échec',{exact:true}).waitFor();await error.getByText('handler_error',{exact:true}).waitFor();
    assert(!(await page.locator('body').innerText()).includes(secret));
  });
  await check('Journal multiligne expurgé, texte HTML et détail au clavier',async()=>{
    const row=item(logId),summary=row.locator('summary');await summary.focus();await page.keyboard.press('Enter');
    const text=await row.locator('pre').innerText();assert(text.includes('Première ligne\n<script>window.observationInjected=true</script>'));assert(text.includes('Dernière ligne sur stderr'));assert(!text.includes(secret));
    assert.equal(await page.evaluate(()=>window.observationInjected),undefined);assert.equal(await row.locator('script').count(),0);
    await capture('logs-desktop');await page.keyboard.press('Enter');assert.equal(await row.locator('details').getAttribute('open'),null);assert(await summary.evaluate(node=>document.activeElement===node));
  });
  await check('Journal tronqué, mobile 390 px et retour desktop',async()=>{
    await open(longId);await item(longId).getByText('Journal tronqué à la limite de collecte.',{exact:true}).waitFor();
    await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    const log=item(longId).locator('pre');await log.focus();assert(await log.evaluate(node=>document.activeElement===node));const top=await log.evaluate(node=>node.scrollTop);await page.keyboard.press('End');await until(async()=>(await log.evaluate(node=>node.scrollTop))>top,'Journal sans défilement clavier',5);assert(await log.evaluate(node=>node.scrollHeight>node.clientHeight));
    await capture('logs-mobile');await page.setViewportSize({width:1440,height:1000});
    const sixth=await invoke();await refresh();await changePage('Suivante');assert.equal(await rows().count(),1);assert(!(await rows().innerText()).includes(sixth));
    assert(await region().getByRole('heading',{name:'Invocations',exact:true}).evaluate(node=>document.activeElement===node));
    await changePage('Précédente');assert.equal(await rows().count(),5);
  });
  await check('Invocation active puis refus en file : démarrage Oui et Non',async()=>{
    const active=start({action:'delay',ms:12000});
    const row=await until(async()=>{const values=await history();return values.find(value=>value.state==='running'&&value.handler_started===true);},'Appel actif non observé');
    await refresh();const displayed=await open(row.id);await displayed.getByText('En cours',{exact:true}).waitFor();await displayed.getByText('Oui',{exact:true}).waitFor();await displayed.getByText('Journaux disponibles à la fin de l’invocation.',{exact:true}).waitFor();await capture('running');
    const rejected=await invoke({},429);await refresh();const refusal=await open(rejected);await refusal.getByText('Refusée',{exact:true}).waitFor();await refusal.getByText('Non',{exact:true}).waitFor();
    assert.equal((await active).status,200);
  });
  await check('Import réel retardé : démarrage non confirmé puis terminé',async()=>{
    await update({}, {OBSERVATION_IMPORT_DELAY_MS:'12000'});await until(async()=>(await manage(`/api/functions/${functionId}/instances`)).total===0,'Ancienne génération non drainée');const active=start();
    const row=await until(async()=>{const values=await history();return values.find(value=>value.state==='running'&&value.handler_started===null);},'Import en cours non observé');
    await refresh();await open(row.id);await item(row.id).getByText('Non confirmé',{exact:true}).waitFor();await capture('unconfirmed');
    assert.equal((await active).status,200);await update();await until(async()=>(await manage(`/api/functions/${functionId}/instances`)).total===0,'Génération retardée non drainée');
  });
  await check('Conteneur interrompu : mesures indisponibles et allocation conservée',async()=>{
    const active=start({action:'delay',ms:25000});const row=await until(async()=>{const values=await history();return values.find(value=>value.state==='running'&&value.handler_started===true);},'Handler actif non observé');
    const guard=await writer();
    try{await operator('kill-instance',[row.instance_id]);await tab('Instances');await page.getByText('Indisponible',{exact:true}).first().waitFor();
      assert(await page.getByText('0,05 CPU',{exact:true}).isVisible());assert(await page.getByText('128 Mio',{exact:true}).isVisible());await capture('metrics-unavailable');}
    finally{await guard.release();}
    assert.equal((await active).status,503);await until(async()=>(await manage(`/api/functions/${functionId}/instances`)).total===0,'Réservation interrompue non libérée');
  });
  await check('Session absente : refus réel et reprise de la session autorisée',async()=>{
    await tab('Invocations');const cookies=await context.cookies(base);await context.clearCookies();
    try{await refresh();await page.getByRole('alert').getByRole('link',{name:'Se reconnecter avec le SSO',exact:true}).waitFor();assert.equal(await rows().count(),0);await capture('unauthorized');}
    finally{await context.addCookies(cookies);}
    await refresh();assert.equal(await rows().count(),5);assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
  });
  await check('Retour configuration, suppression réelle et refus de consultation',async()=>{
    await tab('Configuration');await page.getByRole('button',{name:'Modifier l’exécution',exact:true}).waitFor();
    await tab('Instances');await manage(`/api/functions/${functionId}`,{method:'DELETE'});deleted=true;
    await refresh();await page.getByRole('alert').getByText('Fonction introuvable.',{exact:true}).waitFor();assert.equal(await rows().count(),0);assert.deepEqual(faults,[]);await capture('deleted');
  });
  completed=true;
} catch(error) {
  if (!checks.some(row=>row.status==='failed')) checks.push({name:'Préparation ou fin de campagne',status:'failed',error:error.name});
  process.exitCode=1;console.error(error.name, error.message);
} finally {
  if(context)await context.setOffline(false).catch(()=>{});
  for(const guard of guards)try{await guard.release();}catch(error){cleanupErrors.push('garde:'+error.name);}
  await Promise.allSettled(pending);
  if(session?.authenticated){try{
    namespaceId ||= await find('/api/namespaces',prefix);if(namespaceId)serviceId ||= await find(`/api/namespaces/${namespaceId}/services`,'observations');if(serviceId&&!deleted)functionId ||= await find(`/api/services/${serviceId}/functions`,functionName);
  }catch(error){cleanupErrors.push('identification:'+error.name);}}
  if(functionId) {
    try{if(!deleted){await until(async()=>(await history()).every(row=>!['receiving','queued','admitted','running'].includes(row.state)),'Invocations non terminées');await manage(`/api/functions/${functionId}`,{method:'DELETE'});}storageArchive=await purgeStorageArchive(functionId,namespaceId);}
    catch(error){cleanupErrors.push('fonction:'+error.name);}
  }
  for(const [kind,id] of [['services',serviceId],['namespaces',namespaceId]])if(id)try{await manage(`/api/${kind}/${id}`,{method:'DELETE'});}catch(error){cleanupErrors.push(kind+':'+error.name);}
  if(browser)await browser.close();if(work)await rm(work,{recursive:true,force:true});
  cleanupCompleted=true;await save();if(!completed||cleanupErrors.length||faults.length)process.exitCode=1;
}
