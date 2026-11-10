// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#facette-planifications | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md#planifications-du-manifeste-sls-078 | docs/manual.md#planifications-du-manifeste
import React, {useEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge, ErrorMessage, Facts, Section} from './ui';
import {withCatalogue} from './catalogue';

const size = 5;
const states = {
  claimed:['Réclamé','brand'], dispatched:['Envoyé','brand'], succeeded:['Terminé','success'], failed:['Échec','danger'],
  skipped_downtime:['Ignoré pendant l’arrêt','neutral'], skipped_overlap:['Ignoré : tir précédent en cours','neutral'],
  refused_capacity:['Refusé : capacité indisponible','danger'], refused_changed:['Refusé : planification remplacée','neutral'],
  refused_unavailable:['Refusé : moteur indisponible','danger'],
};
const stamp = value => value == null ? 'Non observé' : new Date(value * 1000).toISOString().replace('T',' ').replace('.000Z',' UTC');
const code = value => <span className="mono">{value}</span>;
function State({value}) {
  const [label,tone] = states[value] || ['État inconnu','neutral'];
  return <Badge tone={tone}>{label}</Badge>;
}

export function FunctionSchedules({functionId}) {
  const [page,setPage] = useState(0), [revision,setRevision] = useState(0), [state,setState] = useState({loading:true,total:0});
  const heading = useRef(null), focusAfterPage = useRef(false), inFlight = useRef(true);
  useEffect(() => {
    const controller = new AbortController(); let current = true;
    inFlight.current = true;
    setState(previous => ({loading:true,total:previous.total}));
    async function load() {
      try {
        const declarations = await api(`/api/functions/${functionId}/schedules`,{signal:controller.signal});
        const history = await api(`/api/functions/${functionId}/schedule-firings?limit=${size}&offset=${page * size}`,{signal:controller.signal});
        if (!current) return;
        const last = Math.min(2000,Math.max(0,Math.ceil(history.total / size)-1));
        if (page > last) {setPage(last);return;}
        setState({loading:false,declarations,history,total:history.total});
      } catch (error) {
        if (current) setState(previous => ({loading:false,error,total:previous.total}));
      } finally {if (current) inFlight.current = false;}
    }
    load();
    return () => {current = false;controller.abort();};
  }, [functionId,page,revision]);
  useEffect(() => {
    if (!state.loading && focusAfterPage.current) {focusAfterPage.current = false;heading.current?.focus();}
  }, [state]);
  function refresh() {if (!inFlight.current) {inFlight.current = true;setRevision(value => value + 1);}}
  function change(value) {if (!inFlight.current) {inFlight.current = true;focusAfterPage.current = true;setPage(value);}}
  return <>
    <Section title="Planifications du manifeste" action={<button onClick={refresh} aria-disabled={state.loading}><RefreshCw aria-hidden="true"/>{state.error ? 'Réessayer' : 'Actualiser'}</button>}>
      <p><a href="/console/manual#planifications-du-manifeste">Fonctionnement des planifications</a></p>
      <div aria-busy={state.loading}>{state.loading ? <p role="status">Chargement des planifications…</p> : state.error ? <ErrorMessage error={state.error}/> :
        !state.declarations.items.length ? <p className="empty">Aucune planification dans la version promue.</p> :
        <ul className="observation-list">{state.declarations.items.map(row => <li key={row.index}><article aria-label={`Planification ${row.index + 1}`}>
          <div className="observation-heading"><h3>Planification {row.index + 1}</h3><Badge tone={row.enabled ? 'success' : 'neutral'}>{row.enabled ? 'Activée' : 'Désactivée'}</Badge></div>
          <Facts values={[
            ['Expression UTC',code(row.cron)],['Hash promu',code(row.code_hash)],['Activation',stamp(row.activated_at)],
            ['Prochain créneau nominal',row.enabled ? row.next ? stamp(row.next.nominal_at) : 'Aucun créneau calculable' : 'Planification désactivée'],
            ['Prochaine frontière de lancement',row.enabled ? row.next ? stamp(row.next.window_at) : 'Aucun créneau calculable' : 'Planification désactivée'],
            ['Dernier résultat',row.last_firing ? <State value={row.last_firing.state}/> : 'Aucun tir enregistré'],
          ]}/>
        </article></li>)}</ul>}
      </div>
    </Section>
    <Section title="Historique des tirs" headingRef={heading}>
      <div aria-busy={state.loading}>{state.loading ? <p role="status">Chargement des tirs…</p> : state.error ? <p className="muted">Historique indisponible.</p> : <>
        <p className="muted" role="status">{state.total} tir{state.total > 1 ? 's' : ''} enregistré{state.total > 1 ? 's' : ''}</p>
        {!state.history.items.length ? <p className="empty">Aucun tir enregistré.</p> : <ul className="observation-list">{state.history.items.map(row => <li key={row.id}><article aria-label={`Tir ${row.id}`}>
          <div className="observation-heading"><h3>{stamp(row.nominal_at)}</h3><State value={row.state}/></div>
          <Facts values={[
            ['Expression UTC',code(row.expression)],['Hash du code',code(row.code_hash)],['Frontière prévue',stamp(row.window_at)],
            ['Envoi',stamp(row.dispatched_at)],['Retard observé',row.delay_seconds == null ? 'Non mesuré' : `${row.delay_seconds.toFixed(3)} s`],
            ['Créneaux fusionnés',row.coalesced],['Fin',stamp(row.completed_at)],
            ['Invocation',row.invocation_id ? <a className="mono" href={withCatalogue(`/console/functions/${functionId}/invocations`)}>{row.invocation_id}</a> : 'Aucune invocation créée'],
            ...(row.error_code ? [['Diagnostic',code(row.error_code)]] : []),
          ]}/>
        </article></li>)}</ul>}
      </>}</div>
      {state.total > 0 && <nav className="pagination" aria-label="Pagination des tirs">
        <button aria-disabled={state.loading || page === 0} onClick={() => {if (page) change(page - 1);}}><ChevronLeft aria-hidden="true"/>Précédente</button>
        <span>Page {page + 1} sur {Math.max(1,Math.min(2001,Math.ceil(state.total / size)))}</span>
        <button aria-disabled={state.loading || page >= 2000 || (page + 1) * size >= state.total} onClick={() => {if (page < 2000 && (page + 1) * size < state.total) change(page + 1);}}>Suivante<ChevronRight aria-hidden="true"/></button>
      </nav>}
    </Section>
  </>;
}
