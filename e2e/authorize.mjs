// @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/CONTROL.md#preuves
// Opens the normal login for the account owner. Never reads password fields.
import {mkdir,writeFile,chmod} from 'node:fs/promises';
import {chromium} from 'playwright';

const base = 'https://serverless-dev.lelabs.tech';
const output = new URL('../.local/e2e/admin-session.json',import.meta.url);
await mkdir(new URL('../.local/e2e/',import.meta.url),{recursive:true,mode:0o700});
const browser = await chromium.launch({headless:false});
const context = await browser.newContext({viewport:{width:1280,height:900},locale:'fr-FR'});
const page = await context.newPage();
try {
  await page.goto(base);
  await page.getByRole('link',{name:'Se connecter avec le SSO'}).click();
  await page.waitForURL(value => value.hostname === 'oauth.lelabs.tech');
  console.log('AUTHORIZATION_WINDOW_READY — connexion SSO attendue dans Chromium.');
  const deadline = Date.now()+30*60*1000;
  let authenticated = false;
  while (Date.now()<deadline && !page.isClosed()) {
    if (new URL(page.url()).origin===base) {
      const session = await page.evaluate(async () => {
        const response = await fetch('/api/session',{credentials:'same-origin'});
        return response.ok ? response.json() : {authenticated:false};
      });
      if (session.authenticated) {authenticated=true;break;}
    }
    await new Promise(resolve => setTimeout(resolve,2000));
  }
  if (!authenticated) throw new Error('Connexion administrateur non effectuée ; aucune session de remplacement.');
  const state = await context.storageState();
  state.cookies = state.cookies.filter(cookie => cookie.domain==='serverless-dev.lelabs.tech');
  state.origins = [];
  await writeFile(output,JSON.stringify(state),{mode:0o600});
  await chmod(output,0o600);
  console.log('AUTHENTICATED — session de plateforme sauvegardée localement pour la qualification.');
} finally {
  await browser.close();
}
