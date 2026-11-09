// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium} from 'playwright';
import {enterNamespaces} from './console-navigation.mjs';

const base='https://serverless.lelabs.tech',out=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const prefix='version-execution-ui-'+randomUUID().slice(0,8),checks=[],captures={},faults=[],evidence=[],pending=[],cleanupErrors=[],creations=[];
let browser,context,page,session,namespace,service,fn,work,completed=false,cleanup=false;
async function save(){await writeFile(new URL('function-versions-ui.json',out),JSON.stringify({target:base,prefix,completed:completed&&cleanup&&!faults.length,cleanup,cleanup_errors:cleanupErrors,creations,skipped:0,checks,captures,faults,evidence,
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
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){const r=await context.request.fetch(base+path,{method,data:bytes ? await readFile(bytes) : body,headers:{...(bytes?{'Content-Type':'application/zip'}:{}),Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers},timeout:120000});assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);return r.json();}
async function ready(){await page.waitForFunction(()=>{const b=document.querySelector('.publication-view button.primary');return b&&!b.disabled;});}
async function refresh(){await page.getByRole('region',{name:'Code de la fonction',exact:true}).getByRole('button',{name:'Actualiser',exact:true}).click();await ready();}
async function capture(name,fullPage=true){
  if(fullPage)await page.evaluate(()=>scrollTo(0,0));
  const file=new URL(`function-versions-${name}.jpg`,out),bytes=await page.screenshot({path:file.pathname,type:'jpeg',quality:85,fullPage});
  captures[file.pathname.split('/').at(-1)]={sha256:createHash('sha256').update(bytes).digest('hex'),viewport:page.viewportSize(),full_page:fullPage};
}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
const card=hash=>page.getByRole('article',{name:'Version '+hash,exact:true});
async function publicationFollow(response){
  assert.equal(response.status(),200);const path=new URL(response.url()).pathname;
  assert.match(path,/^\/api\/deployments\/[0-9a-f-]{36}\/artifact$/);
  const id=path.split('/')[3],result=await api(`/api/deployments/${id}`);
  assert.equal(result.id,id);assert.equal(result.function_id,fn.id);assert.equal(result.state,'published');
  assert(result.validation?.valid&&result.validation?.container_removed,'real_validator_completed_and_removed');
  await page.getByRole('dialog').waitFor({state:'hidden'});await ready();
  const notice=result.version_restored?'Version réimportée.':result.code_changed?'Nouvelle version publiée.':'Code inchangé : version réutilisée.';
  await page.getByRole('region',{name:'Code de la fonction',exact:true}).getByText(notice,{exact:true}).waitFor();
  evidence.push({artifact_request:{url:response.url(),status:response.status(),body_read:false},
    publication_follow:{id,state:result.state,code_hash:result.code_hash,code_changed:result.code_changed,version_restored:result.version_restored},visible_notice:notice});
  return result;
}
async function publish(){await ready();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();const dialog=page.getByRole('dialog');
  await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(new URL('function.zip',work).pathname);await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
  await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();const wait=watch(page.waitForResponse(r=>r.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(r.url()).pathname),{timeout:120000}));
  await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();
  return publicationFollow(await observed(wait));
}
async function until(action){const end=Date.now()+120000;while(Date.now()<end){const r=await action();if(r)return r;await new Promise(r=>setTimeout(r,150));}assert.fail('Cycle réel non terminé');}
async function promoteInUi(hash){
  const target=card(hash);await target.getByRole('button',{name:'Promouvoir cette version',exact:true}).first().click();
  const waiting=watch(page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}/promote`));
  await target.locator('.confirm').getByRole('button',{name:'Promouvoir cette version',exact:true}).click();assert.equal((await observed(waiting)).status(),200);await ready();
  await card(hash).getByText('Cible par défaut',{exact:true}).waitFor();
}
async function prepareExternal(file,handler='handler.handler'){
  const current=await api(`/api/functions/${fn.id}`),candidate=await api(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(current.updated_at)},body:{deployment_id:randomUUID(),handler}});
  return {candidate,send:()=>api(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',body:undefined,bytes:file})};
}
async function archiveZip(name,files){const target=new URL(name,work).pathname;
  await run('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(sys.argv[2],'w');[z.write(p/n,n) for n in sys.argv[3:]];z.close()",work.pathname,target,...files]);return target;}
await mkdir(out,{recursive:true,mode:0o700});await save();
try{
  browser=await chromium.launch({headless:true});context=await browser.newContext({storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),viewport:{width:1440,height:1000},locale:'fr-FR'});
  page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',e=>faults.push(e.name));session=await api('/api/session');assert(session.authenticated);
  work=new URL((await mkdtemp(new URL('version-execution-ui-code-',out).pathname))+'/','file:');
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
    assert.equal((await api(`/api/functions/${fn.id}`)).active_revision_id,null);
    const row=(await api(`/api/functions/${fn.id}/revisions`)).items.find(r=>r.id===first.revision_id);hash=row.code_hash;assert.match(hash,/^[0-9a-f]{64}$/);
    await card(hash).getByText(hash,{exact:true}).waitFor();await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});
    await cp(new URL('function.zip',work),new URL('first.zip',work));
    const copy=card(hash).getByRole('button',{name:'Copier le hash du code',exact:true});await copy.focus();await page.keyboard.press('Enter');await card(hash).getByText('Hash du code copié.',{exact:true}).waitFor();
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),hash);await fits();await capture('copy-desktop');
    await card(hash).scrollIntoViewIfNeeded();await capture('copy-viewport-desktop',false);
    await refresh();assert.equal(await card(hash).getByText('Hash du code copié.',{exact:true}).count(),0);
    evidence.push({revision_id:first.revision_id,code_hash:hash,clipboard_match:true,confirmation_cleared_by_refresh:true});
  });
  await check('Même contenu : une version réutilisée, promotion et adresses mobiles',async()=>{
    const second=await publish();assert.equal(second.revision_id,first.revision_id);assert.equal(second.code_hash,hash);assert.equal(second.code_changed,false);
    assert.equal((await api(`/api/functions/${fn.id}/versions`)).total,1);assert.equal((await api(`/api/functions/${fn.id}/revisions`)).items.length,1);
    await page.setViewportSize({width:390,height:844});await card(hash).getByRole('button',{name:'Copier le hash du code',exact:true}).click();
    await card(hash).getByText('Hash du code copié.',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),hash);await fits();await capture('same-code-mobile');
    await promoteInUi(hash);
    await card(hash).getByRole('link',{name:'Adresses de cette version',exact:true}).click();await page.getByText('Hash explicite',{exact:true}).waitFor();
    assert.equal(new URL(page.url()).searchParams.get('version'),hash);
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Code et révisions',exact:true}).click();await ready();assert.equal(await page.getByText('Hash du code copié.',{exact:true}).count(),0);
    const token=await api(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'invoke-observed-version',rights:['read']}});
    const r=await context.request.get(base+`/invoke/${fn.id}@${hash}`,{headers:{'X-Serverless-Token':token.token}});assert.equal(r.status(),200);assert.equal((await r.json()).revision,'registry-ui');assert.equal(r.headers()['x-serverless-code-hash'],hash);
    await api(`/api/tokens/${token.id}/revoke`,{method:'POST'});evidence.push({deduplicated_revision_id:first.revision_id,code_hash:hash,invocation_id:r.headers()['x-serverless-request-id'],confirmation_cleared_by_navigation:true});
  });
  await check('Refus natif du presse-papiers : diagnostic, texte et reprise',async()=>{
    const cdp=await context.newCDPSession(page);
    try{
      const {targetInfo}=await cdp.send('Target.getTargetInfo');for(const allowWithoutSanitization of [false,true])await cdp.send('Browser.setPermission',{permission:{name:'clipboard-write',allowWithoutSanitization},setting:'denied',origin:base,browserContextId:targetInfo.browserContextId});
      assert.equal(await page.evaluate(async()=>(await navigator.permissions.query({name:'clipboard-write'})).state),'denied');
      await card(hash).getByRole('button',{name:'Copier le hash du code',exact:true}).click();await card(hash).getByText('Copie refusée. Sélectionnez et copiez le hash affiché.',{exact:true}).waitFor();
      assert.equal(await card(hash).getByText('Hash du code copié.',{exact:true}).count(),0);assert.notEqual(await card(hash).getByText(hash,{exact:true}).evaluate(e=>getComputedStyle(e).userSelect),'none');await fits();await capture('clipboard-refused-mobile');
      await card(hash).scrollIntoViewIfNeeded();await capture('clipboard-refused-viewport-mobile',false);
    }finally{await context.clearPermissions();await cdp.detach();}
    await refresh();assert.equal(await page.getByText('Copie refusée. Sélectionnez et copiez le hash affiché.',{exact:true}).count(),0);
    await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});await card(hash).getByRole('button',{name:'Copier le hash du code',exact:true}).click();await card(hash).getByText('Hash du code copié.',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),hash);await fits();await capture('clipboard-recovered-mobile');
  });
  await check('Archive/restore et vrai conflit de promotion : confirmation et focus conservés',async()=>{
    await ready();await card(hash).getByRole('button',{name:'Archiver cette version',exact:true}).click();let dialog=page.getByRole('dialog',{name:'Archiver la version courante',exact:true});
    await dialog.getByLabel('Cible après retrait',{exact:true}).selectOption('disable');await dialog.getByRole('button',{name:'Vérifier le retrait',exact:true}).click();
    let waiting=watch(page.waitForResponse(r=>new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}/archive`&&r.request().method()==='POST'));
    await dialog.getByRole('button',{name:'Confirmer l’archivage',exact:true}).click();assert.equal((await observed(waiting)).status(),200);await dialog.waitFor({state:'hidden'});await ready();
    await card(hash).getByText('Archivée',{exact:true}).waitFor();assert.equal((await api(`/api/functions/${fn.id}`)).active_revision_id,null);
    waiting=watch(page.waitForResponse(r=>new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}/restore`&&r.request().method()==='POST'));
    await card(hash).getByRole('button',{name:'Restaurer cette version',exact:true}).click();assert.equal((await observed(waiting)).status(),200);await ready();assert.equal((await api(`/api/functions/${fn.id}`)).active_revision_id,null);
    await card(hash).getByRole('button',{name:'Promouvoir cette version',exact:true}).first().click();
    const current=await api(`/api/functions/${fn.id}`);await api(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(current.updated_at)},body:{name:current.name,config:{...current.config,cpu:.1}}});
    waiting=watch(page.waitForResponse(r=>new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}/promote`&&r.request().method()==='POST'));
    await card(hash).locator('.confirm').getByRole('button',{name:'Promouvoir cette version',exact:true}).click();assert.equal((await observed(waiting)).status(),409);
    await card(hash).getByRole('alert').waitFor();await ready();assert(await page.evaluate(()=>Boolean(document.activeElement?.closest('.confirm'))),'refusal_focus_must_remain_in_confirmation');
    await fits();await capture('promotion-conflict-mobile',false);await card(hash).locator('.confirm').getByRole('button',{name:'Annuler',exact:true}).click();
    await promoteInUi(hash);await fits();await capture('restored-mobile');
  });
  await check('Refus de retrait conservé, suppression puis réimportation du même hash',async()=>{
    await card(hash).getByRole('button',{name:'Supprimer cette version',exact:true}).click();let dialog=page.getByRole('dialog',{name:'Supprimer la version courante',exact:true});
    await dialog.getByLabel('Cible après retrait',{exact:true}).selectOption('replacement');await dialog.getByLabel('Hash de remplacement',{exact:true}).fill('0'.repeat(64));
    await dialog.getByRole('button',{name:'Vérifier le retrait',exact:true}).click();let waiting=watch(page.waitForResponse(r=>new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}`&&r.request().method()==='DELETE'));
    await dialog.getByRole('button',{name:'Confirmer la suppression',exact:true}).click();assert.equal((await observed(waiting)).status(),404);
    await dialog.getByRole('alert').getByText('La version demandée est inconnue, archivée ou supprimée.',{exact:true}).waitFor();await ready();
    assert.equal(await dialog.getByLabel('Hash de remplacement',{exact:true}).inputValue(),'0'.repeat(64));await dialog.getByRole('group',{name:'Confirmation de l’opération',exact:true}).waitFor();
    assert(await page.evaluate(()=>Boolean(document.activeElement?.closest('dialog'))),'refusal_focus_must_remain_in_dialog');await fits();await capture('withdrawal-refused-mobile',false);
    await dialog.getByRole('button',{name:'Revenir à la saisie',exact:true}).click();await dialog.getByLabel('Cible après retrait',{exact:true}).selectOption('disable');
    await dialog.getByRole('button',{name:'Vérifier le retrait',exact:true}).click();waiting=watch(page.waitForResponse(r=>new URL(r.url()).pathname===`/api/functions/${fn.id}/versions/${hash}`&&r.request().method()==='DELETE'));
    await dialog.getByRole('button',{name:'Confirmer la suppression',exact:true}).click();assert.equal((await observed(waiting)).status(),200);await dialog.waitFor({state:'hidden'});await ready();await card(hash).getByText('Supprimée',{exact:true}).waitFor();
    await card(hash).getByRole('button',{name:'Réimporter cette version',exact:true}).click();dialog=page.getByRole('dialog',{name:'Réimporter une version',exact:true});
    assert(await dialog.getByLabel('Handler',{exact:true}).getAttribute('readonly')!==null);await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(new URL('first.zip',work).pathname);
    await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();waiting=watch(page.waitForResponse(r=>r.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(r.url()).pathname)));
    await dialog.getByRole('button',{name:'Confirmer la réimportation',exact:true}).click();
    const result=await publicationFollow(await observed(waiting));
    assert(result.version_restored&&!result.code_changed);assert.equal(result.code_hash,hash);
    await dialog.waitFor({state:'hidden'});await ready();await card(hash).getByText('Disponible',{exact:true}).waitFor();assert.equal((await api(`/api/functions/${fn.id}`)).active_revision_id,null);
    await promoteInUi(hash);await fits();await capture('reimported-mobile');
  });
  await check('Publication externe : dialog conservé hors page et catalogue terminal cohérent',async()=>{
    await page.setViewportSize({width:1440,height:1000});
    for(let index=1;index<=4;index++){
      await writeFile(new URL('revision.json',work),JSON.stringify({name:'extra-'+index}));const file=await archiveZip('extra-'+index+'.zip',['handler.cjs','revision.json']);
      const prepared=await prepareExternal(file);assert.equal((await prepared.send()).state,'published');
    }
    const previous=await api(`/api/functions/${fn.id}`),catalogue=await api(`/api/functions/${fn.id}/versions?limit=100`);assert.equal(catalogue.total,5);
    const replacement=catalogue.items.find(row=>row.code_hash!==hash&&row.state==='available').code_hash;
    await cp(new URL('../qualification/artifacts/function-version-pilot-delay.mjs',import.meta.url),new URL('pilot-delay.mjs',work));const file=await archiveZip('external-pilot.zip',['pilot-delay.mjs']);
    const external=await prepareExternal(file,'pilot-delay.handler'),uploading=watch(external.send());
    await until(async()=>{const row=await api(`/api/deployments/${external.candidate.id}`);assert.notEqual(row.state,'failed');return row.state==='validating';});
    const ordering=[];let candidateRead=false;
    function observe(request){if(request.method()!=='GET')return;const path=new URL(request.url()).pathname;
      if(path===`/api/deployments/${external.candidate.id}`)candidateRead=true;
      if(path===`/api/functions/${fn.id}/versions`){ordering.push({candidate_before_catalogue:candidateRead});candidateRead=false;}}
    page.on('request',observe);
    try{
      await page.goto(base+`/console/functions/${fn.id}/code?deployment=${external.candidate.id}`);await ready();
      await card(hash).getByRole('button',{name:'Archiver cette version',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Archiver la version courante',exact:true});
      await dialog.getByLabel('Cible après retrait',{exact:true}).selectOption('replacement');await dialog.getByLabel('Hash de remplacement',{exact:true}).fill(replacement);
      const published=await observed(uploading);assert.equal(published.state,'published');assert.equal((await api(`/api/functions/${fn.id}`)).updated_at,previous.updated_at);
      await until(async()=>await card(hash).count()===0);assert.equal((await api(`/api/functions/${fn.id}/versions`)).total,6);
      assert(await dialog.isVisible());assert.equal(await dialog.getByLabel('Hash de remplacement',{exact:true}).inputValue(),replacement);assert(ordering.length>0&&ordering.every(row=>row.candidate_before_catalogue));
      await fits();await capture('dialog-card-left-page-desktop',false);await page.keyboard.press('Escape');await dialog.getByRole('button',{name:'Abandonner',exact:true}).click();await dialog.waitFor({state:'hidden'});
      assert.equal(await page.evaluate(()=>document.activeElement?.id),'revisions-heading');assert(await page.evaluate(()=>!document.body.classList.contains('dialog-open')));
      await page.setViewportSize({width:390,height:844});const pages=page.getByRole('navigation',{name:'Pagination des versions',exact:true});await pages.getByRole('button',{name:'Suivante',exact:true}).click();await ready();await card(hash).waitFor();
      await fits();await capture('versions-second-page-mobile');evidence.push({external_deployment_id:external.candidate.id,published_code_hash:published.code_hash,catalogue_read_order:ordering,dialog_preserved:true});
    }finally{page.off('request',observe);}
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
assert(completed&&cleanup&&faults.length===0,'ui_campaign_must_finish_without_pageerror');
