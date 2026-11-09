// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#catalogue-public-sous-refus-de-lecture
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_SOURCE_PERMISSIONS.md#catalogue-public-sous-refus-de-lecture
// Real HTTPS catalogue, adapter publication, official-source EACCES and Docker invocations.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {createInterface} from 'node:readline';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',alias='https://functions.lelabs.tech';
const helper='/srv/p2enjoy-serverless/e2e/invocation-source-permissions.py';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const checks=[],observations=[],tasks=[],cleanupErrors=[],operatorErrors=[],tokens=[],invokedAddresses=[];
const nonce=randomUUID(),prefix='source-access-'+nonce.slice(0,8);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
// OpenSSH joins its command arguments through the remote shell; quote the JSON scope.
const quote=value=>"'"+String(value).replaceAll("'","'\\''")+"'";
let completed=false,failure,client,admin,session,namespace,service,fn,revision,work,full,read,baseline,task,purged;
await mkdir(out,{recursive:true,mode:0o700});const report=path.join(out,'invocation-source-api.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const image=JSON.parse(await readFile(path.join(root,'docs/evidence/invocation-source-guard-dev-2026-11-09.json'),'utf8')).control_image;
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
    const child=execFile(file,args,{cwd:root,timeout:300000,maxBuffer:2*1024*1024,...options},
      (error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr}));child.stdin.end();
  });
}
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),'platform_api_status');
  return response.json();
}
async function issue(name,rights){
  const result=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name,rights},status:201});
  tokens.push(result.token);return result;
}
async function catalogue(credential=read,status=200,asAdmin=false){
  const url=base+`/api/functions/${fn.id}/invocation-urls?limit=20`;
  const response=await (asAdmin?admin:client).get(url,{headers:credential?{'X-Serverless-Token':credential}:{}});
  assert.equal(response.status(),status,'catalogue_http_status');
  const raw=await response.text();assert(!tokens.some(token=>raw.includes(token)),'credential_disclosure');
  assert(!raw.includes('/etc/spark')&&!raw.includes('/spark/routes'),'internal_source_path_disclosure');
  return JSON.parse(raw);
}
function unavailable(value){
  assert.equal(value.source.state,'unavailable');assert.equal(value.source.error_code,'source_forbidden');
  assert.deepEqual(Object.keys(value.source).sort(),['error_code','observed_at','state']);
  assert.equal(typeof value.source.observed_at,'number');assert(Number.isFinite(value.source.observed_at));
  assert.equal(value.function_id,fn.id);assert.equal(value.service_id,service.id);assert.equal(value.revision_id,revision);
  assert.equal(value.function_state,'published');assert.equal(value.total,0);assert.deepEqual(value.items,[]);assert.deepEqual(value.wildcards,[]);
  assert.equal(value.console_url,base+`/console/functions/${fn.id}/invocation-urls`);
}
function available(value){
  assert.equal(value.source.state,'available');assert.equal(value.total,2);assert.equal(value.revision_id,revision);
  assert.deepEqual(value.items.map(row=>row.origin).sort(),[base,alias].sort());
  assert.equal(value.source.sha256,baseline?.source.sha256??value.source.sha256);
  if(baseline)assert.deepEqual(value.items,baseline.items);
}
async function invoke(item,phase){
  const entry=item.urls.find(row=>row.methods.includes('GET'));assert(entry);
  assert([base,alias].includes(item.origin));assert.equal(entry.url,item.origin+'/invoke/'+fn.id);
  const response=await client.get(entry.url,{headers:{'X-Serverless-Token':read}});
  assert.equal(response.status(),200,'real_docker_invocation');assert.equal((await response.json()).revision,'source-access');
  const requestId=response.headers()['x-serverless-request-id'];assert.match(requestId,/^[0-9a-f-]{36}$/);
  invokedAddresses.push({phase,url:entry.url,status:200,revision:'source-access',request_id:requestId});
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000,ignoreHTTPSErrors:false});
  client=await request.newContext({timeout:20000,ignoreHTTPSErrors:false});
  session=await(await admin.get('/api/session')).json();assert(session.authenticated,'real_admin_session_required');
  assert.equal((await api('/api/functions?limit=1')).total,0,'quiet_installation_required');
  await health();
  const deniedTokens=[];
  await check('Publication par adaptateur : une fonction possédée et deux domaines réels',async()=>{
    namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix,description:nonce},status:201});
    service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'source-access-fixture',description:nonce},status:201});
    full=(await issue('publish-source-fixture',['read','create','update'])).token;
    work=await mkdtemp(path.join(out,'invocation-source-code-'));
    await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
    await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'source-access'}));
    const manifest={service:service.name,provider:{name:'p2enjoy',runtime:'node24',minScale:0,maxScale:1,p2enjoy:{idle_seconds:1}},
      functions:{'source-access-entry':{handler:'handler.handler'}},package:{patterns:['!**','*.cjs','revision.json']}};
    await writeFile(path.join(work,'serverless.yml'),JSON.stringify(manifest));
    const result=await command('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',service.id],
      {env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:full}});
    assert.equal(result.code,0,'real_fixture_deployment');assert(!tokens.some(token=>result.stdout.includes(token)||result.stderr.includes(token)));
    const deployed=JSON.parse(result.stdout);assert(deployed.completed&&deployed.results.length===1);
    fn={id:deployed.results[0].function_id};revision=deployed.results[0].revision_id;assert(revision);
    const issued=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'invoke-source-fixture',rights:['read'],function_ids:[fn.id]},status:201});
    read=issued.token;tokens.push(read);
    for(const right of ['create','update','delete'])deniedTokens.push({right,token:(await issue('without-read-'+right,[right])).token,status:403});
    const revoked=await issue('revoked-source-reader',['read']);await api(`/api/tokens/${revoked.id}/revoke`,{method:'POST'});
    deniedTokens.push({right:'revoked',token:revoked.token,status:401});
    baseline=await catalogue();available(baseline);observations.push({scenario:'before-fault',catalogue:baseline});
  });
  await check('EACCES réel : diagnostic borné pour Read/admin et refus sans divulgation',async()=>{
    task=start('release',{namespace_id:namespace.id,function_id:fn.id,nonce});
    const active=await task.wait('fault-active');assert.equal(active.control_open.errno,13);assert.equal(active.source.mode,0);
    const tokenPage=await catalogue(),adminPage=await catalogue(null,200,true);unavailable(tokenPage);unavailable(adminPage);
    observations.push({scenario:'permission-denied',catalogue:tokenPage,admin_catalogue:adminPage});
    const refusals=[{right:'anonymous',token:null,status:401},{right:'invalid',token:'invalid-token',status:401},...deniedTokens];
    for(const row of refusals){
      const denied=await catalogue(row.token,row.status);assert(!('source' in denied)&&!('items' in denied)&&!('revision_id' in denied));
      observations.push({scenario:'authorization-before-source',right:row.right,status:row.status,response:denied});
    }
    await health();
  });
  await check('Source refusée : les deux URL connues invoquent réellement Docker',async()=>{
    for(const item of baseline.items)await invoke(item,'during-fault');
    const denied=await catalogue();unavailable(denied);observations.push({scenario:'after-invocations-under-fault',catalogue:denied});
  });
  await check('Restitution explicite : même catalogue, même révision et appels réels',async()=>{
    task.send('release');const restored=await task.finish();assert.equal(restored.restoration.independent,false);
    assert.deepEqual(restored.restoration.identity.scope,{namespace_id:namespace.id,function_id:fn.id,nonce});
    const normal=await catalogue();available(normal);observations.push({scenario:'restored',catalogue:normal});
    await health();for(const item of normal.items)await invoke(item,'after-restoration');
  });
  completed=true;
}catch(error){failure={name:error.name,message:error.message};throw new Error('invocation_source_api_failed');}
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
  await admin?.dispose();await client?.dispose();
  const raw=JSON.stringify({completed:completed&&!cleanupErrors.length,cleanup:!cleanupErrors.length,checks,skipped:0,observations,
    tasks:tasks.map(current=>current.receipt??current.diagnostic()),failure,cleanup_errors:cleanupErrors,operator_errors:operatorErrors,
    prefix,ownership_nonce:nonce,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],revision_id:revision,
    invoked_addresses:invokedAddresses,purged,work_retained:Boolean(work&&cleanupErrors.length),route_changes:0},null,2);
  assert(!tokens.some(token=>raw.includes(token)),'credential_in_report');await writeFile(report,raw+'\n');
  assert.equal(cleanupErrors.length,0,'source_permission_cleanup_required');
}
