// @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves | docs/DESIGN_SYSTEM_APP.md
// Canonical UI paths on the real deployment using a real SSO admin session.
import {purgeStorageArchive} from './storage-archives.mjs';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {chromium} from 'playwright';

const base='https://serverless.lelabs.tech';
const output=new URL('../.local/e2e/',import.meta.url);
await mkdir(output,{recursive:true,mode:0o700});
await writeFile(new URL('control-ui.json',output),JSON.stringify({completed:false,error:'Campagne non terminée'})+'\n');
const state=JSON.parse(await readFile(new URL('admin-session.json',output),'utf8'));
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});
const page=await context.newPage();
const faults=[],checks=[],cleanupErrors=[],storageArchives=[];
page.on('pageerror',error => faults.push(error.name));
const prefix=`ui-${randomUUID().slice(0,8)}`;
const namespaceName=(prefix+'x'.repeat(63)).slice(0,63);
let namespaceId,serviceId,functionId,completed=false;
const dialog=page.getByRole('dialog');
async function check(name,run) {try {await run();checks.push({name,status:'passed'});console.log('PASS',name);} catch (error) {checks.push({name,status:'failed',error:error.name});throw error;}}
async function gone() {await dialog.waitFor({state:'hidden'});}
async function screenshot(name) {await page.screenshot({path:new URL(name+'.jpg',output).pathname,type:'jpeg',quality:85,fullPage:true});}
async function api(path,method='GET',body,headers={}) {
  const session=await (await context.request.get(base+'/api/session')).json();
  assert(session.authenticated,'Session administrateur réelle requise.');
  const response=await context.request.fetch(base+path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});
  assert(response.ok(),`${method} ${path} refusé à ${response.status()}`);return response.json();
}

