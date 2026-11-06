// @spec docs/BACKLOG.md#sls-062 | docs/CONSOLE_MANUAL.md | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-062 | docs/CONSOLE_MANUAL.md#preuves-attendues
import assert from 'node:assert/strict';
import {readFile,writeFile,rename,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright';

const base = 'https://serverless.lelabs.tech', output = new URL('../.local/e2e/',import.meta.url);
const checks = [], faults = [], captures = {}, report = new URL('manual-ui.json',output);
let browser, context, page, state, completed = false, sourceSha, paragraphsChecked = 0;
const normalize = value => value.replace(/\s+/g,' ').trim();
async function save() {
  const temporary = new URL('manual-ui.pending',output);
  await writeFile(temporary,JSON.stringify({target:base,completed,skipped:0,checks,faults,captures,source_sha256:sourceSha,paragraphs_checked:paragraphsChecked},null,2)+'\n',{mode:0o600});
  await rename(temporary,report);
}
async function check(name,action) {
  try {await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}
  catch(error) {checks.push({name,status:'failed',error:error.name});await save();throw error;}
}
async function capture(name) {
  const path = new URL('manual-'+name+'.jpg',output);
  await page.screenshot({path:path.pathname,type:'jpeg',quality:85});
  captures[path.pathname.split('/').at(-1)] = createHash('sha256').update(await readFile(path)).digest('hex');
}
async function fits() {assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));}
async function chapter(name) {
  const link = page.getByRole('navigation',{name:'Sommaire',exact:true}).getByRole('link',{name,exact:true});
  const hash = await link.getAttribute('href');
  await link.click();
  await page.waitForFunction(hash => location.hash === hash && document.activeElement?.id === hash.slice(1),hash);
  assert(await page.getByRole('heading',{name,exact:true}).isVisible());
  return hash;
}

