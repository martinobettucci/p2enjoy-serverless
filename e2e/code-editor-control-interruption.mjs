// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_CONTROL_INTERRUPTION.md
// @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_CONTROL_INTERRUPTION.md#quatre-groupes-ciblés-puis-25-communs-frais
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium,request} from 'playwright';
import {enterNamespaces} from './console-navigation.mjs';

const exec=promisify(execFile),base='https://serverless.lelabs.tech',id=randomUUID();
const out=new URL('../.local/e2e/',import.meta.url),prefix='code-editor-control-interruption-'+id;
const report=new URL(prefix+'.json',out),helper='/srv/p2enjoy-serverless/e2e/code-editor-control-interruption-operator.py';
const SSH=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const checks=[],observations=[],intents=[],publications=[],gates=[],invocations=[],http=[],captures={},faults=[],cleanupErrors=[],pending=[];
const applicationSecret='editor-control-interruption-'+randomUUID(),markerPath='publication-marker.json';
const sha=v=>createHash('sha256').update(v).digest('hex'),match=v=>({'If-Match':String(v)}),ep=()=>'/api/functions/'+fn.id;
let credentials,browser,context,page,admin,caller,session,namespace,service,fn,token,work,pkg,stable,latest;
let completed=false,scenariosPassed=false,failure=null,writes=Promise.resolve();
function diagnosis(error){return {type:error.name,code:error.code??null,message_sha256:sha(String(error.message)),source_line:String(error.stack??'').match(/code-editor-control-interruption\.mjs:(\d+)/)?.[1]};}
async function save(){const raw=JSON.stringify({campaign:id,target:base,completed,skipped:0,checks,observations,intents,publication_intents:publications,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],token_ids:token?[token.id]:[],invocations,http,captures,faults,cleanup_errors:cleanupErrors,failure,gates:gates.map(({phase,events,restored,terminal,independentWait,recoveryReceipts})=>({phase,events,restored,terminal,independent_wait:independentWait,recovery_receipts:recoveryReceipts}))},null,2)+'\n';const next=writes.then(async()=>{const temporary=new URL(report.href+'.pending');await writeFile(temporary,raw,{mode:0o600});await rename(temporary,report);});writes=next.catch(()=>{});await next;}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',...diagnosis(error)});throw error;}finally{await save();}}
async function privateInput(){const input=createInterface({input:process.stdin});try{return JSON.parse(await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));}));}finally{input.close();}}
async function until(action,label,seconds=90){const end=performance.now()+seconds*1000;while(performance.now()<end){const value=await action();if(value)return value;await new Promise(resolve=>setTimeout(resolve,50));}throw new Error(label);}
async function api(path,{method='GET',body,bytes,status=200,headers={},technical=false}={}){
 const response=await(technical?caller:admin).fetch(base+path,{method,data:bytes??body,headers:{...(technical?{'X-Serverless-Token':token.token}:{Origin:base,'X-CSRF-Token':session.csrf_token}),...(bytes?{'Content-Type':'application/zip'}:{}),...headers},timeout:180000});
 const raw=await response.text();http.push({method,path,status:response.status(),body_bytes:Buffer.byteLength(raw),body_sha256:sha(raw)});await save();assert(!raw.includes(applicationSecret));assert([status].flat().includes(response.status()),'unexpected_http_status');return JSON.parse(raw);
}
async function create(kind,path,body){for(let offset=0;;offset+=100){const rows=(await api(path+'?limit=100&offset='+offset)).items;assert(!rows.some(v=>v.name===body.name));if(rows.length<100)break;}const intent={kind,path,name:body.name,absent_before_post:true};intents.push(intent);await save();const response=await admin.post(base+path,{data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token}});intent.response_status=response.status();await save();assert.equal(response.status(),201);const row=await response.json();intent.id=row.id;await save();return row;}
async function reconcile(){for(const intent of intents){if(!intent.id&&!(intent.response_status>=400&&intent.response_status<500)){for(let offset=0;;offset+=100){const rows=(await api(intent.path+'?limit=100&offset='+offset)).items,found=rows.filter(v=>v.name===intent.name);assert(found.length<=1);if(found.length){intent.id=found[0].id;break;}if(rows.length<100)break;}}if(intent.id){if(intent.kind==='namespace'&&!namespace)namespace={id:intent.id};if(intent.kind==='service'&&!service)service={id:intent.id};if(intent.kind==='function'&&!fn)fn={id:intent.id};if(intent.kind==='token'&&!token)token={id:intent.id};}}await save();}
async function remote(mode,extra=[],timeout=210000){const result=await exec('ssh',[...SSH,'python3','-B',helper,mode,namespace.id,fn.id,...extra],{timeout,maxBuffer:4*1024**2});return JSON.parse(result.stdout.trim().split('\n').at(-1));}
async function idle(){await until(async()=>{const rows=(await api(ep()+'/instances')).items;return rows.length===0;},'instances_not_released');}
async function draft(){return(await api(ep()+'/code-draft')).draft;}
async function marker(value){const before=await draft(),text=JSON.stringify({value,validation_delay_ms:8000});observations.push({draft_save_intent:{id:before.id,version:before.version,path:markerPath,text_sha256:sha(text)}});await save();const saved=(await api(ep()+'/code-draft',{method:'PUT',headers:match(before.version),body:{file:{action:'write',path:markerPath,text}}})).draft;assert.equal(saved.version,before.version+1);return {draft:saved,text};}
async function intent(draft,kind){const value={deployment_id:randomUUID(),draft_id:draft.id,draft_version:draft.version,kind};publications.push(value);await save();return value;}
async function publish(draft,kind){const next=await intent(draft,kind),value=await api(ep()+'/code-draft/publish',{method:'POST',headers:match(fn.updated_at),body:{deployment_id:next.deployment_id,draft_version:next.draft_version}});observations.push({published:{intent:next,result:value}});await save();assert.equal(value.state,'published');assert(value.validation.valid&&value.validation.container_removed);return value;}
async function invoke(row,marker,pinned=false){const response=await caller.get(base+'/invoke/'+fn.id+(pinned?'@'+row.code_hash:''),{headers:{'X-Serverless-Token':token.token},timeout:60000});const raw=await response.text(),record={id:response.headers()['x-serverless-request-id'],code_hash:response.headers()['x-serverless-code-hash'],requested_code_hash:pinned?row.code_hash:null,status:response.status(),body_sha256:sha(raw),expected_marker:marker};observations.push({invocation_attempt:record});await save();assert.equal(response.status(),200);assert(!raw.includes(applicationSecret));const data=JSON.parse(raw);assert.equal(data.marker,marker);assert.equal(data.label,'stable');assert.equal(data.secret_sha256,sha(applicationSecret));assert.equal(data.request_id,record.id);assert.equal(record.code_hash,row.code_hash);invocations.push({...record,function_id:fn.id});await idle();}
function preservedDraft(row){const {last_deployment_id,last_publication_version,...preserved}=row;return preserved;}

