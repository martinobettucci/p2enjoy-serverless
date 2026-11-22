// @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#préconditions-et-historique
// @verifies docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_UI_CONCURRENCY.md
// @verifies docs/CODE_EDITOR_UI_CONCURRENCY.md#dix-groupes-ciblés-ordinateur-et-mobile
// @spec docs/BACKLOG.md#sls-115 | docs/CODE_EDITOR_ADOPTION_FOCUS.md
// @verifies docs/CODE_EDITOR_ADOPTION_FOCUS.md#nouveau-passage-requis
// Actual HTTPS/SSO/browser actions and native read entry; no intercepted or substituted responses.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium} from 'playwright';
import {enterNamespaces} from './console-navigation.mjs';
const exec=promisify(execFile),base='https://serverless.lelabs.tech',id=randomUUID();
const image='sha256:f73efa6e4e2b944b0cbc02f207c6cda0258138df1a7718579a9b0396d02e68d0';
const out=new URL('../.local/e2e/',import.meta.url),prefix='code-editor-ui-concurrency-'+id,report=new URL(prefix+'.json',out);
const checks=[],observations=[],cleanupErrors=[],intents=[],functions=[],tokens=[],gates=[],pending=[],invocations=[],faults=[],captures={},adoptionFocus=[],adoptionFallbackFocus=[];
const sha=v=>createHash('sha256').update(v).digest('hex'),match=v=>({'If-Match':String(v)}),ep=()=>'/api/functions/'+fn.id;
const SSH=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
let credentials,browser,context,page,admin,session,namespace,service,fn,work,pkg,published,completed=false,scenariosPassed=false,failure=null;
function diagnosis(error){return {type:error.name,message_sha256:sha(String(error.message)),source_line:String(error.stack??'').match(/code-editor-ui-concurrency\.mjs:(\d+)/)?.[1]};}
async function save(){const p=new URL(report.href+'.pending');await writeFile(p,JSON.stringify({campaign:id,target:base,completed,checks,observations,cleanup_errors:cleanupErrors,intents,namespace_id:namespace?.id,service_id:service?.id,function_ids:functions.map(v=>v.id),token_ids:tokens.map(v=>v.id),invocations,captures,faults,gate_sessions:gates.map(({unit,events,restored})=>({unit,events,restored})),adoption_focus:adoptionFocus,adoption_fallback_focus:adoptionFallbackFocus,skipped:0,failure},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}catch(error){checks.push({name,status:'failed',...diagnosis(error)});throw error;}finally{await save();}}
async function privateInput(){const input=createInterface({input:process.stdin});try{return JSON.parse(await new Promise((resolve,reject)=>{input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));}));}finally{input.close();}}
async function api(path,{method='GET',body,bytes,status=200,headers={}}={}){const r=await admin.fetch(base+path,{method,data:bytes??body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token,...(bytes?{'Content-Type':'application/zip'}:{}),...headers},timeout:120000});assert([status].flat().includes(r.status()),`${method} ${path}: ${r.status()}`);return {data:await r.json(),status:r.status(),headers:r.headers()};}
async function value(path,options){return(await api(path,options)).data;}
async function create(kind,path,body){for(let offset=0;;offset+=100){const rows=(await value(path+'?limit=100&offset='+offset)).items;assert(!rows.some(v=>v.name===body.name));if(rows.length<100)break;}const intent={kind,path,name:body.name,absent_before_post:true};intents.push(intent);await save();const r=await admin.post(base+path,{data:body,headers:{Origin:base,'X-CSRF-Token':session.csrf_token}});intent.response_status=r.status();await save();assert.equal(r.status(),201);const row=await r.json();intent.id=row.id;await save();return row;}
async function reconcile(){for(const intent of intents){if(!intent.id&&!(intent.response_status>=400&&intent.response_status<500)){for(let offset=0;;offset+=100){const rows=(await value(intent.path+'?limit=100&offset='+offset)).items,found=rows.filter(v=>v.name===intent.name);assert(found.length<=1);if(found.length){intent.id=found[0].id;break;}if(rows.length<100)break;}}if(intent.id){if(intent.kind==='namespace'&&!namespace)namespace={id:intent.id};if(intent.kind==='service'&&!service)service={id:intent.id};if(intent.kind==='function'&&!functions.some(v=>v.id===intent.id))functions.push({id:intent.id});if(intent.kind==='token'&&!tokens.some(v=>v.id===intent.id))tokens.push({id:intent.id});}}await save();}
async function until(action,label='real_state_timeout',seconds=90){const end=Date.now()+seconds*1000;while(Date.now()<end){const r=await action();if(r)return r;await new Promise(resolve=>setTimeout(resolve,100));}throw new Error(label);}
async function remote(mode,unit){return JSON.parse((await exec('ssh',[...SSH,'python3','-B','/srv/p2enjoy-serverless/e2e/code-editor-read-operator.py',mode,fn.id,namespace.id,unit],{timeout:75000,maxBuffer:2*1024**2})).stdout);}
async function inspect(){return JSON.parse((await exec('python3',['-B','e2e/code-editor-read-inspect.py',namespace.id],{timeout:75000,maxBuffer:4*1024**2})).stdout);}
async function gate(count){
 const unit='serverless-restore-editor-read-'+randomUUID().replaceAll('-',''),events=[],stderrHash=createHash('sha256');
 let child,lines,terminal=null,signal=null,closed=false,protocolError=null,stderrBytes=0,stdoutBytes=0;
 let resolveEnded;const ended=new Promise(resolve=>{resolveEnded=resolve;});
 const streamFailure=error=>{if(protocolError)return;protocolError=error;child?.stdin.end();};
 async function awaitClosed(milliseconds){let timer;try{return await Promise.race([ended.then(()=>true),new Promise(resolve=>{timer=setTimeout(()=>resolve(false),milliseconds);})]);}finally{clearTimeout(timer);}}
 async function closeTransport(){
  child?.stdin.end();
  if(!closed){child?.kill('SIGTERM');if(!await awaitClosed(2000)){child?.kill('SIGKILL');assert(await awaitClosed(5000),'local_SSH_not_joined');}}
 }
 const v={unit,events,restored:false,async wait(event,seconds=45){return until(async()=>{if(protocolError)throw protocolError;const found=events.find(x=>x.event===event);if(found)return found;assert(!closed,'native_helper_terminated');},'native_'+event+'_missing',seconds);},
  async join(){
   if(!await awaitClosed(75000)){
    try{const receipt=await remote('recover',unit);if(receipt.completed)this.restored=true;}
    finally{await closeTransport();}
    throw new Error('native_helper_join_timeout');
   }
   return {exit_code:terminal,signal,stderr_bytes:stderrBytes,stderr_sha256:stderrHash.copy().digest('hex'),protocol_error:protocolError?diagnosis(protocolError):null};
  },
  async release(eof=false){
   if(eof)child.stdin.end();else child.stdin.end('release\n');
   const result=await this.join();if(protocolError)throw protocolError;assert.equal(result.exit_code,0);
   const receipt=events.find(x=>x.event==='restored');assert(receipt?.completed);
   const finished=events.find(x=>x.event==='guard-finished');assert(finished);this.restored=true;
   return {result,receipt,states:finished.states};
  },
  async recover(){
   let receipt,result,error;child?.stdin.end();
   try{receipt=await remote('recover',unit);assert(receipt.completed);this.restored=true;}
   catch(e){error=e;}
   finally{try{result=await this.join();}finally{await closeTransport();}}
   if(error)throw error;return {receipt,result};
  },
 };
 gates.push(v);observations.push({gate_intent:{unit,count}});await save();
 child=spawn('ssh',[...SSH,'python3','-B','/srv/p2enjoy-serverless/e2e/code-editor-read-operator.py','hold',fn.id,namespace.id,image,String(count),unit],{stdio:['pipe','pipe','pipe']});
 child.stderr.on('data',chunk=>{stderrBytes+=chunk.length;stderrHash.update(chunk);if(stderrBytes>262144){streamFailure(new Error('native_stderr_limit'));child.stderr.pause();}});
 child.stdout.on('data',chunk=>{stdoutBytes+=chunk.length;if(stdoutBytes>2*1024**2){streamFailure(new Error('native_stdout_limit'));child.stdout.pause();lines?.close();}});
 child.stdout.on('error',streamFailure);child.stderr.on('error',streamFailure);child.stdin.on('error',streamFailure);
 lines=createInterface({input:child.stdout});lines.on('line',line=>{if(protocolError)return;try{assert(line.length<=2*1024**2);assert(events.length<1000);events.push(JSON.parse(line));}catch(error){streamFailure(error);}});lines.on('error',streamFailure);
 child.once('close',(code,s)=>{terminal=code;signal=s;closed=true;lines.close();resolveEnded();});child.once('error',streamFailure);
 const prepared=await v.wait('prepared',15);assert.equal(prepared.unit,unit);await v.wait('armed',15);return v;
}

