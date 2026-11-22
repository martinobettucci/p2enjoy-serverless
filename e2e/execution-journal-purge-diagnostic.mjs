// @spec docs/BACKLOG.md#sls-128 | docs/CONSOLE_STORAGE.md
// @verifies docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#conservation-par-service-et-budget
// One owned real purge intention; preserve failure and never blindly retry.
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash,randomUUID} from 'node:crypto';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {chromium} from 'playwright';
import {privateInput,adminConnection,base,until,diagnosis} from './execution-journal-harness.mjs';
const prior=JSON.parse(await readFile(process.argv[2]));assert.equal(prior.cleanup,false);assert.equal(prior.kind,'api');
const fixture=prior.observations.find(row=>row.scenario==='actual-byte-boundary-exact');assert(fixture && prior.function_ids.includes(fixture.function_id));
const id=randomUUID(),report=new URL('../.local/e2e/execution-journal-purge-diagnostic-'+id+'.json',import.meta.url);
const record={campaign:id,kind:'api',completed:false,cleanup:false,checks:[],cleanup_errors:[],observations:[],captures:{},skipped:0,prior_campaign:prior.campaign,namespace_id:prior.namespace_id,function_ids:prior.function_ids,source_sha256:createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex')};
const save=()=>writeFile(report,JSON.stringify(record,null,2)+'\n',{mode:0o600});
let browser,connection,observer,joined;
try {
 const credentials=await privateInput();browser=await chromium.launch({headless:true});connection=await adminConnection(browser,credentials);
 const {admin,session}=connection,archive='/api/archives/'+fixture.function_id;
 const current=await admin.get(archive);assert.equal(current.status(),200);const row=await current.json();assert.equal(row.namespace_id,prior.namespace_id);assert.equal(row.name,'journal-byte-volume-corpus-handler');assert(!row.purged_at && !row.storage_operation);
 const events=[];observer=spawn('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24',
  ['python3','-B','/srv/p2enjoy-serverless/e2e/execution-journal-purge-space-observer.py',prior.namespace_id,fixture.function_id,prior.campaign].join(' ')],{stdio:['ignore','pipe','pipe']});
 let stderr=0;observer.stderr.on('data',data=>stderr+=data.length);const lines=createInterface({input:observer.stdout});lines.on('line',line=>events.push(JSON.parse(line)));
 joined=new Promise(resolve=>observer.once('close',(code,signal)=>{lines.close();resolve({code,signal,stderr_bytes:stderr});}));
 await until(()=>events.some(row=>row.event==='ready'),'temp_observer_not_ready',15);
 record.intention={path:archive+'/purge',operation_id:randomUUID(),expected_version:row.updated_at,confirm_name:row.name};await save();
 const started=performance.now(),response=await admin.post(record.intention.path,{headers:{Origin:base,'X-CSRF-Token':session.csrf_token,'If-Match':String(row.updated_at)},data:{operation_id:record.intention.operation_id,confirm_name:row.name}}),body=await response.json();
 record.http={status:response.status(),elapsed_ms:performance.now()-started,request_id:response.headers()['x-request-id']||null,public_error:typeof body.error==='string'?body.error:null,operation_id:body.id||null,state:body.state||null};await save();
 record.observer_exit=await joined;record.observations=events;assert.equal(record.observer_exit.code,0);assert(events.some(row=>row.event==='temp-space-observation' && row.completed));
 assert.equal(response.status(),503,'diagnostic_expected_original_refusal');record.completed=true;
} catch(error){record.failure=diagnosis(error);process.exitCode=1;}
finally {
 if(observer && observer.exitCode===null && observer.signalCode===null){observer.kill('SIGTERM');record.observer_exit=await joined;}
 if(connection){try{const response=await connection.admin.post('/auth/logout',{headers:{Origin:base,'X-CSRF-Token':connection.session.csrf_token}});record.logout_status=response.status();}finally{await connection.admin.dispose();await connection.context.close();}}
 await browser?.close();record.local_closed=true;await save();
}
console.log(JSON.stringify({completed:record.completed,groups:0,cleanup:false,report:report.pathname}));