async function gate(phase,publication){
 const g={phase,events:[],restored:false,terminal:null,independentWait:null,recoveryReceipts:[]};gates.push(g);await save();
 const child=spawn('ssh',[...SSH,'python3','-B',helper,phase,namespace.id,fn.id,publication.deployment_id,publication.draft_id,String(publication.draft_version)],{stdio:['pipe','pipe','pipe']});
 let ended=false,protocolError=null,stdoutBytes=0,stderrBytes=0;const stderrHash=createHash('sha256');
 let resolveDone;const done=new Promise(resolve=>{resolveDone=resolve;});
 const fail=error=>{protocolError??=error;child.stdin.end();};
 const lines=createInterface({input:child.stdout});lines.on('line',line=>{if(protocolError)return;try{assert(g.events.length<2048);g.events.push(JSON.parse(line));}catch(error){fail(error);}});
 child.stdout.on('data',chunk=>{stdoutBytes+=chunk.length;if(stdoutBytes>4*1024**2){fail(new Error('native_stdout_limit'));child.stdout.pause();lines.close();}});
 child.stderr.on('data',chunk=>{stderrBytes+=chunk.length;stderrHash.update(chunk);if(stderrBytes>262144){fail(new Error('native_stderr_limit'));child.stderr.pause();}});
 for(const stream of [child.stdout,child.stderr,child.stdin])stream.on('error',fail);child.once('error',fail);
 child.once('close',(exit_code,signal)=>{ended=true;lines.close();g.terminal={exit_code,signal,stdout_bytes:stdoutBytes,stderr_bytes:stderrBytes,stderr_sha256:stderrHash.digest('hex')};resolveDone();});
 g.send=value=>{assert(!ended&&!protocolError);child.stdin.write(value+'\n');};
 g.wait=(name,seconds=70)=>until(()=>{if(protocolError)throw protocolError;const value=g.events.find(v=>v.event===name);assert(value||!ended,'native_ended_before_'+name);return value;},'native_event_missing_'+name,seconds);
 g.join=async(seconds=70)=>{await until(()=>ended,'native_SSH_not_joined',seconds);await done;assert(!protocolError);await save();return g.terminal;};
 g.finish=async()=>{const terminal=await g.join();assert.equal(terminal.exit_code,0);const receipt=g.events.find(v=>v.event==='restored'),finished=g.events.find(v=>v.event==='guard-finished');assert(receipt?.healthy&&receipt.reference_unchanged&&receipt.stop_mutator_joined);assert(finished&&Object.values(finished.states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));g.restored=true;await save();return receipt;};
 g.recover=async()=>{
  child.stdin.end();const armed=g.events.find(v=>v.event==='guard-armed');assert(armed,'guard_identity_unknown');const recoveryMode=ended?'restore':'rescue';
  const receipt=await remote(recoveryMode,[armed.unit]);g.recoveryReceipts.push({mode:recoveryMode,receipt});await save();assert(receipt.healthy&&receipt.reference_unchanged&&receipt.stop_mutator_joined);assert(Object.values(receipt.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));
  try{await g.join(20);}catch(error){child.kill('SIGKILL');await until(()=>ended,'local_SSH_not_joined_after_kill',10);await done;throw error;}
  g.restored=true;await save();return receipt;
 };
 g.independent=async()=>{
  const terminal=await g.join(30);assert([137,255].includes(terminal.exit_code));assert(g.events.some(v=>v.event==='observer-loss'&&v.signal==='SIGKILL'));
  const armed=g.events.find(v=>v.event==='armed'),protocol=armed.restore_protocol;assert.deepEqual(protocol,{version:1,guard_delay_seconds:45,restore_alarm_seconds:180,evidence_probe_timeout_seconds:10});
  const started=performance.now(),budget=protocol.guard_delay_seconds+protocol.restore_alarm_seconds+protocol.evidence_probe_timeout_seconds,deadline=started+budget*1000;
  g.independentWait={protocol,budget_seconds:budget,probes:[],completed:false};await save();let receipt;
  while(performance.now()<deadline){const timeout=Math.min(10000,Math.max(1,Math.floor(deadline-performance.now())));let value;try{value=await remote('evidence',[armed.unit],timeout);}catch(error){g.independentWait.probes.push({elapsed_ms:performance.now()-started,timeout_ms:timeout,error:diagnosis(error)});await save();throw error;}g.independentWait.probes.push({elapsed_ms:performance.now()-started,timeout_ms:timeout,receipt:value});await save();if(performance.now()<=deadline&&value.event==='restored'){receipt=value;break;}const remaining=deadline-performance.now();if(remaining>0)await new Promise(resolve=>setTimeout(resolve,Math.min(100,remaining)));}
  g.independentWait.elapsed_ms=performance.now()-started;await save();assert(receipt,'independent_receipt_missing');assert(receipt.independent&&receipt.observer_gone&&receipt.healthy&&receipt.reference_unchanged&&receipt.stop_mutator_joined&&receipt.stop_receipt_sha256);
  const joined=await remote('restore',[armed.unit]);g.independentWait.guard_finished=joined;await save();assert(Object.values(joined.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));g.independentWait.completed=true;g.restored=true;await save();return receipt;
 };
 await g.wait('armed',30);return g;
}

