// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {chromium} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url),report=new URL('storage-console-ui.json',output);
const prefix='storage-ui-'+randomUUID().slice(0,8),functionName=(prefix+'-persistent-cache-'+'x'.repeat(63)).slice(0,63);
const checks=[],faults=[],captures={},cleanupErrors=[],evidence=[],paginationFunctions=[];
let browser,context,page,session,storageState,namespaceId,serviceId,functionId,token,work,completed=false,cleanup=false;
async function save(){const ids=[functionId,...paginationFunctions.map(row=>row.id)].filter(Boolean);const temporary=new URL('storage-console-ui.pending',output);await writeFile(temporary,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length&&!faults.length,skipped:0,checks,faults,captures,cleanup,cleanup_errors:cleanupErrors,namespace_id:namespaceId,service_id:serviceId,function_id:functionId,function_ids:ids,campaigns:namespaceId?{[namespaceId]:ids}:{},evidence},null,2)+'\n');await rename(temporary,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function manage(url,{method='GET',body,headers={},status=200}={}){const response=await context.request.fetch(base+url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});assert([status].flat().includes(response.status()),`${method} ${url}: ${response.status()}`);return response.json();}
async function until(action,message,milliseconds=60000){const end=Date.now()+milliseconds;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,150));}assert.fail(message);}
async function capture(name){const file=new URL('storage-ui-'+name+'.jpg',output);await page.evaluate(()=>scrollTo(0,0));const bytes=await page.screenshot({path:file.pathname,type:'jpeg',quality:85,fullPage:true});captures[file.pathname.split('/').at(-1)]=createHash('sha256').update(bytes).digest('hex');}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
const panel=name=>page.locator('section.panel').filter({has:page.getByRole('heading',{name,exact:true})});
const storage=()=>panel('Volumes de la fonction'),follow=()=>panel('Suivi de l’opération'),archive=()=>panel('Archives conservées');
async function ready(){await page.waitForFunction(()=>{const b=[...document.querySelectorAll('main button')].find(b=>/^(Actualiser|Réessayer)$/.test(b.textContent));return b&&b.getAttribute('aria-disabled')!=='true';});}
async function refresh(){await page.getByRole('button',{name:/^(Actualiser|Réessayer)$/}).click();await ready();}
async function navigation(name){if(page.viewportSize().width<1024)await page.getByRole('button',{name:'Menu',exact:true}).click();await page.getByRole('complementary',{name:'Navigation principale'}).getByRole('link',{name,exact:true}).click();}
async function invoke(body){const response=await context.request.fetch(base+`/invoke/${functionId}`,{method:body?'POST':'GET',data:body,headers:{'X-Serverless-Token':token}});assert.equal(response.status(),200);return response.json();}
async function finishCommand(id){await until(async()=>(await manage(`/api/storage-operations/${id}`)).state==='completed','Commande non terminée');await refresh();await follow().getByText('Terminée',{exact:true}).waitFor();}
async function confirm(container,label){await container.getByRole('button',{name:label,exact:true}).first().click();await container.locator('.confirm').getByRole('button',{name:label,exact:true}).click();}
async function deleteViaUI(label){await page.getByRole('button',{name:label,exact:true}).click();await page.locator('.confirm').getByRole('button',{name:label,exact:true}).click();}
async function listAll(url){const items=[];for(let offset=0;offset<=10000;offset+=100){const page=await manage(url+`?limit=100&offset=${offset}`);items.push(...page.items);if(page.items.length<100)return items;}assert.fail('Inventaire de nettoyage trop grand');}
async function discoverCampaign(){
  namespaceId||=(await listAll('/api/namespaces')).find(row=>row.name===prefix)?.id;
  if(namespaceId)serviceId||=(await listAll(`/api/namespaces/${namespaceId}/services`)).find(row=>row.name==='storage-console')?.id;
  if(!serviceId)return;
  const response=await context.request.get(base+`/api/services/${serviceId}`);if(response.status()===404)return;
  assert.equal(response.status(),200);assert.equal((await response.json()).namespace_id,namespaceId);
  const allowed=new Set(Array.from({length:11},(_,index)=>prefix+'-pagination-'+String(index+1).padStart(2,'0')));
  for(const row of await listAll(`/api/services/${serviceId}/functions`)){
    assert.equal(row.service_id,serviceId);
    if(row.name===functionName){assert(!functionId||row.id===functionId);functionId=row.id;}
    else{assert(allowed.has(row.name),'Fonction étrangère dans le service de campagne');if(!paginationFunctions.some(value=>value.id===row.id))paginationFunctions.push({id:row.id,name:row.name,discovered_during_cleanup:true});}
  }
  await save();
}

