// @spec docs/BACKLOG.md#sls-020 | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md
import React, {useEffect, useId, useRef, useState} from 'react';
import {AlertCircle, Check, ChevronLeft, ChevronRight, X} from 'lucide-react';
import {api} from './api';

export function useResource(url) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState({loading: true});
  useEffect(() => {
    let current = true;
    setState({loading: true});
    api(url).then(data => {if (current) setState({data});})
      .catch(error => {if (current) setState({error});});
    return () => {current = false;};
  }, [url, revision]);
  return {...state, reload: () => setRevision(v => v + 1)};
}

export function ErrorMessage({error}) {
  if (!error) return null;
  return <div className="notice error" role="alert"><AlertCircle aria-hidden="true"/>
    <div><p>{error.message || String(error)}</p>
      {error.details?.length > 0 && <ul>{error.details.map((item, index) =>
        <li key={index}>{item.field.slice(1).join(' · ')} : {item.message}</li>)}</ul>}
      {error.status === 401 && <a href="/auth/login">Se reconnecter avec le SSO</a>}
    </div></div>;
}

export function Resource({resource, children}) {
  if (resource.loading) return <div className="loading" role="status">Chargement…<span/><span/><span/></div>;
  if (resource.error) return <><ErrorMessage error={resource.error}/><button type="button" onClick={resource.reload}>Réessayer</button></>;
  return children(resource.data);
}

export function Field({label, children, help}) {
  const id = useId();
  return <div className="field"><label htmlFor={id}>{label}</label>
    {React.cloneElement(children, {id, 'aria-describedby': help ? `${id}-help` : undefined})}
    {help && <small id={`${id}-help`}>{help}</small>}</div>;
}

export function Section({title, action, children}) {
  return <section className="panel"><div className="section-heading"><h2>{title}</h2>{action}</div>{children}</section>;
}

export function Badge({children, tone = 'neutral'}) {return <span className={`badge ${tone}`}>{children}</span>;}
export function Facts({values}) {return <dl className="facts">{values.map(([name, value]) =>
  <div key={name}><dt>{name}</dt><dd>{value}</dd></div>)}</dl>;}

export function Pagination({page, size, count, change}) {
  if (!page && count < size) return null;
  return <nav className="pagination" aria-label="Pagination">
    <button type="button" disabled={!page} onClick={() => change(page - 1)}><ChevronLeft aria-hidden="true"/>Précédente</button>
    <span>Page {page + 1}</span>
    <button type="button" disabled={count < size} onClick={() => change(page + 1)}>Suivante<ChevronRight aria-hidden="true"/></button>
  </nav>;
}

