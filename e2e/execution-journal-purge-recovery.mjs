// @spec docs/BACKLOG.md#sls-128 | docs/CONSOLE_STORAGE.md | docs/EXECUTION_LOGS.md#effacement-massif-des-anciens-logs--sls-128
// @verifies docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#effacement-massif-des-anciens-logs--sls-128
// Recover only a recorded owned archive; one durable intention and joined cleanup.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {chromium,request} from 'playwright';
import {JournalCampaign,privateInput,adminConnection,base,until,diagnosis} from './execution-journal-harness.mjs';
import {inspectJournal} from './execution-journal-native.mjs';
const prior=JSON.parse(await readFile(process.argv[2]));assert.equal(prior.cleanup,false);assert.equal(prior.kind,'api');
const fixture=prior.observations.find(row=>row.scenario==='actual-byte-boundary-exact');assert(fixture && prior.function_ids.includes(fixture.function_id));
const c=new JournalCampaign('api');c.namespace={id:prior.namespace_id};c.creations=structuredClone(prior.creations);
c.functions=prior.function_ids.map(id=>({id}));c.services=prior.service_ids.map(id=>({id}));c.tokens=prior.creations.filter(row=>row.kind==='token').map(row=>({id:row.id}));
c.observations.push({scenario:'owned-prior-campaign-recovery',prior_campaign:prior.campaign,namespace_id:prior.namespace_id});
let observer,joined;
try {
 const credentials=await privateInput();c.browser=await chromium.launch({headless:true});Object.assign(c,await adminConnection(c.browser,credentials));
 c.caller=await request.newContext({baseURL:base,timeout:120000});
 const namespace=await c.value('/api/namespaces/'+prior.namespace_id);assert.equal(namespace.description,prior.campaign);
 for(const service of c.services){const response=await c.call('/api/services/'+service.id,{status:[200,404]});service.retired=response.status===404;if(!service.retired){assert.equal(response.data.namespace_id,prior.namespace_id);assert.equal(response.data.description,prior.campaign);}}
 const archive='/api/archives/'+fixture.function_id,row=await c.value(archive);assert.equal(row.namespace_id,prior.namespace_id);assert.equal(row.name,'journal-byte-volume-corpus-handler');assert(!row.purged_at);
 const events=[],failures=[];observer=spawn('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24',
  ['python3','-B','/srv/p2enjoy-serverless/e2e/execution-journal-purge-space-observer.py',prior.namespace_id,fixture.function_id,prior.campaign].join(' ')],{stdio:['ignore','pipe','pipe']});
 let stderr=0;observer.stderr.on('data',data=>stderr+=data.length);observer.on('error',error=>failures.push(diagnosis(error)));
 const lines=createInterface({input:observer.stdout});lines.on('line',line=>{try{events.push(JSON.parse(line));}catch(error){failures.push(diagnosis(error));}});
 joined=new Promise(resolve=>observer.once('close',(code,signal)=>{lines.close();resolve({code,signal,stderr_bytes:stderr});}));
 await until(()=>{assert.deepEqual(failures,[]);return events.some(row=>row.event==='ready');},'temp_observer_not_ready',15);
 let identifier;
 if(row.storage_operation){identifier=row.storage_operation.id;assert.equal(row.command?.id,identifier);c.observations.push({scenario:'join-existing-purge-intention',operation_id:identifier});await c.save();}
 else {
  identifier=randomUUID();c.observations.push({scenario:'purge-intention',path:archive+'/purge',operation_id:identifier,expected_version:row.updated_at,confirm_name:row.name});await c.save();
  const started=performance.now(),response=await c.admin.post(archive+'/purge',{headers:{Origin:base,'X-CSRF-Token':c.session.csrf_token,'If-Match':String(row.updated_at)},data:{operation_id:identifier,confirm_name:row.name}}),body=await response.json();
  c.observations.push({scenario:'purge-recovery-http-result',http_status:response.status(),elapsed_ms:performance.now()-started,request_id:response.headers()['x-request-id']||null,public_error:typeof body.error==='string'?body.error:null,operation_id:body.id||null,state:body.state||null});await c.save();
  assert([200,202].includes(response.status()));assert.equal(body.id,identifier);
 }
 await until(async()=>{const operation=await c.value('/api/storage-operations/'+identifier);assert.notEqual(operation.state,'aborted');return operation.state==='completed';},'owned_purge_not_completed',60);
 const final=await c.value(archive);assert(final.purged_at && final.artifact_bytes===0 && !final.storage_operation);
 const exit=await joined;c.observations.push({scenario:'purge-native-temp-observation',exit,events,failures});await c.save();assert.equal(exit.code,0);assert.deepEqual(failures,[]);
 const measured=events.find(row=>row.event==='temp-space-observation');assert(measured?.completed && measured.minimum_available_bytes>0);assert.equal(measured.initial.total_bytes,16777216);assert.equal(measured.final.available_bytes,measured.initial.available_bytes);
 c.scenariosPassed=true;
 await c.close({nativeCleanup:async()=>{const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});}});
} catch(error){c.failure=diagnosis(error);process.exitCode=1;}
finally {
 if(observer && observer.exitCode===null && observer.signalCode===null){observer.kill('SIGTERM');const exit=await joined;c.observations.push({scenario:'observer-joined-after-failure',exit});}
 if(!c.cleanup){try{if(c.admin && c.session)await c.value('/auth/logout',{method:'POST'});}catch(error){c.cleanupErrors.push({phase:'logout',...diagnosis(error)});}finally{await c.closeLocal();}}
 c.completed=Boolean(c.scenariosPassed && c.cleanup && !c.failure && !c.cleanupErrors.length);await c.save();if(!c.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:c.completed,groups:0,cleanup:c.cleanup,report:c.report.pathname}));
