// @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md | docs/EXECUTION.md
// @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
// Real SSO, normal publication, HTTPS invocation, Docker and persistent volumes.
import assert from 'node:assert/strict';
import {readFile,writeFile,rename,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile,spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {promisify} from 'node:util';
import {randomUUID,createHash} from 'node:crypto';
import https from 'node:https';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';
// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md

const run=promisify(execFile),root=fileURLToPath(new URL('../',import.meta.url));
const output=path.join(root,'.local/e2e'),report=path.join(output,'public-invocations-http.json');
const base='https://serverless.lelabs.tech',prefix='invocation-'+randomUUID().slice(0,8);
await mkdir(output,{recursive:true,mode:0o700});await writeFile(report,JSON.stringify({completed:false,cleanup:false,skipped:0})+'\n');
const state=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));
const admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});
const checks=[],functions=[],tokens=[],archives=[],storageArchives=[],cleanupErrors=[],pending=[],outcomes=[],invocationTransports=[],publications=[],versionEvidence=[];
const guards=[],operatorEvidence=[],additionalServices=[];
const deletedFunctions=new Set();
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/execution-faults.py';
let session,namespace,service,work,completed=false,readonly,operator;
const secret='invocation-secret-'+randomUUID();
function resources(){return {namespace_id:namespace?.id??null,service_id:service?.id??null,additional_service_ids:additionalServices.map(row=>row.id),function_ids:functions.map(fn=>fn.id),token_ids:tokens.map(t=>t.id)};}
async function saveReport(value){const temporary=report+'.pending';await writeFile(temporary,JSON.stringify(value,null,2)+'\n',{mode:0o600});await rename(temporary,report);}
async function checkpoint(){await saveReport({completed:false,cleanup:false,skipped:0,checks,resources:resources(),deleted_function_ids:[...deletedFunctions],pre_purge_revisions:archives,storage_archives:storageArchives,invocation_transports:invocationTransports,publications,version_evidence:versionEvidence});}
async function manage(url,{method='GET',body,bytes,status=200,token,headers={}}={}){
  const response=await admin.fetch(url,{method,data:bytes??body,headers:{...(token?{'X-Serverless-Token':token}:{Origin:base,'X-CSRF-Token':session.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert.equal(response.status(),status,`${method} ${url}: ${response.status()} au lieu de ${status}`);
  const text=await response.text();assert(!text.includes(secret),'Secret dans les métadonnées');return JSON.parse(text);
}
function start(url,{method='GET',body,bytes,token=readonly,headers={},open=false}={}){
  const clientRequestId=randomUUID();
  const payload=bytes??(body===undefined?undefined:Buffer.from(JSON.stringify(body)));
  const transport={connected:false,status:null,error:null};
  let req;const promise=new Promise((resolve,reject)=>{
    req=https.request(base+url,{method,headers:{...(token?{'X-Serverless-Token':token}:{}),...(payload?{'Content-Length':payload.length}:{}),...(body!==undefined?{'Content-Type':'application/json'}:{}),...headers}},res=>{
      transport.status=res.statusCode;const chunks=[];res.on('data',chunk=>chunks.push(chunk));res.on('end',()=>{const match=url.match(/^\/invoke\/([0-9a-f-]{36})(?:@([0-9a-f]{64}))?(?:[/?]|$)/);if(match)invocationTransports.push({client_request_id:clientRequestId,id:res.headers['x-serverless-request-id']??null,function_id:match[1],method,status:res.statusCode,requested_code_hash:match[2]??null,resolved_code_hash:res.headers['x-serverless-code-hash']??null});resolve({status:res.statusCode,headers:res.headers,rawHeaders:res.rawHeaders,bytes:Buffer.concat(chunks)});});res.on('error',reject);
    });req.on('socket',socket=>{transport.connected=!socket.connecting;if(socket.connecting)socket.once('secureConnect',()=>{transport.connected=true;});});
    req.on('error',error=>{transport.error=error.code??error.name;reject(error);});req.setTimeout(45000,()=>req.destroy(new Error('request_timeout')));if(open)req.flushHeaders();else req.end(payload);
  });
  const settled=promise.then(value=>({value}),error=>({error}));pending.push(settled);
  return {clientRequestId,promise,settled,transport,abort:()=>req.destroy(),end:bytes=>req.end(bytes)};
}
async function invoke(fn,options={}){
  const {status=200,suffix='',...rest}=options;const value=await start(`/invoke/${fn.id}${suffix}`,rest).promise;
  outcomes.push({function_id:fn.id,status:value.status,expected:status,invocation_id:value.headers['x-serverless-request-id']??null});
  assert.equal(value.status,status,`Invocation attendue ${status}, reçue ${value.status}`);
  return {...value,json:()=>JSON.parse(value.bytes.toString())};
}
async function check(name,action){try{await action();checks.push({name,status:'passed'});await checkpoint();console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:diagnostic(error)});await checkpoint();throw error;}}
async function until(action,message,seconds=20){const end=Date.now()+seconds*1000;while(Date.now()<end){const result=await action();if(result)return result;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function current(fn){return manage(`/api/functions/${fn.id}`);}
async function instances(fn){return (await manage(`/api/functions/${fn.id}/instances`)).items;}
async function history(fn){return (await manage(`/api/functions/${fn.id}/invocations?limit=100`)).items;}
async function healthy(){await until(async()=>{try{return(await admin.get('/healthz',{timeout:2000})).status()===200;}catch{return false;}},'Contrôle non rétabli',90);}
async function remote(mode,fn,extra=[]){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,mode,fn.id,...extra],{timeout:90000,maxBuffer:2*1024*1024});const rows=stdout.trim().split('\n').map(line=>JSON.parse(line));operatorEvidence.push({mode,function_id:fn.id,rows});return rows;}
async function holdWriter(fn){
  const child=spawn('ssh',[...ssh,'python3','-B',helper,'hold-database',fn.id],{stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false;
  createInterface({input:child.stdout}).on('line',line=>events.push(JSON.parse(line)));child.stderr.resume();
  const done=new Promise(resolve=>{child.on('exit',code=>{ended=true;resolve(code);});child.on('error',()=>{ended=true;resolve(-1);});});
  const handle={events,done,async release(){if(!ended)child.stdin.end('release\n');assert.equal(await done,0,'Garde SQL non restaurée');}};guards.push(handle);
  const locked=await until(async()=>{assert(!ended,'Garde SQL interrompue');return events.find(row=>row.event==='writer-locked');},'Verrou écrivain non observé');
  assert(locked.identity.effective_uid>0);assert(locked.identity.effective_gid>0);assert.equal(locked.operator_uid,0);
  assert(Object.values(locked.identity.sidecar_uids).every(uid=>uid===locked.identity.effective_uid));return handle;
}
async function update(fn,overrides,configuration={environment:{PUBLIC_LABEL:'first'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}}){
  const row=await current(fn);return manage(`/api/functions/${fn.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:{...row.config,...overrides},configuration}});
}
async function policy(value){return manage(`/api/services/${service.id}`,{method:'PUT',body:{name:'public-invocations',policy:value}});}
async function token(name,rights,extra={}){const row=await manage(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights,...extra}});tokens.push(row);await checkpoint();return row;}
async function create(name,config={}){
  const fn=await manage(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'public-invocation.handler',memory_mib:128,cpu:.25,timeout_seconds:10,idle_seconds:30,...config}}});functions.push(fn);await checkpoint();return fn;
}
async function packageCode(revision){
  const project=path.join(work,revision);await mkdir(project);
  for(const name of ['public-invocation.cjs','invoke.cjs','volume-operations.cjs'])await cp(path.join(root,'qualification/artifacts',name),path.join(project,name));
  await writeFile(path.join(project,'revision.json'),JSON.stringify({revision}));
  const config=path.join(project,'serverless.yml');await writeFile(config,JSON.stringify({service:'public-invocations',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'public-invocation.handler'}},package:{patterns:['!**','*.cjs','revision.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',config],{cwd:root});
  const descriptor=JSON.parse(await readFile(path.join(project,'.serverless-p2/deployment.json'),'utf8'));
  return readFile(path.join(project,'.serverless-p2',descriptor.artifacts.probe.file));
}
async function publish(fn,bytes,overrides={},activate=true){
  const row=await current(fn),candidate=await manage(`/api/functions/${fn.id}/deployments`,{method:'POST',status:201,token:operator,headers:{'If-Match':String(row.updated_at)},
    body:{config:{...row.config,...overrides},configuration:{environment:{PUBLIC_LABEL:'first'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}},events:{http:[{path:'probe',methods:['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'],implicit:true}]}}});
  const result=await manage(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',token:operator,bytes});assert.equal(result.state,'published');assert.match(result.code_hash,/^[0-9a-f]{64}$/);assert.equal((await current(fn)).active_revision_id,row.active_revision_id);publications.push({function_id:fn.id,candidate_id:candidate.id,revision_id:result.revision_id,code_hash:result.code_hash,code_changed:result.code_changed,previous_default_revision_id:row.active_revision_id});archives.push(result.revision_id);if(activate)await promote(fn,result.revision_id);await checkpoint();return result.revision_id;
}

function publishedVersion(fn,id){const value=publications.find(v=>v.function_id===fn.id&&v.revision_id===id);assert(value,'published_version_not_tracked');return value;}
async function promote(fn,id){const value=publishedVersion(fn,id);const row=await current(fn);await manage(`/api/functions/${fn.id}/versions/${value.code_hash}/promote`,{method:'POST',token:operator,headers:{'If-Match':String(row.updated_at)}});assert.equal((await current(fn)).active_revision_id,id);}
async function purgeArchive(fn){await until(async()=>!(await manage(`/api/archives/${fn.id}`)).storage_operation,'archive_not_settled');const row=await manage(`/api/archives/${fn.id}`);const response=await admin.post(`/api/archives/${fn.id}/purge`,{headers:{Origin:base,'X-CSRF-Token':session.csrf_token,'If-Match':String(row.updated_at)},data:{operation_id:randomUUID(),confirm_name:row.name}});assert([200,202].includes(response.status()));const op=await response.json();await until(async()=>{const value=await manage(`/api/storage-operations/${op.id}`);assert.notEqual(value.state,'aborted');return value.state==='completed';},'public_purge_not_completed',60);const after=await manage(`/api/archives/${fn.id}`);assert(after.purged_at&&after.artifact_bytes===0&&!after.storage_operation);return {function_id:fn.id,namespace_id:namespace.id,operation_id:op.id,purged:true,artifact_bytes:after.artifact_bytes};}
function diagnostic(error){const location=String(error?.stack??'').match(/public-invocations\.mjs:(\d+):(\d+)/);return {name:error?.name??'UnknownError',operator:error?.operator,source:location?{line:Number(location[1]),column:Number(location[2])}:undefined,message_sha256:createHash('sha256').update(String(error?.message??'')).digest('hex')};}
try{
  session=await (await admin.get('/api/session')).json();assert(session.authenticated,'Session SSO réelle requise');
  work=await mkdtemp(path.join(output,'invocation-code-'));const firstCode=await packageCode('first'),secondCode=await packageCode('second');
  namespace=await manage('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await checkpoint();
  service=await manage(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'public-invocations'}});await checkpoint();
  operator=(await token('publish',['create','read','update','delete'])).token;readonly=(await token('invoke',['read'])).token;
  const fn=await create('http-probe');
  await check('Jeton obligatoire, session admin insuffisante, Read et brouillon',async()=>{
    await invoke(fn,{token:null,status:401});
    const cookie=state.cookies.filter(c=>c.name==='__Host-p2-session').map(c=>c.name+'='+c.value).join('; ');
    await invoke(fn,{token:null,headers:{Cookie:cookie},status:401});
    await invoke(fn,{status:409});const forbidden=await token('create-only',['create']);await invoke(fn,{token:forbidden.token,status:403});
  });
  await check('Normalisation stricte des origines, réseaux mapped et alias implicites',async()=>{
    await manage(`/api/services/${service.id}`,{method:'PUT',status:422,body:{name:service.name,policy:{origins:['https://app.example:0']}}});
    const changed=await policy({ips:['::ffff:192.0.2.0/120']});assert.deepEqual(changed.policy.ips,['192.0.2.0/24']);await policy({});
    const row=await current(fn);await manage(`/api/functions/${fn.id}/deployments`,{method:'POST',token:operator,status:422,headers:{'If-Match':String(row.updated_at)},body:{config:row.config,events:{http:[{path:'a',methods:['GET'],implicit:true},{path:'b',methods:['GET'],implicit:true}]}}});
  });
  const firstRevision=await publish(fn,firstCode);
  await check('Invocation froide puis chaude, identité et mesures Docker réelles',async()=>{
    const a=(await invoke(fn)).json();assert.equal(a.revision,'first');assert.equal(a.context.functionVersion,firstRevision);
    assert.equal(a.context.awsRequestId,a.event.requestContext.requestId);assert.equal(a.context.memoryLimitInMB,'128');assert(a.context.remaining>0);
    const before=await instances(fn);assert.equal(before.length,1);assert.equal(before[0].memory_mib,128);assert.equal(before[0].cpu_nanos,250000000);assert(before[0].metrics.memory_usage_bytes>0);
    const b=(await invoke(fn)).json();assert.notEqual(a.context.awsRequestId,b.context.awsRequestId);assert.equal((await instances(fn))[0].id,before[0].id);
  });
  await check('Événement Lambda, valeurs multiples et retrait des seuls identifiants de contrôle',async()=>{
    const answer=(await invoke(fn,{method:'POST',suffix:'/probe?x=first&x=last&empty=&path=wrong',body:{hello:'world'},headers:{Authorization:'Bearer business-proof','X-Tag':['one','two'],Cookie:'business=ok; __Host-p2-session=hidden; __Host-p2-flow=hidden','X-CSRF-Token':'hidden'}})).json();
    assert.equal(answer.event.path,'/probe');assert.equal(answer.event.headers.authorization,'Bearer business-proof');assert.equal(answer.event.headers.cookie,'business=ok');
    for(const key of ['x-serverless-token','x-csrf-token'])assert(!(key in answer.event.headers));
    assert.deepEqual(answer.event.multiValueHeaders['x-tag'],['one','two']);assert.equal(answer.event.headers['x-tag'],'two');assert.deepEqual(answer.event.multiValueQueryStringParameters.x,['first','last']);assert.equal(answer.event.queryStringParameters.x,'last');
    assert.equal((await invoke(fn,{suffix:'?path=wrong'})).json().event.path,'/probe');
    await invoke(fn,{suffix:'/probe/',status:404});await invoke(fn,{headers:{'X-Serverless-Token':[readonly,readonly]},status:400});
    const refused=await invoke(fn,{method:'TRACE',status:405});assert.equal(refused.json().error,'method_not_allowed');assert.equal(refused.json().invocation_id,refused.headers['x-serverless-request-id']);assert.equal(refused.headers['x-request-id'],refused.headers['x-serverless-request-id']);
  });
  await check('Corps texte et binaire, limite exacte de 1 Mio',async()=>{
    for(const [bytes,type] of [[Buffer.alloc(1024*1024,65),'text/plain'],[Buffer.from([0,255,128,10]),'application/octet-stream']]){
      const value=(await invoke(fn,{method:'POST',suffix:'?mode=digest',bytes,headers:{'Content-Type':type}})).json();assert.equal(value.bytes,bytes.length);assert.equal(value.sha256,createHash('sha256').update(bytes).digest('hex'));assert.equal(value.encoded,type==='application/octet-stream');
    }
    await invoke(fn,{method:'POST',suffix:'?mode=digest',bytes:Buffer.alloc(1024*1024+1),status:413});
  });
  await check('Réponses binaires, en-têtes métier multiples et HEAD',async()=>{
    assert.deepEqual((await invoke(fn,{method:'POST',suffix:'?mode=runtime',body:{operation:'binary'}})).bytes,Buffer.from([0,255,10,128]));
    const response=await invoke(fn,{suffix:'?mode=headers',status:202});assert.equal(response.headers['cache-control'],'private, max-age=17');assert.equal(response.headers['content-security-policy'],"default-src 'none'");assert.equal(response.headers['x-transient'],undefined);
    assert.deepEqual(response.headers['set-cookie'],['business-a=1; Path=/','business-b=2; Path=/']);assert.notEqual(response.headers['x-request-id'],'forged');assert.notEqual(response.headers['x-serverless-request-id'],'forged');assert.match(response.headers.vary,/Accept-Encoding/);assert.match(response.headers.vary,/Origin/);
    assert.equal((await invoke(fn,{method:'HEAD'})).bytes.length,0);
  });
  await check('Politique origine/IP ET puis OU et préflight sans invocation',async()=>{
    const ip=(await invoke(fn)).json().event.requestContext.identity.sourceIp;const origin='https://app.example';
    await policy({origins:[origin],ips:[ip],combination:'and'});
    await invoke(fn,{status:403});await invoke(fn,{headers:{Origin:'https://denied.example'},status:403});await invoke(fn,{headers:{Origin:origin}});
    const before=(await history(fn)).length;
    const pre=await invoke(fn,{method:'OPTIONS',token:null,status:204,headers:{Origin:origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type, authorization, x-serverless-token'}});
    assert.equal(pre.headers['access-control-allow-origin'],origin);assert.equal(pre.headers['access-control-allow-credentials'],undefined);assert.equal((await history(fn)).length,before);
    await invoke(fn,{method:'OPTIONS',token:null,headers:{Origin:origin},status:401});
    await invoke(fn,{method:'OPTIONS',token:null,headers:{Origin:origin,'Access-Control-Request-Method':'','Access-Control-Request-Headers':'cookie'},status:400});
    await policy({origins:[origin],ips:[ip],combination:'or'});await invoke(fn,{headers:{Origin:'https://elsewhere.example'}});
    await policy({origins:[origin],ips:['192.0.2.99'],combination:'and'});await invoke(fn,{headers:{Origin:origin,'X-Forwarded-For':'192.0.2.99'},status:403});await policy({});
  });
  await check('Exceptions, logs expurgés, timeout et invocation saine après recyclage',async()=>{
    await invoke(fn,{method:'POST',suffix:'?mode=runtime',body:{operation:'logs'}});
    let rows=await history(fn);assert(rows[0].logs.includes('stderr'));assert(!JSON.stringify(rows).includes(secret));assert.equal(rows[0].handler_started,true);
    await invoke(fn,{method:'POST',suffix:'?mode=runtime',body:{operation:'throw'},status:502});
    await update(fn,{timeout_seconds:.4});await invoke(fn,{method:'POST',suffix:'?mode=runtime',body:{operation:'spin'},status:504});
    await update(fn,{timeout_seconds:10});await invoke(fn);
  });
  await check('Révocation d’un appel en file sans interrompre celui déjà admis',async()=>{
    const secondary=await token('queued-read',['read']);
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:3000}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Handler actif non observé');
    const queued=start(`/invoke/${fn.id}`,{token:secondary.token});await until(async()=>(await history(fn)).some(row=>row.state==='queued'),'File non observée');
    await manage(`/api/tokens/${secondary.id}/revoke`,{method:'POST'});assert.equal((await queued.promise).status,401);assert.equal((await active.promise).status,200);
    const denied=(await history(fn)).find(row=>row.actor_id===secondary.id);assert.equal(denied.handler_started,false);
  });
  await check('Minimum chaud, extinction des excédents et budget des minima',async()=>{
    await update(fn,{min_instances:2,max_instances:2,concurrency:2,idle_seconds:0});
    await until(async()=>{const rows=await instances(fn);return rows.length===2&&rows.every(row=>row.state==='ready');},'Minimum non démarré');
    await manage(`/api/services/${service.id}/functions`,{method:'POST',status:409,body:{name:'unaffordable-minimum',config:{cpu:1,min_instances:2,max_instances:2}}});
    await update(fn,{min_instances:0,max_instances:1,concurrency:1,idle_seconds:0});await until(async()=>(await instances(fn)).length===0,'Instances minimales non drainées');
    await invoke(fn);await until(async()=>(await instances(fn)).length===0,'Instance inactive non éteinte');await update(fn,{idle_seconds:30});
  });
  await check('Génération de configuration, code publié et rollback exécutés',async()=>{
    await update(fn,{}, {environment:{PUBLIC_LABEL:'updated'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}});
    assert.equal((await invoke(fn)).json().label,'updated');const second=await publish(fn,secondCode,{},false);assert.equal((await invoke(fn)).json().revision,'first');const pilot=publishedVersion(fn,second);assert.equal((await invoke(fn,{suffix:'@'+pilot.code_hash})).json().revision,'second');await promote(fn,second);assert.equal((await invoke(fn)).json().revision,'second');versionEvidence.push({scenario:'generation-pilot-and-explicit-promotion',stable_revision_id:firstRevision,pilot_revision_id:second,pilot_hash:pilot.code_hash});
    const row=await current(fn);await manage(`/api/functions/${fn.id}/rollback`,{method:'POST',headers:{'If-Match':String(row.updated_at)},body:{revision_id:firstRevision}});
    assert.equal((await invoke(fn)).json().revision,'first');assert.notEqual(second,firstRevision);
  });
  await check('File par fonction saturée, admission en ordre et absence de surallocation',async()=>{
    await update(fn,{queue_timeout_seconds:15});
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:3000}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Appel actif non observé');
    const queued=Array.from({length:16},()=>start(`/invoke/${fn.id}`));
    await until(async()=>(await history(fn)).filter(row=>row.state==='queued').length===16,'Seize attentes non observées');
    assert.equal((await invoke(fn,{status:429})).json().error,'queue_full');assert.equal((await instances(fn)).length,1);
    assert.equal((await active.promise).status,200);
    const results=await Promise.all(queued.map(item=>item.promise));assert(results.every(row=>row.status===200));
    const ids=new Set(results.map(row=>row.headers['x-serverless-request-id']));const rows=(await history(fn)).filter(row=>ids.has(row.id)).sort((a,b)=>a.created_at-b.created_at||a.id.localeCompare(b.id));
    assert.equal(rows.length,16);for(let i=1;i<rows.length;i++)assert(rows[i].admitted_at>=rows[i-1].admitted_at);
  });
  await check('Délai de file puis tentative immédiate sans exécution indue',async()=>{
    await update(fn,{queue_timeout_seconds:.25});await until(async()=>(await instances(fn)).length===0,'Ancienne génération non retirée');
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:2000}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Appel actif non observé');
    const expired=await invoke(fn,{status:429});assert.equal(expired.json().error,'queue_timeout');
    await update(fn,{queue_timeout_seconds:0});const immediate=await invoke(fn,{status:429});assert.equal(immediate.json().error,'queue_timeout');
    assert.equal((await active.promise).status,200);
    const ids=[expired.headers['x-serverless-request-id'],immediate.headers['x-serverless-request-id']];assert((await history(fn)).filter(row=>ids.includes(row.id)).every(row=>row.handler_started===false&&row.instance_id===null));
    await update(fn,{queue_timeout_seconds:10});
  });
  await check('Déconnexion en file retirée avant admission',async()=>{
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:2200}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Appel actif non observé');
    const waiting=start(`/invoke/${fn.id}`);const row=await until(async()=>(await history(fn)).find(row=>row.state==='queued'),'Attente non observée');
    waiting.abort();assert((await waiting.settled).error);await until(async()=>(await history(fn)).some(item=>item.id===row.id&&item.state==='disconnected'&&item.handler_started===false),'Attente non retirée');
    assert.equal((await active.promise).status,200);
  });
  const storage={data:{enabled:true,quota_mib:2},cache:{enabled:true,quota_mib:2},concurrency:'exclusive'};
  await check('Déconnexion après admission : propriétaire conservé et écriture terminée une seule fois',async()=>{
    await update(fn,{storage});const active=start(`/invoke/${fn.id}?mode=counter`,{method:'POST',body:{ms:1500}});
    const row=await until(async()=>(await history(fn)).find(row=>row.state==='running'&&row.handler_started),'Handler non observé');
    active.abort();assert((await active.settled).error);
    await until(async()=>(await history(fn)).some(item=>item.id===row.id&&item.state==='succeeded'),'Appel détaché non terminé');outcomes.push({transport:'disconnected-after-admission',invocation_id:row.id,function_id:fn.id,completed_without_response:true});
    assert.equal((await invoke(fn,{suffix:'?mode=counter'})).json().count,1);
  });
  await check('Stockage public : quota Linux, réduction refusée et conservation après drainage',async()=>{
    const volume=(body,status=200)=>invoke(fn,{method:'POST',suffix:'?mode=volume',body,status});
    await volume({operation:'write',volume:'cache',name:'cache-proof',value:'cache-preserved'});
    assert.equal((await volume({operation:'fill',name:'too-large',bytes:3*1024*1024},507)).json().error,'EDQUOT');
    await volume({operation:'remove',name:'too-large'});
    await volume({operation:'fill',name:'stored-data',bytes:1280*1024});
    const row=await current(fn);await manage(`/api/functions/${fn.id}`,{method:'PUT',status:422,body:{name:row.name,config:{...row.config,storage:{...storage,data:{enabled:true,quota_mib:1}}}}});
    assert.equal((await current(fn)).config.storage.data.quota_mib,2);
    await volume({operation:'remove',name:'stored-data'});
    await update(fn,{storage:{...storage,data:{enabled:false,quota_mib:2}}});await volume({operation:'read',name:'counter'},404);
    await update(fn,{storage});assert.equal((await invoke(fn,{suffix:'?mode=counter'})).json().count,1);assert.equal((await volume({operation:'read',volume:'cache',name:'cache-proof'})).json().value,'cache-preserved');
  });
  await check('Mutation de stockage et suppression refusées pendant une invocation admise',async()=>{
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:2500}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Handler actif non observé');
    const row=await current(fn);await manage(`/api/functions/${fn.id}`,{method:'PUT',status:409,body:{name:row.name,config:{...row.config,storage:{...storage,data:{enabled:true,quota_mib:3}}}}});
    await manage(`/api/functions/${fn.id}`,{method:'DELETE',status:409});assert.equal((await active.promise).status,200);assert.equal((await current(fn)).config.storage.data.quota_mib,2);
  });
  await check('Publication et promotion pendant appel : instantané conservé puis retrait différé du hash',async()=>{
    const old=(await current(fn)).active_revision_id,oldVersion=publishedVersion(fn,old);
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:7000}});
    const admitted=await until(async()=>(await history(fn)).find(row=>row.state==='running'&&row.handler_started),'Ancienne invocation non observée');
    const next=await publish(fn,secondCode,{},false);const pilot=publishedVersion(fn,next);assert.equal((await current(fn)).active_revision_id,old);
    let currentRow=await current(fn);await manage(`/api/functions/${fn.id}/revisions/${old}`,{method:'DELETE',status:409,headers:{'If-Match':String(currentRow.updated_at)}});
    await promote(fn,next);assert((await history(fn)).some(row=>row.id===admitted.id&&row.state==='running'&&row.handler_started));
    currentRow=await current(fn);const removed=await manage(`/api/functions/${fn.id}/revisions/${old}`,{method:'DELETE',headers:{'If-Match':String(currentRow.updated_at)}});assert.equal(removed.state,'deleted');assert.equal(removed.cleanup_pending,true);
    const following=start(`/invoke/${fn.id}`);assert.equal(JSON.parse((await active.promise).bytes).context.functionVersion,old);assert.equal(JSON.parse((await following.promise).bytes).context.functionVersion,next);await invoke(fn,{suffix:'@'+oldVersion.code_hash,status:404});
    await until(async()=>!(await instances(fn)).some(row=>row.revision_id===old),'Ancienne référence non drainée');
    await until(async()=>{const versions=await manage(`/api/functions/${fn.id}/versions?limit=100`);return versions.items.some(row=>row.code_hash===oldVersion.code_hash&&row.state==='deleted'&&row.stored_bytes===0);},'Ancien code non effacé',60);
    assert.equal((await invoke(fn,{suffix:'?mode=counter'})).json().count,1);versionEvidence.push({scenario:'running-snapshot-and-deferred-version-removal',invocation_id:admitted.id,stable_revision_id:old,stable_hash:oldVersion.code_hash,pilot_revision_id:next,pilot_hash:pilot.code_hash,cleanup_pending_at_decision:removed.cleanup_pending});
  });
  await check('Budget CPU global et limites réellement transmises à Docker',async()=>{
    const peer=await create('budget-peer',{queue_timeout_seconds:.25});await publish(peer,firstCode);
    await update(fn,{cpu:1,memory_mib:256});await until(async()=>(await instances(fn)).length===0,'Ancienne allocation non retirée');
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:2500}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Invocation CPU non observée');
    const observed=(await remote('inspect',fn))[0];assert.equal(observed.containers.length,1);const container=observed.containers[0];
    assert.equal(container.cpu_nanos,1000000000);assert.equal(container.memory_bytes,256*1024*1024);assert.equal(container.memory_swap_bytes,container.memory_bytes);assert.equal(container.pids_limit,64);assert(container.readonly_root);assert.deepEqual(container.cap_drop,['ALL']);
    assert.equal((await invoke(peer,{status:429})).json().error,'queue_timeout');assert.equal((await instances(peer)).length,0);assert.equal((await active.promise).status,200);
    await update(fn,{idle_seconds:0});await until(async()=>(await instances(fn)).length===0,'Budget CPU non libéré');await invoke(peer);await update(peer,{idle_seconds:0});
    await update(fn,{cpu:.25,memory_mib:128,idle_seconds:30});
  });
  await check('Contention SQLite après dispatch : finalisation conservée et reprise sans restart',async()=>{
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:1800}});
    const held=await holdWriter(fn);
    let replied=false;active.settled.then(()=>{replied=true;});
    try{
      const id=held.events.find(row=>row.event==='writer-locked').invocation_id;
      const evidence=await until(async()=>{const row=(await remote('finalization-evidence',fn,[id]))[0];return row.pending_result_observed&&row;},'Résultat effectivement bloqué par SQLite non observé');
      assert.equal(evidence.state,'running');assert.equal(evidence.handler_started,true);assert(!replied,'La réponse attend sa finalisation durable');
      assert.equal((await admin.get('/healthz',{timeout:2000})).status(),503);
    }
    finally{await held.release();}
    assert.equal((await active.promise).status,200);await healthy();const id=held.events.find(row=>row.event==='writer-locked').invocation_id;
    await until(async()=>(await history(fn)).some(row=>row.id===id&&row.state==='succeeded'),'Résultat terminal non repris');await invoke(fn);
  });
  await check('Réception complète sous verrou SQLite : refus public stable et abandons repris',async()=>{
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:8000}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Handler du verrou non observé');
    const completing=start(`/invoke/${fn.id}`,{method:'POST',open:true,headers:{'Content-Length':'16','Content-Type':'application/json',Origin:'https://allowed-origin.example'}});
    const incoming=await until(async()=>(await history(fn)).find(row=>row.state==='receiving'),'Réception à refuser non observée');
    const disconnecting=start(`/invoke/${fn.id}`,{method:'POST',open:true,headers:{'Content-Length':'16','Content-Type':'application/json'}});
    const abandoned=await until(async()=>(await history(fn)).find(row=>row.state==='receiving'&&row.id!==incoming.id),'Réception à abandonner non observée');
    const queued=start(`/invoke/${fn.id}`);const queuedRow=await until(async()=>(await history(fn)).find(row=>row.state==='queued'),'Attente à abandonner non observée');
    const held=await holdWriter(fn);
    try{
      disconnecting.abort();queued.abort();await Promise.all([disconnecting.settled,queued.settled]);completing.end(Buffer.alloc(16,32));
      const response=await completing.promise;assert.equal(response.status,503);assert.equal(JSON.parse(response.bytes).error,'execution_unavailable');
      assert.equal(JSON.parse(response.bytes).invocation_id,incoming.id);assert.equal(response.headers['x-serverless-request-id'],incoming.id);assert.equal(response.headers['access-control-allow-origin'],'https://allowed-origin.example');
      assert.equal(response.headers['x-request-id'],incoming.id);
      const evidence=await until(async()=>{const observed=(await remote('rejection-evidence',fn,[incoming.id,abandoned.id,queuedRow.id]))[0];return observed.events.length===3&&observed;},'Décisions de rejet sous verrou non observées');
      for(const id of [abandoned.id,queuedRow.id])assert(evidence.events.some(row=>row.invocation_id===id&&row.state==='disconnected'&&row.http_status===499&&row.error_code==='client_disconnected'));
      assert(evidence.events.some(row=>row.invocation_id===incoming.id&&row.state==='rejected'&&row.http_status===503&&row.error_code==='execution_unavailable'));
    }finally{await held.release();completing.abort();disconnecting.abort();queued.abort();}
    assert.equal((await active.promise).status,200);await healthy();
    await until(async()=>{const rows=await history(fn);return rows.some(row=>row.id===incoming.id&&row.state==='rejected'&&row.http_status===503&&row.error_code==='execution_unavailable'&&row.handler_started===false)&&[abandoned.id,queuedRow.id].every(id=>rows.some(row=>row.id===id&&row.state==='disconnected'&&row.http_status===499&&row.error_code==='client_disconnected'&&row.handler_started===false));},'Réceptions non finalisées après restitution SQL');
    await invoke(fn);
  });
  await check('SIGKILL du contrôle pendant écriture : réservation réconciliée sans rejeu',async()=>{
    const before=(await invoke(fn,{suffix:'?mode=counter'})).json().count;
    const active=start(`/invoke/${fn.id}?mode=counter`,{method:'POST',body:{ms:10000}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Handler à interrompre non observé');
    const events=await remote('crash-control',fn);assert(events.some(row=>row.event==='control-killed'));const interruptedTransport=await active.settled;assert(interruptedTransport.error||interruptedTransport.value.status===502);await healthy();
    const row=events.find(row=>row.event==='control-killed').before.invocations.find(row=>row.state==='running'&&row.handler_started);
    const recovered=(await history(fn)).find(item=>item.id===row.id);versionEvidence.push({scenario:'control-crash-transport',client_request_id:active.clientRequestId,function_id:fn.id,invocation_id:row.id,outcome:interruptedTransport.error?{kind:'transport-error',code:interruptedTransport.error.code??interruptedTransport.error.name}:{kind:'http',status:interruptedTransport.value.status,response_id:interruptedTransport.value.headers['x-serverless-request-id']??null,resolved_code_hash:interruptedTransport.value.headers['x-serverless-code-hash']??null}});assert.equal(recovered.state,'interrupted');assert.equal(recovered.handler_started,true);assert.equal((await instances(fn)).length,0);
    assert.equal((await invoke(fn,{suffix:'?mode=counter'})).json().count,before+1);await invoke(fn);
  });
  await check('Observations : droits Read, portée fonction/service, révocation, expiration et pagination',async()=>{
    const other=await create('observation-scope');
    const scoped=await token('observe-this-function',['read'],{function_ids:[fn.id]});
    const unrelated=await token('observe-other-function',['read'],{function_ids:[other.id]});
    const createOnly=await token('observe-with-create',['create']);
    const foreign=await manage(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:'separate-observation-scope'}});additionalServices.push(foreign);await checkpoint();
    const foreignToken=await manage(`/api/services/${foreign.id}/tokens`,{method:'POST',status:201,body:{name:'other-service-read',rights:['read']}});tokens.push(foreignToken);await checkpoint();
    for(const route of ['instances','invocations']){
      const url=`/api/functions/${fn.id}/${route}`;
      for(const [credential,status] of [[readonly,200],[scoped.token,200],[createOnly.token,403],[unrelated.token,403],[foreignToken.token,403],[null,401]]){
        const reply=await start(url,{token:credential}).promise;assert.equal(reply.status,status);
        assert(!reply.bytes.includes(Buffer.from(secret)));assert(!reply.bytes.includes(Buffer.from('snapshot_cipher')));assert(!reply.bytes.includes(Buffer.from('generation')));
      }
      assert.equal((await admin.get(url)).status(),200);
      const first=JSON.parse((await start(url+'?limit=1&offset=0').promise).bytes),second=JSON.parse((await start(url+'?limit=1&offset=1').promise).bytes);
      assert(first.items.length<=1&&second.items.length<=1);if(first.total>1)assert.notEqual(first.items[0].id,second.items[0].id);
      for(const query of ['limit=0','limit=101','offset=-1','offset=10001'])assert.equal((await start(url+'?'+query).promise).status,422);
    }
    await manage(`/api/tokens/${scoped.id}/revoke`,{method:'POST'});
    for(const route of ['instances','invocations'])assert.equal((await start(`/api/functions/${fn.id}/${route}`,{token:scoped.token}).promise).status,401);
    const expires=await token('observation-expiration',['read'],{expires_at:Date.now()/1000+2});
    await until(async()=>(await start(`/api/functions/${fn.id}/instances`,{token:expires.token}).promise).status===401,'Expiration non appliquée');
    assert.equal((await start(`/api/functions/${fn.id}/invocations`,{token:expires.token}).promise).status,401);
  });
  await check('Budget mémoire réservé : refus sans saturation CPU et minima atomiques',async()=>{
    const large=await create('memory-reservation',{cpu:.05,memory_mib:8192,idle_seconds:0});await publish(large,firstCode);
    await update(fn,{idle_seconds:0,queue_timeout_seconds:.25});await until(async()=>(await instances(fn)).length===0,'Instance précédente non fermée');
    const active=start(`/invoke/${large.id}?mode=delay`,{method:'POST',body:{ms:3500}});
    await until(async()=>(await history(large)).some(row=>row.state==='running'&&row.handler_started),'Réservation mémoire non observée');
    const observed=(await remote('inspect',large))[0];assert.equal(observed.instances.length,1);assert.equal(observed.instances[0].memory_mib,8192);assert.equal(observed.containers[0].memory_bytes,8192*1024*1024);
    const denied=await invoke(fn,{status:429});assert.equal(denied.json().error,'queue_timeout');
    const row=(await history(fn)).find(item=>item.id===denied.headers['x-serverless-request-id']);assert.equal(row.handler_started,false);assert.equal(row.instance_id,null);
    assert.equal((await active.promise).status,200);await until(async()=>(await instances(large)).length===0,'Mémoire non libérée');await invoke(fn);
    const before=await current(large);
    await manage(`/api/functions/${large.id}`,{method:'PUT',status:409,body:{name:before.name,config:{...before.config,min_instances:2,max_instances:2}}});
    assert.equal((await current(large)).updated_at,before.updated_at);assert.equal((await current(large)).active_revision_id,before.active_revision_id);
    await update(fn,{idle_seconds:30,queue_timeout_seconds:10});
  });
  await check('Concurrence partagée puis génération exclusive : maximum commun et instantanés conservés',async()=>{
    await update(fn,{max_instances:2,concurrency:2,storage:{...storage,concurrency:'shared'}});
    const pair=[start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:1800}}),start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:1800}})];
    await until(async()=>(await history(fn)).filter(row=>row.state==='running'&&row.handler_started).length===2,'Deux appels partagés non observés');assert.equal((await instances(fn)).length,2);
    assert((await Promise.all(pair.map(item=>item.promise))).every(row=>row.status===200));
    await update(fn,{max_instances:2,concurrency:1,storage});await until(async()=>(await instances(fn)).length===0,'Génération partagée non drainée');
    const exclusive=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:2200}});
    const old=await until(async()=>(await history(fn)).find(row=>row.state==='running'&&row.handler_started),'Appel exclusif non observé');
    await update(fn,{concurrency:2,storage:{...storage,concurrency:'shared'}},{environment:{PUBLIC_LABEL:'shared-generation'},secrets:{QUALIFICATION_SYNTHETIC_SECRET:secret}});
    const waiting=start(`/invoke/${fn.id}`);await until(async()=>(await history(fn)).some(row=>row.state==='queued'),'Ancienne génération exclusive non respectée');
    assert.equal((await history(fn)).filter(row=>row.state==='running').length,1);
    assert.equal(JSON.parse((await exclusive.promise).bytes).label,'first');assert.equal(JSON.parse((await waiting.promise).bytes).label,'shared-generation');
    const latest=(await history(fn)).find(row=>row.id===old.id);assert.equal(latest.state,'succeeded');await update(fn,{max_instances:1,concurrency:1,storage});
  });
  await check('Politique modifiée pendant attente : nouvelle admission refusée et appel admis conservé',async()=>{
    const active=start(`/invoke/${fn.id}?mode=delay`,{method:'POST',body:{ms:1800}});
    await until(async()=>(await history(fn)).some(row=>row.state==='running'&&row.handler_started),'Appel admis non observé');
    const queued=start(`/invoke/${fn.id}`);const row=await until(async()=>(await history(fn)).find(row=>row.state==='queued'),'Appel en file non observé');
    try{await policy({origins:['https://only-this-origin.example']});const denied=await queued.promise;assert.equal(denied.status,403);assert.equal(JSON.parse(denied.bytes).error,'network_policy_denied');assert.equal((await active.promise).status,200);}
    finally{await policy({});}
    const terminal=(await history(fn)).find(item=>item.id===row.id);assert.equal(terminal.handler_started,false);assert.equal(terminal.instance_id,null);
  });
  await check('Arrêt gracieux sous verrou SQLite : propriétaires, instance prête et baux joints avant sortie',async()=>{
    const peer=await create('shutdown-ready-instance',{min_instances:1,idle_seconds:90});await publish(peer,firstCode);await invoke(peer);
    await update(fn,{timeout_seconds:40});const before=(await invoke(fn,{suffix:'?mode=counter'})).json().count;
    const active=start(`/invoke/${fn.id}?mode=counter`,{method:'POST',body:{ms:30000}});
    const row=await until(async()=>(await history(fn)).find(row=>row.state==='running'&&row.handler_started),'Appel à arrêter non observé');
    const queued=start(`/invoke/${fn.id}`);await until(async()=>(await history(fn)).some(row=>row.state==='queued'),'Attente à arrêter non observée');
    const held=await holdWriter(fn);let stopped;
    try{
      active.abort();queued.abort();await Promise.all([active.settled,queued.settled]);
      stopped=(await remote('graceful-stop',fn,[peer.id]))[0];assert([0,143].includes(stopped.exit_code));assert(stopped.lifespan_completed&&stopped.lock_released);
    }finally{
      try{await held.release();}
      finally{if(stopped)await remote('start-control',fn,[stopped.restart_guard]);await healthy();}
    }
    assert.equal((await history(fn)).find(item=>item.id===row.id).state,'interrupted');
    assert.equal((await instances(fn)).length,0);assert((await instances(peer)).every(row=>!stopped.peer_before.instances.some(old=>old.id===row.id)));
    assert.equal((await invoke(fn,{suffix:'?mode=counter'})).json().count,before+1);await invoke(peer);await update(peer,{min_instances:0,idle_seconds:0});await update(fn,{timeout_seconds:10});
  });
  await check('Plafond global de 128 réceptions en attente puis libération sur déconnexion',async()=>{
    const fleet=[fn];for(let i=1;i<9;i++){const item=await create('queue-reception-'+i);await publish(item,firstCode);fleet.push(item);}
    const held=[];
    try{
      for(const item of fleet.slice(0,8)){
        held.push(...Array.from({length:16},()=>start(`/invoke/${item.id}`,{method:'POST',open:true,headers:{'Content-Length':'16','Content-Type':'application/json'}})));
        await until(async()=>(await history(item)).filter(row=>row.state==='receiving').length===16,'Lot de réceptions non observé');
      }
      await until(async()=>{let count=0;for(const item of fleet.slice(0,8))count+=(await history(item)).filter(row=>row.state==='receiving').length;return count===128;},'128 réceptions non observées');
      assert.equal((await invoke(fleet[8],{status:429})).json().error,'queue_full');
    }finally{operatorEvidence.push({mode:'receiving-client-connections',requests:held.map(item=>({...item.transport}))});for(const item of held)item.abort();await Promise.all(held.map(item=>item.settled));}
    await until(async()=>{for(const item of fleet.slice(0,8))if((await history(item)).some(row=>row.state==='receiving'||row.state==='queued'))return false;return true;},'Places de réception non libérées');
    await invoke(fleet[8]);
  });
  await check('Réception HTTP/1.1 bornée puis refus transmis après fin du corps',async()=>{
    const request=start(`/invoke/${fn.id}`,{method:'POST',open:true,headers:{'Content-Length':'16','Content-Type':'application/json'}});
    const begin=Date.now();
    try{
      const row=await until(async()=>(await history(fn)).find(row=>row.state==='receiving'),'Reception absente');
      await until(async()=>(await history(fn)).some(item=>item.id===row.id&&item.error_code==='body_timeout'),'Timeout serveur absent',36);
      assert(Date.now()-begin>=29000);assert.equal((await instances(fn)).length,0);
      request.end(Buffer.alloc(16,32));const reply=await request.promise;assert.equal(reply.status,408);
      outcomes.push({transport:'http/1.1',status:reply.status,elapsed_ms:Date.now()-begin,body_released_after_durable_timeout:true});
    }finally{request.abort();}
  });
  await check('Réception HTTP/2 bornée et refus immédiat sans fin du corps',async()=>{
    const {connect}=await import('node:http2');const connection=connect(base);let connectionClosed=false;connection.once('close',()=>{connectionClosed=true;});
    const begin=Date.now();let status,responseHeaders;const chunks=[];
    const request=connection.request({':method':'POST',':path':`/invoke/${fn.id}`,'x-serverless-token':readonly,'content-length':'16','content-type':'application/json'},{endStream:false});
    const result=new Promise((resolve,reject)=>{request.on('response',headers=>{responseHeaders=headers;status=headers[':status'];});request.on('data',chunk=>chunks.push(chunk));request.on('end',resolve);request.on('error',reject);request.setTimeout(40000,()=>{reject(new Error('h2_timeout'));request.close();});});
    try{await result;invocationTransports.push({client_request_id:randomUUID(),transport:'h2',id:responseHeaders['x-serverless-request-id']??null,function_id:fn.id,method:'POST',status,requested_code_hash:null,resolved_code_hash:responseHeaders['x-serverless-code-hash']??null});assert.equal(status,408);assert.equal(JSON.parse(Buffer.concat(chunks)).error,'body_timeout');assert(Date.now()-begin>=29000);outcomes.push({transport:'h2',status,elapsed_ms:Date.now()-begin,body_left_open:true});}
    finally{request.close();connection.close();try{await until(()=>connectionClosed,'h2_connection_not_joined',5);}catch(error){connection.destroy();await until(()=>connectionClosed,'h2_connection_not_destroyed',5);throw error;}}
  });
  // @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#intégration-et-portée-des-preuves
  // The count-limit group runs after this campaign's cleanup in public-invocations-suite.py.
  completed=true;
}finally{
  for(const guard of guards)try{await guard.release();}catch(error){cleanupErrors.push({step:'guard',error:diagnostic(error)});}
  await Promise.all(pending);
  for(const fn of functions.reverse()){
    try{
      const current=await admin.get(`/api/functions/${fn.id}`);
      if(current.status()===404)deletedFunctions.add(fn.id);
      else{
        assert.equal(current.status(),200);
        await until(async()=>(await history(fn)).every(row=>!['receiving','queued','admitted','running'].includes(row.state)),'Invocation serveur encore active au nettoyage',35);
        await manage(`/api/functions/${fn.id}`,{method:'DELETE'});deletedFunctions.add(fn.id);await checkpoint();
      }
      storageArchives.push(await purgeArchive(fn));
      const observed=(await remote('inspect',fn))[0];assert.equal(observed.instances.length,0);assert.equal(observed.containers.length,0);assert.equal(observed.networks.length,0);assert.equal(observed.leases.length,0);assert.equal(observed.reserved_channel_count,0);assert.equal(observed.active_invocations,0);assert.equal(observed.unreferenced_channel_count,0);
    }catch(error){cleanupErrors.push({step:'function',id:fn.id,error:diagnostic(error)});}
  }
  for(const t of tokens){try{await manage(`/api/tokens/${t.id}/revoke`,{method:'POST'});}catch(error){cleanupErrors.push({step:'token',id:t.id,error:diagnostic(error)});}}
  for(const extra of additionalServices)try{await manage(`/api/services/${extra.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'additional-service',id:extra.id,error:diagnostic(error)});}
  if(service)try{await manage(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service',id:service.id,error:diagnostic(error)});}
  if(namespace)try{await manage(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace',id:namespace.id,error:diagnostic(error)});}
  if(work)await rm(work,{recursive:true,force:true});await admin.dispose();
  const result={completed:completed&&!cleanupErrors.length,cleanup:!cleanupErrors.length,checks,failed:Math.max(completed?0:1,checks.filter(r=>r.status==='failed').length)+(cleanupErrors.length?1:0),skipped:0,cleanupErrors,resources:resources(),deleted_function_ids:[...deletedFunctions],storage_archives:storageArchives,pre_purge_revisions:archives,invocation_transports:invocationTransports,publications,version_evidence:versionEvidence,request_outcomes:outcomes,operator_evidence:operatorEvidence,guards:guards.map(g=>g.events)};
  assert(!JSON.stringify(result).includes(secret));await saveReport(result);assert.equal(cleanupErrors.length,0,'Nettoyage incomplet');
}
