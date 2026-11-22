// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#console-et-manuel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
import React, {useEffect,useRef,useState} from 'react';
import {Download,Pause,Play,RefreshCw,ScrollText} from 'lucide-react';
import {api} from './api';
import {Badge,ErrorMessage,Facts,Field,Section,Success} from './ui';
import {withCatalogue,Pages} from './catalogue';
import {journalResponse} from './execution-journal-contract';

const pageSize=5;
const filters=['from','to','q','source','severity','state','invocation','instance','version','kind'];
const severityNames={trace:'Trace',debug:'Débogage',info:'Information',warning:'Avertissement',error:'Erreur',fatal:'Fatale',unknown:'Non renseigné'};
const stateNames={receiving:'Réception',queued:'En attente',admitted:'Admise',running:'En cours',succeeded:'Terminée',failed:'Échec',rejected:'Refusée',disconnected:'Client déconnecté',interrupted:'Interrompue',starting:'Démarrage',ready:'Disponible',busy:'Occupée',draining:'Arrêt en cours',cleanup_failed:'Nettoyage à reprendre',prepared:'Préparée',validating:'Validation',published:'Publiée',expired:'Expirée',preparing:'Préparation',pending:'À terminer',completed:'Achevée',aborted:'Abandonnée'};
const classes={application_response:'Réponse applicative',code:'Erreur de code',admission:'Refus d’admission',timeout:'Délai dépassé',infrastructure:'Défaillance d’infrastructure'};
const utc=value=>new Date(value*1000).toISOString();
const utcInput=value=>utc(value).slice(0,23);
const mono=value=>value ? <span className="mono">{value}</span> : 'Non attribué';

function initialQuery() {
  const now=Date.now()/1000;
  const params=new URLSearchParams(location.search),seen=new Set();let page=1;
  const period=['invocation','instance','version'].some(key=>params.get(key))?604800:3600;
  const value={from:utc(now-period),to:utc(now),q:'',source:'',severity:'',state:'',invocation:'',instance:'',version:'',kind:''};
  try {
    for(const [key,item] of params) {
      if(key==='catalogue')continue;
      if(seen.has(key) || (![...filters,'page'].includes(key)))throw new Error('Les paramètres du journal sont invalides. Ouvrez un nouveau relevé.');
      seen.add(key);
      if(key==='page') {
        if(!/^[0-9]+$/.test(item) || Number(item)<1 || Number(item)>2001)throw new Error('La page demandée est invalide.');
        page=Number(item);
      } else value[key]=item;
    }
    validate(value);return {value,page,error:null};
  } catch(error) {return {value,page,error};}
}

function validate(value) {
  const start=Date.parse(value.from),end=Date.parse(value.to);
  if(!Number.isFinite(start) || !Number.isFinite(end) || !/(?:Z|\+00:00)$/.test(value.from) || !/(?:Z|\+00:00)$/.test(value.to) || start>end || end-start>7*86400000)
    throw new Error('Choisissez une période UTC valide de sept jours au maximum.');
  if([...value.q].length>200)throw new Error('La recherche accepte au plus 200 caractères.');
}

function queryString(value,page=1) {
  const params=new URLSearchParams();
  for(const key of filters)if(value[key]!=='' && value[key]!=null)params.set(key,String(value[key]));
  if(page!==1)params.set('page',String(page));
  return params.toString();
}

function friendly(error) {
  if(error.responseInvalid)error.message='La réponse du journal est incomplète ou invalide. Ouvrez un nouveau relevé ; aucune ancienne ligne ne la remplace.';
  else if(error.status===410)error.message='Ce relevé ne peut plus être complété : conservation, purge ou politique modifiée, ou curseur expiré. Ouvrez un nouveau relevé ; aucune ligne ancienne n’est affichée.';
  else if(error.status===429)error.message='Les deux lecteurs de journaux sont occupés. Réessayez dans quelques instants.';
  else if(error.status===503 || !error.status)error.message='La lecture des journaux est indisponible. Vérifiez la connexion et réessayez ; aucun appel de fonction ne sera relancé.';
  else if(error.status===403)error.message='Vos droits ne permettent plus de consulter ces journaux.';
  else if(error.status===409)error.message='Le périmètre de lecture a changé. Ouvrez un nouveau relevé.';
  else if(error.message?.startsWith('log_'))error.message='Les filtres ou le curseur de ce relevé sont invalides. Vérifiez la période et les identifiants, puis ouvrez un nouveau relevé.';
  return error;
}

