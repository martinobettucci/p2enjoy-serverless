// @spec docs/BACKLOG.md#sls-130 | docs/EXECUTION_LOGS.md#réponse-de-politique-arrêtée-dans-le-navigateur--sls-130
// @verifies docs/BACKLOG.md#sls-130 | docs/EXECUTION_LOGS.md#console-et-manuel
// Isolate the same real UI07 case. No qualified group, mock or intercepted response.
import {JournalCampaign,privateInput,diagnosis} from './execution-journal-harness.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {retentionPolicyCase} from './execution-journal-ui-policy-case.mjs';
import {inspectJournal,joinJournalSqlBarriers,joinJournalCuts} from './execution-journal-native.mjs';
const c=new JournalCampaign('ui');
try {
  await c.open(await privateInput());const cases=new JournalApiCases(c,null);await cases.prepare();
  c.stage='Diagnostic réel UI07 après commit de politique';await c.save();
  await retentionPolicyCase(c,cases);c.scenariosPassed=true;
} catch(error) {c.failure=diagnosis(error);process.exitCode=1;}
finally {
  const attempt=async(phase,run)=>{try{await run();}catch(error){c.cleanupErrors.push({phase,...diagnosis(error)});process.exitCode=1;}};
  await attempt('join-native-sql-barriers',()=>joinJournalSqlBarriers(c));await attempt('join-native-control-cuts',()=>joinJournalCuts(c));await attempt('join-http-operations',()=>c.joinPending());
  await attempt('owned-resources',()=>c.close({nativeCleanup:async()=>{const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});}}));
  c.completed=c.scenariosPassed && c.cleanup && !c.cleanupErrors.length;await c.save();if(!c.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:c.completed,groups:0,cleanup:c.cleanup,report:c.report.pathname}));
