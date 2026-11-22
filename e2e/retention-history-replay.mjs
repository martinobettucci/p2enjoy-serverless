// @spec docs/BACKLOG.md#sls-132 | docs/RETENTION_SCHEMA_011.md#âge-authentique-sur-copies-migrées
// @verifies docs/BACKLOG.md#sls-132 | docs/RETENTION_SCHEMA_011.md#âge-authentique-sur-copies-migrées
// @spec docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md#parcours-gardé-distinct
// @verifies docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md#lecture-publique-restitution-et-preuves-propres
// Real sealed backups, native syscall gates, SSO/API reads and independent DEV restoration.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,readFile,writeFile,rename} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium} from 'playwright';

const current=process.argv[4]==='--target-schema011';
const kind=process.argv[2],mode=process.argv[3];assert((process.argv.length===4||(process.argv.length===5&&current))&&['source','terminal'].includes(kind)&&['invalid','not-eligible','preflight','age','seed-loss','observer-loss','foreign-namespace'].includes(mode),'explicit_retention_replay_kind_and_mode_required');
assert(mode!=='foreign-namespace'||kind==='source','foreign_namespace_requires_live_source');
const observationMode=mode==='foreign-namespace'?(current?'age':'preflight'):mode;
const run=promisify(execFile),campaign=randomUUID(),base='https://serverless.lelabs.tech';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py',module='/srv/p2enjoy-serverless/e2e/retention-history-replay.py';
const out=new URL('../.local/e2e/',import.meta.url),report=new URL(`retention-history-replay-${kind}-${mode}-${campaign}.json`,out);
const capture=kind==='source'?'schedule-retention-9a2a4cd1eb134c20b4e1c5a1a1bdc7c0':'schedule-terminal-history-a3993b7d64f14650933cf03960c3d3b0',events=[],checks=[],observations=[],refusals=[];
let child,ended=false,exitCode=null,browser,admin,session,credentials,ready,restoration,before,source,foreignNamespace,namespaceCreation;
let completed=false,cleanup=false,failure=null,errors='',saveQueue=Promise.resolve();
function save(){saveQueue=saveQueue.then(async()=>{const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({campaign,kind,mode,source_capture:capture,target_schema:current?'011':'009',completed:completed&&cleanup&&!failure,cleanup,skipped:0,checks,events,observations,refusals,exit_code:exitCode,failure,restoration,foreign_namespace:foreignNamespace,namespace_creation:namespaceCreation},null,2)+'\n',{mode:0o600});await rename(pending,report);});return saveQueue;}
async function until(action,message,seconds=90){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,250));}assert.fail(message);}
async function event(name,seconds=370){return until(()=>{const value=events.find(v=>v.event===name);assert(value||!ended,'deployment_driver_stopped');return value;},'deployment_event_missing',seconds);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function operation(op){const offset=events.length;assert(!ended);child.stdin.write(JSON.stringify({op})+'\n');return until(()=>{const value=events.slice(offset).find(v=>v.event==='result'&&v.op===op);assert(value||!ended,'deployment_driver_stopped');return value?.value;},'operator_result_missing');}
async function remote(op){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,op,campaign],{timeout:150000,maxBuffer:32*1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
async function verifySource(operation='verify'){const {stdout}=await run('ssh',[...ssh,'python3','-B',module,operation,capture],{timeout:45000,maxBuffer:1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
async function native(identifier=campaign){
 const program='campaign='+JSON.stringify(identifier)+'\n'+String.raw`
import hashlib,json,os,socket,subprocess,time,uuid
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless' and str(uuid.UUID(campaign))==campaign
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
rows=json.loads(subprocess.check_output(D+['inspect','serverless-api','serverless-runtime-reference'],text=True,timeout=20))
services=[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'running':v['State']['Running'],'health':v['State']['Health']['Status']} for v in rows]
assert all(v['running'] and v['health']=='healthy' for v in services)
names=['/etc/spark/env','/run/spark/secrets','/etc/spark/routes','/etc/spark/env.?']
official={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() if Path(name).exists() else None for name in names}
present=[prefix for prefix in ['storage-absence-','function-version-purge-','function-version-unknown-first-','instance-limit-'] if (Path('/srv/p2enjoy-serverless/qualification-history')/(prefix+campaign)).exists()]
print(json.dumps({'services':services,'official_sha256':official,'campaign_directories':present,'sampled_at':time.time()}))
`;
 return new Promise((resolve,reject)=>{const process=execFile('ssh',[...ssh,'python3 -B -'],{timeout:40000,maxBuffer:1024*1024},(error,stdout)=>{if(error){reject(error);return;}try{resolve(JSON.parse(stdout));}catch(error){reject(error);}});process.stdin.on('error',reject);process.stdin.end(program);});
}
const flags=(id,observation)=>[`--retention-history=${id}`,`--retention-observation=${observation}`,'--guard-seconds=120',...(current?['--retention-target-schema011']:[])];
async function refusal(name,helperMode,args,reason,imageOverride){const identifier=randomUUID();let rejected;try{await run('ssh',[...ssh,'python3','-B',helper,helperMode,identifier,imageOverride??(current?before.services[0].image:(source?.images.control.image??before.services[0].image)),...args],{timeout:45000,maxBuffer:1024*1024});}catch(error){assert.equal(error.code,1);assert(String(error.stderr).includes(reason),'expected_refusal_reason_missing');rejected={name,reason,campaign:identifier,exit_code:error.code,stderr_sha256:createHash('sha256').update(String(error.stderr)).digest('hex')};}assert(rejected,'refusal_missing');const after=await native(identifier);assert.deepEqual(after.services,before.services);assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.campaign_directories,[]);refusals.push(rejected);}
async function api(url,status=200,{method='GET',body}={}){assert(Date.now()/1000<ready.retention_replay.observation.start_boundary+110,'api_replay_window_expired');const response=await admin.fetch(base+url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token},timeout:10000});assert.equal(response.status(),status);return response.json();}
function restored(value,independent){assert(value.control_healthy&&value.agent_healthy&&value.directories_identical&&value.databases_identical&&value.artifacts_identical&&value.configuration_unchanged&&value.reference_unchanged&&value.temporary_directories_removed);assert.equal(value.independent,independent);assert.equal(value.original_id,before.services[0].id);assert.equal(value.image,before.services[0].image);}
function joined(value){assert(value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state));}

// @verifies docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md#refus-du-périmètre-cloné
async function fixtureApi(url,status,rescue=false,method='GET'){
 if(!rescue)return api(url,status,{method});
 const response=await admin.fetch(base+url,{method,headers:{Origin:base,'X-CSRF-Token':session.csrf_token},timeout:10000});
 assert.equal(response.status(),status);return response.json();
}
async function findOwnedNamespace(rescue=false){
 assert(namespaceCreation);assert.equal(namespaceCreation.name,'outside-retention-scope-'+campaign);
 const listed=await fixtureApi('/api/namespaces?limit=100',200,rescue);assert(Array.isArray(listed.items)&&listed.items.length<100,'namespace_cleanup_list_truncated');
 const matches=listed.items.filter(v=>v.name===namespaceCreation.name);assert(matches.length<=1,'ambiguous_namespace_fixture');
 if(!matches.length)return null;
 const found=matches[0];assert(!namespaceCreation.before_ids.includes(found.id),'preexisting_namespace_not_owned');assert.match(found.id,/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/);
 if(foreignNamespace)assert.equal(found.id,foreignNamespace.id,'namespace_identity_changed');
 const row=await fixtureApi(`/api/namespaces/${found.id}`,200,rescue);assert.equal(row.id,found.id);assert.equal(row.name,namespaceCreation.name);
 assert.deepEqual((await fixtureApi(`/api/namespaces/${found.id}/services?limit=100`,200,rescue)).items,[],'namespace_fixture_not_empty');
 return row;
}
async function removeForeignNamespace(rescue=false){
 const owned=await findOwnedNamespace(rescue);
 if(owned){const url=`/api/namespaces/${owned.id}`;await fixtureApi(url,200,rescue,'DELETE');await fixtureApi(url,404,rescue);}
 foreignNamespace=null;namespaceCreation=null;
}

async function refusedNative(){
 const expected={campaign,original:before.services[0].id,temporary:ready.container.id,image:current?before.services[0].image:source.images.control.image,installation:source.installation_id};
 const program='expected='+JSON.stringify(expected)+'\n'+String.raw`
import json,os,socket,subprocess,uuid
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
assert str(uuid.UUID(expected['campaign']))==expected['campaign']
work=Path('/srv/p2enjoy-serverless/qualification-history')/('instance-limit-'+expected['campaign'])
item=json.loads((work/'restore.json').read_text())
assert not item.get('restored') and item['original']['id']==expected['original']
assert item['temporary_installation']==item['installation']==expected['installation']
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
rows=json.loads(subprocess.check_output(D+['inspect',expected['original'],expected['temporary']],text=True,timeout=20))
original,temporary=rows
assert original['Id']==expected['original'] and not original['State']['Running']
assert temporary['Id']==expected['temporary'] and temporary['State']['Running'] and temporary['Image']==expected['image']
assert temporary['Config']['Labels']['com.docker.compose.project']==item['project']
print(json.dumps({'restored':False,'original_id':original['Id'],'original_running':False,'temporary_id':temporary['Id'],'temporary_running':True,'temporary_image':temporary['Image'],'installation_id':item['temporary_installation']}))
`;
 return new Promise((resolve,reject)=>{const p=execFile('ssh',[...ssh,'python3 -B -'],{timeout:40000,maxBuffer:1024*1024},(error,stdout)=>{if(error){reject(error);return;}try{resolve(JSON.parse(stdout));}catch(error){reject(error);}});p.stdin.on('error',reject);p.stdin.end(program);});
}

await mkdir(out,{recursive:true,mode:0o700});await save();
try{
 if(['preflight','age','foreign-namespace'].includes(mode)&&!(current&&mode==='preflight')){
  assert(!process.stdin.isTTY,'private_pipe_required');const input=createInterface({input:process.stdin});credentials=await new Promise((resolve,reject)=>{input.once('line',line=>{try{assert(line.length<=8192);resolve(JSON.parse(line));}catch{reject(new Error('private_input_invalid'));}finally{input.close();}});input.once('close',()=>reject(new Error('private_input_missing')));});assert(credentials?.username&&credentials?.password);
 }
 before=await native();
 if(current&&mode==='preflight'){
  await check('Sources scellées et original011 vérifiés en lecture seule sans fenêtre',async()=>{
   const verified=await verifySource('verify-current');source=verified.source;assert.equal(source.capture_id,capture);assert.equal(source.kind,kind);assert(verified.completed&&verified.master_key_witness_equal&&verified.no_window_created&&verified.no_service_or_configuration_change);assert.equal(verified.current.services[0].image,before.services[0].image);assert.equal(verified.current.schema_migrations.length,11);assert.equal(verified.current.schema_migrations.at(-1),'011_execution_logs.sql');
   const after=await native();assert.deepEqual(after.services,before.services);assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.campaign_directories,[]);observations.push({scenario:'current-read-only-preflight',verified,after});cleanup=true;
  });completed=true;
 }else if(mode==='invalid'){
  if(current)source=await verifySource();
  await check(current?'Treize refus réels dont cinq propres au replay011 avant mutation':'Huit refus réels des options de rétention avant mutation',async()=>{
   await refusal('source_without_mode','instance-limit',[`--retention-history=${capture}`],'retention_replay_option_pair_required');
   await refusal('mode_without_source','instance-limit',['--retention-observation=preflight'],'retention_replay_option_pair_required');
   await refusal('noncanonical_source','instance-limit',flags('../source','preflight'),'canonical_retention_capture_required');
   await refusal('unknown_mode','instance-limit',flags(capture,'unknown'),'unknown_retention_observation');
   await refusal('wrong_environment','function-version-purge',flags(capture,'preflight').slice(0,2),'retention_replay_requires_instance_limit');
   await refusal('mixed_histories','instance-limit',[...flags(capture,'preflight'),'--firing-history=schedule-firing-volume-5d3595f228964f4e848a8974004e8c0f','--firing-observation=count'],'history_replays_are_exclusive');
   await refusal('two_sources','instance-limit',[...flags(capture,'preflight'),'--retention-history=other'],'one_retention_replay_source_required');
   await refusal('omitted_short_guard','instance-limit',flags(capture,'preflight').slice(0,2),'retention_replay_guard_duration');
   if(current){
    await refusal('current_target_without_pair','instance-limit',['--retention-target-schema011'],'retention_target_requires_replay_pair');
    await refusal('current_target_with_firing_only','instance-limit',['--firing-history=schedule-firing-volume-a5a8fc06179d4a31bd5620f0d9c87c97','--firing-observation=count','--guard-seconds=120','--retention-target-schema011'],'retention_target_requires_replay_pair');
    await refusal('current_target_wrong_real_image','instance-limit',flags(capture,'age'),'current_retention_image_required',source.images.runtime.image);
    await refusal('current_image_without_explicit_target','instance-limit',flags(capture,'age').filter(v=>v!=='--retention-target-schema011'),'captured_control_image_required');
    await refusal('historical_young_preflight_after_real_age','instance-limit',flags(capture,'preflight'),'young_preflight_no_longer_eligible');
   }cleanup=true;
  });completed=true;
 }else if(mode==='not-eligible'){
  source=await verifySource();assert(before.sampled_at<source.eligible_after,'refusal_requires_real_early_date');
  await check('Refus réel avant sept jours sans fenêtre créée',async()=>{await refusal('age_before_real_eligibility','instance-limit',flags(capture,'age'),'age_replay_not_yet_eligible');cleanup=true;});completed=true;
 }else{
  source=await verifySource();assert.equal(source.capture_id,capture);assert.equal(source.kind,kind);
  child=spawn('ssh',[...ssh,'python3','-B',helper,'instance-limit',campaign,current?before.services[0].image:source.images.control.image,...flags(capture,observationMode)],{stdio:['pipe','pipe','pipe']});createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});child.stderr.on('data',data=>{if(errors.length<1048576)errors+=data.toString().slice(0,1048576-errors.length);});child.stdin.on('error',()=>{});child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
  if(['seed-loss','observer-loss'].includes(mode)){
   await check('Perte réelle du pilote et du mutateur au point durable demandé',async()=>{const armed=await event('guard-armed');assert.equal(armed.guard_seconds,120);await until(()=>ended,'lost_driver_not_joined',65);assert.notEqual(exitCode,0);const state=await remote('status'),point=mode==='seed-loss'?state.retention_replay.seed:state.retention_replay.observation;assert(point.driver_killed&&point.inherited_guard_lock);assert.equal(point.fault_signal,'SIGKILL');if(mode==='seed-loss')assert(point.registry_published&&point.artifacts_verified&&!point.control_published);else{assert(point.observer_attached&&point.native_stop&&state.retention_replay.seed.control_published);if(current){const versions=point.before_observer_loss.schema_migrations;assert([9,10].includes(versions.length)&&['009_schedules.sql','010_code_drafts.sql'].includes(versions.at(-1)));assert(!versions.includes('011_execution_logs.sql'));assert.deepEqual(point.before_observer_loss.invocations,point.before_start.invocations);assert(point.control_paused_for_incomplete_loss&&point.paused_container_id===point.container_id)}}observations.push({scenario:'real-loss-point',point});});
   await check('Garde indépendante120, mêmes originaux et source scellée conservée',async()=>{const state=await until(async()=>{const value=await remote('status');return value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state)?value:false;},'independent_restore_missing',200);joined(state);if(current&&mode==='observer-loss')assert.equal(state.observation_error?.type,'retention_copy_migration_incomplete');restoration=state.restoration;restored(restoration,true);const boundary=state.retention_replay.armed_boundary;assert(restoration.temporary_control_absent_at<boundary+240&&restoration.restored_at<boundary+270);assert.deepEqual(await verifySource(),source);const after=await native();assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.services[1],before.services[1]);for(const key of ['id','image','running','health'])assert.equal(after.services[0][key],before.services[0][key]);observations.push({scenario:'independent-restore-joined',terminal_status:{restored:state.restored,driver_alive:state.driver_alive,timer_state:state.timer_state,service_state:state.service_state},restoration,after});cleanup=true;});completed=true;
  }else{
   await check('Chargement exact de la capture et observation native du contrôle réel',async()=>{const armed=await event('guard-armed');assert.equal(armed.guard_seconds,120);ready=await event('retention-replay-ready');assert.equal(ready.container.image,current?before.services[0].image:source.images.control.image);assert.equal(ready.installation_id,source.installation_id);const replay=ready.retention_replay;assert.deepEqual(replay.source,source);assert(replay.seed.completed&&replay.seed.control_published&&replay.seed.inherited_guard_lock);const measured=replay.observation;assert(measured.completed&&measured.observer_attached&&measured.inherited_guard_lock);assert.equal(measured.age_retention_qualified,observationMode==='age');if(current){assert.equal(measured.current_schema_migrations.length,11);assert.equal(measured.current_schema_migrations.at(-1),'011_execution_logs.sql');assert.match(measured.current_collection_id,/^[a-f0-9-]{36}$/);if(kind==='source')assert(measured.protected_metadata_preserved&&measured.protected_logs_expired)};assert.equal(measured.mode,observationMode);assert.equal(measured.start_boundary,replay.armed_boundary);assert(replay.armed_at-replay.armed_boundary>=10&&replay.armed_at-replay.armed_boundary<=60);assert.equal(measured.final.new_invocations,0);assert.deepEqual(measured.final.instances,[]);assert.deepEqual(measured.before_start.invocations,source.target_calls);assert.deepEqual(measured.before_start.firings,source.witnesses.firings);
    if(observationMode==='preflight'){assert.deepEqual(measured.final.invocations,source.target_calls);if(kind==='terminal'){assert.deepEqual(measured.final.firings,source.witnesses.firings);assert.deepEqual(measured.final.generations,source.witnesses.generations);}else assert.equal(measured.final.firings[0].state,'succeeded');}
    else if(kind==='source'){assert.equal(measured.protected.invocations.length,1);assert.equal(measured.protected.firings[0].completed_at,null);assert.deepEqual(measured.final.invocations,[]);assert.equal(measured.final.firings.length,1);assert.equal(measured.final.firings[0].state,'succeeded');}
    else for(const key of ['invocations','firings','generations'])assert.deepEqual(measured.final[key],[]);
   });
   await check('Nouveau SSO depuis accueil et lectures publiques recoupées sans handler nouveau',async()=>{browser=await chromium.launch({headless:true});const context=await browser.newContext({locale:'fr-FR'}),page=await context.newPage();await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);credentials=null;await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:60000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();admin=context.request;session=await api('/api/session');assert(session.authenticated);const measured=await operation('retention-replay-state');assert.equal(measured.new_invocations,0);assert.deepEqual(measured.instances,[]);
    if(kind==='source'){const id=source.live_functions[0].id,row=await api(`/api/functions/${id}`);assert.equal(row.name,source.live_functions[0].name);const calls=await api(`/api/functions/${id}/invocations?limit=100`);assert.deepEqual(calls.items.map(v=>v.id).sort(),measured.invocations.map(v=>v.id).sort());const identifier=source.witnesses.firings[0].id;let found;await until(async()=>{const head=await api(`/api/functions/${id}/schedule-firings?limit=1`);const tail=await api(`/api/functions/${id}/schedule-firings?limit=100&offset=${Math.max(0,head.total-1)}`);found=tail.items.find(v=>v.id===identifier);return Boolean(found);},'source_firing_api_not_found',15);assert.deepEqual(found,measured.firings[0]);observations.push({scenario:'source-public-reads',invocation_ids:calls.items.map(v=>v.id),firing:found});}
    else{for(const fn of source.witnesses.functions){const row=await api(`/api/archives/${fn.id}`);assert.equal(row.name,fn.name);assert.equal(row.purged_at,fn.purged_at);await api(`/api/functions/${fn.id}`,404);}observations.push({scenario:'terminal-public-archives',function_ids:source.witnesses.functions.map(v=>v.id)});}
   });
   if(mode==='foreign-namespace')await check('Namespace hors périmètre préservé au refus puis seule fixture retirée par API',async()=>{
    const name='outside-retention-scope-'+campaign,initialNamespaces=await api('/api/namespaces?limit=100');
    assert.deepEqual(initialNamespaces.items.map(v=>v.id).sort(),source.namespaces.map(v=>v.id).sort());assert(!initialNamespaces.items.some(v=>v.name===name));namespaceCreation={name,before_ids:initialNamespaces.items.map(v=>v.id)};await save();
    const posted=await api('/api/namespaces',201,{method:'POST',body:{name}});foreignNamespace=await findOwnedNamespace();assert(foreignNamespace);assert.equal(foreignNamespace.id,posted.id);assert.equal(foreignNamespace.name,name);await save();
    let refused;try{await remote('restore');}catch(error){assert.equal(error.code,1);assert(String(error.stderr).includes('foreign_namespace'),'expected_scope_refusal_missing');refused={code:1,reason:'foreign_namespace',stderr_sha256:createHash('sha256').update(String(error.stderr)).digest('hex')};}
    assert(refused,'foreign_namespace_was_not_refused');await until(()=>ended,'refused_driver_not_joined',30);assert.notEqual(exitCode,0);
    const status=await remote('status');assert(!status.restored&&!status.driver_alive);const kept=await api(`/api/namespaces/${foreignNamespace.id}`);assert.equal(kept.name,name);assert.equal(kept.id,foreignNamespace.id);
    const identities=await refusedNative();observations.push({scenario:'foreign-namespace-refused',namespace:foreignNamespace,refusal:refused,identities,terminal_status:{restored:status.restored,driver_alive:status.driver_alive,timer_state:status.timer_state,service_state:status.service_state}});await save();
    await removeForeignNamespace();observations.push({scenario:'foreign-namespace-fixture-removed',namespace_id:kept.id});
   });
   await check(mode==='foreign-namespace'?'Restitution explicite après refus, mêmes originaux et source inchangée':'Restitution nominale jointe, mêmes originaux et source inchangée',async()=>{assert(Date.now()/1000<ready.retention_replay.armed_boundary+110,'nominal_restore_request_deadline');if(mode==='foreign-namespace'){restoration=await remote('restore');restored(restoration,true);}else{child.stdin.end(JSON.stringify({op:'restore'})+'\n');restoration=await event('restored',100);restored(restoration,false);}assert(restoration.temporary_control_absent_at<ready.retention_replay.armed_boundary+240&&restoration.restored_at<ready.retention_replay.armed_boundary+270);await until(()=>ended,'driver_not_joined',30);if(mode==='foreign-namespace')assert.notEqual(exitCode,0);else assert.equal(exitCode,0);const state=await remote('status');joined(state);assert.deepEqual(await verifySource(),source);const after=await native();assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.services[1],before.services[1]);for(const key of ['id','image','running','health'])assert.equal(after.services[0][key],before.services[0][key]);observations.push({scenario:mode==='foreign-namespace'?'explicit-scope-restore-joined':'nominal-restore-joined',restoration,terminal_status:{restored:state.restored,driver_alive:state.driver_alive,timer_state:state.timer_state,service_state:state.service_state},after});cleanup=true;});completed=true;
  }
 }
}catch(error){failure={type:error.name,code:error.code,signal:error.signal,source_line:String(error.stack??'').match(/retention-history-replay\.mjs:(\d+)/)?.[1],message_sha256:createHash('sha256').update(String(error.message)).digest('hex')};}
finally{credentials=null;if(namespaceCreation){try{await removeForeignNamespace(true);}catch(error){failure={...failure,namespace_cleanup_error:error.name};}}if(child&&!cleanup){child.stdin.end();try{restoration=await remote('restore');cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}catch(error){failure={...failure,restoration_error:error.name};}await until(()=>ended,'failed_driver_not_joined',60).catch(()=>{cleanup=false;});}await browser?.close();if(errors)await writeFile(new URL(`retention-replay-${kind}-${mode}-${campaign}.stderr`,out),errors,{mode:0o600});await save();}
assert(completed&&cleanup&&!failure,`retention_history_replay_failed:${report.pathname}`);console.log(JSON.stringify({completed:true,kind,mode,groups:checks.length,report:report.pathname}));
