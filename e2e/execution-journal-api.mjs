// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// Twelve named real API groups, serial, with owned native recovery before cleanup.
import assert from 'node:assert/strict';
import {JournalCampaign,privateInput,diagnosis} from './execution-journal-harness.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {eventBudget,byteBudget} from './execution-journal-budget-cases.mjs';
import {inspectJournal,joinJournalSqlBarriers,joinJournalCuts} from './execution-journal-native.mjs';

const campaign=new JournalCampaign('api');
try {
  const credentials=await privateInput();await campaign.open(credentials);
  const cases=new JournalApiCases(campaign,credentials);
  campaign.stage='Préconditions, fixture originale et publication pilote explicite';await campaign.save();await cases.prepare();
  for(const [name,run] of [
    ['API 01 — buffers, Unicode, JSON et niveaux réels',()=>cases.formats()],
    ['API 02 — droits, scopes et révocation acceptée pendant IO',()=>cases.scopes()],
    ['API 03 — filtres, bornes et pages stables',()=>cases.filters()],
    ['API 04 — projections, buffers et secrets expurgés',()=>cases.projection()],
    ['API 07 — minute écoulée, effacement et absence de résurrection',()=>cases.expiration()],
    ['API 08 — politique, ordre de décision, perte de réponse et autorité retirée',()=>cases.policies()],
    ['API 09 — vrais exports bornés, reprise et refus',()=>cases.exports()],
    ['API 10 — suivi, vraie coupure et compteur sans rejeu',()=>cases.followAndRestart()],
    ['API 11 — cycles, classifications et corrélation de stockage',()=>cases.correlations()],
    ['API 12 — lecteurs retenus, 429, jonction et EMFILE réel',()=>cases.readers()],
    ['API 05 — exactement 10000 événements puis dépassement',()=>eventBudget(campaign)],
    ['API 06 — exactement 16 Mio puis un octet supplémentaire',()=>byteBudget(campaign)],
  ])await campaign.check(name,run);
  assert.equal(campaign.checks.length,12);assert(campaign.checks.every(row=>row.status==='passed'));
  campaign.scenariosPassed=true;
} catch(error) {
  campaign.failure=diagnosis(error);process.exitCode=1;
} finally {
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
console.log(JSON.stringify({completed:campaign.completed,groups:campaign.checks.filter(row=>row.status==='passed').length,
  cleanup:campaign.cleanup,report:campaign.report.pathname}));
