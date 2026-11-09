// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#preuves-à-terminer
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#matrice-réelle
// Genuine old control, SSO, HTTP purge, EACCES, SQLite migration and guarded restoration.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,rm,rename} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium,request} from 'playwright';
import {publicationArchive} from './publication-fixtures.mjs';

const run=promisify(execFile),base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url);
const expectation=process.argv[2],phase=process.argv[3],options=process.argv.slice(4),guarded=options.includes('--restore-with-guard');
assert(['refusal','upgrade'].includes(expectation)&&['volumes','artifacts'].includes(phase));
assert(new Set(options).size===options.length&&options.every(v=>['--restore-with-guard','--source-schema007','--target-schema008'].includes(v)));
const sourceSchema=options.includes('--source-schema007')?'007':'006',targetSchema=options.includes('--target-schema008')?'008':'007';
assert(sourceSchema!=='007'||targetSchema==='008');assert(targetSchema!=='008'||expectation==='upgrade');
const historicalRevision='f56d79ebe3d1d84731bfd262d1e6a9d5b5a680c0';
const campaign=randomUUID(),namespaceName='code-purge-migration-'+campaign.slice(0,8),checks=[],evidence=[],events=[],cleanupErrors=[];
const stem=`function-version-purge-${targetSchema==='008'?sourceSchema+'-to-008-':''}${expectation}-${phase}${guarded?'-guard':''}`,report=new URL(stem+'.json',output);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py';
const versions006=['001_control.sql','002_login_limits.sql','003_deployments.sql','004_function_operations.sql','005_execution.sql','006_storage_commands.sql'];
const versions007=[...versions006,'007_function_code_hash.sql'],sourceVersions=sourceSchema==='007'?versions007:versions006,targetVersions=targetSchema==='008'?[...versions007,'008_function_versions.sql']:versions007;
let oldImage,child,ended=false,exitCode,credentials,browser,admin,session,work,fn,namespace,service,operationId,armed,completed=false,cleanup=false,driverStderr='';
async function save(){const temporary=new URL(stem+'.pending',output);await writeFile(temporary,JSON.stringify({target:base,campaign,expectation,phase,guarded,source_schema:sourceSchema,target_schema:targetSchema,completed:completed&&cleanup&&!cleanupErrors.length,cleanup,skipped:0,
  checks,evidence,events,cleanup_errors:cleanupErrors,local_work:work,historical_image:oldImage,current_image:armed?.current_image,namespace_id:namespace?.id,service_id:service?.id,function_id:fn?.id,operation_id:operationId},null,2)+'\n',{mode:0o600});await rename(temporary,report);}
