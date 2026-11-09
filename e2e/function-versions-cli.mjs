// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm,readdir} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {request} from 'playwright';

const root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),base='https://serverless.lelabs.tech';
const options=process.argv.slice(2),dockerMode=options.length?options[1]:null;
assert(options.length===0||(options.length===2&&options[0]==='--docker'&&['cli','qualification'].includes(dockerMode)),'expected_docker_cli_or_qualification');
const reportName=dockerMode?`function-versions-cli-docker-${dockerMode}.json`:'function-versions-cli.json';
const checks=[],evidence=[],cleanupErrors=[],tokens=[],secret='cli-version-private-'+randomUUID();
let api,caller,session,namespace,service,fn,work,manifest,publisher,scoped,reader,a,b,executionImage,completed=false,cleanup=false;
await mkdir(out,{recursive:true,mode:0o700});
async function save(){await writeFile(new URL(reportName,out),JSON.stringify({target:base,execution:dockerMode?`docker-${dockerMode}`:'host-python',image:executionImage,completed:completed&&cleanup,cleanup,cleanup_errors:cleanupErrors,
  checks,skipped:0,evidence,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[]},null,2)+'\n',{mode:0o600});}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}}
async function call(path,{method='GET',body,headers={},status=200}={}){const r=await api.fetch(path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...headers}});
  assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);const text=await r.text();assert(!text.includes(secret));return JSON.parse(text);}
async function until(action){const end=Date.now()+120000;while(Date.now()<end){const v=await action();if(v)return v;await new Promise(resolve=>setTimeout(resolve,150));}assert.fail('real_lifecycle_deadline');}
async function credential(name,rights,extra={}){const row=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights,...extra}});tokens.push(row);return row.token;}
async function executeInContainer(args,token){
  const modules={},files={};
  for(const name of (await readdir(new URL('adapter/',root))).filter(n=>n.endsWith('.py')))
    modules['adapter/'+name]=createHash('sha256').update(await readFile(new URL('adapter/'+name,root))).digest('hex');
  modules['function_code_hash.py']=createHash('sha256').update(await readFile(new URL('function_code_hash.py',root))).digest('hex');
  for(const name of ['serverless.yml','function-versions.cjs','version-marker.json'])files[name]=await readFile(new URL(name,work),'utf8');
  const mapped=args.map(value=>value===new URL('serverless.yml',work).pathname?'/tmp/serverless-cli-project/serverless.yml':value);
  const payload=JSON.stringify({args:mapped,target:base,token,secret,files,modules});
  const result=await new Promise(resolve=>{
    let inputError;const child=execFile('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','spark-docker@10.77.0.24',
      `python3 -B /srv/p2enjoy-serverless/e2e/function-version-cli-container.py ${dockerMode}`],{timeout:240000,maxBuffer:6*1024*1024},
      (error,stdout,stderr)=>resolve({error:error??inputError,stdout,stderr}));
    child.stdin.on('error',error=>{inputError=error;});child.stdin.end(payload);
  });
  for(const value of [token,secret])assert(!result.stdout.includes(value)&&!result.stderr.includes(value),'container_transport_private_output');
  assert.equal(result.stderr,'','container_transport_stderr');
  const receipt=JSON.parse(result.stdout);
  if(receipt.protocol_error){evidence.push({container_transport_error:{type:receipt.protocol_error,stage:receipt.stage}});await save();}
  assert.equal(result.error?.code??0,0,'container_transport_exit');assert(!receipt.protocol_error&&receipt.container_absent&&receipt.compose_definition_absent,'container_command_and_cleanup');
  assert.match(receipt.image,/^sha256:[0-9a-f]{64}$/);executionImage??=receipt.image;assert.equal(receipt.image,executionImage,'image_changed_during_campaign');
  assert.deepEqual(receipt.modules,modules);assert.deepEqual(receipt.files,Object.fromEntries(Object.entries(files).map(([name,text])=>[name,createHash('sha256').update(text).digest('hex')])));
  evidence.push({cli_container:{image:receipt.image,name:receipt.container_name,absent:true,command:args[0],code_only:args.includes('--code-only'),exit_code:receipt.exit_code,modules:receipt.modules,files:receipt.files,python:receipt.python,compose_stderr:receipt.compose_stderr,compose_definition_absent:true}});await save();
  return {error:receipt.exit_code?{code:receipt.exit_code}:null,stdout:receipt.stdout,stderr:receipt.stderr};
}
async function execute(args,token,success=true){const env={...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:token,QUALIFICATION_SYNTHETIC_SECRET:secret};delete env.UNRESOLVED_VERSION_PILOT_VALUE;
  const result=dockerMode?await executeInContainer(args,token):await new Promise(resolve=>execFile('python3',['-B','-m','adapter',...args],{cwd:root.pathname,env,timeout:180000,maxBuffer:4*1024*1024},
    (error,stdout,stderr)=>resolve({error,stdout,stderr})));
  assert.equal(result.error?.code??0,success?0:1,'real_cli_exit');assert(!result.stderr.includes('Traceback'));
  for(const sensitive of [secret,token])assert(!result.stdout.includes(sensitive)&&!result.stderr.includes(sensitive),'cli_credential_exposed');
  const report=JSON.parse(result.stdout);assert.equal(report.completed,success);return report;}
