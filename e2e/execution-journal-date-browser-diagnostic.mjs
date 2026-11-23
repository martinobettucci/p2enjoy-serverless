// @spec docs/BACKLOG.md#sls-138
// @verifies docs/BACKLOG.md#sls-138 | docs/EXECUTION_LOGS.md#console-et-manuel
// Diagnose native date normalization on the deployed console, through real inputs.
import assert from 'node:assert/strict';
import {JournalCampaign,privateInput,diagnosis,base,endpoint,until,utcDateInputValue} from './execution-journal-harness.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {inspectJournal} from './execution-journal-native.mjs';

const c=new JournalCampaign('ui');
try {
  await c.open(await privateInput());const cases=new JournalApiCases(c,null);await cases.prepare();await cases.invoke('text');
  c.stage='Diagnostic réel des formes natives FinUTC';await c.save();
  c.observations.push({scenario:'native-date-browser-version',version:c.browser.version()});
  const future=new Date(Date.now()+3600000);future.setUTCSeconds(34,0);
  const seconds=future.toISOString().slice(0,19),minute=seconds.slice(0,16);
  const variants=[
    {name:'fraction-120-raw',input:seconds+'.120',native:seconds+'.12',accepted:false},
    {name:'fraction-123',input:seconds+'.123',native:seconds+'.123',accepted:true},
    {name:'fraction-zero-raw',input:seconds+'.000',native:seconds,accepted:false},
    {name:'minute-raw',input:minute+':00.000',native:minute,accepted:false},
    {name:'fraction-120-canonical',input:seconds+'.12',native:seconds+'.12',accepted:true},
    {name:'fraction-zero-canonical',input:seconds,native:seconds,accepted:true},
    {name:'minute-canonical',input:minute,native:minute,accepted:true},
    {name:'fraction-100-canonical',input:seconds+'.1',native:seconds+'.1',accepted:true},
    {name:'fraction-010-canonical',input:seconds+'.01',native:seconds+'.01',accepted:true},
    {name:'fraction-001-canonical',input:seconds+'.001',native:seconds+'.001',accepted:true},
  ];
  for(const variant of variants) {
    await c.page.goto(base+'/console/functions/'+cases.fn.id+'/logs');
    const journal=c.page.locator('section.panel').filter({has:c.page.getByRole('heading',{name:'Journaux',exact:true})});
    await until(()=>journal.getByRole('button',{name:'Suivre les nouveaux événements',exact:true}).isEnabled(),'date_diagnostic_journal_not_ready');
    const input=journal.getByLabel('Fin (UTC)',{exact:true});
    const row={scenario:'real-native-date-input',...variant};c.observations.push(row);await c.save();
    const candidate=variant.accepted?utcDateInputValue(new Date(Date.parse(variant.input+'Z'))):variant.input;
    row.shared_formatter=variant.accepted;assert.equal(candidate,variant.input);
    try {await input.fill(candidate);row.fill_returned=true;}
    catch(error) {row.failure=diagnosis(error);row.error_class=String(error.message).includes('Malformed value')?'native-value-normalized':'unclassified';}
    row.control=await input.evaluate(element=>({type:element.type,step:element.getAttribute('step'),value:element.value,
      valid:element.validity.valid,bad_input:element.validity.badInput,step_mismatch:element.validity.stepMismatch}));
    assert.equal(row.control.type,'datetime-local');assert.equal(row.control.step,'0.001');assert.equal(row.control.value,variant.native);assert(row.control.valid);
    assert.equal(Boolean(row.fill_returned),variant.accepted);
    if(!variant.accepted)assert.equal(row.error_class,'native-value-normalized');
    else {
      const pending=c.track(c.page.waitForResponse(response=>new URL(response.url()).pathname===endpoint(cases.fn)+'/logs' && response.request().method()==='GET',{timeout:15000}));
      await journal.getByRole('button',{name:'Rechercher',exact:true}).click();const result=await pending;if(result.error)throw result.error;
      const response=result.value;row.http_status=response.status();assert.equal(row.http_status,200);const data=await response.json();
      row.actual_period=data.period;row.total=data.total;assert.equal(data.period.to,Date.parse(variant.native+'Z')/1000);assert(data.total>0);
      await until(()=>journal.getByRole('button',{name:'Suivre les nouveaux événements',exact:true}).isEnabled(),'date_diagnostic_search_not_ready');
    }
    if(variant.name==='fraction-120-raw')await c.capture('date-native-normalized-refusal',c.page,input);
    if(variant.name==='minute-canonical')await c.capture('date-native-minute-search',c.page,input);
    row.completed=true;await c.save();
  }
  c.scenariosPassed=true;
} catch(error) {c.failure=diagnosis(error);process.exitCode=1;}
finally {
  try {await c.close({nativeCleanup:async()=>{const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});}});}
  catch(error) {c.cleanupErrors.push({phase:'owned-resources',...diagnosis(error)});process.exitCode=1;}
  c.completed=c.scenariosPassed && c.cleanup && !c.cleanupErrors.length;await c.save();if(!c.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:c.completed,groups:0,cleanup:c.cleanup,report:c.report.pathname}));
