// @spec docs/BACKLOG.md#sls-130 | docs/EXECUTION_LOGS.md#réponse-de-politique-arrêtée-dans-le-navigateur--sls-130
// @verifies docs/BACKLOG.md#sls-130 | docs/EXECUTION_LOGS.md#console-et-manuel
// One real UI07 scenario shared by the complete campaign and its zero-group preparatory client.
import assert from 'node:assert/strict';
import {base,endpoint,match,until,sha,diagnosis} from './execution-journal-harness.mjs';
import {JournalSqlBarrier} from './execution-journal-native.mjs';

// @spec docs/BACKLOG.md#sls-137
// Observe the real archived-function read, without modifying or retrying it.
async function archivedJournalRead(c,cases,invocation,ready,journal) {
  const path='/api/services/'+cases.service.id+'/logs',pending=[];
  const observation={scenario:'archived-function-service-journal-browser-read',invocation_id:invocation,
    service_id:cases.service.id,function_id:cases.fn.id,events:[],started_at_ms:Date.now()};
  c.observations.push(observation);
  const record=row=>{if(observation.events.length<100){observation.events.push(row);return true;}observation.events_omitted=(observation.events_omitted || 0)+1;return false;};
  const parameters=url=>[...new URL(url).searchParams].map(([key,value])=>{
    const allowed=(['from','to'].includes(key) && /^\d{4}-\d\d-\d\dT[\d:.]+Z$/.test(value)) ||
      (key==='source' && value==='platform') || (key==='invocation' && value===invocation) ||
      (['limit','offset','page'].includes(key) && /^\d{1,6}$/.test(value));
    return allowed?{key,value}:{key_sha256:sha(key),value_sha256:sha(value)};
  });
  const selected=request=>request.method()==='GET' && new URL(request.url()).pathname===path;
  const requested=request=>{if(selected(request))record({event:'request',at_ms:Date.now(),parameters:parameters(request.url())});};
  const failed=request=>{if(selected(request))record({event:'requestfailed',at_ms:Date.now(),error_sha256:sha(request.failure()?.errorText || '')});};
  const received=response=>{
    if(!selected(response.request()))return;
    const row={event:'response',at_ms:Date.now(),status:response.status()};if(!record(row))return;
    pending.push(c.track((async()=>{
      try {
        const body=await response.body();row.body_bytes=body.length;row.body_sha256=sha(body);
        if(body.length>1024**2){row.structure_omitted='body_over_1MiB';return;}
        let value;try {value=JSON.parse(body.toString('utf8'));}catch {row.json_valid=false;return;}
        row.json_valid=true;
        const type=value=>value===null?'null':Array.isArray(value)?'array':typeof value;
        row.structure=Object.fromEntries(['items','total','limit','mode','snapshot','follow_cursor','partial','period','collection','error'].map(key=>[key,type(value?.[key])]));
        if(Array.isArray(value?.items))row.items=value.items.slice(0,5).map(item=>({id_type:type(item?.id),message_type:type(item?.message),observed_at_type:type(item?.observed_at),metadata_type:type(item?.metadata),function_name_type:type(item?.function_name)}));
        for(const key of ['total','limit'])if(Number.isSafeInteger(value?.[key]))row[key]=value[key];
        if(typeof value?.error==='string')row.error_sha256=sha(value.error);
      } catch(error) {row.body_observation_failure=diagnosis(error);}
    })()));
  };
  const pageError=error=>record({event:'pageerror',at_ms:Date.now(),...diagnosis(error)});
  c.page.on('request',requested);c.page.on('requestfailed',failed);c.page.on('response',received);c.page.on('pageerror',pageError);
  let primary;
  try {
    await c.page.goto(base+'/console/services/'+cases.service.id+'/logs?source=platform&invocation='+invocation);await ready();observation.ready=true;
  } catch(error) {primary=error;observation.failure=diagnosis(error);}
  finally {
    c.page.off('request',requested);c.page.off('requestfailed',failed);c.page.off('response',received);c.page.off('pageerror',pageError);
    try {
      observation.url_parameters=parameters(c.page.url());
      observation.route_matches=new URL(c.page.url()).pathname==='/console/services/'+cases.service.id+'/logs';
      const alerts=await c.page.getByRole('alert').allTextContents();observation.alerts=alerts.map(text=>({sha256:sha(text),characters:text.length}));
      const follow=journal().getByRole('button',{name:'Suivre les nouveaux événements',exact:true});
      observation.follow_buttons=await follow.count();if(observation.follow_buttons===1)observation.follow_disabled=await follow.isDisabled();
      observation.loading=await journal().getByText('Chargement des journaux…',{exact:true}).count();
      observation.rows=await journal().locator('[data-log-id]').count();
      if(primary)await c.capture('archived-reference-read-failed',c.page);
    } catch(error) {observation.dom_observation_failure=diagnosis(error);}
    const joined=Promise.all(pending);let timer;
    try {
      const complete=await Promise.race([joined.then(()=>true),new Promise(resolve=>{
        timer=setTimeout(()=>resolve(false),Math.max(0,observation.started_at_ms+90000-Date.now()));
      })]);
      if(!complete) {
        observation.body_join_deadline_reached=true;
        if(!primary) {
          primary=new Error('archived_journal_observation_not_joined');observation.failure=diagnosis(primary);
          try {await c.capture('archived-reference-read-failed',c.page);}catch(error) {observation.capture_failure=diagnosis(error);}
        }
        // Closing this owned Page aborts real pending reads before joining them.
        await c.page.close();observation.page_closed_to_cancel_reads=true;await joined;
      }
    } catch(error) {if(!primary)primary=error;else observation.join_failure=diagnosis(error);}
    finally {clearTimeout(timer);}
    observation.finished_at_ms=Date.now();
    try {await c.save();}catch(error) {if(!primary)throw error;observation.save_failure=diagnosis(error);}
  }
  if(primary)throw primary;
}

