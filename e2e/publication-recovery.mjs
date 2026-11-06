// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#limites-et-reprise-des-publications
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#limites-et-reprise-des-publications
import {purgeStorageArchive} from './storage-archives.mjs';
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {randomUUID,randomBytes} from 'node:crypto';
import https from 'node:https';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const run=promisify(execFile),root=fileURLToPath(new URL('../',import.meta.url));
const output=path.join(root,'.local/e2e'),base='https://serverless.lelabs.tech';
await mkdir(output,{recursive:true,mode:0o700});
const report=path.join(output,'publication-recovery.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
const state=JSON.parse(await readFile(path.join(output,'admin-session.json'),'utf8'));
const admin=await request.newContext({baseURL:base,storageState:state,timeout:30000});
const caller=await request.newContext({baseURL:base,timeout:30000});
const checks=[],observations=[],functions=new Map(),archives=[],cleanupErrors=[];
let session,namespace,service,work,credential,before,completed=false,needsStart=false;
const prefix='publication-recovery-'+randomUUID().slice(0,8);
const applicationSecret='publication-recovery-secret-'+randomUUID();
const sshArgs=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','spark-docker@10.77.0.24'];
const quote=value=>"'"+value.replaceAll("'","'\"'\"'")+"'";
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function ssh(command) {
  try {
    const result=await run('ssh',[...sshArgs,command],{timeout:45000,maxBuffer:2*1024*1024});
    return result.stdout;
  } catch(error) {
    const detail=error.stderr?.trim().split('\n').at(-1)?.slice(0,256)??'Commande interrompue';
    throw new Error('Observation SPARK refusée : '+detail);
  }
}
async function inspect(options={}) {
  // Reads persisted state through a read-only SQLite connection; only an explicit
  // interrupt request sends SIGKILL, after observing the exact candidate phase.
  const program=`import hashlib,json,sqlite3,subprocess,time
from pathlib import Path
assert Path('/etc/hostname').read_text().strip()=='infra-serverless'
options=json.loads(${JSON.stringify(JSON.stringify(options))})
def run(args):return subprocess.check_output(args,text=True)
control=json.loads(run(['docker','inspect','serverless-api']))[0]
environment=dict(entry.split('=',1) for entry in control['Config']['Env'])
root=Path(environment['SERVERLESS_STATE_HOST_PATH'])
db=sqlite3.connect('file:'+str(root/'control.sqlite3')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
installation=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
def validators():
 ids=run(['docker','ps','-aq','--filter','label=tech.p2enjoy.serverless.kind=validation','--filter','label=tech.p2enjoy.serverless.installation='+installation]).split()
 return json.loads(run(['docker','inspect',*ids])) if ids else []
result={'image':control['Image'],'installation':installation}
key=options.get('candidate')
if key:
 row=db.execute('SELECT state,error_code,reserved_bytes,configuration_cipher IS NULL AS payload_erased,revision_id FROM deployments WHERE id=?',(key,)).fetchone()
 assert row
 result['candidate']=dict(row)
 folder=root/'artifacts'/key
 result['candidate']['directory_exists']=folder.exists()
 result['candidate']['archive_bytes']=(folder/'archive.zip').stat().st_size if (folder/'archive.zip').exists() else 0
if options.get('function'):
 row=db.execute('SELECT active_revision_id,config_json,environment_json,secrets_cipher FROM functions WHERE id=?',(options['function'],)).fetchone()
 assert row
 result['function']={'active_revision_id':row[0],'configuration_sha256':hashlib.sha256(json.dumps(list(row)[1:]).encode()).hexdigest()}
if options.get('interrupt'):
 phase=options['interrupt'];assert phase in ('receiving','validating') and key
 observed=None;end=time.monotonic()+8
 while time.monotonic()<end:
  row=db.execute('SELECT state FROM deployments WHERE id=?',(key,)).fetchone()
  assert row[0]==phase, 'Fenetre de coupure manquee : '+row[0]
  if phase=='receiving':
   file=root/'artifacts'/key/'archive.zip'
   if file.exists() and file.stat().st_size>0:
    observed={'phase':phase,'partial_archive_bytes':file.stat().st_size};break
  else:
   for item in validators():
    if item['State']['Running'] and any(m['Destination']=='/code' and m['Source']==str(root/'artifacts'/key/'code') for m in item['Mounts']):
     observed={'phase':phase,'validation_container':item['Id']};break
   if observed:break
  time.sleep(.05)
 assert observed,'Phase physique non observee'
 run(['docker','kill','--signal','KILL','serverless-api'])
 stopped=json.loads(run(['docker','inspect','serverless-api']))[0]['State']
 assert not stopped['Running'] and stopped['ExitCode']==137
 result['interruption']={**observed,'control_stopped':True,'exit_code':stopped['ExitCode']}
else:
 result['reserved_bytes']=db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0]
 result['active_candidates']=db.execute("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()[0]
 result['validation_containers']=[item['Id'] for item in validators()]
 result['validation_channels']=[p.name for p in (root/'validation').iterdir()]
 result['archives']={}
 for row in db.execute('SELECT id,archive_sha256 FROM revisions WHERE stored_bytes>0'):
  file=root/'artifacts'/row[0]/'archive.zip'
  actual=hashlib.sha256(file.read_bytes()).hexdigest();assert actual==row[1]
  result['archives'][row[0]]=actual
 result['integrity']=db.execute('PRAGMA integrity_check').fetchone()[0]
 assert result['integrity']=='ok'
db.close()
print(json.dumps(result))`;
  return JSON.parse(await ssh('python3 -B -c '+quote(program)));
}
async function call(url,{method='GET',body,bytes,token=false,status=200,headers={}}={}) {
  const response=await (token?caller:admin).fetch(url,{method,data:bytes??body,
    headers:{...(token?{'X-Serverless-Token':credential}:{Origin:base,'X-CSRF-Token':session.csrf_token}),
      ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert.equal(response.status(),status,`${method} ${url}: attendu ${status}, reçu ${response.status()}`);
  const raw=await response.text();assert(!raw.includes(applicationSecret),'Valeur secrète exposée');
  return JSON.parse(raw);
}
async function check(name,action) {
  try {await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error) {checks.push({name,status:'failed',error:error.name});throw error;}
}
async function create(name) {
  const row=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name,config:{handler:'src/handlers.echo',memory_mib:128}}});
  functions.set(row.id,row);functionIds.push(row.id);return row;
}
const storageArchives=[],functionIds=[],deletedFunctions=new Set();
async function remove(fn) {
  if(!deletedFunctions.has(fn.id)){
    await call(`/api/functions/${fn.id}`,{method:'DELETE'});deletedFunctions.add(fn.id);
  }
  storageArchives.push(await purgeStorageArchive(fn.id,namespace.id));functions.delete(fn.id);
}
async function current(fn) {return call(`/api/functions/${fn.id}`,{token:true});}
async function prepare(fn,handler='src/handlers.echo',status=201) {
  const row=await current(fn);
  return call(`/api/functions/${fn.id}/deployments`,{method:'POST',token:true,status,headers:{'If-Match':String(row.updated_at)},
    body:{config:{...row.config,handler},configuration:{environment:{REVISION_LABEL:'stable'},secrets:{PUBLICATION_RECOVERY_SECRET:applicationSecret}}}});
}
async function upload(candidate,bytes,status=200) {
  return call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',token:true,bytes,status});
}
async function publish(fn,bytes) {
  const result=await upload(await prepare(fn),bytes);
  assert.equal(result.state,'published');assert(result.validation.valid&&result.validation.container_removed);
  return result;
}
async function waitState(candidate,phase) {
  const end=Date.now()+10000;
  while(Date.now()<end) {
    const row=await call(`/api/deployments/${candidate.id}`,{token:true});
    if(row.state===phase)return;
    assert(['prepared','receiving'].includes(row.state),'Phase non exercee : '+row.state);
    await pause(50);
  }
  assert.fail('Phase attendue absente : '+phase);
}
async function restoreControl() {
  await ssh('docker start serverless-api');
  const end=Date.now()+60000;
  while(Date.now()<end) {
    try {const response=await caller.get('/healthz',{timeout:2000});if(response.ok()) {needsStart=false;return;}} catch {}
    await pause(250);
  }
  assert.fail('Le contrôle ne reprend pas après son arrêt');
}
function interruptedUpload(candidate,bytes,partial) {
  let client;
  const outcome=new Promise(resolve=>{
    client=https.request(base+`/api/deployments/${candidate.id}/artifact`,{method:'PUT',headers:{
      'Content-Type':'application/zip','Content-Length':bytes.length,'X-Serverless-Token':credential}},response=>{
      response.resume();response.on('end',()=>resolve({status:response.statusCode}));
      response.on('error',error=>resolve({error:error.code??error.name}));
    });
    client.on('error',error=>resolve({error:error.code??error.name}));
    client.setTimeout(30000,()=>client.destroy(new Error('Upload timeout')));
    if(partial)client.write(bytes.subarray(0,192*1024));else client.end(bytes);
  });
  return {outcome,close:()=>client.destroy()};
}
async function interrupt(fn,bytes,phase,handler) {
  const previous=await current(fn),privateBefore=await inspect({function:fn.id});
  assert.deepEqual(previous.secret_names,['PUBLICATION_RECOVERY_SECRET']);
  const candidate=await prepare(fn,handler),pending=interruptedUpload(candidate,bytes,phase==='receiving');
  let cut,outcome;
  try {
    await waitState(candidate,phase);needsStart=true;
    cut=await inspect({candidate:candidate.id,function:fn.id,interrupt:phase});
  } finally {
    try {if(needsStart)await restoreControl();}
    finally {pending.close();outcome=await pending.outcome;}
  }
  assert(outcome.error||outcome.status>=500,'L’upload interrompu ne doit pas rendre un succès');
  const resumed=await call(`/api/deployments/${candidate.id}`,{token:true});
  assert.equal(resumed.state,'failed');assert.equal(resumed.error_code,'control_interrupted');assert.equal(resumed.revision_id,null);
  assert.deepEqual(await current(fn),previous);
  const after=await inspect({candidate:candidate.id,function:fn.id});
  assert.deepEqual(after.function,privateBefore.function);assert.equal(after.image,before.image);
  assert.equal(after.candidate.reserved_bytes,0);assert.equal(after.candidate.payload_erased,1);
  assert.equal(after.candidate.directory_exists,false);assert.equal(after.reserved_bytes,0);
  assert.deepEqual(after.validation_containers,[]);assert.deepEqual(after.validation_channels,[]);
  for(const [id,sha] of Object.entries(privateBefore.archives))assert.equal(after.archives[id],sha);
  observations.push({candidate_id:candidate.id,cut,after,transport:outcome});
}

try {
  session=await (await admin.get('/api/session')).json();assert(session.authenticated,'Session SSO réelle requise');
  before=await inspect();assert.equal(before.active_candidates,0);assert.equal(before.reserved_bytes,0);
  assert.deepEqual(before.validation_containers,[]);assert.deepEqual(before.validation_channels,[]);
  work=await mkdtemp(path.join(output,'publication-recovery-'));
  await cp(path.join(root,'qualification/src'),path.join(work,'src'),{recursive:true});
  await cp(path.join(root,'qualification/package.json'),path.join(work,'package.json'));
  await cp(path.join(root,'qualification/artifacts/deployment-delay.mjs'),path.join(work,'src/deployment-delay.mjs'));
  // Real packaged bytes keep the partial upload nonempty after file buffering.
  await writeFile(path.join(work,'src/upload-payload.bin'),randomBytes(256*1024));
  await writeFile(path.join(work,'serverless.yml'),JSON.stringify({service:prefix,provider:{name:'p2enjoy',runtime:'nodejs24.x'},
    functions:{publication:{handler:'src/handlers.echo'}},package:{patterns:['!**','src/**','package.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',path.join(work,'serverless.yml')],{cwd:root});
  const descriptor=JSON.parse(await readFile(path.join(work,'.serverless-p2/deployment.json'),'utf8'));
  const bytes=await readFile(path.join(work,'.serverless-p2',descriptor.artifacts.publication.file));assert(bytes.length>192*1024);
  namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});
  service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',status:201,body:{name:prefix}});
  credential=(await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name:'publication-limits-and-recovery',rights:['create','read','update','delete']}})).token;
  await check('64 candidats globaux : refus du 65e puis places libérées',async()=>{
    const limited=[];
    for(let i=0;i<9;i++)limited.push(await create('candidate-limit-'+i));
    for(const fn of limited.slice(0,8))for(let i=0;i<8;i++)await prepare(fn);
    await prepare(limited[8],'src/handlers.echo',429);
    assert.equal((await inspect()).active_candidates,64);
    await remove(limited[0]);await prepare(limited[8]);
    assert.equal((await inspect()).active_candidates,57);
    for(const fn of limited.slice(1))await remove(fn);
    assert.equal((await inspect()).active_candidates,0);
  });
  const fn=await create('revision-history');
  await check('Vingt révisions distinctes : refus du dépassement puis publication après retrait',async()=>{
    const revisions=[];
    for(let i=0;i<20;i++)revisions.push(await publish(fn,bytes));
    assert.equal(new Set(revisions.map(row=>row.revision_id)).size,20);
    const previous=await current(fn),extra=await prepare(fn);
    await upload(extra,bytes,409);assert.deepEqual(await current(fn),previous);
    const rejected=await inspect({candidate:extra.id});
    assert.equal(rejected.candidate.state,'prepared');assert.equal(rejected.candidate.reserved_bytes,0);
    assert.equal((await call(`/api/functions/${fn.id}/revisions?limit=100`,{token:true})).items.length,20);
    await call(`/api/functions/${fn.id}/revisions/${revisions[0].revision_id}`,{method:'DELETE',token:true});
    assert(!(revisions[0].revision_id in (await inspect()).archives));
    const next=await publish(fn,bytes);assert(!revisions.some(row=>row.revision_id===next.revision_id));
    assert.equal((await call(`/api/functions/${fn.id}/revisions?limit=100`,{token:true})).items.length,20);
    // Free room for the two recovery publications; retain the active revision.
    for(const row of revisions.slice(1,3))await call(`/api/functions/${fn.id}/revisions/${row.revision_id}`,{method:'DELETE',token:true});
  });
  await check('SIGKILL pendant réception partielle : reprise sans publication et nouvel upload réussi',async()=>{
    await interrupt(fn,bytes,'receiving','src/handlers.echo');await publish(fn,bytes);
  });
  await check('SIGKILL pendant validation Docker : destruction, conservation puis publication',async()=>{
    await interrupt(fn,bytes,'validating','src/deployment-delay.handler');await publish(fn,bytes);
  });
  completed=true;
} finally {
  if(needsStart)try {await restoreControl();} catch {cleanupErrors.push('control_restart');}
  for(const fn of functions.values())try {
    if(!deletedFunctions.has(fn.id)){
      const history=await call(`/api/functions/${fn.id}/revisions?limit=100`);
      for(const row of history.items)archives.push({function_id:fn.id,revision_id:row.id});
    }
    await remove(fn);
  } catch {cleanupErrors.push('function:'+fn.id);}
  if(service)try {await call(`/api/services/${service.id}`,{method:'DELETE'});} catch {cleanupErrors.push('service:'+service.id);}
  if(namespace)try {await call(`/api/namespaces/${namespace.id}`,{method:'DELETE'});} catch {cleanupErrors.push('namespace:'+namespace.id);}
  if(work)try {await rm(work,{recursive:true,force:true});} catch {cleanupErrors.push('local_files');}
  let after;
  try {
    after=await inspect();assert.equal(after.active_candidates,0);assert.equal(after.reserved_bytes,0);
    assert.deepEqual(after.validation_containers,[]);assert.deepEqual(after.validation_channels,[]);
    if(before)for(const [id,sha] of Object.entries(before.archives))assert.equal(after.archives[id],sha);
  } catch {cleanupErrors.push('state_or_archive_verification');}
  await admin.dispose();await caller.dispose();
  await writeFile(report,JSON.stringify({completed:completed&&!cleanupErrors.length,checks,skipped:0,cleanup:!cleanupErrors.length,
    cleanupErrors,before,observations,after,retained_archives:archives,storage_archives:storageArchives,function_ids:functionIds,namespace_id:namespace?.id,
    remaining_proofs:['Expiration réelle','Budget et marge disque','Déconnexion administrateur concurrente','Interruption pendant nettoyage','Invocation après rollback']},null,2)+'\n');
  assert.deepEqual(cleanupErrors,[]);
}
assert(completed);
