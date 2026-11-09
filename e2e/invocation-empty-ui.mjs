// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#parcours-public-du-catalogue-vide-sous-vraies-routes | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#parcours-public-du-catalogue-vide-sous-vraies-routes
// Real home, UI creation/publication, admitted browser GET, normal route console and Docker.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {createInterface} from 'node:readline';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {chromium} from 'playwright';
import {enterNamespaces} from './console-navigation.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',nonce=randomUUID(),prefix='invocation-route-pause-'+nonce.slice(0,8);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/invocation-request-pause.py',routeHelper=path.join(root,'e2e/invocation-route-guard.py');
const checks=[],observations=[],guards=[],cleanupErrors=[],tokens=[],operatorErrors=[],faults=[],captures={};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let browser,context,page,admin,session,namespace,service,fn,revision,work,image,completed=false,purged,failure,read;
let routeFolder,routePossiblyArmed=false,routeRestored=false,routeRestoration,routeMutationUnknown=false;
const routeRecords={};
await mkdir(out,{recursive:true,mode:0o700});
const report=path.join(out,'invocation-empty-ui.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
async function until(action,message,timeout=40000){
  const deadline=Date.now()+timeout;
  while(true){const value=await action();if(value)return value;assert(Date.now()<deadline,message);await sleep(100);}
}
function command(file,args,options={}){
  return new Promise(resolve=>{
    const child=execFile(file,args,{cwd:root,timeout:180000,maxBuffer:2*1024*1024,...options},(error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr}));
    child.stdin.end();
  });
}
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),'platform_api_status');
  return response.json();
}
function args(mode,extra=[]){return ['python3','-B',helper,mode,namespace.id,service.id,fn.id,nonce,image,...extra];}
async function remote(mode,unit){
  const result=await command('ssh',[...ssh,...args(mode,[unit])]);
  if(result.code!==0)operatorErrors.push({mode,exit_code:result.code,stderr:result.stderr});
  assert.equal(result.code,0,'pause_remote_operator_failed');return JSON.parse(result.stdout);
}
async function quiet(){
  await until(async()=>{
    const all=await api('/api/functions?limit=100');assert.equal(all.total,1);assert.equal(all.items[0].id,fn.id);
    const instances=await api(`/api/functions/${fn.id}/instances?limit=100`),calls=await api(`/api/functions/${fn.id}/invocations?limit=100`);
    return !instances.items.length&&!calls.items.some(row=>['receiving','queued','admitted','running'].includes(row.state));
  },'fixture_not_quiet');
}
async function arm(mode){
  await quiet();
  const child=spawn('ssh',[...ssh,...args(mode)],{cwd:root,stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,exitCode,stderr='',protocolError=false;
  const lines=createInterface({input:child.stdout});
  lines.on('line',line=>{try{events.push(JSON.parse(line));}catch{protocolError=true;}});
  child.stderr.on('data',bytes=>{stderr+=bytes.toString();});child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{
    child.once('close',code=>{ended=true;exitCode=code;resolve(code);});
    child.once('error',()=>{ended=true;exitCode=-1;resolve(-1);});
  });
  const value={mode,events,restored:false,diagnostic:()=>({mode,events,exit_code:exitCode,stderr,restored:value.restored}),
    async wait(event){return until(()=>{assert(!protocolError,'native_protocol_invalid');const row=events.find(v=>v.event===event);assert(row||!ended,'native_observer_ended_before_gate');return row;},'native_event_missing:'+event);},
    send(text){child.stdin.write(text+'\n');},
    async finish(){
      const code=await done;
      assert(mode==='pause'?code===0:[137,255].includes(code),'native_helper_exit');
      if(mode==='loss')assert(events.some(v=>v.event==='observer-loss'&&v.signal==='SIGKILL'));
      const armed=events.find(v=>v.event==='guard-armed');assert(armed);
      const resumed=await until(async()=>{
        const v=await remote('evidence',armed.unit);
        return v.event==='resumed'&&['inactive','unknown'].includes(v.service_state)?v:false;
      },'independent_resume_missing',40000);
      assert(resumed.healthy&&resumed.tracer_absent&&resumed.control_start_unchanged&&resumed.reference_unchanged);
      assert.equal(resumed.independent,mode==='loss');
      if(mode==='loss')assert(resumed.observer_gone);
      const disarmed=await remote('disarm',armed.unit);assert(['inactive','unknown'].includes(disarmed.timer_state)&&['inactive','unknown'].includes(disarmed.service_state));
      assert(!tokens.some(token=>JSON.stringify(events).includes(token)||stderr.includes(token)));
      value.restored=true;value.receipt={mode,events,exit_code:code,resumed:disarmed};return value.receipt;
    },
    async recover(){
      child.stdin.end();
      const armed=events.find(v=>v.event==='guard-armed');
      if(armed){
        const resumed=await remote('recover',armed.unit);await done;
        assert(resumed.healthy&&resumed.tracer_absent&&resumed.control_start_unchanged&&resumed.reference_unchanged);
        assert(['inactive','unknown'].includes(resumed.timer_state)&&['inactive','unknown'].includes(resumed.service_state));
        value.restored=true;
      }
      else {await done;assert.fail('guard_identity_unknown_fixture_retained');}
    }};
  guards.push(value);await value.wait('armed');return value;
}
async function route(action,...args){
  const value=await command('python3',['-B',routeHelper,action,...args],{timeout:0});
  if(value.code!==0)operatorErrors.push({action,exit_code:value.code,stdout:value.stdout,stderr:value.stderr});
  assert.equal(value.code,0,'route_console_operator_failed');return JSON.parse(value.stdout);
}
async function collectRouteRecords(){
  if(!routeFolder)return;
  assert.equal(path.dirname(routeFolder),out);assert(/^invocation-route-guard-[0-9a-f-]{36}$/.test(path.basename(routeFolder)));
  for(const name of ['identity.json','restored.json']){
    try{
      const raw=await readFile(path.join(routeFolder,name),'utf8');
      routeRecords[name]={raw_utf8:raw,sha256:createHash('sha256').update(raw).digest('hex')};
    }catch(error){if(error.code!=='ENOENT')throw error;if(routeRestored)throw error;}
  }
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
async function capture(name){
  await page.evaluate(()=>scrollTo(0,0));
  const target=path.join(out,'invocation-empty-ui-'+name+'.jpg');
  const bytes=await page.screenshot({path:target,type:'jpeg',quality:85,fullPage:true});
  captures[path.basename(target)]={sha256:createHash('sha256').update(bytes).digest('hex'),viewport:page.viewportSize()};
}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page_overflow');}
async function ready(){
  await page.getByRole('heading',{name:'Adresses d’appel',exact:true}).waitFor();
  await page.waitForFunction(()=>{const b=[...document.querySelectorAll('button')].find(v=>v.textContent==='Actualiser');return b&&!b.disabled;});
}
async function create(url,click){
  const pending=page.waitForResponse(r=>r.url()===base+url&&r.request().method()==='POST');
  await click();assert.equal((await pending).status(),201);
  const kind=url.split('/').at(-1);
  await page.waitForURL(new RegExp('/console/'+kind+'/[0-9a-f-]{36}'));
  return {id:new URL(page.url()).pathname.split('/')[3]};
}
async function twoDomains(){
  for(const domain of ['functions.lelabs.tech','serverless.lelabs.tech'])await page.getByRole('heading',{name:domain,exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Copier l’adresse',exact:true}).count(),2);
}
try{
  image=JSON.parse(await readFile(path.join(root,'docs/evidence/invocation-request-pause-dev-2026-11-09.json'),'utf8')).control_image;
  browser=await chromium.launch({headless:true});
  context=await browser.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),viewport:{width:1440,height:1000},locale:'fr-FR'});
  admin=context.request;session=await(await admin.get('/api/session')).json();assert(session.authenticated,'real_admin_session_required');
  assert.equal((await api('/api/functions?limit=1')).total,0,'quiet_installation_required');
  page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',error=>faults.push(error.name));
  work=await mkdtemp(path.join(out,'invocation-empty-ui-code-'));
  await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
  await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'ui-empty'}));
  const packed=await command('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(p/'function.zip','w');[z.write(p/n,n) for n in ('handler.cjs','revision.json')];z.close()",work]);assert.equal(packed.code,0);
  await check('Accueil, création et publication UI puis catalogue initial à deux domaines',async()=>{
    await enterNamespaces(page,base);
    await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');
    await dialog.getByLabel('Nom',{exact:true}).fill(prefix);await dialog.getByLabel('Description',{exact:true}).fill(nonce);
    namespace=await create('/api/namespaces',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');
    await dialog.getByLabel('Nom',{exact:true}).fill('request-pause-fixture');await dialog.getByLabel('Description',{exact:true}).fill(nonce);
    service=await create(`/api/namespaces/${namespace.id}/services`,()=>dialog.getByRole('button',{name:'Enregistrer',exact:true}).click());
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');
    await dialog.getByLabel('Nom',{exact:true}).fill('route-entry');await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    fn=await create(`/api/services/${service.id}/functions`,()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());
    await page.getByRole('link',{name:'Code et révisions',exact:true}).click();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();
    dialog=page.getByRole('dialog');await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(path.join(work,'function.zip'));
    await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();
    const upload=page.waitForResponse(r=>r.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(r.url()).pathname));
    await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();assert.equal((await upload).status(),200);await dialog.waitFor({state:'hidden'});
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Adresses d’appel',exact:true}).click();await ready();await twoDomains();
    revision=(await api(`/api/functions/${fn.id}`)).active_revision_id;assert(revision);
    read=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'invoke-empty-ui-fixture',rights:['read'],function_ids:[fn.id]},status:201})).token;tokens.push(read);
    await fits();await capture('initial-desktop');
  });
  await check('Vrai GET public conservé pendant détour des deux routes : état vide desktop et mobile',async()=>{
    await quiet();routePossiblyArmed=true;
    const armed=await route('arm','--owner',String(process.pid),'--seconds','180');routeFolder=armed.folder;
    const observer=await arm('pause');let settled=false;
    const pending=page.waitForResponse(r=>r.request().method()==='GET'&&r.url()===base+`/api/functions/${fn.id}/invocation-urls?limit=5&offset=0`,{timeout:120000});
    pending.then(()=>{settled=true;},()=>{settled=true;});observer.pending=pending;
    await page.getByRole('button',{name:'Actualiser',exact:true}).click();const gated=await observer.wait('gated');assert(!settled,'browser_request_must_be_held');
    routeMutationUnknown=true;
    const changed=await route('divert-both','--folder',routeFolder);assert(changed.completed);
    assert(Object.values(changed.after).every(v=>v.target_port===18091));routeMutationUnknown=false;observer.send('release');
    const receipt=await observer.finish(),response=await pending;assert.equal(response.status(),200,'same_browser_connection_survived');
    const catalogue=await response.json();assert.equal(catalogue.source.state,'available');assert.equal(catalogue.total,0);assert.deepEqual(catalogue.items,[]);assert.equal(catalogue.revision_id,revision);
    await ready();await page.getByText('Aucun domaine d’appel applicable. Demandez une route vers la passerelle à l’administrateur du SPARK, puis actualisez.',{exact:true}).waitFor();
    assert.equal(await page.getByRole('button',{name:'Copier l’adresse',exact:true}).count(),0);assert.equal(await page.getByRole('button',{name:'Copier l’exemple curl',exact:true}).count(),0);
    assert.equal(await page.locator('.invocation-url').count(),0);assert.equal(await page.locator('.notice.success').count(),0);assert.equal(await page.getByRole('alert').count(),0);
    assert.equal(await page.evaluate(()=>document.activeElement?.id),'invocation-urls-title');await fits();await capture('empty-desktop');
    await page.setViewportSize({width:390,height:844});await fits();await capture('empty-mobile');
    observations.push({scenario:'real-public-empty',gated,route_change:changed,native_receipt:receipt,catalogue,browser_response_status:response.status(),same_admitted_browser_request:true});
  });
  await check('Restauration, actualisation UI puis invocation Docker de l’adresse copiée',async()=>{
    routeRestoration=await route('release','--folder',routeFolder);assert(routeRestoration.completed);routeRestored=true;
    await page.getByRole('button',{name:'Actualiser',exact:true}).click();await ready();await twoDomains();await fits();await capture('restored-mobile');
    await page.setViewportSize({width:1440,height:1000});await fits();await capture('restored-desktop');
    await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});
    const item=page.locator('.observation-list>li').filter({has:page.getByRole('heading',{name:'serverless.lelabs.tech',exact:true})});
    await item.getByRole('button',{name:'Copier l’adresse',exact:true}).click();await item.getByText('Adresse copiée.',{exact:true}).waitFor();
    const copied=await page.evaluate(()=>navigator.clipboard.readText());assert.equal(copied,base+'/invoke/'+fn.id);
    const response=await admin.get(copied,{headers:{'X-Serverless-Token':read}});assert.equal(response.status(),200);assert.equal((await response.json()).revision,'ui-empty');
    observations.push({scenario:'restored-ui-copy-and-invoke',copied_url:copied,status:200,revision:'ui-empty',restoration:routeRestoration});
  });
  completed=true;
}catch(error){failure={name:error.name,message:error.message};throw error;}
finally{
  for(const guard of guards)if(!guard.restored){try{await guard.recover();}catch(error){cleanupErrors.push({resource:'native-guard',error:error.name});}}
  await Promise.allSettled(guards.map(v=>v.pending).filter(Boolean));
  if(routeFolder&&!routeRestored){try{routeRestoration=await route('release','--folder',routeFolder);assert(routeRestoration.completed);routeRestored=true;}catch(error){cleanupErrors.push({resource:'route-guard',error:error.name});}}
  if(routePossiblyArmed&&!routeRestored)cleanupErrors.push({resource:'route-restoration-unconfirmed-fixture-retained'});
  if(routeMutationUnknown)cleanupErrors.push({resource:'route-mutation-unconfirmed-fixture-retained'});
  try{await collectRouteRecords();}catch(error){cleanupErrors.push({resource:'native-route-records',error:error.name});}
  if(!cleanupErrors.length&&admin&&session?.authenticated){
    try{
      if(!namespace){const rows=await api('/api/catalogue/namespaces?q='+encodeURIComponent(prefix)+'&limit=50');namespace=rows.items.find(v=>v.name===prefix&&v.description===nonce);}
      if(namespace&&!service)service=(await api(`/api/namespaces/${namespace.id}/services?limit=100`)).items.find(v=>v.name==='request-pause-fixture'&&v.description===nonce);
      if(service){
        assert.equal((await api(`/api/services/${service.id}`)).description,nonce);
        const rows=(await api(`/api/services/${service.id}/functions?limit=100`)).items;assert(rows.length<=1&&rows.every(v=>v.name==='route-entry'));
        for(const row of rows){
          fn??={id:row.id};await api(`/api/functions/${row.id}`,{method:'DELETE'});const archive=await api(`/api/archives/${row.id}`);
          let operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',body:{operation_id:randomUUID(),confirm_name:archive.name},headers:{'If-Match':String(archive.updated_at)},status:[200,202]});
          await until(async()=>{operation=await api(`/api/storage-operations/${operation.id}`);assert.notEqual(operation.state,'failed');return operation.state==='completed';},'purge_not_completed',90000);
          purged={function_id:row.id,operation_id:operation.id};
        }
        await api(`/api/services/${service.id}`,{method:'DELETE'});
      }
      if(namespace){assert.equal((await api(`/api/namespaces/${namespace.id}`)).description,nonce);await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}
    }catch(error){cleanupErrors.push({resource:'fixture',error:error.name});}
  }
  if(work&&!cleanupErrors.length)await rm(work,{recursive:true,force:true});await browser?.close();
  const value={completed:completed&&!cleanupErrors.length&&!faults.length,cleanup:!cleanupErrors.length,checks,skipped:0,faults,captures,observations,cleanup_errors:cleanupErrors,failure,
    prefix,ownership_nonce:nonce,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],revision_id:revision,purged,
    guard_receipts:guards.map(v=>v.receipt??v.diagnostic()),operator_errors:operatorErrors,route_guard_folder:routeFolder,route_restoration:routeRestoration,route_restored:routeRestored,
    route_mutation_unknown:routeMutationUnknown,route_records:routeRecords,
    work_retained:Boolean(work&&cleanupErrors.length)};
  const raw=JSON.stringify(value,null,2);assert(!tokens.some(token=>raw.includes(token)),'private_credential_in_report');
  await writeFile(report,raw+'\n');assert.equal(cleanupErrors.length,0,'cleanup_required');
}
