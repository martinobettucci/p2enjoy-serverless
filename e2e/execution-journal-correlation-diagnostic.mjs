// @spec docs/BACKLOG.md#sls-125 | docs/EXECUTION_LOGS.md#modèle-et-migration-011
// @verifies docs/BACKLOG.md#sls-125 | docs/EXECUTION_LOGS.md#modèle-et-migration-011
// Isolated original correlation scenario; diagnostic epoch, zero qualified groups.
import {JournalCampaign,privateInput,diagnosis} from './execution-journal-harness.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {inspectJournal,joinJournalSqlBarriers,joinJournalCuts} from './execution-journal-native.mjs';
const campaign=new JournalCampaign('api');
try {
  const credentials=await privateInput();await campaign.open(credentials);
  const cases=new JournalApiCases(campaign,credentials);
  await cases.prepare();
  const sibling=await campaign.function(cases.service,'journal-other-function');
  const siblingVersion=await campaign.publish(sibling,'journal-other');await campaign.promote(sibling,siblingVersion.code_hash);
  await cases.invoke('text',{},sibling,cases.reader);
  campaign.stage='Diagnostic réel de corrélation après purge du frère';await campaign.save();
  await cases.correlations();campaign.scenariosPassed=true;
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
