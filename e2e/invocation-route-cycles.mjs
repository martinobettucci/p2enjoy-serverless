// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_ROUTE_CYCLES.md
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_ROUTE_CYCLES.md#cinq-groupes-e2e-sérialisés
// Real normal-console operations, platform publication, native reads and Docker calls.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,readdir} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',alias='https://functions.lelabs.tech';
const guardFile=path.join(root,'e2e/invocation-route-guard.py');
const tokens=[],operatorErrors=[];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function command(file,args,options={}){
  const {privateInput,...spawnOptions}=options;
  return new Promise(resolve=>{
    const child=execFile(file,args,{cwd:root,timeout:300000,maxBuffer:2*1024*1024,...spawnOptions},
      (error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr}));
    if(privateInput!==undefined)child.stdin.end(privateInput);
    else child.stdin.end();
  });
}
async function guard(action,...args){
  // The operator owns bounded HTTP calls; never kill a console mutator on a wrapper timer.
  const value=await command('python3',['-B',guardFile,action,...args],{timeout:0});
  if(value.code!==0){operatorErrors.push({action,exit_code:value.code});throw new Error('guard_command_failed');}
  return JSON.parse(value.stdout);
}
async function processIdentity(pid){
  try{
    const raw=await readFile(`/proc/${pid}/stat`,'utf8'),fields=raw.slice(raw.lastIndexOf(')')+2).trim().split(/\s+/);
    return {pid,birth:fields[19],running:fields[0]!=='Z'};
  }catch(error){if(error.code==='ENOENT')return null;throw error;}
}
async function alive(identity){const current=await processIdentity(identity.pid);return Boolean(current?.running&&current.birth===identity.birth);}
async function bounded(promise,milliseconds,code){
  let timer;
  try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error(code)),milliseconds);})]);}
  finally{clearTimeout(timer);}
}

if(process.argv.length>2){
  assert.deepEqual(process.argv.slice(2),['--diverted-owner-pilot']);
  const armed=await guard('arm','--owner',String(process.pid),'--seconds','90');
  const changed=await guard('divert-alias','--folder',armed.folder);
  assert(changed.completed);
  console.log(JSON.stringify({event:'diverted',...armed,change:changed}));
  // Real independently identified pilot; the parent kills only this PID after confirmation.
  await sleep(120000);
  process.exit(2);
}

