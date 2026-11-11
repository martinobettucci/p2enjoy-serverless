// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#chargement-gardé-de-la-copie
// @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#observation-du-replay-et-preuves-propres
// Real sealed backups, native syscall gates, SSO/API reads and independent DEV restoration.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,readFile,writeFile,rename} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {chromium} from 'playwright';

const mode=process.argv[2];assert(process.argv.length===3&&['invalid','not-eligible','preflight','count','seed-loss','observer-loss'].includes(mode),'explicit_replay_mode_required');
const run=promisify(execFile),campaign=randomUUID(),base='https://serverless.lelabs.tech';
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py',module='/srv/p2enjoy-serverless/e2e/schedule_firing_volume_replay.py';
const out=new URL('../.local/e2e/',import.meta.url),report=new URL(`schedule-firing-volume-replay-${mode}-${campaign}.json`,out);
const evidence=JSON.parse(await readFile(new URL('../docs/evidence/schedule-firing-volume-capture-dev-2026-11-11.json',import.meta.url),'utf8'));assert(evidence.completed&&evidence.capture_qualified);
const capture=evidence.receipt.capture_id,events=[],checks=[],observations=[],refusals=[];
let child,ended=false,exitCode=null,browser,admin,session,credentials,ready,restoration,before,source;
let completed=false,cleanup=false,failure=null,errors='',saveQueue=Promise.resolve();
function save(){saveQueue=saveQueue.then(async()=>{const pending=new URL(report.pathname+'.pending','file:');await writeFile(pending,JSON.stringify({campaign,mode,source_capture:capture,completed:completed&&cleanup&&!failure,cleanup,skipped:0,checks,events,observations,refusals,exit_code:exitCode,failure,restoration},null,2)+'\n',{mode:0o600});await rename(pending,report);});return saveQueue;}
async function until(action,message,seconds=90){const deadline=Date.now()+seconds*1000;while(Date.now()<deadline){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,250));}assert.fail(message);}
async function event(name,seconds=370){return until(()=>{const value=events.find(v=>v.event===name);assert(value||!ended,'deployment_driver_stopped');return value;},'deployment_event_missing',seconds);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',error:error.name});throw error;}finally{await save();}}
async function operation(op){const offset=events.length;assert(!ended);child.stdin.write(JSON.stringify({op})+'\n');return until(()=>{const value=events.slice(offset).find(v=>v.event==='result'&&v.op===op);assert(value||!ended,'deployment_driver_stopped');return value?.value;},'operator_result_missing');}
async function remote(op){const {stdout}=await run('ssh',[...ssh,'python3','-B',helper,op,campaign],{timeout:150000,maxBuffer:32*1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
async function verifySource(){const {stdout}=await run('ssh',[...ssh,'python3','-B',module,'verify',capture],{timeout:45000,maxBuffer:1024*1024});return JSON.parse(stdout.trim().split('\n').at(-1));}
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
const flags=(id,observation)=>[`--firing-history=${id}`,`--firing-observation=${observation}`,'--guard-seconds=120'];
async function refusal(name,helperMode,args,reason){const identifier=randomUUID();let rejected;try{await run('ssh',[...ssh,'python3','-B',helper,helperMode,identifier,before.services[0].image,...args],{timeout:45000,maxBuffer:1024*1024});}catch(error){assert.equal(error.code,1);assert(String(error.stderr).includes(reason),'expected_refusal_reason_missing');rejected={name,reason,campaign:identifier,exit_code:error.code,stderr_sha256:createHash('sha256').update(String(error.stderr)).digest('hex')};}assert(rejected,'refusal_missing');const after=await native(identifier);assert.deepEqual(after.services,before.services);assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.campaign_directories,[]);refusals.push(rejected);}
async function api(url){assert(Date.now()/1000<ready.firing_replay.observation.start_boundary+260,'api_replay_window_expired');const response=await admin.get(base+url,{headers:{Origin:base,'X-CSRF-Token':session?.csrf_token},timeout:10000});assert.equal(response.status(),200);return response.json();}
function restored(value,independent){assert(value.control_healthy&&value.agent_healthy&&value.directories_identical&&value.databases_identical&&value.artifacts_identical&&value.configuration_unchanged&&value.reference_unchanged&&value.temporary_directories_removed);assert.equal(value.independent,independent);assert.equal(value.original_id,before.services[0].id);assert.equal(value.image,before.services[0].image);}
function joined(value){assert(value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state));}

await mkdir(out,{recursive:true,mode:0o700});await save();
try{
 if(['preflight','count'].includes(mode)){
  assert(!process.stdin.isTTY,'private_pipe_required');const input=createInterface({input:process.stdin});credentials=await new Promise((resolve,reject)=>{input.once('line',line=>{try{assert(line.length<=8192);resolve(JSON.parse(line));}catch{reject(new Error('private_input_invalid'));}finally{input.close();}});input.once('close',()=>reject(new Error('private_input_missing')));});assert(credentials?.username&&credentials?.password);
 }
 before=await native();
 if(mode==='invalid'){
  await check('Huit refus réels de paramètres/source avant mutation',async()=>{
   await refusal('source_without_mode','instance-limit',[`--firing-history=${capture}`],'firing_replay_option_pair_required');
   await refusal('mode_without_source','instance-limit',['--firing-observation=preflight'],'firing_replay_option_pair_required');
   await refusal('noncanonical_source','instance-limit',flags('../source','preflight'),'canonical_capture_required');
   await refusal('unknown_mode','instance-limit',flags(capture,'unknown'),'unknown_firing_observation');
   await refusal('wrong_environment_mode','function-version-purge',flags(capture,'preflight').slice(0,2),'firing_replay_requires_instance_limit');
   await refusal('two_sources','instance-limit',[...flags(capture,'preflight'),`--firing-history=schedule-firing-volume-${randomUUID().replaceAll('-','')}`],'one_firing_replay_source_required');
   await refusal('unknown_source','instance-limit',flags('schedule-firing-volume-'+randomUUID().replaceAll('-',''),'preflight'),'firing_replay_error:FileNotFoundError');
   await refusal('missing_short_guard','instance-limit',flags(capture,'preflight').slice(0,2),'firing_replay_guard_duration');
   assert.equal(refusals.length,8);cleanup=true;
  });completed=true;
 }else if(mode==='not-eligible'){
  await check('Refus réel du replay numérique avant39 fenêtres sans création de fenêtre',async()=>{assert(before.sampled_at<evidence.receipt.eligible_after-60,'refusal_requires_real_early_date');await refusal('numeric_before_39_windows','instance-limit',flags(capture,'count'),'numeric_replay_not_yet_eligible');cleanup=true;});completed=true;
 }else{
  source=await verifySource();assert.equal(source.capture_id,capture);
  child=spawn('ssh',[...ssh,'python3','-B',helper,'instance-limit',campaign,before.services[0].image,...flags(capture,mode)],{stdio:['pipe','pipe','pipe']});createInterface({input:child.stdout}).on('line',line=>{try{events.push(JSON.parse(line));}catch{events.push({event:'invalid-driver-output'});}});child.stderr.on('data',data=>{if(errors.length<1048576)errors+=data.toString().slice(0,1048576-errors.length);});child.stdin.on('error',()=>{});child.on('close',code=>{ended=true;exitCode=code;});child.on('error',()=>{ended=true;exitCode=-1;});
  if(['seed-loss','observer-loss'].includes(mode)){
   await check('Perte réelle du pilote et du mutateur au point natif demandé',async()=>{const armed=await event('guard-armed');assert.equal(armed.guard_seconds,120);assert(armed.timer_schedule.includes('OnActiveUSec=2min'));await until(()=>ended,'lost_driver_not_joined',65);assert.notEqual(exitCode,0);const state=await remote('status'),point=mode==='seed-loss'?state.firing_replay.seed:state.firing_replay.observation;assert.equal(point.fault_signal,'SIGKILL');assert(point.driver_killed&&point.inherited_guard_lock);assert.equal(state.driver_alive,false);if(mode==='seed-loss')assert(point.registry_published&&point.artifacts_verified&&!point.control_published);else assert(point.observer_attached&&point.native_stop&&state.firing_replay.seed.control_published);observations.push({scenario:'real-loss-point',point});});
   await check('Restitution indépendante120s, source scellée inchangée et gardes jointes',async()=>{const state=await until(async()=>{const value=await remote('status');return value.restored&&!value.driver_alive&&['inactive','unknown'].includes(value.timer_state)&&['inactive','unknown'].includes(value.service_state)?value:false;},'independent_replay_restore_missing',170);joined(state);restoration=state.restoration;restored(restoration,true);assert.deepEqual(await verifySource(),source);const after=await native();assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.services[1],before.services[1]);for(const key of ['id','image','running','health'])assert.equal(after.services[0][key],before.services[0][key]);observations.push({scenario:'independent-restore-joined',status:state,after});cleanup=true;});completed=true;
  }else{
   await check(mode==='count'?'Chargement réel et deux frontières natives de la borne10000':'Chargement réel et observation native avant la borne10000',async()=>{
    const armed=await event('guard-armed');assert.equal(armed.guard_seconds,120);assert(armed.timer_schedule.includes('OnActiveUSec=2min'));ready=await event('instance-limit-ready');const replay=ready.firing_replay;assert.deepEqual(replay.source,source);assert.equal(ready.installation_id,source.installation_id);assert.equal(ready.container.image,before.services[0].image);assert(replay.seed.completed&&replay.seed.control_published&&replay.seed.inherited_guard_lock);const observation=replay.observation;assert(observation.completed&&observation.observer_attached&&observation.inherited_guard_lock);assert.equal(observation.start_boundary,replay.armed_boundary);assert(replay.armed_at-replay.armed_boundary>=10&&replay.armed_at-replay.armed_boundary<=120);assert(replay.timer_active_monotonic_us>0);assert.equal(observation.mode,mode);assert.deepEqual(observation.before.invocations,evidence.receipt.witnesses.invocations);assert.equal(observation.count_retention_qualified,mode==='count');
    if(mode==='count'){assert(observation.before.count>10000);assert.equal(observation.after.count,10000);assert.equal(observation.after.cursor,observation.before.cursor);const ordered=[...observation.before.firings].sort((a,b)=>b.completed_at-a.completed_at||(a.id<b.id?1:a.id>b.id?-1:0));assert.deepEqual([...observation.after.ids].sort(),ordered.slice(0,10000).map(v=>v.id).sort());assert.deepEqual([...observation.after.removed_ids].sort(),ordered.slice(10000).map(v=>v.id).sort());}else assert(observation.before.count<10000);
   });
   await check('Nouveau SSO depuis l’accueil et lectures API paginées recoupées sans handler nouveau',async()=>{
    browser=await chromium.launch({headless:true});const context=await browser.newContext({locale:'fr-FR'}),page=await context.newPage();await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);credentials=null;await page.locator('input[type=submit],button[type=submit]').first().click();await page.waitForURL(base+'/**',{timeout:60000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();admin=context.request;session=await api('/api/session');assert(session.authenticated);
    const state=await until(async()=>{const value=await operation('firing-replay-state');return value.cursor===ready.firing_replay.observation.start_boundary?value:false;},'recovery_cursor_not_finished',45);assert.equal(state.invocations.length,2);assert(state.invocations.every(v=>v.state==='succeeded'&&v.handler_started));assert.deepEqual(state.invocations.map(v=>v.id).sort(),evidence.receipt.witnesses.invocations.map(v=>v.id).sort());assert.equal(state.firings.length,mode==='count'?10000:256*(1+ready.firing_replay.observation.missed_windows));const pages=[];
    for(const identifier of source.function_ids){const expected=state.firings.filter(v=>v.function_id===identifier);assert(expected.length<10000);let rows=[],offset=0,total;do{const result=await api(`/api/functions/${identifier}/schedule-firings?limit=100&offset=${offset}`);total=result.total;assert.equal(total,expected.length);rows.push(...result.items);offset+=result.items.length;assert(result.items.length||offset===total,'empty_page_before_end');}while(offset<total);assert.deepEqual(rows.map(v=>v.id).sort(),expected.map(v=>v.id).sort());for(const row of rows)assert.deepEqual(row,expected.find(v=>v.id===row.id));pages.push({function_id:identifier,total,pages:Math.ceil(total/100)});}
    observations.push({scenario:'real-sso-api-pages',native:state,pages});
   });
   await check('Restitution nominale jointe et sauvegarde source identique',async()=>{child.stdin.end(JSON.stringify({op:'restore'})+'\n');restoration=await event('restored',100);restored(restoration,false);await until(()=>ended,'replay_driver_not_joined',30);assert.equal(exitCode,0);const state=await remote('status');joined(state);assert.deepEqual(await verifySource(),source);const after=await native();assert.deepEqual(after.official_sha256,before.official_sha256);assert.deepEqual(after.services[1],before.services[1]);for(const key of ['id','image','running','health'])assert.equal(after.services[0][key],before.services[0][key]);observations.push({scenario:'nominal-restore-joined',terminal_status:{restored:state.restored,driver_alive:state.driver_alive,timer_state:state.timer_state,service_state:state.service_state},after});cleanup=true;});completed=true;
  }
 }
}catch(error){failure={type:error.name,code:error.code,signal:error.signal,source_line:String(error.stack??'').match(/schedule-firing-volume-replay\.mjs:(\d+)/)?.[1],message_sha256:createHash('sha256').update(String(error.message)).digest('hex')};}
finally{
 credentials=null;if(child&&!cleanup){child.stdin.end();try{restoration=await remote('restore');cleanup=Boolean(restoration.control_healthy&&restoration.configuration_unchanged);}catch(error){failure={...failure,restoration_error:error.name};}await until(()=>ended,'failed_replay_driver_not_joined',60).catch(()=>{cleanup=false;});}
 await browser?.close();if(errors)await writeFile(new URL(`firing-replay-${mode}-${campaign}.stderr`,out),errors,{mode:0o600});await save();
}
assert(completed&&cleanup&&!failure,`schedule_firing_volume_replay_failed:${report.pathname}`);console.log(JSON.stringify({completed:true,mode,groups:checks.length,report:report.pathname}));