async function deploy(token,{codeOnly=false,success=true}={}){await writeFile(new URL('serverless.yml',work),JSON.stringify(manifest));
  return execute(['deploy','--config',new URL('serverless.yml',work).pathname,'--service',service.id,...(codeOnly?['--code-only']:[])],token,success);}
async function promote(hash,token=publisher,success=true){return execute(['promote','--function',fn.id,'--code-hash',hash],token,success);}
async function invoke(row,marker,handler){assert.equal(row.invocation_urls.state,'available');assert.equal(row.invocation_urls.selection,'version');assert(row.invocation_urls.items.length>=2);
  assert(row.invocation_urls.items.every(domain=>domain.urls.length>0),'each_domain_requires_an_invocable_url');
  for(const domain of row.invocation_urls.items)for(const entry of domain.urls){const r=await caller.get(entry.url,{headers:{'X-Serverless-Token':reader,Authorization:'Bearer qualification-business'}});assert.equal(r.status(),200);
    const body=await r.json();assert.equal(body.marker,marker);assert.equal(body.handler,handler);assert.equal(body.common,'service-value');assert.equal(body.local,'function-value');
    assert.equal(body.secret_sha256,createHash('sha256').update(secret).digest('hex'));assert.equal(r.headers()['x-serverless-code-hash'],row.code_hash);
    evidence.push({invoked_domain:domain.domain,code_hash:row.code_hash,invocation_id:r.headers()['x-serverless-request-id']});}}
