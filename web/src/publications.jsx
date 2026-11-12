// @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md | docs/DESIGN_SYSTEM_APP.md
// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#gérer-les-révisions
import React, {useEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, Copy, RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge, Confirm, DialogForm, ErrorMessage, Facts, Field, Section, Success} from './ui';
import {withCatalogue} from './catalogue';

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
  if (error.message==='version_unavailable') error.message='La version demandée est inconnue, archivée ou supprimée.';
  return error;
}

export function CodePublications({functionId,onFunction}) {
  const [state,setState] = useState({loading:true,data:null,error:null});
  const [revision,setRevision] = useState(0), [candidatePage,setCandidatePage] = useState(0), [revisionPage,setRevisionPage] = useState(0);
  const [selected,setSelected] = useState(() => new URLSearchParams(location.search).get('deployment') || '');
  const [removal,setRemoval]=useState(null);
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
        const candidates=await api(`/api/functions/${functionId}/deployments?limit=${size}&offset=${candidatePage*size}`,options);
        let candidate=null, candidateError=null;
        if (selected) {
          try {
            candidate=await api(`/api/deployments/${encodeURIComponent(selected)}`,options);
            if (candidate.function_id !== functionId) throw Object.assign(new Error('Cette tentative appartient à une autre fonction.'),{status:403});
          } catch(error) {candidate=null;candidateError=readable(error);}
        }
        // A terminal candidate and its catalogue entry share one commit. Read
        // the catalogue after that candidate: code-only publication keeps the
        // parent ETag unchanged, so the final parent check alone cannot prove it.
        const versions=await api(`/api/functions/${functionId}/versions?limit=${size}&offset=${revisionPage*size}`,options);
        const observedCandidates=candidate ? {...candidates,items:candidates.items.map(row=>row.id===candidate.id ? candidate : row)} : candidates;
        const confirmed=await api(`/api/functions/${functionId}`,options);
        if (!current) return;
        if (confirmed.updated_at !== fn.updated_at || versions.function_version !== fn.updated_at) {setRevision(value=>value+1);return;}
        const lastPage=Math.min(maxPage,Math.max(0,Math.ceil(candidates.total/size)-1));
        if (candidatePage>lastPage) {setCandidatePage(lastPage);return;}
        const lastVersionPage=Math.min(maxPage,Math.max(0,Math.ceil(versions.total/size)-1));
        if (revisionPage>lastVersionPage) {setRevisionPage(lastVersionPage);return;}
        onFunction(fn);
        reading.current=false;
        setState({loading:false,error:null,data:{fn,versions,candidates:observedCandidates,candidatePage,candidate,candidateError},loadedAt:Date.now()/1000});
        if (!candidateError && (uploading || activeStates.has(candidate?.state))) timer=setTimeout(() => setRevision(value=>value+1),1000);
      } catch(error) {
        if (!current) return;
        reading.current=false;
        setState(previous=>({...previous,loading:false,error:readable(error)}));
      }
    }
    read();
    return () => {current=false;controller.abort();clearTimeout(timer);};
  }, [functionId,onFunction,candidatePage,revisionPage,selected,revision,uploading]);
  useEffect(() => {
    if (!state.loading && focusHistory.current) {focusHistory.current=false;historyHeading.current?.focus();}
  }, [state]);
  useEffect(() => {
    if (!dialog && focusFollow.current) {focusFollow.current=false;followHeading.current?.focus();}
  }, [dialog,selected]);

  const data=state.data, locked=busy || state.loading || Boolean(state.error) || Boolean(data?.candidateError);
  function refresh() {if (!reading.current) {setNotice('');reading.current=true;setState(previous=>({...previous,loading:true}));setRevision(value=>value+1);}}
  function selectCandidate(id) {
    if (id===selected) {refresh();return;}
    setNotice('');
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
      const result=await api(`/api/deployments/${id}/artifact`,{method:'PUT',body:file});
      if (mounted.current) setNotice(result.version_restored ? 'Version réimportée.' : result.code_changed ? 'Nouvelle version publiée.' : 'Code inchangé : version réutilisée.');
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
      await api(`/api/functions/${functionId}/code-deployments`,{method:'POST',headers:{'If-Match':String(data.fn.updated_at)},
        body:{handler:value.handler,deployment_id:id,...(value.restoreHash ? {restore_code_hash:value.restoreHash,events:value.events} : {})}});
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
    try {const result=await action();if (mounted.current) {setNotice(typeof message==='function' ? message(result) : message);focusHistory.current=true;}return result;}
    catch(error) {
      const failure=readable(error);
      if (mounted.current && (!failure.status || failure.status>=500)) setActionError(failure);
      throw failure;
    }
    finally {completed();}
  }
  function changeCandidates(page) {
    if (page===candidatePage) {refresh();return;}
    if (!reading.current && !busy) {setNotice('');reading.current=true;setState(previous=>({...previous,loading:true}));setCandidatePage(page);}
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
          ['Cible par défaut',data.versions.active_code_hash ? reference(data.versions.active_code_hash) : 'Aucune version promue'],
          ['Handler par défaut',reference(data.fn.config.handler)],['Runtime',data.fn.config.runtime],
        ]}/>
        {data.fn.storage_operation && <p className="notice">Une opération de stockage attend sa confirmation. Relisez son état avant une nouvelle modification.</p>}
        <p><a href="/console/manual#gérer-les-révisions">Consulter le manuel des versions et promotions</a></p>
        <button className="primary" disabled={locked || Boolean(data.fn.storage_operation)} onClick={() => setDialog({})}>Publier une archive</button>
      </>}
    </section>

    {selected && <section className="panel" aria-labelledby="publication-follow-heading">
      <div className="section-heading"><h2 id="publication-follow-heading" tabIndex={-1} ref={followHeading}>Tentative suivie</h2></div>
      <p className="mono">{selected}</p>
      {uploading && <p className="notice" role="status">Envoi et validation en cours. Quitter ou recharger la page peut interrompre l’envoi ; consultez ensuite cette tentative avant de recommencer.</p>}
      <ErrorMessage error={data?.candidateError}/>
      {data?.candidate?.id===selected && <Candidate row={data.candidate} disabled={locked} abandon={() => mutate(
        () => api(`/api/deployments/${data.candidate.id}`,{method:'DELETE'}),'Préparation abandonnée.')} />}
      {!busy && <button onClick={() => selectCandidate('')}>Fermer le suivi</button>}
    </section>}

    <section className="panel" aria-labelledby="revisions-heading">
      <div className="section-heading"><h2 id="revisions-heading" tabIndex={-1} ref={historyHeading}>Versions du code</h2></div>
      {data && <>
        {!data.versions.total ? <p className="empty">Aucune version publiée.</p> : <ul className="observation-list">
          {data.versions.items.map(row => <li key={row.code_hash}><CodeVersion row={row} functionName={data.fn.name} functionId={functionId}
            observation={`${state.loadedAt}:${state.loading}`} disabled={locked}
            perform={(action,body={}) => mutate(() => api(`/api/functions/${functionId}/versions/${row.code_hash}${action==='delete' ? '' : '/'+action}`,
              {method:action==='delete' ? 'DELETE' : 'POST',headers:{'If-Match':String(data.fn.updated_at)},...(action==='archive'||action==='delete' ? {body} : {})}),
              result => action==='delete' ? (result.cleanup_pending ? 'Version retirée. Nettoyage physique en attente.' : 'Version supprimée.') :
                action==='promote' ? (result.changed ? 'Cible par défaut mise à jour.' : 'Cette version est déjà la cible par défaut.') : action==='restore' ? 'Version restaurée.' : 'Version archivée.')}
            requestRemoval={setRemoval} reimport={() => setDialog({restoreHash:row.code_hash,handler:row.handler,events:row.events})}/></li>)}
        </ul>}
        <Pages name="versions" page={revisionPage} total={data.versions.total} disabled={busy || state.loading}
          change={page=>{if (!reading.current) {setNotice('');reading.current=true;setRevisionPage(page);focusHistory.current=true;}}}/>
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

    {dialog && <DialogForm title={dialog.restoreHash ? 'Réimporter une version' : 'Publier une archive'}
      initial={{handler:dialog.handler || data.fn.config.handler,file:null,restoreHash:dialog.restoreHash || null,events:dialog.events || null}}
      submitLabel="Vérifier la publication" confirmationLabel={dialog.restoreHash ? 'Confirmer la réimportation' : 'Confirmer la publication'}
      preserveConfirmationOnError
      onClose={()=>setDialog(false)} onSubmit={publish}
      confirmation={value=>`${value.restoreHash ? 'Réimporter le hash '+value.restoreHash+' depuis' : 'Publier'} « ${value.file?.name || ''} » pour « ${data.fn.name} » avec le handler ${value.handler} ? La cible par défaut sera conservée.`}>
      {(value,setValue)=><>
        {value.restoreHash && <Facts values={[["Hash à réimporter",reference(value.restoreHash)]]}/>}
        <Field label="Archive ZIP" help="64 Mio maximum. Le code et ses dépendances doivent être prêts à exécuter."><input type="file" accept=".zip,application/zip" required onChange={event=>setValue({...value,file:event.target.files[0] || null})}/></Field>
        <Field label="Handler" help={value.restoreHash ? 'Handler de la version supprimée.' : 'Chemin du module puis nom de l’export, par exemple src/handler.run.'}><input required readOnly={Boolean(value.restoreHash)} minLength={3} maxLength={256} value={value.handler} onChange={event=>setValue({...value,handler:event.target.value})}/></Field>
      </>}
    </DialogForm>}
    {removal && <VersionRemoval choice={removal} onClose={()=>setRemoval(null)} focusTarget={historyHeading}/>}
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

// @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#publication-et-réponses-perdues | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#modifier-le-code-dans-la-console
export function Candidate({row,disabled,abandon}) {
  return <article aria-label={`Suivi ${row.id}`}>
    <div className="observation-heading"><h3>État de la tentative</h3><CandidateState row={row}/></div>
    <Facts values={[
      ['Préparation',stamp(row.created_at)],['Expiration',stamp(row.expires_at)],['Fin',stamp(row.completed_at)],
      ['Révision publiée',row.revision_id ? reference(row.revision_id) : 'Aucune'],
      ...(row.restore_code_hash ? [['Hash à réimporter',reference(row.restore_code_hash)]] : []),
      ...(row.code_hash ? [['Hash publié',reference(row.code_hash)],['Résultat du code',row.version_restored ? 'Version réimportée' : row.code_changed ? 'Nouvelle version' : 'Code inchangé'],
        ['Cible observée à publication',row.default_code_hash_at_publication ? reference(row.default_code_hash_at_publication) : 'Aucune version promue']] : []),
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

// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#gérer-les-révisions
function HashCopy({value,disabled}) {
  const [copied,setCopied]=useState(false),[error,setError]=useState(null),[busy,setBusy]=useState(false);
  async function copy() {
    if (busy || disabled) return;
    setBusy(true);setCopied(false);setError(null);
    try {await navigator.clipboard.writeText(value);setCopied(true);}
    catch {setError(new Error('Copie refusée. Sélectionnez et copiez le hash affiché.'));}
    finally {setBusy(false);}
  }
  return <><Facts values={[["Hash du code",reference(value)]]}/>
    <div className="actions"><button disabled={disabled || busy} onClick={copy}><Copy aria-hidden="true"/>Copier le hash du code</button></div>
    <Success>{copied ? 'Hash du code copié.' : ''}</Success><ErrorMessage error={error}/></>;
}

function CodeVersion({row,functionName,functionId,observation,disabled,perform,reimport,requestRemoval}) {
  const [restoreError,setRestoreError]=useState(null);
  const [restoring,setRestoring]=useState(false);
  const states={available:['Disponible','success'],archived:['Archivée','neutral'],deleted:['Supprimée','neutral']};
  const [label,tone]=states[row.state] || ['État inconnu','neutral'];
  async function restore() {
    if (disabled || restoring) return;
    setRestoring(true);setRestoreError(null);
    try {await perform('restore');} catch(error) {setRestoreError(error);} finally {setRestoring(false);}
  }
  return <article aria-label={`Version ${row.code_hash}`}>
    <div className="observation-heading"><h3>Version du {stamp(row.created_at)}</h3><div className="actions">
      <Badge tone={tone}>{label}</Badge>{row.active && <Badge tone="brand">Cible par défaut</Badge>}</div></div>
    <HashCopy key={observation} value={row.code_hash} disabled={disabled}/>
    <Facts values={[["Handler",reference(row.handler)],['Runtime',row.runtime],['Espace stocké',`${new Intl.NumberFormat('fr-FR').format(row.stored_bytes)} octets`]]}/>
    <details className="invocation-details"><summary>Métadonnées de la version</summary><div className="stack">
      <Facts values={[["Révision interne",reference(row.revision_id)],["Alias historiques",row.revision_count],
        ['SHA256 de l’archive',reference(row.archive_sha256)],['Image Node',reference(row.image_id)],['Architecture',row.architecture],['Dernière modification',stamp(row.updated_at)]]}/>
      <h4>Événements de la version</h4><pre className="invocation-log" tabIndex={0} aria-label={`Événements de ${row.code_hash}`}>{JSON.stringify(row.events,null,2)}</pre>
    </div></details>
    <fieldset className="form-fields revision-actions" disabled={disabled}>
      {row.state==='available' && <>
        <a href={withCatalogue(`/console/functions/${functionId}/invocation-urls?version=${row.code_hash}`)}>Adresses de cette version</a>
        {!row.active && <Confirm tone="primary" label="Promouvoir cette version"
          message={`Promouvoir le hash ${row.code_hash} pour « ${functionName} » comme cible des appels sans tag ?`} action={()=>perform('promote')}/>}
        {row.active ? <button onClick={()=>requestRemoval({row,functionName,perform,action:'archive'})}>Archiver cette version</button> :
          <Confirm label="Archiver cette version" message={`Archiver le hash ${row.code_hash} de « ${functionName} » et refuser ses nouveaux appels ?`} action={()=>perform('archive')}/>}
      </>}
      {row.state==='archived' && <button disabled={restoring} onClick={restore}>{restoring ? 'Restauration…' : 'Restaurer cette version'}</button>}
      {row.state==='deleted' ? <button onClick={reimport}>Réimporter cette version</button> :
        row.active ? <button onClick={()=>requestRemoval({row,functionName,perform,action:'delete'})}>Supprimer cette version</button> :
          <Confirm label="Supprimer cette version" message={`Supprimer le code du hash ${row.code_hash} de « ${functionName} » après la fin de ses appels admis ? Une réimportation du paquet sera nécessaire pour le retrouver.`} action={()=>perform('delete')}/>}
    </fieldset>
    {/* @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#parcours-et-droits | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#modifier-le-code-dans-la-console */}
    {row.state!=='deleted'&&row.stored_bytes>0&&<a href={withCatalogue(`/console/functions/${functionId}/editor?view=source&version=${row.code_hash}`)}>Modifier ce code</a>}
    <ErrorMessage error={restoreError}/>

  </article>;
}

// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#gérer-les-révisions
function VersionRemoval({choice,onClose,focusTarget}) {
  // Ownership belongs to the view, independently of the paginated source card.
  const {row,functionName,perform,action:removal}=choice;
  return <DialogForm title={removal==='delete' ? 'Supprimer la version courante' : 'Archiver la version courante'}
      initial={{mode:'',replacement:''}} submitLabel="Vérifier le retrait" confirmationLabel={removal==='delete' ? 'Confirmer la suppression' : 'Confirmer l’archivage'}
      confirmationTone={removal==='delete' ? 'danger' : 'primary'} onClose={onClose} focusTarget={focusTarget}
      preserveConfirmationOnError
      onSubmit={value=>perform(removal,value.mode==='disable' ? {disable_default:true} : {replacement_code_hash:value.replacement})}
      confirmation={value=>`${removal==='delete' ? 'Supprimer' : 'Archiver'} le hash ${row.code_hash} de « ${functionName} » et ${value.mode==='disable' ? 'désactiver sa cible sans tag' : 'promouvoir le hash '+value.replacement} ?`}>
      {(value,setValue)=><>
        <Facts values={[["Fonction",functionName],["Hash retiré",reference(row.code_hash)]]}/>
        <Field label="Cible après retrait"><select required value={value.mode} onChange={event=>setValue({...value,mode:event.target.value})}>
          <option value="">Choisir la cible</option><option value="replacement">Remplacer par un hash disponible</option><option value="disable">Désactiver les appels sans tag</option>
        </select></Field>
        {value.mode==='replacement' && <Field label="Hash de remplacement" help="Hash complet d’une autre version disponible de cette fonction.">
          <input required minLength={64} maxLength={64} pattern="[0-9a-f]{64}" value={value.replacement} onChange={event=>setValue({...value,replacement:event.target.value})}/>
        </Field>}
      </>}
    </DialogForm>;
}