await mkdir(output,{recursive:true,mode:0o700});await save();
try {
  storageState=JSON.parse(await readFile(new URL('admin-session.json',output),'utf8'));
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState,viewport:{width:1440,height:1000},locale:'fr-FR'});
  page=await context.newPage();page.on('pageerror',error=>faults.push(error.name));session=await(await context.request.get(base+'/api/session')).json();assert(session.authenticated);
  work=await mkdtemp(new URL('storage-ui-',output).pathname);const zip=await publicationArchive(work,'storage','storage-console.handler');
  await check('Accueil, créations UI et consultation initiale sans volume',async()=>{
    await page.goto(base);await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(prefix);await dialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.waitForURL(/\/console\/namespaces\//);namespaceId=new URL(page.url()).pathname.split('/').at(-1);
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('storage-console');await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.waitForURL(/\/console\/services\//);serviceId=new URL(page.url()).pathname.split('/')[3];
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(functionName);await dialog.getByLabel('Handler',{exact:true}).fill(zip.handler);await dialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.waitForURL(/\/console\/functions\//);functionId=new URL(page.url()).pathname.split('/')[3];await save();
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Stockage',exact:true}).click();await ready();
    assert.equal(new URL(page.url()).pathname,`/console/functions/${functionId}/storage`);await page.getByText('Aucun volume alloué.',{exact:true}).waitFor();await page.getByText('Aucune commande de stockage enregistrée.',{exact:true}).waitFor();await capture('empty');
  });
  await check('Onze archives de pagination créées et supprimées depuis les parcours UI',async()=>{
    await page.getByRole('link',{name:'Fonctions du service',exact:true}).click();
    for(let index=0;index<11;index++){
      const name=prefix+'-pagination-'+String(index+1).padStart(2,'0');
      await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();const dialog=page.getByRole('dialog');
      await dialog.getByLabel('Nom',{exact:true}).fill(name);await dialog.getByLabel('Handler',{exact:true}).fill(zip.handler);
      await dialog.getByRole('button',{name:'Créer',exact:true}).click();await page.waitForURL(/\/console\/functions\//);
      const id=new URL(page.url()).pathname.split('/')[3];assert(id!==functionId&&!paginationFunctions.some(row=>row.id===id));
      paginationFunctions.push({id,name});await save();
      await deleteViaUI('Supprimer la fonction');await page.waitForURL(/\/console\/services\//);
      const archived=await manage(`/api/archives/${id}`);assert.equal(archived.namespace_id,namespaceId);assert(!archived.purged_at);
    }
    evidence.push({pagination_fixture_ids:paginationFunctions.map(row=>row.id),created_and_archived_via_ui:true});
    await page.getByRole('link',{name:functionName,exact:true}).click();
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Stockage',exact:true}).click();await ready();
  });
  await check('Configuration des volumes, publication et jeton depuis la console',async()=>{
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Configuration',exact:true}).click();await page.getByRole('button',{name:'Modifier le stockage',exact:true}).click();let dialog=page.getByRole('dialog');
    for(const name of ['Données permanentes','Cache reconstructible']){const fieldset=dialog.getByRole('group',{name,exact:true});await fieldset.getByLabel('Activer',{exact:true}).check();await fieldset.getByLabel('Allocation (Mio)',{exact:true}).fill('8');}
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await dialog.waitFor({state:'hidden'});
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Code et révisions',exact:true}).click();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(zip.file);await dialog.getByLabel('Handler',{exact:true}).fill(zip.handler);await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();await dialog.waitFor({state:'hidden'});await page.getByText('Publiée',{exact:true}).first().waitFor();
    await page.getByRole('link',{name:'Fonctions du service',exact:true}).click();await page.getByRole('navigation',{name:'Service',exact:true}).getByRole('link',{name:'Jetons',exact:true}).click();
    await page.getByRole('button',{name:'Créer un jeton',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom du jeton',{exact:true}).fill('storage-invocation');await dialog.getByRole('button',{name:'Créer le jeton',exact:true}).click();await dialog.getByRole('button',{name:'Confirmer la création',exact:true}).click();await dialog.waitFor({state:'hidden'});
    token=await page.getByLabel('Valeur de storage-invocation',{exact:true}).inputValue();assert(token.startsWith('p2s_'));await page.getByRole('button',{name:'Fermer la valeur',exact:true}).click();
    await page.getByRole('navigation',{name:'Service',exact:true}).getByRole('link',{name:'Fonctions',exact:true}).click();await page.getByRole('link',{name:functionName,exact:true}).click();await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Stockage',exact:true}).click();await ready();
    await invoke({data:'ui-permanent',cache:'ui-cache'});await refresh();await page.getByRole('heading',{name:'Données permanentes',exact:true}).waitFor();await fits();await capture('volumes-desktop');
  });
  let firstCommand;
  await check('Confirmation annulée, vidage réel, données conservées et focus',async()=>{
    const button=storage().getByRole('button',{name:'Vider le cache',exact:true});await button.click();await page.keyboard.press('Escape');assert(await button.evaluate(node=>document.activeElement===node));assert.equal((await invoke()).cache,'ui-cache');
    await confirm(storage(),'Vider le cache');await storage().locator('.confirm').waitFor({state:'hidden'});await ready();firstCommand=new URL(page.url()).searchParams.get('operation');assert(firstCommand);
    assert(await page.evaluate(()=>['Volumes de la fonction','Vider le cache'].includes(document.activeElement?.textContent)),'Focus perdu après confirmation');await capture('cache-pending');
    await finishCommand(firstCommand);const current=await invoke();assert.equal(current.data,'ui-permanent');assert.equal(current.cache,null);await capture('cache-completed');
    await follow().getByRole('button',{name:'Ne plus suivre cet identifiant',exact:true}).click();await ready();assert(await storage().getByRole('heading',{name:'Volumes de la fonction',exact:true}).evaluate(node=>document.activeElement===node));
  });
  await check('Réponse réellement perdue, UUID cohérent et reprise sans second vidage',async()=>{
    await invoke({cache:'cache-before-second'});await storage().getByRole('button',{name:'Vider le cache',exact:true}).click();
    const cdp=await context.newCDPSession(page);let sent=0,received=0;
    const path=base+`/api/functions/${functionId}/cache-clear`,onRequest=r=>{if(r.method()==='POST'&&r.url()===path)sent++;},onResponse=r=>{if(r.request().method()==='POST'&&r.url()===path)received++;};page.on('request',onRequest);page.on('response',onResponse);
    try {
      await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:10000,downloadThroughput:-1,uploadThroughput:-1});
      await storage().locator('.confirm').getByRole('button',{name:'Vider le cache',exact:true}).click();const id=new URL(page.url()).searchParams.get('operation');assert(id&&id!==firstCommand);
      assert.equal(await follow().getByText(firstCommand,{exact:true}).count(),0);await follow().getByText('Demande en cours…',{exact:true}).waitFor();
      await until(async()=>{const result=await context.request.get(base+`/api/storage-operations/${id}`);return result.status()===200&&(await result.json()).state==='completed';},'Effacement effectif non observé');
      assert.equal(sent,1);assert.equal(received,0);await invoke({cache:'rebuilt-after-lost-response'});await capture('response-pending');const address=page.url();
      await page.goto('about:blank');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await page.goto(address);await ready();await follow().getByText('Terminée',{exact:true}).waitFor();
      assert.equal(sent,1);assert.equal((await invoke()).cache,'rebuilt-after-lost-response');assert.equal((await manage(`/api/storage-operations/${id}`)).state,'completed');evidence.push({lost_response_operation:id,posts:sent,responses_before_exit:0});await capture('response-recovered');
    } finally {page.off('request',onRequest);page.off('response',onResponse);await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.detach();}
  });
  await check('Conflit réel, suivi inconnu et reprise de lecture explicite',async()=>{
    const row=await manage(`/api/functions/${functionId}`);await manage(`/api/functions/${functionId}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:row.config,configuration:{environment:{MANAGEMENT_LABEL:'concurrent-update'}}}});
    await confirm(storage(),'Vider le cache');await storage().locator('.confirm').getByRole('alert').waitFor();await ready();assert(await storage().locator('.confirm').getByRole('button',{name:'Vider le cache',exact:true}).isDisabled());await capture('conflict');
    await storage().locator('.confirm').getByRole('button',{name:'Annuler',exact:true}).click();await follow().getByRole('button',{name:'Ne plus suivre cet identifiant',exact:true}).click();await ready();assert(await storage().getByRole('button',{name:'Vider le cache',exact:true}).isEnabled());assert.equal((await invoke()).cache,'rebuilt-after-lost-response');
  });
  await check('Session retirée et reprise avec la vraie session',async()=>{
    await context.clearCookies();await refresh();await page.getByRole('link',{name:'Se reconnecter avec le SSO',exact:true}).waitFor();assert(await storage().getByRole('button',{name:'Vider le cache',exact:true}).isDisabled());await capture('session-error');
    await context.addCookies(storageState.cookies);await refresh();assert(await storage().getByRole('button',{name:'Vider le cache',exact:true}).isEnabled());
  });
  await check('Suppression UI des parents et accès autonome aux archives',async()=>{
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Configuration',exact:true}).click();await deleteViaUI('Supprimer la fonction');await page.waitForURL(/\/console\/services\//);
    await page.getByRole('navigation',{name:'Service',exact:true}).getByRole('link',{name:'Configuration',exact:true}).click();await deleteViaUI('Supprimer le service');await page.waitForURL(/\/console\/namespaces\//);await deleteViaUI('Supprimer le namespace');await page.waitForURL(base+'/');
    await navigation('Archives de fonctions');await ready();await page.getByRole('link',{name:functionName,exact:true}).click();await ready();
    assert.equal(new URL(page.url()).pathname,`/console/archives/${functionId}`);await archive().getByText(namespaceId,{exact:true}).waitFor();await archive().getByText(serviceId,{exact:true}).waitFor();await capture('archive-desktop');
  });
  await check('Purge : nom exact, annulation, mobile, terminaison et focus',async()=>{
    await page.setViewportSize({width:390,height:844});await archive().getByRole('button',{name:'Purger les archives',exact:true}).click();let confirmation=archive().locator('.confirm'),field=confirmation.getByRole('textbox');
    assert(await field.evaluate(node=>document.activeElement===node));assert(await field.getAttribute('aria-describedby'));await field.fill('wrong');assert(await confirmation.getByRole('button',{name:'Purger les archives',exact:true}).isDisabled());await fits();await capture('purge-confirmation-mobile');await page.keyboard.press('Escape');assert(await archive().getByRole('button',{name:'Purger les archives',exact:true}).evaluate(node=>document.activeElement===node));
    await archive().getByRole('button',{name:'Purger les archives',exact:true}).click();confirmation=archive().locator('.confirm');await confirmation.getByRole('textbox').fill(functionName);await confirmation.getByRole('button',{name:'Purger les archives',exact:true}).focus();await page.keyboard.press('Enter');await confirmation.waitFor({state:'hidden'});await ready();
    assert(await archive().getByRole('heading',{name:'Archives conservées',exact:true}).evaluate(node=>document.activeElement===node));const id=new URL(page.url()).searchParams.get('operation');await finishCommand(id);await fits();await capture('purged-mobile');assert(await archive().getByRole('button',{name:'Purger les archives',exact:true}).isDisabled());
    const result=await manage(`/api/archives/${functionId}`);assert(result.purged_at&&result.artifact_bytes===0);assert.deepEqual(result.storage.volumes,{});await page.reload();await ready();await follow().getByText('Terminée',{exact:true}).waitFor();
  });
  await check('Filtres, pagination après vraie panne réseau et identifiants recoupés',async()=>{
    await navigation('Archives de fonctions');await ready();await fits();await capture('catalogue-mobile');await page.setViewportSize({width:1440,height:1000});
    const owned=new Set(paginationFunctions.map(row=>row.id));assert.equal(owned.size,11);
    const first=await manage('/api/archives?limit=5&offset=0');assert(first.total>=owned.size);assert.equal(first.items.length,5);assert(first.items.every(row=>owned.has(row.id)),'Première page étrangère aux fixtures');await until(async()=>JSON.stringify(await page.locator('.observation-list article .mono').allTextContents())===JSON.stringify(first.items.map(row=>row.id)),'Première page rendue non recoupée');
    await context.setOffline(true);await page.getByRole('button',{name:'Suivante',exact:true}).click();await page.getByRole('alert').waitFor();assert(await page.getByRole('button',{name:'Suivante',exact:true}).isDisabled());await capture('pagination-error');
    await context.setOffline(false);await refresh();const second=await manage('/api/archives?limit=5&offset=5');assert.equal(second.items.length,5);assert(second.items.every(row=>owned.has(row.id)),'Deuxième page étrangère aux fixtures');assert.equal(new Set([...first.items,...second.items].map(row=>row.id)).size,10);evidence.push({pagination_first_ids:first.items.map(row=>row.id),pagination_second_ids:second.items.map(row=>row.id),owned_fixtures_verified:true});await until(async()=>JSON.stringify(await page.locator('.observation-list article .mono').allTextContents())===JSON.stringify(second.items.map(row=>row.id)),'Deuxième page rendue non recoupée');assert((await page.getByRole('navigation',{name:'Pagination des archives'}).innerText()).includes('Page 2'));await capture('catalogue-desktop');
    await page.getByLabel('Afficher les archives',{exact:true}).selectOption('purged');await ready();await page.getByRole('link',{name:functionName,exact:true}).waitFor();await page.getByRole('link',{name:functionName,exact:true}).click();await ready();assert.equal((await manage(`/api/archives/${functionId}`)).purged_at>0,true);
    assert.deepEqual(faults,[]);assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
  });
  completed=true;
} finally {
  if(context){await context.setOffline(false);await context.addCookies(storageState.cookies);}
  // Stop the browser actor before discovering a creation whose response was lost.
  if(page)try{await page.close();}catch(error){cleanupErrors.push({step:'fermeture-page',error:error.name});}
  if(context&&session?.authenticated)try{await discoverCampaign();}catch(error){cleanupErrors.push({step:'inventaire',error:error.name});}
  for(const target of [functionId,...paginationFunctions.map(row=>row.id)].filter(Boolean))try{
    const response=await context.request.get(base+`/api/functions/${target}`);if(response.status()===200)await manage(`/api/functions/${target}`,{method:'DELETE'});else assert.equal(response.status(),404);
    await until(async()=>!(await manage(`/api/archives/${target}`)).storage_operation,'Archivage de nettoyage non confirmé');const row=await manage(`/api/archives/${target}`);
    if(!row.purged_at){const id=randomUUID();await manage(`/api/archives/${target}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:id,confirm_name:row.name}});await until(async()=>(await manage(`/api/storage-operations/${id}`)).state==='completed','Purge de nettoyage non terminée');}
    const purged=await manage(`/api/archives/${target}`);assert(purged.purged_at&&purged.artifact_bytes===0&&!purged.storage_operation);
  }catch(error){cleanupErrors.push({function_id:target,error:error.name});}
  for(const [kind,id]of [['services',serviceId],['namespaces',namespaceId]])if(id)try{const response=await context.request.get(base+`/api/${kind}/${id}`);if(response.status()===200)await manage(`/api/${kind}/${id}`,{method:'DELETE'});else assert.equal(response.status(),404);}catch(error){cleanupErrors.push({object_id:id,error:error.name});}
  await browser?.close();if(work)await rm(work,{recursive:true,force:true});cleanup=!cleanupErrors.length;await save();assert.deepEqual(cleanupErrors,[]);assert.deepEqual(faults,[]);
}
