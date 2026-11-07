// @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md | docs/DESIGN_SYSTEM_APP.md
import React, {useEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge, Confirm, DialogForm, ErrorMessage, Facts, Field, Section, Success} from './ui';

const size = 5, maxPage = 10000 / size;
const stamp = value => value == null ? 'Non observée' : new Date(value * 1000).toLocaleString('fr-FR');
const reference = value => <span className="mono">{value}</span>;
const states = {
  prepared:['En attente d’archive','neutral'], receiving:['Réception de l’archive','brand'],
  validating:['Validation du handler','brand'], published:['Publiée','success'],
  failed:['Échec','danger'], expired:['Expirée','neutral'],
};
const activeStates = new Set(['receiving','validating']);
function CandidateState({row}) {
  const [label,tone] = row.error_code === 'candidate_abandoned' ? ['Abandonnée','neutral'] : states[row.state] || ['État inconnu','neutral'];
  return <Badge tone={tone}>{label}</Badge>;
}
function readable(error) {
  if (!error.status) error.message = 'Impossible de joindre le serveur. Relisez l’état avant une nouvelle opération.';
  return error;
}

export function CodePublications({functionId,onFunction}) {
  const [state,setState] = useState({loading:true,data:null,error:null});
  const [revision,setRevision] = useState(0), [candidatePage,setCandidatePage] = useState(0), [revisionPage,setRevisionPage] = useState(0);
  const [selected,setSelected] = useState(() => new URLSearchParams(location.search).get('deployment') || '');
  const [dialog,setDialog] = useState(false), [busy,setBusy] = useState(false), [uploading,setUploading] = useState(false);
  const [actionError,setActionError] = useState(null), [notice,setNotice] = useState('');
  const heading = useRef(null), historyHeading = useRef(null), focusHistory = useRef(false);
  const followHeading = useRef(null), focusFollow = useRef(false);
  const mounted = useRef(true), mutating = useRef(false), reading = useRef(true);
  useEffect(() => {mounted.current=true;return () => {mounted.current=false;};}, []);

  // All observations in a cycle are serial. A failed observation stops automatic
  // polling until an explicit retry, and stale data cannot authorize a mutation.
  useEffect(() => {
    let current = true, timer;
    const controller = new AbortController();
    reading.current=true;
    setState(previous => ({...previous,loading:true,error:null}));
    async function read() {
      const options={signal:controller.signal};
      try {
        const fn=await api(`/api/functions/${functionId}`,options);
        const revisions=await api(`/api/functions/${functionId}/revisions?limit=100`,options);
        const candidates=await api(`/api/functions/${functionId}/deployments?limit=${size}&offset=${candidatePage*size}`,options);
        let candidate=null, candidateError=null;
        if (selected) {
          try {
            candidate=await api(`/api/deployments/${encodeURIComponent(selected)}`,options);
            if (candidate.function_id !== functionId) throw Object.assign(new Error('Cette tentative appartient à une autre fonction.'),{status:403});
          } catch(error) {candidate=null;candidateError=readable(error);}
        }
        const observedCandidates=candidate ? {...candidates,items:candidates.items.map(row=>row.id===candidate.id ? candidate : row)} : candidates;
        const confirmed=await api(`/api/functions/${functionId}`,options);
        if (!current) return;
        if (confirmed.updated_at !== fn.updated_at) {setRevision(value=>value+1);return;}
        const lastPage=Math.min(maxPage,Math.max(0,Math.ceil(candidates.total/size)-1));
        if (candidatePage>lastPage) {setCandidatePage(lastPage);return;}
        setRevisionPage(page => Math.min(page,Math.max(0,Math.ceil(revisions.items.length/size)-1)));
        onFunction(fn);
        reading.current=false;
        setState({loading:false,error:null,data:{fn,revisions:revisions.items,candidates:observedCandidates,candidatePage,candidate,candidateError},loadedAt:Date.now()/1000});
        if (!candidateError && (uploading || activeStates.has(candidate?.state))) timer=setTimeout(() => setRevision(value=>value+1),1000);
      } catch(error) {
        if (!current) return;
        reading.current=false;
        setState(previous=>({...previous,loading:false,error:readable(error)}));
      }
    }
    read();
    return () => {current=false;controller.abort();clearTimeout(timer);};
  }, [functionId,onFunction,candidatePage,selected,revision,uploading]);
  useEffect(() => {
    if (!state.loading && focusHistory.current) {focusHistory.current=false;historyHeading.current?.focus();}
  }, [state]);
  useEffect(() => {
    if (!dialog && focusFollow.current) {focusFollow.current=false;followHeading.current?.focus();}
  }, [dialog,selected]);

  const data=state.data, locked=busy || state.loading || Boolean(state.error) || Boolean(data?.candidateError);
  function refresh() {if (!reading.current) {reading.current=true;setState(previous=>({...previous,loading:true}));setRevision(value=>value+1);}}
  function selectCandidate(id) {
    if (id===selected) {refresh();return;}
    const address=new URL(location.href);
    if (id) address.searchParams.set('deployment',id);else address.searchParams.delete('deployment');
    history.replaceState(null,'',address);
    reading.current=true;setState(previous=>({...previous,loading:true}));
    setSelected(id);
  }
  function completed() {
    if (!mounted.current) return;
    reading.current=true;setState(previous=>({...previous,loading:true}));
    mutating.current=false;setBusy(false);setUploading(false);setRevision(value=>value+1);
  }
  async function upload(id,file) {
    try {
      await api(`/api/deployments/${id}/artifact`,{method:'PUT',body:file});
      if (mounted.current) setNotice('Archive publiée. L’état de la fonction est relu.');
    } catch(error) {if (mounted.current) setActionError(readable(error));}
    finally {completed();}
  }
  async function publish(value) {
    if (mutating.current || locked) throw new Error('Actualisez l’état avant de publier.');
    if (!value.file || value.file.size>64*1024*1024) throw new Error('Choisissez une archive ZIP de 64 Mio maximum.');
    mutating.current=true;setBusy(true);setActionError(null);setNotice('');
    const id=crypto.randomUUID();
    // Persist correlation before sending. No content, credential or configuration
    // is persisted in browser storage, and an unknown POST is never replayed.
    const previousAddress=location.href,address=new URL(location.href);address.searchParams.set('deployment',id);history.replaceState(null,'',address);
    try {
      await api(`/api/functions/${functionId}/code-deployments`,{method:'POST',headers:{'If-Match':String(data.fn.updated_at)},body:{handler:value.handler,deployment_id:id}});
      if (!mounted.current) return;
      focusFollow.current=true;setSelected(id);setCandidatePage(0);setUploading(true);
      void upload(id,value.file);
    } catch(error) {
      if (error.status>=400 && error.status<500) {
        history.replaceState(null,'',previousAddress);completed();throw readable(error);
      }
      if (mounted.current) {focusFollow.current=true;setSelected(id);setActionError(readable(error));}
      completed();
    }
  }
  async function mutate(action,message) {
    if (mutating.current || locked) throw new Error('Actualisez l’état avant de poursuivre.');
    mutating.current=true;setBusy(true);setActionError(null);setNotice('');
    try {await action();if (mounted.current) setNotice(message);}
    catch(error) {if (mounted.current) setActionError(readable(error));}
    finally {focusHistory.current=true;completed();}
  }
  function changeCandidates(page) {
    if (page===candidatePage) {refresh();return;}
    if (!reading.current && !busy) {reading.current=true;setState(previous=>({...previous,loading:true}));setCandidatePage(page);}
  }

  return <div className="stack publication-view">
    <section className="panel" aria-labelledby="code-heading">
      <div className="section-heading"><h2 id="code-heading" ref={heading} tabIndex={-1}>Code de la fonction</h2>
        <button onClick={refresh} aria-disabled={state.loading}><RefreshCw aria-hidden="true"/>{state.error ? 'Réessayer' : 'Actualiser'}</button></div>
      {state.loading && <p className="loading" role="status">Lecture de la publication…</p>}
      <ErrorMessage error={state.error}/><ErrorMessage error={actionError}/><Success>{notice}</Success>
      {data && <>
        <p className="muted">Relevé du {stamp(state.loadedAt)}{state.error ? ' · État non actualisé' : ''}</p>
        <Facts values={[
          ['Révision active',data.fn.active_revision_id ? reference(data.fn.active_revision_id) : 'Aucune — fonction brouillon'],
          ['Handler',reference(data.fn.config.handler)],['Runtime',data.fn.config.runtime],
        ]}/>
        {data.fn.storage_operation && <p className="notice">Une opération de stockage attend sa confirmation. Relisez son état avant une nouvelle modification.</p>}
        <p>La publication conserve les ressources, variables, secrets, volumes et routes actuels.</p>
        <button className="primary" disabled={locked || Boolean(data.fn.storage_operation)} onClick={() => setDialog(true)}>Publier une archive</button>
      </>}
    </section>

    {selected && <section className="panel" aria-labelledby="publication-follow-heading">
      <div className="section-heading"><h2 id="publication-follow-heading" tabIndex={-1} ref={followHeading}>Tentative suivie</h2></div>
      <p className="mono">{selected}</p>
      {uploading && <p className="notice" role="status">Envoi et validation en cours. Quitter ou recharger la page peut interrompre l’envoi ; consultez ensuite cette tentative avant de recommencer.</p>}
      <ErrorMessage error={data?.candidateError}/>
      {data?.candidate?.id===selected && <Candidate row={data.candidate} disabled={locked} abandon={() => mutate(
        () => api(`/api/deployments/${data.candidate.id}`,{method:'DELETE'}),'Tentative abandonnée. Aucune révision activée.')} />}
      {!busy && <button onClick={() => selectCandidate('')}>Fermer le suivi</button>}
    </section>}

    <section className="panel" aria-labelledby="revisions-heading">
      <div className="section-heading"><h2 id="revisions-heading" tabIndex={-1} ref={historyHeading}>Révisions conservées</h2></div>
      {data && <>
        {!data.revisions.length ? <p className="empty">Aucune révision publiée.</p> : <ul className="observation-list">
          {data.revisions.slice(revisionPage*size,(revisionPage+1)*size).map(row => <li key={row.id}><Revision row={row} disabled={locked}
            activate={() => mutate(() => api(`/api/functions/${functionId}/rollback`,{method:'POST',headers:{'If-Match':String(data.fn.updated_at)},body:{revision_id:row.id}}),'Révision activée. La configuration courante est conservée.')}
            remove={() => mutate(() => api(`/api/functions/${functionId}/revisions/${row.id}`,{method:'DELETE'}),'Révision supprimée.')}/></li>)}
        </ul>}
        <Pages name="révisions" page={revisionPage} total={data.revisions.length} disabled={busy || state.loading}
          change={page=>{setRevisionPage(page);historyHeading.current?.focus();}}/>
      </>}
    </section>

    <Section title="Tentatives de publication">
      {data && <>
        {!data.candidates.total ? <p className="empty">Aucune tentative de publication.</p> : <ul className="observation-list">{data.candidates.items.map(row => <li key={row.id}>
          <article aria-label={`Tentative ${row.id}`}><div className="observation-heading"><h3 className="mono">{row.id}</h3><CandidateState row={row}/></div>
          <p className="muted">Préparée le {stamp(row.created_at)}</p>
          <button disabled={busy || state.loading} onClick={()=>selectCandidate(row.id)}>Consulter cette tentative</button></article>
        </li>)}</ul>}
        <Pages name="tentatives" page={data.candidatePage} total={data.candidates.total} disabled={busy || state.loading} change={changeCandidates}/>
      </>}
    </Section>

    {dialog && <DialogForm title="Publier une archive" initial={{handler:data.fn.config.handler,file:null}} submitLabel="Vérifier la publication" confirmationLabel="Confirmer la publication"
      onClose={()=>setDialog(false)} onSubmit={publish}
      confirmation={value=>`Publier « ${value.file?.name || ''} » pour « ${data.fn.name} » avec le handler ${value.handler} ? Les réglages, variables, secrets et routes courants seront conservés.`}>
      {(value,setValue)=><>
        <Field label="Archive ZIP" help="64 Mio maximum. Le code et ses dépendances doivent être prêts à exécuter."><input type="file" accept=".zip,application/zip" required onChange={event=>setValue({...value,file:event.target.files[0] || null})}/></Field>
        <Field label="Handler" help="Chemin du module puis nom de l’export, par exemple src/handler.run."><input required minLength={3} maxLength={256} value={value.handler} onChange={event=>setValue({...value,handler:event.target.value})}/></Field>
      </>}
    </DialogForm>}
  </div>;
}