const ed=()=>page.locator('.editor-view'),tree=()=>page.locator('.editor-layout>.panel').first();
const tracking=()=>ed().locator('section.panel').filter({has:page.getByRole('heading',{name:'Tentative suivie',exact:true})});
async function keyboard(button){await button.focus();await button.press('Enter');}
async function snap(name,target){await target.scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));const path=new URL(prefix+'-'+name+'.jpg',out),raw=await page.screenshot({path:path.pathname,type:'jpeg',quality:85,fullPage:false});captures[path.pathname.split('/').at(-1)]={sha256:sha(raw),viewport:page.viewportSize(),full_page:false};await save();}
async function reopen(width,publication,text){
 await page.setViewportSize({width,height:width===390?844:1000});await enterNamespaces(page,base);await page.getByRole('link',{name:namespace.name,exact:true}).click();await page.getByRole('link',{name:service.name,exact:true}).click();await page.getByRole('link',{name:fn.name,exact:true}).click();await keyboard(page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Éditeur',exact:true}));
 await ed().getByRole('button',{name:'Actualiser le contexte',exact:true}).waitFor();await until(async()=>await ed().getByRole('button',{name:'Actualiser le contexte',exact:true}).isEnabled()&&!await tree().getByText('Lecture des fichiers…',{exact:true}).count(),'editor_not_ready');
 const open=ed().getByRole('button',{name:'Ouvrir mon brouillon',exact:true});if(await open.count())await keyboard(open);
 await tracking().getByText(publication.deployment_id,{exact:true}).waitFor();await tracking().getByText('control_interrupted',{exact:true}).waitFor();await snap('failed-candidate-'+width,tracking());
 await tree().getByRole('searchbox',{name:'Rechercher un chemin',exact:true}).fill(markerPath);await keyboard(tree().getByRole('button',{name:'Rechercher',exact:true}));await keyboard(tree().getByRole('button',{name:new RegExp('^publication-marker\\.json')}));
 const area=ed().getByRole('textbox',{name:'Code enregistré en lecture',exact:true});await area.waitFor();const actual=await area.inputValue();observations.push({browser_recovery:{width,deployment_id:publication.deployment_id,textarea_sha256:sha(actual),read_only:await area.getAttribute('readonly'),url:new URL(page.url()).pathname+new URL(page.url()).search}});await save();assert.equal(actual,text);await snap('persistent-file-'+width,area);
 await page.goto(base);await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
}

async function interrupt(phase,width){
 const changed=await marker(phase+'-pilot'),before=await remote('inspect'),publication=await intent(changed.draft,'cut-'+phase),record={scenario:'cut-'+phase,before,publication};observations.push(record);await save();let g,flight,primaryError;
 try{
  g=await gate(phase,publication);const armed=g.events.find(v=>v.event==='armed');assert.deepEqual(armed.before,before);
  flight=admin.post(base+ep()+'/code-draft/publish',{headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...match(fn.updated_at)},data:{deployment_id:publication.deployment_id,draft_version:publication.draft_version},timeout:180000}).then(async response=>{const raw=await response.text();return {status:response.status(),body_bytes:Buffer.byteLength(raw),body_sha256:sha(raw)};}).catch(error=>({error:diagnosis(error)}));pending.push(flight);g.send('observe');
  const held=await g.wait('gated',35);record.held=held;await save();assert.equal(held.phase,phase);assert.equal(held.durable.draft_link.last_deployment_id,publication.deployment_id);g.send('interrupt');record.cut=await g.wait('cut');await save();assert.equal(record.cut.native_signal,9);assert.equal(record.cut.exit_code,137);
  record.restored=phase==='validating'?await g.independent():await g.finish();record.guard_receipt=await remote('receipt',[armed.unit]);record.transport=await flight;await save();assert(record.transport.error||record.transport.status>=500);assert(record.guard_receipt.completed&&!record.guard_receipt.helper_same_process_alive);assert(Object.values(record.guard_receipt.guard_states).every(v=>v.ActiveState==='inactive'&&(v.MainPID??'0')==='0'));const nativeRestored=record.guard_receipt.files[phase==='validating'?'restored-independent.json':'restored.json'];assert(nativeRestored);for(const key of ['container_id','image','healthy','stop_mutator_joined','started_at','stop_receipt_sha256'])assert.equal(nativeRestored.value[key],record.restored[key]);assert.equal(record.guard_receipt.files['kill-result.json'].sha256,record.restored.stop_receipt_sha256);
  const candidate=await api('/api/deployments/'+publication.deployment_id),resumed=await draft(),file=await api(ep()+'/code-draft/file?path='+markerPath),after=await remote('inspect',[publication.deployment_id]);Object.assign(record,{candidate,resumed,file_sha256:sha(file.file.text),after});await save();
  assert.equal(candidate.state,'failed');assert.equal(candidate.error_code,'control_interrupted');assert.equal(candidate.revision_id,null);assert.deepEqual(after.function,before.function);for(const key of ['versions','revisions','archives'])assert.deepEqual(after[key],before[key]);
  assert.deepEqual(preservedDraft(after.draft),preservedDraft(before.draft));assert.equal(after.draft.last_deployment_id,publication.deployment_id);assert.equal(after.draft.last_publication_version,publication.draft_version);assert.deepEqual(resumed,{...changed.draft,last_deployment_id:publication.deployment_id,last_publication_version:publication.draft_version});assert.equal(file.file.text,changed.text);
  assert.equal(after.control.Id,before.control.Id);assert.equal(after.control.Image,before.control.Image);assert.notEqual(after.control.started_at,before.control.started_at);assert.notEqual(after.control.init_pid,before.control.init_pid);assert.deepEqual(after.counts,{active_candidates:0,reserved_bytes:0,instances:0,active_calls:0,operations:0});assert.equal(after.candidate.payload_erased,1);assert.equal(after.candidate.directory_exists,false);assert.deepEqual(after.validation_containers,[]);assert.deepEqual(after.validation_channels,[]);
  await reopen(width,publication,changed.text);await invoke(stable,'stable-A');latest=await publish(resumed,'explicit-recovery-'+phase);assert.equal(latest.code_changed,true);await invoke(latest,phase+'-pilot',true);assert.equal((await api(ep())).active_revision_id,stable.revision_id);
 }catch(error){primaryError=error;throw error;}
 finally{
  let cleanupError;
  try{if(g&&!g.restored)record.recovery=await g.recover();}catch(error){record.recovery_error=diagnosis(error);cleanupError=error;}
  try{if(flight)record.transport??=await flight;}catch(error){record.transport_join_error=diagnosis(error);cleanupError??=error;}
  await save();if(!primaryError&&cleanupError)throw cleanupError;
 }
}