export function ExecutionJournal({functionId,serviceId}) {
  const kind=functionId?'functions':'services',subject=functionId || serviceId;
  const endpoint=`/api/${kind}/${subject}/logs`;
  const [initial]=useState(initialQuery);
  const [query,setQuery]=useState({value:initial.value,page:initial.page,epoch:0});
  const [draft,setDraft]=useState(initial.value),[filterError,setFilterError]=useState(initial.error);
  const [historyState,setHistoryState]=useState({loading:true,key:null});
  const [mode,setMode]=useState('history'),[running,setRunning]=useState(false);
  const [live,setLive]=useState({items:[],busy:false,error:null,notice:''});
  const [format,setFormat]=useState('jsonl'),[exportState,setExportState]=useState({busy:false});
  const snapshot=useRef(null),cursor=useRef(null),liveWindow=useRef({items:[],generation:null});
  const heading=useRef(null),exportRequest=useRef(null),download=useRef(null);
  const filterKey=endpoint+'?'+queryString(query.value)+'#'+query.epoch;
  const requestKey=filterKey+'&page='+query.page;
  const exportKey=filterKey+'#format='+format;
  const latestExportKey=useRef(exportKey);latestExportKey.current=exportKey;
  const historyView=historyState.key===requestKey?historyState:{key:requestKey,loading:true};

  useEffect(()=>{
    const shared=queryString(query.value,query.page),target=withCatalogue(location.pathname+'?'+shared);
    globalThis.history.replaceState(null,'',target);
  },[filterKey,query.page]);

  useEffect(()=>{
    if(mode!=='history' || filterError)return;
    let current=true;const controller=new AbortController();
    setHistoryState({key:requestKey,loading:true});
    const parameters=new URLSearchParams(queryString(query.value));
    parameters.set('limit',String(pageSize));parameters.set('offset',String((query.page-1)*pageSize));
    if(snapshot.current?.key===filterKey)parameters.set('snapshot',snapshot.current.token);
    api(endpoint+'?'+parameters,{signal:controller.signal}).then(data=>{
      if(!current)return;
      journalResponse(data);
      snapshot.current={key:filterKey,token:data.snapshot};
      setHistoryState({key:requestKey,loading:false,data,error:null});
    }).catch(error=>{if(current)setHistoryState({key:requestKey,loading:false,error:friendly(error)});});
    return()=>{current=false;controller.abort();};
  },[requestKey,mode,filterError]);

  useEffect(()=>{
    if(mode!=='live' || !running)return;
    let current=true,timer;const controller=new AbortController();
    async function poll() {
      if(!current)return;
      setLive(old=>({...old,busy:true,error:null}));
      try {
        const data=journalResponse(await api(endpoint+'?'+new URLSearchParams({cursor:cursor.current,limit:'100'}),{signal:controller.signal}));
        if(!current)return;
        if(!Number.isInteger(data.collection.prune_generation))throw new Error('Réponse de conservation invalide.');
        const changed=liveWindow.current.generation!==null && liveWindow.current.generation!==data.collection.prune_generation;
        const old=changed?[]:liveWindow.current.items.filter(item=>item.observed_at>=data.collection.available_from);
        const merged=[...new Map([...old,...data.items].map(item=>[item.id,item])).values()];
        const retained=merged.slice(-200),focused=document.activeElement?.closest('[data-log-id]')?.dataset.logId;
        const removedByPolicy=focused && !old.some(item=>item.id===focused);
        if(focused && !retained.some(item=>item.id===focused) && !removedByPolicy) {
          // Retention applies even when a different, still valid row keeps focus.
          // The unaccepted incoming batch does not advance the acknowledged cursor.
          liveWindow.current={items:old,generation:data.collection.prune_generation};
          setRunning(false);setLive({items:old,busy:false,error:null,data,loadedAt:Date.now()/1000,
            notice:'Suivi mis en pause pour conserver l’entrée qui a le focus. Les entrées expirées sont retirées. Déplacez le focus puis reprenez le suivi.'});return;
        }
        if(removedByPolicy)heading.current?.focus();
        liveWindow.current={items:retained,generation:data.collection.prune_generation};cursor.current=data.follow_cursor;
        setLive({items:retained,busy:false,error:null,data,loadedAt:Date.now()/1000,
          notice:changed || removedByPolicy?'Fenêtre actualisée après une expiration, une purge ou un changement de visibilité.':merged.length>200?'Les 200 dernières entrées de ce suivi sont conservées dans la page.':''});
        timer=setTimeout(poll,data.partial?0:2000);
      } catch(error) {if(current){
        if(document.activeElement?.closest('[data-log-id]'))heading.current?.focus();
        setRunning(false);
        const invalid=[401,403,404,409,410,422].includes(error.status) || error.responseInvalid;
        if(invalid) {
          cursor.current=null;liveWindow.current={items:[],generation:null};snapshot.current=null;
          setLive({items:[],busy:false,error:friendly(error),requiresNew:true,notice:''});
        } else setLive(previous=>({...previous,busy:false,error:friendly(error)}));
      }}
    }
    poll();return()=>{current=false;clearTimeout(timer);controller.abort();};
  },[mode,running,filterKey]);

  useEffect(()=>{
    exportRequest.current?.controller.abort();exportRequest.current=null;
    setExportState({busy:false,key:exportKey});
  },[exportKey]);
  useEffect(()=>()=>{exportRequest.current?.controller.abort();if(download.current)URL.revokeObjectURL(download.current);},[]);

  function apply(value=draft) {
    try {
      validate(value);setFilterError(null);setRunning(false);setMode('history');snapshot.current=null;
      setDraft(value);setQuery(old=>({value:{...value},page:1,epoch:old.epoch+1}));
    } catch(error) {setFilterError(error);}
  }
  function preset(seconds) {const now=Date.now()/1000;apply({...draft,from:utc(now-seconds),to:utc(now)});}
  function startFollow() {
    if(exportRequest.current || (mode==='live' && live.requiresNew))return;
    if(mode==='history') {
      if(!historyView.data || historyView.loading || historyView.error || filterError)return;
      cursor.current=historyView.data.follow_cursor;liveWindow.current={items:[],generation:historyView.data.collection.prune_generation};
      setLive({items:[],busy:true,error:null,notice:'Le suivi consulte les nouveaux événements après ce relevé, au-delà de sa période historique.'});
    }
    setMode('live');setRunning(true);
  }
  function page(value) {if(historyView.loading || exportRequest.current)return;heading.current?.focus();setQuery(old=>({...old,page:value}));}
  async function exportBatch() {
    if(exportRequest.current || mode!=='history' || !historyView.data || filterError || historyView.error || historyView.loading)return;
    const controller=new AbortController(),request={controller,key:exportKey};exportRequest.current=request;
    const offset=exportState.key===exportKey && exportState.nextOffset!=null?exportState.nextOffset:0;
    setExportState(old=>({...old,key:exportKey,busy:true,error:null}));
    try {
      const params=new URLSearchParams({snapshot:snapshot.current.token,format,offset:String(offset)});
      const response=await fetch(endpoint+'/export?'+params,{credentials:'same-origin',signal:controller.signal,headers:{Accept:format==='jsonl'?'application/x-ndjson':'text/plain'}});
      if(!response.ok) {
        const body=await response.json().catch(()=>({}));
        if(response.status===403 && ['verification','administration'].includes(body.access_requirement))location.assign('/auth/attente?reason='+body.access_requirement);
        const error=new Error(body.error || 'Export refusé.');error.status=response.status;throw error;
      }
      const blob=await response.blob(),countHeader=response.headers.get('X-Log-Count'),count=Number(countHeader);
      const partialHeader=response.headers.get('X-Log-Partial'),partial=partialHeader==='true',next=response.headers.get('X-Log-Next-Offset');
      const expected=format==='jsonl'?'application/x-ndjson':'text/plain';
      if(blob.size>1024**2 || !/^[0-9]+$/.test(countHeader || '') || count>1000 || !['true','false'].includes(partialHeader) ||
         !response.headers.get('Content-Type')?.startsWith(expected) || response.headers.get('X-Log-Snapshot')!==snapshot.current?.token ||
         (partial && (!/^[0-9]+$/.test(next || '') || Number(next)<=offset || Number(next)>10000)))
        throw new Error('Le lot exporté ne respecte pas ses limites annoncées.');
      if(exportRequest.current!==request || latestExportKey.current!==request.key)return;
      if(download.current)URL.revokeObjectURL(download.current);
      download.current=URL.createObjectURL(blob);
      const link=document.createElement('a');link.href=download.current;
      link.download=`journaux-${subject}-${offset}.${format==='jsonl'?'jsonl':'txt'}`;link.click();
      setExportState({key:exportKey,busy:false,count,bytes:blob.size,nextOffset:partial?Number(next):null,finished:!partial,error:null});
    } catch(error) {
      if(exportRequest.current===request && latestExportKey.current===request.key) {
        const failure=friendly(error);
        if([401,403,404,409,410,422].includes(error.status)) {
          snapshot.current=null;cursor.current=null;liveWindow.current={items:[],generation:null};
          setRunning(false);setMode('history');setLive({items:[],busy:false,error:null,notice:''});
          setHistoryState({key:requestKey,loading:false,error:failure});
          setExportState({key:exportKey,busy:false});
          if(download.current){URL.revokeObjectURL(download.current);download.current=null;}
          heading.current?.focus();
        } else setExportState(old=>({...old,busy:false,error:failure}));
      }
    }
    finally {if(exportRequest.current===request)exportRequest.current=null;}
  }

  const data=mode==='history'?historyView.data:live.data,error=filterError || (mode==='history'?historyView.error:live.error);
  const items=mode==='history'?(data?.items || []):[...live.items].reverse();
  const busy=mode==='history'?historyView.loading:live.busy;
  const outOfRange=mode==='history' && data && query.page>Math.max(1,Math.ceil(data.total/pageSize));
  const exportView=exportState.key===exportKey?exportState:{busy:false};
  return <Section title="Journaux" headingRef={heading} action={<button onClick={()=>apply(query.value)}><RefreshCw aria-hidden="true"/>Nouveau relevé</button>}>
    <div className="stack journal-content">
    {functionId && serviceId && <p><a href={withCatalogue(`/console/services/${serviceId}/logs`)}>Journaux et conservation de tout le service</a></p>}
    <form className="stack journal-filters" onSubmit={event=>{event.preventDefault();apply();}}>
      <div className="form-grid">
        {['from','to'].map((key,index)=><Field key={key} label={index?'Fin (UTC)':'Début (UTC)'}><input required type="datetime-local" step="0.001" value={Number.isFinite(Date.parse(draft[key]))?utcInput(Date.parse(draft[key])/1000):''}
          onChange={event=>setDraft(old=>({...old,[key]:event.target.value?event.target.value+'Z':''}))}/></Field>)}
        <Field label="Texte à rechercher" help="Recherche littérale, sensible à la casse, 200 caractères au plus."><input type="search" maxLength={400} value={draft.q} onChange={event=>setDraft(old=>({...old,q:event.target.value}))}/></Field>
      </div>
      <details className="invocation-details journal-correlation" open={['source','severity','state','invocation','instance','version','kind'].some(key=>draft[key]) || undefined}>
        <summary>Source, niveau et corrélation</summary><div className="form-grid">
        <Field label="Source"><select value={draft.source} onChange={event=>setDraft(old=>({...old,source:event.target.value}))}><option value="">Toutes les sources</option><option value="application">Application</option><option value="platform">Plateforme</option></select></Field>
        <Field label="Niveau"><select value={draft.severity} onChange={event=>setDraft(old=>({...old,severity:event.target.value}))}><option value="">Tous les niveaux</option>{Object.entries(severityNames).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></Field>
        <Field label="État"><select value={draft.state} onChange={event=>setDraft(old=>({...old,state:event.target.value}))}><option value="">Tous les états</option>{Object.entries(stateNames).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></Field>
        <Field label="Identifiant d’appel ou de requête"><input className="mono" maxLength={36} value={draft.invocation} onChange={event=>setDraft(old=>({...old,invocation:event.target.value}))}/></Field>
        <Field label="Identifiant d’instance"><input className="mono" maxLength={36} value={draft.instance} onChange={event=>setDraft(old=>({...old,instance:event.target.value}))}/></Field>
        <Field label="Hash complet du code"><input className="mono" maxLength={64} value={draft.version} onChange={event=>setDraft(old=>({...old,version:event.target.value}))}/></Field>
        <Field label="Type d’événement" help="Par exemple application.message ou invocation.completed."><input maxLength={64} value={draft.kind} onChange={event=>setDraft(old=>({...old,kind:event.target.value}))}/></Field>
        </div>
      </details>
      <div className="actions"><button className="primary" type="submit">Rechercher</button>{[[900,'15 minutes'],[3600,'1 heure'],[86400,'24 heures'],[604800,'7 jours']].map(([seconds,label])=><button key={seconds} type="button" onClick={()=>preset(seconds)}>{label}</button>)}</div>
      {JSON.stringify(draft)!==JSON.stringify(query.value) && <p role="status" className="muted">Filtres modifiés : choisissez Rechercher pour les appliquer.</p>}
    </form>
    <div className="actions journal-controls">
      {running?<button onClick={()=>setRunning(false)}><Pause aria-hidden="true"/>Mettre en pause</button>:<button disabled={Boolean(exportView.busy || filterError || (mode==='history' && (!historyView.data || historyView.loading || historyView.error)) || (mode==='live' && live.requiresNew))} onClick={startFollow}><Play aria-hidden="true"/>{mode==='live'?'Reprendre le suivi':'Suivre les nouveaux événements'}</button>}
      {mode==='live' && <button onClick={()=>apply(query.value)}>Revenir à cette période</button>}
      <Field label="Format de l’export"><select disabled={exportView.busy} value={format} onChange={event=>setFormat(event.target.value)}><option value="jsonl">JSONL</option><option value="text">Texte</option></select></Field>
      <button disabled={mode!=='history' || busy || Boolean(error) || !data || exportView.busy || exportView.finished} onClick={exportBatch}><Download aria-hidden="true"/>{exportView.busy?'Export…':exportView.nextOffset!=null?'Exporter le lot suivant':'Exporter cette période'}</button>
    </div>
    {mode==='live' && <p className="muted">{running?'Suivi actif':'Suivi en pause'} · Les sorties applicatives arrivent en fin d’invocation, pas pendant son exécution. La fenêtre de la page est limitée à 200 entrées.</p>}
    {mode==='live' && !error && <p role="status" className="muted">{live.notice} {live.loadedAt?`${live.items.length} entrées dans cette fenêtre ; dernière lecture ${utc(live.loadedAt)}.`:''} {live.busy?'Lecture des nouveaux événements en cours…':''}</p>}
    <ErrorMessage error={error}/>
    {!error && mode==='history' && busy?<div className="loading" role="status">Chargement des journaux…<span/><span/><span/></div>:null}
    {!error && data && !outOfRange && <>
      <p className="muted">{mode==='history'?`${data.total} événements dans cette période · ${utc(data.period.from)} → ${utc(data.period.to)} (UTC).`:`Suivi ouvert le ${utc(data.period.from)} ; séquences relues le ${utc(data.period.to)} (UTC).`} Conservation : {data.collection.retention_minutes} min.</p>
      {data.collection.period_precedes_collection && <p className="notice">Cette période commence avant l’installation du registre. La collecte a débuté le {utc(data.collection.started_at)} ; aucun historique antérieur n’a été reconstitué.</p>}
      {data.collection.capacity_loss && <p className="notice">Le budget du journal a déjà retiré des événements de ce service. Ce relevé porte sur les événements encore conservés.</p>}
      {!items.length?<p className="empty">{mode==='live'?'Aucun nouvel événement dans ce suivi.':'Aucun événement ne correspond à ces filtres dans les données encore conservées.'}</p>:<ul className="observation-list journal-events">{items.map(item=><li key={item.id} data-log-id={item.id}><JournalEvent item={item}/></li>)}</ul>}
    </>}
    {!error && outOfRange && <p className="notice">Cette page ne contient plus d’événement dans ce relevé. <button onClick={()=>page(1)}>Revenir à la première page</button></p>}
    {!error && mode==='history' && !busy && data && !outOfRange && data.total>pageSize && <Pages page={query.page} total={data.total} pageSize={pageSize} change={page} disabled={exportView.busy} label="Pagination des journaux"/>}
    <ErrorMessage error={exportView.error}/>
    {exportView.count!=null && <Success>{`${exportView.count} événements, ${exportView.bytes} octets téléchargés. ${exportView.finished?'Fin de l’export.':'Un autre lot est disponible ; il reprend le même relevé.'}`}</Success>}
    <p className="muted">Un lot exporte au plus 1000 événements et 1 Mio. Le texte reste échappé. Seuls les secrets effectifs connus sont expurgés ; le code reste responsable des données métier qu’il imprime.</p>
    </div>
  </Section>;
}

function formatJson(text) {
  // Formatting preserves numeric lexemes and escaped strings; converting via
  // JSON.stringify(JSON.parse(...)) would round integers beyond 2^53.
  try {JSON.parse(text);} catch {return text;}
  const tokens=text.match(/"(?:\\.|[^"\\])*"|true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|[{}\[\],:]/g);
  if(!tokens)return text;
  let depth=0,result='';
  for(let index=0;index<tokens.length;index++) {
    const token=tokens[index],previous=tokens[index-1],next=tokens[index+1];
    if(token==='{' || token==='[') {
      result+=token;depth++;
      if(next!==(token==='{'?'}':']'))result+='\n'+'  '.repeat(depth);
    } else if(token==='}' || token===']') {
      depth--;
      if(previous!==(token==='}'?'{':'['))result+='\n'+'  '.repeat(Math.max(0,depth));
      result+=token;
    } else if(token===',')result+=',\n'+'  '.repeat(depth);
    else result+=token===':'?': ':token;
  }
  return result;
}

function JournalEvent({item}) {
  let message=item.message;
  const preview=[...item.message].slice(0,240).join('');
  if(item.message_format==='json')message=formatJson(message);
  const liveFunction=Boolean(item.function_id && item.function_name);
  return <article aria-label={`Événement ${item.id}`}>
    <div className="observation-heading"><h3><ScrollText aria-hidden="true"/>{item.source==='application'?'Message de l’application':'Événement de plateforme'}</h3><Badge tone={['error','fatal'].includes(item.severity)?'danger':'neutral'}>{severityNames[item.severity] || 'Non renseigné'}</Badge></div>
    <p className="muted">{utc(item.observed_at)} · {item.function_name || 'Fonction indisponible'} · {stateNames[item.state] || item.state || 'Sans état'}</p>
    <p className="mono journal-message-preview" aria-label="Aperçu du message">{preview || 'Message vide.'}{preview!==item.message?'…':''}</p>
    <details className="invocation-details"><summary>Texte, corrélation et chronologie</summary><div className="stack">
      <Facts values={[
        ['Événement',mono(item.id)],['Type',mono(item.kind)],['Classe',classes[item.metadata.classification] || 'Non renseignée'],
        ['Fonction',mono(item.function_id)],['Service',mono(item.service_id)],['Invocation',mono(item.invocation_id)],
        ['Requête',mono(item.request_id)],[item.invocation_id?'Hash résolu pour l’appel':'Hash du code',mono(item.code_hash)],['Révision interne',mono(item.revision_id)],
        ['Instance',mono(item.instance_id)],['Publication',mono(item.deployment_id)],['Opération de stockage',mono(item.operation_id)],
      ]}/>
      <p className="muted">{item.source==='application'?'Date observée à la fin de l’invocation. Les dates déclarées dans le message restent des données de l’application.':'Date observée par le contrôle.'}</p>
      {(item.message_truncated || item.collection_truncated || item.projection_truncated) && <p className="notice">{item.message_truncated?'Message limité à 4096 octets UTF-8. ':''}{item.collection_truncated?'Buffer de collecte limité à 64 Kio. ':''}{item.projection_truncated?'Projection limitée aux 1024 premières lignes ; consultez le buffer de l’invocation encore conservé.':''}</p>}
      <p className="muted">Les longues lignes se parcourent horizontalement dans leur cadre au clavier.</p>
      <pre className="invocation-log" tabIndex={0} aria-label={`Texte de ${item.id}`}>{message || 'Message vide.'}</pre>
      <details><summary>Métadonnées publiques et chronologie</summary><pre className="invocation-log" tabIndex={0}>{JSON.stringify(item.metadata,null,2)}</pre></details>
      {liveFunction?<div className="actions"><a href={withCatalogue(`/console/functions/${item.function_id}`)}>Ouvrir la fonction</a>
        {item.invocation_id && <a href={withCatalogue(`/console/functions/${item.function_id}/invocations?invocation=${item.invocation_id}`)}>Ouvrir l’invocation si elle est encore conservée</a>}
        {item.code_hash && <a href={withCatalogue(`/console/functions/${item.function_id}/code`)}>Code et révisions de cette fonction</a>}
        {item.code_hash && <a href={withCatalogue(`/console/functions/${item.function_id}/logs?version=${item.code_hash}`)}>Journaux de ce hash</a>}
        {item.instance_id && <a href={withCatalogue(`/console/functions/${item.function_id}/logs?instance=${item.instance_id}`)}>Journaux de cette instance</a>}
      </div>:<p className="muted">Objet indisponible : ses identifiants sont conservés comme références, sans lien de gestion.</p>}
    </div></details>
  </article>;
}
