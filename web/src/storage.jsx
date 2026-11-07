// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#console-et-manuel | docs/manual.md | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md#stockage-et-archives-sls-065
import React, {useEffect,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight,RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge,Confirm,ErrorMessage,Facts,Field,Section,Success} from './ui';

const pageSize=5;
const stamp=value=>value==null?'Non terminée':new Date(value*1000).toLocaleString('fr-FR');
const size=value=>value==null?'Indisponible':new Intl.NumberFormat('fr-FR',{maximumFractionDigits:3}).format(value/1024**2)+' Mio';
const reference=value=><span className="mono">{value}</span>;
const phaseLabels={active:'Actif',archived:'Archivé',purging:'Purge en cours',purged:'Purgé',mounted:'Monté',unmounted:'Démonté',
  mounting:'Montage en cours',unmounting:'Démontage en cours',failed:'À reprendre',draining:'Arrêt des instances',
  volumes:'Effacement des volumes',artifacts:'Effacement du code'};
const commandStates={preparing:['Préparation','brand'],pending:['En attente','neutral'],completed:['Terminée','success'],aborted:['Abandonnée','neutral']};

function Command({row}) {
  if (!row) return <p className="empty">Aucune commande de stockage enregistrée.</p>;
  const [label,tone]=commandStates[row.state]||['État inconnu','neutral'];
  return <div className="stack" aria-live="polite"><div className="section-heading"><h3>{row.kind==='purge'?'Purge des archives':'Vidage du cache'}</h3><Badge tone={tone}>{label}</Badge></div>
    <Facts values={[
      ['Identifiant de l’opération',reference(row.id)],['Demandée le',stamp(row.created_at)],
      ['Étape',row.phase?phaseLabels[row.phase]||'Indisponible':'Aucune étape en cours'],['Terminée le',stamp(row.completed_at)],
    ]}/>
    {row.state==='pending'&&<p>La demande est enregistrée. Actualiser permet de consulter son avancement.</p>}
    {row.error_code&&<p>Diagnostic : <span className="mono">{row.error_code}</span></p>}
  </div>;
}

function Volumes({storage}) {
  if (!storage.available) return <div className="notice error" role="status"><p>Le stockage est momentanément indisponible. Actualisez pour réessayer.</p></div>;
  if (!storage.registered||!Object.keys(storage.volumes).length) return <p className="empty">Aucun volume alloué.</p>;
  return <div className="stack"><Facts values={[
    ['État du stockage',phaseLabels[storage.state]||'Indisponible'],['Baux actifs',storage.leases],
  ]}/>{Object.entries(storage.volumes).map(([kind,row])=><section key={kind} className="storage-volume" aria-label={kind==='data'?'Données permanentes':'Cache reconstructible'}>
    <h3>{kind==='data'?'Données permanentes':'Cache reconstructible'}</h3><Facts values={[
      ['Accès',row.enabled?'Activé':'Désactivé'],['Espace alloué',size(row.quota_bytes)],
      ['Dernière occupation mesurée',size(row.last_measured_used_bytes)],['Montage',phaseLabels[row.phase]||'Indisponible'],
    ]}/>{row.error&&<p>Diagnostic : <span className="mono">{row.error}</span></p>}
  </section>)}<p className="muted">L’occupation est la dernière mesure logique disponible ; elle peut évoluer entre deux relevés.</p></div>;
}

export function FunctionStorage({functionId}) {return <StorageDetail id={functionId}/>;}

export function ArchiveDetail({id}) {
  return <><nav className="breadcrumb" aria-label="Fil d’Ariane"><a href="/console/archives">Archives de fonctions</a><span>/</span><span>Détail de l’archive</span></nav>
    <div className="page-title"><h1>Archive de fonction</h1></div><StorageDetail id={id} archived/></>;
}