function Pages({name,page,total,disabled,change}) {
  if (!total) return null;
  const pages=Math.max(1,Math.min(maxPage+1,Math.ceil(total/size)));
  return <nav className="pagination" aria-label={`Pagination des ${name}`}>
    <button disabled={disabled || page===0} onClick={()=>change(page-1)}><ChevronLeft aria-hidden="true"/>Précédente</button>
    <span>Page {page+1} sur {pages}</span>
    <button disabled={disabled || page+1>=pages} onClick={()=>change(page+1)}>Suivante<ChevronRight aria-hidden="true"/></button>
  </nav>;
}

function Candidate({row,disabled,abandon}) {
  return <article aria-label={`Suivi ${row.id}`}>
    <div className="observation-heading"><h3>État de la tentative</h3><CandidateState row={row}/></div>
    <Facts values={[
      ['Préparation',stamp(row.created_at)],['Expiration',stamp(row.expires_at)],['Fin',stamp(row.completed_at)],
      ['Révision publiée',row.revision_id ? reference(row.revision_id) : 'Aucune'],
      ...(row.error_code ? [['Diagnostic',reference(row.error_code)]] : []),
    ]}/>
    {row.validation && <details className="invocation-details"><summary>Validation et journal</summary><div className="stack">
      <Facts values={[
        ['Chargement valide',row.validation.valid ? 'Oui' : 'Non'],['Image Node',reference(row.validation.image_id)],
        ['Diagnostic du chargement',row.validation.error || 'Aucun'],['Conteneur de validation supprimé',row.validation.container_removed ? 'Oui' : 'Non confirmé'],
      ]}/>
      {row.validation.logs_truncated && <p className="notice log-warning">Journal tronqué à la limite de collecte.</p>}
      {row.validation.logs ? <pre className="invocation-log" tabIndex={0} aria-label={`Journal de validation de ${row.id}`}>{row.validation.logs}</pre> : <p className="muted">Aucun journal collecté.</p>}
    </div></details>}
    {row.state==='prepared' && <fieldset className="form-fields" disabled={disabled}><Confirm label="Abandonner cette tentative" message="Libérer cette tentative en attente d’archive ? La fonction active sera conservée." action={abandon}/></fieldset>}
  </article>;
}

