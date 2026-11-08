// @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
// @verifies docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
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
const base='https://serverless.lelabs.tech',prefix='service-transport-'+randomUUID().slice(0,8);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/service-transport-observer.py';
const checks=[],observations=[],gates=[],services=[],archives=[],cleanupErrors=[],credentials=[];
const secret=randomUUID()+randomUUID(),digest=value=>createHash('sha256').update(value).digest('hex');
await mkdir(out,{recursive:true,mode:0o700});
const report=path.join(out,'service-transport.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
const caller=await request.newContext({baseURL:base,timeout:120000});
let session,namespace,work,completed=false,activeTask;

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
  const child=spawn('ssh',[...ssh,'python3','-B',helper,mode,service.id,namespace.id],{stdio:['pipe','pipe','pipe']});
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
  const row=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name},status:201});services.push(row);return row;
}
async function token(service,name,rights){
  const row=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name,rights},status:201});credentials.push(row.token);return row.token;
}
async function startDeployment(service,credential,label,trace=false){
  const config=path.join(work,'serverless.yml');
  await writeFile(config,JSON.stringify({service:service.name,provider:{name:'p2enjoy',runtime:'node24',env:{SHARED_LABEL:label},secret:{SHARED_SECRET:'${env:SHARED_SECRET}'},p2enjoy:{idle_seconds:0}},
    functions:{'transport-inheritance':{handler:'handler.handler'}},package:{patterns:['!**','*.cjs']}}));
  const task={settled:false,async result(success){
    const value=await task.done;task.settled=true;
    assert.equal(value.code,success?0:1,'Code de sortie CLI');
    for(const credential of [secret,...credentials])assert(!value.stdout.includes(credential)&&!value.stderr.includes(credential),'Identifiant exposé');
    assert(!value.stderr.includes('Traceback'));const result=JSON.parse(value.stdout);assert.equal(result.completed,success);
    if(trace){
      const native=await readFile(tracePath,'utf8');
      for(const credential of [secret,...credentials])assert(!native.includes(credential),'Identifiant dans la trace native');
      const attempts=native.split('\n').filter(line=>line.includes('connect(')&&line.includes('htons(443)'));
      const connections=attempts.filter(line=>/ = 0$| = -1 EINPROGRESS /.test(line));
      assert.equal(connections.length,3,'Deux lectures et une seule tentative de mutation HTTPS');
      assert.equal(attempts.length,connections.length,'Aucune autre tentative HTTPS');
      observations.push({scenario:'native-cli-connections',service_id:service.id,https_connect_attempts:attempts.length,
        expected_read_requests:2,expected_mutation_attempts:1,trace_sha256:digest(native)});
    }
    return result;
  }};
  const tracePath=path.join(work,'https-connect.trace'),args=['-B','-m','adapter','deploy','--config',config,'--service',service.id];
  task.done=new Promise(resolve=>execFile(trace?'strace':'python3',trace?['-f','-qq','-e','trace=connect,getsockopt','-s','0','-o',tracePath,'python3',...args]:args,
    {cwd:root,timeout:300000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:credential,SHARED_SECRET:secret}},
    (error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr})));
  activeTask=task;return task;
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
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
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
      await check(`Relance explicite après coupure ${boundary} : publication et invocation Docker`,async()=>{
        const retry=await startDeployment(service,credential,label),published=await retry.result(true);
        assert.equal(published.service_configuration.state,'applied');assert.equal(published.results.length,1);
        const functions=(await api(`/api/services/${service.id}/functions`)).items;assert.equal(functions.length,1);
        const read=await token(service,'invocation',['read']);
        const response=await caller.get(`/invoke/${functions[0].id}`,{headers:{'X-Serverless-Token':read}});assert.equal(response.status(),200);
        assert.deepEqual(await response.json(),{label,local:null,secret_sha256:digest(secret)});
        const state=await remote('inspect',service);assert.equal(state.mutations,boundary==='before'?1:2);
        observations.push({scenario:boundary+'-explicit-retry',service_id:service.id,function_id:functions[0].id,mutations:state.mutations});
      });
      await purge(service);
    });
  }
  completed=true;
}finally{
  for(const held of gates)if(!held.restored)try{await held.recover();}catch(error){cleanupErrors.push({resource:'observer',error:error.name});}
  if(activeTask&&!activeTask.settled)await activeTask.done;
  if(session?.authenticated&&gates.every(row=>row.restored)){
    for(const service of services)if(!service.cleaned)try{await purge(service);}catch(error){cleanupErrors.push({resource:service.id,error:error.name});}
    if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'namespace',error:error.name});}
  }
  if(work)await rm(work,{recursive:true,force:true});
  await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({target:base,completed:completed&&!cleanupErrors.length,checks,observations,skipped:0,cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,
    namespace_id:namespace?.id,service_ids:services.map(row=>row.id),function_ids:archives.map(row=>row.function_id),storage_archives:archives},null,2)+'\n');
}
assert(completed&&!cleanupErrors.length);
