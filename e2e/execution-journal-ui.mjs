// @spec docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-124 | docs/EXECUTION_LOGS.md#console-et-manuel
// @verifies docs/EXECUTION_LOGS.md#découpage-et-qualification-réels | docs/DESIGN_SYSTEM_APP.md
// Real browser/API/Docker scenarios. No network interception or synthetic server.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {JournalCampaign,privateInput,diagnosis,base,endpoint,match,until,delay,sha,adminConnection,utcDateInputValue} from './execution-journal-harness.mjs';
import {retentionPolicyCase} from './execution-journal-ui-policy-case.mjs';
import {JournalApiCases} from './execution-journal-api-cases.mjs';
import {inspectJournal,JournalSqlBarrier,joinJournalSqlBarriers,joinJournalCuts} from './execution-journal-native.mjs';

const c=new JournalCampaign('ui');let cases,credentials;
const panel=(page,title)=>page.locator('section.panel').filter({has:page.getByRole('heading',{name:title,exact:true})});
const journal=()=>panel(c.page,'Journaux');
const rows=()=>journal().locator('[data-log-id]');
const ids=()=>rows().evaluateAll(elements=>elements.map(element=>element.dataset.logId));
const path=()=>endpoint(cases.fn)+'/logs';
const done=async promise=>{const result=await promise;if(result.error)throw result.error;return result.value;};
async function response(page,pathname,action,{status=200,method='GET'}={}) {
  const pending=c.track(page.waitForResponse(r=>new URL(r.url()).pathname===pathname && r.request().method()===method,{timeout:15000}));
  await action();const r=await done(pending);assert.equal(r.status(),status);return r;
}
const capture=(name,page=c.page,target)=>c.capture(name,page,target);

async function ready() {await until(()=>journal().getByRole('button',{name:'Suivre les nouveaux événements',exact:true}).isEnabled(),'journal_history_not_ready');}
async function navigate(filters={}) {
  const params=new URLSearchParams(filters);await c.page.goto(base+'/console/functions/'+cases.fn.id+'/logs?'+params);await ready();
}
async function facets() {
  const detail=journal().locator('details.journal-correlation');if(await detail.getAttribute('open')===null)await detail.locator('summary').click();
}
async function filter(values) {
  await facets();const labels={source:'Source',severity:'Niveau',state:'État',invocation:'Identifiant d’appel ou de requête',instance:'Identifiant d’instance',version:'Hash complet du code',kind:'Type d’événement',q:'Texte à rechercher'};
  for(const [key,label]of Object.entries(labels)) {
    if(key!=='q')await facets();
    const input=journal().getByLabel(label,{exact:true});if(['source','severity','state'].includes(key))await input.selectOption(values[key]||'');else await input.fill(values[key]||'');
  }
  const result=await response(c.page,path(),()=>journal().getByRole('button',{name:'Rechercher',exact:true}).click());await ready();return result.json();
}
async function assertPage(data) {await until(async()=>JSON.stringify(await ids())===JSON.stringify(data.items.map(row=>row.id)),'journal_ids_not_http_page');}
async function details(id) {const card=journal().getByRole('article',{name:'Événement '+id,exact:true});await card.locator(':scope > details > summary').click();return card;}