function StorageDetail({id,archived=false}) {
  const endpoint=archived?`/api/archives/${id}`:`/api/functions/${id}/storage`;
  const initialOperation=new URL(location.href).searchParams.get('operation');
  const [tracked,setTracked]=useState(initialOperation),operation=useRef(initialOperation);
  const [state,setState]=useState({loading:true,row:null,error:null}),[busy,setBusy]=useState(false),[success,setSuccess]=useState(null);
  const controller=useRef(null),alive=useRef(true),heading=useRef(null);
  async function load() {
    controller.current?.abort();const current=new AbortController();controller.current=current;
    setSuccess(null);setState(old=>({...old,loading:true,error:null}));
    try {
      const row=await api(endpoint,{signal:current.signal});
      const command=operation.current?await api(`/api/storage-operations/${encodeURIComponent(operation.current)}`,{signal:current.signal}):row.command;
      if (command&&command.function_id!==id) throw new Error('Cette opération appartient à une autre fonction. Arrêtez son suivi pour relire cette fiche.');
      if (!current.signal.aborted&&alive.current) setState({loading:false,row,command,error:null,loadedAt:Date.now()/1000});
    } catch(error) {
      if (!current.signal.aborted&&alive.current) {
        if (!error.status) error.message=error.message.startsWith('Cette opération')?error.message:'Impossible de joindre le serveur. Vérifiez la connexion puis réessayez.';
        setState(old=>({...old,loading:false,error}));
      }
    }
  }
  useEffect(()=>{alive.current=true;load();return()=>{alive.current=false;controller.current?.abort();};},[endpoint]);
  function follow(value) {
    operation.current=value;setTracked(value);const url=new URL(location.href);
    setState(old=>({...old,command:null}));
    if (value) url.searchParams.set('operation',value);else url.searchParams.delete('operation');
    history.replaceState(null,'',url);
  }
  async function start() {
    if (disabled) return;
    const identifier=crypto.randomUUID();follow(identifier);setBusy(true);setSuccess(null);
    try {
      const result=await api(archived?`/api/archives/${id}/purge`:`/api/functions/${id}/cache-clear`,{
        method:'POST',headers:{'If-Match':String(state.row.updated_at)},
        body:{operation_id:identifier,...(archived?{confirm_name:state.row.name}:{})},
      });
      await load();
      if (alive.current&&result.state==='completed') setSuccess(archived?'Les archives de cette fonction sont purgées.':'Le cache de cette fonction est vidé.');
    } catch(error) {
      await load();
      if (!error.status) error.message='La réponse n’a pas été reçue. Consultez le suivi avant toute nouvelle demande.';
      throw error;
    } finally {if (alive.current) setBusy(false);}
  }
  const row=state.row;
  const disabled=busy||state.loading||Boolean(state.error)||!row||!row.storage.available||Boolean(row.storage_operation)||Boolean(row.purged_at);
  return <>
    <Section title={archived?'Archives conservées':'Volumes de la fonction'} headingRef={heading} action={<button onClick={()=>{if (!state.loading&&!busy) load();}} aria-disabled={state.loading||busy}><RefreshCw aria-hidden="true"/>{state.error?'Réessayer':'Actualiser'}</button>}>
      {state.loading&&<p role="status">Lecture du stockage…</p>}<ErrorMessage error={state.error}/>
      {row&&<div aria-busy={state.loading} className="stack">
        <p className="muted">Relevé du {stamp(state.loadedAt)}</p>
        {archived&&<><h3>{row.name}</h3><Badge tone="neutral">{row.purged_at?'Purgée':row.storage_operation?.kind==='purge'?'Purge en cours':'Conservée'}</Badge><Facts values={[
          ['Fonction',reference(row.id)],['Service',<>{row.service_name}<br/>{reference(row.service_id)}</>],
          ['Namespace',<>{row.namespace_name}<br/>{reference(row.namespace_id)}</>],['Suppression',stamp(row.deleted_at)],
          ['Révisions conservées',row.revision_count],['Espace du code encore occupé ou réservé',size(row.artifact_bytes)],
          ['Purge terminée',row.purged_at?stamp(row.purged_at):'Non effectuée'],
        ]}/></>}
        <Volumes storage={row.storage}/>
        {row.storage_operation&&<p role="status">Une opération de stockage est en cours. Les modifications attendent sa confirmation.</p>}
        <Confirm disabled={disabled} focusTarget={heading} label={archived?'Purger les archives':'Vider le cache'} name={archived?row.name:undefined}
          message={archived?`Effacer définitivement les données, le cache, le code et la configuration propre de « ${row.name} » ?`:
            `Vider le cache de « ${row.name} » ? Les instances au repos seront arrêtées ; les données permanentes, le code et les réglages seront conservés.`} action={start}/>
      </div>}
      <Success>{success}</Success>
    </Section>
    <Section title="Suivi de l’opération" action={tracked&&<button disabled={state.loading||busy} onClick={()=>{follow(null);heading.current?.focus();load();}}>Ne plus suivre cet identifiant</button>}>
      {tracked&&<p>Identifiant suivi : {reference(tracked)}</p>}
      {busy||state.loading?<p role="status">{busy?'Demande en cours…':'Lecture du suivi…'}</p>:state.error?<p>Le suivi n’est pas confirmé. Actualisez avant de lancer une nouvelle demande.</p>:
        tracked&&state.command?.id!==tracked?<p role="status">Le résultat de cet identifiant n’est pas encore confirmé.</p>:<Command row={state.command}/>}
    </Section>
  </>;
}