export function DialogForm({title, initial, submitLabel = 'Enregistrer', confirmationLabel = 'Confirmer la création', children, onSubmit, onClose, confirmation}) {
  const [value, setValue] = useState(initial);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [discard, setDiscard] = useState(false);
  const [review,setReview] = useState(false);
  const ref = useRef(null);
  const heading = useId();
  const origin = useRef(document.activeElement);
  const discardRef = useRef(null);
  const reviewRef = useRef(null);
  const previousPanel = useRef(false);
  const dirty = JSON.stringify(value) !== JSON.stringify(initial);
  useEffect(() => {
    ref.current.showModal();
    document.body.classList.add('dialog-open');
    (ref.current.querySelector('input:not([readonly]),textarea,select') || ref.current.querySelector('button'))?.focus();
    return () => {document.body.classList.remove('dialog-open'); origin.current?.focus();};
  }, []);
  useEffect(() => {
    if (discard) discardRef.current?.focus();
    else if (review) reviewRef.current?.focus();
    else if (previousPanel.current) ref.current.querySelector('input:not([readonly]),textarea,select')?.focus();
    previousPanel.current=discard || review;
  }, [discard,review]);
  function close() {if (!busy) {if (dirty) setDiscard(true); else onClose();}}
  async function submit(event,confirmed=false) {
    event?.preventDefault();
    if (busy || discard) return;
    if (confirmation && !confirmed) {setReview(true);return;}
    setBusy(true); setError(null);
    try {await onSubmit(value); onClose();}
    catch (err) {setError(err);setReview(false);}
    finally {setBusy(false);}
  }
  return <dialog ref={ref} aria-labelledby={heading} onCancel={event => {event.preventDefault(); close();}}>
    <form onSubmit={submit}>
      <div className="dialog-heading"><h2 id={heading}>{title}</h2><button type="button" onClick={close} aria-label="Fermer la fenêtre" disabled={busy}><X aria-hidden="true"/></button></div>
      <div className="form-content"><fieldset className="form-fields" disabled={busy || review}>{children(value, setValue)}</fieldset><ErrorMessage error={error}/></div>
      {discard ? <div className="confirm" role="group" aria-label="Abandon des modifications">
        <p>Abandonner les modifications non enregistrées ?</p><div className="actions">
          <button ref={discardRef} type="button" onClick={() => setDiscard(false)}>Continuer la saisie</button>
          <button className="danger" type="button" onClick={onClose}>Abandonner</button>
        </div></div> : review ? <div className="confirm" role="group" aria-label="Confirmation de l’opération">
          <p>{confirmation(value)}</p><div className="actions"><button ref={reviewRef} type="button" onClick={() => setReview(false)} disabled={busy}>Revenir à la saisie</button>
            <button className="primary" type="button" disabled={busy} onClick={() => submit(null,true)}>{busy ? 'Enregistrement…' : confirmationLabel}</button></div>
        </div> : <div className="dialog-actions"><button type="button" onClick={close} disabled={busy}>Annuler</button>
        <button className="primary" disabled={busy}>{busy ? 'Enregistrement…' : submitLabel}</button></div>}
    </form>
  </dialog>;
}

export function Confirm({label, message, action, name}) {
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const opener = useRef(null);
  const target = useRef(null);
  const explanation = useId();
  useEffect(() => {if (open) target.current?.focus();}, [open]);
  function cancel() {if (!busy) {setOpen(false); setTyped(''); setError(null); opener.current?.focus();}}
  async function run() {
    if (busy) return;
    setBusy(true); setError(null);
    try {await action(); setOpen(false); opener.current?.focus();}
    catch (err) {setError(err);}
    finally {setBusy(false);}
  }
  return <div className="confirmation"><button ref={opener} onClick={() => open ? cancel() : setOpen(true)} aria-expanded={open}>{label}</button>
    {open && <div className="confirm" onKeyDown={e => {if (e.key === 'Escape') {e.stopPropagation(); cancel();}}}>
      <p id={explanation}>{message}{name ? ` Saisissez exactement « ${name} » pour confirmer.` : ''}</p>{name && <Field label={`Saisir « ${name} » pour confirmer`}>
        <input ref={target} value={typed} onChange={e => setTyped(e.target.value)} autoComplete="off"/>
      </Field>}
      <ErrorMessage error={error}/><div className="actions"><button ref={name ? undefined : target} onClick={cancel} disabled={busy}>Annuler</button>
      <button className="danger" aria-describedby={explanation} onClick={run} disabled={busy || Boolean(name && typed !== name)}>{busy ? 'Traitement…' : label}</button></div>
    </div>}
  </div>;
}

export function Success({children}) {return children ? <div className="notice success" role="status"><Check aria-hidden="true"/><p>{children}</p></div> : null;}

export function NamedFields({value, setValue}) {
  return <><Field label="Nom"><input required maxLength={63} pattern="[a-z0-9][a-z0-9_-]*" value={value.name} onChange={e => setValue({...value, name:e.target.value})}/></Field>
    <Field label="Description"><textarea rows={3} maxLength={2000} value={value.description} onChange={e => setValue({...value, description:e.target.value})}/></Field></>;
}
