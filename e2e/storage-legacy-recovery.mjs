// @spec docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md
// @verifies docs/BACKLOG.md#sls-065 | docs/STORAGE_LEGACY_PROOF.md#parcours-réel
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile,writeFile,rename,mkdir,mkdtemp,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium,request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const run=promisify(execFile),base='https://serverless.lelabs.tech';
const output=new URL('../.local/e2e/',import.meta.url),campaign=randomUUID();
const mode=process.argv[2];assert(['--partial','--full'].includes(mode),'Choisir --partial ou --full');
const report=new URL(mode==='--partial'?'storage-legacy-partial.json':'storage-legacy-recovery.json',output);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py';
const checks=[],evidence=[],functions=[],cleanupErrors=[];
let child,ended=false,exitCode,events=[],browser,context,admin,session,work,completed=false,cleanup=false,build,currentImage,driverStderr='';
async function save(){const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({target:base,campaign,completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,checks,evidence,cleanup_errors:cleanupErrors,function_ids:functions.map(fn=>fn.id),historical_image:build?.historical_image,current_image:currentImage},null,2)+'\n',{mode:0o600});await rename(pending,report);}
async function until(action,message,seconds=90){const end=Date.now()+seconds*1000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,200));}assert.fail(message);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name,...(error.name==='AssertionError'?{message:error.message}:{})});throw error;}finally{await save();}}
async function remoteStatus(){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,'status',campaign],{timeout:30000,maxBuffer:1024*1024});return JSON.parse(stdout);}
async function waitEvent(name,seconds=90){return until(()=>{const value=events.find(row=>row.event===name);assert(value||!ended,`Pilote arrêté avant ${name}, code ${exitCode}`);return value;},'Événement absent : '+name,seconds);}
async function operation(op,extra={}){const offset=events.length;assert(!ended);child.stdin.write(JSON.stringify({op,...extra})+'\n');return until(()=>{const value=events.slice(offset).find(row=>row.event==='result'&&row.op===op);assert(value||!ended,'Pilote arrêté pendant '+op);return value?.value;},'Opération sans résultat : '+op,120);}
async function call(path,{method='GET',body,bytes,headers={},status=200}={}){
  const response=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()} au lieu de ${status}`);
  if(method==='POST'&&path.endsWith('/purge'))assert.equal(response.headers().location,'/api/storage-operations/'+body.operation_id);
  return response.json();
}
async function receipt(id,predicate){return until(async()=>{const row=await call('/api/storage-operations/'+id);return predicate(row)?row:false;},'État attendu du reçu absent');}
async function purge(fn){const row=await call('/api/archives/'+fn.id),id=randomUUID();const result=await call(`/api/archives/${fn.id}/purge`,{method:'POST',body:{operation_id:id,confirm_name:row.name},headers:{'If-Match':String(row.updated_at)},status:[200,202]});return {id,result};}

await mkdir(output,{recursive:true,mode:0o700});await save();
let credentials;
try{
  if(mode==='--full'){
    console.log('Identifiants SSO attendus sur stdin, utilisés en mémoire uniquement.');
    const input=createInterface({input:process.stdin});
    credentials=await new Promise((resolve,reject)=>input.once('line',line=>{
      try{resolve(JSON.parse(line));}catch{reject(new Error('invalid_sso_credentials_input'));}finally{input.close();}
    }));
    assert(credentials&&typeof credentials.username==='string'&&typeof credentials.password==='string');
  }
  build=JSON.parse(await readFile(new URL('storage-legacy-build.json',output),'utf8'));assert(build.completed);
  child=spawn('ssh',[...ssh,'python3','-B',helper,mode==='--partial'?'partial':'historical',campaign,build.historical_image],{stdio:['pipe','pipe','pipe']});
  createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});
  // Only fixed JSON events enter the report; diagnostic stderr cannot expose session data.
  child.stderr.on('data',bytes=>{driverStderr=(driverStderr+bytes.toString()).slice(-8000);});child.stdin.on('error',()=>{});
  child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
  currentImage=(await waitEvent('guard-armed')).current_image;assert.match(currentImage,/^sha256:[0-9a-f]{64}$/);
  if(mode==='--partial'){
    await check('Pilote tué après le premier renommage : restauration indépendante des originaux',async()=>{
      await waitEvent('first-directory-moved');
      await until(()=>ended,'Pilote non terminé',20);assert.notEqual(exitCode,0);
      const result=await until(async()=>{const value=await remoteStatus();return value.restored?value:false;},'Garde indépendante non terminée',150);
      assert(result.restoration.independent&&result.restoration.databases_identical&&result.restoration.artifacts_identical);
      assert.equal(result.driver_alive,false);evidence.push(result);cleanup=true;
    });
  }else{
    const ready=await waitEvent('historical-ready',150);evidence.push(ready);
    await check('Ancienne API : SSO réel, deux publications Docker et suppression avant registre',async()=>{
      browser=await chromium.launch({headless:true});context=await browser.newContext({locale:'fr-FR'});const page=await context.newPage();
      await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO'}).click();await page.waitForURL('https://oauth.lelabs.tech/**');
      await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);
      credentials=null;await page.locator('input[type=submit],button[type=submit]').first().click();
      await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
      const state=await context.storageState();state.cookies=state.cookies.filter(row=>row.domain==='serverless.lelabs.tech');state.origins=[];
      admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});await browser.close();browser=null;
      session=await call('/api/session');assert(session.authenticated);
      const namespace=await call('/api/namespaces',{method:'POST',body:{name:'legacy-'+campaign.slice(0,8)},status:201});
      const service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'archived-code'},status:201});
      work=await mkdtemp(new URL('legacy-archives-',output).pathname);const bundle=await publicationArchive(work,'historical-publication');
      const config={handler:'publication.handler',runtime:'node24',memory_mib:256,cpu:.2,timeout_seconds:10,idle_seconds:0,min_instances:0,max_instances:1,concurrency:1,queue_timeout_seconds:10,storage:{data:{enabled:false,quota_mib:8},cache:{enabled:false,quota_mib:8},concurrency:'exclusive'}};
      for(const name of ['archive-without-volumes','archive-unexpected-registry']){
        const fn=await call(`/api/services/${service.id}/functions`,{method:'POST',body:{name,config,configuration:{environment:{},secrets:{}}},status:201});functions.push(fn);
        const candidate=await call(`/api/functions/${fn.id}/deployments`,{method:'POST',headers:{'If-Match':String(fn.updated_at)},body:{config,configuration:{environment:{},secrets:{}},events:{}},status:201});
        const published=await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:bundle.bytes});
        assert.equal(published.state,'published');assert(published.validation.valid&&published.validation.container_removed);assert.equal(published.revision_id,candidate.id);
        assert.equal((await call('/api/functions/'+fn.id)).active_revision_id,candidate.id);
        assert.equal((await call('/api/functions/'+fn.id,{method:'DELETE'})).data_policy,'archive');
        const physical=await operation('inspect',{function_id:fn.id});assert.equal(physical.versions.length,3);assert.deepEqual(physical.agent,[]);assert(physical.artifacts[candidate.id]);
        evidence.push({scenario:'historical-archive',function_id:fn.id,revision_id:candidate.id,archive_sha256:bundle.sha256,validation:published.validation,physical});
      }
    });
    await check('Migration réelle 001–003 vers 001–006 : session et archives conservées',async()=>{
      const current=await operation('upgrade');assert.equal(current.image,currentImage);
      session=await call('/api/session');assert(session.authenticated);
      for(const fn of functions){const row=await call('/api/archives/'+fn.id);assert(row.artifact_bytes>0&&row.storage.available&&!row.storage.registered);const physical=await operation('inspect',{function_id:fn.id});assert.equal(physical.versions.length,6);assert.deepEqual(physical.agent,[]);evidence.push({scenario:'migrated-archive',function_id:fn.id,physical});}
    });
    await check('Archive sans registre : purge terminée, absence persistée et aucun reçu agent inventé',async()=>{
      const fn=functions[0],action=await purge(fn);const done=await receipt(action.id,row=>row.state==='completed');
      const physical=await operation('inspect',{function_id:fn.id});assert.deepEqual(physical.agent,[]);assert.deepEqual(physical.agent_receipts,[]);assert.deepEqual(physical.guards,[]);assert.equal(physical.commands[0].storage_absent,1);assert.equal(physical.commands[0].id,action.id);
      assert.equal(physical.reserved_bytes,0);assert(physical.revisions.every(row=>row.stored_bytes===0));assert(Object.values(physical.artifacts).every(value=>!value));
      const row=await call('/api/archives/'+fn.id);assert(row.purged_at&&row.artifact_bytes===0);evidence.push({scenario:'absent-storage-purge',receipt:done,physical});
    });
    await check('Registre apparu après décision : reçu conservé et code protégé après redémarrage',async()=>{
      const fn=functions[1];await operation('deny-artifact',{function_id:fn.id});const action=await purge(fn);
      const pending=await receipt(action.id,row=>row.state==='pending'&&row.phase==='artifacts'&&row.error_code==='artifact_cleanup_pending');
      const before=await operation('inspect',{function_id:fn.id});assert.equal(before.commands[0].storage_absent,1);assert.equal(before.guards[0].decision,'commit');
      evidence.push({scenario:'contradiction-before-registry',operation_id:action.id,pending,before});await save();
      const appeared=await operation('introduce-storage',{function_id:fn.id});
      const changed=await receipt(action.id,row=>row.state==='pending'&&row.error_code==='storage_state_changed');assert.equal(changed.result_version,pending.result_version);
      const protectedCode=await operation('inspect',{function_id:fn.id});evidence.push({scenario:'contradiction-after-registry',operation_id:action.id,appeared,receipt:changed,physical:protectedCode});await save();assert.deepEqual(protectedCode.artifacts,before.artifacts);assert.deepEqual(protectedCode.revisions,before.revisions);assert.equal(protectedCode.agent.length,1);assert.deepEqual(protectedCode.agent_receipts,[]);
      await operation('restart');
      await until(async()=>{let response;try{response=await admin.get('/api/storage-operations/'+action.id,{timeout:3000});}catch{return false;}if([502,503].includes(response.status()))return false;assert.equal(response.status(),200);return true;},'API non rétablie');
      const restarted=await receipt(action.id,row=>row.state==='pending'&&row.error_code==='storage_state_changed');assert.equal(restarted.result_version,pending.result_version);
      const after=await operation('inspect',{function_id:fn.id});evidence.push({scenario:'contradiction-after-restart',operation_id:action.id,receipt:restarted,physical:after});await save();assert.deepEqual(after,protectedCode);assert.equal((await call('/api/archives/'+fn.id)).purged_at,null);
      evidence.push({scenario:'unexpected-registry-after-absence',operation_id:action.id,before,appeared,receipt:restarted,after});
    });
  }
  completed=true;
}catch(error){
  evidence.push({scenario:'campaign-error',error:error.name,...(error.name==='AssertionError'?{message:error.message}:{})});
  // Browser errors can contain input arguments: never rethrow their message, stack or cause.
  throw new Error('storage_legacy_campaign_failed');
}finally{
  credentials=null;await browser?.close();await admin?.dispose();
  if(child&&!cleanup){
    try{
      if(!ended&&!child.stdin.writableEnded)child.stdin.end(JSON.stringify({op:'restore'})+'\n');
      let closureFailed=false;
      try{await until(()=>ended,'Pilote non terminé après demande de restauration',180);}catch{closureFailed=true;}
      let result=await remoteStatus();
      if(result.not_started){assert(ended&&!events.some(row=>row.event==='guard-armed'));evidence.push({scenario:'preflight-stopped-before-window'});cleanup=true;}
      else{
        if(!result.restored||closureFailed){await run('ssh',[...ssh,'python3','-B',helper,'restore',campaign],{timeout:240000,maxBuffer:1024*1024});result=await remoteStatus();}
        assert(result.restored&&result.restoration.databases_identical&&result.restoration.artifacts_identical);assert.equal(result.driver_alive,false);
        evidence.push({scenario:'original-installation-restored',driver_exit_code:exitCode,...result});cleanup=true;
        if(mode==='--full'&&completed)assert.equal(exitCode,0,'Le pilote a terminé anormalement malgré la restauration');
      }
    }catch(error){cleanupErrors.push({error:error.name,...(error.name==='AssertionError'?{message:error.message}:{})});}
  }
  if(work)await rm(work,{recursive:true,force:true});if(driverStderr)await writeFile(new URL('storage-legacy-driver.log',output),driverStderr,{mode:0o600});await save();assert.deepEqual(cleanupErrors,[],'Restauration incomplète');
}
