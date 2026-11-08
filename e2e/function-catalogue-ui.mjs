// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// Real home, management, catalogue and detail pages; actual HTTPS/Docker fixtures.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium} from 'playwright';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url);
const prefix='function-catalogue-ui-'+randomUUID().slice(0,8),namespaceName=(prefix+'-primary'+'x'.repeat(63)).slice(0,62);
const serviceName=('catalogue-service-'+'s'.repeat(63)).slice(0,63),functionName=('catalogue-function-'+'f'.repeat(63)).slice(0,63);
const namespaces=[],services=[],functions=[],archives=[],checks=[],observations=[],captures={},faults=[],cleanupErrors=[];
let browser,context,page,session,primary,secondary,service,work,completed=false;
const run=promisify(execFile);
await mkdir(out,{recursive:true,mode:0o700});
await writeFile(new URL('function-catalogue-ui.json',out),JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function until(action,label){const end=Date.now()+90000;while(Date.now()<end){if(await action())return;await new Promise(resolve=>setTimeout(resolve,100));}assert.fail(label);}
async function api(path,{method='GET',body,status=200,headers={}}={}){
  const response=await context.request.fetch(base+path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),method+' '+path+': '+response.status());return response.json();
}
async function capture(name){const file='function-catalogue-ui-'+name+'.jpg',fullPage=!['desktop','tablet','mobile','mobile-table-left','mobile-table-middle','mobile-scrolled','mobile-picker','clamped-page'].includes(name);const bytes=await page.screenshot({path:new URL(file,out).pathname,type:'jpeg',quality:85,fullPage});captures[file]={sha256:createHash('sha256').update(bytes).digest('hex'),viewport:page.viewportSize(),full_page:fullPage};}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Page trop large');}
function search(){return page.getByRole('searchbox',{name:'Rechercher une fonction',exact:true});}
function pagination(){return page.getByRole('navigation',{name:'Pagination des fonctions',exact:true});}
async function rows(count,total){
  await until(async()=>await page.locator('.catalogue-total').isVisible()&&await page.locator('tbody tr').count()===count&&new RegExp('^'+total+' fonction').test(await page.locator('.catalogue-total').innerText()),'Résultats du catalogue');
}
async function reset(){const button=page.getByRole('button',{name:'Réinitialiser les filtres',exact:true});if(await button.isVisible())await button.click();await rows(25,27);}
async function created(path,click){
  const response=page.waitForResponse(r=>r.url()===base+path&&r.request().method()==='POST').then(r=>r.status());await click();assert.equal(await response,201);
  await page.waitForURL(new RegExp('/console/'+path.split('/').at(-1)+'/[0-9a-f-]{36}'));return {id:new URL(page.url()).pathname.split('/')[3]};
}
async function parent(kind,name){
  await page.getByRole('button',{name:'Choisir un '+kind,exact:true}).click();const dialog=page.getByRole('dialog');
  const choiceName=kind==='service'?name+' '+namespaceName:name;
  const query=kind==='namespace'?prefix:'catalogue',endpoint='/api/catalogue/'+(kind==='namespace'?'namespaces':'services');
  const searched=page.waitForResponse(r=>new URL(r.url()).pathname===endpoint&&new URL(r.url()).searchParams.get('q')===query&&new URL(r.url()).searchParams.get('offset')==='0');
  await dialog.getByRole('searchbox').fill(query);assert.equal((await searched).status(),200);
  await until(async()=>await dialog.getByRole('radio',{name:choiceName,exact:true}).count()>0||await dialog.getByText('Page 1 sur 2',{exact:true}).isVisible(),'Choix paginé');
  const pages=dialog.getByRole('navigation');
  if(!await dialog.getByRole('radio',{name:choiceName,exact:true}).count()){
    await pages.getByRole('button',{name:'Suivante',exact:true}).click();await dialog.getByText('Page 2 sur 2',{exact:true}).waitFor();
    assert(await dialog.getByRole('heading',{name:'Résultats de recherche',exact:true}).evaluate(e=>e===document.activeElement));
  }
  await dialog.getByRole('radio',{name:choiceName,exact:true}).check();await dialog.getByRole('button',{name:'Appliquer',exact:true}).click();await dialog.waitFor({state:'hidden'});
}
async function purge(row){
  let response=await context.request.get(base+'/api/archives/'+row.id);
  if(response.status()===404){await until(async()=>!(await api('/api/functions/'+row.id+'/instances')).items.length,'Fin des instances');await api('/api/functions/'+row.id,{method:'DELETE'});response=await context.request.get(base+'/api/archives/'+row.id);}
  assert.equal(response.status(),200);let archived=await response.json();
  if(!archived.purged_at){
    row.purgeId??=randomUUID();let operation=await api('/api/storage-operations/'+row.purgeId,{status:[200,404]});
    if(!operation.id)operation=await api('/api/archives/'+row.id+'/purge',{method:'POST',body:{operation_id:row.purgeId,confirm_name:archived.name},status:[200,202],headers:{'If-Match':String(archived.updated_at)}});
    await until(async()=>{const v=await api('/api/storage-operations/'+operation.id);assert.notEqual(v.state,'failed');return v.state==='completed';},'Fin de purge');archived=await api('/api/archives/'+row.id);
  }
  assert(archived.purged_at&&archived.artifact_bytes===0&&!archived.storage_operation);
  archives.push({function_id:row.id,namespace_id:row.namespace_id,operation_id:row.purgeId});
}
try{
  const state=JSON.parse(await readFile(new URL('admin-session.json',out),'utf8'));
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});
  page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',error=>faults.push(error.name));
  session=await api('/api/session');assert(session.authenticated);
  await check('Accueil normal, vide global et création par la navigation de gestion',async()=>{
    await page.goto(base+'/');await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
    await page.getByText('Aucune fonction. Créez un service et une fonction depuis Namespaces.',{exact:true}).waitFor();await capture('empty');
    await page.getByRole('link',{name:'Organiser les namespaces',exact:true}).click();await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    const dialog=page.getByRole('dialog');await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();
    await dialog.getByLabel('Nom',{exact:true}).fill(namespaceName);await dialog.getByLabel('Description',{exact:true}).fill('Été Café <texte>');
    primary=await created('/api/namespaces',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());namespaces.push(primary);
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();await dialog.getByLabel('Nom',{exact:true}).fill(serviceName);
    service=await created('/api/namespaces/'+primary.id+'/services',()=>dialog.getByRole('button',{name:'Enregistrer',exact:true}).click());services.push(service);
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();await dialog.getByLabel('Nom',{exact:true}).fill(functionName);await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    const fn=await created('/api/services/'+service.id+'/functions',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());functions.push({...fn,name:functionName,namespace_id:primary.id});
  });
  await check('Jeu réel au-delà d’une page, homonymes et publication exécutée par Docker',async()=>{
    let current=await api('/api/functions/'+functions[0].id);await api('/api/functions/'+current.id,{method:'PUT',headers:{'If-Match':String(current.updated_at)},body:{name:current.name,config:{...current.config,idle_seconds:0}}});
    secondary=await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix+'-other'}});namespaces.push(secondary);
    for(let i=0;i<4;i++)namespaces.push(await api('/api/namespaces',{method:'POST',status:201,body:{name:prefix+'-lookup-'+i}}));
    for(let i=0;i<5;i++)services.push(await api('/api/namespaces/'+primary.id+'/services',{method:'POST',status:201,body:{name:'catalogue-lookup-'+i}}));
    const other=await api('/api/namespaces/'+secondary.id+'/services',{method:'POST',status:201,body:{name:serviceName}});services.push(other);
    for(let i=1;i<=25;i++)functions.push({...await api('/api/services/'+service.id+'/functions',{method:'POST',status:201,body:{name:'entry-'+String(i).padStart(2,'0'),config:{handler:'handler.handler',idle_seconds:0}}}),namespace_id:primary.id});
    functions.push({...await api('/api/services/'+other.id+'/functions',{method:'POST',status:201,body:{name:functionName,config:{handler:'handler.handler',idle_seconds:0}}}),namespace_id:secondary.id});
    const full=(await api('/api/services/'+service.id+'/tokens',{method:'POST',status:201,body:{name:'catalogue-publication',rights:['read','create','update']}})).token;
    work=await mkdtemp(new URL('function-catalogue-ui-code-',out).pathname);await cp(new URL('../qualification/artifacts/invocation-addresses.cjs',import.meta.url),work+'/handler.cjs');
    await writeFile(work+'/revision.json',JSON.stringify({name:'catalogue-ui'}));
    await writeFile(work+'/serverless.yml',JSON.stringify({service:serviceName,provider:{name:'p2enjoy',runtime:'node24',p2enjoy:{idle_seconds:0}},functions:{[functionName]:{handler:'handler.handler'}},package:{patterns:['!**','*.cjs','revision.json']}}));
    const result=await run('python3',['-B','-m','adapter','deploy','--config',work+'/serverless.yml','--service',service.id],{timeout:300000,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:full}});
    assert(!result.stdout.includes(full));assert(JSON.parse(result.stdout).completed);
    const response=await context.request.get(base+'/invoke/'+functions[0].id,{headers:{'X-Serverless-Token':full}});assert.equal(response.status(),200);assert.equal((await response.json()).revision,'catalogue-ui');
    await page.getByRole('complementary',{name:'Navigation principale',exact:true}).getByRole('link',{name:'Fonctions',exact:true}).click();await rows(25,27);
  });
  await check('Recherche globale, contextes des homonymes et pagination au clavier',async()=>{
    await search().fill(prefix);await until(async()=>new URL(page.url()).searchParams.get('q')===prefix,'Recherche appliquée');await rows(25,27);
    assert.equal(await page.getByRole('link',{name:functionName,exact:true}).count(),2);await capture('desktop');
    await pagination().getByRole('button',{name:'Suivante',exact:true}).focus();await page.keyboard.press('Enter');await rows(2,27);
    assert.equal(new URL(page.url()).searchParams.get('page'),'2');assert(await page.getByRole('heading',{name:'Résultats',exact:true}).evaluate(e=>e===document.activeElement));
    await page.getByText('Page 2 sur 2',{exact:true}).waitFor();await capture('page-two');await pagination().getByRole('button',{name:'Précédente',exact:true}).click();await rows(25,27);
  });
  await check('Choix de namespace et de service recherchés, paginés et combinés avec l’état',async()=>{
    await parent('namespace',namespaceName);await rows(25,26);assert.equal(new URL(page.url()).searchParams.get('namespace_id'),primary.id);
    await parent('service',serviceName);await rows(25,26);assert.equal(new URL(page.url()).searchParams.get('service_id'),service.id);
    await page.getByLabel('État',{exact:true}).selectOption('published');await rows(1,1);await capture('filters');
    await parent('namespace',prefix+'-other');await rows(0,0);assert(!new URL(page.url()).searchParams.has('service_id'));
    await page.getByText('Aucune fonction ne correspond aux filtres.',{exact:true}).waitFor();await capture('no-match');await reset();
  });
  await check('Recherche invalide corrigée vers la recherche appliquée puis vers une saisie vide',async()=>{
    await search().fill(prefix);await until(async()=>new URL(page.url()).searchParams.get('q')===prefix,'Recherche appliquée');await rows(25,27);
    await search().fill('a b c d e f g h i');await page.getByRole('alert').waitFor();assert.equal(await page.locator('tbody tr').count(),0);await capture('invalid-search');
    await search().fill(prefix);await page.getByRole('alert').waitFor({state:'hidden'});await rows(25,27);
    await reset();await search().fill('a b c d e f g h i');await page.getByRole('alert').waitFor();await search().fill('');await page.getByRole('alert').waitFor({state:'hidden'});await rows(25,27);
  });
  await check('Saisie rapide sous vrai délai réseau : requête ancienne annulée et résultat récent conservé',async()=>{
    const cdp=await context.newCDPSession(page),aborted=[];page.on('requestfailed',request=>{if(request.url().includes('/api/functions?'))aborted.push(request.url());});
    await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:800,downloadThroughput:1000000,uploadThroughput:1000000});
    try{
      const first=page.waitForRequest(r=>r.url().includes('/api/functions?')&&new URL(r.url()).searchParams.get('q')===prefix+' entry-0');await search().fill(prefix+' entry-0');await first;
      await search().fill(prefix+' entry-2');await rows(6,6);assert(await page.locator('tbody tr').allTextContents().then(values=>values.every(v=>/entry-2[0-5]/.test(v))));
      await until(()=>aborted.length>0,'Annulation native de la première recherche');observations.push({scenario:'rapid-search',aborted_requests:aborted.length});await capture('latest-search');
    }finally{await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.detach();}
    await reset();
  });
  await check('Tri, historique précédent/suivant et rechargement conservent les critères de l’URL',async()=>{
    await search().fill(prefix);await until(async()=>new URL(page.url()).searchParams.get('q')===prefix,'Recherche appliquée');await rows(25,27);
    await page.getByLabel('Trier par',{exact:true}).selectOption('name_desc');await rows(25,27);await pagination().getByRole('button',{name:'Suivante',exact:true}).click();await rows(2,27);
    const target=page.url();await page.goBack();await rows(25,27);assert(!new URL(page.url()).searchParams.has('page'));
    await page.goForward();await rows(2,27);assert.equal(page.url(),target);await page.reload();await rows(2,27);assert.equal(await page.getByLabel('Trier par',{exact:true}).inputValue(),'name_desc');assert.equal(await search().inputValue(),prefix);await reset();
  });
  await check('Retour filtré à la page deux conservé dans les six facettes',async()=>{
    await search().fill(prefix);await until(async()=>new URL(page.url()).searchParams.get('q')===prefix,'Recherche appliquée');await rows(25,27);
    await pagination().getByRole('button',{name:'Suivante',exact:true}).click();await rows(2,27);const query=new URL(page.url()).search.slice(1);
    await page.getByRole('link',{name:'entry-25',exact:true}).click();await page.getByRole('heading',{name:'entry-25',exact:true}).waitFor();
    for(const tab of ['Code et révisions','Adresses d’appel','Stockage','Instances','Invocations','Configuration']){
      await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:tab,exact:true}).click();await page.getByRole('heading',{name:'entry-25',exact:true}).waitFor();
      assert.equal(new URL(page.url()).searchParams.get('catalogue'),query);assert.equal(await page.getByRole('link',{name:'Revenir au catalogue',exact:true}).getAttribute('href'),'/console/functions?'+query);
    }
    await capture('return-context');await page.getByRole('link',{name:'Revenir au catalogue',exact:true}).click();await rows(2,27);assert.equal(new URL(page.url()).search.slice(1),query);await reset();
  });
  await check('Retour au catalogue par défaut sans perdre le contexte vide',async()=>{
    await page.getByRole('link',{name:functionName,exact:true}).first().click();await page.getByRole('heading',{name:functionName,exact:true}).waitFor();
    assert.equal(new URL(page.url()).searchParams.get('catalogue'),'');await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Code et révisions',exact:true}).click();
    await page.getByRole('link',{name:'Revenir au catalogue',exact:true}).waitFor();assert.equal(new URL(page.url()).searchParams.get('catalogue'),'');
    assert.equal(await page.getByRole('link',{name:'Revenir au catalogue',exact:true}).getAttribute('href'),'/console/functions');await page.getByRole('link',{name:'Revenir au catalogue',exact:true}).click();await rows(25,27);
  });
  await check('Coupure réseau réelle retire les anciennes lignes puis permet une relance explicite',async()=>{
    try{await context.setOffline(true);await page.getByRole('button',{name:'Actualiser',exact:true}).click();await page.getByRole('alert').waitFor();assert.equal(await page.locator('tbody tr').count(),0);await capture('network-error');}
    finally{await context.setOffline(false);}
    await page.getByRole('button',{name:'Réessayer',exact:true}).click();await rows(25,27);
  });
  await check('Absence réelle du cookie de session et restauration de la session autorisée',async()=>{
    try{await context.clearCookies();await page.reload();await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).waitFor();assert.equal(await page.locator('tbody tr').count(),0);}
    finally{await context.addCookies(state.cookies);}
    await page.reload();await rows(25,27);session=await api('/api/session');assert(session.authenticated);
  });
  await check('Tablette et mobile : noms longs, défilement local et choix au clavier',async()=>{
    await page.setViewportSize({width:834,height:1112});await fits();await capture('tablet');
    await page.setViewportSize({width:390,height:844});await fits();await capture('mobile');
    const region=page.getByRole('region',{name:'Résultats des fonctions',exact:true});assert(await region.evaluate(e=>e.scrollWidth>e.clientWidth));
    await region.focus();await until(async()=>{if(await region.evaluate(e=>e.scrollLeft<=0))return true;await page.keyboard.press('ArrowLeft');return false;},'Bord gauche de table au clavier');await fits();await capture('mobile-table-left');
    await until(async()=>{const box=await region.boundingBox(),ns=await region.locator('th').nth(2).boundingBox(),handler=await region.locator('th').nth(3).boundingBox();if(ns.x>=box.x&&handler.x+handler.width<=box.x+box.width)return true;await page.keyboard.press('ArrowRight');return false;},'Namespace et handler complets dans le viewport');await fits();await capture('mobile-table-middle');
    await until(async()=>{if(await region.evaluate(e=>e.scrollLeft>=e.scrollWidth-e.clientWidth-2))return true;await page.keyboard.press('ArrowRight');return false;},'Dernière colonne de table au clavier');await fits();await capture('mobile-scrolled');
    const button=page.getByRole('button',{name:'Choisir un namespace',exact:true});await button.click();const dialog=page.getByRole('dialog');
    const searched=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/catalogue/namespaces'&&new URL(r.url()).searchParams.get('q')===prefix&&new URL(r.url()).searchParams.get('offset')==='0');
    await dialog.getByRole('searchbox').fill(prefix);assert.equal((await searched).status(),200);await dialog.getByText('Page 1 sur 2',{exact:true}).waitFor();
    await dialog.getByRole('navigation').getByRole('button',{name:'Suivante',exact:true}).focus();await page.keyboard.press('Enter');await dialog.getByText('Page 2 sur 2',{exact:true}).waitFor();
    assert(await dialog.getByRole('heading',{name:'Résultats de recherche',exact:true}).evaluate(e=>e===document.activeElement));await fits();await capture('mobile-picker');
    await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert(await button.evaluate(e=>e===document.activeElement));await page.setViewportSize({width:1440,height:1000});
  });
  await check('Suppression réelle depuis la page deux, retour puis recalage vers la dernière page existante',async()=>{
    await search().fill(prefix);await until(async()=>new URL(page.url()).searchParams.get('q')===prefix,'Recherche appliquée');await rows(25,27);
    await pagination().getByRole('button',{name:'Suivante',exact:true}).click();await rows(2,27);
    for(const [name,count,total] of [['entry-25',1,26],['entry-24',25,25]]){
      await page.getByRole('link',{name,exact:true}).click();await page.getByRole('heading',{name,exact:true}).waitFor();await page.getByRole('button',{name:'Supprimer la fonction',exact:true}).click();
      await page.getByRole('button',{name:'Supprimer la fonction',exact:true}).last().click();await rows(count,total);assert.equal(new URL(page.url()).pathname,'/console/functions');
    }
    assert(!new URL(page.url()).searchParams.has('page'));assert(await page.getByRole('heading',{name:'Résultats',exact:true}).evaluate(e=>e===document.activeElement));await capture('clamped-page');
  });
  await check('Liens de contexte, stockage navigateur et erreurs JavaScript',async()=>{
    const row=page.locator('tbody tr').first();await row.getByRole('link',{name:serviceName,exact:true}).click();await page.getByRole('heading',{name:serviceName,exact:true}).waitFor();
    await page.getByRole('link',{name:'Namespaces',exact:true}).first().click();await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);assert.deepEqual(faults,[]);
  });
  completed=true;
}catch(error){console.error('Catalogue UI interrompu :',error.name);throw error;}
finally{
  if(context){
    for(const row of functions)try{await purge(row);}catch(error){cleanupErrors.push({function_id:row.id,error:error.name});}
    for(const row of services)try{const current=await api('/api/services/'+row.id);await api('/api/services/'+row.id+'/configuration',{method:'PUT',body:{environment:{},replace_secrets:true,secrets:{}},headers:{'If-Match':String(current.updated_at)}});await api('/api/services/'+row.id,{method:'DELETE'});}catch(error){cleanupErrors.push({service_id:row.id,error:error.name});}
    for(const row of namespaces)try{await api('/api/namespaces/'+row.id,{method:'DELETE'});}catch(error){cleanupErrors.push({namespace_id:row.id,error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});if(browser)await browser.close();
  await writeFile(new URL('function-catalogue-ui.json',out),JSON.stringify({completed:completed&&!cleanupErrors.length&&!faults.length,checks,observations,captures,faults,cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,skipped:0,namespaces:namespaces.map(v=>v.id),service_ids:services.map(v=>v.id),function_ids:functions.map(v=>v.id),storage_archives:archives},null,2)+'\n');
}
assert(completed&&!cleanupErrors.length&&!faults.length);
