// @spec docs/BACKLOG.md#sls-108 | docs/SERVICE_TRANSPORT_REGRESSIONS.md
// @verifies docs/BACKLOG.md#sls-108 | docs/SERVICE_TRANSPORT_REGRESSIONS.md
// @spec docs/BACKLOG.md#sls-142 | docs/SERVICE_TRANSPORT_REGRESSIONS.md#diagnostic-de-lacquisition-courante--sls-142
// @verifies docs/BACKLOG.md#sls-142 | docs/SERVICE_TRANSPORT_REGRESSIONS.md#diagnostic-de-lacquisition-courante--sls-142
// @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
// @verifies docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
// All helpers exercise the real CLI, native control process and public HTTPS API.
import assert from 'node:assert/strict';
import {readFile,writeFile,rename,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {createHash,randomUUID} from 'node:crypto';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',prefix='service-transport-'+randomUUID().slice(0,8);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/service-transport-observer.py';
const checks=[],observations=[],gates=[],services=[],archives=[],cleanupErrors=[],credentials=[];
const secret=randomUUID()+randomUUID(),digest=value=>createHash('sha256').update(value).digest('hex');
await mkdir(out,{recursive:true,mode:0o700});
const report=path.join(out,'service-transport.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n',{mode:0o600});
const admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
const caller=await request.newContext({baseURL:base,timeout:120000});
let session,namespace,work,completed=false,cleanupFinished=false,activeTask;

async function save(){
  const value={target:base,completed:completed&&cleanupFinished&&!cleanupErrors.length,checks,observations,skipped:0,cleanup:cleanupFinished&&!cleanupErrors.length,cleanup_errors:cleanupErrors,
    namespace_id:namespace?.id,service_ids:services.map(row=>row.id),function_ids:archives.map(row=>row.function_id),storage_archives:archives,
    native_gates:gates.map(held=>({service_id:held.service.id,mode:held.mode,events:held.events,restored:held.restored,helper_transport:held.transport}))};
  const text=JSON.stringify(value,null,2);for(const value of [secret,...credentials])assert(!text.includes(value),'Identifiant dans le rapport');
  await writeFile(report+'.pending',text+'\n',{mode:0o600});await rename(report+'.pending',report);
}

async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),method+' '+url+': '+response.status());
  const text=await response.text();assert(!text.includes(secret),'Secret exposé');
  return JSON.parse(text);
}
async function until(action,message,timeout=40000){
  const end=Date.now()+timeout;
  while(Date.now()<end){const result=await action();if(result)return result;await new Promise(resolve=>setTimeout(resolve,100));}
  assert.fail(message);
}
async function remote(mode,service,extra=[]){
  return new Promise((resolve,reject)=>execFile('ssh',[...ssh,'python3','-B',helper,mode,service.id,namespace.id,...extra],
    {timeout:200000,maxBuffer:1024*1024},(error,stdout,stderr)=>error?reject(new Error('observer_operator_failed: '+stderr.slice(-1000))):resolve(JSON.parse(stdout.trim().split('\n').at(-1)))));
}
async function gate(mode,service){
  const transport={started_at_ms:Date.now(),closed_at_ms:null,exit_code:null,joined:false,stderr_bytes:0,stderr_sha256:null,stderr_excerpt:''};
  const stderrHash=createHash('sha256');
  const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,service.id,namespace.id],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,exitCode=null,stderr='';
  createInterface({input:child.stdout}).on('line',line=>events.push(JSON.parse(line)));
  const safeStderr=()=>{let text=stderr;for(const value of [secret,...credentials])text=text.replaceAll(value,'[redacted]');return text;};
  child.stderr.on('data',bytes=>{stderrHash.update(bytes);transport.stderr_bytes+=bytes.length;stderr+=bytes.toString();});child.stdin.on('error',()=>{});
  child.on('error',error=>{transport.spawn_error=error.code??error.name;});
  const done=new Promise(resolve=>{child.on('close',code=>{ended=true;exitCode=code;Object.assign(transport,{closed_at_ms:Date.now(),exit_code:code,joined:true,stderr_sha256:stderrHash.digest('hex'),stderr_excerpt:safeStderr().slice(-4096)});resolve(code);});});
  const value={service,mode,events,transport,restored:false,
    async wait(name){return until(()=>{const event=events.find(row=>row.event===name);assert(event||!ended,`Observateur terminé : ${exitCode}; ${safeStderr().slice(-700)}`);return event;},'Barrière native absente : '+name);},
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
  const row=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name},status:201});services.push(row);return row;
}
async function token(service,name,rights){
  const row=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name,rights},status:201});credentials.push(row.token);return row.token;
}
async function startDeployment(service,credential,label,trace=false){
  const config=path.join(work,'serverless.yml');
  await writeFile(config,JSON.stringify({service:service.name,provider:{name:'p2enjoy',runtime:'node24',env:{SHARED_LABEL:label},secret:{SHARED_SECRET:'${env:SHARED_SECRET}'},p2enjoy:{idle_seconds:0}},
    functions:{'transport-inheritance':{handler:'handler.handler'}},package:{patterns:['!**','*.cjs']}}));
  let observation;
  const task={settled:false,expectedSuccess:null,async observe(){
    if(observation)return observation;
    observation=(async()=>{
    const value=await task.done;task.settled=true;
    for(const credential of [secret,...credentials])assert(!value.stdout.includes(credential)&&!value.stderr.includes(credential),'Identifiant exposé');
    observations.push({scenario:'cli-deploy-exit',service_id:service.id,expected_success:task.expectedSuccess,observation_context:task.expectedSuccess===null?'finally-without-result-oracle':'result-oracle',exit_code:value.code,stdout_sha256:digest(value.stdout),stderr_sha256:digest(value.stderr)});await save();
    let result,parseError;
    try{result=JSON.parse(value.stdout);observations.push({scenario:'cli-deploy-result',service_id:service.id,expected_success:task.expectedSuccess,report:result});}
    catch(error){parseError=error;observations.push({scenario:'cli-deploy-result-unparseable',service_id:service.id,error_type:error.name,stdout_sha256:digest(value.stdout)});}
    await save();let native;
    if(trace){
      const traceText=await readFile(tracePath,'utf8');
      for(const credential of [secret,...credentials])assert(!traceText.includes(credential),'Identifiant dans la trace native');
      const preserved=path.join(out,'service-transport-cli-connections-'+service.id+'.trace');await writeFile(preserved,traceText,{flag:'wx',mode:0o600});
      const attempts=traceText.split('\n').filter(line=>line.includes('connect(')&&line.includes('htons(443)'));
      const connections=attempts.filter(line=>/ = 0$| = -1 EINPROGRESS /.test(line));
      observations.push({scenario:'native-cli-connections',service_id:service.id,https_connect_attempts:attempts.length,https_connections:connections.length,
        expected_read_requests:task.expectedSuccess===null?null:2,expected_mutation_attempts:task.expectedSuccess===null?null:1,trace_path:preserved,trace_bytes:Buffer.byteLength(traceText),trace_sha256:digest(traceText)});await save();
      native={attempts:attempts.length,connections:connections.length};
    }
    return {value,result,parseError,native};})();return observation;
  },async result(success){
    task.expectedSuccess=success;const {value,result,parseError,native}=await task.observe();
    assert.equal(value.code,success?0:1,'Code de sortie CLI');assert(!value.stderr.includes('Traceback'));
    if(parseError)throw parseError;assert.equal(result.completed,success);
    if(trace){assert.equal(native.connections,3,'Deux lectures et une seule tentative de mutation HTTPS');assert.equal(native.attempts,native.connections,'Aucune autre tentative HTTPS');}
    return result;
  }};
  const tracePath=path.join(work,'https-connect.trace'),args=['-B','-m','adapter','deploy','--config',config,'--service',service.id];
  task.done=new Promise(resolve=>execFile(trace?'strace':'python3',trace?['-f','-qq','-e','trace=connect,getsockopt','-s','0','-o',tracePath,'python3',...args]:args,
    {cwd:root,timeout:300000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:credential,SHARED_SECRET:secret}},
    (error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr})));
  activeTask=task;return task;
}
async function promote(credential,published,boundary){
  const value=await new Promise(resolve=>execFile('python3',['-B','-m','adapter','promote','--function',published.function_id,'--code-hash',published.code_hash],
    {cwd:root,timeout:60000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:credential}},
    (error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr})));
  for(const privateValue of [secret,...credentials])assert(!value.stdout.includes(privateValue)&&!value.stderr.includes(privateValue),'Identifiant exposé par promote');
  observations.push({scenario:boundary+'-promotion-exit',exit_code:value.code,stdout_sha256:digest(value.stdout),stderr_sha256:digest(value.stderr)});await save();
  assert.equal(value.code,0);const result=JSON.parse(value.stdout);observations.push({scenario:boundary+'-explicit-promotion',report:result});await save();
  assert(result.completed);assert.equal(result.state,'promoted');assert.equal(result.function_id,published.function_id);assert.equal(result.code_hash,published.code_hash);assert.equal(result.revision_id,published.revision_id);assert.equal(result.changed,true);return result;
}

