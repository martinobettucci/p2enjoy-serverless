// @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// Reproduce the real corpus and observe the failed boundary; zero qualified groups.
import assert from 'node:assert/strict';
import {JournalCampaign,privateInput,diagnosis} from './execution-journal-harness.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {inspectJournal,joinJournalSqlBarriers} from './execution-journal-native.mjs';

const c=new JournalCampaign('api');
try {
  const credentials=await privateInput();await c.open(credentials);
  const cases=new JournalApiCases(c,credentials);await cases.prepare();
  for(const [name,run] of [
    ['formats',()=>cases.formats()],['scopes',()=>cases.scopes()],
    ['filters',()=>cases.filters()],['projection',()=>cases.projection()],
    ['expiration',()=>cases.expiration()],
  ]) {
    c.stage='Diagnostic121 : corpus réel / '+name;await c.save();await run();
    c.observations.push({scenario:'diagnostic-real-prefix',name});await c.save();
  }
  c.stage='Diagnostic121 : observation de la frontière finale';await c.save();
  try {await cases.policies();c.observations.push({scenario:'diagnostic-boundary-outcome',returned:true});}
  catch(error) {c.observations.push({scenario:'diagnostic-boundary-outcome',returned:false,...diagnosis(error)});}
  await joinJournalSqlBarriers(c);await c.joinPending();
  const http=c.observations.filter(row=>row.scenario==='final-read-http-observed');
  const native=c.observations.flatMap(row=>row.scenario==='native-reader'?row.events:[])
    .filter(row=>row.event==='syscall-diagnostic');
  assert(http.length>=1 && native.length>=1,'diagnostic_native_and_HTTP_observations_required');
  assert(http.every(row=>Number.isFinite(row.elapsed_ms) && (Number.isInteger(row.http_status) || row.transport_failure)),
    'diagnostic_HTTP_outcome_incomplete');
  assert(native.every(row=>row.registers_or_results_modified===false && row.application_buffers_read===false));
  assert.equal(c.checks.length,0);c.scenariosPassed=true;
} catch(error) {c.failure=diagnosis(error);process.exitCode=1;}
finally {
  try {
    await joinJournalSqlBarriers(c);await c.joinPending();
    await c.close({nativeCleanup:async()=>{
      const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});
    }});
  } catch(error) {c.cleanupErrors.push({phase:'diagnostic-cleanup',...diagnosis(error)});c.completed=false;process.exitCode=1;await c.save();}
  if(!c.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:c.completed,groups:0,cleanup:c.cleanup,report:c.report.pathname}));
