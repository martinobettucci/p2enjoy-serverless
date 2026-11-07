// @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md
// @verifies docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {chromium} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';
import {purgeStorageArchive} from './storage-archives.mjs';

const base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url),report=new URL('publication-ui.json',output);
const prefix='publication-ui-'+randomUUID().slice(0,8),functionName='publication-'+randomUUID().replaceAll('-','')+'x'.repeat(19);
const secrets=['publication-ui-private-'+randomUUID(),'publication-ui-rotated-'+randomUUID()],checks=[],faults=[],captures={},pending=[],cleanupErrors=[],retained=[],evidence=[];
let secret=secrets[0],browser,context,page,session,storageState,namespaceId,serviceId,functionId,work,token,firstId,secondId,completed=false,cleanup=false,storageArchive;
async function save(){const temp=new URL('publication-ui.pending',output);await writeFile(temp,JSON.stringify({target:base,completed:completed&&cleanup&&!cleanupErrors.length&&!faults.length,skipped:0,checks,faults,captures,cleanup,cleanup_errors:cleanupErrors,namespace_id:namespaceId,service_id:serviceId,function_id:functionId,retained_archives:retained,storage_archive:storageArchive,evidence},null,2)+'\n');await rename(temp,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function manage(url,{method='GET',body,headers={},status=200}={}){
  const response=await context.request.fetch(base+url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers},timeout:60000});
  assert.equal(response.status(),status,`${method} ${url}: ${response.status()}`);const text=await response.text();assert(secrets.every(value=>!text.includes(value)));return JSON.parse(text);
}
async function find(url,name){for(let offset=0;offset<=10000;offset+=100){const data=await manage(`${url}?limit=100&offset=${offset}`),row=data.items.find(item=>item.name===name);if(row)return row.id;if(data.items.length<100)return null;}throw new Error('lookup_limit');}
async function until(action,message){const end=Date.now()+60000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,100));}assert.fail(message);}
async function ready(){await page.waitForFunction(()=>{const button=document.querySelector('.publication-view button.primary');return button&&!button.disabled&&!document.querySelector('.publication-view .loading');});}
const code=()=>page.getByRole('region',{name:'Code de la fonction',exact:true}),follow=()=>page.getByRole('region',{name:'Tentative suivie',exact:true});
const revisions=()=>page.getByRole('region',{name:'Révisions conservées',exact:true});
const revision=id=>page.getByRole('article',{name:`Révision ${id}`,exact:true});
async function refresh(){await code().getByRole('button',{name:/^(Actualiser|Réessayer)$/}).click();await ready();}
async function update(change={},label='current'){
  const fn=await manage(`/api/functions/${functionId}`);
  return manage(`/api/functions/${functionId}`,{method:'PUT',headers:{'If-Match':String(fn.updated_at)},body:{name:fn.name,config:{...fn.config,...change},configuration:{environment:{PUBLIC_LABEL:label},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}}});
}
async function invoke(expected,method='GET'){
  const response=await context.request.fetch(base+`/invoke/${functionId}?mode=counter`,{method,headers:{'X-Serverless-Token':token},timeout:60000});
  assert.equal(response.status(),200);const text=await response.text();assert(secrets.every(value=>!text.includes(value)));const data=JSON.parse(text);
  for(const [key,value]of Object.entries(expected))assert.equal(data[key],value);
  assert.equal(data.secret_sha256,createHash('sha256').update(secret).digest('hex'));return data;
}
async function capture(name){const file=new URL(`publication-ui-${name}.jpg`,output);await page.evaluate(()=>scrollTo(0,0));const bytes=await page.screenshot({path:file.pathname,type:'jpeg',quality:85,fullPage:!name.includes('confirmation')});captures[file.pathname.split('/').at(-1)]=createHash('sha256').update(bytes).digest('hex');}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
async function form(archive,handler=archive.handler){await ready();await code().getByRole('button',{name:'Publier une archive',exact:true}).click();const dialog=page.getByRole('dialog');await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(archive.file);await dialog.getByLabel('Handler',{exact:true}).fill(handler);return dialog;}
async function confirmation(dialog){await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).focus();await page.keyboard.press('Enter');await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).waitFor();}
function tracked(promise){const handled=promise.then(value=>({value}),error=>({error}));pending.push(handled);return handled;}
async function startPublication(archive,{opened=false}={}){
  const dialog=opened?page.getByRole('dialog'):await form(archive);await confirmation(dialog);
  const response=tracked(page.waitForResponse(value=>value.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(value.url()).pathname),{timeout:60000}).then(result=>({status:result.status()})));
  await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).focus();await page.keyboard.press('Enter');await dialog.waitFor({state:'hidden'});
  const id=new URL(page.url()).searchParams.get('deployment');assert.match(id,/^[0-9a-f-]{36}$/);
  return {id,response};
}
async function finished(upload,status=200){const result=await upload.response;if(result.error)throw result.error;assert.equal(result.value.status,status);await ready();return manage(`/api/deployments/${upload.id}`);}
async function publish(archive){const result=await startPublication(archive);await finished(result);await code().getByText(result.id,{exact:true}).waitFor();return result.id;}
async function confirmAction(container,label,matcher){await container.getByRole('button',{name:label,exact:true}).first().click();const response=tracked(page.waitForResponse(matcher).then(result=>result.status()));await container.locator('.confirm').getByRole('button',{name:label,exact:true}).click();const result=await response;if(result.error)throw result.error;assert.equal(result.value,200);await ready();}