async function purge(){const response=await admin.get(base+ep());if(response.status()===200)await api(ep(),{method:'DELETE'});else assert.equal(response.status(),404);await until(async()=>!(await api('/api/archives/'+fn.id)).storage_operation,'archive_pending');const archived=await api('/api/archives/'+fn.id);if(!archived.purged_at){const operation=await api('/api/archives/'+fn.id+'/purge',{method:'POST',status:[200,202],headers:match(archived.updated_at),body:{operation_id:randomUUID(),confirm_name:archived.name}});await until(async()=>{const value=await api('/api/storage-operations/'+operation.id);assert.notEqual(value.state,'aborted');return value.state==='completed';},'purge_pending');}assert((await api('/api/archives/'+fn.id)).purged_at);}

async function main(){
 await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1440,height:1000}});page=await context.newPage();page.on('pageerror',error=>faults.push(diagnosis(error)));admin=context.request;caller=await request.newContext({timeout:120000});
 try{
  await check('SSO réel, paquet original, cible A et brouillon personnel',async()=>{
   await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);await page.locator('input[type=submit],button[type=submit]').first().click();credentials=null;await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();session=await(await admin.get(base+'/api/session')).json();assert(session.authenticated);
   work=await mkdtemp(new URL(prefix+'-',out).pathname);pkg=JSON.parse((await exec('python3',['-B','e2e/code-editor-control-interruption-package.py',work+'/source.zip'],{timeout:30000,maxBuffer:1048576})).stdout);observations.push({package:pkg});await save();const archive=await readFile(work+'/source.zip');assert.equal(sha(archive),pkg.archive_sha256);
   namespace=await create('namespace','/api/namespaces',{name:'code-editor-control-interruption-'+id.slice(0,8),description:id});service=await create('service','/api/namespaces/'+namespace.id+'/services',{name:'editor-control-interruption',description:id});fn=await create('function','/api/services/'+service.id+'/functions',{name:'persistent-editor-publication-'+id.slice(0,8),config:{handler:'publication-recovery.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,max_instances:1},configuration:{environment:{REVISION_LABEL:'stable'},secrets:{PUBLICATION_RECOVERY_SECRET:applicationSecret}}});
   const first={deployment_id:randomUUID(),kind:'initial'};publications.push(first);await save();await api(ep()+'/code-deployments',{method:'POST',status:201,headers:match(fn.updated_at),body:{deployment_id:first.deployment_id,handler:'publication-recovery.cjs.handler'}});stable=await api('/api/deployments/'+first.deployment_id+'/artifact',{method:'PUT',bytes:archive});assert.equal(stable.state,'published');await api(ep()+'/versions/'+stable.code_hash+'/promote',{method:'POST',headers:match((await api(ep())).updated_at)});fn=await api(ep());
   token=await create('token','/api/services/'+service.id+'/tokens',{name:'invoke-persistent-editor-'+id.slice(0,8),rights:['read'],function_ids:[fn.id]});await api(ep()+'/code-draft',{method:'POST',status:201,headers:match(fn.updated_at),body:{base_code_hash:stable.code_hash}});await invoke(stable,'stable-A');
  });
  await check('Coupure receiving complète : brouillon persistant, UI ordinateur et pilote explicite',()=>interrupt('receiving',1440));
  await check('Coupure validating et perte du helper : garde indépendante, UI mobile et pilote explicite',()=>interrupt('validating',390));
  await check('Déduplication après reprise et consolidation native des deux coupures',async()=>{
   const duplicate=await publish(await draft(),'explicit-unchanged');assert.equal(duplicate.code_changed,false);assert.equal(duplicate.code_hash,latest.code_hash);assert.equal(duplicate.revision_id,latest.revision_id);await invoke(duplicate,'validating-pilot',true);
   const native=await remote('inspect');observations.push({scenario:'native-consolidation',native});await save();assert.equal(invocations.length,6);assert.equal(new Set(invocations.map(v=>v.id)).size,6);assert.equal(native.invocations.length,6);for(const item of invocations){const row=native.invocations.find(v=>v.id===item.id);assert(row?.state==='succeeded'&&row.handler_started===1&&row.http_status===200);assert.equal(native.revisions.find(v=>v.id===row.revision_id).code_hash,item.code_hash);}assert.equal(native.revisions.length,3);assert.equal(native.versions.length,3);assert.equal(native.candidates.length,6);assert(native.candidates.every(v=>publications.some(p=>p.deployment_id===v.id)));assert.equal(native.candidates.filter(v=>v.state==='published').length,4);assert.equal(native.candidates.filter(v=>v.state==='failed'&&v.error_code==='control_interrupted').length,2);assert.equal(native.audits.filter(v=>v.action==='deployment.prepare').length,6);assert.equal(native.audits.filter(v=>v.action==='function.deploy').length,4);assert.equal(native.audits.filter(v=>v.action==='deployment.abandon').length,0);assert.equal(native.function.active_revision_id,stable.revision_id);assert.equal(native.function.updated_at,fn.updated_at);assert.equal(native.integrity,'ok');assert.deepEqual(native.foreign_keys,[]);assert.equal(gates.length,2);assert(gates.every(v=>v.restored));assert.equal(Object.keys(captures).length,4);assert.equal(faults.length,0);
  });
  scenariosPassed=true;
 }finally{
  credentials=null;for(const g of [...gates].reverse())if(!g.restored)try{observations.push({guard_recovery:await g.recover()});}catch(error){cleanupErrors.push({phase:'guard-recovery',...diagnosis(error)});}await Promise.allSettled(pending);
  if(admin&&session&&gates.every(v=>v.restored)){
   try{await reconcile();}catch(error){cleanupErrors.push({phase:'reconcile',...diagnosis(error)});}
   if(fn&&namespace)try{const native=await remote('inspect');observations.push({cleanup_ownership:native});await save();assert(native.candidates.every(v=>publications.some(p=>p.deployment_id===v.id)),'foreign_candidate_prevents_cleanup');for(const row of native.candidates)if(row.state==='prepared')await api('/api/deployments/'+row.id,{method:'DELETE'});await until(async()=>{const n=await remote('inspect');assert(n.candidates.every(v=>publications.some(p=>p.deployment_id===v.id)));return n.counts.active_candidates===0&&n.counts.reserved_bytes===0;},'owned_candidates_not_settled');if(!cleanupErrors.length)await purge();}catch(error){cleanupErrors.push({phase:'function-purge',...diagnosis(error)});}
   if(token)try{assert((await api('/api/tokens/'+token.id+'/revoke',{method:'POST'})).revoked);}catch(error){cleanupErrors.push({phase:'token-revoke',...diagnosis(error)});}
   if(fn&&namespace)try{const native=await remote('inspect');observations.push({scenario:'native-cleanup',native});await save();assert(native.function.purged_at);assert.equal(native.draft,null);assert(native.revisions.every(v=>v.stored_bytes===0&&!native.archives[v.id].directory_exists));assert(native.candidates.every(v=>v.payload_erased===1&&v.reserved_bytes===0&&!v.directory_exists));assert(Object.values(native.counts).every(v=>v===0));assert.deepEqual(native.validation_containers,[]);assert.deepEqual(native.validation_channels,[]);}catch(error){cleanupErrors.push({phase:'native-cleanup',...diagnosis(error)});}
   if(!cleanupErrors.length){if(service)try{await api('/api/services/'+service.id,{method:'DELETE'});}catch(error){cleanupErrors.push({phase:'service-delete',...diagnosis(error)});}if(namespace)try{await api('/api/namespaces/'+namespace.id,{method:'DELETE'});}catch(error){cleanupErrors.push({phase:'namespace-delete',...diagnosis(error)});}}
   try{await api('/auth/logout',{method:'POST'});}catch(error){cleanupErrors.push({phase:'logout',...diagnosis(error)});}
  }
  for(const [phase,close] of [['caller',()=>caller?.dispose()],['context',()=>context?.close()],['browser',()=>browser?.close()],['work',()=>work?rm(work,{recursive:true,force:true}):null]])try{await close();}catch(error){cleanupErrors.push({phase,...diagnosis(error)});}
  completed=scenariosPassed&&!cleanupErrors.length;await save();
 }
 assert(completed);console.log(JSON.stringify({completed,groups:checks.length,report:report.pathname}));
}
main().catch(async error=>{credentials=null;completed=false;failure=diagnosis(error);await save().catch(()=>{});console.error('code_editor_control_interruption_e2e_failed');process.exitCode=1;});
