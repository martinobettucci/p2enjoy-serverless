// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#entrée-publique-de-lalias-et-sso-réel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#entrée-publique-de-lalias-et-sso-réel
// Real HTTPS, fresh browsers, actual SSO and closure of only the sessions created here.
import assert from 'node:assert/strict';
import {mkdir,writeFile,chmod} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {createHash,randomUUID} from 'node:crypto';
import {chromium,request} from 'playwright';

const base='https://serverless.lelabs.tech',alias='https://functions.lelabs.tech';
const issuer='https://oauth.lelabs.tech',authorization=issuer+'/realms/lelabs/protocol/openid-connect/auth';
const output=new URL('../.local/e2e/',import.meta.url);
const checks=[],observations=[],captures={},faults=[],cleanupErrors=[],contexts=[],privateValues=[];
const hash=value=>createHash('sha256').update(value).digest('hex');
let credentials,browser,publicClient,completed=false;
async function privateCredentials(){
  assert(!process.stdin.isTTY,'private_pipe_required');const input=createInterface({input:process.stdin});
  try{
    const line=await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));});
    assert(line.length<=8192);const value=JSON.parse(line);
    assert(value&&typeof value.username==='string'&&typeof value.password==='string'&&value.username&&value.password);
    return value;
  }finally{input.close();}
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){
    const message=String(error.message??'');
    const kind=/No resource with given identifier|No data found for resource|Resource.*not.*found/i.test(message)?'response_body_unavailable':
      /strict mode violation/i.test(message)?'ambiguous_locator':/Timeout/i.test(error.name)?'operation_timeout':
      /Execution context was destroyed/i.test(message)?'navigation_context_replaced':'browser_operation_error';
    checks.push({name,status:'failed',error:error.name,error_kind:kind,phase:contexts.at(-1)?.phase});throw error;
  }
}
async function capture(page,name){
  await page.evaluate(()=>scrollTo(0,0));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page_overflow');
  const target=new URL('invocation-alias-entry-'+name+'.jpg',output);
  const bytes=await page.screenshot({path:target.pathname,type:'jpeg',quality:85,fullPage:true});
  captures[target.pathname.split('/').at(-1)]={sha256:hash(bytes),viewport:page.viewportSize()};
}
async function session(context){
  const response=await context.request.get(base+'/api/session');assert.equal(response.status(),200);return response.json();
}
async function closeOwnSession(record){
  const flows=(await record.context.cookies(base)).filter(v=>v.domain==='serverless.lelabs.tech'&&v.name==='__Host-p2-flow');
  assert(flows.length<=1);
  if(flows.length){
    assert(/^[A-Za-z0-9_-]{43}$/.test(flows[0].value));
    record.flowState=flows[0].value;record.flowDigest=hash(record.flowState);privateValues.push(record.flowState);
  }
  const current=await session(record.context);
  if(current.authenticated){
    const response=await record.context.request.post(base+'/auth/logout',{headers:{Origin:base,'X-CSRF-Token':current.csrf_token}});
    assert.equal(response.status(),200);assert((await response.json()).signed_out);
  }else if(record.flowState){
    const response=await record.context.request.get(base+'/auth/retour?state='+encodeURIComponent(record.flowState)+'&error=access_denied',{maxRedirects:0});
    assert.equal(response.status(),401);
  }
  assert.equal((await session(record.context)).authenticated,false);record.closed=true;
}
function watch(record,promise){
  promise.catch(()=>{});record.waiters.push(promise);return promise;
}
async function observeLogout(page,record){
  const cdp=await record.context.newCDPSession(page);
  let requestId,status,reading=false,settled=false,resolve,reject;
  const finished=watch(record,new Promise((yes,no)=>{resolve=yes;reject=no;}));
  const finish=(error,value)=>{
    if(settled)return;settled=true;clearTimeout(timer);if(error)reject(error);else resolve(value);
  };
  const timer=setTimeout(()=>finish(new Error('logout_observation_timeout')),20000);
  const requested=event=>{
    if(event.request.url===base+'/auth/logout'&&event.request.method==='POST'){
      if(requestId&&requestId!==event.requestId){finish(new Error('multiple_logout_requests'));return;}
      requestId=event.requestId;
    }
  };
  const responded=event=>{if(event.requestId===requestId)status=event.response.status;};
  const failed=event=>{if(event.requestId===requestId)finish(new Error('logout_network_failed'));};
  const loaded=event=>{
    if(event.requestId!==requestId||reading||settled)return;reading=true;
    cdp.send('Network.getResponseBody',{requestId}).then(value=>{
      const body=value.base64Encoded?Buffer.from(value.body,'base64').toString('utf8'):value.body;
      assert(Buffer.byteLength(body)<=4096,'logout_body_limit');const data=JSON.parse(body);
      assert.equal(status,200);assert(data.signed_out===true&&data.sso_signed_out===true);
      finish(null,{status,signed_out:data.signed_out,sso_signed_out:data.sso_signed_out,body_sha256:hash(body),body_bytes:Buffer.byteLength(body),read_only_cdp:true});
    }).catch(()=>finish(new Error('logout_observed_body_unavailable')));
  };
  cdp.on('Network.requestWillBeSent',requested);cdp.on('Network.responseReceived',responded);
  cdp.on('Network.loadingFinished',loaded);cdp.on('Network.loadingFailed',failed);
  const observer={finished,async stop(){
    finish(new Error('logout_observation_closed'));
    cdp.off('Network.requestWillBeSent',requested);cdp.off('Network.responseReceived',responded);
    cdp.off('Network.loadingFinished',loaded);cdp.off('Network.loadingFailed',failed);await cdp.detach();
  }};
  record.observer=observer;
  // Only after login; bounded native buffering, no interception or traffic mutation.
  await cdp.send('Network.enable',{maxTotalBufferSize:2*1024*1024,maxResourceBufferSize:65536,maxPostDataSize:0});
  await cdp.send('Network.configureDurableMessages',{maxTotalBufferSize:2*1024*1024,maxResourceBufferSize:65536});
  return observer;
}
async function preserveOwnSession(record){
  const cookies=(await record.context.cookies(base)).filter(v=>v.domain==='serverless.lelabs.tech'&&v.name==='__Host-p2-session');
  if(!cookies.length)return;
  assert.equal(cookies.length,1);assert(cookies[0].secure&&cookies[0].httpOnly);privateValues.push(cookies[0].value);
  const file=new URL('alias-entry-session-pending-'+randomUUID()+'.json',output);
  await writeFile(file,JSON.stringify({cookies,origins:[]})+'\n',{mode:0o600,flag:'wx'});await chmod(file,0o600);
  record.recoveryFile=file.pathname;
}
async function browserFlow(label,viewport){
  const context=await browser.newContext({locale:'fr-FR',viewport,ignoreHTTPSErrors:false});
  const record={context,label,closed:false,waiters:[]};contexts.push(record);
  const page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',error=>faults.push({label,error:error.name}));
  await page.goto(alias);
  await page.getByRole('heading',{name:'Votre console serverless',exact:true}).waitFor();
  assert.equal(new URL(page.url()).origin,base);assert.equal(new URL(page.url()).pathname,'/');
  assert.equal((await context.cookies(alias)).length,0,'no_alias_cookie_before_login');
  await capture(page,label+'-welcome');
  const authRequest=watch(record,page.waitForRequest(r=>r.method()==='GET'&&r.url().split('?')[0]===authorization));
  await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();
  const target=new URL((await authRequest).url());await page.waitForURL(value=>value.origin===issuer);
  assert.equal(target.searchParams.get('client_id'),'p2enjoy-serverless-dev');
  assert.equal(target.searchParams.get('redirect_uri'),base+'/auth/retour');assert.equal(target.searchParams.get('response_type'),'code');
  assert.equal(target.searchParams.get('code_challenge_method'),'S256');
  assert.deepEqual(target.searchParams.get('scope').split(' ').sort(),['email','openid','profile']);
  record.flowState=target.searchParams.get('state');assert(/^[A-Za-z0-9_-]{43}$/.test(record.flowState));privateValues.push(record.flowState);
  record.flowDigest=hash(record.flowState);
  const flow=(await context.cookies(base)).filter(v=>v.name==='__Host-p2-flow');
  assert.equal(flow.length,1);assert.equal(flow[0].domain,'serverless.lelabs.tech');assert(flow[0].secure&&flow[0].httpOnly);assert.equal(flow[0].value,record.flowState);
  await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);
  await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:90000});
  await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();assert.equal(new URL(page.url()).origin,base);
  assert((await session(context)).authenticated);
  const cookie=(await context.cookies(base)).filter(v=>v.name==='__Host-p2-session');
  assert.equal(cookie.length,1);assert.equal(cookie[0].domain,'serverless.lelabs.tech');assert(cookie[0].secure&&cookie[0].httpOnly&&cookie[0].path==='/'&&cookie[0].sameSite==='Lax');
  privateValues.push(cookie[0].value);record.sessionDigest=hash(cookie[0].value);
  assert.equal((await context.cookies(alias)).length,0,'no_alias_cookie_after_login');
  await capture(page,label+'-authenticated');
  record.phase='logout-observation-arm';const native=await observeLogout(page,record);
  record.phase='logout-locate';let logout=page.getByRole('button',{name:'Se déconnecter',exact:true});
  if(!await logout.isVisible())await page.getByRole('button',{name:'Menu',exact:true}).click();
  record.phase='logout-open';await logout.click();const pending=watch(record,page.waitForResponse(r=>r.url()===base+'/auth/logout'&&r.request().method()==='POST'));
  record.phase='logout-confirm';
  await page.locator('.confirmation .confirm').getByRole('button',{name:'Se déconnecter',exact:true}).click();
  record.phase='logout-response';const response=await pending;record.logoutStatus=response.status();assert.equal(response.status(),200);
  record.phase='logout-body';const result=await native.finished;assert(result.signed_out&&result.sso_signed_out);
  record.logoutObservation=result;
  record.phase='logout-return';
  await page.getByRole('heading',{name:'Votre console serverless',exact:true}).waitFor();assert.equal(new URL(page.url()).origin,base);
  record.phase='logout-state';assert.equal((await session(context)).authenticated,false);
  assert.equal((await context.cookies(base)).filter(v=>['__Host-p2-session','__Host-p2-flow'].includes(v.name)).length,0);
  assert.equal((await context.cookies(alias)).length,0);record.closed=true;
  record.phase='logout-capture';await capture(page,label+'-signed-out');record.phase='completed';
  observations.push({scenario:label,entry_origin:alias,console_origin:base,issuer_origin:issuer,client_id:'p2enjoy-serverless-dev',redirect_uri:base+'/auth/retour',response_type:'code',pkce:'S256',scopes:['openid','profile','email'],host_only_secure_http_only_platform_cookie:true,no_alias_cookie:true,session_digest:record.sessionDigest,flow_digest:record.flowDigest,signed_out:true,sso_signed_out:result.sso_signed_out,logout_observation:result});
}
async function main(){
  await mkdir(output,{recursive:true,mode:0o700});const report=new URL('invocation-alias-entry.json',output);
  await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
  try{
    credentials=await privateCredentials();privateValues.push(credentials.password);
    browser=await chromium.launch({headless:true});publicClient=await request.newContext({ignoreHTTPSErrors:false,timeout:30000});
    await check('Alias HTTPS : redirections canoniques fixes, aucun cookie et API session anonyme',async()=>{
      const samples=[];
      for(const [path,wanted] of [['/','/'],['/auth/login?next=https%3A%2F%2Foutside.invalid','/auth/login'],['/console/manual?next=https%3A%2F%2Foutside.invalid','/console/manual']]){
        const response=await publicClient.get(alias+path,{maxRedirects:0});assert.equal(response.status(),303);assert.equal(response.headers().location,base+wanted);assert(!response.headers()['set-cookie']);
        samples.push({path,status:response.status(),location:response.headers().location,no_set_cookie:true});
      }
      const response=await publicClient.get(alias+'/api/session',{maxRedirects:0});assert.equal(response.status(),200);assert.equal((await response.json()).authenticated,false);assert(!response.headers().location&&!response.headers()['set-cookie']);
      assert.equal((await publicClient.storageState()).cookies.length,0);observations.push({scenario:'anonymous-https',redirects:samples,session_api_status:200,authenticated:false,no_alias_cookie:true});
    });
    await check('Accueil alias desktop : vrai SSO, console canonique et déconnexion UI',()=>browserFlow('desktop',{width:1440,height:1000}));
    await check('Accueil alias mobile : vrai SSO, menu et déconnexion UI',()=>browserFlow('mobile',{width:390,height:844}));
    assert.equal(new Set(contexts.map(v=>v.sessionDigest)).size,2,'independent_sessions_required');completed=true;
  }finally{
    for(const record of contexts){
      if(!record.closed){
        try{await closeOwnSession(record);}catch(error){
          cleanupErrors.push({label:record.label,error:error.name});
          try{await preserveOwnSession(record);}catch(error){cleanupErrors.push({label:record.label,resource:'private-session-recovery',error:error.name});}
        }
      }
      if(record.observer){try{await record.observer.stop();}catch(error){cleanupErrors.push({label:record.label,resource:'native-browser-observer',error:error.name});}}
      try{await record.context.close();}catch(error){cleanupErrors.push({label:record.label,resource:'browser-context',error:error.name});}
      await Promise.allSettled(record.waiters);
    }
    credentials=null;await publicClient?.dispose();await browser?.close();
    const value={completed:completed&&!cleanupErrors.length&&!faults.length,cleanup:!cleanupErrors.length,checks,skipped:0,faults,captures,observations,cleanup_errors:cleanupErrors,
      sessions:contexts.map(v=>({label:v.label,session_digest:v.sessionDigest,flow_digest:v.flowDigest,closed:v.closed,recovery_file:v.recoveryFile,phase:v.phase,logout_status:v.logoutStatus})),route_changes:0,workloads_created:0,browser_version:browser?.version()};
    const raw=JSON.stringify(value,null,2);assert(!privateValues.some(v=>raw.includes(v)),'private_value_in_report');
    await writeFile(report,raw+'\n');assert.equal(cleanupErrors.length,0,'own_session_cleanup_required');
  }
}
// Never emit Playwright messages/stacks: fill() diagnostics may contain credentials.
main().catch(()=>{console.error('invocation_alias_entry_failed');process.exitCode=1;});