await mkdir(out,{recursive:true,mode:0o700});
const reportPath=path.join(out,'invocation-route-cycles.json');
const nonce=randomUUID(),prefix='invocation-route-cycles-'+nonce.slice(0,8);
const checks=[],observations=[],guards=[],pendingGuards=new Set(),cleanupErrors=[];
let namespace,service,fn,revision,work,admin,caller,session,full,read,pilot,pilotIdentity,pilotExit,pilotTerminal,pilotLines;
let completed=false,purged,failure,pilotChangeConfirmed=false,pilotMutationUnknown=false;
const principalIdentity=await processIdentity(process.pid);assert(principalIdentity?.running);
const invokedAddresses=[];
await writeFile(reportPath,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),'platform_api_status');
  return response.json();
}
async function catalogue(query='?limit=20'){
  const response=await caller.get(base+`/api/functions/${fn.id}/invocation-urls`+query,{headers:{'X-Serverless-Token':read}});
  assert.equal(response.status(),200);const value=await response.json();
  assert.equal(value.source.state,'available');assert.equal(value.revision_id,revision);
  return value;
}
async function invokeEntry(item){
  assert([base,alias].includes(item.origin));
  const entry=item.urls.find(row=>row.methods.includes('GET'));assert(entry,'emitted_get_required');
  const target=new URL(entry.url);assert.equal(target.origin,item.origin);assert.equal(target.pathname,'/invoke/'+fn.id);
  assert.equal(target.href,entry.url);assert(!target.search&&!target.hash);
  const response=await caller.get(entry.url,{headers:{'X-Serverless-Token':read}});
  assert.equal(response.status(),200,'real_docker_invocation');assert.equal((await response.json()).revision,'routes');
  invokedAddresses.push({url:entry.url,status:200,revision:'routes'});
}
async function invokeFrom(value,origin){const item=value.items.find(row=>row.origin===origin);assert(item);await invokeEntry(item);}
async function health(origin,status=200){
  const response=await caller.get(origin+'/healthz');assert.equal(response.status(),status,'real_https_health');
  if(status===200){const value=await response.json();assert.equal(value.status,'ok');assert.equal(value.component,'control');}
}
async function quiet(){
  const deadline=Date.now()+20000;
  while(true){
    const all=await api('/api/functions?limit=100');assert.equal(all.total,1);assert.equal(all.items[0].id,fn.id);
    const instances=await api(`/api/functions/${fn.id}/instances?limit=100`);
    const calls=await api(`/api/functions/${fn.id}/invocations?limit=100`);
    if(instances.items.length===0&&!calls.items.some(row=>['receiving','queued','admitted','running'].includes(row.state)))return;
    assert(Date.now()<deadline,'owned_function_not_quiet');await sleep(100);
  }
}
async function arm(){
  await quiet();await health(base);await health(alias);
  const value=await guard('arm','--owner',String(process.pid),'--seconds','90');
  pendingGuards.add(value.folder);assert(await alive(value.guard));return value.folder;
}
async function collectGuard(folder,trigger){
  const identity=JSON.parse(await readFile(path.join(folder,'identity.json'),'utf8'));
  const deadline=Date.now()+240000;let restored;
  while(true){
    try{restored=JSON.parse(await readFile(path.join(folder,'restored.json'),'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
    if(restored&&!await alive(identity.guard))break;
    assert(Date.now()<deadline,'guard_not_finished');await sleep(100);
  }
  assert(restored.completed);assert.equal(restored.trigger,trigger);
  const requested=await readFile(path.join(folder,'restore.request')).then(()=>true,error=>{if(error.code==='ENOENT')return false;throw error;});
  if(trigger==='owner_gone')assert(!requested,'independent_restore_required');
  const result={folder,identity,restoration:restored,guard_absent:true,explicit_restore_requested:requested};
  guards.push(result);pendingGuards.delete(folder);return result;
}
async function release(folder){await guard('release','--folder',folder);return collectGuard(folder,'explicit');}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
async function expectTwo(){
  const value=await catalogue();assert.equal(value.total,2);
  assert.deepEqual(value.items.map(row=>row.origin).sort(),[alias,base].sort());return value;
}
async function expectOne(){const value=await catalogue();assert.equal(value.total,1);assert.equal(value.items[0].origin,base);return value;}
async function recoverOwnedGuards(){
  const owners=[principalIdentity,...(pilotIdentity?[pilotIdentity]:[])];
  for(const name of await readdir(out)){
    if(!name.startsWith('invocation-route-guard-'))continue;
    const folder=path.join(out,name);let identity;
    try{identity=JSON.parse(await readFile(path.join(folder,'identity.json'),'utf8'));}catch{continue;}
    if(owners.some(owner=>identity.owner?.pid===owner.pid&&identity.owner?.birth===owner.birth)&&!guards.some(row=>row.folder===folder))pendingGuards.add(folder);
  }
}
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
  caller=await request.newContext({timeout:120000});
  session=await(await admin.get('/api/session')).json();assert(session.authenticated,'real_admin_session_required');
  assert.equal((await api('/api/functions?limit=1')).total,0,'quiet_installation_required');
  await health(base);await health(alias);
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix,description:nonce},status:201});
  service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'route-cycle-fixture',description:nonce},status:201});
  full=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'publish-route-fixture',rights:['read','create','update']},status:201})).token;tokens.push(full);
  work=await mkdtemp(path.join(out,'invocation-route-code-'));
  await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
  await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'routes'}));
  const manifest={service:service.name,provider:{name:'p2enjoy',runtime:'node24',minScale:0,maxScale:1,p2enjoy:{idle_seconds:1}},
    functions:{'route-entry':{handler:'handler.handler'}},package:{patterns:['!**','*.cjs','revision.json']}};
  await writeFile(path.join(work,'serverless.yml'),JSON.stringify(manifest));
  const deployed=await command('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',service.id],
    {env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:full}});
  assert.equal(deployed.code,0,'real_fixture_deployment');assert(!tokens.some(token=>deployed.stdout.includes(token)||deployed.stderr.includes(token)));
  const result=JSON.parse(deployed.stdout);assert(result.completed&&result.results.length===1);
  fn={id:result.results[0].function_id};revision=result.results[0].revision_id;assert(revision);
  read=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'invoke-route-fixture',rights:['read'],function_ids:[fn.id]},status:201})).token;tokens.push(read);
  await check('Deux vrais domaines : seconde page API de taille un et invocations Docker',async()=>{
    const first=await catalogue('?limit=1&offset=0'),second=await catalogue('?limit=1&offset=1');
    assert.equal(first.total,2);assert.equal(second.total,2);assert.equal(first.items.length,1);assert.equal(second.items.length,1);
    assert.equal(first.source.sha256,second.source.sha256);assert.notEqual(first.items[0].domain,second.items[0].domain);
    observations.push({scenario:'two-domain-api-pagination',first,second});await invokeEntry(first.items[0]);await invokeEntry(second.items[0]);
  });
  await check('Alias vers 18091 : exclusion réelle, HTTP 502 puis restauration explicite',async()=>{
    const folder=await arm();const changed=await guard('divert-alias','--folder',folder);assert(changed.completed);
    const reduced=await expectOne();await health(base);await health(alias,502);
    observations.push({scenario:'alias-diverted-explicit',changed,catalogue:reduced});await release(folder);
    await invokeFrom(await expectTwo(),alias);
  });
  await check('Pilote perdu après détour confirmé : restauration indépendante puis invocation',async()=>{
    await quiet();await health(base);await health(alias);
    pilot=spawn(process.execPath,[fileURLToPath(import.meta.url),'--diverted-owner-pilot'],{cwd:root,stdio:['ignore','pipe','pipe'],detached:true});
    pilotIdentity=await processIdentity(pilot.pid);assert(pilotIdentity?.running);
    pilotExit=new Promise(resolve=>pilot.once('exit',(code,signal)=>resolve({code,signal})));
    pilotLines=createInterface({input:pilot.stdout});
    pilotTerminal=new Promise(resolve=>{
      pilotLines.once('line',line=>{try{resolve(JSON.parse(line));}catch{resolve({event:'invalid-metadata'});}});
      pilotExit.then(exit=>resolve({event:'pilot-exited',exit}));
    });
    const armed=await bounded(pilotTerminal,30000,'pilot_not_ready');
    pilotChangeConfirmed=armed.event==='diverted'&&armed.change?.completed===true;
    assert(pilotChangeConfirmed,'pilot_mutator_terminal_confirmation_required');
    pilotLines.close();pilotLines=null;assert.deepEqual(armed.owner,pilotIdentity);assert(await alive(armed.guard));
    pendingGuards.add(armed.folder);const reduced=await expectOne();await health(alias,502);
    assert(pilot.kill('SIGKILL'));const ended=await pilotExit;assert.equal(ended.signal,'SIGKILL');assert.equal(ended.code,null);
    const restored=await collectGuard(armed.folder,'owner_gone');
    observations.push({scenario:'alias-diverted-owner-loss',change:armed.change,catalogue:reduced,pilot:pilotIdentity,pilot_exit:ended,restoration:restored.restoration});
    pilot=null;await invokeFrom(await expectTwo(),alias);
  });
  await check('Retrait et rétablissement réels : nouvel identifiant, même révision et invocation',async()=>{
    const folder=await arm(),before=await guard('inspect');
    const removed=await guard('remove-alias','--folder',folder);assert.equal(removed.after['functions.lelabs.tech'],null);
    const reduced=await expectOne();const recreated=await guard('recreate-alias','--folder',folder);
    assert.notEqual(recreated.after['functions.lelabs.tech'].id,before['functions.lelabs.tech'].id);
    observations.push({scenario:'alias-withdrawal-recreation',removed,recreated,catalogue:reduced});
    await release(folder);await invokeFrom(await expectTwo(),alias);
  });
  await check('Deux ports vers 18091 : catalogue vide du vrai HTTP local puis appels restaurés',async()=>{
    const folder=await arm(),changed=await guard('divert-both','--folder',folder);assert(changed.completed);
    const native=await command('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24',
      'python3','-B','/srv/p2enjoy-serverless/e2e/invocation-url-host.py'],{privateInput:JSON.stringify({function_id:fn.id,token:read})+'\n'});
    assert.equal(native.code,0);assert(!tokens.some(token=>native.stdout.includes(token)));
    const empty=JSON.parse(native.stdout);assert(empty.completed);assert.equal(empty.catalogue.source.state,'available');
    assert.equal(empty.catalogue.total,0);assert.deepEqual(empty.catalogue.items,[]);assert.equal(empty.catalogue.revision_id,revision);
    observations.push({scenario:'both-diverted-native-empty',changed,native:empty});
    await release(folder);const restored=await expectTwo();for(const item of restored.items)await invokeEntry(item);
  });
  completed=true;
}catch(error){failure={name:error.name};throw new Error('invocation_route_cycles_failed');}
finally{
  if(pilot){
    if(!pilotChangeConfirmed){
      const terminal=await bounded(pilotTerminal,900000,'pilot_mutator_terminal_unknown').catch(()=>null);
      pilotChangeConfirmed=terminal?.event==='diverted'&&terminal.change?.completed===true;
      if(pilotChangeConfirmed)pendingGuards.add(terminal.folder);
    }
    if(pilotChangeConfirmed){
      if(pilot.exitCode===null&&pilot.signalCode===null)pilot.kill('SIGKILL');
      await pilotExit;
    }else{
      // A missing terminal acknowledgement never authorizes killing an in-flight mutator.
      pilotMutationUnknown=true;
      await bounded(pilotExit,900000,'pilot_state_unknown').catch(()=>null);
      if(pilot.exitCode===null&&pilot.signalCode===null){pilot.unref();pilot.stdout.destroy();pilot.stderr.destroy();}
      cleanupErrors.push({resource:'pilot-mutator-unconfirmed',identity:pilotIdentity});
    }
    pilotLines?.close();pilotLines=null;
  }
  await recoverOwnedGuards();
  if(!pilotMutationUnknown)for(const folder of pendingGuards){try{await guard('release','--folder',folder);await collectGuard(folder,'explicit');}catch(error){cleanupErrors.push({resource:'guard',folder,error:error.name});}}
  let safe=false;
  try{const rows=await guard('inspect');assert(Object.values(rows).every(row=>row&&row.target_port===18090));await health(base);assert(!(await Promise.all(guards.map(row=>alive(row.identity.guard)))).some(Boolean));safe=!pilotMutationUnknown&&pendingGuards.size===0;}catch(error){cleanupErrors.push({resource:'routes',error:error.name});}
  if(safe&&admin&&session?.authenticated){
    try{
      if(!namespace){const found=await api('/api/catalogue/namespaces?q='+encodeURIComponent(prefix)+'&limit=50');namespace=found.items.find(row=>row.name===prefix&&row.description===nonce);}
      if(namespace&&!service){const found=await api(`/api/namespaces/${namespace.id}/services?limit=100`);service=found.items.find(row=>row.name==='route-cycle-fixture'&&row.description===nonce);}
      if(service){
        const rows=(await api(`/api/services/${service.id}/functions?limit=100`)).items;assert(rows.every(row=>row.name==='route-entry'));
        for(const row of rows){
          fn??={id:row.id};await api(`/api/functions/${row.id}`,{method:'DELETE'});const archived=await api(`/api/archives/${row.id}`);
          let operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',body:{operation_id:randomUUID(),confirm_name:archived.name},status:[200,202],headers:{'If-Match':String(archived.updated_at)}});
          const deadline=Date.now()+90000;
          while(operation.state!=='completed'){assert.notEqual(operation.state,'failed');assert(Date.now()<deadline);await sleep(200);operation=await api(`/api/storage-operations/${operation.id}`);}
          purged={function_id:row.id,operation_id:operation.id};
        }
        await api(`/api/services/${service.id}`,{method:'DELETE'});
      }
      if(namespace)await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});
    }catch(error){cleanupErrors.push({resource:'fixture',error:error.name});}
  }
  if(!safe)cleanupErrors.push({resource:'fixture-retained-until-restoration'});
  if(work&&!cleanupErrors.length)await rm(work,{recursive:true,force:true});
  await admin?.dispose();await caller?.dispose();
  const result={completed:completed&&!cleanupErrors.length,checks,observations,guards,invoked_addresses:invokedAddresses,operator_errors:operatorErrors,pilot_mutation_state_unknown:pilotMutationUnknown,skipped:0,
    cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,failure,prefix,ownership_nonce:nonce,
    namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],revision_id:revision,purged,work_retained:Boolean(work&&cleanupErrors.length)};
  const raw=JSON.stringify(result,null,2);assert(!tokens.some(token=>raw.includes(token)),'private_credential_in_report');
  await writeFile(reportPath,raw+'\n');assert.equal(cleanupErrors.length,0,'cleanup_required');
}
