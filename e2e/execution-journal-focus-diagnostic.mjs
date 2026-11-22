// @spec docs/BACKLOG.md#sls-124 | docs/EXECUTION_LOGS.md#console-et-manuel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md
// @verifies docs/BACKLOG.md#sls-124 | docs/EXECUTION_LOGS.md#console-et-manuel
// Repeat the real focus cases on desktop/mobile; no qualified UI group.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {JournalCampaign,privateInput,diagnosis,base,match,until} from './execution-journal-harness.mjs';
import {inspectJournal,joinJournalSqlBarriers,joinJournalCuts} from './execution-journal-native.mjs';
const campaign=new JournalCampaign('ui');
const section=(page,title)=>page.locator('section.panel').filter({has:page.getByRole('heading',{name:title,exact:true})});
async function capture(name) {
  const filename='execution-journal-focus-'+campaign.id+'-'+name+'.jpg',path=new URL(filename,campaign.output);
  await campaign.page.screenshot({path:path.pathname,type:'jpeg',quality:85});
  const bytes=await readFile(path);campaign.captures[filename]=createHash('sha256').update(bytes).digest('hex');await campaign.save();
}
async function focus() {
  return campaign.page.evaluate(()=>{const element=document.activeElement;return {tag:element?.tagName,role:element?.getAttribute('role'),text:element?.tagName==='BUTTON' || /^H[1-6]$/.test(element?.tagName)?element.textContent.trim():null,disabled:Boolean(element?.disabled)};});
}
try {
  await campaign.open(await privateInput());const page=campaign.page;
  const pageErrors=[];page.on('pageerror',error=>pageErrors.push(diagnosis(error)));
  campaign.observations.push({scenario:'browser-page-errors',errors:pageErrors});
  const service=await campaign.service('journal-keyboard-focus'),fn=await campaign.function(service,'journal-keyboard-handler');
  const token=await campaign.mint(service),version=await campaign.publish(fn,'journal-keyboard-focus');await campaign.promote(fn,version.code_hash);
  await campaign.invoke(fn,token,{mode:'text'});
  const results=[];
  for(const [width,height] of [[1440,1000],[390,844]]) {
  await page.setViewportSize({width,height});
  await page.goto(base);await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
  await page.getByLabel('Rechercher une fonction',{exact:true}).fill(fn.name);
  const functionLink=page.getByRole('link',{name:fn.name,exact:true});await functionLink.focus();await page.keyboard.press('Enter');
  const tab=page.getByRole('link',{name:'Journaux',exact:true});await tab.focus();await page.keyboard.press('Enter');
  const serviceLink=page.getByRole('link',{name:'Journaux et conservation de tout le service',exact:true});await serviceLink.focus();await page.keyboard.press('Enter');
  const retention=section(page,'Conservation des journaux'),journal=section(page,'Journaux');
  const opener=retention.getByRole('button',{name:'Modifier la conservation',exact:true});
  await until(()=>opener.isEnabled(),'retention_command_not_ready');await opener.focus();await page.keyboard.press('Enter');
  const dialog=page.getByRole('dialog',{name:'Conservation des journaux',exact:true});await dialog.waitFor();await capture('retention-open-'+width);
  await page.evaluate(()=>{
    const events=[];const describe=element=>({tag:element?.tagName,disabled:Boolean(element?.disabled)});
    const record=event=>{if(events.length<64)events.push({type:event.type,target:describe(event.target),active:describe(document.activeElement)});};
    document.addEventListener('focusin',record,true);document.addEventListener('focusout',record,true);
    window.__journalFocusObservation={events,stop(){document.removeEventListener('focusin',record,true);document.removeEventListener('focusout',record,true);return events;}};
  });
  const policyRead=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/services/'+service.id+'/log-policy' && response.request().method()==='GET');
  await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert.equal((await policyRead).status(),200);
  await until(()=>opener.isEnabled(),'retention_command_not_restored');
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const retentionFocus=await focus(),retentionPassed=await retention.getByRole('heading',{name:'Conservation des journaux',exact:true}).evaluate(element=>element===document.activeElement);
  const focusEvents=await page.evaluate(()=>{const rows=window.__journalFocusObservation.stop();delete window.__journalFocusObservation;return rows;});
  campaign.observations.push({scenario:'retention-escape-focus-after-real-reread',viewport:width,focus:retentionFocus,focus_events:focusEvents,passed:retentionPassed,policy_http_status:200});await capture('retention-closed-'+width);
  const follow=journal.getByRole('button',{name:'Suivre les nouveaux événements',exact:true});await until(()=>follow.isEnabled(),'journal_not_ready');
  await follow.focus();await page.keyboard.press('Enter');
  const pause=journal.getByRole('button',{name:'Mettre en pause',exact:true});await pause.waitFor();
  await campaign.invoke(fn,token,{mode:'text'});await until(async()=>await journal.locator('[data-log-id]').count()>0,'live_rows_missing');
  await pause.focus();assert(await pause.evaluate(element=>element===document.activeElement));
  const path='/api/services/'+service.id+'/log-policy',old=await campaign.value(path);
  const invalidated=campaign.track(page.waitForResponse(response=>new URL(response.url()).pathname==='/api/services/'+service.id+'/logs' && response.request().method()==='GET' && response.status()===410,{timeout:10000}));
  const changed=await campaign.value(path,{method:'PUT',headers:match(old.version),body:{retention_minutes:old.retention_minutes-1}});assert.equal(changed.version,old.version+1);
  const invalid=await invalidated;if(invalid.error)throw invalid.error;const refused=await invalid.value.json();assert.equal(refused.error,'log_policy_changed');
  await journal.getByRole('alert').waitFor();await until(async()=>await journal.locator('[data-log-id]').count()===0,'invalidated_live_rows_retained');
  const resume=journal.getByRole('button',{name:'Reprendre le suivi',exact:true});assert(await resume.isDisabled());
  const liveFocus=await focus(),livePassed=await journal.getByRole('heading',{name:'Journaux',exact:true}).evaluate(element=>element===document.activeElement);
  campaign.observations.push({scenario:'focused-pause-invalidated-by-real-policy-change',viewport:width,http_status:invalid.value.status(),public_error:refused.error,focus:liveFocus,passed:livePassed,rows:0,disabled_resume:true,before_version:old.version,after_version:changed.version});await capture('live-invalidated-'+width);
  results.push(retentionPassed && livePassed);
  }
  assert.deepEqual(pageErrors,[]);assert(results.every(Boolean),'journal_keyboard_focus_not_restored');campaign.scenariosPassed=true;
} catch(error) {campaign.failure=diagnosis(error);process.exitCode=1;}
finally {
  const attempt=async(phase,run)=>{try{await run();}catch(error){campaign.cleanupErrors.push({phase,...diagnosis(error)});process.exitCode=1;}};
  await attempt('join-native-sql-barriers',()=>joinJournalSqlBarriers(campaign));
  await attempt('join-native-control-cuts',()=>joinJournalCuts(campaign));
  await attempt('join-http-operations',()=>campaign.joinPending());
  await attempt('owned-resources',()=>campaign.close({nativeCleanup:async()=>{const result=await inspectJournal(campaign,'cleanup');campaign.observations.push({scenario:'native-complete-cleanup',result});}}));
  campaign.completed=campaign.scenariosPassed && campaign.cleanup && !campaign.cleanupErrors.length;await campaign.save();if(!campaign.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:campaign.completed,groups:0,cleanup:campaign.cleanup,report:campaign.report.pathname}));
