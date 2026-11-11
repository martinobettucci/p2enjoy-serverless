// @spec docs/BACKLOG.md#sls-100 | docs/DESIGN_SYSTEM_APP.md#serverless-identity | docs/DESIGN_SYSTEM.md#13-preuves-ui-et-validation
// @verifies docs/BACKLOG.md#sls-100 | docs/DESIGN_SYSTEM_APP.md#serverless-identity
// Actual home, SSO, console, navigation and served SVG. No intercepted response.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,readFile,writeFile,rename} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {chromium} from 'playwright';

const base='https://serverless.lelabs.tech',campaign=randomUUID();
const out=new URL('../.local/e2e/',import.meta.url),prefix='application-icon-'+campaign;
const report=new URL(prefix+'.json',out),checks=[],captures=[],observations=[],pageErrors=[];
const digest=value=>createHash('sha256').update(value).digest('hex');
let browser,credentials,completed=false,failure=null,phase='private-input';
async function save(){
  const pending=new URL(prefix+'.pending',out);
  await writeFile(pending,JSON.stringify({campaign,target:base,completed,phase,checks,captures,observations,page_errors:pageErrors,failure,skipped:0},null,2)+'\n',{mode:0o600});
  await rename(pending,report);
}
async function privateInput(){
  assert(!process.stdin.isTTY,'private_pipe_required');
  const input=createInterface({input:process.stdin});
  try{
    const line=await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));});
    assert(line.length<=8192);const value=JSON.parse(line);
    assert(typeof value.username==='string'&&value.username&&typeof value.password==='string'&&value.password);
    return value;
  }finally{input.close();}
}
async function check(name,action){
  phase=name;await save();
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error_type:error.name,message_sha256:digest(String(error.message))});throw error;}
  finally{await save();}
}
async function capture(page,label){
  const path=new URL(prefix+'-'+label+'.jpg',out);
  await page.screenshot({path:path.pathname,type:'jpeg',quality:90,fullPage:false});
  const bytes=await readFile(path);captures.push({path:path.pathname,sha256:digest(bytes),bytes:bytes.length,viewport:page.viewportSize()});
}
async function brand(page,expected){
  const image=page.locator('.brand img');await image.waitFor({state:'visible'});
  await page.waitForFunction(()=>{const image=document.querySelector('.brand img');return image?.complete&&image.naturalWidth>0&&image.naturalHeight>0;});
  assert.equal(await image.getAttribute('alt'),'');
  assert.match(await page.locator('.brand').innerText(),/P2Enjoy\s+Serverless/);
  const source=await image.getAttribute('src'),icon=await page.locator('link[rel="icon"]').getAttribute('href');
  assert.equal(source,'/favicon.svg');assert.equal(icon,source);
  const response=await page.request.get(new URL(icon,base).href);
  assert.equal(response.status(),200);assert.match(response.headers()['content-type'],/^image\/svg\+xml/);
  assert.equal(response.headers()['cache-control'],'no-store');
  const bytes=await response.body();assert.equal(digest(bytes),expected);
  const box=await image.boundingBox();assert(box.width>0&&box.height>0&&box.x>=0&&box.x+box.width<=page.viewportSize().width);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  observations.push({scenario:phase,path:new URL(page.url()).pathname,icon_sha256:digest(bytes),cache_control:'no-store',box});
}
async function signIn(page){
  const login=page.getByRole('link',{name:'Se connecter avec le SSO',exact:true});
  await page.keyboard.press('Tab');assert(await login.evaluate(node=>node===document.activeElement));await page.keyboard.press('Enter');
  await page.waitForURL('https://oauth.lelabs.tech/**');
  await page.locator('input[name="username"]').fill(credentials.username);
  await page.locator('input[type="password"]').fill(credentials.password);
  await page.locator('input[type="submit"],button[type="submit"]').first().click();
  await page.waitForURL(base+'/**',{timeout:90000});
  await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
}
async function openMenu(page){
  const menu=page.getByRole('button',{name:'Menu',exact:true});await menu.click();
  const close=page.getByRole('button',{name:'Fermer le menu',exact:true});
  await close.waitFor();assert(await close.evaluate(node=>node===document.activeElement));
  assert(await page.locator('.shell').evaluate(node=>node.inert));
}
async function signOut(page,mobile){
  if(mobile)await openMenu(page);
  await page.getByRole('button',{name:'Se déconnecter',exact:true}).click();
  await page.locator('.confirmation .confirm').getByRole('button',{name:'Se déconnecter',exact:true}).click();
  await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).waitFor();
  assert.equal(new URL(page.url()).pathname,'/');
}
async function main(){
  await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();
  const expected=digest(await readFile(new URL('../web/public/favicon.svg',import.meta.url)));
  browser=await chromium.launch({headless:true});
  try{
    for(const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
      const context=await browser.newContext({viewport:{width,height},locale:'fr-FR'}),page=await context.newPage();
      page.on('pageerror',error=>pageErrors.push({type:error.name,message_sha256:digest(String(error.message))}));
      try{
        await check('Accueil '+label+' : marque et favicon réels',async()=>{
          await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).waitFor();
          assert.equal(await page.getByRole('navigation').count(),0);await brand(page,expected);await capture(page,label+'-home');
        });
        await check('SSO et navigation '+label+' avec la nouvelle marque',async()=>{
          await signIn(page);const mobile=label==='mobile';if(mobile)await openMenu(page);
          await brand(page,expected);await capture(page,label+'-console');
          if(mobile){await page.keyboard.press('Escape');assert(await page.getByRole('button',{name:'Menu',exact:true}).evaluate(node=>node===document.activeElement));await openMenu(page);}
          const manual=page.getByRole('link',{name:'Manuel d’usage',exact:true});await manual.focus();await page.keyboard.press('Enter');
          await page.getByRole('heading',{name:'Manuel d’usage',exact:true}).waitFor();
          if(mobile){await openMenu(page);await brand(page,expected);await page.keyboard.press('Escape');}else await brand(page,expected);
          await signOut(page,mobile);await brand(page,expected);
        });
      }finally{await context.close();}
    }
    assert.deepEqual(pageErrors,[]);completed=true;phase='completed';
  }finally{credentials=null;await browser?.close();await save();}
  console.log(JSON.stringify({completed,groups:checks.length,report:report.pathname,captures:captures.length}));
}
main().catch(async error=>{
  credentials=null;completed=false;failure={type:error.name,message_sha256:digest(String(error.message))};
  await browser?.close().catch(()=>{});await save().catch(()=>{});
  console.error('application_icon_e2e_failed');process.exitCode=1;
});