const ed=()=>page.locator('.editor-view'),tree=()=>page.locator('.editor-layout>.panel').first(),content=()=>page.locator('.editor-file');
const comparison=()=>ed().locator('section.panel').filter({has:page.getByRole('heading',{name:'Comparer le brouillon enregistré',exact:true})});
const workPath='working-note.txt',gatePath='reader-gate.txt',search=()=>tree().getByLabel('Rechercher un chemin',{exact:true});
async function frames(){await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));}
async function ready(){await ed().getByRole('button',{name:'Actualiser le contexte',exact:true}).waitFor();await until(async()=>await ed().getByRole('button',{name:'Actualiser le contexte',exact:true}).isEnabled()&&!await tree().getByText('Lecture des fichiers…',{exact:true}).count());}
async function snap(name,target=comparison()){await target.scrollIntoViewIfNeeded();await frames();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));const path=new URL(prefix+'-'+name+'.jpg',out),raw=await page.screenshot({path:path.pathname,type:'jpeg',quality:85,fullPage:false});captures[path.pathname.split('/').at(-1)]={sha256:sha(raw),viewport:page.viewportSize(),full_page:false};}
function watch(method,path,parameters={}){let answered=false;const promise=page.waitForResponse(r=>{const u=new URL(r.url());return r.request().method()===method&&u.pathname===path&&Object.entries(parameters).every(([k,v])=>u.searchParams.get(k)===v);},{timeout:120000}).then(async r=>{answered=true;return {status:r.status(),data:await r.json(),headers:r.headers(),url:r.url()};},error=>({error}));pending.push(promise);return {promise,get answered(){return answered;}};}
async function response(w,status=200){const r=await w.promise;if(r.error)throw r.error;assert.equal(r.status,status);observations.push({http:{method:new URL(r.url).pathname.endsWith('/diff')?'GET':null,url:r.url,status:r.status,headers:{retry_after:r.headers['retry-after']??null}}});return r;}
async function keyboard(button){await button.focus();await button.press('Enter');}
async function uiConfirm(label,method,path,status=200){const scope=ed().locator('.confirmation').filter({has:page.getByRole('button',{name:label,exact:true})});await keyboard(scope.getByRole('button',{name:label,exact:true}).first());const w=method?watch(method,path):null;await keyboard(scope.locator('.confirm').getByRole('button',{name:label,exact:true}));if(w)return response(w,status);}
async function openEditor(){await enterNamespaces(page,base);await page.getByRole('link',{name:namespace.name,exact:true}).click();await page.getByRole('link',{name:service.name,exact:true}).click();await page.getByRole('link',{name:fn.name,exact:true}).click();await page.getByRole('navigation',{name:'Fonction',exact:true}).getByRole('link',{name:'Éditeur',exact:true}).click();await ready();}
async function resetDraft(width,{many=false}={}){if(await ed().getByText('Saisies non enregistrées',{exact:true}).count()){await keyboard(content().getByRole('button',{name:'Terminer l’édition',exact:true}));const dialog=page.getByRole('dialog',{name:'Modifications non enregistrées',exact:true});await dialog.waitFor();await keyboard(dialog.getByRole('button',{name:'Continuer sans enregistrer',exact:true}));await dialog.waitFor({state:'hidden'});}await page.setViewportSize({width,height:width===390?844:1000});const prior=await value(ep()+'/code-draft');if(prior.draft)await value(ep()+'/code-draft',{method:'DELETE',headers:match(prior.draft.version)});let d=await value(ep()+'/code-draft',{method:'POST',status:201,headers:match((await value(ep())).updated_at),body:{base_code_hash:published.code_hash}});const patches=many?[...Array.from({length:6},(_,i)=>['a-diff-'+i+'.txt','Diff '+i]),[gatePath,'Comparaison réelle '+width+'\n']]:[[gatePath,'Comparaison réelle '+width+'\n'],[workPath,'Travail enregistré\n']];for(const [path,text]of patches)d=await value(ep()+'/code-draft',{method:'PUT',headers:match(d.draft.version),body:{file:{action:'write',path,text}}});await openEditor();assert.equal(new URL(page.url()).searchParams.get('view'),null);return d;}
async function patch(path,text,action='write'){const d=(await value(ep()+'/code-draft')).draft;return value(ep()+'/code-draft',{method:'PUT',headers:match(d.version),body:{file:{action,path,...(action==='write'?{text}:{})}}});}
async function chooseWork({editFile=true}={}){await search().fill(workPath);await tree().getByRole('button',{name:'Rechercher',exact:true}).click();const w=watch('GET',ep()+'/code-draft/file',{path:workPath});await tree().locator('.editor-files button').filter({has:page.getByText(workPath,{exact:true})}).click();await response(w);await content().getByRole('heading',{name:workPath,exact:true}).waitFor();if(editFile)await content().getByRole('button',{name:'Modifier le fichier',exact:true}).click();return content().getByLabel(editFile?'Code en cours de saisie':'Code enregistré en lecture',{exact:true});}
async function list(){const w=watch('GET',ep()+'/code-draft/diff',{offset:'0',limit:'5'});await keyboard(comparison().getByRole('button',{name:/^(Voir le diff avec la cible|Réessayer la comparaison)$/}));await response(w);await comparison().locator('.editor-diff-list').waitFor();}
async function detailGate({offset='0'}={}){const draftBefore=(await value(ep()+'/code-draft')).draft;const g=await gate(1),w=watch('GET',ep()+'/code-draft/diff',{path:gatePath,offset});await keyboard(comparison().getByRole('button',{name:gatePath+' · Modifié',exact:true}));const held=await g.wait('held');assert.equal(held.readers.length,1);assert(!w.answered,'detail_already_answered_before_hold');await comparison().getByText('Lecture de la comparaison…',{exact:true}).waitFor();const start=performance.now(),h=await admin.get(base+'/healthz');assert.equal(h.status(),200);assert(performance.now()-start<5000);observations.push({held_detail:{unit:g.unit,viewport:page.viewportSize(),offset,path:gatePath,readers:held.readers,health_ms:performance.now()-start,response_absent:true,draft_id:draftBefore.id,draft_version:draftBefore.version}});return {g,w,draftBefore};}
async function releaseDetail(held){
 const restored=await held.g.release();observations.push({gate_restored:{unit:held.g.unit,...restored}});
 const result=await response(held.w),data=result.data;
 observations.push({returned_snapshot:{unit:held.g.unit,url:result.url,draft_id:data.draft.id,draft_version:data.draft.version,
  before_hash:data.comparison.before?.code_hash??null,after_hash:data.comparison.after.code_hash??null,
  offset:data.diff.offset,total:data.diff.total,paths:data.diff.items.map(v=>v.path),
  detail_path:data.diff.file?.path??null,detail_sha256:data.diff.file?.diff===null?null:sha(data.diff.file?.diff??'')}});
 assert.equal(data.draft.id,held.draftBefore.id);assert.equal(data.draft.version,held.draftBefore.version);
 return result;
}
async function currentFocus(){await frames();return page.evaluate(()=>({tag:document.activeElement.tagName,id:document.activeElement.id,label:document.activeElement.getAttribute('aria-label'),connected:document.activeElement.isConnected}));}
async function captureAdoption(field,phase,width,replaceText){
 await frames();const focus=await field.evaluate(node=>({on_field:node===document.activeElement,tag:document.activeElement.tagName,
  id:document.activeElement.id,label:document.activeElement.getAttribute('aria-label'),connected:document.activeElement.isConnected}));
 observations.push({adoption_focus_measurement:{width,replace_text:replaceText,phase,...focus}});return focus;
}
async function idle(){await until(async()=>{const n=await inspect();return Object.values(n.busy).every(v=>v===0)&&n.reserved_bytes===0;},'native_not_idle');}
async function invoke(){const r=await admin.get(base+'/invoke/'+fn.id,{headers:{'X-Serverless-Token':tokens[0].token},timeout:60000});assert.equal(r.status(),200);const d=await r.json();assert.equal(d.marker,'editor-reader-lifecycle');assert.equal(d.bytes,pkg.files[gatePath].bytes);assert.equal(d.sha256,pkg.files[gatePath].sha256);assert.equal(r.headers()['x-serverless-code-hash'],published.code_hash);invocations.push({id:r.headers()['x-serverless-request-id'],function_id:fn.id,code_hash:published.code_hash});await idle();}
async function purge(row){const r=await admin.get(base+'/api/functions/'+row.id);if(r.status()===200)await value('/api/functions/'+row.id,{method:'DELETE'});else assert.equal(r.status(),404);await until(async()=>!(await value('/api/archives/'+row.id)).storage_operation,'archive_pending');const a=await value('/api/archives/'+row.id);if(!a.purged_at){const op=await value('/api/archives/'+row.id+'/purge',{method:'POST',status:[200,202],headers:match(a.updated_at),body:{operation_id:randomUUID(),confirm_name:a.name}});await until(async()=>{const s=await value('/api/storage-operations/'+op.id);assert.notEqual(s.state,'aborted');return s.state==='completed';},'purge_pending');}assert((await value('/api/archives/'+row.id)).purged_at);}

