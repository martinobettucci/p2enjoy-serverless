// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#parcours-navigateur-du-refus-de-lecture
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#parcours-navigateur-du-refus-de-lecture
// Real home/forms/publication, official-source EACCES, browser refresh, clipboard and Docker.
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
const base='https://serverless.lelabs.tech',alias='https://functions.lelabs.tech';
const helper='/srv/p2enjoy-serverless/e2e/invocation-source-permissions.py';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const checks=[],observations=[],tasks=[],cleanupErrors=[],operatorErrors=[],tokens=[],invokedAddresses=[];
const captures={},faults=[],pendingResponses=[];
const nonce=randomUUID(),prefix='source-access-'+nonce.slice(0,8);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
// OpenSSH joins its command arguments through the remote shell; quote the JSON scope.
const quote=value=>"'"+String(value).replaceAll("'","'\\''")+"'";
let completed=false,failure,client,admin,session,namespace,service,fn,revision,work,read,task,purged,browser,context,page;
await mkdir(out,{recursive:true,mode:0o700});const report=path.join(out,'invocation-source-ui.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const image=JSON.parse(await readFile(path.join(root,'docs/evidence/invocation-source-api-dev-2026-11-09.json'),'utf8')).control_image;
async function until(action,code,seconds=50){
  const deadline=Date.now()+seconds*1000;
  while(true){const value=await action();if(value)return value;assert(Date.now()<deadline,code);await sleep(100);}
}
async function remote(mode,unit){
  const value=await new Promise(resolve=>{
    const child=execFile('ssh',[...ssh,'python3','-B',helper,mode,'--folder','/run/'+unit],{timeout:180000,maxBuffer:2*1024*1024},(error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr}));child.stdin.end();
  });
  if(value.code!==0)operatorErrors.push({mode,unit,...value});
  assert.equal(value.code,0,'permission_operator_failed');return JSON.parse(value.stdout);
}
async function health(){
  for(const origin of ['https://serverless.lelabs.tech','https://functions.lelabs.tech']){
    const response=await client.get(origin+'/healthz');assert.equal(response.status(),200);assert.equal((await response.json()).component,'control');
  }
}
function start(action,scope){
  const events=[];let ended=false,exitCode,stderr='',invalid=false;
  const argv=['python3','-B',helper,'supervise','--image',image,'--delay','120','--scope',JSON.stringify(scope)];
  const child=spawn('ssh',[...ssh,argv.map(quote).join(' ')],{stdio:['pipe','pipe','pipe']});
  createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{invalid=true;}});
  child.stderr.on('data',value=>{stderr+=value.toString();});child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{
    child.once('close',code=>{ended=true;exitCode=code;resolve(code);});
    child.once('error',()=>{ended=true;exitCode=-1;resolve(-1);});
  });
  const task={events,restored:false,receipt:null,
    async wait(name){return until(()=>{
      assert(!invalid,'permission_protocol_invalid');const value=events.find(v=>v.event===name);
      assert(value||!ended,'permission_helper_ended');return value;
    },'permission_event_missing:'+name);},
    send(value){child.stdin.write(value+'\n');},
    async finish(){
      const code=await done;
      assert.equal(code,0,'permission_supervisor_exit');
      const armed=events.find(v=>v.event==='guard-armed');assert(armed);
      const started=events.find(v=>v.event==='helper-started'),exited=events.find(v=>v.event==='helper-exited');
      assert.equal(started?.pid,armed.identity.helper_pid);assert.equal(exited?.pid,armed.identity.helper_pid);
      assert.equal(exited.returncode,action==='release'?0:-9);assert.equal(exited.signal,action==='release'?null:'SIGKILL');
      if(action!=='release')assert(events.some(v=>v.event==='helper-signal'&&v.signal===(action==='kill-helper'?'SIGKILL':'SIGSTOP')));
      if(action==='stop-helper')assert(events.some(v=>v.event==='helper-stopped'&&v.pid===armed.identity.helper_pid&&v.signal==='SIGSTOP'));
      const restored=await until(async()=>{
        const value=await remote('evidence',armed.unit);
        return value.completed&&value.event==='restored'&&['inactive','unknown'].includes(value.service_state)?value:false;
      },'permission_restore_missing');
      assert(restored.source_restored);assert.equal(restored.independent,action!=='release');
      if(action==='stop-helper')assert(restored.helper_killed&&restored.helper_absent);
      if(action==='kill-helper')assert(restored.helper_absent);
      const value=await remote('disarm',armed.unit);
      assert(['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state));
      assert.equal(value.source.after.mode,armed.identity.source.mode);assert.equal(value.source.after.sha256,armed.identity.source.sha256);
      assert.equal(value.current_installation.open.errno,0);assert(value.current_installation.local_health);
      task.restored=true;task.receipt={action,events,exit_code:code,restoration:value};return task.receipt;
    },
    async recover(){
      child.stdin.end();const armed=events.find(v=>v.event==='guard-armed');
      if(!armed){await done;assert.fail('permission_guard_identity_unknown');}
      const value=await remote('recover',armed.unit);await done;
      assert(value.completed&&value.source_restored&&value.current_installation.local_health);
      assert(['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state));task.restored=true;
    },
    diagnostic(){return {action,events,exit_code:exitCode,stderr,restored:task.restored};}
  };
  tasks.push(task);return task;
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
}async function quiet(){
  await until(async()=>{
    const all=await api('/api/functions?limit=100');assert.equal(all.total,1);assert.equal(all.items[0].id,fn.id);
    const instances=await api(`/api/functions/${fn.id}/instances?limit=100`),calls=await api(`/api/functions/${fn.id}/invocations?limit=100`);
    return !instances.items.length&&!calls.items.some(row=>['receiving','queued','admitted','running'].includes(row.state));
  },'fixture_not_quiet');
}
function watch(promise){
  promise.catch(()=>{});pendingResponses.push(promise);return promise;
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
async function capture(name){
  await page.evaluate(()=>scrollTo(0,0));
  const target=path.join(out,'invocation-source-ui-'+name+'.jpg');
  const bytes=await page.screenshot({path:target,type:'jpeg',quality:85,fullPage:true});
  captures[path.basename(target)]={sha256:createHash('sha256').update(bytes).digest('hex'),viewport:page.viewportSize()};
}
async function fits(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'page_overflow');}
async function ready(){
  await page.getByRole('heading',{name:'Adresses d’appel',exact:true}).waitFor();
  await page.waitForFunction(()=>{const b=[...document.querySelectorAll('button')].find(v=>v.textContent==='Actualiser');return b&&!b.disabled;});
}
async function create(url,click){
  const pending=watch(page.waitForResponse(r=>r.url()===base+url&&r.request().method()==='POST'));
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
  browser=await chromium.launch({headless:true});
  context=await browser.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),viewport:{width:1440,height:1000},locale:'fr-FR'});
  admin=context.request;client=admin;session=await(await admin.get('/api/session')).json();assert(session.authenticated,'real_admin_session_required');
  assert.equal((await api('/api/functions?limit=1')).total,0,'quiet_installation_required');
  page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',error=>faults.push(error.name));
  work=await mkdtemp(path.join(out,'invocation-source-ui-code-'));
  await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
  await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'source-ui'}));
  const packed=await command('python3',['-B','-c',"import sys,zipfile;from pathlib import Path;p=Path(sys.argv[1]);z=zipfile.ZipFile(p/'function.zip','w');[z.write(p/n,n) for n in ('handler.cjs','revision.json')];z.close()",work]);assert.equal(packed.code,0);
  await check('Accueil, création et publication UI puis catalogue initial à deux domaines',async()=>{
    await enterNamespaces(page,base);
    await page.getByRole('button',{name:'Créer un namespace',exact:true}).click();let dialog=page.getByRole('dialog');
    await dialog.getByLabel('Nom',{exact:true}).fill(prefix);await dialog.getByLabel('Description',{exact:true}).fill(nonce);
    namespace=await create('/api/namespaces',()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());
    await page.getByRole('button',{name:'Créer un service',exact:true}).click();dialog=page.getByRole('dialog');
    await dialog.getByLabel('Nom',{exact:true}).fill('source-access-fixture');await dialog.getByLabel('Description',{exact:true}).fill(nonce);
    service=await create(`/api/namespaces/${namespace.id}/services`,()=>dialog.getByRole('button',{name:'Enregistrer',exact:true}).click());
    await page.getByRole('button',{name:'Créer une fonction',exact:true}).click();dialog=page.getByRole('dialog');
    await dialog.getByLabel('Nom',{exact:true}).fill('source-access-entry');await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');
    fn=await create(`/api/services/${service.id}/functions`,()=>dialog.getByRole('button',{name:'Créer',exact:true}).click());
    await page.getByRole('link',{name:'Code et révisions',exact:true}).click();await page.getByRole('button',{name:'Publier une archive',exact:true}).click();
    dialog=page.getByRole('dialog');await dialog.getByLabel('Archive ZIP',{exact:true}).setInputFiles(path.join(work,'function.zip'));
    await dialog.getByLabel('Handler',{exact:true}).fill('handler.handler');await dialog.getByRole('button',{name:'Vérifier la publication',exact:true}).click();
    const upload=watch(page.waitForResponse(r=>r.request().method()==='PUT'&&/\/api\/deployments\/[^/]+\/artifact$/.test(new URL(r.url()).pathname)));
    await dialog.getByRole('button',{name:'Confirmer la publication',exact:true}).click();assert.equal((await upload).status(),200);await dialog.waitFor({state:'hidden'});
    await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Adresses d’appel',exact:true}).click();await ready();await twoDomains();
    revision=(await api(`/api/functions/${fn.id}`)).active_revision_id;assert(revision);
    read=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'invoke-source-ui-fixture',rights:['read'],function_ids:[fn.id]},status:201})).token;tokens.push(read);
    await context.grantPermissions(['clipboard-read','clipboard-write'],{origin:base});
    const item=page.locator('.observation-list>li').filter({has:page.getByRole('heading',{name:'serverless.lelabs.tech',exact:true})});
    await item.getByRole('button',{name:'Copier l’adresse',exact:true}).click();await item.getByText('Adresse copiée.',{exact:true}).waitFor();
    const copied=await page.evaluate(()=>navigator.clipboard.readText());assert.equal(copied,base+'/invoke/'+fn.id);
    observations.push({scenario:'initial-ui-copy',copied_url:copied,revision_id:revision});
    await fits();await capture('initial-desktop');
  });

  await check('Refus réel du relevé : Actualiser retire les adresses et explique la panne',async()=>{
    await quiet();await health();
    task=start('release',{namespace_id:namespace.id,function_id:fn.id,nonce});
    const active=await task.wait('fault-active');assert.equal(active.control_open.errno,13);assert.equal(active.source.mode,0);
    const pending=watch(page.waitForResponse(r=>r.request().method()==='GET'&&r.url()===base+`/api/functions/${fn.id}/invocation-urls?limit=5&offset=0`));
    await page.getByRole('button',{name:'Actualiser',exact:true}).click();
    const response=await pending;assert.equal(response.status(),200);const catalogue=await response.json();
    assert.equal(catalogue.source.state,'unavailable');assert.equal(catalogue.source.error_code,'source_forbidden');
    assert.deepEqual(Object.keys(catalogue.source).sort(),['error_code','observed_at','state']);
    assert.deepEqual(catalogue.items,[]);assert.equal(catalogue.total,0);assert.equal(catalogue.revision_id,revision);
    await ready();const alert=page.getByRole('alert');
    await alert.getByText('Lecture des domaines refusée. Actualisez ; si le problème persiste, contactez l’administrateur du SPARK.',{exact:true}).waitFor();
    assert.equal(await alert.count(),1);assert.equal(await page.getByRole('button',{name:'Copier l’adresse',exact:true}).count(),0);
    assert.equal(await page.getByRole('button',{name:'Copier l’exemple curl',exact:true}).count(),0);
    assert.equal(await page.locator('.invocation-url').count(),0);assert.equal(await page.locator('.notice.success').count(),0);
    for(const domain of ['serverless.lelabs.tech','functions.lelabs.tech'])assert.equal(await page.getByRole('heading',{name:domain,exact:true}).count(),0);
    assert.equal(await page.evaluate(()=>document.activeElement?.id),'invocation-urls-title');
    await fits();await capture('refused-desktop');
    await page.setViewportSize({width:390,height:844});await fits();await capture('refused-mobile');
    observations.push({scenario:'source-forbidden-ui',catalogue,browser_response_status:response.status(),focus_dom:'invocation-urls-title',native_errno:active.control_open.errno});
  });
  await check('Restitution, Actualiser et invocation Docker de l’adresse copiée',async()=>{
    task.send('release');const restored=await task.finish();assert.equal(restored.restoration.independent,false);
    const pending=watch(page.waitForResponse(r=>r.request().method()==='GET'&&r.url()===base+`/api/functions/${fn.id}/invocation-urls?limit=5&offset=0`));
    await page.getByRole('button',{name:'Actualiser',exact:true}).click();
    const response=await pending;assert.equal(response.status(),200);const catalogue=await response.json();
    assert.equal(catalogue.source.state,'available');assert.equal(catalogue.total,2);assert.equal(catalogue.revision_id,revision);
    assert.equal(catalogue.source.sha256,restored.restoration.identity.source.sha256);
    await ready();await twoDomains();assert.equal(await page.getByRole('alert').count(),0);await fits();await capture('restored-mobile');
    await page.setViewportSize({width:1440,height:1000});await fits();await capture('restored-desktop');
    const item=page.locator('.observation-list>li').filter({has:page.getByRole('heading',{name:'serverless.lelabs.tech',exact:true})});
    await item.getByRole('button',{name:'Copier l’adresse',exact:true}).click();await item.getByText('Adresse copiée.',{exact:true}).waitFor();
    const copied=await page.evaluate(()=>navigator.clipboard.readText());assert.equal(copied,base+'/invoke/'+fn.id);
    const result=await admin.get(copied,{headers:{'X-Serverless-Token':read}});assert.equal(result.status(),200);
    assert.equal((await result.json()).revision,'source-ui');const requestId=result.headers()['x-serverless-request-id'];assert.match(requestId,/^[0-9a-f-]{36}$/);
    invokedAddresses.push({phase:'after-restoration',url:copied,status:200,revision:'source-ui',request_id:requestId});
    observations.push({scenario:'restored-ui-copy-and-invoke',catalogue,copied_url:copied,status:200,revision:'source-ui'});await health();
  });
  completed=true;
}catch(error){failure={name:error.name,message:error.message};throw new Error('invocation_source_ui_failed');}
finally{
  for(const current of tasks)if(!current.restored){try{await current.recover();}catch(error){cleanupErrors.push({resource:'permission-guard',error:error.name});}}
  // Without confirmed restoration retain the owned fixture for diagnosis.
  const safe=tasks.every(current=>current.restored)&&cleanupErrors.length===0;
  if(safe&&admin&&session?.authenticated){
    try{
      if(!namespace){const found=await api('/api/catalogue/namespaces?q='+encodeURIComponent(prefix)+'&limit=50');namespace=found.items.find(row=>row.name===prefix&&row.description===nonce);}
      if(namespace&&!service){const found=await api(`/api/namespaces/${namespace.id}/services?limit=100`);service=found.items.find(row=>row.name==='source-access-fixture'&&row.description===nonce);}
      if(service){
        const rows=(await api(`/api/services/${service.id}/functions?limit=100`)).items;assert(rows.every(row=>row.name==='source-access-entry'));
        for(const row of rows){
          fn??={id:row.id};await api(`/api/functions/${row.id}`,{method:'DELETE'});const archived=await api(`/api/archives/${row.id}`);
          let operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',body:{operation_id:randomUUID(),confirm_name:archived.name},status:[200,202],headers:{'If-Match':String(archived.updated_at)}});
          const deadline=Date.now()+90000;
          while(operation.state!=='completed'){assert.notEqual(operation.state,'failed');assert(Date.now()<deadline);await sleep(200);operation=await api(`/api/storage-operations/${operation.id}`);}
          purged={function_id:row.id,namespace_id:namespace.id,operation_id:operation.id};
        }
        await api(`/api/services/${service.id}`,{method:'DELETE'});
      }
      if(namespace)await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});
    }catch(error){cleanupErrors.push({resource:'fixture',error:error.name});}
  }
  if(!safe)cleanupErrors.push({resource:'fixture-retained-until-restoration'});
  if(work&&!cleanupErrors.length)await rm(work,{recursive:true,force:true});
  try{await browser?.close();}catch(error){cleanupErrors.push({resource:'browser',error:error.name});}
  await Promise.allSettled(pendingResponses);
  const raw=JSON.stringify({completed:completed&&!cleanupErrors.length&&!faults.length,cleanup:!cleanupErrors.length,checks,skipped:0,observations,captures,faults,
    tasks:tasks.map(current=>current.receipt??current.diagnostic()),failure,cleanup_errors:cleanupErrors,operator_errors:operatorErrors,
    prefix,ownership_nonce:nonce,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],revision_id:revision,
    invoked_addresses:invokedAddresses,purged,work_retained:Boolean(work&&cleanupErrors.length),route_changes:0},null,2);
  assert(!tokens.some(token=>raw.includes(token)),'credential_in_report');await writeFile(report,raw+'\n');
  assert.equal(cleanupErrors.length,0,'source_permission_cleanup_required');
}