function Revision({row,disabled,activate,remove}) {
  return <article aria-label={`Révision ${row.id}`}>
    <div className="observation-heading"><h3 className="mono">{row.id}</h3><Badge tone={row.active ? 'success' : 'neutral'}>{row.active ? 'Active' : 'Inactive'}</Badge></div>
    <p className="muted">Publiée le {stamp(row.created_at)}</p>
    <Facts values={[["Handler",reference(row.handler)],['Runtime',row.runtime],['Espace stocké',`${new Intl.NumberFormat('fr-FR').format(row.stored_bytes)} octets`]]}/>
    <details className="invocation-details"><summary>Métadonnées de la révision</summary><div className="stack">
      <Facts values={[
        ['SHA256 de l’archive',reference(row.archive_sha256)],['Image Node',reference(row.image_id)],['Architecture',row.architecture],
      ]}/>
      <h4>Événements de la révision</h4><pre className="invocation-log" tabIndex={0} aria-label={`Événements de ${row.id}`}>{JSON.stringify(row.events,null,2)}</pre>
    </div></details>
    {!row.active && <fieldset className="form-fields revision-actions" disabled={disabled}>
      <Confirm label="Activer cette révision" message={`Activer la révision ${row.id} ? Les ressources, variables, secrets et volumes courants seront conservés.`} action={activate}/>
      <Confirm label="Supprimer cette révision" message={`Supprimer définitivement la révision ${row.id} ? Cette archive de code ne pourra plus être réactivée.`} action={remove}/>
    </fieldset>}
  </article>;
}