export async function retentionPolicyCase(c,cases) {
  const panel=(page,title)=>page.locator('section.panel').filter({has:page.getByRole('heading',{name:title,exact:true})});
  const journal=()=>panel(c.page,'Journaux');
  const ready=()=>until(()=>journal().getByRole('button',{name:'Suivre les nouveaux événements',exact:true}).isEnabled(),'journal_history_not_ready');
  const done=async promise=>{const result=await promise;if(result.error)throw result.error;return result.value;};
  async function response(page,path,action,{method='GET',status=200}={}) {
    const pending=c.track(page.waitForResponse(r=>new URL(r.url()).pathname===path && r.request().method()===method,{timeout:15000}));
    await action();const r=await done(pending);assert.equal(r.status(),status);return r;
  }

    await c.page.goto(base+'/console/functions/'+cases.fn.id+'/logs');await ready();await c.page.getByRole('link',{name:'Journaux et conservation de tout le service',exact:true}).click();await ready();
    const retention=panel(c.page,'Conservation des journaux'),opener=retention.getByRole('button',{name:'Modifier la conservation',exact:true});await until(()=>opener.isEnabled(),'retention_not_ready');await opener.click();
    let dialog=c.page.getByRole('dialog',{name:'Conservation des journaux',exact:true}),input=dialog.getByLabel('Conservation (minutes)',{exact:true});
    const prior=await c.value('/api/services/'+cases.service.id+'/log-policy'),policyPath='/api/services/'+cases.service.id+'/log-policy';
    const wanted=prior.retention_minutes<10080?prior.retention_minutes+1:prior.retention_minutes-1;await input.fill(String(wanted));
    const committed=await new JournalSqlBarrier(c,cases.image,1,'policy-commit').start();let writes=0;
    let stop;
    const transport={scenario:'policy-browser-native-stop',method:'Page.stopLoading',events:[],response_status:null};c.observations.push(transport);
    const count=request=>{if(new URL(request.url()).pathname===policyPath && request.method()==='PUT'){writes++;transport.events.push({event:'request',at_ms:Date.now()});}};
    const received=response=>{if(new URL(response.url()).pathname===policyPath && response.request().method()==='PUT'){transport.response_status=response.status();transport.events.push({event:'response',at_ms:Date.now(),status:response.status()});}};
    const interrupted=request=>{if(new URL(request.url()).pathname===policyPath && request.method()==='PUT')transport.events.push({event:'requestfailed',at_ms:Date.now(),error_sha256:request.failure()?sha(request.failure().errorText):null});};
    c.page.on('request',count);c.page.on('response',received);c.page.on('requestfailed',interrupted);
    try {
      stop=await c.context.newCDPSession(c.page);await stop.send('Page.enable');
      const failed=c.track(c.page.waitForEvent('requestfailed',{predicate:request=>new URL(request.url()).pathname===policyPath && request.method()==='PUT',timeout:10000}));
      await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();
      if(wanted<prior.retention_minutes)await dialog.getByRole('button',{name:'Confirmer la diminution',exact:true}).click();
      const held=await committed.held();assert.equal(held.readers[0].boundary,'policy-commit');
      const actual=await c.value(policyPath);assert.equal(actual.version,prior.version+1);assert.equal(actual.retention_minutes,wanted);
      transport.events.push({event:'commit-read-before-stop',at_ms:Date.now(),version:actual.version});assert.equal(transport.response_status,null);
      transport.events.push({event:'stop-intent',at_ms:Date.now()});await c.save();await stop.send('Page.stopLoading');transport.events.push({event:'stop-ack',at_ms:Date.now()});
      const lost=await done(failed);assert(lost.failure());assert.equal(transport.response_status,null);
      await c.save();
      await dialog.getByText(/Son résultat est inconnu/).waitFor();assert(await dialog.getByRole('button',{name:'Enregistrer',exact:true}).isDisabled());assert.equal(await input.inputValue(),String(wanted));await c.capture('retention-response-lost',c.page,dialog);
      await committed.close();
      await response(c.page,policyPath,()=>dialog.getByRole('button',{name:'Relire la politique',exact:true}).click());await dialog.getByText(/Votre saisie est conservée/).waitFor();assert.equal(writes,1);
      c.observations.push({scenario:'committed-policy-response-lost-in-real-browser',before_version:prior.version,after_version:actual.version,put_requests:writes,network_failure_sha256:sha(lost.failure().errorText),draft_preserved:true});
    } catch(error) {transport.failure=diagnosis(error);throw error;}
    finally {c.page.off('request',count);c.page.off('response',received);c.page.off('requestfailed',interrupted);try {if(stop)await stop.detach();}finally {if(!committed.closed)await committed.close();await c.save();}}
    await c.page.keyboard.press('Escape');await dialog.getByRole('button',{name:'Abandonner',exact:true}).click();await dialog.waitFor({state:'hidden'});await until(()=>opener.isEnabled(),'retention_unknown_reread_not_joined');await opener.click();
    dialog=c.page.getByRole('dialog',{name:'Conservation des journaux',exact:true});input=dialog.getByLabel('Conservation (minutes)',{exact:true});await input.fill('1');
    const before=await c.value('/api/services/'+cases.service.id+'/log-policy');await cases.policy(cases.service,before.retention_minutes-1);
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await dialog.getByRole('button',{name:'Confirmer la diminution',exact:true}).click();
    await dialog.getByText(/La politique a changé dans une autre session/).waitFor();assert.equal(await input.inputValue(),'1');assert(await dialog.getByRole('button',{name:'Enregistrer',exact:true}).isDisabled());await c.capture('retention-conflict',c.page,dialog);
    await response(c.page,'/api/services/'+cases.service.id+'/log-policy',()=>dialog.getByRole('button',{name:'Relire la politique',exact:true}).click());await dialog.getByText(/Votre saisie est conservée/).waitFor();assert.equal(await input.inputValue(),'1');
    await input.fill('0');assert.equal(await input.evaluate(element=>element.validity.rangeUnderflow),true);await input.fill('10081');assert.equal(await input.evaluate(element=>element.validity.rangeOverflow),true);await input.fill('1');
    await dialog.getByRole('button',{name:'Enregistrer',exact:true}).click();await dialog.getByText(new RegExp(cases.service.name)).waitFor();
    await response(c.page,'/api/services/'+cases.service.id+'/log-policy',()=>dialog.getByRole('button',{name:'Confirmer la diminution',exact:true}).click(),{method:'PUT'});await dialog.waitFor({state:'hidden'});
    const current=await c.value('/api/services/'+cases.service.id+'/log-policy');assert.equal(current.retention_minutes,1);await until(()=>opener.isEnabled(),'retention_save_reread_missing');await c.capture('retention-saved',c.page,retention);
    const finalCall=await cases.invoke('text');await c.value(endpoint(cases.fn),{method:'DELETE'});
    await archivedJournalRead(c,cases,finalCall.id,ready,journal);
    await c.value(endpoint(cases.fn)+'/logs'+'?source=application&invocation='+finalCall.id,{status:404});
    const unavailable=journal().locator('[data-log-id] article').first();await unavailable.locator(':scope > details > summary').click();await unavailable.getByText(/Objet indisponible/).waitFor();assert.equal(await unavailable.getByRole('link',{name:'Ouvrir la fonction',exact:true}).count(),0);await c.capture('archived-reference',c.page,unavailable.getByText(/Objet indisponible/));
    c.observations.push({scenario:'real-retention-conflict-and-save',before_version:before.version,after_version:current.version,draft_preserved:true,retention_minutes:1});
}
