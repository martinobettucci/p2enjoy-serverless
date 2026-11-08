// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
// Read the shared catalogue; copy feedback belongs only to the current observation.
import React, {useEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, Copy, RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge, ErrorMessage, Facts, Success} from './ui';

const size = 5;
const sourceErrors = {
  source_forbidden:'Lecture des domaines refusée.', source_missing:'Relevé des domaines absent.',
  invalid_source:'Relevé des domaines invalide.', incomplete_source:'Relevé des domaines incomplet.',
  source_changed:'Le relevé a changé pendant sa lecture.', source_limit:'Le relevé dépasse la limite de lecture.',
  conflicting_source:'Le relevé contient des domaines contradictoires.',
};
const stamp = value => new Date(value * 1000).toLocaleString('fr-FR');

function Address({entry}) {
  const [copied,setCopied] = useState(''), [error,setError] = useState(null), [busy,setBusy] = useState(false);
  const example = `curl --request ${entry.methods.includes('GET') ? 'GET' : entry.methods[0]} --header 'X-Serverless-Token: VOTRE_JETON' '${entry.url}'`;
  async function copy(value,label) {
    if (busy) return;
    setBusy(true);setCopied('');setError(null);
    try {await navigator.clipboard.writeText(value);setCopied(label);}
    catch {setError(new Error('Copie refusée. Sélectionnez et copiez le texte affiché.'));}
    finally {setBusy(false);}
  }
  return <div className="invocation-address">
    <p className="mono">{entry.methods.join(' · ')}</p><p className="mono invocation-url">{entry.url}</p>
    <div className="actions"><button disabled={busy} onClick={() => copy(entry.url,'Adresse copiée.')}><Copy aria-hidden="true"/>Copier l’adresse</button>
      <button disabled={busy} onClick={() => copy(example,'Exemple copié.')}><Copy aria-hidden="true"/>Copier l’exemple curl</button></div>
    <details className="invocation-details"><summary>Exemple curl</summary><pre className="invocation-log">{example}</pre></details>
    <Success>{copied}</Success><ErrorMessage error={error}/>
  </div>;
}

export function InvocationUrls({functionId}) {
  const [page,setPage] = useState(0), [revision,setRevision] = useState(0);
  const [state,setState] = useState({loading:true,data:null,error:null});
  const heading = useRef(null), inFlight = useRef(true), restoreFocus = useRef(false);
  useEffect(() => {
    let current = true;
    const controller = new AbortController();
    inFlight.current = true;
    setState({loading:true,data:null,error:null});
    api(`/api/functions/${functionId}/invocation-urls?limit=${size}&offset=${page * size}`,{signal:controller.signal})
      .then(data => {
        if (!current) return;
        const last = Math.max(0,Math.ceil(data.total / size) - 1);
        if (page > last) {setPage(last);return;}
        inFlight.current = false;setState({loading:false,data,error:null});
      }).catch(error => {
        if (!current) return;
        if (!error.status) error.message = 'Impossible de consulter les adresses. Vérifiez la connexion puis réessayez.';
        inFlight.current = false;setState({loading:false,data:null,error});
      });
    return () => {current=false;controller.abort();};
  },[functionId,page,revision]);
  useEffect(() => {
    if (!state.loading && restoreFocus.current) {restoreFocus.current=false;heading.current?.focus();}
  },[state]);
  function refresh() {
    if (inFlight.current) return;
    inFlight.current=true;restoreFocus.current=true;
    setState({loading:true,data:null,error:null});setRevision(value => value+1);
  }
  function changePage(value) {
    if (inFlight.current) return;
    inFlight.current=true;restoreFocus.current=true;
    setState({loading:true,data:null,error:null});setPage(value);
  }
  const data = state.data;
  return <section className="panel" aria-labelledby="invocation-urls-title">
    <div className="section-heading"><h2 id="invocation-urls-title" ref={heading} tabIndex={-1}>Adresses d’appel</h2>
      <button disabled={state.loading} onClick={refresh}><RefreshCw aria-hidden="true"/>Actualiser</button></div>
    <p><a href="/console/manual#adresses-d-appel">Consulter le manuel des adresses d’appel</a></p>
    {state.loading && <p className="empty" role="status">Consultation des adresses…</p>}
    <ErrorMessage error={state.error}/>
    {data && <>
      <Facts values={[
        ['Relevé des domaines',stamp(data.source.observed_at)],
        ['Révision appelée sans tag',data.revision_id ? <span className="mono">{data.revision_id}</span> : 'Aucune révision active'],
      ]}/>
      {data.source.state !== 'available' ? <div className="notice error" role="alert"><p>{sourceErrors[data.source.error_code] || 'Relevé des domaines indisponible.'} Actualisez ; si le problème persiste, contactez l’administrateur du SPARK.</p></div> : <>
        {data.function_state === 'draft' ? <p className="empty">Fonction brouillon : publiez une révision dans Code et révisions pour obtenir ses adresses.</p> :
          !data.total ? <p className="empty">Aucun domaine d’appel applicable. Demandez une route vers la passerelle à l’administrateur du SPARK, puis actualisez.</p> :
            <ul className="observation-list">{data.items.map(item => <li key={`${item.origin}-${data.revision_id}-${data.source.sha256}-${revision}`}>
              <div className="observation-heading"><h3>{item.domain}</h3><Badge>{item.transport === 'https' ? 'HTTPS déclaré' : 'HTTP déclaré'}</Badge></div>
              <p>Disponibilité non vérifiée</p>
              {item.urls.map(entry => <Address key={entry.url} entry={entry}/>)}</li>)}</ul>}
        {data.wildcards.length > 0 && <div className="observation-note"><h3>Domaines génériques</h3><p className="mono">{data.wildcards.join(' · ')}</p><p>Aucune adresse concrète déterminée.</p></div>}
        {data.function_state !== 'draft' && data.total > size && <nav className="pagination" aria-label="Domaines d’appel">
          <button disabled={state.loading || !page} onClick={() => changePage(page-1)}><ChevronLeft aria-hidden="true"/>Précédente</button>
          <span>Page {page+1} sur {Math.ceil(data.total / size)} · {data.total} domaines</span>
          <button disabled={state.loading || (page+1)*size >= data.total} onClick={() => changePage(page+1)}>Suivante<ChevronRight aria-hidden="true"/></button>
        </nav>}
      </>}
    </>}
  </section>;
}
