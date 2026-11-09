// @spec docs/BACKLOG.md#sls-061 | docs/CONSOLE_EXECUTION.md | docs/DESIGN_SYSTEM_APP.md
// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#sélection-http-et-admission | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#consulter-les-instances-et-les-journaux
import React, {useEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge, ErrorMessage, Facts} from './ui';

const pageSize = 5;
const maxPage = 10000 / pageSize;
const titles = {instances:'Instances', invocations:'Invocations'};
const states = {
  starting:['Démarrage','brand'], ready:['Disponible','success'], busy:['Occupée','brand'],
  draining:['Arrêt en cours','neutral'], cleanup_failed:['Nettoyage à reprendre','danger'],
  receiving:['Réception','brand'], queued:['En attente','neutral'], admitted:['Admise','brand'],
  running:['En cours','brand'], succeeded:['Terminée','success'], failed:['Échec','danger'],
  rejected:['Refusée','danger'], disconnected:['Client déconnecté','neutral'], interrupted:['Interrompue','danger'],
};
const activeStates = new Set(['receiving','queued','admitted','running']);
const number = (value, divisor = 1) => value == null ? 'Indisponible' : new Intl.NumberFormat('fr-FR',{maximumFractionDigits:3}).format(value / divisor);
const stamp = value => value == null ? 'Non observée' : new Date(value * 1000).toLocaleString('fr-FR');
const reference = value => value ? <span className="mono">{value}</span> : 'Non attribuée';
function State({value}) {
  const [label,tone] = states[value] || ['État inconnu','neutral'];
  return <Badge tone={tone}>{label}</Badge>;
}

// Manual refresh keeps controls mounted and serializes requests for this view.
export function ExecutionObservations({functionId,kind}) {
  const [page,setPage] = useState(0), [revision,setRevision] = useState(0);
  const [state,setState] = useState({loading:true,data:null,error:null,total:0});
  const heading = useRef(null), focusAfterPage = useRef(false), inFlight = useRef(true);
  const title = titles[kind];
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    inFlight.current = true;
    setState(previous => ({...previous,loading:true,error:null,data:null}));
    api(`/api/functions/${functionId}/${kind}?limit=${pageSize}&offset=${page * pageSize}`,{signal:controller.signal})
      .then(data => {
        if (!current) return;
        const lastPage = Math.min(maxPage,Math.max(0,Math.ceil(data.total / pageSize) - 1));
        if (page > lastPage) {setPage(lastPage);return;}
        inFlight.current = false;
        setState({loading:false,data,error:null,total:data.total,loadedAt:Date.now() / 1000});
      }).catch(error => {
        if (!current) return;
        if (!error.status) error.message = 'Impossible de joindre le serveur. Vérifiez la connexion puis réessayez.';
        inFlight.current = false;
        setState(previous => ({...previous,loading:false,data:null,error}));
      });
    return () => {current = false;controller.abort();};
  }, [functionId,kind,page,revision]);
  useEffect(() => {
    if (!state.loading && focusAfterPage.current) {focusAfterPage.current = false;heading.current?.focus();}
  }, [state]);
  function changePage(value) {
    if (inFlight.current) return;
    inFlight.current = true;focusAfterPage.current = true;setPage(value);
  }
  function refresh() {if (!inFlight.current) {inFlight.current = true;setRevision(value => value + 1);}}
  return <section className="panel" aria-labelledby={`observations-${kind}`}>
    <div className="section-heading"><h2 id={`observations-${kind}`} ref={heading} tabIndex={-1}>{title}</h2>
      <button onClick={refresh} aria-disabled={state.loading}><RefreshCw aria-hidden="true"/>{state.error ? 'Réessayer' : 'Actualiser'}</button></div>
    <div aria-busy={state.loading}>
      {state.loading ? <div className="loading" role="status">Chargement des {title.toLowerCase()}…<span/><span/><span/></div> : state.error ? <ErrorMessage error={state.error}/> : <>
        <p className="muted observation-summary" role="status">{state.total} {kind === 'instances' ? 'instance' : 'invocation'}{state.total > 1 ? 's' : ''} · Relevé du {stamp(state.loadedAt)}</p>
        {!state.data.items.length ? <p className="empty">{kind === 'instances' ? 'Aucune instance réservée.' : 'Aucune invocation enregistrée.'}</p> :
          <ul className="observation-list">{state.data.items.map(row => <li key={row.id}>{kind === 'instances' ? <Instance row={row}/> : <Invocation row={row}/>}</li>)}</ul>}
      </>}
    </div>
    {state.total > 0 && <nav className="pagination" aria-label={`Pagination des ${title.toLowerCase()}`}>
      <button aria-disabled={state.loading || page === 0} onClick={() => {if (page > 0) changePage(page - 1);}}><ChevronLeft aria-hidden="true"/>Précédente</button>
      <span>Page {page + 1} sur {Math.max(1,Math.min(maxPage + 1,Math.ceil(state.total / pageSize)))}</span>
      <button aria-disabled={state.loading || page >= maxPage || (page + 1) * pageSize >= state.total} onClick={() => {if (page < maxPage && (page + 1) * pageSize < state.total) changePage(page + 1);}}>Suivante<ChevronRight aria-hidden="true"/></button>
    </nav>}
  </section>;
}

