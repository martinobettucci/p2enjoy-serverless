// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli
// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#révocation-avant-le-get-facultatif
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#révocation-avant-le-get-facultatif
// All helpers exercise the real CLI, native control process and public HTTPS API.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {createHash,randomUUID} from 'node:crypto';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',prefix='invocation-url-transport-'+randomUUID().slice(0,8);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/service-transport-observer.py';
const checks=[],observations=[],gates=[],services=[],archives=[],cleanupErrors=[],credentials=[];
const digest=value=>createHash('sha256').update(value).digest('hex');
await mkdir(out,{recursive:true,mode:0o700});
const report=path.join(out,'invocation-url-transport.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
const caller=await request.newContext({baseURL:base,timeout:120000});
let session,namespace,work,completed=false,activeTask;

async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),method+' '+url+': '+response.status());
  const text=await response.text();for(const token of credentials)assert(!text.includes(token),'Identifiant exposé');
  return JSON.parse(text);
}
async function until(action,message,timeout=40000){
  const end=Date.now()+timeout;
  while(Date.now()<end){const result=await action();if(result)return result;await new Promise(resolve=>setTimeout(resolve,100));}
  assert.fail(message);
}
async function remote(mode,service,extra=[]){
  const tail=['inspect'].includes(mode)?[service.function.id,...extra]:extra;
  return new Promise((resolve,reject)=>execFile('ssh',[...ssh,'python3','-B',helper,mode,service.id,namespace.id,...tail],
    {timeout:200000,maxBuffer:2*1024*1024},(error,stdout,stderr)=>error?reject(new Error('observer_operator_failed: '+stderr.slice(-700))):resolve(JSON.parse(stdout.trim().split('\n').at(-1)))));
}
async function gate(mode,service){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,'catalogue-'+mode,service.id,namespace.id,service.function.id],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,exitCode=null,stderr='';
  createInterface({input:child.stdout}).on('line',line=>events.push(JSON.parse(line)));
  child.stderr.on('data',bytes=>{stderr+=bytes.toString();});child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{child.on('close',code=>{ended=true;exitCode=code;resolve(code);});child.on('error',()=>{ended=true;exitCode=-1;resolve(-1);});});
  const value={service,events,restored:false,
    async wait(name){return until(()=>{const event=events.find(row=>row.event===name);assert(event||!ended,`Observateur terminé : ${exitCode}; ${stderr.slice(-700)}`);return event;},'Barrière native absente : '+name);},
    send(command){child.stdin.write(command+'\n');},
    async finish(){assert.equal(await done,0,'Fin de l’observateur');const restored=events.find(row=>row.event==='restored');assert(restored?.healthy&&restored.reference_unchanged);value.restored=true;return restored;},
    async recover(){
      if(!ended){child.stdin.end();await done;}
      const armed=events.find(row=>row.event==='guard-armed');
      if(armed)await remote('restore',service,[armed.unit]);
      value.restored=true;
    },
    async independent(){
      assert([137,255].includes(await done),'Fin de SSH après perte du pilote');
      assert(events.some(row=>row.event==='observer-loss'&&row.signal==='SIGKILL'),'SIGKILL natif demandé');
      const armed=events.find(row=>row.event==='armed');assert(armed);
      const event=await until(async()=>{const row=await remote('evidence',service,[armed.unit]);return row.event==='restored'?row:false;},'Garde indépendante absente',30000);
      assert(event.independent&&event.observer_gone&&event.healthy&&event.reference_unchanged&&event.stop_mutator_joined);
      await remote('restore',service,[armed.unit]);value.restored=true;return {...event,ssh_exit_code:exitCode};
    }};
  gates.push(value);await value.wait('armed');return value;
}
async function createService(name){
  const row=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name},status:201});services.push(row);
  row.function=await api(`/api/services/${row.id}/functions`,{method:'POST',body:{name:'durable-publication',config:{handler:'handler.handler'}},status:201});return row;
}
async function token(service,name,rights){
  const row=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name,rights},status:201});credentials.push(row.token);return row.token;
}
async function startDeployment(service,credential,{refusal=false}={}){
  const config=path.join(work,'serverless.yml');
  await writeFile(config,JSON.stringify({service:service.name,provider:{name:'p2enjoy',runtime:'node24',p2enjoy:{idle_seconds:0}},
    functions:{'durable-publication':{handler:'handler.handler'}},package:{patterns:['!**','*.cjs','revision.json']}}));
  const tracePath=path.join(work,'https-connect.trace'),args=['-f','-qq','-e','trace=connect,getsockopt','-s','0','-o',tracePath,
    'python3','-B','-m','adapter','deploy','--config',config,'--service',service.id];
  const nativeEvents=[];
  const task={settled:false,groupConfirmedGone:false,async result(){
    const value=await task.done;task.settled=true;assert(task.groupConfirmedGone,'Fin du groupe CLI non confirmée');assert.equal(value.code,0,'Code de sortie CLI');
    const finished=refusal?nativeEvents.find(row=>row.event==='finished'):null;
    if(refusal)assert(finished?.child_reaped&&finished.exit_code===0&&finished.connect_results.length===6&&nativeEvents.some(row=>row.event==='armed'&&row.exitkill),'Fin native de la vraie CLI');
    const cliStdout=refusal?finished.stdout:value.stdout,cliStderr=refusal?finished.stderr:value.stderr;
    const native=refusal?JSON.stringify(nativeEvents):await readFile(tracePath,'utf8');
    for(const token of credentials)assert(!value.stdout.includes(token)&&!value.stderr.includes(token)&&!native.includes(token),'Identifiant exposé');
    assert(!cliStderr.includes('Traceback'));const result=JSON.parse(cliStdout);assert.equal(result.completed,true);
    let attempts;
    if(refusal){attempts=finished.https_connect_attempts;assert(finished.connect_results.every(value=>[0,-115].includes(value)));}
    else{
      const lines=native.split('\n').filter(line=>line.includes('connect(')&&line.includes('htons(443)'));
      const connections=lines.filter(line=>/ = 0$| = -1 EINPROGRESS /.test(line));
      assert.equal(lines.length,connections.length,'Aucune tentative HTTPS supplémentaire refusée');attempts=lines.length;
    }
    assert.equal(attempts,6,'Lectures service/liste/fonction, préparation, upload et catalogue sans rejeu');
    observations.push({scenario:'native-cli-connections',service_id:service.id,function_id:service.function.id,
      https_connect_attempts:attempts,expected_read_requests:4,expected_mutation_attempts:2,
      observer_kind:refusal?'child-ptrace':'strace',exitkill:refusal,
      cli_process_group_confirmed_gone:task.groupConfirmedGone,trace_sha256:digest(native)});
    return result;
  }};
  task.diagnostic=async()=>{
    const value=await task.done;
    const safe=!credentials.some(token=>value.stdout.includes(token)||value.stderr.includes(token));
    const result={exit_code:value.code,group_confirmed_gone:task.groupConfirmedGone,stdout_sha256:digest(value.stdout),stderr_sha256:digest(value.stderr),credential_exposure_detected:!safe};
    if(safe){
      try{result.cli_result=JSON.parse(refusal?nativeEvents.find(row=>row.event==='finished')?.stdout:value.stdout);}
      catch{result.cli_result_unreadable=true;}
      if(refusal)result.native_events=nativeEvents;
      else try{
        const native=await readFile(tracePath,'utf8');
        assert(!credentials.some(token=>native.includes(token)));
        result.https_connect_attempts=native.split('\n').filter(line=>line.includes('connect(')&&line.includes('htons(443)')).length;
        result.native_trace_sha256=digest(native);
      }catch{result.native_trace_unavailable=true;}
    }
    return result;
  };
  const child=spawn(refusal?'python3':'strace',refusal?['-B',path.join(root,'e2e/adapter-catalogue-barrier.py'),config,service.id]:args,
    {cwd:root,detached:true,stdio:['pipe','pipe','pipe'],
    env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:credential}});
  child.stdin.on('error',()=>{});
  if(refusal){
    createInterface({input:child.stdout}).on('line',line=>{
      try{nativeEvents.push(JSON.parse(line));}catch{nativeEvents.push({event:'protocol-error'});}
    });
    task.waitGate=()=>until(()=>{assert(!nativeEvents.some(row=>row.event==='protocol-error'));return nativeEvents.find(row=>row.event==='gated');},'Barrière CLI absente',60000);
    task.release=()=>child.stdin.write('release\n');
  }
  task.processGroup=child.pid;
  let stdout='',stderr='',expired=false,overflow=false;
  const groupAlive=()=>{
    try{process.kill(-child.pid,0);return true;}
    catch(error){if(error.code==='ESRCH')return false;throw error;}
  };
  const killGroup=()=>{try{process.kill(-child.pid,'SIGKILL');}catch(error){if(error.code!=='ESRCH')throw error;}};
  const timer=setTimeout(()=>{expired=true;killGroup();},300000);
  const collect=(field,bytes)=>{
    if(field==='stdout')stdout+=bytes.toString();else stderr+=bytes.toString();
    if(stdout.length+stderr.length>4*1024*1024){overflow=true;killGroup();}
  };
  child.stdout.on('data',bytes=>collect('stdout',bytes));child.stderr.on('data',bytes=>collect('stderr',bytes));
  task.done=new Promise(resolve=>{
    child.once('error',()=>{clearTimeout(timer);resolve({code:1,stdout,stderr});});
    child.once('close',async code=>{
      clearTimeout(timer);
      try{
        // A tracer exit is insufficient: wait for the entire isolated group.
        await until(()=>!groupAlive(),'Groupe CLI encore présent',10000);task.groupConfirmedGone=true;
      }catch{task.groupConfirmedGone=false;}
      resolve({code:expired||overflow?1:code??1,stdout,stderr,expired,overflow});
    });
  });
  activeTask=task;return task;
}
async function purge(service){
  const rows=(await api(`/api/services/${service.id}/functions`)).items;
  assert(rows.length<=1&&rows.every(row=>row.name==='durable-publication'),'Inventaire possédé exact');
  // Recover an accepted creation whose response was lost, by exact service/name.
  if(!service.function&&rows.length)service.function=rows[0];
  if(service.function){
    const row=service.function;assert(rows.every(item=>item.id===row.id),'UUID de fonction possédé exact');
    if(rows.length){
      await until(async()=>!(await api(`/api/functions/${row.id}/instances`)).items.length,'Instance encore active');
      await api(`/api/functions/${row.id}`,{method:'DELETE'});
    }
    let archived=await api(`/api/archives/${row.id}`);
    if(!archived.purged_at){
      service.purgeId??=archived.storage_operation?.id??randomUUID();
      let operation;
      const observed=await api(`/api/storage-operations/${service.purgeId}`,{status:[200,404]});
      if(observed.id)operation=observed;
      else operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archived.updated_at)},body:{operation_id:service.purgeId,confirm_name:archived.name}});
      await until(async()=>{const result=await api(`/api/storage-operations/${operation.id}`);assert.notEqual(result.state,'failed');return result.state==='completed';},'Purge inachevée',90000);
      archived=await api(`/api/archives/${row.id}`);
    }
    assert(archived.purged_at&&archived.artifact_bytes===0&&!archived.storage_operation);
    if(!archives.some(item=>item.function_id===row.id))archives.push({namespace_id:namespace.id,function_id:row.id,operation_id:service.purgeId??null,purged:true});
  }
  await api(`/api/services/${service.id}`,{method:'DELETE'});service.cleaned=true;
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
try{
  session=await api('/api/session');assert(session.authenticated,'Session SSO requise');
  work=await mkdtemp(path.join(out,'invocation-url-transport-code-'));
  await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
  await writeFile(path.join(work,'revision.json'),JSON.stringify({name:prefix}));
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix},status:201});
  await check('Observateur de catalogue perdu : restauration indépendante, brouillon intact',async()=>{
    const service=await createService('observer-recovery'),held=await gate('watchdog',service);
    await held.wait('suspended');held.send('lose-observer');const restored=await held.independent();
    const state=await remote('inspect',service);assert.equal(state.candidates,0);assert.equal(state.publication.active_revision_id,null);
    observations.push({scenario:'observer-loss',events:held.events,restored,durable:state});await purge(service);
  });
  for(const boundary of ['before','after']){
    await check(`GET catalogue coupé ${boundary==='before'?'après réception':'avant émission'} : publication conservée sans rejeu`,async()=>{
      const service=await createService('catalogue-'+boundary),credential=await token(service,'deployment',['read','create','update']);
      const held=await gate(boundary,service),task=await startDeployment(service,credential),gated=await held.wait('gated');
      assert.equal(gated.boundary,boundary==='before'?'after-receive':'before-send');
      assert.equal(gated.durable.publication.deploy_audits,1);held.send('cut');assert.equal((await held.wait('cut')).exit_code,137);
      const restored=await held.finish(),result=await task.result(),state=await remote('inspect',service);
      assert.equal(result.service_configuration.state,'preserved');assert.equal(result.results.length,1);
      const published=result.results[0];assert.equal(published.state,'published');assert.equal(published.function_id,service.function.id);
      assert.equal(published.deployment_id,state.publication.candidates[0].id);assert.equal(published.revision_id,state.publication.active_revision_id);
      assert.equal(published.invocation_urls.state,'unavailable');assert(!published.error);
      assert(['http_502','network_error'].includes(published.invocation_urls.error.code),'Diagnostic réel de coupure attendu');
      assert.deepEqual(state,gated.durable,'Une seule publication et même archive après reprise');
      const read=await token(service,'invocation',['read']);
      const catalogue=await caller.get(`/api/functions/${service.function.id}/invocation-urls?limit=5&offset=0`,{headers:{'X-Serverless-Token':read}});
      assert.equal(catalogue.status(),200);const addresses=await catalogue.json();assert.equal(addresses.revision_id,published.revision_id);
      assert.equal(addresses.source.state,'available');const entry=addresses.items.find(row=>row.origin===base);assert(entry);
      const response=await caller.get(entry.urls[0].url,{headers:{'X-Serverless-Token':read}});assert.equal(response.status(),200);
      assert.equal((await response.json()).revision,prefix);
      const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));
      assert.equal(descriptor.artifacts['durable-publication'].sha256,state.publication.archive_sha256);
      observations.push({scenario:boundary,service_id:service.id,function_id:service.function.id,events:held.events,restored,
        report:result,durable:state,catalogue:addresses,invocation_status:response.status()});await purge(service);
    });
  }
  await check('Jeton révoqué après publication : vrai GET 401, publication conservée sans rejeu',async()=>{
    const service=await createService('catalogue-revoked');
    const credential=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'deployment-to-revoke',rights:['read','create','update']},status:201});
    credentials.push(credential.token);
    const task=await startDeployment(service,credential.token,{refusal:true}),barrier=await task.waitGate();
    assert.equal(barrier.boundary,'before-sixth-https-connect');assert.equal(barrier.https_connect_attempts,6);
    const before=await remote('inspect',service);assert.equal(before.publication.deploy_audits,1);
    assert.equal(before.publication.candidates[0].state,'published');assert.equal(before.publication.revisions.length,1);
    await api(`/api/tokens/${credential.id}/revoke`,{method:'POST'});
    const denied=await caller.get(`/api/functions/${service.function.id}/invocation-urls`,{headers:{'X-Serverless-Token':credential.token}});
    assert.equal(denied.status(),401);task.release();
    const result=await task.result(),state=await remote('inspect',service);assert.deepEqual(state,before);
    assert.equal(result.service_configuration.state,'preserved');assert.equal(result.results.length,1);
    const published=result.results[0];assert.equal(published.state,'published');assert.equal(published.function_id,service.function.id);
    assert.equal(published.revision_id,state.publication.active_revision_id);assert.equal(published.deployment_id,state.publication.candidates[0].id);
    assert.deepEqual(published.invocation_urls,{state:'unavailable',error:{code:'http_401',status:401}});assert(!published.error);
    const read=await token(service,'invocation-after-revocation',['read']);
    const catalogue=await caller.get(`/api/functions/${service.function.id}/invocation-urls?limit=5&offset=0`,{headers:{'X-Serverless-Token':read}});
    assert.equal(catalogue.status(),200);const addresses=await catalogue.json();assert.equal(addresses.revision_id,published.revision_id);
    const entry=addresses.items.find(row=>row.origin===base);assert(entry);
    const response=await caller.get(entry.urls[0].url,{headers:{'X-Serverless-Token':read}});assert.equal(response.status(),200);assert.equal((await response.json()).revision,prefix);
    const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));
    assert.equal(descriptor.artifacts['durable-publication'].sha256,state.publication.archive_sha256);
    observations.push({scenario:'revoked-before-catalogue',service_id:service.id,function_id:service.function.id,token_id:credential.id,
      barrier,revocation_confirmed_status:denied.status(),report:result,durable:state,catalogue:addresses,invocation_status:response.status()});
    await purge(service);
  });
  completed=true;
}finally{
  for(const held of gates)if(!held.restored)try{await held.recover();}catch(error){cleanupErrors.push({resource:'observer',error:error.name});}
  if(activeTask&&!activeTask.settled)await activeTask.done;
  const cliDiagnostic=activeTask?await activeTask.diagnostic():null;
  const cliGone=!activeTask||activeTask.groupConfirmedGone;
  if(!cliGone)cleanupErrors.push({resource:'cli-process-group',error:'state_unknown_cleanup_blocked'});
  if(session?.authenticated&&cliGone&&gates.every(row=>row.restored)){
    for(const service of services)if(!service.cleaned)try{await purge(service);}catch(error){cleanupErrors.push({resource:service.id,error:error.name});}
    if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'namespace',error:error.name});}
  }
  if(work&&cliGone)await rm(work,{recursive:true,force:true});
  await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({target:base,completed:completed&&!cleanupErrors.length,checks,observations,skipped:0,cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,
    cli_diagnostic:cliDiagnostic,observer_diagnostics:gates.map(row=>({service_id:row.service.id,events:row.events,restored:row.restored})),
    cli_process_group:activeTask?{id:activeTask.processGroup,confirmed_gone:activeTask.groupConfirmedGone}:null,
    work_retained:!!work&&!cliGone,namespace_id:namespace?.id,service_ids:services.map(row=>row.id),function_ids:archives.map(row=>row.function_id),storage_archives:archives},null,2)+'\n');
}
assert(completed&&!cleanupErrors.length);