async function until(action,message,seconds=120){const end=Date.now()+seconds*1000;while(Date.now()<end){const value=await action();if(value)return value;await new Promise(r=>setTimeout(r,100));}assert.fail(message);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function remoteStatus(){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,'status',campaign],{timeout:30000,maxBuffer:1024*1024});return JSON.parse(stdout);}
async function event(name){return until(()=>{const value=events.find(row=>row.event===name);assert(value||!ended,'Pilote arrêté avant '+name);return value;},'Événement absent : '+name,180);}
async function operation(op,extra={}){assert(!ended);const offset=events.length;child.stdin.write(JSON.stringify({op,...extra})+'\n');return until(()=>{const value=events.slice(offset).find(row=>row.event==='result'&&row.op===op);assert(value||!ended,'Pilote arrêté pendant '+op);return value?.value;},'Résultat absent : '+op,150);}
async function call(path,{method='GET',body,bytes,headers={},status=200}={}){
  const response=await admin.fetch(path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(response.status()),`${method} ${path}: ${response.status()} au lieu de ${status}`);return response.json();
}
async function receipt(id,predicate){return until(async()=>{const row=await call('/api/storage-operations/'+id);return predicate(row)?row:false;},'Reçu attendu absent');}
async function inspect(){return operation('inspect-purge-upgrade',{function_id:fn.id});}
async function restoreNow(independent=false){
  if(independent){assert.equal(armed.unit,'serverless-restore-version-purge-'+campaign);await run('ssh',[...ssh,'systemctl','start',armed.unit+'.service'],{timeout:180000,maxBuffer:1024*1024});}
  else if(!ended&&!child.stdin.writableEnded)child.stdin.end(JSON.stringify({op:'restore'})+'\n');
  await until(()=>ended,'Pilote non terminé',180);
  let state=await remoteStatus();
  if(!state.restored){await run('ssh',[...ssh,'python3','-B',helper,'restore',campaign],{timeout:240000,maxBuffer:1024*1024});}
  state=await until(async()=>{const value=await remoteStatus();return value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state)?value:false;},'Restauration/garde non terminée',180);
  const restored=state.restoration;assert(restored.databases_identical&&restored.artifacts_identical&&restored.configuration_unchanged&&restored.agent_healthy&&restored.control_healthy&&restored.reference_unchanged&&restored.temporary_directories_removed);
  assert.equal(restored.original_id,armed.original_id);assert.equal(restored.image,armed.current_image);
  if(independent){assert.equal(restored.independent,true);assert.notEqual(exitCode,0);}else assert.equal(exitCode,0);
  cleanup=true;evidence.push({scenario:'original-installation-restored',independent,driver_exit_code:exitCode,...state});await save();return state;
}
await mkdir(output,{recursive:true,mode:0o700});if(targetSchema==='008')await assert.rejects(readFile(report),error=>error.code==='ENOENT','preserve_previous_purge_migration_report');await save();
try{
  const reference=JSON.parse(await readFile(new URL(sourceSchema==='007'?'function-version-control-schema007-reference.json':'function-version-control-schema006-build.json',output),'utf8'));
  assert(reference.completed&&reference.current_tag_unchanged);if(sourceSchema==='006')assert.equal(reference.revision,historicalRevision);else assert.equal(reference.schema,'007');oldImage=reference.image;assert.match(oldImage,/^sha256:[0-9a-f]{64}$/);
  evidence.push({scenario:'genuine-schema'+sourceSchema+'-source-reference',revision:sourceSchema==='006'?historicalRevision:undefined,image:oldImage,compared_product_files:reference.compared_product_files??Object.keys(reference.embedded).length,attestation_sha256:reference.attestation_sha256});
  console.log('Identifiants SSO attendus sur stdin privée, utilisés uniquement en mémoire.');const input=createInterface({input:process.stdin});
  credentials=await new Promise((resolve,reject)=>input.once('line',line=>{try{resolve(JSON.parse(line));}catch{reject(new Error('invalid_private_input'));}finally{input.close();}}));
  assert(credentials&&typeof credentials.username==='string'&&typeof credentials.password==='string');
  child=spawn('ssh',[...ssh,'python3','-B',helper,'function-version-purge',campaign,oldImage,...options.filter(v=>v!=='--restore-with-guard')],{stdio:['pipe','pipe','pipe']});
  createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});
  child.stderr.on('data',bytes=>{driverStderr=(driverStderr+bytes.toString()).slice(-12000);});child.stdin.on('error',()=>{});
  child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
  armed=await event('guard-armed');await event('historical-ready');
  await check(`Vraie API${sourceSchema} : SSO, publication Docker et décision de purge sous EACCES`,async()=>{
    browser=await chromium.launch({headless:true});const context=await browser.newContext({locale:'fr-FR'}),page=await context.newPage();
    await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO'}).click();await page.waitForURL('https://oauth.lelabs.tech/**');
    await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);credentials=null;
    await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
    const state=await context.storageState();state.cookies=state.cookies.filter(row=>row.domain==='serverless.lelabs.tech');state.origins=[];
    admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});await browser.close();browser=null;
    session=await call('/api/session');assert(session.authenticated);
    namespace=await call('/api/namespaces',{method:'POST',body:{name:namespaceName},status:201});await save();
    service=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'code-purge-lifecycle'},status:201});await save();
    const otherService=await call(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'code-purge-other-service'},status:201});
    evidence.push({scenario:'real-service-for-correlation-rejections',service_id:otherService.id});await save();
    work=await mkdtemp(new URL('function-version-purge-package-',output).pathname);const bundle=await publicationArchive(work,'purge-upgrade-code');
    fn=await call(`/api/services/${service.id}/functions`,{method:'POST',status:201,body:{name:'code-retired-before-upgrade',config:{handler:bundle.handler,memory_mib:128,idle_seconds:0,min_instances:0,
      storage:{data:{enabled:false,quota_mib:8},cache:{enabled:false,quota_mib:8}}}}});await save();
    const candidate=await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,headers:{'If-Match':String(fn.updated_at)},body:{deployment_id:randomUUID(),handler:bundle.handler}});
    const published=await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:bundle.bytes});assert.equal(published.state,'published');assert(published.validation.valid&&published.validation.container_removed);
    const initial=await inspect();assert.deepEqual(initial.versions,sourceVersions);assert.equal(initial.has_code_hash_column,sourceSchema==='007');if(sourceSchema==='007')assert.match(initial.code[0].code_hash,/^[0-9a-f]{64}$/);assert.equal(initial.code.length,1);
    if(phase==='volumes'){
      const row=await call(`/api/functions/${fn.id}`),id=randomUUID();await call(`/api/functions/${fn.id}/cache-clear`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:id}});
      await receipt(id,row=>row.state==='completed');evidence.push({scenario:'maintenance-synchronized-by-real-cache-command',operation_id:id});
    }
    await call(`/api/functions/${fn.id}`,{method:'DELETE'});const archived=await call(`/api/archives/${fn.id}`);assert.equal(archived.storage_operation,null);
    await operation('deny-artifact',{function_id:fn.id});operationId=randomUUID();await save();
    await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(archived.updated_at)},body:{operation_id:operationId,confirm_name:archived.name}});
    if(phase==='artifacts')await receipt(operationId,row=>row.state==='pending'&&row.phase==='artifacts'&&row.error_code==='artifact_cleanup_pending');
    const pending=await inspect();assert.equal(pending.purge_commands[0].id,operationId);assert.equal(pending.purge_commands[0].phase,phase);assert.equal(pending.purge_guards[0].decision,'commit');
    assert(pending.code[0].empty_inventory&&pending.code[0].empty_events&&pending.code[0].stored_bytes>0);assert(pending.artifacts[candidate.id]);
    evidence.push({scenario:'genuine-pending-purge-before-upgrade',physical:pending,validation:published.validation});
  });
  await check(expectation==='refusal'?'007 actuelle : vrai refus et rollback006 intégral':`${targetSchema} : migration et API lisible avec purge conservée`,async()=>{
    const result=await operation(expectation==='refusal'?'upgrade-refusal':'upgrade-readable',{function_id:fn.id,phase});
    if(expectation==='refusal'){assert(result.migration_refused&&result.rollback_complete&&result.udf_error_seen);assert.deepEqual(result.after.versions,versions006);}
    else{
      assert(result.anonymous_api_readable);assert.deepEqual(result.after.versions,targetVersions);assert(result.after.has_code_hash_column);
      const originalCode=result.before.observation.code[0];assert(result.after.code.every(row=>row.code_hash===originalCode.code_hash&&row.stored_bytes>0));
      if(targetSchema==='008'){
        assert.equal(result.after.function.first_published_code_hash,originalCode.code_hash);assert.equal(result.after.function.first_promoted_at,originalCode.created_at);
        assert.equal(result.after.version_registry.length,sourceSchema==='007'?1:0);
        if(sourceSchema==='007'){const entry=result.after.version_registry[0];assert.equal(entry.code_hash,originalCode.code_hash);assert.equal(entry.state,'deleted');assert.equal(entry.revision_id,originalCode.id);assert.equal(entry.created_at,originalCode.created_at);}
        assert(result.after.old_column_conservation.tables.includes('deployments'));
      }assert.equal(result.after.purge_guards[0].id,operationId);
      assert.equal(result.after.purge_commands[0].result_version,result.before.observation.purge_commands[0].result_version);
      assert.equal(result.after.function.id,result.before.function_id);assert.equal(result.after.function.updated_at,result.before.observation.function.updated_at);
    }
    evidence.push({scenario:'migration-result',...result});
  });
  if(guarded){
    await check('Garde indépendante : perte du pilote et originaux entièrement rétablis',async()=>{await restoreNow(true);});
  }else{
    await check(expectation==='refusal'?'Même base006 reprise, purge terminée puis upgrade sain':`Relâchement, purge physique et reprise${targetSchema} persistante`,async()=>{
      if(expectation==='refusal'){const resumed=await operation('resume-historical',{function_id:fn.id});assert(resumed.same_database_resumed);assert.deepEqual(resumed.after.versions,versions006);evidence.push({scenario:'schema006-resumed-without-database-restore',...resumed});}
      await receipt(operationId,row=>row.state==='pending'&&row.phase==='artifacts'&&row.error_code==='artifact_cleanup_pending');
      const release=await operation('release-artifact',{function_id:fn.id});assert(release.released&&release.owner_changed_last&&release.descriptor_identity_confirmed);
      const done=await receipt(operationId,row=>row.state==='completed');const physical=await inspect();assert.equal(physical.code[0].stored_bytes,0);assert.equal(physical.artifacts[physical.code[0].id],false);assert.deepEqual(physical.purge_guards,[]);
      assert.equal(physical.agent[0].state,'purged');assert.deepEqual(physical.agent_volumes,[]);assert.deepEqual(physical.agent_leases,[]);
      if(expectation==='refusal')await operation('upgrade');else await operation('restart');
      await until(async()=>{try{const r=await admin.get('/api/storage-operations/'+operationId,{timeout:3000});return r.status()===200;}catch{return false;}},'API non rétablie');
      const after=await inspect();assert.deepEqual(after.versions,targetVersions);assert(after.has_code_hash_column);const originalCode=evidence.find(v=>v.scenario==='genuine-pending-purge-before-upgrade').physical.code[0];assert.equal(after.code[0].code_hash,originalCode.code_hash);
      if(targetSchema==='008'){assert.equal(after.function.first_published_code_hash,originalCode.code_hash);assert.equal(after.function.first_promoted_at,originalCode.created_at);assert.equal(after.version_registry.length,sourceSchema==='007'?1:0);if(sourceSchema==='007')assert.equal(after.version_registry[0].state,'deleted');}
      assert.equal((await call('/api/storage-operations/'+operationId)).state,'completed');assert((await call(`/api/archives/${fn.id}`)).purged_at);
      evidence.push({scenario:'purge-completed-and-persistent',release,receipt:done,physical_before_restart:physical,physical_after_restart:after});
    });
    await check('Installation d’origine restaurée par identité, configuration et données',async()=>{await restoreNow();});
  }
  assert(!events.some(row=>row.event==='invalid-driver-output'));completed=true;
}catch(error){evidence.push({scenario:'campaign-error',error:error.name});throw new Error('function_version_purge_upgrade_failed');}
finally{
  credentials=null;
  try{try{await browser?.close();}catch(error){cleanupErrors.push({resource:'browser',error:error.name});}
      try{await admin?.dispose();}catch(error){cleanupErrors.push({resource:'http-client',error:error.name});}}
  finally{
    if(child&&!cleanup){
      try{
        const status=await remoteStatus();
        if(status.not_started){assert(ended&&!events.some(row=>row.event==='guard-armed'));cleanup=true;}
        else if(armed){
          if(!ended&&!child.stdin.writableEnded)child.stdin.end(JSON.stringify({op:'restore'})+'\n');
          await until(()=>ended,'Pilote non terminé pendant reprise',180);
          let result=await remoteStatus();if(!result.restored){await run('ssh',[...ssh,'python3','-B',helper,'restore',campaign],{timeout:240000,maxBuffer:1024*1024});result=await remoteStatus();}
          assert(result.restored&&result.restoration.databases_identical&&result.restoration.artifacts_identical&&!result.driver_alive);evidence.push({scenario:'restoration-after-failure',...result});cleanup=true;
        }else assert.fail('Identité de garde non reçue');
      }catch(error){cleanupErrors.push({error:error.name});}
    }
    try{if(work)await rm(work,{recursive:true});if(driverStderr)await writeFile(new URL(stem+'-driver.log',output),driverStderr,{mode:0o600});}
    catch(error){cleanupErrors.push({resource:'local-work-or-diagnostic',error:error.name});}
    finally{await save();assert.deepEqual(cleanupErrors,[],'Restauration incomplète');}
  }
}
