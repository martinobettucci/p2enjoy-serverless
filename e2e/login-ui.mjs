// @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/DESIGN_SYSTEM_APP.md
// Real browser, real deployed console, real SSO. No interception or fixture API.
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium,request} from 'playwright';

const base = 'https://serverless.lelabs.tech';
const directory = new URL('../.local/e2e/',import.meta.url).pathname;
await mkdir(directory,{recursive:true,mode:0o700});
await writeFile(directory+'login-ui.json',JSON.stringify({completed:false,error:'Campagne non terminée'})+'\n');
const browser = await chromium.launch({headless:true});
const checks = [], failures = [];
const pending = [];
let completed = false;
const context = await browser.newContext({viewport:{width:1440,height:1000},locale:'fr-FR'});
const page = await context.newPage();
page.on('pageerror',error => failures.push(error.name));
try {
  await page.goto(base);
  const login = page.getByRole('link',{name:'Se connecter avec le SSO'});
  await login.waitFor();
  assert.equal(await page.getByRole('navigation').count(),0);
  assert.equal(await page.getByRole('heading',{level:1}).textContent(),'Votre console serverless');
  await page.keyboard.press('Tab');
  assert(await login.evaluate(element => document.activeElement === element));
  checks.push('Accueil anonyme et navigation clavier');
  for (const [name,width,height] of [['desktop',1440,1000],['tablette',820,1180],['mobile',390,844]]) {
    await page.setViewportSize({width,height});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert((await login.boundingBox()).height >= 40);
    await page.screenshot({path:directory+`login-${name}.png`,fullPage:true});
    checks.push(`Accueil ${name} sans débordement, cible 40 px`);
  }
  const contrast = await login.evaluate(element => {
    const css = getComputedStyle(element);
    const luminance = color => color.match(/[\d.]+/g).slice(0,3).map(Number).map(v => v/255)
      .map(v => v <= .04045 ? v/12.92 : ((v+.055)/1.055)**2.4).reduce((s,v,i) => s + v*[.2126,.7152,.0722][i],0);
    const a = luminance(css.color), b = luminance(css.backgroundColor);
    return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  });
  assert(contrast >= 4.5);
  checks.push(`Contraste de connexion mesuré : ${contrast.toFixed(2)}:1`);
  await page.goto(base+'/auth/retour?state=%C3%A9');
  await page.getByRole('alert').waitFor();
  assert(await page.getByRole('alert').textContent());
  assert(!page.url().includes('state'));
  await page.screenshot({path:directory+'login-error.png',fullPage:true});
  checks.push('Refus de callback visible depuis le vrai serveur');
  await page.getByRole('link',{name:'Se connecter avec le SSO'}).click();
  await page.waitForURL(value => value.hostname === 'oauth.lelabs.tech');
  await page.waitForLoadState('domcontentloaded');
  assert.equal(new URL(page.url()).protocol,'https:');
  await page.screenshot({path:directory+'sso-entry.png',fullPage:true});
  checks.push('Entrée normale vers le vrai SSO en HTTPS');
  const currentState = new URL(page.url()).searchParams.get('state');
  assert(currentState);
  assert.equal((await context.request.get(base+'/auth/retour?state='+currentState+'&error=access_denied',
    {headers:{Accept:'application/json'},maxRedirects:0})).status(),401);
  let limited = false;
  for (let index=0;index<9;index++) {
    const client = await request.newContext({baseURL:base});
    const response = await client.get('/auth/login',{headers:{Accept:'application/json'},maxRedirects:0});
    if (response.status()===429) {limited=true;await client.dispose();break;}
    assert.equal(response.status(),303);
    const state = new URL(response.headers().location).searchParams.get('state');
    pending.push({client,state});
  }
  assert(limited);
  const refusal = await page.goto(base+'/auth/login');
  assert.equal(refusal.status(),429);
  assert.equal(refusal.headers()['retry-after'],'60');
  assert(!refusal.headers()['set-cookie']);
  await page.getByRole('alert').waitFor();
  assert.match(await page.getByRole('alert').textContent(),/Trop de/);
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({path:directory+'login-limit.png',fullPage:true});
  checks.push('Refus 429 visible sur mobile, Retry-After conservé et aucun flow créé');
  assert.deepEqual(failures,[]);
  checks.push('Aucune erreur JavaScript de page');
  completed=true;
  console.log(JSON.stringify({passed:checks.length,checks,skipped:0},null,2));
} catch (error) {
  failures.push(error.name);
  throw error;
} finally {
  for (const {client,state} of pending) {
    try {assert.equal((await client.get('/auth/retour?state='+state+'&error=access_denied',
      {headers:{Accept:'application/json'},maxRedirects:0})).status(),401);}
    catch (error) {failures.push('Nettoyage : '+error.name);}
    finally {await client.dispose();}
  }
  await browser.close();
  await writeFile(directory+'login-ui.json',JSON.stringify({target:base,completed:completed && !failures.length,checks,failures,skipped:0},null,2)+'\n');
  assert.deepEqual(failures,[]);
}