export function Archives() {
  const [filter,setFilter]=useState('retained'),[page,setPage]=useState(0),[revision,setRevision]=useState(0);
  const [state,setState]=useState({loading:true,data:null,error:null}),heading=useRef(null),focus=useRef(false);
  useEffect(()=>{
    const controller=new AbortController();setState(old=>({...old,loading:true,error:null}));
    api(`/api/archives?state=${filter}&limit=${pageSize}&offset=${page*pageSize}`,{signal:controller.signal}).then(data=>{
      if (controller.signal.aborted) return;
      const last=Math.max(0,Math.ceil(data.total/pageSize)-1);
      if (page>last) {setPage(last);return;}
      setState({loading:false,data,error:null,page});
    }).catch(error=>{
      if (controller.signal.aborted) return;
      if (!error.status) error.message='Impossible de joindre le serveur. Vérifiez la connexion puis réessayez.';
      setState(old=>({...old,loading:false,error}));
    });return()=>controller.abort();
  },[filter,page,revision]);
  useEffect(()=>{if (!state.loading&&focus.current) {focus.current=false;heading.current?.focus();}},[state]);
  const total=state.data?.total||0;
  function changePage(value) {if (!state.loading) {focus.current=true;setPage(value);}}
  return <><div className="page-title"><h1 ref={heading} tabIndex={-1}>Archives de fonctions</h1><button aria-disabled={state.loading} onClick={()=>{if (!state.loading) setRevision(v=>v+1);}}><RefreshCw aria-hidden="true"/>{state.error?'Réessayer':'Actualiser'}</button></div>
    <section className="panel"><Field label="Afficher les archives"><select value={filter} disabled={state.loading} onChange={event=>{focus.current=true;setPage(0);setFilter(event.target.value);}}>
      <option value="retained">Conservées</option><option value="purged">Purgées</option><option value="all">Toutes</option>
    </select></Field>
    <div aria-busy={state.loading}>{state.loading?<p role="status">Chargement des archives…</p>:state.error?<ErrorMessage error={state.error}/>:<>
      <p className="muted" role="status">{total} archive{total>1?'s':''}</p>
      {!state.data.items.length?<p className="empty">Aucune archive pour ce filtre.</p>:<ul className="observation-list">{state.data.items.map(row=><li key={row.id}>
        <article aria-label={`Archive ${row.name}`}><div className="section-heading"><h2><a href={`/console/archives/${row.id}`}>{row.name}</a></h2><Badge tone="neutral">{row.purged_at?'Purgée':'Conservée'}</Badge></div>
          <Facts values={[
            ['Identifiant de fonction',reference(row.id)],['Namespace et service',<>{row.namespace_name} / {row.service_name}</>],
            ['Suppression',stamp(row.deleted_at)],['Code encore occupé ou réservé',size(row.artifact_bytes)],
          ]}/></article>
      </li>)}</ul>}
    </>}</div>
    {total>0&&<nav className="pagination" aria-label="Pagination des archives"><button disabled={state.loading||Boolean(state.error)||page===0} onClick={()=>changePage(page-1)}><ChevronLeft aria-hidden="true"/>Précédente</button>
      <span>Page {(state.page??page)+1} sur {Math.max(1,Math.ceil(total/pageSize))}</span>
      <button disabled={state.loading||Boolean(state.error)||(page+1)*pageSize>=total} onClick={()=>changePage(page+1)}>Suivante<ChevronRight aria-hidden="true"/></button>
    </nav>}</section></>;
}