await mkdir(output,{recursive:true,mode:0o700});await save();
try{
  storageState=JSON.parse(await readFile(new URL('admin-session.json',output),'utf8'));
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState,viewport:{width:1440,height:1000},locale:'fr-FR'});page=await context.newPage();page.setDefaultTimeout(30000);
  page.on('pageerror',error=>faults.push(error.name));
  session=await(await context.request.get(base+'/api/session')).json();assert.equal(session.authenticated,true,'Session SSO réelle requise');
  work=await mkdtemp(new URL('publication-ui-',output).pathname);
  const a=await publicationArchive(work,'revision-a'),b=await publicationArchive(work,'revision-b'),slow=await publicationArchive(work,'slow','deployment-delay.handler'),broken=await publicationArchive(work,'broken','log-secret-then-throw.handler');
  const invalid={file:work+'/invalid.zip',handler:'publication.handler'};await writeFile(invalid.file,'invalid zip');

  await check('Entrée normale, création UI, facette partageable et états vides',async()=>{
    await page.goto(base);await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(prefix);
    const response=page.waitForResponse(value=>value.url()===base+'/api/namespaces'&&value.request().method()==='POST').then(result=>result.status());const [created]=await Promise.all([response,dialog.getByRole('button',{name:'Créer',exact:true}).click()]);assert.equal(created,201);namespaceId=await until(()=>find('/api/namespaces',prefix),'Namespace créé non retrouvé');
    await page.waitForURL(/\/console\/namespaces\//);await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('publications');
    const serviceResponse=page.waitForResponse(value=>value.url()===base+`/api/namespaces/${namespaceId}/services`&&value.request().method()==='POST').then(result=>result.status());const [serviceCreated]=await Promise.all([serviceResponse,dialog.getByRole('button',{name:'Enregistrer',exact:true}).click()]);assert.equal(serviceCreated,201);serviceId=await until(()=>find(`/api/namespaces/${namespaceId}/services`,'publications'),'Service créé non retrouvé');
    await page.waitForURL(/\/console\/services\//);await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(functionName);await dialog.getByLabel('Handler',{exact:true}).fill('publication.handler');
    const functionResponse=page.waitForResponse(value=>value.url()===base+`/api/services/${serviceId}/functions`&&value.request().method()==='POST').then(result=>result.status());const [functionCreated]=await Promise.all([functionResponse,dialog.getByRole('button',{name:'Créer',exact:true}).click()]);assert.equal(functionCreated,201);functionId=await until(()=>find(`/api/services/${serviceId}/functions`,functionName),'Fonction créée non retrouvée');
    await page.waitForURL(/\/console\/functions\//);await save();
    await update({memory_mib:256,cpu:.2,idle_seconds:0,timeout_seconds:5,storage:{data:{enabled:true,quota_mib:8},cache:{enabled:false,quota_mib:8},concurrency:'exclusive'}},'initial');
    token=(await manage(`/api/services/${serviceId}/tokens`,{method:'POST',status:201,body:{name:'invoke-publication',rights:['read']}})).token;
    const tab=page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Code et révisions',exact:true});await tab.focus();await page.keyboard.press('Enter');await ready();assert.equal(new URL(page.url()).pathname,`/console/functions/${functionId}/code`);
    await page.getByText('Aucune révision publiée.',{exact:true}).waitFor();await page.getByText('Aucune tentative de publication.',{exact:true}).waitFor();await capture('empty');
  });
  await check('Refus de préparation : saisie ZIP et handler conservée après 422 et conflit réel',async()=>{
    const dialog=await form(a,'handlerSansPoint');await confirmation(dialog);
    let response=page.waitForResponse(value=>value.url()===base+`/api/functions/${functionId}/code-deployments`&&value.request().method()==='POST');let [result]=await Promise.all([response,dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click()]);assert.equal(result.status(),422);await dialog.getByRole('alert').waitFor();
    assert.equal(await dialog.getByLabel('Handler',{exact:true}).inputValue(),'handlerSansPoint');assert.equal(await dialog.getByLabel('Archive ZIP',{exact:true}).evaluate(node=>node.files.length),1);
    await ready();await dialog.getByLabel('Handler',{exact:true}).fill(a.handler);await confirmation(dialog);await update({},'concurrent-before-prepare');
    response=page.waitForResponse(value=>value.url()===base+`/api/functions/${functionId}/code-deployments`&&value.request().method()==='POST');[result]=await Promise.all([response,dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click()]);assert.equal(result.status(),409);await dialog.getByRole('alert').waitFor();assert.equal(await dialog.getByLabel('Archive ZIP',{exact:true}).evaluate(node=>node.files.length),1);assert.equal(await dialog.getByLabel('Handler',{exact:true}).inputValue(),a.handler);await capture('preparation-conflict');await ready();
  });
  await check('Publication UI de A, corrélation, focus, SHA256 et invocation réelle',async()=>{
    const upload=await startPublication(a,{opened:true});firstId=upload.id;
    await until(()=>page.evaluate(()=>document.activeElement?.id==='publication-follow-heading'),'Focus absent après fermeture de la modale');
    const result=await finished(upload);assert.equal(result.state,'published');assert.equal(result.revision_id,firstId);await code().getByText(firstId,{exact:true}).waitFor();
    const history=await manage(`/api/functions/${functionId}/revisions`);assert.equal(history.items[0].archive_sha256,a.sha256);assert.equal(history.items[0].active,true);
    await invoke({revision:'revision-a',functionVersion:firstId,label:'concurrent-before-prepare',count:1},'POST');await revision(firstId).locator('summary').click();await fits();await capture('published-desktop');
  });
  await check('Archive invalide, import en erreur et journal expurgé dans la console',async()=>{
    const badZip=await startPublication(invalid);await finished(badZip,422);await follow().getByText('Échec',{exact:true}).waitFor();assert.equal((await manage(`/api/functions/${functionId}`)).active_revision_id,firstId);
    const badImport=await startPublication(broken);await finished(badImport,422);await follow().locator('summary').click();const text=await follow().locator('pre').innerText();assert(text.includes('qualification-import-secret=[redacted]'));assert(secrets.every(value=>!text.includes(value)));await follow().getByText('import_failed',{exact:true}).waitFor();await capture('validation-failed');
  });
  await check('Publication B puis activation UI de A avec configuration et données courantes',async()=>{
    secret=secrets[1];await update({memory_mib:384},'current-config');await refresh();secondId=await publish(b);await invoke({revision:'revision-b',functionVersion:secondId,label:'current-config',count:1,memory:'384'});
    const before=await manage(`/api/functions/${functionId}`);await confirmAction(revision(firstId),'Activer cette révision',value=>value.url()===base+`/api/functions/${functionId}/rollback`&&value.request().method()==='POST');
    assert.equal((await manage(`/api/functions/${functionId}`)).active_revision_id,firstId);assert.deepEqual((await manage(`/api/functions/${functionId}`)).config,before.config);await code().getByText(firstId,{exact:true}).waitFor();await invoke({revision:'revision-a',functionVersion:firstId,label:'current-config',count:1,memory:'384'});await capture('activated');
  });
  await check('Suppression UI inactive, confirmation annulée et protection de la révision active',async()=>{
    const row=revision(secondId);await row.getByRole('button',{name:'Supprimer cette révision',exact:true}).click();await row.locator('.confirm').getByRole('button',{name:'Annuler',exact:true}).click();assert((await manage(`/api/functions/${functionId}/revisions`)).items.some(item=>item.id===secondId));
    await until(async()=>!(await manage(`/api/functions/${functionId}/instances?limit=100`)).items.some(item=>item.revision_id===secondId),'Instance de B encore présente');
    await confirmAction(row,'Supprimer cette révision',value=>value.url()===base+`/api/functions/${functionId}/revisions/${secondId}`&&value.request().method()==='DELETE');
    assert(!(await manage(`/api/functions/${functionId}/revisions`)).items.some(item=>item.id===secondId));assert.equal(await revision(firstId).getByRole('button',{name:'Supprimer cette révision',exact:true}).count(),0);await invoke({revision:'revision-a',count:1});
  });
  await check('Conflit pendant validation : ancienne révision et modification concurrente conservées',async()=>{
    const upload=await startPublication(slow);await until(async()=>(await manage(`/api/deployments/${upload.id}`)).state==='validating','Validation réelle non observée');await capture('validating');await update({},'during-validation');await finished(upload,409);await follow().getByText('Échec',{exact:true}).waitFor();assert.equal((await manage(`/api/functions/${functionId}`)).active_revision_id,firstId);assert.equal((await manage(`/api/functions/${functionId}`)).environment.PUBLIC_LABEL,'during-validation');
  });
  await check('Rechargement pendant son upload : même candidat et pointeur actif relu sans rejeu',async()=>{
    const before=(await manage(`/api/functions/${functionId}/deployments?limit=100`)).total,upload=await startPublication(slow);
    await until(async()=>(await manage(`/api/deployments/${upload.id}`)).state==='validating','Validation réelle non observée');await page.reload();
    const terminal=await until(async()=>{const value=await manage(`/api/deployments/${upload.id}`);return ['published','failed'].includes(value.state)&&value;},'Candidat resté actif');
    await page.waitForFunction(()=>!document.querySelector('.publication-view .loading'));assert.equal(new URL(page.url()).searchParams.get('deployment'),upload.id);
    if(terminal.state==='published'){await code().getByText(upload.id,{exact:true}).waitFor();await revision(upload.id).getByText('Active',{exact:true}).waitFor();assert.equal((await manage(`/api/functions/${functionId}`)).active_revision_id,upload.id);}
    else{await follow().getByText('Échec',{exact:true}).waitFor();assert.equal((await manage(`/api/functions/${functionId}`)).active_revision_id,firstId);}
    assert.equal((await manage(`/api/functions/${functionId}/deployments?limit=100`)).total,before+1);evidence.push({reloaded_candidate:upload.id,state:terminal.state});await capture('reloaded');
  });
  await check('Candidat préparé retrouvé dans la liste et abandonné par la console',async()=>{
    await ready();const fn=await manage(`/api/functions/${functionId}`),id=randomUUID();await manage(`/api/functions/${functionId}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(fn.updated_at)},body:{handler:a.handler,deployment_id:id}});await refresh();
    for(let repeat=0;repeat<2;repeat++){await page.getByRole('article',{name:`Tentative ${id}`,exact:true}).getByRole('button',{name:'Consulter cette tentative',exact:true}).click();await ready();}await follow().getByText('En attente d’archive',{exact:true}).waitFor();
    await confirmAction(follow(),'Abandonner cette tentative',value=>value.url()===base+`/api/deployments/${id}`&&value.request().method()==='DELETE');await follow().getByText('Abandonnée',{exact:true}).waitFor();assert.equal((await manage(`/api/deployments/${id}`)).error_code,'candidate_abandoned');
  });
  await check('Pagination réelle des révisions, recalage après suppression et pagination des tentatives',async()=>{
    for(let index=0;(await manage(`/api/functions/${functionId}/revisions?limit=100`)).items.length<6;index++)await publish(await publicationArchive(work,'page-'+index));
    const all=(await manage(`/api/functions/${functionId}/revisions?limit=100`)).items,pages=page.getByRole('navigation',{name:'Pagination des révisions',exact:true});
    assert.deepEqual(await revisions().getByRole('article').locator('h3').allTextContents(),all.slice(0,5).map(row=>row.id));await pages.getByRole('button',{name:'Suivante',exact:true}).click();const last=all[5];await revision(last.id).waitFor();assert.equal(await revisions().getByRole('article').count(),1);
    await confirmAction(revision(last.id),'Supprimer cette révision',value=>value.url()===base+`/api/functions/${functionId}/revisions/${last.id}`&&value.request().method()==='DELETE');await pages.getByText('Page 1 sur 1',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>document.activeElement?.id),'revisions-heading');
    const candidates=page.getByRole('navigation',{name:'Pagination des tentatives',exact:true});await candidates.getByRole('button',{name:'Suivante',exact:true}).click();await ready();const second=await manage(`/api/functions/${functionId}/deployments?limit=5&offset=5`);await candidates.getByText(`Page 2 sur ${Math.ceil(second.total/5)}`,{exact:true}).waitFor();assert.deepEqual(await page.getByRole('article',{name:/^Tentative /}).locator('h3').allTextContents(),second.items.map(row=>row.id));await capture('pagination');await candidates.getByRole('button',{name:'Précédente',exact:true}).click();await ready();const first=await manage(`/api/functions/${functionId}/deployments?limit=5`);assert.deepEqual(await page.getByRole('article',{name:/^Tentative /}).locator('h3').allTextContents(),first.items.map(row=>row.id));assert.equal(new Set([...first.items,...second.items].map(row=>row.id)).size,10);
  });
  await check('Panne réseau réelle, reprise de lecture et refus de session',async()=>{
    const candidates=page.getByRole('navigation',{name:'Pagination des tentatives',exact:true});
    await context.setOffline(true);await candidates.getByRole('button',{name:'Suivante',exact:true}).click();await page.getByRole('alert').filter({hasText:'Impossible de joindre le serveur'}).waitFor();
    await candidates.getByText(/^Page 1 sur/).waitFor();await context.setOffline(false);await candidates.getByRole('button',{name:'Suivante',exact:true}).click();await ready();
    const second=await manage(`/api/functions/${functionId}/deployments?limit=5&offset=5`);assert.deepEqual(await page.getByRole('article',{name:/^Tentative /}).locator('h3').allTextContents(),second.items.map(row=>row.id));
    await context.setOffline(true);await code().getByRole('button',{name:'Actualiser',exact:true}).click();await page.getByRole('alert').filter({hasText:'Impossible de joindre le serveur'}).waitFor();assert(await code().getByRole('button',{name:'Publier une archive',exact:true}).isDisabled());await capture('network-error');await context.setOffline(false);await refresh();
    await context.clearCookies();await code().getByRole('button',{name:'Actualiser',exact:true}).click();await page.getByRole('link',{name:'Se reconnecter avec le SSO',exact:true}).waitFor();await capture('unauthorized');await context.addCookies(storageState.cookies);await refresh();
  });
  await check('Réponse de préparation interrompue en quittant la page : candidat retrouvé sans upload',async()=>{
    const before=(await manage(`/api/functions/${functionId}/deployments?limit=100`)).total;
    const dialog=await form(a);await confirmation(dialog);
    const cdp=await context.newCDPSession(page),previousId=new URL(page.url()).searchParams.get('deployment');let uploads=0;
    const countUpload=request=>{if(request.method()==='PUT'&&request.url().endsWith('/artifact'))uploads++;};page.on('request',countUpload);
    try{
      // Real Chromium transport: POST commits before its delayed response headers.
      // Leaving for a local blank document destroys the page without waiting for
      // a second remote navigation, then the recorded address restores the view.
      await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:10000,downloadThroughput:-1,uploadThroughput:-1});
      await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();
      const id=await until(async()=>{const value=new URL(page.url()).searchParams.get('deployment');return value&&value!==previousId&&value;},'Identifiant de préparation absent');
      await until(async()=>{const list=await manage(`/api/functions/${functionId}/deployments?limit=100`);return list.items.some(row=>row.id===id&&row.state==='prepared');},'Préparation réelle non observée');
      evidence.push({preparation_before_reload:id,uploads,dialog_open:await dialog.isVisible()});await save();
      assert.equal(uploads,0,'La réponse de préparation est déjà consommée');assert(await dialog.isVisible());
      const address=page.url();await page.goto('about:blank');
      await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});
      await page.goto(address);
      const observed=await manage(`/api/deployments/${id}`);evidence.push({preparation_after_reload:id,state:observed.state,uploads});await save();assert.equal(observed.state,'prepared');assert.equal(uploads,0);
      await ready();await follow().getByText('En attente d’archive',{exact:true}).waitFor();assert.equal(new URL(page.url()).searchParams.get('deployment'),id);
      const list=await manage(`/api/functions/${functionId}/deployments?limit=100`);assert.equal(list.total,before+1);assert.equal(list.items.find(row=>row.id===id).state,'prepared');
      evidence.push({lost_preparation_response:id,archive_upload_requests:uploads});await capture('preparation-response-lost');
      await confirmAction(follow(),'Abandonner cette tentative',value=>value.url()===base+`/api/deployments/${id}`&&value.request().method()==='DELETE');
    }finally{
      page.off('request',countUpload);await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await context.setOffline(false);await cdp.detach();
    }
  });
  await check('Identifiant absent : erreur explicite et aucune nouvelle préparation automatique',async()=>{
    const before=(await manage(`/api/functions/${functionId}/deployments?limit=100`)).total,id=randomUUID();
    await page.goto(`${base}/console/functions/${functionId}/code?deployment=${id}`);await follow().getByRole('alert').filter({hasText:'Déploiement introuvable.'}).waitFor();
    assert(await code().getByRole('button',{name:'Publier une archive',exact:true}).isDisabled());assert.equal((await manage(`/api/functions/${functionId}/deployments?limit=100`)).total,before);
    await follow().getByRole('button',{name:'Fermer le suivi',exact:true}).click();await ready();assert.equal(new URL(page.url()).searchParams.has('deployment'),false);
  });
  await check('Mobile 390 px, nom long, détails et confirmation au clavier',async()=>{
    await page.setViewportSize({width:390,height:844});await fits();await capture('mobile');
    const row=revisions().getByRole('article').first();await row.locator('summary').focus();await page.keyboard.press('Enter');await row.getByText('SHA256 de l’archive',{exact:true}).waitFor();await fits();await capture('metadata-mobile');
    const dialog=await form(a);await confirmation(dialog);await capture('confirmation-mobile');await dialog.getByRole('button',{name:'Revenir à la saisie',exact:true}).focus();await page.keyboard.press('Enter');await dialog.getByRole('button',{name:'Annuler',exact:true}).focus();await page.keyboard.press('Enter');await until(()=>page.evaluate(()=>document.activeElement?.textContent==='Continuer la saisie'),'Focus d’abandon absent');await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement?.textContent),'Abandonner');await page.keyboard.press('Enter');await dialog.waitFor({state:'hidden'});await until(()=>page.evaluate(()=>document.activeElement===document.querySelector('.publication-view button.primary')),'Focus non rendu au bouton de publication');await fits();
    const rendered=await page.locator('body').innerText();assert(secrets.every(value=>!rendered.includes(value)));assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);assert.deepEqual(faults,[]);
  });
  completed=true;
}catch(error){if(!checks.some(row=>row.status==='failed'))checks.push({name:'Préparation ou fin',status:'failed',error:error.name});console.error(error.name,error.message);process.exitCode=1;}
finally{
  if(context){await context.setOffline(false).catch(error=>cleanupErrors.push('connexion:'+error.name));if(storageState)await context.addCookies(storageState.cookies).catch(error=>cleanupErrors.push('session:'+error.name));}await Promise.all(pending);
  const failure=(step,error)=>cleanupErrors.push({step,error:error.name,message:error.message});
  if(session?.authenticated)try{namespaceId ||= await find('/api/namespaces',prefix);if(namespaceId)serviceId ||= await find(`/api/namespaces/${namespaceId}/services`,'publications');if(serviceId)functionId ||= await find(`/api/services/${serviceId}/functions`,functionName);}catch(error){failure('identification',error);}
  if(functionId){
    try{await until(async()=>!(await manage(`/api/functions/${functionId}/deployments?limit=100`)).items.some(row=>['receiving','validating'].includes(row.state)),'Publication non terminée');const history=await manage(`/api/functions/${functionId}/revisions?limit=100`);retained.push(...history.items.map(row=>({function_id:functionId,id:row.id,archive_sha256:row.archive_sha256})));}catch(error){failure('historique',error);}
    try{await manage(`/api/functions/${functionId}`,{method:'DELETE'});}catch(error){failure('suppression',error);}
    try{storageArchive=await purgeStorageArchive(functionId,namespaceId);}catch(error){failure('purge',error);}
  }
  for(const [kind,id]of [['services',serviceId],['namespaces',namespaceId]])if(id)try{await manage(`/api/${kind}/${id}`,{method:'DELETE'});}catch(error){failure(kind,error);}
  try{await browser?.close();}catch(error){failure('navigateur',error);}if(work)try{await rm(work,{recursive:true,force:true});}catch(error){failure('fichiers',error);}
  cleanup=true;await save();if(!completed||cleanupErrors.length||faults.length)process.exitCode=1;
}