function Instance({row}) {
  const metrics = row.metrics;
  return <article aria-label={`Instance ${row.id}`}>
    <div className="observation-heading"><h3 className="mono">{row.id}</h3><State value={row.state}/></div>
    <Facts values={[
      ['Hash du code',reference(row.code_hash)],['Révision interne',reference(row.revision_id)],['Création',stamp(row.created_at)],
      ['CPU alloué',`${number(row.cpu_nanos,1e9)} CPU`],['Mémoire allouée',`${number(row.memory_mib)} Mio`],
      ['Mémoire consommée',metrics?.memory_usage_bytes == null ? 'Indisponible' : `${number(metrics.memory_usage_bytes,1024 ** 2)} Mio`],
      ['Temps CPU cumulé',metrics?.cpu_usage_ns == null ? 'Indisponible' : `${number(metrics.cpu_usage_ns,1e9)} s`],
      ['PID actifs',number(metrics?.pids_current)],['Dernière utilisation',stamp(row.last_used_at)],
    ]}/>
    {row.metrics_error && <p className="muted observation-note">{row.metrics_error === 'instance_unavailable' ? 'Les mesures de cette instance ne sont pas disponibles.' : 'Les mesures Docker sont momentanément indisponibles.'}</p>}
    {row.error_code && <p className="observation-note">Diagnostic : <span className="mono">{row.error_code}</span></p>}
  </article>;
}

function Invocation({row}) {
  return <article aria-label={`Invocation ${row.id}`}>
    <div className="observation-heading"><h3 className="mono">{row.id}</h3><State value={row.state}/></div>
    <p className="muted">Reçue le {stamp(row.created_at)}{row.http_status != null && <> · HTTP {row.http_status}</>}</p>
    <details className="invocation-details"><summary>Détails et journal</summary><div className="stack">
      <Facts values={[
        ['Sélection demandée',row.requested_code_hash ? reference(row.requested_code_hash) : 'Cible par défaut'],
        ['Hash exécuté',reference(row.resolved_code_hash)],['Révision interne',reference(row.revision_id)],['Instance',reference(row.instance_id)],
        ['Mise en file',stamp(row.queued_at)],['Admission',stamp(row.admitted_at)],
        ['Envoi au runtime',stamp(row.dispatched_at)],['Fin',stamp(row.completed_at)],
        ['Démarrage du handler confirmé',row.handler_started === true ? 'Oui' : row.handler_started === false ? 'Non' : 'Non confirmé'],
        ...(row.error_code ? [['Diagnostic',<span className="mono">{row.error_code}</span>]] : []),
      ]}/>
      <div className="stack"><h4>Journal de l’invocation</h4>
        {row.logs_truncated && <p className="notice log-warning">Journal tronqué à la limite de collecte.</p>}
        {row.logs ? <pre className="invocation-log" tabIndex={0} aria-label={`Journal de ${row.id}`}>{row.logs}</pre> : <p className="muted">{activeStates.has(row.state) ? 'Journaux disponibles à la fin de l’invocation.' : 'Aucun journal collecté.'}</p>}
      </div>
    </div></details>
  </article>;
}
