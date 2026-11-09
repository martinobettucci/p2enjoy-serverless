// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#console-et-manuel | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium} from 'playwright';
import {enterNamespaces} from './console-navigation.mjs';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const prefix='version-registry-ui-'+randomUUID().slice(0,8),checks=[],captures={},faults=[],evidence=[],pending=[],cleanupErrors=[],creations=[];
let browser,context,page,session,namespace,service,fn,work,completed=false,cleanup=false;
async function save(){await writeFile(new URL('function-version-registry-ui.json',out),JSON.stringify({target:base,prefix,completed:completed&&cleanup&&!faults.length,cleanup,cleanup_errors:cleanupErrors,creations,skipped:0,checks,captures,faults,evidence,
  namespace_id:namespace?.id,service_id:service?.id,function_id:fn?.id},null,2)+'\n',{mode:0o600});}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(e){checks.push({name,status:'failed',error:e.name});throw e;}}
function watch(promise){const tracked=promise.then(value=>({value}),error=>({error}));pending.push(tracked);return tracked;}
async function observed(promise){const r=await promise;if(r.error)throw r.error;return r.value;}
async function created(path,action){
  const kind=path.split('/').at(-1),intent={kind,status:null,id:null};creations.push(intent);await save();
  const waiting=watch(page.waitForResponse(r=>r.url()===base+path&&r.request().method()==='POST'));await action();const r=await observed(waiting);
  intent.status=r.status();await save();assert.equal(r.status(),201);
  await page.waitForURL(new RegExp('/console/'+kind+'/[0-9a-f-]{36}(?:/|$)'));intent.id=new URL(page.url()).pathname.split('/')[3];await save();return {id:intent.id};
}
async function api(path,{method='GET',body,status=200,headers={}}={}){const r=await context.request.fetch(base+path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers},timeout:120000});assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);return r.json();}
async function ready(){await page.waitForFunction(()=>{const b=document.querySelector('.publication-view button.primary');return b&&!b.disabled;});}
async function refresh(){await page.getByRole('region',{name:'Code de la fonction',exact:true}).getByRole('button',{name:'Actualiser',exact:true}).click();await ready();}
async function capture(name,fullPage=true){
  if(fullPage)await page.evaluate(()=>scrollTo(0,0));
  const file=new URL(`function-version-registry-${name}.jpg`,out),bytes=await page.screenshot({path:file.pathname,type:'jpeg',quality:85,fullPage});
  captures[file.pathname.split('/').at(-1)]={sha256:createHash('sha256').update(bytes).digest('hex'),viewport:page.viewportSize(),full_page:fullPage};
}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
const card=id=>page.getByRole('article',{name:'Révision '+id,exact:true});
async function publish(){await ready();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();const dialog=page.getByRole('dialog');
  await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(new URL('function.zip',work).pathname);await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
  await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();const wait=watch(page.waitForResponse(r=>r.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(r.url()).pathname),{timeout:120000}));
  await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();assert.equal((await observed(wait)).status(),200);await dialog.waitFor({state:'hidden'});await ready();
  return (await api(`/api/functions/${fn.id}`)).active_revision_id;
}
async function until(action){const end=Date.now()+120000;while(Date.now()<end){const r=await action();if(r)return r;await new Promise(r=>setTimeout(r,150));}assert.fail('Cycle réel non terminé');}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),viewport:{width:1440,height:1000},locale:'fr-FR'});
  page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',e=>faults.push(e.name));session=await api('/api/session');assert(session.authenticated);
  work=new URL((await mkdtemp(new URL('version-registry-ui-code-',out).pathname))+'/','file:');
  await cp(new URL('../qualification/artifacts/invocation-addresses.cjs',import.meta.url),new URL('handler.cjs',work));await writeFile(new URL('revision.json',work),JSON.stringify({name:'registry-ui'}));
  await run('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(p/'function.zip','w');[z.write(p/n,n) for n in ('handler.cjs','revision.json')];z.close()",work.pathname]);
  let first,hash;
  await check('Accueil et formulaires : vrai upload, hash complet et copie clavier',async()=>{
    await enterNamespaces(page,base);await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill(prefix);
    namespace=await created('/api/namespaces',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());await save();
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('code-identity');
    service=await created(`/api/namespaces/${namespace.id}/services`,()=>dialog.getByRole('button',{name:'Enregistrer',exact:true}).click());await save();
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Nom',{exact:true}).fill('readable-code-identity');await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    fn=await created(`/api/services/${service.id}/functions`,()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());await save();
    await page.getByRole('button',{name:'Modifier l’exécution',exact:true}).click();dialog=page.getByRole('dialog');await dialog.getByLabel('Inactivité avant extinction (s)',{exact:true}).fill('0');
    const changed=watch(page.waitForResponse(r=>r.url()===base+`/api/functions/${fn.id}`&&r.request().method()==='PUT'));
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();assert.equal((await observed(changed)).status(),200);await dialog.waitFor({state:'hidden'});
    const tab=page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Code et révisions',exact:true});await tab.focus();await page.keyboard.press('Enter');first=await publish();
    const row=(await api(`/api/functions/${fn.id}/revisions`)).items.find(r=>r.id===first);hash=row.code_hash;assert.match(hash,/^[0-9a-f]{64}$/);
    await card(first).getByText(hash,{exact:true}).waitFor();await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});
    const copy=card(first).getByRole('button',{name:'Copier le hash du code',exact:true});await copy.focus();await page.keyboard.press('Enter');await card(first).getByText('Hash du code copié.',{exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),hash);await fits();await capture('copy-desktop');
    await card(first).scrollIntoViewIfNeeded();await capture('copy-viewport-desktop',false);
    await refresh();assert.equal(await card(first).getByText('Hash du code copié.',{exact:true}).count(),0);
    evidence.push({revision_id:first,code_hash:hash,clipboard_match:true,confirmation_cleared_by_refresh:true});
  });
  await check('Même contenu : deux cartes au même hash, copie et navigation mobile',async()=>{
    const second=await publish();assert.notEqual(second,first);const history=(await api(`/api/functions/${fn.id}/revisions`)).items;
    assert.equal(history.length,2);assert(history.every(r=>r.code_hash===hash));await page.setViewportSize({width:390,height:844});
    for(const id of [first,second]){await card(id).getByText(hash,{exact:true}).waitFor();await card(id).getByRole('button',{name:'Copier le hash du code',exact:true}).click();await card(id).getByText('Hash du code copié.',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),hash);}
    await fits();await capture('same-code-mobile');
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Adresses d’appel',exact:true}).click();
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Code et révisions',exact:true}).click();await ready();assert.equal(await page.getByText('Hash du code copié.',{exact:true}).count(),0);
    const token=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-observed-code',rights:['read']}});
    const r=await context.request.get(base+`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':token.token}});assert.equal(r.status(),200);assert.equal((await r.json()).revision,'registry-ui');
    await api(`/api/tokens/${token.id}/revoke`,{method:'POST'});evidence.push({same_hash_aliases:[first,second],invocation_id:r.headers()['x-serverless-request-id'],confirmation_cleared_by_navigation:true});
  });
  await check('Refus natif du presse-papiers : diagnostic, texte et reprise',async()=>{
    const cdp=await context.newCDPSession(page);
    try{
      const {targetInfo}=await cdp.send('Target.getTargetInfo');for(const allowWithoutSanitization of [false,true])await cdp.send('Browser.setPermission',{permission:{name:'clipboard-write',allowWithoutSanitization},setting:'denied',origin:base,browserContextId:targetInfo.browserContextId});
      assert.equal(await page.evaluate(async()=>(await navigator.permissions.query({name:'clipboard-write'})).state),'denied');
      await card(first).getByRole('button',{name:'Copier le hash du code',exact:true}).click();await card(first).getByText('Copie refusée. Sélectionnez et copiez le hash affiché.',{exact:true}).waitFor();
      assert.equal(await card(first).getByText('Hash du code copié.',{exact:true}).count(),0);assert.notEqual(await card(first).getByText(hash,{exact:true}).evaluate(e=>getComputedStyle(e).userSelect),'none');await fits();await capture('clipboard-refused-mobile');
      await card(first).scrollIntoViewIfNeeded();await capture('clipboard-refused-viewport-mobile',false);
    }finally{await context.clearPermissions();await cdp.detach();}
    await refresh();assert.equal(await page.getByText('Copie refusée. Sélectionnez et copiez le hash affiché.',{exact:true}).count(),0);
    await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});await card(first).getByRole('button',{name:'Copier le hash du code',exact:true}).click();await card(first).getByText('Hash du code copié.',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),hash);await fits();await capture('clipboard-recovered-mobile');
  });
  completed=true;
}finally{
  try{
  if(page){
    const path=new URL(page.url()).pathname.split('/');
    for(const intent of creations)if(!intent.id&&path[2]===intent.kind&&/^[0-9a-f-]{36}$/.test(path[3]))intent.id=path[3];
    namespace??=creations.find(r=>r.kind==='namespaces'&&r.id);service??=creations.find(r=>r.kind==='services'&&r.id);fn??=creations.find(r=>r.kind==='functions'&&r.id);
  }
  await page?.close();await Promise.all(pending);
  if(fn){await until(async()=>!(await api(`/api/functions/${fn.id}/instances`)).items.length);await api(`/api/functions/${fn.id}`,{method:'DELETE'});
    await until(async()=>!(await api(`/api/archives/${fn.id}`)).storage_operation);const archive=await api(`/api/archives/${fn.id}`);
    const op=await api(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archive.updated_at)},body:{operation_id:randomUUID(),confirm_name:archive.name}});
    await until(async()=>{const r=await api(`/api/storage-operations/${op.id}`);assert.notEqual(r.state,'aborted');return r.state==='completed';});evidence.push({purged_function_id:fn.id,operation_id:op.id});}
  if(service)await api(`/api/services/${service.id}`,{method:'DELETE'});if(namespace)await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});
  if(work)await rm(work,{recursive:true});assert(creations.every(r=>r.id),'Création non résolue : conserver et reprendre explicitement son nettoyage');cleanup=true;
  }catch(error){cleanupErrors.push({error:error.name});throw error;}
  finally{try{await save();}finally{try{await context?.close();}finally{await browser?.close();}}}
}