try {
  await check('Accueil authentifié depuis l’entrée normale',async () => {
    await page.goto(base);
    await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    assert(await page.getByRole('button',{name:'Se déconnecter',exact:true}).isVisible());
    await screenshot('console-namespaces');
  });
  await check('Modale : focus, annulation des changements et retour au déclencheur',async () => {
    const button=page.getByRole('button',{name:'Créer un namespace',exact:true});
    await button.click();
    const field=dialog.getByLabel('Nom',{exact:true});
    assert(await field.evaluate(element => document.activeElement===element));
    await field.fill('a-abandonner');
    await page.keyboard.press('Escape');
    await dialog.getByRole('button',{name:'Continuer la saisie'}).click();
    assert.equal(await field.inputValue(),'a-abandonner');
    assert(await field.evaluate(element => document.activeElement===element));
    await page.keyboard.press('Escape');
    await dialog.getByRole('button',{name:'Abandonner',exact:true}).click();await gone();
    assert(await button.evaluate(element => document.activeElement===element));
  });
  await check('Namespace : création avec nom long et description rendue comme texte',async () => {
    await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();
    await dialog.getByLabel('Nom',{exact:true}).fill(namespaceName);
    await dialog.getByLabel('Description',{exact:true}).fill('<script>texte de qualification</script>');
    await dialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.waitForURL(/\/console\/namespaces\//);namespaceId=new URL(page.url()).pathname.split('/').at(-1);
    await page.getByRole('heading',{name:namespaceName,exact:true}).waitFor();
    assert(await page.getByText('<script>texte de qualification</script>',{exact:true}).isVisible());
    assert.equal(await page.locator('script').filter({hasText:'texte de qualification'}).count(),0);
  });
  await check('Responsive : nom long, tiroir, clavier et retour au desktop',async () => {
    await page.setViewportSize({width:390,height:844});
    await screenshot('namespace-mobile-long');
    assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth));
    for (const gesture of ['escape','button','backdrop']) {
      await page.getByRole('button',{name:'Menu',exact:true}).click();
      assert(await page.getByRole('button',{name:'Fermer le menu',exact:true}).evaluate(element => document.activeElement===element));
      assert(await page.evaluate(() => document.querySelector('.shell').inert && getComputedStyle(document.body).overflow==='hidden'));
      if (gesture==='escape') await page.keyboard.press('Escape');
      else if (gesture==='button') await page.getByRole('button',{name:'Fermer le menu',exact:true}).click();
      else await page.locator('.nav-veil').click({position:{x:380,y:400}});
      assert(await page.getByRole('button',{name:'Menu',exact:true}).evaluate(element => document.activeElement===element));
      assert(await page.evaluate(() => !document.querySelector('.shell').inert && getComputedStyle(document.body).overflow!=='hidden'));
    }
    await page.getByRole('button',{name:'Menu',exact:true}).click();
    await page.setViewportSize({width:1440,height:1000});
    await page.waitForFunction(() => !document.querySelector('.shell').inert && getComputedStyle(document.body).overflow!=='hidden');
    assert(await page.getByRole('link',{name:'Namespaces',exact:true}).first().evaluate(element => document.activeElement===element));
    await page.getByRole('button',{name:'Modifier le namespace',exact:true}).click();
    await dialog.getByRole('button',{name:'Annuler',exact:true}).click();await gone();
  });
  await check('Service : création et navigation par onglets partageables',async () => {
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();
    await dialog.getByLabel('Nom',{exact:true}).fill(prefix+'-service');
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await page.waitForURL(/\/console\/services\//);serviceId=new URL(page.url()).pathname.split('/')[3];
    await page.getByRole('heading',{name:prefix+'-service',exact:true}).waitFor();
    await page.getByRole('link',{name:'Configuration',exact:true}).click();
    await page.getByRole('heading',{name:'Variables',exact:true}).waitFor();
    assert.equal(new URL(page.url()).pathname,`/console/services/${serviceId}/configuration`);
  });
  await check('Variables : enregistrement réel et champs protégés durant l’envoi',async () => {
    await page.getByRole('button',{name:'Modifier les variables',exact:true}).click();
    await dialog.getByRole('button',{name:'Ajouter une ligne',exact:true}).click();
    await dialog.getByLabel('Nom 1',{exact:true}).fill('UI_LABEL');
    await dialog.getByLabel('Valeur 1',{exact:true}).fill('valeur réelle');
    const cdp=await context.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:800,downloadThroughput:1000000,uploadThroughput:1000000});
    try {await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
      assert(await dialog.getByLabel('Valeur 1',{exact:true}).isDisabled());await gone();}
    finally {await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.detach();}
    assert.equal((await api(`/api/services/${serviceId}`)).environment.UI_LABEL,'valeur réelle');
  });
  await check('Secret : saisie masquée, lecture expurgée et suppression confirmée',async () => {
    const secret='ui-secret-'+randomUUID();
    await page.getByRole('button',{name:'Ajouter ou remplacer des secrets',exact:true}).click();
    await dialog.getByLabel('Nom 1',{exact:true}).fill('UI_SECRET');
    const field=dialog.getByLabel('Valeur 1',{exact:true});assert.equal(await field.getAttribute('type'),'password');
    await field.fill(secret);await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await gone();
    await page.getByText('UI_SECRET',{exact:true}).waitFor();
    assert(!(await page.locator('body').innerText()).includes(secret));
    assert(!(JSON.stringify(await api(`/api/services/${serviceId}`))).includes(secret));
    await page.getByRole('button',{name:'Retirer UI_SECRET',exact:true}).click();
    await page.getByRole('button',{name:'Retirer UI_SECRET',exact:true}).last().click();
    await page.getByText('Aucun secret à ce niveau.',{exact:true}).waitFor();
  });
  await check('Politique réseau : sauvegarde et refus d’une édition obsolète',async () => {
    await page.getByRole('button',{name:'Modifier la politique',exact:true}).click();
    await dialog.getByLabel('Origines autorisées',{exact:true}).fill('https://ui.example.com');
    await dialog.getByLabel('Adresses IP ou réseaux CIDR',{exact:true}).fill('192.0.2.0/24');
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await gone();
    await page.getByRole('button',{name:'Modifier le service',exact:true}).click();
    await dialog.getByLabel('Description',{exact:true}).fill('Saisie conservée après conflit');
    const current=await api(`/api/services/${serviceId}`);
    await api(`/api/services/${serviceId}`,'PUT',{name:current.name,description:current.description,policy:{origins:['https://newer.example.com']}},{'If-Match':String(current.updated_at)});
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
    await dialog.getByRole('alert').waitFor();
    assert.equal(await dialog.getByLabel('Description',{exact:true}).inputValue(),'Saisie conservée après conflit');
    assert.deepEqual((await api(`/api/services/${serviceId}`)).policy.origins,['https://newer.example.com']);
    await screenshot('configuration-conflict');
    await dialog.getByRole('button',{name:'Annuler',exact:true}).click();await dialog.getByRole('button',{name:'Abandonner',exact:true}).click();await gone();
  });
  await check('Fonction : création, paramètres précis et stockage',async () => {
    await page.getByRole('link',{name:'Fonctions',exact:true}).click();
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();
    await dialog.getByLabel('Nom',{exact:true}).fill(prefix+'-Handler');
    await dialog.getByLabel('Handler',{exact:true}).fill('src/handlers.echo');
    await dialog.getByRole('button',{name:'Créer',exact:true}).click();
    await page.waitForURL(/\/console\/functions\//);functionId=new URL(page.url()).pathname.split('/').at(-1);
    await page.getByRole('button',{name:'Modifier l’exécution',exact:true}).click();
    await dialog.getByLabel('Plafond CPU',{exact:true}).fill('0.123');
    await dialog.getByLabel('Durée maximale d’invocation (s)',{exact:true}).fill('4.321');
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await gone();
    const current=await api(`/api/functions/${functionId}`);assert.equal(current.config.cpu,.123);assert.equal(current.config.timeout_seconds,4.321);
    await page.getByRole('button',{name:'Modifier le stockage',exact:true}).click();
    const data=dialog.getByRole('group',{name:'Données permanentes',exact:true});
    await data.getByLabel('Activer',{exact:true}).check();await data.getByLabel('Allocation (Mio)',{exact:true}).fill('8');
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await gone();
    assert.equal((await api(`/api/functions/${functionId}`)).config.storage.data.quota_mib,8);
    await screenshot('function-desktop');
    await page.setViewportSize({width:390,height:844});assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth));await screenshot('function-mobile');
    await page.setViewportSize({width:1440,height:1000});
  });
  await check('Jetons : confirmation, valeurs uniques conservées et révocation',async () => {
    await page.getByRole('link',{name:'Fonctions du service',exact:true}).click();
    await page.getByRole('link',{name:'Jetons',exact:true}).click();
    const names=[prefix+'-read-a',prefix+'-read-b'];
    let firstValue;
    for (const name of names) {
      await page.getByRole('button',{name:'Créer un jeton',exact:true}).click();
      await dialog.getByLabel('Nom du jeton',{exact:true}).fill(name);
      await dialog.getByRole('button',{name:'Créer le jeton',exact:true}).click();
      await dialog.getByRole('button',{name:'Confirmer la création',exact:true}).click();await gone();
      const value=await page.getByLabel(`Valeur de ${name}`,{exact:true}).inputValue();assert.match(value,/^p2s_/);
      if (!firstValue) firstValue=value;
    }
    assert.equal(await page.getByLabel(`Valeur de ${names[0]}`,{exact:true}).inputValue(),firstValue);
    assert.equal(await page.evaluate(() => localStorage.length+sessionStorage.length),0);
    for (const name of names) {
      const section=page.locator('section').filter({has:page.getByRole('heading',{name:`Jeton « ${name} »`,exact:true})});
      await section.getByRole('button',{name:'Fermer la valeur',exact:true}).click();
    }
    const row=page.locator('li').filter({has:page.getByRole('heading',{name:names[0],exact:true})});
    await row.getByRole('button',{name:'Révoquer',exact:true}).click();
    assert(await row.getByRole('button',{name:'Révoquer',exact:true}).last().isDisabled());
    await row.getByLabel(`Saisir « ${names[0]} » pour confirmer`,{exact:true}).fill(names[0]);
    await row.getByRole('button',{name:'Révoquer',exact:true}).last().click();
    await row.getByText('Révoqué',{exact:true}).waitFor();await screenshot('tokens-desktop');
  });
  await check('Activité réelle et absence d’erreurs JavaScript',async () => {
    await page.getByRole('link',{name:'Activité',exact:true}).click();
    await page.getByRole('heading',{name:'Activité du service',exact:true}).waitFor();
    await page.getByText('token.revoke',{exact:true}).waitFor();assert.deepEqual(faults,[]);await screenshot('activity-desktop');
  });
  completed=true;
} finally {
  for (const [kind,id] of [['functions',functionId],['services',serviceId],['namespaces',namespaceId]]) {
    if (id) {try {await api(`/api/${kind}/${id}`,'DELETE');if(kind==='functions')storageArchives.push(await purgeStorageArchive(id,namespaceId));} catch {cleanupErrors.push(`${kind}:${id}`);}}
  }
  await browser.close();
  await writeFile(new URL('control-ui.json',output),JSON.stringify({target:base,completed:completed && !cleanupErrors.length && !faults.length,checks,faults,cleanupErrors,skipped:0,storage_archives:storageArchives,namespace_id:namespaceId,function_id:functionId},null,2)+'\n');
  assert.deepEqual(cleanupErrors,[],'Nettoyage des objets créés par le parcours UI.');
}