try {
  credentials=await privateInput();await c.open(credentials);cases=new JournalApiCases(c,credentials);await cases.prepare();
  const errors=[];c.page.on('pageerror',error=>errors.push(diagnosis(error)));c.observations.push({scenario:'browser-page-errors',errors});
  await cases.formats();await cases.invoke('bytes',{bytes:4097});
  await c.check('UI 01 — Accueil, fonction, service et retour catalogue',async()=>{
    await c.page.goto(base);await c.page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
    await c.page.getByLabel('Rechercher une fonction',{exact:true}).fill(cases.fn.name);
    const link=c.page.getByRole('link',{name:cases.fn.name,exact:true});
    await until(async()=>{const href=await link.getAttribute('href');if(!href)return false;return new URLSearchParams(new URL(href,base).searchParams.get('catalogue')||'').get('q')===cases.fn.name;},'catalogue_query_not_applied');await link.focus();await c.page.keyboard.press('Enter');
    const tab=c.page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Journaux',exact:true});await tab.focus();await c.page.keyboard.press('Enter');await ready();
    const selected=new URL(c.page.url()).searchParams.get('catalogue');assert(selected);
    const service=c.page.getByRole('link',{name:'Journaux et conservation de tout le service',exact:true});await service.click();await ready();
    assert(new URL(c.page.url()).pathname.includes('/services/'+cases.service.id+'/logs'));
    await panel(c.page,'Conservation des journaux').getByRole('heading').waitFor();await capture('service-desktop');
    const catalogue=c.page.getByRole('link',{name:'Revenir au catalogue',exact:true});assert.equal(await catalogue.count(),1);await catalogue.click();
    await c.page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();assert.equal(await c.page.getByLabel('Rechercher une fonction',{exact:true}).inputValue(),cases.fn.name);
    c.observations.push({scenario:'catalogue-context-retained',catalogue_sha256:sha(selected)});await navigate();
  });
  await c.check('UI 02 — Filtres, pages stables, URL partageable et vide',async()=>{
    const call=cases.calls.levels,record=await c.value(endpoint(cases.fn)+'/invocations/'+call);
    const data=await filter({source:'application',invocation:call,instance:record.instance_id,version:record.resolved_code_hash,state:'succeeded',kind:'application.message'});
    assert.equal(data.total,15);assert.equal(data.items.length,5);await assertPage(data);
    const first=await ids(),nav=journal().getByRole('navigation',{name:'Pagination des journaux',exact:true});
    const next=await response(c.page,path(),()=>nav.getByRole('button',{name:'Suivante',exact:true}).click());const second=await next.json();await assertPage(second);
    assert.equal(second.total,15);assert(!second.items.some(row=>first.includes(row.id)));
    await journal().getByLabel('Fin (UTC)',{exact:true}).fill(utcDateInputValue(new Date(Date.now()+3600000)));
    const stable=await filter({source:'application'});assert(stable.total>5);
    const stableNext=await response(c.page,path(),()=>nav.getByRole('button',{name:'Suivante',exact:true}).click());const stablePage=await stableNext.json();await assertPage(stablePage);
    const inserted=await cases.invoke('levels');
    await response(c.page,path(),()=>nav.getByRole('button',{name:'Précédente',exact:true}).click());
    const same=await response(c.page,path(),()=>nav.getByRole('button',{name:'Suivante',exact:true}).click());const unchanged=await same.json();assert.deepEqual(unchanged.items,stablePage.items);assert.equal(unchanged.total,stable.total);await assertPage(unchanged);
    const shared=c.page.url();await c.page.goto(shared);await ready();
    const parameters=new URL(shared).searchParams;parameters.delete('page');parameters.delete('catalogue');parameters.set('limit','5');parameters.set('offset','5');
    const fresh=await c.value(path()+'?'+parameters);assert.equal(fresh.total,stable.total+15);await assertPage(fresh);
    c.observations.push({scenario:'matching-insertion-preserves-snapshot',inserted_invocation:inserted.id,old_total:stable.total,new_total:fresh.total,page_ids:stablePage.items.map(row=>row.id)});
    const restricted=await filter({source:'application',severity:'error',invocation:call,q:'explicite'});assert.equal(restricted.total,2);await assertPage(restricted);
    const empty=await filter({source:'application',invocation:call,q:'EXPlicite'});assert.equal(empty.total,0);assert.equal(await rows().count(),0);assert.equal(await nav.count(),0);
    await journal().getByText(/Aucun événement/).waitFor();await capture('empty');
    c.observations.push({scenario:'combined-filter-pages',first,second:second.items.map(row=>row.id),shared_url_sha256:sha(shared),empty:0});
  });
  await c.check('UI 03 — Chargement, ancienne requête annulée et session refusée',async()=>{
    await navigate({source:'application',invocation:cases.calls.levels});assert.equal(await rows().count(),5);
    const gate=await new JournalSqlBarrier(c,cases.image,1,'reader-start').start();
    try {
      await journal().getByRole('button',{name:'Nouveau relevé',exact:true}).click();await gate.held();
      await journal().getByText('Chargement des journaux…',{exact:true}).waitFor();assert.equal(await rows().count(),0);
      assert.equal(await journal().getByRole('navigation',{name:'Pagination des journaux',exact:true}).count(),0);
      assert(!/\d+ événements dans cette période/.test(await journal().innerText()));await capture('loading',c.page,journal().getByText('Chargement des journaux…',{exact:true}));
      const data=await filter({q:'no-such-event-'+c.id});assert.equal(data.total,0);await assertPage(data);
      await gate.close();assert.equal(await rows().count(),0);assert.equal(await journal().getByLabel('Texte à rechercher',{exact:true}).inputValue(),'no-such-event-'+c.id);
    } finally {if(!gate.closed)await gate.close();}
    const other=await adminConnection(c.browser,credentials);
    try {
      await other.page.goto(base+'/console/functions/'+cases.fn.id+'/logs');const view=panel(other.page,'Journaux');
      await until(()=>view.getByRole('button',{name:'Suivre les nouveaux événements',exact:true}).isEnabled(),'secondary_journal_not_ready');assert(await view.locator('[data-log-id]').count()>0);
      const logout=await other.admin.post('/auth/logout',{headers:{Origin:base,'X-CSRF-Token':other.session.csrf_token}});assert.equal(logout.status(),200);
      await response(other.page,path(),()=>view.getByRole('button',{name:'Nouveau relevé',exact:true}).click(),{status:401});
      await view.getByRole('alert').waitFor();assert.equal(await view.locator('[data-log-id]').count(),0);assert.equal(await view.getByRole('navigation',{name:'Pagination des journaux',exact:true}).count(),0);await capture('session-refused',other.page);
    } finally {await other.admin.dispose();await other.context.close();}
  });
  await c.check('UI 04 — Détails, JSON exact, HTML inerte et références',async()=>{
    await navigate({source:'application',invocation:cases.calls.text});const actual=await cases.application(cases.fn,cases.calls.text);
    const html=actual.find(row=>row.message.startsWith('<script>'));assert(html);const card=await details(html.id);
    assert.equal(await card.getByLabel('Texte de '+html.id,{exact:true}).textContent(),html.message);assert.equal(await c.page.evaluate(()=>globalThis.journalInjected),undefined);
    for(const value of [html.id,html.invocation_id,html.code_hash,html.service_id,html.function_id,html.instance_id])if(value)assert((await card.innerText()).includes(value));
    await card.getByText(/Date observée à la fin/).waitFor();await capture('text-and-correlation',c.page,card.getByLabel('Texte de '+html.id,{exact:true}));
    await navigate({source:'application',invocation:cases.calls.json});const structured=(await cases.application(cases.fn,cases.calls.json))[0],json=await details(structured.id);
    const text=await json.getByLabel('Texte de '+structured.id,{exact:true}).textContent();for(const value of ['9007199254740993','1.2300','1e+30','\\u00e9'])assert(text.includes(value));await capture('json-exact',c.page,json.getByLabel('Texte de '+structured.id,{exact:true}));
    await navigate({source:'application',invocation:cases.calls.bytes});const cut=(await cases.application(cases.fn,cases.calls.bytes))[0];assert(cut.message_truncated);const truncated=await details(cut.id);await truncated.getByText(/Message limité à 4096/).waitFor();
    const collected=await cases.invoke('bytes',{bytes:65537});await navigate({source:'application',invocation:collected.id});
    const collectionRows=await cases.application(cases.fn,collected.id),collectionItem=collectionRows.find(row=>row.collection_truncated);assert(collectionItem);
    const collectionCard=await details(collectionItem.id);await collectionCard.getByText(/Buffer de collecte limité à 64 Kio/).waitFor();await capture('collection-truncated',c.page,collectionCard.getByText(/Buffer de collecte limité à 64 Kio/));
    const projected=await cases.invoke('lines',{count:1025}),projectionRows=await cases.application(cases.fn,projected.id),projectionItem=projectionRows.find(row=>row.projection_truncated);assert(projectionItem);
    await navigate({source:'application',invocation:projected.id,q:projectionItem.message});const projectionCard=await details(projectionItem.id);await projectionCard.getByText(/Projection limitée aux 1024 premières lignes/).waitFor();await capture('projection-truncated',c.page,projectionCard.getByText(/Projection limitée aux 1024 premières lignes/));
    c.observations.push({scenario:'collection-and-projection-truncation-rendered',collection_invocation:collected.id,collection_event:collectionItem.id,projection_invocation:projected.id,projection_event:projectionItem.id});
    c.observations.push({scenario:'details-escaped-exact',html_event_id:html.id,json_event_id:structured.id,truncated_event_id:cut.id,script_executed:false});
  });
  await c.check('UI 05 — Résultat du testeur vers le même appel',async()=>{
    await navigate();await c.page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Tester',exact:true}).click();
    await c.page.getByLabel('Jeton Read',{exact:true}).fill(cases.reader.token);
    await c.page.getByLabel('Méthode HTTP',{exact:true}).selectOption('POST');await c.page.getByLabel('Corps de requête',{exact:true}).selectOption('json');await c.page.getByLabel('Contenu JSON',{exact:true}).fill('{"mode":"text"}');
    const sent=await response(c.page,endpoint(cases.fn)+'/test-invocation',()=>c.page.getByRole('button',{name:'Envoyer la requête',exact:true}).click(),{method:'POST'});const result=await sent.json();assert(result.request_id);
    await c.terminal(cases.fn,result.request_id);const before=await c.value(endpoint(cases.fn)+'/invocations');
    const link=c.page.getByRole('link',{name:'Rechercher les journaux de cet appel',exact:true});await link.focus();await c.page.keyboard.press('Enter');await ready();assert.equal(new URL(c.page.url()).searchParams.get('invocation'),result.request_id);
    assert(await rows().count()>0);const after=await c.value(endpoint(cases.fn)+'/invocations');assert.equal(after.total,before.total);await capture('tester-correlation',c.page,journal().locator('[data-log-id] article').first().getByRole('heading'));
    c.observations.push({scenario:'tester-no-reinvocation',invocation_id:result.request_id,before:before.total,after:after.total});
  });
  await c.check('UI 06 — Suivi, pause, reprise, fenêtre et focus',async()=>{
    await navigate({source:'application'});await journal().getByRole('button',{name:'Suivre les nouveaux événements',exact:true}).click();
    await cases.invoke('line',{text:'live-first-'+c.id});await until(async()=>await rows().count()>0,'live_first_missing');
    const first=await ids(),card=journal().getByRole('article',{name:'Événement '+first.at(-1),exact:true});
    await card.locator(':scope > details > summary').click();const text=card.getByLabel('Texte de '+first.at(-1),{exact:true});await text.focus();
    await cases.invoke('line',{text:'live-second-'+c.id});await until(async()=>await rows().count()>first.length,'live_second_missing');assert(await text.evaluate(element=>element===document.activeElement));
    await journal().getByRole('button',{name:'Mettre en pause',exact:true}).click();const paused=await ids();await cases.invoke('line',{text:'live-while-paused-'+c.id});await delay(2200);assert.deepEqual(await ids(),paused);
    await journal().getByRole('button',{name:'Reprendre le suivi',exact:true}).click();await until(async()=>await rows().count()>paused.length,'live_resume_missing');
    const beforeDisconnect=await ids();
    try {
      await c.context.setOffline(true);await journal().getByRole('alert').waitFor({timeout:10000});
      assert.equal(await rows().count(),0);assert(await journal().getByRole('button',{name:'Reprendre le suivi',exact:true}).isEnabled());await capture('follow-disconnected');
    } finally {await c.context.setOffline(false);}
    const disconnectedCall=await cases.invoke('line',{text:'live-after-disconnection-'+c.id});
    await journal().getByRole('button',{name:'Reprendre le suivi',exact:true}).click();await until(async()=>await rows().count()>beforeDisconnect.length,'follow_did_not_resume_after_disconnection');
    assert.equal(new Set(await ids()).size,(await ids()).length);assert(await ids().then(current=>beforeDisconnect.every(id=>current.includes(id))));
    c.observations.push({scenario:'actual-browser-disconnection-and-resume',before:beforeDisconnect,after:await ids(),new_invocation:disconnectedCall.id,intercepted_responses:0});
    await card.locator(':scope > details > summary').click();await text.focus();await c.page.keyboard.press('Tab');await c.page.keyboard.press('Shift+Tab');assert(await text.evaluate(element=>element===document.activeElement));await cases.invoke('lines',{count:220});
    await journal().getByText(/Suivi mis en pause pour conserver l’entrée qui a le focus/).waitFor({timeout:15000});assert(await text.evaluate(element=>element===document.activeElement));assert(await rows().count()<=200);
    await capture('follow-protects-focus-notice',c.page,journal().getByText(/Suivi mis en pause pour conserver l’entrée qui a le focus/));await capture('follow-protects-focus',c.page,text);const resume=journal().getByRole('button',{name:'Reprendre le suivi',exact:true});await resume.focus();await c.page.keyboard.press('Enter');
    await until(async()=>await rows().count()===200,'live_window_not_capped');const retained=await ids();assert.equal(new Set(retained).size,200);
    await journal().getByText(/Les 200 dernières entrées/).waitFor();await capture('follow-window');
    const old=await c.value('/api/services/'+cases.service.id+'/log-policy'),pause=journal().getByRole('button',{name:'Mettre en pause',exact:true});await pause.focus();
    const refused=c.track(c.page.waitForResponse(r=>new URL(r.url()).pathname===path() && r.status()===410));
    await cases.policy(cases.service,old.retention_minutes-1);const invalid=await done(refused);assert.equal((await invalid.json()).error,'log_policy_changed');
    await journal().getByRole('alert').waitFor();assert.equal(await rows().count(),0);assert(await journal().getByRole('button',{name:'Reprendre le suivi',exact:true}).isDisabled());
    assert(await journal().getByRole('heading',{name:'Journaux',exact:true}).evaluate(element=>element===document.activeElement));
    c.observations.push({scenario:'follow-window-and-invalidation',limit:200,ids:retained,policy_http_status:410,focus_heading:true});
  });
  await c.check('UI 08 — Téléchargements réels JSONL/texte et limites',async()=>{
    const short=await cases.invoke('lines',{count:1024});await navigate({source:'application',invocation:short.id});
    async function download(label) {
      const pending=c.track(c.page.waitForEvent('download',{timeout:15000}));
      const exported=c.track(c.page.waitForResponse(r=>new URL(r.url()).pathname===path()+'/export',{timeout:15000}));
      await journal().getByRole('button',{name:label,exact:true}).click();const r=await done(exported);assert.equal(r.status(),200);
      const d=await done(pending);assert.equal(await d.failure(),null);const bytes=await readFile(await d.path());assert(bytes.length<=1024**2);
      const headers=r.headers();assert.equal(Number(headers['x-log-count'])<=1000,true);assert.equal(headers['cache-control'].includes('no-store'),true);
      c.observations.push({scenario:'real-browser-download',filename:d.suggestedFilename(),bytes:bytes.length,sha256:sha(bytes),count:Number(headers['x-log-count']),partial:headers['x-log-partial'],next_offset:headers['x-log-next-offset']});
      return {bytes,headers};
    }
    const first=await download('Exporter cette période'),tail=await download('Exporter le lot suivant');
    const parse=bytes=>bytes.toString('utf8').trimEnd().split('\n').filter(Boolean).map(line=>JSON.parse(line));
    const firstRows=parse(first.bytes),tailRows=parse(tail.bytes);assert.equal(firstRows.length,1000);assert.equal(tailRows.length,24);assert.equal(new Set([...firstRows,...tailRows].map(row=>row.id)).size,1024);
    assert.equal(tail.headers['x-log-partial'],'false');assert(await journal().getByRole('button',{name:'Exporter cette période',exact:true}).isDisabled());
    await journal().getByLabel('Format de l’export',{exact:true}).selectOption('text');const text=await download('Exporter cette période');assert(text.headers['content-type'].startsWith('text/plain'));assert(text.bytes.includes(Buffer.from('ligne-')));
    for(let index=0;index<40;index++)await cases.invoke('batch',{lengths:Array(16).fill(4095)});
    await navigate({source:'application',q:'a'.repeat(200)});const large=await download('Exporter cette période'),next=await download('Exporter le lot suivant');
    const a=parse(large.bytes),b=parse(next.bytes);assert(a.length<1000 && a.length>0 && b.length>0);assert.equal(large.headers['x-log-partial'],'true');assert(large.bytes.length+Buffer.byteLength(JSON.stringify(b[0])+'\n')>1024**2);
    assert(!a.some(row=>b.some(other=>other.id===row.id)));await capture('export-batches',c.page,journal().getByRole('status').filter({hasText:/octets téléchargés/}));
    const old=await c.value('/api/services/'+cases.service.id+'/log-policy');await cases.policy(cases.service,old.retention_minutes-1);
    await response(c.page,path()+'/export',()=>journal().getByRole('button',{name:'Exporter le lot suivant',exact:true}).click(),{status:410});
    await journal().getByRole('alert').waitFor();assert.equal(await rows().count(),0);assert.equal(await journal().getByRole('navigation',{name:'Pagination des journaux',exact:true}).count(),0);
    assert(await journal().getByRole('heading',{name:'Journaux',exact:true}).evaluate(element=>element===document.activeElement));
  });
  await c.check('UI 09 — Clavier, intentions successives et texte agrandi',async()=>{
    await navigate();await c.page.getByRole('link',{name:'Journaux et conservation de tout le service',exact:true}).click();await ready();
    const retention=panel(c.page,'Conservation des journaux'),opener=retention.getByRole('button',{name:'Modifier la conservation',exact:true});
    for(let index=0;index<3;index++) {
      await until(()=>opener.isEnabled(),'retention_not_ready');await opener.focus();await c.page.keyboard.press('Enter');const dialog=c.page.getByRole('dialog',{name:'Conservation des journaux',exact:true});await dialog.waitFor();
      assert(await dialog.getByLabel('Conservation (minutes)',{exact:true}).evaluate(element=>element===document.activeElement));
      await c.page.keyboard.press('Tab');assert(await dialog.evaluate(element=>element.contains(document.activeElement)));
      const cdp=await c.context.newCDPSession(c.page);let pending,received=false;
      try {
        await cdp.send('Network.enable');await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:800,downloadThroughput:1000000,uploadThroughput:1000000});
        pending=c.track(c.page.waitForResponse(r=>new URL(r.url()).pathname==='/api/services/'+cases.service.id+'/log-policy' && r.request().method()==='GET').then(r=>{received=true;return r;}));
        const request=c.track(c.page.waitForRequest(r=>new URL(r.url()).pathname==='/api/services/'+cases.service.id+'/log-policy' && r.method()==='GET'));
        await c.page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});await done(request);
        if(index===0)assert(await retention.getByRole('heading',{name:'Conservation des journaux',exact:true}).evaluate(element=>element===document.activeElement));
        const search=journal().getByLabel('Texte à rechercher',{exact:true});assert.equal(received,false);await search.focus();assert.equal(received,false);
        const response=await done(pending);assert.equal(response.status(),200);await until(()=>opener.isEnabled(),'retention_reread_not_joined');assert(await search.evaluate(element=>element===document.activeElement));
        c.observations.push({scenario:'other-control-chosen-before-policy-response',repetition:index,http_status:200,focus_preserved:true,network_latency_ms:800});
      } finally {await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await cdp.detach();}
    }
    const pagination=journal().getByRole('navigation',{name:'Pagination des journaux',exact:true});
    const nextPage=pagination.getByRole('button',{name:'Suivante',exact:true});await nextPage.focus();
    await response(c.page,'/api/services/'+cases.service.id+'/logs',()=>c.page.keyboard.press('Enter'));
    assert(await journal().getByRole('heading',{name:'Journaux',exact:true}).evaluate(element=>element===document.activeElement));
    const disclosure=journal().locator('[data-log-id] article > details > summary').first();await disclosure.focus();await c.page.keyboard.press('Enter');
    assert(await disclosure.evaluate(element=>element.parentElement.open));
    const before=await journal().getByLabel('Texte à rechercher',{exact:true}).evaluate(element=>parseFloat(getComputedStyle(element).fontSize));
    const entry=await c.call('/',{anonymous:true,json:false}),policy=entry.headers['content-security-policy'];
    assert(policy?.includes("default-src 'self'") && !policy.includes("'unsafe-inline'"),'unexpected_product_style_policy');
    const enlargement=await c.page.evaluate(()=>{
      const names=['--text-small','--text-body','--text-h3','--text-h2','--text-h1'],found=[];
      for(const sheet of document.styleSheets) {
        if(!sheet.href || new URL(sheet.href).origin!==location.origin)continue;
        for(let index=0;index<sheet.cssRules.length;index++) {
          const rule=sheet.cssRules[index];
          if(rule.selectorText===':root' && names.every(name=>rule.style.getPropertyValue(name)))found.push({sheet,rule,index});
        }
      }
      if(found.length!==1)throw new Error('unique_external_typography_rule_required');
      const {sheet,rule,index}=found[0],values=names.map(name=>{
        const value=rule.style.getPropertyValue(name),priority=rule.style.getPropertyPriority(name);
        if(!/^\d+(?:\.\d+)?px$/.test(value) || Number.parseFloat(value)<=0)throw new Error('pixel_typography_token_required');
        return {name,value,priority,scaled:2*Number.parseFloat(value)+'px'};
      });
      try {for(const item of values)rule.style.setProperty(item.name,item.scaled,item.priority);}
      catch(error) {for(const item of values)rule.style.setProperty(item.name,item.value,item.priority);throw error;}
      return {href:sheet.href,index,values};
    });
    let after;
    try {
      after=await journal().getByLabel('Texte à rechercher',{exact:true}).evaluate(element=>parseFloat(getComputedStyle(element).fontSize));assert(after>=before*1.9);
      assert(await c.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await capture('text-enlarged',c.page,journal().getByLabel('Texte à rechercher',{exact:true}));
    } finally {
      await c.page.evaluate(state=>{
        const sheets=[...document.styleSheets].filter(sheet=>sheet.href===state.href);if(sheets.length!==1)throw new Error('typography_sheet_changed');
        const rule=sheets[0].cssRules[state.index];if(rule.selectorText!==':root')throw new Error('typography_rule_changed');
        for(const item of state.values)if(rule.style.getPropertyValue(item.name)!==item.scaled)throw new Error('typography_token_changed');
        for(const item of state.values)rule.style.setProperty(item.name,item.value,item.priority);
      },enlargement);
    }
    c.observations.push({scenario:'served-csp-and-reversible-cssom',policy_sha256:sha(policy),tokens:enlargement.values,restored:true});
    c.observations.push({scenario:'repeated-keyboard-focus',repetitions:3,other_control_respected:true,text_font_before:before,text_font_after:after,measurement:'product font tokens doubled, not browser zoom'});
  });
  await c.check('UI 10 — Desktop, tablette, mobile et défilement local',async()=>{
    const old=await c.value(endpoint(cases.fn)),name='journal-long-function-'+('a'.repeat(41));assert.equal(name.length,63);
    await c.value(endpoint(cases.fn),{method:'PUT',headers:match(old.updated_at),body:{name,config:old.config}});
    for(const [width,height]of [[1440,1000],[1024,768],[390,844]]) {
      await c.page.setViewportSize({width,height});await navigate({source:'application',invocation:cases.calls.bytes});
      const item=(await cases.application(cases.fn,cases.calls.bytes))[0],card=await details(item.id),pre=card.getByLabel('Texte de '+item.id,{exact:true});
      await pre.scrollIntoViewIfNeeded();await pre.focus();const initial=await pre.evaluate(element=>({left:element.scrollLeft,width:element.clientWidth,scroll:element.scrollWidth}));assert(initial.scroll>initial.width);
      await c.page.keyboard.press('ArrowRight');await until(()=>pre.evaluate(element=>element.scrollLeft>0),'local_horizontal_keyboard_scroll_missing');
      assert(await c.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await capture('long-message-'+width);
      c.observations.push({scenario:'viewport-local-scroll',width,height,global_overflow:false,before:initial,after:await pre.evaluate(element=>element.scrollLeft)});
    }
    await c.page.setViewportSize({width:1440,height:1000});
  });
  await c.check('UI 07 — Conservation, confirmation, conflit et relecture',()=>retentionPolicyCase(c,cases));
  assert.deepEqual(errors,[]);assert.equal(c.checks.length,10);c.scenariosPassed=true;
} catch(error) {c.failure=diagnosis(error);process.exitCode=1;}
finally {
  const attempt=async(phase,run)=>{try{await run();}catch(error){c.cleanupErrors.push({phase,...diagnosis(error)});process.exitCode=1;}};
  await attempt('join-native-sql-barriers',()=>joinJournalSqlBarriers(c));await attempt('join-native-control-cuts',()=>joinJournalCuts(c));await attempt('join-http-operations',()=>c.joinPending());
  await attempt('owned-resources',()=>c.close({nativeCleanup:async()=>{const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});}}));
  c.completed=c.scenariosPassed && c.cleanup && !c.cleanupErrors.length;await c.save();if(!c.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:c.completed,groups:c.completed?c.checks.length:0,cleanup:c.cleanup,report:c.report.pathname}));
