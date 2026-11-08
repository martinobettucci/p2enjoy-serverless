// @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#configuration-de-service-et-surcharges
// @verifies docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuves-et-manuel
// Real CLI, HTTPS, SSO session, service tokens and Docker invocations; no substitute server.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {createHash,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',prefix='service-configuration-'+randomUUID().slice(0,8);
const report=path.join(out,'service-configuration.json');
await mkdir(out,{recursive:true,mode:0o700});
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
const caller=await request.newContext({baseURL:base,timeout:120000});
const session=await (await admin.get('/api/session')).json();assert(session.authenticated);
const secrets=Array.from({length:4},()=>randomUUID()+randomUUID()),tokens=[],checks=[],archives=[],cleanupErrors=[],observations=[];
const digest=value=>createHash('sha256').update(value).digest('hex');
let namespace,service,work,manifest,full,read,create,restricted,completed=false,fn={};
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),method+' '+url+': '+response.status());
  const text=await response.text();assert(secrets.every(value=>!text.includes(value)));
  return JSON.parse(text);
}
async function token(name,rights,extra={}){
  const value=await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name,rights,...extra},status:201});tokens.push(value.token);return value.token;
}
async function deploy(credential,success){
  await writeFile(path.join(work,'serverless.yml'),JSON.stringify(manifest));
  const value=await new Promise(resolve=>execFile('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',service.id],
    {cwd:root,timeout:300000,maxBuffer:4*1024*1024,env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:credential,
      SHARED_SECRET:secrets[0],LOCAL_SECRET:secrets[1]}},(error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr})));
  assert.equal(value.code,success?0:1,'Code de sortie CLI');
  for(const secret of [...secrets,...tokens])assert(!value.stdout.includes(secret)&&!value.stderr.includes(secret));
  const result=JSON.parse(value.stdout);assert.equal(result.completed,success);
  assert(!value.stderr.includes('Traceback'));
  const descriptor=await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8');
  assert(secrets.every(secret=>!descriptor.includes(secret)));
  return result;
}
async function functions(){return (await api(`/api/services/${service.id}/functions`)).items;}
async function current(name){return api(`/api/functions/${fn[name].id}`);}
async function invoke(name,query=''){
  const response=await caller.get(`/invoke/${fn[name].id}${query}`,{headers:{'X-Serverless-Token':read}});
  assert.equal(response.status(),200,'Invocation Docker');return response.json();
}
async function configure(body,headers={}){
  service=await api(`/api/services/${service.id}`);
  service=await api(`/api/services/${service.id}/configuration`,{method:'PUT',body,headers:{'If-Match':String(service.updated_at),...headers}});
}
async function purge(row){
  const archived=await api(`/api/archives/${row.id}`);assert.equal(archived.namespace_id,namespace.id);
  const operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archived.updated_at)},
    body:{operation_id:randomUUID(),confirm_name:archived.name}});
  const deadline=Date.now()+90000;let result=operation;
  while(result.state!=='completed'&&Date.now()<deadline){
    assert.notEqual(result.state,'failed');await new Promise(resolve=>setTimeout(resolve,200));
    result=await api(`/api/storage-operations/${operation.id}`);
  }
  assert.equal(result.state,'completed');
  const done=await api(`/api/archives/${row.id}`);assert(done.purged_at&&done.artifact_bytes===0);
  return {function_id:row.id,namespace_id:namespace.id,operation_id:operation.id,purged:true};
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
try{
  work=await mkdtemp(path.join(out,'service-configuration-code-'));
  await cp(path.join(root,'qualification/artifacts/service-configuration.cjs'),path.join(work,'handler.cjs'));
  await cp(path.join(root,'qualification/artifacts/throws.cjs'),path.join(work,'throws.cjs'));
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix},status:201});
  service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:prefix},status:201});
  full=await token('publication',['read','create','update']);read=await token('invocation',['read']);create=await token('creation',['read','create']);
  manifest={service:prefix,provider:{name:'p2enjoy',runtime:'node24',env:{SHARED_LABEL:'common-one'},secret:{SHARED_SECRET:'${env:SHARED_SECRET}'}},
    functions:{'configuration-overrides':{handler:'handler.handler',env:{SHARED_LABEL:'local-one',LOCAL_LABEL:'configuration-overrides'},secret:{SHARED_SECRET:'${env:LOCAL_SECRET}'}},'configuration-inherited':{handler:'handler.handler'}},
    package:{patterns:['!**','*.cjs']}};
  await check('Provider conservé dans le service et seules surcharges dans les fonctions',async()=>{
    const result=await deploy(full,true);assert.equal(result.results.length,2);
    for(const item of await functions())fn[item.name]=item;
    service=await api(`/api/services/${service.id}`);
    observations.push({scenario:'provider-placement',service_environment:service.environment,service_secret_names:service.secret_names,
      functions:Object.values(fn).map(row=>({id:row.id,name:row.name,environment:row.environment,secret_names:row.secret_names}))});
    assert.deepEqual(service.environment,{SHARED_LABEL:'common-one'});assert.deepEqual(service.secret_names,['SHARED_SECRET']);
    assert.deepEqual(fn['configuration-inherited'].environment,{});assert.deepEqual(fn['configuration-inherited'].secret_names,[]);
    assert.deepEqual(fn['configuration-overrides'].environment,{SHARED_LABEL:'local-one',LOCAL_LABEL:'configuration-overrides'});
    assert.deepEqual(fn['configuration-overrides'].secret_names,['SHARED_SECRET']);
    assert.equal(result.service_configuration.state,'applied');
  });
  await check('Invocations Docker : héritage et surcharge de secret effectifs',async()=>{
    assert.deepEqual(await invoke('configuration-overrides'),{label:'local-one',local:'configuration-overrides',secret_sha256:digest(secrets[1])});
    const expected={label:'common-one',local:null,secret_sha256:digest(secrets[0])};
    assert.deepEqual(await invoke('configuration-inherited'),expected);assert.deepEqual(await invoke('configuration-inherited'),expected);
  });
  await check('Modification commune et rotation : appels admis stables, suivants actualisés',async()=>{
    const before=await current('configuration-inherited');const running=invoke('configuration-inherited','?delay=4000');
    const deadline=Date.now()+15000;let busy=false;
    while(Date.now()<deadline){
      const rows=await api(`/api/functions/${fn['configuration-inherited'].id}/invocations`);
      if(rows.items.some(row=>row.state==='running')){busy=true;break;}
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    assert(busy,'Invocation réelle active avant modification commune');
    await configure({environment:{SHARED_LABEL:'common-two'},secrets:{SHARED_SECRET:secrets[2]}});
    assert.deepEqual(await running,{label:'common-one',local:null,secret_sha256:digest(secrets[0])});
    assert.deepEqual(await invoke('configuration-inherited'),{label:'common-two',local:null,secret_sha256:digest(secrets[2])});
    assert.deepEqual(await invoke('configuration-overrides'),{label:'local-one',local:'configuration-overrides',secret_sha256:digest(secrets[1])});
    assert.equal((await current('configuration-inherited')).active_revision_id,before.active_revision_id);
  });
  await check('Provider absent préservé et suppression de surcharge rétablissant l’héritage',async()=>{
    delete manifest.provider.env;delete manifest.provider.secret;
    manifest.functions['configuration-overrides'].env={SHARED_LABEL:null};manifest.functions['configuration-overrides'].secret={SHARED_SECRET:null};
    await deploy(full,true);assert.deepEqual((await current('configuration-overrides')).environment,{});
    assert.deepEqual((await current('configuration-overrides')).secret_names,[]);
    assert.deepEqual(await invoke('configuration-overrides'),{label:'common-two',local:null,secret_sha256:digest(secrets[2])});
    assert.deepEqual((await api(`/api/services/${service.id}`)).environment,{SHARED_LABEL:'common-two'});
  });
  await check('Droits : configuration commune refusée avant toute publication',async()=>{
    manifest.provider.env={SHARED_LABEL:'forbidden'};
    const before=await functions();let result=await deploy(create,false);
    assert.equal(result.error.status,403);assert.deepEqual(result.results,[]);
    restricted=await token('fonctions',['read','update'],{function_ids:[fn['configuration-overrides'].id,fn['configuration-inherited'].id]});
    result=await deploy(restricted,false);assert.equal(result.error.status,403);assert.deepEqual(result.results,[]);
    assert.deepEqual((await functions()).map(row=>[row.id,row.active_revision_id]),before.map(row=>[row.id,row.active_revision_id]));
    assert.deepEqual((await api(`/api/services/${service.id}`)).environment,{SHARED_LABEL:'common-two'});
    delete manifest.provider.env;
  });
  await check('Catégories provider vides : retrait des valeurs et secrets communs',async()=>{
    manifest.provider.env={};manifest.provider.secret={};await deploy(full,true);
    service=await api(`/api/services/${service.id}`);assert.deepEqual(service.environment,{});assert.deepEqual(service.secret_names,[]);
    assert.deepEqual(await invoke('configuration-inherited'),{label:null,local:null,secret_sha256:null});
  });
  await check('Échec partiel : code actif conservé et changement commun explicite',async()=>{
    const before=await current('configuration-overrides');manifest.provider.env={SHARED_LABEL:'partial'};
    manifest.functions['configuration-overrides'].handler='throws.handler';
    const result=await deploy(full,false);assert.equal(result.service_configuration.state,'applied');
    assert.equal(result.results[0].error.status,422);assert.equal(result.results[1].state,'published');
    assert.equal((await current('configuration-overrides')).active_revision_id,before.active_revision_id);
    assert.equal((await invoke('configuration-overrides')).label,'partial');assert.equal((await invoke('configuration-inherited')).label,'partial');
    manifest.functions['configuration-overrides'].handler='handler.handler';
  });
  await check('Redéploiement d’une ancienne configuration aplatie puis nouvelle valeur commune',async()=>{
    let row=await current('configuration-inherited');
    await api(`/api/functions/${row.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config:row.config,configuration:{environment:{SHARED_LABEL:'old-flat'},secrets:{SHARED_SECRET:secrets[3]}}}});
    assert.equal((await invoke('configuration-inherited')).label,'old-flat');
    await deploy(full,true);assert.deepEqual((await current('configuration-inherited')).environment,{});assert.deepEqual((await current('configuration-inherited')).secret_names,[]);
    await configure({environment:{SHARED_LABEL:'after-flat'},secrets:{SHARED_SECRET:secrets[2]}});
    assert.deepEqual(await invoke('configuration-inherited'),{label:'after-flat',local:null,secret_sha256:digest(secrets[2])});
  });
  await check('Version obsolète du service et collision effective refusées',async()=>{
    const stale=await api(`/api/services/${service.id}`);await configure({environment:{SHARED_LABEL:'current'}});
    await api(`/api/services/${service.id}/configuration`,{method:'PUT',body:{environment:{SHARED_LABEL:'stale'}},headers:{'If-Match':String(stale.updated_at)},status:409});
    manifest.functions['configuration-overrides'].env={SHARED_SECRET:'collision'};
    // The undeclared provider secret category preserves the existing service secret.
    delete manifest.provider.secret;
    const result=await deploy(full,false);assert.equal(result.results[0].error.status,422);
    assert.deepEqual((await current('configuration-overrides')).environment,{});
  });
  await check('Remplacement de 128 secrets et validation stricte du drapeau',async()=>{
    for(const prefix of ['OLD_','NEW_']){
      await configure({secrets:Object.fromEntries(Array.from({length:128},(_,index)=>[prefix+index,secrets[0]])),replace_secrets:true});
      assert.equal(service.secret_names.length,128);assert(service.secret_names.every(name=>name.startsWith(prefix)));
    }
    await api(`/api/services/${service.id}/configuration`,{method:'PUT',body:{replace_secrets:true},status:422});
    await api(`/api/services/${service.id}/configuration`,{method:'PUT',body:{secrets:Object.fromEntries(Array.from({length:129},(_,index)=>['TOO_'+index,secrets[0]])),replace_secrets:true},status:422});
    const row=await current('configuration-inherited');
    await api(`/api/functions/${row.id}`,{method:'PUT',body:{name:row.name,configuration:{replace_secrets:true,secrets:{}}},status:422});
    await configure({secrets:{},replace_secrets:true});assert.deepEqual(service.secret_names,[]);
  });
  await check('Configurations effectives : collision et dépassement refusés avant mutation',async()=>{
    let row=await current('configuration-overrides');
    await api(`/api/functions/${row.id}`,{method:'PUT',body:{name:row.name,config:row.config,configuration:{environment:{LOCAL_LABEL:'local'},secrets:{LOCAL_BLOCK:secrets[1]}}}});
    const before=await api(`/api/services/${service.id}`);
    await api(`/api/services/${service.id}/configuration`,{method:'PUT',body:{environment:{LOCAL_BLOCK:'collision'}},status:422});
    assert.equal((await api(`/api/services/${service.id}`)).updated_at,before.updated_at);
    await api(`/api/services/${service.id}/configuration`,{method:'PUT',body:{environment:Object.fromEntries(Array.from({length:128},(_,index)=>['COMMON_'+index,'value']))},status:422});
    assert.equal((await api(`/api/services/${service.id}`)).updated_at,before.updated_at);
    await configure({secrets:{SHARED_SECRET:secrets[0]}});
    row=await current('configuration-inherited');
    await api(`/api/functions/${row.id}`,{method:'PUT',body:{name:row.name,config:row.config,configuration:{environment:{SHARED_SECRET:'collision'}}},status:422});
    await api(`/api/services/${service.id}/functions`,{method:'POST',body:{name:'invalid-effective',config:{handler:'handler.handler'},configuration:{environment:{SHARED_SECRET:'collision'}}},status:422});
    assert.equal((await functions()).length,2);
    assert.deepEqual(await invoke('configuration-inherited'),{label:before.environment.SHARED_LABEL,local:null,secret_sha256:digest(secrets[0])});
  });
  await check('Fusion connue trop grande : CLI refusée avant toute modification',async()=>{
    const previous=structuredClone(manifest),before=await api(`/api/services/${service.id}`),rows=await functions();
    for(const [label,count,commonValue,localValue] of [['ascii',24,'x'.repeat(8192),'x'.repeat(8192)],['unicode',4,'é'.repeat(4096),'é'.repeat(8192)]]){
      manifest.provider.env=Object.fromEntries(Array.from({length:count},(_,index)=>['COMMON_'+index,commonValue]));
      manifest.functions={'configuration-too-large':{handler:'handler.handler',env:Object.fromEntries(Array.from({length:count},(_,index)=>['LOCAL_'+index,localValue]))}};
      const result=await deploy(full,false),after=await api(`/api/services/${service.id}`);
      observations.push({scenario:'known-payload-limit',encoding:label,service_changed:after.updated_at!==before.updated_at,report:result});
      assert.equal(result.error?.code,'configuration_body_too_large');assert.deepEqual(result.results,[]);
      assert.equal(after.updated_at,before.updated_at);
      assert.deepEqual((await functions()).map(row=>[row.id,row.updated_at]),rows.map(row=>[row.id,row.updated_at]));
    }
    manifest=previous;
  });
  await check('Redémarrage du contrôle : valeurs communes, surcharges et jeton persistants',async()=>{
    await configure({environment:{SHARED_LABEL:'after-restart'},secrets:{SHARED_SECRET:secrets[2]},replace_secrets:true});
    const ids=Object.values(fn).map(row=>row.id).sort();
    const script=`import json,shlex,socket,subprocess,sys,time,urllib.request
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
sys.path.insert(0,'/srv/p2enjoy-serverless/e2e')
from control_database import read_control
values={}
for line in Path('/etc/spark/env').read_text().splitlines():
 parts=shlex.split(line,comments=True)
 if len(parts)==1 and '=' in parts[0]:
  key,value=parts[0].split('=',1);values[key]=value
with read_control(Path(values['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3') as db:
 assert sorted(r[0] for r in db.execute('SELECT id FROM functions WHERE deleted_at IS NULL'))==${JSON.stringify(ids)}
 assert not db.execute("SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')").fetchone()[0]
 assert not db.execute('SELECT count(*) FROM function_operations').fetchone()[0]
docker=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
before=json.loads(subprocess.check_output(docker+['inspect','serverless-api'],timeout=30))[0]
reference=json.loads(subprocess.check_output(docker+['inspect','serverless-runtime-reference'],timeout=30))[0]
subprocess.run(['timeout','--kill-after=5s','50s']+docker+['restart','--time','10','serverless-api'],capture_output=True,check=True,timeout=60)
deadline=time.monotonic()+90
while True:
 try:
  with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=3) as response:assert response.status==200
  break
 except Exception:
  if time.monotonic()>=deadline:raise
  time.sleep(.25)
after=json.loads(subprocess.check_output(docker+['inspect','serverless-api'],timeout=30))[0]
peer=json.loads(subprocess.check_output(docker+['inspect','serverless-runtime-reference'],timeout=30))[0]
assert before['Id']==after['Id'] and before['Image']==after['Image']
assert before['State']['StartedAt']!=after['State']['StartedAt']
assert reference['Id']==peer['Id'] and reference['State']['StartedAt']==peer['State']['StartedAt']
print(json.dumps({'restarted':True,'image':after['Image'],'reference_unchanged':True}))
`;
    const result=await new Promise((resolve,reject)=>{
      const child=execFile('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],
        {timeout:180000,maxBuffer:1024*1024},(error,stdout)=>error?reject(new Error('restart_failed')):resolve(JSON.parse(stdout)));
      child.stdin.end(script);
    });observations.push({scenario:'control-restart',...result});
    assert.deepEqual(await invoke('configuration-inherited'),{label:'after-restart',local:null,secret_sha256:digest(secrets[2])});
    assert.deepEqual(await invoke('configuration-overrides'),{label:'after-restart',local:'local',secret_sha256:digest(secrets[2])});
    assert.deepEqual((await api(`/api/services/${service.id}`)).environment,{SHARED_LABEL:'after-restart'});
  });
  completed=true;
}catch(error){
  throw new Error('service_configuration_campaign_failed');
}finally{
  if(service){
    try{
      for(const row of await functions()){
        try{await api(`/api/functions/${row.id}`,{method:'DELETE'});archives.push(await purge(row));}
        catch(error){cleanupErrors.push({resource:row.id,error:error.name});}
      }
      await api(`/api/services/${service.id}`,{method:'DELETE'});
    }catch(error){cleanupErrors.push({resource:'service',error:error.name});}
  }
  if(namespace)try{await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});}catch(error){cleanupErrors.push({resource:'namespace',error:error.name});}
  if(work)await rm(work,{recursive:true,force:true});
  await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({completed:completed&&!cleanupErrors.length,checks,observations,skipped:0,cleanup:!cleanupErrors.length,cleanup_errors:cleanupErrors,
    namespace_id:namespace?.id,service_id:service?.id,function_ids:[...new Set([...Object.values(fn).map(row=>row.id),...archives.map(row=>row.function_id)])],storage_archives:archives},null,2)+'\n');
}
assert(completed&&!cleanupErrors.length);
