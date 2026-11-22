// @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// Real helper SIGSTOP and independent timer restoration. The primary stays red; zero qualified groups.
import assert from 'node:assert/strict';
import {JournalCampaign,privateInput,diagnosis,base,endpoint,match} from './execution-journal-harness.mjs';
import {inspectJournal,JournalSqlBarrier,joinJournalSqlBarriers} from './execution-journal-native.mjs';

const c=new JournalCampaign('api');
async function observed(label,path,{method='GET',body,headers={}}={}) {
  const row={scenario:label+'-http-result',http_status:null},started=performance.now();
  c.observations.push(row);let response,data;
  try {
    response=await c.admin.fetch(path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':c.session.csrf_token,...headers}});
    row.http_status=response.status();data=await response.json();
    if(/^log_[a-z_]+$/.test(data?.error || ''))row.public_error=data.error;
    return {status:response.status(),data};
  } catch(error) {row.failure=diagnosis(error);throw error;}
  finally {row.elapsed_ms=performance.now()-started;await c.save();}
}

try {
  await c.open(await privateInput());
  const native=await inspectJournal(c,'baseline');assert.equal(native.migrations.length,11);
  assert(Object.values(native.counts).every(value=>value===0));
  const service=await c.service('journal-independent-guard-closure');
  const fn=await c.function(service,'journal-guard-closure-handler'),reader=await c.mint(service);
  const version=await c.publish(fn,'journal-guard-closure');await c.promote(fn,version.code_hash);
  const call=await c.invoke(fn,reader,{mode:'text'}),terminal=await c.terminal(fn,call.id);
  assert.equal(terminal.state,'succeeded');assert(terminal.handler_started);
  const policyPath='/api/services/'+service.id+'/log-policy',before=await c.value(policyPath);
  c.stage='122 : vraie réservation finale puis suspension du seul helper';await c.save();
  const gate=await new JournalSqlBarrier(c,native.containers['serverless-api'].image,1,'sqlite-reservation',
    {recovery:'independent_guard'}).start();
  const reading=c.track(observed('guard-held-read',endpoint(fn)+'/logs'));
  const held=await gate.held();assert.equal(held.readers.length,1);
  assert.equal(held.readers[0].comm,'journal-verify');assert.equal(held.readers[0].syscall_result,0);
  const stopped=await gate.action('suspend');assert.equal(stopped.signal,19);
  c.observations.push({scenario:'actual-helper-suspended',unit:gate.unit,held,stopped});await c.save();
  const writing=c.track(observed('guard-held-policy',policyPath,{method:'PUT',headers:match(before.version),
    body:{retention_minutes:before.retention_minutes-1}}));
  c.stage='122 : attendre exclusivement la garde systemd déjà armée';await c.save();
  await gate.recover();await c.joinPending();
  const restored=c.observations.find(row=>row.scenario==='native-independent-guard-confirmed' && row.unit===gate.unit);
  assert(restored);assert.equal(restored.receipt.restoration_origin,'systemd_guard');
  assert.equal(restored.receipt.restorer_systemd_unit,gate.unit+'.service');
  assert(restored.receipt.helper_killed_at_ns && restored.receipt.helper_joined_at_ns);
  const read=await reading,write=await writing;if(read.error)throw read.error;if(write.error)throw write.error;
  assert.equal(read.value.status,503);assert.equal(write.value.status,200);
  assert.equal((await c.value(policyPath)).version,before.version+1);
  c.observations.push({scenario:'real-guard-closure-outcome',unit:gate.unit,function_id:fn.id,invocation_id:call.id,
    read_http_status:read.value.status,write_http_status:write.value.status,guard_elapsed_ms:restored.elapsed_ms});
  // Preserve the actual failed read as the primary, even after successful restoration and cleanup.
  try {assert.equal(read.value.status,200);}catch(error){c.failure=diagnosis(error);process.exitCode=1;}
} catch(error) {c.failure??=diagnosis(error);process.exitCode=1;}
finally {
  try {
    try {
      await joinJournalSqlBarriers(c);await c.joinPending();
      await c.close({nativeCleanup:async()=>{
        const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});
      }});
    } catch(error) {c.cleanupErrors.push({phase:'guard-closure-cleanup',...diagnosis(error)});c.completed=false;process.exitCode=1;await c.save();}
  } finally {
    await c.closeLocal();await c.save();if(!c.completed)process.exitCode=1;
  }
}
console.log(JSON.stringify({completed:c.completed,groups:0,cleanup:c.cleanup,report:c.report.pathname}));
