// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
// @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
// All helpers use the actual home/SSO flow; only platform cookies reach private files.
import assert from 'node:assert/strict';
import {mkdir,writeFile,rename,chmod,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {randomUUID} from 'node:crypto';
import {chromium} from 'playwright';

const base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url);
async function credentialsFromStdin(){
  assert(!process.stdin.isTTY,'private_pipe_required');
  const input=createInterface({input:process.stdin});
  try{
    const line=await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));});
    assert(line.length<=8192);const value=JSON.parse(line);
    assert(value&&typeof value.username==='string'&&typeof value.password==='string'&&value.username&&value.password);
    return value;
  }finally{input.close();}
}
async function signIn(browser,credentials,filename){
  const context=await browser.newContext({locale:'fr-FR'});
  const pending=new URL('.sso-'+randomUUID()+'.pending',output);
  try{
    const page=await context.newPage();await page.goto(base);
    await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();
    await page.waitForURL('https://oauth.lelabs.tech/**');
    await page.locator('input[name=username]').fill(credentials.username);
    await page.locator('input[type=password]').fill(credentials.password);
    await page.locator('input[type=submit],button[type=submit]').first().click();
    await page.waitForURL(base+'/**',{timeout:90000});
    await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
    const response=await context.request.get(base+'/api/session');assert.equal(response.status(),200);
    assert((await response.json()).authenticated);
    const state=await context.storageState();
    state.cookies=state.cookies.filter(row=>row.domain==='serverless.lelabs.tech'&&row.name==='__Host-p2-session');state.origins=[];
    assert.equal(state.cookies.length,1);assert(state.cookies[0].secure&&state.cookies[0].httpOnly);
    await writeFile(pending,JSON.stringify(state)+'\n',{mode:0o600,flag:'wx'});
    const target=new URL(filename,output);await rename(pending,target);await chmod(target,0o600);
    return state.cookies[0].value;
  }finally{await context.close();await rm(pending,{force:true});}
}
async function main(){
  const args=process.argv.slice(2);
  assert(args.length===0||(args.length===1&&args[0]==='--for-storage-decisions'),'invalid_sso_purpose');
  const purpose=args.length?'storage-decisions':'suite-start';
  await mkdir(output,{recursive:true,mode:0o700});
  const report=new URL(args.length?'dev-sso-decision-sessions.json':'dev-sso-sessions.json',output);
  await writeFile(report,JSON.stringify({completed:false,purpose})+'\n',{mode:0o600});
  let credentials=await credentialsFromStdin(),browser;
  try{
    browser=await chromium.launch({headless:true});
    const purge=await signIn(browser,credentials,'purge-admin-session.json');
    const control=await signIn(browser,credentials,'admin-session.json');
    assert.notEqual(purge,control,'independent_platform_sessions_required');
    const result={completed:true,purpose,authenticated:true,independent_sessions:2,platform_cookies_only:true};
    await writeFile(report,JSON.stringify(result)+'\n',{mode:0o600});console.log(JSON.stringify(result));
  }finally{credentials=null;await browser?.close();}
}
// Playwright errors may quote fill() arguments. Never emit their message, stack or cause.
main().catch(()=>{console.error('dev_sso_sessions_failed');process.exitCode=1;});