async function purge(service){
  const rows=(await api(`/api/services/${service.id}/functions`)).items;
  for(const row of rows){
    await until(async()=>!(await api(`/api/functions/${row.id}/instances`)).items.length,'Instance encore active');
    await api(`/api/functions/${row.id}`,{method:'DELETE'});
    const archived=await api(`/api/archives/${row.id}`);
    const operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archived.updated_at)},body:{operation_id:randomUUID(),confirm_name:archived.name}});
    await until(async()=>{const result=await api(`/api/storage-operations/${operation.id}`);assert.notEqual(result.state,'failed');return result.state==='completed';},'Purge inachevée',90000);
    const final=await api(`/api/archives/${row.id}`);assert(final.purged_at&&final.artifact_bytes===0&&!final.storage_operation);
    archives.push({namespace_id:namespace.id,function_id:row.id,operation_id:operation.id,purged:true});
  }
  await api(`/api/services/${service.id}`,{method:'DELETE'});service.cleaned=true;
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}
  catch(error){checks.push({name,status:'failed',error:error.name});await save();throw error;}
}
try{
  session=await api('/api/session');assert(session.authenticated,'Session SSO requise');
  work=await mkdtemp(path.join(out,'service-transport-code-'));
  await cp(path.join(root,'qualification/artifacts/service-configuration.cjs'),path.join(work,'handler.cjs'));
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix},status:201});
  await check('Perte de l’observateur suspendu : restauration indépendante et contrôle sain',async()=>{
    const service=await createService('observer-recovery');const held=await gate('watchdog',service);
    await held.wait('suspended');held.send('lose-observer');
    const restored=await held.independent();observations.push({scenario:'observer-loss',events:held.events,restored});
    assert.equal((await remote('inspect',service)).mutations,0);await purge(service);
  });
  for(const boundary of ['before','after']){
    await check(`Réponse perdue ${boundary==='before'?'avant traitement':'après commit'} : issue inconnue, sans rejeu ni publication`,async()=>{
      const service=await createService('configuration-'+boundary),credential=await token(service,'deployment',['read','create','update']);
      const label='transport-'+boundary+'-'+randomUUID().slice(0,8),held=await gate(boundary,service);
      const task=await startDeployment(service,credential,label,true),gated=await held.wait('gated');
      assert.equal(gated.boundary,boundary==='before'?'after-receive':'before-send');
      held.send('cut');const cut=await held.wait('cut');assert.equal(cut.exit_code,137);
      const restored=await held.finish(),result=await task.result(false),state=await remote('inspect',service);
      assert.equal(result.service_configuration.state,'unknown');assert.deepEqual(result.results,[]);
      assert.equal(state.mutations,boundary==='before'?0:1);assert.equal(state.functions,0);assert.equal(state.candidates,0);
      assert.equal(state.environment_sha256,gated.durable.environment_sha256);
      assert.deepEqual((await api(`/api/services/${service.id}`)).environment,boundary==='before'?{}:{SHARED_LABEL:label});
      observations.push({scenario:boundary,service_id:service.id,events:held.events,restored,report:result,durable:state});
      await check(`Relance explicite après coupure ${boundary} : publication, promotion et invocation Docker`,async()=>{
        const retry=await startDeployment(service,credential,label),published=await retry.result(true);
        assert.equal(published.service_configuration.state,'applied');assert.equal(published.results.length,1);
        const functions=(await api(`/api/services/${service.id}/functions`)).items;assert.equal(functions.length,1);const fn=functions[0],publication=published.results[0];
        const catalogue=await api(`/api/functions/${fn.id}/versions?limit=100`),read=await token(service,'invocation',['read']);
        const pilotResponse=await caller.get(`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':read}}),pilotBody=await pilotResponse.json();
        observations.push({scenario:boundary+'-pilot-before-promotion',function_id:fn.id,publication,active_revision_id:fn.active_revision_id,active_code_hash:catalogue.active_code_hash,first_promoted_at:catalogue.first_promoted_at,status:pilotResponse.status(),response:pilotBody});await save();
        assert.equal(publication.function_id,fn.id);assert.equal(publication.state,'published');assert.match(publication.code_hash,/^[0-9a-f]{64}$/);assert.equal(fn.active_revision_id,null);assert.equal(catalogue.active_code_hash,null);assert.equal(catalogue.first_promoted_at,null);assert.equal(pilotResponse.status(),409);assert.equal(pilotBody.error,'function_not_deployed');
        const promoted=await promote(credential,publication,boundary),selected=await api(`/api/functions/${fn.id}`);assert.equal(selected.active_revision_id,promoted.revision_id);
        const response=await caller.get(`/invoke/${fn.id}`,{headers:{'X-Serverless-Token':read}}),body=await response.json();
        observations.push({scenario:boundary+'-invocation-after-promotion',function_id:fn.id,status:response.status(),code_hash:response.headers()['x-serverless-code-hash'],response:body});await save();
        assert.equal(response.status(),200);assert.equal(response.headers()['x-serverless-code-hash'],publication.code_hash);
        assert.deepEqual(body,{label,local:null,secret_sha256:digest(secret)});
        const state=await remote('inspect',service);assert.equal(state.mutations,boundary==='before'?1:2);
        observations.push({scenario:boundary+'-explicit-retry',service_id:service.id,function_id:functions[0].id,mutations:state.mutations});
      });
      await purge(service);
    });
  }
  completed=true;
}finally{
  for(const held of gates)if(!held.restored)try{await held.recover();}catch(error){cleanupErrors.push({resource:'observer',error:error.name});}
  if(activeTask)try{await activeTask.observe();}catch(error){cleanupErrors.push({resource:'cli-evidence',error:error.name});}
  if(session?.authenticated&&gates.every(row=>row.restored)){
    for(const service of services)if(!service.cleaned)try{await purge(service);}catch(error){cleanupErrors.push({resource:service.id,error:error.name});}
    if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'namespace',error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});
  await admin.dispose();await caller.dispose();
  cleanupFinished=true;await save();
}
assert(completed&&!cleanupErrors.length);
