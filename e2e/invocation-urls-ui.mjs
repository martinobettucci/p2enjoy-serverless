// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#qualification-réelle-et-autorité | docs/manual.md
// Real console entry, creation/publication UI, native clipboard and Docker calls.
import {enterNamespaces} from './console-navigation.mjs';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {randomUUID,createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium} from 'playwright';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url);
const prefix='invocation-addresses-ui-'+randomUUID().slice(0,8);
const functionName='function-with-long-name-for-invocation-address-observation-'+randomUUID().slice(0,4);
const checks=[],captures={},faults=[],cleanupErrors=[],observations=[];
let browser,context,page,namespace,service,fn,session,token,work,completed=false,purged,failure;
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function capture(name){
  if(name!=='manual-mobile')await page.evaluate(()=>scrollTo(0,0));
  const path=new URL('invocation-urls-ui-'+name+'.jpg',out);
  const bytes=await page.screenshot({path:path.pathname,type:'jpeg',quality:85,fullPage:name!=='manual-mobile'});
  captures[path.pathname.split('/').at(-1)]={sha256:createHash('sha256').update(bytes).digest('hex'),viewport:page.viewportSize()};
}
async function api(path,{method='GET',body,status=200,headers={}}={}){
  const response=await context.request.fetch(base+path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),method+' '+path+': '+response.status());return response.json();
}
async function create(path,click){
  // The destination identifies the created object even after navigation releases the response body.
  const response=page.waitForResponse(r=>r.url()===base+path&&r.request().method()==='POST').then(r=>r.status());
  await click();assert.equal(await response,201);
  const kind=path.split('/').at(-1);
  await page.waitForURL(new RegExp('/console/'+kind+'/[0-9a-f-]{36}'));
  return {id:new URL(page.url()).pathname.split('/')[3]};
}
async function addresses(){await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Adresses d’appel',exact:true}).click();await ready();}
async function ready(){await page.getByRole('heading',{name:'Adresses d’appel',exact:true}).waitFor();await page.getByRole('button',{name:'Actualiser',exact:true}).waitFor({state:'visible'});await page.waitForFunction(()=>{const button=[...document.querySelectorAll('button')].find(b=>b.textContent==='Actualiser');return button&&!button.disabled;});}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page_overflow');}
async function copiedCall(expected){
  const text=await page.evaluate(()=>navigator.clipboard.readText());
  assert(text.startsWith(base+'/invoke/'+fn.id));
  const response=await context.request.get(text,{headers:{'X-Serverless-Token':token}});assert.equal(response.status(),200);assert.equal((await response.json()).revision,expected);
  observations.push({copied_url:text,invoked:true});return text;
}
await mkdir(out,{recursive:true,mode:0o700});
await writeFile(new URL('invocation-urls-ui.json',out),JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
try{
  const state=JSON.parse(await readFile(new URL('admin-session.json',out),'utf8'));
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});
  page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',error=>faults.push(error.name));
  session=await(await context.request.get(base+'/api/session')).json();assert(session.authenticated);
  work=await mkdtemp(new URL('invocation-addresses-ui-code-',out).pathname);
  await cp(new URL('../qualification/artifacts/invocation-addresses.cjs',import.meta.url),work+'/handler.cjs');
  await writeFile(work+'/revision.json',JSON.stringify({name:'ui-one'}));
  await promisify(execFile)('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(p/'function.zip','w');[z.write(p/n,n) for n in ('handler.cjs','revision.json')];z.close()",work]);
  await check('Accueil normal, création UI et lien des adresses depuis le service',async()=>{
    await enterNamespaces(page,base);
    await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(prefix);
    namespace=await create('/api/namespaces',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('function-addresses');
    service=await create(`/api/namespaces/${namespace.id}/services`,()=>dialog.getByRole('button',{name:'Enregistrer',exact:true}).click());
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(functionName);await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    fn=await create(`/api/services/${service.id}/functions`,()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());
    await page.getByRole('link',{name:'Fonctions du service',exact:true}).click();
    await page.getByRole('link',{name:`Adresses d’appel de ${functionName}`,exact:true}).click();await ready();
    assert.equal(new URL(page.url()).pathname,`/console/functions/${fn.id}/invocation-urls`);
    await page.getByText('Fonction brouillon : publiez une révision dans Code et révisions pour obtenir ses adresses.',{exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:'Copier l’adresse',exact:true}).count(),0);
    await capture('draft-desktop');
    token=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'invoke-addresses',rights:['read']},status:201})).token;
  });
  await check('Publication UI réelle puis adresses de la révision publiée',async()=>{
    await page.getByRole('link',{name:'Code et révisions',exact:true}).click();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();
    const dialog=page.getByRole('dialog');await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(work+'/function.zip');await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();
    const response=page.waitForResponse(r=>r.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(r.url()).pathname));
    await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();assert.equal((await response).status(),200);
    await dialog.waitFor({state:'hidden'});await addresses();await page.getByText('Disponibilité non vérifiée',{exact:true}).first().waitFor();
    await page.getByText('HTTPS déclaré',{exact:true}).first().waitFor();
    assert(await page.getByRole('button',{name:'Copier l’adresse',exact:true}).count()>=1);await fits();await capture('published-desktop');
  });
  await check('Presse-papiers natif : adresse et exemple GET, invocation du code Docker',async()=>{
    await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});
    const item=page.locator('.observation-list>li').filter({has:page.getByRole('heading',{name:'serverless.lelabs.tech',exact:true})});
    await item.getByRole('button',{name:'Copier l’adresse',exact:true}).click();await item.getByText('Adresse copiée.',{exact:true}).waitFor();await copiedCall('ui-one');
    await item.getByRole('button',{name:'Copier l’exemple curl',exact:true}).click();await item.getByText('Exemple copié.',{exact:true}).waitFor();
    const curl=await page.evaluate(()=>navigator.clipboard.readText());assert(curl.startsWith('curl --request GET '));assert(curl.includes('VOTRE_JETON')&&!curl.includes(token));
    await item.getByText('Exemple curl',{exact:true}).click();await item.locator('pre').waitFor();assert.equal(await item.locator('pre').innerText(),curl);await capture('copy-desktop');
    await page.getByRole('button',{name:'Actualiser',exact:true}).focus();await page.keyboard.press('Enter');await ready();
    assert.equal(await page.locator('.notice.success').count(),0);assert.equal(await page.evaluate(()=>document.activeElement?.id),'invocation-urls-title');
  });
  await check('Refus natif de presse-papiers : erreur utile et texte sélectionnable',async()=>{
    const cdp=await context.newCDPSession(page);
    try{
      const {targetInfo}=await cdp.send('Target.getTargetInfo');
      for(const allowWithoutSanitization of [false,true])await cdp.send('Browser.setPermission',{permission:{name:'clipboard-write',allowWithoutSanitization},setting:'denied',origin:base,browserContextId:targetInfo.browserContextId});
      assert.equal(await page.evaluate(async()=> (await navigator.permissions.query({name:'clipboard-write'})).state),'denied');
      await page.getByRole('button',{name:'Copier l’adresse',exact:true}).first().click();
      await page.getByText('Copie refusée. Sélectionnez et copiez le texte affiché.',{exact:true}).waitFor();
      assert.equal(await page.locator('.notice.success').count(),0);assert.notEqual(await page.locator('.invocation-url').first().evaluate(node=>getComputedStyle(node).userSelect),'none');await capture('clipboard-denied');
    }finally{await context.clearPermissions();await cdp.detach();}
  });
  await check('Vraie coupure réseau : anciennes adresses retirées et reprise explicite',async()=>{
    try{
      await context.setOffline(true);await page.getByRole('button',{name:'Actualiser',exact:true}).click();
      await page.getByRole('alert').waitFor();assert.equal(await page.getByRole('button',{name:'Copier l’adresse',exact:true}).count(),0);assert.equal(await page.locator('.invocation-url').count(),0);await capture('network-error');
    }finally{await context.setOffline(false);}
    await page.getByRole('button',{name:'Actualiser',exact:true}).click();await ready();await page.getByRole('button',{name:'Copier l’adresse',exact:true}).first().waitFor();assert.equal(await page.getByRole('alert').count(),0);
  });
  await check('Clavier et mobile 390 px, nom long complet, URL et exemple lisibles',async()=>{
    await page.setViewportSize({width:390,height:844});await fits();assert.equal(await page.getByRole('heading',{name:functionName,exact:true}).innerText(),functionName);
    const copy=page.getByRole('button',{name:'Copier l’exemple curl',exact:true}).first();await copy.focus();await page.keyboard.press('Tab');
    assert(await page.evaluate(()=>document.activeElement?.tagName==='SUMMARY'));
    await page.keyboard.press('Enter');await page.locator('.invocation-log').first().waitFor();await fits();await capture('published-mobile');
    await page.getByRole('link',{name:'Consulter le manuel des adresses d’appel',exact:true}).click();
    await page.getByRole('heading',{name:'Adresses d’appel',exact:true}).waitFor();assert.equal(new URL(page.url()).hash,'#adresses-d-appel');
    const article=page.getByRole('article',{name:'Guide d’utilisation'}),source=await readFile(new URL('../docs/manual.md',import.meta.url));
    assert.equal(await article.getAttribute('data-manual-sha256'),createHash('sha256').update(source).digest('hex'));await fits();await capture('manual-mobile');
  });
  assert.equal(faults.length,0);completed=true;
}catch(error){
  failure={name:error.name,message:error.message.split('\n')[0].replaceAll(token||'\u0000','[redacted]')};
  if(page)try{await capture('failure');}catch{}
  throw new Error('invocation_urls_ui_failed');
}
finally{
  if(context){
    await context.setOffline(false);
    // Recover campaign identities even if a navigation discarded a creation response.
    try{
      if(!namespace)namespace=(await api('/api/namespaces?limit=100')).items.find(row=>row.name===prefix);
      if(namespace&&!service)service=(await api(`/api/namespaces/${namespace.id}/services?limit=100`)).items.find(row=>row.name==='function-addresses');
      if(service&&!fn)fn=(await api(`/api/services/${service.id}/functions?limit=100`)).items.find(row=>row.name===functionName);
    }catch(error){cleanupErrors.push({resource:'campaign-identity',error:error.name});}
    if(fn)try{
      await api(`/api/functions/${fn.id}`,{method:'DELETE'});const archive=await api(`/api/archives/${fn.id}`);
      let operation=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],body:{operation_id:randomUUID(),confirm_name:archive.name},headers:{'If-Match':String(archive.updated_at)}});
      const deadline=Date.now()+90000;
      while(operation.state!=='completed'&&Date.now()<deadline){assert.notEqual(operation.state,'failed');await new Promise(resolve=>setTimeout(resolve,200));operation=await api(`/api/storage-operations/${operation.id}`);}
      assert.equal(operation.state,'completed');purged={function_id:fn.id,operation_id:operation.id};
    }catch(error){cleanupErrors.push({resource:'function',error:error.name});}
    if(service)try{await api(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'service',error:error.name});}
    if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'namespace',error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});await browser?.close();
  await writeFile(new URL('invocation-urls-ui.json',out),JSON.stringify({completed:completed&&!cleanupErrors.length&&!faults.length,prefix,checks,skipped:0,captures,faults,failure,cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,service_id:service?.id,function_id:fn?.id,purged,observations},null,2)+'\n');
  assert.equal(cleanupErrors.length,0,'cleanup_required');
}