await save();
try{
  api=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',out),'utf8')),timeout:180000});caller=await request.newContext({timeout:180000});
  session=await call('/api/session');assert(session.authenticated,'real_sso_session_required');work=new URL((await mkdtemp(new URL('function-versions-cli-',out).pathname))+'/','file:');
  await cp(new URL('../qualification/artifacts/function-versions.cjs',import.meta.url),new URL('function-versions.cjs',work));
  await writeFile(new URL('version-marker.json',work),JSON.stringify({value:'CLI-A'}));
  manifest={service:'version-cli',provider:{name:'p2enjoy',runtime:'nodejs24.x',memorySize:128,timeout:5,
    environment:{VERSIONS_COMMON:'service-value'},secret:{VERSIONS_SECRET:'${env:QUALIFICATION_SYNTHETIC_SECRET}'}},
    functions:{'release-cli':{handler:'function-versions.primary',environment:{VERSIONS_LOCAL:'function-value',VERSIONS_PERSIST:'yes'},
      p2enjoy:{cpu:.05,idle_seconds:0,storage:{data:{enabled:true,quota_mib:8},cache:{enabled:true,quota_mib:8}}}}},package:{patterns:['!**','function-versions.cjs','version-marker.json']}};
  await check('CLI complète : publication et promotion explicite du premier hash',async()=>{
    namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:'version-cli-'+randomUUID().slice(0,8)}});await save();
    service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:manifest.service}});await save();publisher=await credential('publish-and-promote',['read','create','update']);reader=await credential('invoke',['read']);
    const result=await deploy(publisher);assert.equal(result.mode,'complete');assert.equal(result.service_configuration.state,'applied');assert.equal(result.results.length,1);a=result.results[0];assert(a.code_changed);assert.equal(a.default_code_hash_at_publication,null);
    fn=await call(`/api/functions/${a.function_id}`);assert.equal(fn.active_revision_id,null);assert.equal(fn.config.memory_mib,128);await save();await invoke(a,'CLI-A','primary');
    const promoted=await promote(a.code_hash);assert.equal(promoted.state,'promoted');assert(promoted.changed);assert.equal((await call(`/api/functions/${fn.id}`)).active_revision_id,a.revision_id);
  });
  await check('CLI code seul scoped : provider non résolu, ressources/variables/secrets conservés',async()=>{
    scoped=await credential('scoped-pilot',['read','update'],{function_ids:[fn.id]});const before=await call(`/api/functions/${fn.id}`),common=await call(`/api/services/${service.id}`);
    manifest.provider.environment={VERSIONS_COMMON:'${env:UNRESOLVED_VERSION_PILOT_VALUE}'};manifest.provider.secret={VERSIONS_SECRET:'${env:UNRESOLVED_VERSION_PILOT_VALUE}'};
    const target=manifest.functions['release-cli'];target.handler='function-versions.secondary';target.memorySize=256;target.environment={VERSIONS_LOCAL:'unused-pilot-value'};target.events=[{http:{path:'pilot',method:'get'}}];
    await writeFile(new URL('version-marker.json',work),JSON.stringify({value:'CLI-B'}));const result=await deploy(scoped,{codeOnly:true});assert.equal(result.mode,'code_only');assert.equal(result.service_configuration.state,'preserved');b=result.results[0];assert(b.code_changed);assert.equal(b.default_code_hash_at_publication,a.code_hash);
    const after=await call(`/api/functions/${fn.id}`);assert.equal(after.updated_at,before.updated_at);assert.equal(after.active_revision_id,a.revision_id);assert.deepEqual(after.config,before.config);assert.deepEqual(after.environment,before.environment);assert.deepEqual(after.secret_names,before.secret_names);
    assert.deepEqual(await call(`/api/services/${service.id}`),common);await invoke(b,'CLI-B','secondary');
  });
  await check('CLI : réupload identique et promotion par un jeton limité à la fonction',async()=>{
    const before=await call(`/api/functions/${fn.id}`),same=(await deploy(scoped,{codeOnly:true})).results[0];assert(!same.code_changed);assert.equal(same.code_hash,b.code_hash);assert.equal(same.revision_id,b.revision_id);assert.equal((await call(`/api/functions/${fn.id}`)).updated_at,before.updated_at);
    await promote(b.code_hash,scoped);assert.equal((await call(`/api/functions/${fn.id}`)).active_revision_id,b.revision_id);assert.equal((await call(`/api/functions/${fn.id}/versions`)).total,2);
  });
  await check('CLI Read : publication et promotion refusées sans déplacer la cible',async()=>{
    await writeFile(new URL('version-marker.json',work),JSON.stringify({value:'CLI-C'}));const refused=await deploy(reader,{codeOnly:true,success:false});assert.equal(refused.results[0].error.status,403);
    const promotion=await promote(a.code_hash,reader,false);assert.equal(promotion.error.status,403);assert.equal((await call(`/api/functions/${fn.id}`)).active_revision_id,b.revision_id);assert.equal((await call(`/api/functions/${fn.id}/versions`)).total,2);
  });
  await check('CLI rollback, promotion sans changement et hash invalide',async()=>{
    await promote(a.code_hash,scoped);const before=await call(`/api/functions/${fn.id}`),same=await promote(a.code_hash,scoped);assert.equal(same.changed,false);assert.equal((await call(`/api/functions/${fn.id}`)).updated_at,before.updated_at);
    const bad=await promote('abcd',scoped,false);assert.equal(bad.error.code,'invalid_code_hash');await invoke(a,'CLI-A','primary');
  });
  completed=true;
}catch(error){if(!checks.some(row=>row.status==='failed'))checks.push({name:'Préparation ou fin',status:'failed',error:error.name});console.error(error.name,error.message);process.exitCode=1;}
finally{
  if(service&&!fn)try{fn=(await call(`/api/services/${service.id}/functions`)).items.find(row=>row.name==='release-cli');}catch(error){cleanupErrors.push({step:'function-identification',error:error.name});}
  if(fn)try{
    await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.length);await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation);
    const row=await call(`/api/archives/${fn.id}`),operation=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
    await until(async()=>{const value=await call(`/api/storage-operations/${operation.id}`);assert.notEqual(value.state,'aborted');return value.state==='completed';});assert.equal((await call(`/api/archives/${fn.id}`)).artifact_bytes,0);evidence.push({purged_function_id:fn.id,operation_id:operation.id});
  }catch(error){cleanupErrors.push({step:'function-purge',id:fn.id,error:error.name,message:error.message});}
  for(const row of tokens)try{await call(`/api/tokens/${row.id}/revoke`,{method:'POST'});}catch(error){cleanupErrors.push({step:'token',id:row.id,error:error.name});}
  if(service)try{await call(`/api/services/${service.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'service',error:error.name});}
  if(namespace)try{await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({step:'namespace',error:error.name});}
  if(work)await rm(work,{recursive:true});await api?.dispose();await caller?.dispose();cleanup=!cleanupErrors.length;await save();if(!completed||!cleanup)process.exitCode=1;
}
