// @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// Bounded reproduction of the real reader/health failure; zero qualified groups.
import {JournalCampaign,privateInput,diagnosis} from './execution-journal-harness.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {inspectJournal,joinJournalSqlBarriers,joinJournalCuts} from './execution-journal-native.mjs';
const campaign=new JournalCampaign('api');
try {
  const credentials=await privateInput();await campaign.open(credentials);
  const cases=new JournalApiCases(campaign,credentials);
  await cases.prepare();campaign.stage='Diagnostic réel des trois vagues de lecteurs';await campaign.save();
  for(let attempt=1;attempt<=3;attempt++){campaign.observations.push({scenario:'reader-health-reproduction-attempt',attempt});await campaign.save();await cases.readers();}
  campaign.scenariosPassed=true;
} catch(error) {campaign.failure=diagnosis(error);process.exitCode=1;}
finally {
  const attempt=async(phase,run)=>{try{await run();}catch(error){campaign.cleanupErrors.push({phase,...diagnosis(error)});process.exitCode=1;}};
  await attempt('join-native-sql-barriers',()=>joinJournalSqlBarriers(campaign));
  await attempt('join-native-control-cuts',()=>joinJournalCuts(campaign));
  await attempt('join-http-operations',()=>campaign.joinPending());
  await attempt('owned-resources',()=>campaign.close({nativeCleanup:async()=>{
    const result=await inspectJournal(campaign,'cleanup');campaign.observations.push({scenario:'native-complete-cleanup',result});
  }}));
  campaign.completed=campaign.scenariosPassed && campaign.cleanup && !campaign.cleanupErrors.length;
  await campaign.save();if(!campaign.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:campaign.completed,groups:0,cleanup:campaign.cleanup,report:campaign.report.pathname}));
