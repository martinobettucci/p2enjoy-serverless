// @spec docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#qualification-réelle-et-données-de-test | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#qualification-réelle-et-données-de-test
// Public waiting views are labelled separately from unavailable real role/rotation proof.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdir,readFile,writeFile,rename} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {setTimeout as delay} from 'node:timers/promises';
import {chromium} from 'playwright';

const execute=promisify(execFile),base='https://serverless.lelabs.tech',campaign=randomUUID();
const out=new URL('../.local/e2e/',import.meta.url),prefix='sso-session-recovery-'+campaign;
const report=new URL(prefix+'.json',out),checks=[],captures=[],pageErrors=[],observations=[];
const digest=value=>createHash('sha256').update(value).digest('hex');
let browser,credentials,completed=false,failure=null,phase='private-input';
async function save(){
  const pending=new URL(prefix+'.pending',out);
  await writeFile(pending,JSON.stringify({campaign,target:base,completed,phase,checks,captures,observations,
    page_errors:pageErrors,failure,skipped:0,scope:'public_waiting_views_and_real_admin_refresh',
    unproved:['real_unverified_account','real_verified_only_account','discriminating_id_azp_refusal','real_signing_key_rotation']},null,2)+'\n',{mode:0o600});
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
  const path=new URL(prefix+'-'+label+'.jpg',out);await page.screenshot({path:path.pathname,type:'jpeg',quality:90,fullPage:false});
  const bytes=await readFile(path);captures.push({path:path.pathname,sha256:digest(bytes),bytes:bytes.length,viewport:page.viewportSize()});
}
async function inspect(cookie){
  const {stdout}=await execute('python3',['-B','e2e/sso-session-inspect.py',digest(cookie)],{timeout:65000,maxBuffer:32768});
  const value=JSON.parse(stdout);assert(value.verified&&value.lifetime_seconds===300);return value;
}
async function main(){
  await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();
  browser=await chromium.launch({headless:true});
  for(const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
    for(const reason of ['verification','administration']){
      const context=await browser.newContext({viewport:{width,height},locale:'fr-FR'}),page=await context.newPage();
      page.on('pageerror',error=>pageErrors.push({type:error.name,message_sha256:digest(String(error.message))}));
      try{
        await check('Vue publique d’attente '+label+' '+reason+' sans décision de rôle',async()=>{
          let sessionRequests=0;page.on('request',request=>{if(request.url()===base+'/api/session')sessionRequests++;});
          const response=await page.goto(base+'/auth/attente?reason='+reason);assert.equal(response.status(),200);
          await page.getByRole('heading',{name:'Accès en attente',exact:true}).waitFor();
          assert.equal(await page.getByRole('navigation').count(),0);assert.equal(await page.getByRole('alert').count(),0);
          assert(await page.getByText(reason==='verification'?'Demandez à un administrateur du SSO de vérifier votre compte.':'Si vous devez administrer cette plateforme, demandez à un administrateur du SSO de vous attribuer le rôle nécessaire.',{exact:true}).isVisible());
          assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
          assert.equal(await page.locator('.brand img').getAttribute('alt'),'');
          await capture(page,label+'-'+reason);assert.equal(sessionRequests,0,'waiting_view_must_not_read_session');
          const status=await context.request.get(base+'/api/session');assert.deepEqual(await status.json(),{authenticated:false});
          const denied=await context.request.get(base+'/api/namespaces');assert.equal(denied.status(),401);
          const link=page.getByRole('link',{name:'Vérifier mon accès',exact:true});
          await page.keyboard.press('Tab');assert(await link.evaluate(node=>node===document.activeElement));await page.keyboard.press('Enter');
          await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').waitFor();
          const retry=await context.request.get(base+'/auth/login',{maxRedirects:0});assert.equal(retry.status(),303);
          const flow=await context.cookies(base);assert(flow.some(row=>row.name==='__Host-p2-flow'));
          const state=new URL(retry.headers().location).searchParams.get('state');assert(state);
          const cancelled=await context.request.get(base+'/auth/retour?'+new URLSearchParams({state,error:'access_denied'}));
          assert.equal(cancelled.status(),401);assert(!(await context.cookies(base)).some(row=>row.name==='__Host-p2-flow'));
        });
      }finally{await context.close();}
    }
  }
  const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'fr-FR'}),page=await context.newPage();
  page.on('pageerror',error=>pageErrors.push({type:error.name,message_sha256:digest(String(error.message))}));
  let initial,cookie,csrf,user;
  try{
    await check('Motifs invalides refusés et alias canonique sans session',async()=>{
      for(const suffix of ['', '?reason=inconnu','?reason=https%3A%2F%2Fexample.org']){
        const response=await context.request.get(base+'/auth/attente'+suffix);assert.equal(response.status(),400);
        assert.equal(response.headers()['cache-control'],'no-store');
      }
      const alias=await context.request.get('https://functions.lelabs.tech/auth/attente?reason=verification&next=https://example.org',{maxRedirects:0});
      assert.equal(alias.status(),303);assert.equal(alias.headers().location,base+'/auth/attente?reason=verification');
    });
    await check('Accueil et SSO administrateur réels, JWT signé de300s',async()=>{
      await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();
      await page.waitForURL('https://oauth.lelabs.tech/**');
      await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);
      await page.locator('input[type=submit],button[type=submit]').first().click();
      await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
      const response=await context.request.get(base+'/api/session');assert.equal(response.status(),200);const status=await response.json();
      assert(status.authenticated);csrf=status.csrf_token;user=status.user.id;
      cookie=(await context.cookies(base)).find(row=>row.name==='__Host-p2-session').value;
      initial=await inspect(cookie);assert(initial.id_token_present);observations.push({stage:'initial',...initial});await capture(page,'admin-initial');
      for(const reason of ['verification','administration']){
        const seen=[];const record=request=>{if(request.url()===base+'/api/session')seen.push(true);};page.on('request',record);
        const waitingResponse=await page.goto(base+'/auth/attente?reason='+reason);assert.equal(waitingResponse.status(),200);
        await page.getByRole('heading',{name:'Accès en attente',exact:true}).waitFor();assert.equal(seen.length,0);
        page.off('request',record);await page.getByRole('link',{name:'Revenir à l’accueil',exact:true}).click();
        await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
      }
    });
    await check('Expiration réelle puis renouvellement, même cookie et sujet',async()=>{
      const started=Date.now(),wait=(initial.exp+1)*1000-started;
      assert(wait>0&&wait<=301000,'actual_expiry_wait_required');
      observations.push({stage:'waiting_for_actual_expiry',started_at:started/1000,initial_exp:initial.exp,wait_milliseconds:wait});await save();
      await delay(wait);
      const response=await context.request.get(base+'/api/session');assert.equal(response.status(),200);
      const status=await response.json();assert(status.authenticated);assert.equal(status.user.id,user);assert.equal(status.csrf_token,csrf);
      const current=(await context.cookies(base)).find(row=>row.name==='__Host-p2-session');assert.equal(current.value,cookie);
      const refreshed=await inspect(cookie);assert(refreshed.iat>=initial.exp,'refresh_must_follow_initial_expiry');
      assert(refreshed.sampled_at>=initial.exp);assert.equal(refreshed.subject_sha256,initial.subject_sha256);
      assert.equal(refreshed.session_created_at,initial.session_created_at);assert.equal(refreshed.session_expires_at,initial.session_expires_at);
      observations.push({stage:'refreshed',...refreshed,elapsed_seconds:(Date.now()-started)/1000});
      await page.reload();await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();await capture(page,'admin-refreshed');
    });
    await check('Déconnexion réelle et ancien cookie définitivement refusé',async()=>{
      const response=await context.request.post(base+'/auth/logout',{headers:{Origin:base,'X-CSRF-Token':csrf}});
      assert.equal(response.status(),200);assert((await response.json()).signed_out);
      const stale=await context.request.get(base+'/api/session',{headers:{Cookie:'__Host-p2-session='+cookie}});
      assert.deepEqual(await stale.json(),{authenticated:false});
      await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).waitFor();
      assert.equal(await page.getByRole('navigation').count(),0);
    });
    assert.deepEqual(pageErrors,[]);completed=true;phase='completed';
  }finally{
    if(cookie&&csrf&&!completed)await context.request.post(base+'/auth/logout',{headers:{Origin:base,'X-CSRF-Token':csrf}}).catch(()=>{});
    await context.close();
  }
  credentials=null;await browser.close();await save();console.log(JSON.stringify({completed,groups:checks.length,report:report.pathname,captures:captures.length}));
}
main().catch(async error=>{
  credentials=null;completed=false;failure={type:error.name,message_sha256:digest(String(error.message))};
  await browser?.close().catch(()=>{});await save().catch(()=>{});console.error('sso_session_recovery_e2e_failed');process.exitCode=1;
});
