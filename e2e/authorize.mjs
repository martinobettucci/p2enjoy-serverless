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
let timer;
try {
  const authenticated = new Promise((resolve,reject) => {
    timer=setTimeout(() => reject(new Error('Connexion administrateur non effectuée.')),8*60*60*1000);
    page.on('close',() => reject(new Error('Fenêtre de connexion fermée.')));
    page.on('response',async response => {
      if (response.url()!==base+'/api/session' || !response.ok()) return;
      try {if ((await response.json()).authenticated) resolve();} catch {}
    });
  });
  await page.goto(base);
  await page.getByRole('link',{name:'Se connecter avec le SSO'}).waitFor();
  console.log('AUTHORIZATION_WINDOW_READY — cliquer sur Se connecter avec le SSO dans Chromium.');
  await authenticated;
  const state = await context.storageState();
  state.cookies = state.cookies.filter(cookie => cookie.domain==='serverless-dev.lelabs.tech');
  state.origins = [];
  await writeFile(output,JSON.stringify(state),{mode:0o600});
  await chmod(output,0o600);
  console.log('AUTHENTICATED — session de plateforme sauvegardée localement pour la qualification.');
} finally {
  clearTimeout(timer);
  await browser.close();
}