await mkdir(output,{recursive:true,mode:0o700});await save();
try {
  const source = await readFile(new URL('../docs/manual.md',import.meta.url),'utf8');
  sourceSha = createHash('sha256').update(source).digest('hex');
  const headings = [...source.matchAll(/^## (.+)$/gm)].map(match => match[1]);
  state = JSON.parse(await readFile(new URL('admin-session.json',output),'utf8'));
  browser = await chromium.launch({headless:true});
  context = await browser.newContext({storageState:state,viewport:{width:1440,height:1000},locale:'fr-FR'});
  page = await context.newPage();page.on('pageerror',error => faults.push(error.name));
  await check('Accueil réel et accès au manuel par le clavier',async () => {
    await page.goto(base);
    await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    const link = page.getByRole('link',{name:'Manuel d’usage',exact:true});
    await link.focus();await page.keyboard.press('Enter');
    await page.waitForURL(base+'/console/manual');
    await page.getByRole('heading',{name:'Manuel d’usage',exact:true}).waitFor();
    assert.equal(await link.getAttribute('aria-current'),'page');
    assert.equal(await page.getByRole('link',{name:'Namespaces',exact:true}).getAttribute('aria-current'),null);
  });
  await check('Source unique : empreinte, chapitres, paragraphes, tableau et commande',async () => {
    const article = page.getByRole('article',{name:'Guide d’utilisation'});
    assert.equal(await article.getAttribute('data-manual-sha256'),sourceSha);
    assert.deepEqual(await article.locator('h2').allTextContents(),headings);
    const visibleText = normalize(await article.innerText());
    for (const block of source.split(/\n\s*\n/)) {
      if (block.startsWith('#') || block.startsWith('|') || !block.trim()) continue;
      const text = normalize(block.replace(/\[([^\]]+)\]\([^\)]+\)/g,'$1').replace(/\*\*|`/g,''));
      assert(visibleText.includes(text),'Un paragraphe du manuel manque dans le rendu');paragraphsChecked++;
    }
    assert(paragraphsChecked > 20);
    assert.equal(await article.getByRole('row').count(),5);
    const expectedRows = source.split('\n').filter(line => line.startsWith('|') && !line.includes('---')).map(line => line.split('|').slice(1,-1).map(cell => cell.trim()));
    assert.deepEqual(await article.locator('tr').evaluateAll(rows => rows.map(row => [...row.children].map(cell => cell.textContent.trim()))),expectedRows);
    assert(await article.locator('code').filter({hasText:'python3 -m adapter deploy --config serverless.yml --service UUID_DU_SERVICE'}).isVisible());
    for (const href of await article.locator('a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')))) assert(href.startsWith('https://') || href.startsWith('#'));
  });
  await check('Tous les chapitres, focus et ancre conservée après rechargement',async () => {
    let hash;
    for (const heading of headings) hash = await chapter(heading);
    await page.reload();
    await page.getByRole('heading',{name:headings.at(-1),exact:true}).waitFor();
    await page.waitForFunction(hash => document.activeElement?.id === hash.slice(1),hash);
    assert.equal(new URL(page.url()).hash,hash);
    await page.getByRole('link',{name:'Revenir au sommaire',exact:true}).click();
    await page.waitForFunction(() => document.activeElement?.id === 'sommaire');
  });
  await check('Lecture desktop et tableau lisible',async () => {
    await page.getByRole('link',{name:'Manuel d’usage',exact:true}).click();
    await page.waitForURL(base+'/console/manual');
    await page.getByRole('heading',{name:'Manuel d’usage',exact:true}).waitFor();
    assert.equal(await page.evaluate(() => scrollY),0);await fits();await capture('desktop');
    await chapter('Donner un accès à un service');await fits();await capture('rights-desktop');
  });
  await check('Menu mobile, guide à 390 px, tableau et commande longue',async () => {
    await page.getByRole('link',{name:'Namespaces',exact:true}).click();
    await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    await page.setViewportSize({width:390,height:844});
    await page.getByRole('button',{name:'Menu',exact:true}).click();
    await page.getByRole('link',{name:'Manuel d’usage',exact:true}).click();
    await page.getByRole('heading',{name:'Manuel d’usage',exact:true}).waitFor();
    assert(await page.evaluate(() => !document.querySelector('.shell').inert && getComputedStyle(document.body).overflow !== 'hidden'));
    await fits();await capture('mobile');
    await chapter('Donner un accès à un service');await fits();await capture('rights-mobile');
    await chapter('Publier le code avec l’adaptateur');await fits();await capture('command-mobile');
  });
  await check('Tablette et agrandissement mesuré du corps de texte à 200 pour cent',async () => {
    await page.setViewportSize({width:820,height:1180});
    await page.getByRole('button',{name:'Menu',exact:true}).click();
    await page.getByRole('link',{name:'Manuel d’usage',exact:true}).click();
    await page.waitForURL(base+'/console/manual');
    await page.getByRole('heading',{name:'Manuel d’usage',exact:true}).waitFor();
    assert.equal(await page.evaluate(() => scrollY),0);await fits();await capture('tablet');
    await page.setViewportSize({width:390,height:844});
    const normalSize = await page.locator('.manual-content p').first().evaluate(element => parseFloat(getComputedStyle(element).fontSize));
    await page.evaluate(() => document.documentElement.style.fontSize = '30px');
    // Actual browser text layout, with the original document and no response substitution.
    assert.equal(await page.locator('.manual-content p').first().evaluate(element => parseFloat(getComputedStyle(element).fontSize)),normalSize * 2);
    await chapter('Publier le code avec l’adaptateur');await fits();await capture('large-text');
    await page.evaluate(() => document.documentElement.style.removeProperty('font-size'));
  });
  await check('Session retirée : retour à la connexion puis reprise avec la session réelle',async () => {
    await context.clearCookies();await page.reload();
    await page.getByRole('link',{name:'Se connecter avec le SSO'}).waitFor();
    assert.equal(await page.getByRole('article').count(),0);
    assert.equal(await page.getByRole('link',{name:'Manuel d’usage',exact:true}).count(),0);
    await context.addCookies(state.cookies);await page.reload();
    await page.getByRole('heading',{name:'Manuel d’usage',exact:true}).waitFor();
  });
  await check('Retour à la gestion et absence d’erreur JavaScript',async () => {
    await page.setViewportSize({width:1440,height:1000});
    await page.getByRole('link',{name:'Namespaces',exact:true}).click();
    await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    assert.equal(await page.getByRole('link',{name:'Namespaces',exact:true}).getAttribute('aria-current'),'page');
    assert.equal(await page.getByRole('link',{name:'Manuel d’usage',exact:true}).getAttribute('aria-current'),null);
    assert.deepEqual(faults,[]);
    assert.equal(await page.evaluate(() => localStorage.length + sessionStorage.length),0);
  });
  completed = true;
} finally {
  await browser?.close();
  completed = completed && faults.length === 0;
  await save();assert.deepEqual(faults,[]);
}