async function main(){await mkdir(out,{recursive:true,mode:0o700});await save();credentials=await privateInput();assert(credentials.username&&credentials.password);browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1440,height:1000}});page=await context.newPage();page.on('pageerror',error=>faults.push(diagnosis(error)));admin=context.request;
 try{
  await check('Accueil et SSO administrateur réel',async()=>{await page.goto(base);await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();await page.waitForURL('https://oauth.lelabs.tech/**');await page.locator('input[name=username]').fill(credentials.username);await page.locator('input[type=password]').fill(credentials.password);await page.locator('input[type=submit],button[type=submit]').first().click();credentials=null;await page.waitForURL(base+'/**',{timeout:90000});await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();session=await(await admin.get(base+'/api/session')).json();assert(session.authenticated);});
  await check('Publication originale, promotion et invocation Docker avant les lectures',async()=>{work=await mkdtemp(new URL(prefix+'-',out).pathname);pkg=JSON.parse((await exec('python3',['-B','e2e/code-editor-read-package.py',work+'/source.zip'])).stdout);namespace=await create('namespace','/api/namespaces',{name:'code-editor-read-concurrency-'+id.slice(0,8),description:id});service=await create('service','/api/namespaces/'+namespace.id+'/services',{name:'editor-reader-lifecycle',description:id});fn=await create('function','/api/services/'+service.id+'/functions',{name:'editor-reader-lifecycle-'+id.slice(0,8),config:{handler:'editor-reader-lifecycle.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,max_instances:1}});functions.push(fn);const c=await value(ep()+'/code-deployments',{method:'POST',status:201,headers:match(fn.updated_at),body:{deployment_id:randomUUID(),handler:'editor-reader-lifecycle.cjs.handler'}});published=await value('/api/deployments/'+c.id+'/artifact',{method:'PUT',bytes:await readFile(work+'/source.zip')});assert.equal(published.state,'published');await value(ep()+'/versions/'+published.code_hash+'/promote',{method:'POST',headers:match((await value(ep())).updated_at)});tokens.push(await create('token','/api/services/'+service.id+'/tokens',{name:'editor-ui-concurrency-read-'+id.slice(0,8),rights:['read'],function_ids:[fn.id]}));await invoke();});
  await check('Sauvegarde UI pendant détail retenu : réponse ancienne ignorée',async()=>{for(const width of [1440,390]){await resetDraft(width);const field=await chooseWork(),text='Sauvegarde UI '+width;await field.fill(text);await list();const held=await detailGate();try{const w=watch('PUT',ep()+'/code-draft');await keyboard(content().getByRole('button',{name:'Enregistrer le fichier',exact:true}));await response(w);await ed().getByText('Brouillon enregistré.',{exact:true}).waitFor();assert.equal((await value(ep()+'/code-draft/file?path='+workPath)).file.text,text);const focus=await currentFocus();await releaseDetail(held);await frames();assert.equal(await comparison().locator('.editor-diff-list').count(),0);assert.equal(await comparison().getByRole('heading',{name:gatePath,exact:true}).count(),0);assert.deepEqual(await currentFocus(),focus);assert.equal(await field.inputValue(),text);await snap('saved-'+width,content());}finally{if(!held.g.restored)observations.push({recovery:await held.g.recover()});}}await invoke();});
  await check('Changement de surface pendant détail retenu',async()=>{for(const width of [1440,390]){await resetDraft(width);await list();const held=await detailGate();try{await keyboard(ed().getByRole('button',{name:'Lire le code publié',exact:true}));await ready();assert.equal(new URL(page.url()).searchParams.get('view'),'source');await search().focus();const before=await currentFocus();await releaseDetail(held);await frames();assert.equal(new URL(page.url()).searchParams.get('view'),'source');assert.equal(await comparison().locator('.editor-diff-list').count(),0);assert.deepEqual(await currentFocus(),before);await snap('surface-'+width,tree());}finally{if(!held.g.restored)observations.push({recovery:await held.g.recover()});}}await invoke();});
  await check('Adoptions locales garder/remplacer pendant détail retenu, sans PUT',async()=>{for(const width of [1440,390])for(const replaceText of [false,true]){await resetDraft(width);const field=await chooseWork(),local='Texte local '+width,remoteText='Texte serveur '+width;await field.fill(local);await patch(workPath,remoteText);let w=watch('PUT',ep()+'/code-draft');await keyboard(content().getByRole('button',{name:'Enregistrer le fichier',exact:true}));await response(w,409);await ed().getByRole('heading',{name:'Relecture nécessaire',exact:true}).waitFor();await keyboard(ed().getByRole('button',{name:'Relire le brouillon serveur',exact:true}));await ed().getByRole('button',{name:'Adopter cette version en gardant ma saisie',exact:true}).first().waitFor();await list();const before=(await value(ep()+'/code-draft')).draft,held=await detailGate();let puts=0;const listener=r=>{if(r.method()==='PUT'&&new URL(r.url()).pathname===ep()+'/code-draft')puts++;};page.on('request',listener);try{await uiConfirm(replaceText?'Utiliser le texte du serveur':'Adopter cette version en gardant ma saisie');await ed().getByText('Version du serveur adoptée explicitement.',{exact:true}).waitFor();const immediate=await captureAdoption(field,'before_release',width,replaceText);assert.equal(await field.inputValue(),replaceText?remoteText:local);await snap('adoption-before-'+width+'-'+replaceText,content());await releaseDetail(held);const after=await captureAdoption(field,'after_release',width,replaceText);adoptionFocus.push({width,replace_text:replaceText,before_release:immediate,after_release:after});assert.equal(await comparison().locator('.editor-diff-list').count(),0);assert.equal(await field.inputValue(),replaceText?remoteText:local);const current=(await value(ep()+'/code-draft')).draft;assert.equal(current.version,before.version);assert.equal(current.updated_at,before.updated_at);assert.equal((await value(ep()+'/code-draft/file?path='+workPath)).file.text,remoteText);assert.equal(puts,0);await snap('adoption-after-'+width+'-'+replaceText,content());}finally{page.off('request',listener);if(!held.g.restored)observations.push({recovery:await held.g.recover()});}}await invoke();});
  await check('Abandon UI pendant détail retenu : brouillon absent et réponse ancienne ignorée',async()=>{for(const width of [1440,390]){await resetDraft(width);await list();const held=await detailGate();try{await uiConfirm('Abandonner mon brouillon','DELETE',ep()+'/code-draft');await ed().getByText('Brouillon abandonné.',{exact:true}).waitFor();await ready();assert.equal((await value(ep()+'/code-draft')).draft,null);await search().focus();const focus=await currentFocus();await releaseDetail(held);await frames();assert.equal(await ed().getByRole('heading',{name:'Comparer le brouillon enregistré',exact:true}).count(),0);assert.equal(new URL(page.url()).searchParams.get('view'),'source');assert.deepEqual(await currentFocus(),focus);await snap('discarded-'+width,tree());}finally{if(!held.g.restored)observations.push({recovery:await held.g.recover()});}}await invoke();});
  await check('Focus volontaire conservé pendant la lecture réelle du détail',async()=>{for(const width of [1440,390]){await resetDraft(width);await list();const held=await detailGate();try{await search().fill('choix personnel '+width);await search().focus();await snap('loading-choice-'+width,comparison());await releaseDetail(held);await comparison().getByRole('heading',{name:gatePath,exact:true}).waitFor();await frames();assert(await search().evaluate(node=>node===document.activeElement));assert.equal(await search().inputValue(),'choix personnel '+width);await snap('choice-kept-'+width,search());}finally{if(!held.g.restored)observations.push({recovery:await held.g.recover()});}}await invoke();});
  await check('Recalage détaillé5+2 réel, origine du focus transmise au second GET',async()=>{for(const width of [1440,390])for(const elsewhere of [false,true]){await resetDraft(width,{many:true});await list();assert.equal(await comparison().locator('.editor-diff-list>li').count(),5);const second=watch('GET',ep()+'/code-draft/diff',{offset:'5'});await keyboard(comparison().getByRole('navigation',{name:'Pagination du diff',exact:true}).getByRole('button',{name:'Suivante',exact:true}));await response(second);await comparison().getByText('Page 2 sur 2',{exact:true}).waitFor();const paths=await comparison().locator('.editor-diff-list .mono').allTextContents();assert.deepEqual(paths,['a-diff-5.txt',gatePath]);for(let i=0;i<6;i++)await patch('a-diff-'+i+'.txt',null,'revert');const held=await detailGate({offset:'5'}),clamped=watch('GET',ep()+'/code-draft/diff',{path:gatePath,offset:'0'});try{if(elsewhere){await search().fill('focus conservé au recalage');await search().focus();}await snap('clamp-loading-'+width+'-'+elsewhere,comparison());const first=await releaseDetail(held);assert.equal(first.data.diff.total,1);assert.equal(first.data.diff.offset,5);const last=await response(clamped);assert.equal(last.data.diff.offset,0);assert.equal(last.data.diff.total,1);const h3=comparison().getByRole('heading',{name:gatePath,exact:true});await h3.waitFor();await frames();assert.equal(await comparison().getByRole('navigation',{name:'Pagination du diff',exact:true}).getByText('Page 1 sur 1',{exact:true}).count(),1);assert(await(elsewhere?search():h3).evaluate(node=>node===document.activeElement));await snap('clamp-final-'+width+'-'+elsewhere,elsewhere?search():h3);observations.push({clamp:{width,elsewhere,first_url:first.url,second_url:last.url,total:1,focused_expected:true}});}finally{if(!held.g.restored)observations.push({recovery:await held.g.recover()});}}await invoke();});
  await check('Vrais refus404/429 du détail, repli H2 et nouvelle comparaison réussie',async()=>{for(const width of [1440,390]){await resetDraft(width);await list();await patch(workPath,null,'revert');let w=watch('GET',ep()+'/code-draft/diff',{path:workPath});await keyboard(comparison().getByRole('button',{name:workPath+' · Ajouté',exact:true}));await response(w,404);await comparison().getByRole('alert').waitFor();await frames();assert(await comparison().getByRole('heading',{name:'Comparer le brouillon enregistré',exact:true}).evaluate(node=>node===document.activeElement));await snap('detail-404-'+width);await list();const g=await gate(4),reads=[];try{for(let i=0;i<4;i++){const p=api(ep()+'/code-sources/file?path='+gatePath).then(result=>({result}),error=>({error}));pending.push(p);reads.push(p);}const held=await g.wait('held');observations.push({held_four_readers:{viewport:page.viewportSize(),...held}});await save();assert.equal(held.readers.length,4);w=watch('GET',ep()+'/code-draft/diff',{path:gatePath});await keyboard(comparison().getByRole('button',{name:gatePath+' · Modifié',exact:true}));const rejected=await response(w,429);assert.equal(rejected.headers['retry-after'],'2');await comparison().getByRole('alert').waitFor();await frames();assert(await comparison().getByRole('heading',{name:'Comparer le brouillon enregistré',exact:true}).evaluate(node=>node===document.activeElement));await snap('detail-429-'+width);observations.push({gate_restored:{unit:g.unit,...await g.release()}});for(const p of reads){const r=await p;if(r.error)throw r.error;assert.equal(r.result.data.file.sha256,pkg.files[gatePath].sha256);}await list();w=watch('GET',ep()+'/code-draft/diff',{path:gatePath});await keyboard(comparison().getByRole('button',{name:gatePath+' · Modifié',exact:true}));await response(w);await comparison().getByRole('heading',{name:gatePath,exact:true}).waitFor();await frames();assert(await comparison().getByRole('heading',{name:gatePath,exact:true}).evaluate(node=>node===document.activeElement));await snap('detail-recovered-'+width);}finally{if(!g.restored)observations.push({recovery:await g.recover()});for(const p of reads){const r=await p;if(r.error)throw r.error;}}}await invoke();});
  await check('Adoption hors saisie : titre focalisé pour fichier relu ou devenu absent',async()=>{
   for(const width of [1440,390])for(const missing of [false,true])for(const replaceText of [false,true]){
    await resetDraft(width);const field=await chooseWork({editFile:false}),displayedBefore=await field.inputValue();
    if(missing)await patch(workPath,null,'revert');else await patch(workPath,'Copie serveur hors saisie '+width);
    await keyboard(ed().getByRole('button',{name:'Actualiser le contexte',exact:true}));await ready();
    await ed().getByRole('heading',{name:'Relecture nécessaire',exact:true}).waitFor();
    await keyboard(ed().getByRole('button',{name:'Relire le brouillon serveur',exact:true}));
    await ed().getByRole('button',{name:'Adopter cette version en gardant ma saisie',exact:true}).first().waitFor();
    const before=(await value(ep()+'/code-draft')).draft;let puts=0;
    const listener=request=>{if(request.method()==='PUT'&&new URL(request.url()).pathname===ep()+'/code-draft')puts++;};page.on('request',listener);
    try{
     await uiConfirm(replaceText?'Utiliser le texte du serveur':'Adopter cette version en gardant ma saisie');
     await ed().getByText('Version du serveur adoptée explicitement.',{exact:true}).waitFor();await frames();
     const heading=content().getByRole('heading',{name:missing&&replaceText?'Contenu du fichier':workPath,exact:true});
     const focused=await heading.evaluate(node=>node===document.activeElement),after=(await value(ep()+'/code-draft')).draft;
     const server=await api(ep()+'/code-draft/file?path='+workPath,{status:missing?404:200});
     const readonly=content().getByLabel('Code enregistré en lecture',{exact:true}),displayed=await readonly.count()?await readonly.inputValue():null;
     const readOnly=await readonly.count()?await readonly.evaluate(node=>node.readOnly):null;
     const uiDraftVersion=await ed().locator('dt').filter({hasText:/^Enregistrement du brouillon$/}).locator('..').locator('dd').innerText();
     const observed={width,missing,replace_text:replaceText,focused_heading:focused,puts,read_only:readOnly,ui_draft_version:uiDraftVersion,
      before_version:before.version,after_version:after.version,displayed_before_sha256:sha(displayedBefore),
      displayed_after_sha256:displayed===null?null:sha(displayed),server_status:server.status,
      server_text_sha256:missing?null:sha(server.data.file.text),path_after:new URL(page.url()).searchParams.get('file')};
     adoptionFallbackFocus.push(observed);await save();assert(focused,'adoption_did_not_restore_focus_to_file_heading');
     assert.equal(puts,0);assert.equal(after.version,before.version);assert.equal(after.updated_at,before.updated_at);
     assert.equal(uiDraftVersion,String(before.version));
     if(!missing){assert.equal(server.data.file.text,'Copie serveur hors saisie '+width);assert.equal(server.data.file.sha256,sha('Copie serveur hors saisie '+width));}
     assert.equal(displayed,replaceText?(missing?null:server.data.file.text):displayedBefore);
     assert.equal(observed.path_after,missing&&replaceText?null:workPath);
     assert.equal(readOnly,missing&&replaceText?null:true);
     assert.equal((await value(ep())).active_revision_id,published.revision_id);
     await snap('adoption-fallback-'+width+'-'+missing+'-'+replaceText,heading);
    }finally{page.off('request',listener);}
   }
   await invoke();
  });
  await check('Consolidation du focus sur le textarea après les quatre adoptions',async()=>{assert.equal(adoptionFocus.length,4);assert.equal(gates.length,18);assert.equal(gates.reduce((n,g)=>n+(g.events.find(v=>v.event==='held')?.readers.length??0),0),24);assert(gates.every(g=>g.restored));assert.equal(invocations.length,9);assert.equal(new Set(invocations.map(v=>v.id)).size,9);assert.equal(adoptionFallbackFocus.length,8);assert(adoptionFallbackFocus.every(v=>v.focused_heading));assert.equal(Object.keys(captures).length,40);assert.deepEqual(faults,[]);observations.push({adoption_focus_summary:{count:4,correct:adoptionFocus.every(v=>v.before_release.on_field&&v.after_release.on_field)}});assert(adoptionFocus.every(v=>v.before_release.on_field&&v.after_release.on_field),'adoption_did_not_restore_focus_to_current_textarea');});
  scenariosPassed=true;
 }catch(error){failure=diagnosis(error);}
 finally{credentials=null;
  for(const g of gates)if(!g.restored)try{observations.push({terminal_recovery:await g.recover()});}catch(error){cleanupErrors.push({guard:g.unit,...diagnosis(error)});}
  await Promise.allSettled(pending);
  if(admin&&session&&gates.every(v=>v.restored)){
   let purged=true,revoked=true;
   try{await reconcile();}catch(error){purged=false;revoked=false;cleanupErrors.push({phase:'reconcile',...diagnosis(error)});}
   for(const row of functions)try{await purge(row);}catch(error){purged=false;cleanupErrors.push({phase:'purge',...diagnosis(error)});}
   try{if(service){const rows=(await value('/api/services/'+service.id+'/tokens?limit=100')).items;
    assert.equal(rows.length,tokens.length);assert(rows.every(row=>tokens.some(t=>t.id===row.id)));
    for(const row of rows)if(!row.revoked_at)await value('/api/tokens/'+row.id+'/revoke',{method:'POST'});
    assert((await value('/api/services/'+service.id+'/tokens?limit=100')).items.every(v=>v.revoked_at));
   }}catch(error){revoked=false;cleanupErrors.push({phase:'token-revoke',...diagnosis(error)});}
   try{if(namespace){const native=await inspect();observations.push({native_final:native});await save();
    assert.equal(native.drafts.length,0);assert(native.functions.length===functions.length&&native.functions.every(v=>v.deleted_at&&v.purged_at));
    assert(native.revisions.every(v=>!v.stored_bytes&&!v.artifact_directory_exists));assert(native.tokens.every(v=>v.revoked_at));
    assert(Object.values(native.busy).every(v=>v===0));for(const i of invocations){const row=native.invocations.find(v=>v.id===i.id);
     assert(row&&row.state==='succeeded'&&row.handler_started===1&&row.http_status===200);}
   }}catch(error){cleanupErrors.push({phase:'native-cleanup',...diagnosis(error)});}
   if(purged&&revoked)try{if(service)await value('/api/services/'+service.id,{method:'DELETE'});if(namespace)await value('/api/namespaces/'+namespace.id,{method:'DELETE'});}catch(error){cleanupErrors.push({phase:'parents',...diagnosis(error)});}
   try{await value('/auth/logout',{method:'POST'});}catch(error){cleanupErrors.push({phase:'logout',...diagnosis(error)});}
  }else cleanupErrors.push({phase:'guards-before-application-cleanup',type:'NativeRestorationMissing'});

  tokens.forEach(v=>{delete v.token;});for(const [phase,close] of [['context',()=>context?.close()],['browser',()=>browser?.close()],['work',()=>work?rm(work,{recursive:true,force:true}):null]])try{await close();}catch(error){cleanupErrors.push({phase,...diagnosis(error)});}completed=scenariosPassed&&!failure&&!cleanupErrors.length&&!faults.length;await save();
 }
 assert(completed,'editor_ui_concurrency_campaign_failed');
}
await main().catch(error=>{console.error(JSON.stringify(diagnosis(error)));process.exitCode=1;});
