// @spec docs/DESIGN_SYSTEM.md | docs/BACKLOG.md#sls-020 | docs/CONTROL.md#gestion | docs/DESIGN_SYSTEM_APP.md
import React, {useState} from 'react';
import {Plus, Copy, KeyRound} from 'lucide-react';
import {api} from './api';
import {Badge, Confirm, DialogForm, ErrorMessage, Facts, Field, NamedFields, Pagination, Resource, Section, Success, useResource} from './ui';

const pageSize = 25;
export const url = (kind, id, tab = '') => `/console/${kind}/${id}${tab ? `/${tab}` : ''}`;
const rightsNames = {create:'Create — créer', read:'Read — lire et invoquer', update:'Update — modifier', delete:'Delete — supprimer'};
const stamp = value => value ? new Date(value * 1000).toLocaleString('fr-FR') : 'Jamais';

export function Namespaces() {
  const [page, setPage] = useState(0), [create, setCreate] = useState(false);
  const resource = useResource(`/api/namespaces?limit=${pageSize}&offset=${page * pageSize}`);
  return <><div className="page-title"><div><h1>Namespaces</h1><p>Vos espaces de services et de fonctions.</p></div>
    <button className="primary" onClick={() => setCreate(true)}><Plus aria-hidden="true"/>Créer un namespace</button></div>
    <Section title="Espaces"><Resource resource={resource}>{data => <>
      {!data.items.length ? <p className="empty">Aucun namespace.</p> : <ul className="entity-list">{data.items.map(row => <li key={row.id}><div>
        <a href={url('namespaces',row.id)}>{row.name}</a>{row.description && <p>{row.description}</p>}</div><Badge>Namespace</Badge></li>)}</ul>}
      <Pagination page={page} size={pageSize} count={data.items.length} change={setPage}/>
    </>}</Resource></Section>
    {create && <DialogForm title="Créer un namespace" initial={{name:'',description:''}} submitLabel="Créer" onClose={() => setCreate(false)}
      onSubmit={async data => {const row = await api('/api/namespaces',{method:'POST',body:data}); location.assign(url('namespaces',row.id));}}>
      {(value,setValue) => <NamedFields value={value} setValue={setValue}/>}</DialogForm>}
  </>;
}

export function Namespace({id}) {
  const resource = useResource(`/api/namespaces/${id}`);
  return <Resource resource={resource}>{row => <NamespaceView row={row} reload={resource.reload}/>}</Resource>;
}

function NamespaceView({row,reload}) {
  const [page, setPage] = useState(0), [mode,setMode] = useState(null);
  const services = useResource(`/api/namespaces/${row.id}/services?limit=${pageSize}&offset=${page * pageSize}`);
  return <><nav className="breadcrumb" aria-label="Fil d’Ariane"><a href="/">Namespaces</a><span>/</span><span>{row.name}</span></nav>
    <div className="page-title"><div><h1>{row.name}</h1>{row.description && <p>{row.description}</p>}</div><button onClick={() => setMode('edit')}>Modifier le namespace</button></div>
    <Section title="Services" action={<button className="primary" onClick={() => setMode('create')}><Plus aria-hidden="true"/>Créer un service</button>}>
      <Resource resource={services}>{data => <>{!data.items.length ? <p className="empty">Aucun service dans ce namespace.</p> :
        <ul className="entity-list">{data.items.map(service => <li key={service.id}><div><a href={url('services',service.id,'functions')}>{service.name}</a>{service.description && <p>{service.description}</p>}</div><Badge>Service</Badge></li>)}</ul>}
        <Pagination page={page} size={pageSize} count={data.items.length} change={setPage}/></>}</Resource>
    </Section>
    <Section title="Gestion du namespace"><Confirm label="Supprimer le namespace" message={`Supprimer « ${row.name} » ? Ses services doivent être supprimés au préalable.`}
      action={async () => {await api(`/api/namespaces/${row.id}`,{method:'DELETE'}); location.assign('/');}}/></Section>
    {mode && <DialogForm title={mode === 'edit' ? 'Modifier le namespace' : 'Créer un service'}
      initial={mode === 'edit' ? {name:row.name,description:row.description} : {name:'',description:''}} onClose={() => setMode(null)}
      onSubmit={async value => {if (mode === 'edit') {await api(`/api/namespaces/${row.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:value}); reload();}
        else {const service = await api(`/api/namespaces/${row.id}/services`,{method:'POST',body:value}); location.assign(url('services',service.id,'functions'));}}}>
      {(value,setValue) => <NamedFields value={value} setValue={setValue}/>}</DialogForm>}
  </>;
}

export function Service({id,tab}) {
  const resource = useResource(`/api/services/${id}`);
  return <Resource resource={resource}>{row => <ServiceView row={row} tab={tab} reload={resource.reload}/>}</Resource>;
}

function ServiceView({row,tab,reload}) {
  const [edit,setEdit] = useState(false);
  const tabs = {functions:'Fonctions',configuration:'Configuration',tokens:'Jetons',activity:'Activité'};
  const active = tabs[tab] ? tab : 'functions';
  return <><nav className="breadcrumb" aria-label="Fil d’Ariane"><a href="/">Namespaces</a><span>/</span><a href={url('namespaces',row.namespace_id)}>Services du namespace</a><span>/</span><span>{row.name}</span></nav>
    <div className="page-title"><div><h1>{row.name}</h1>{row.description && <p>{row.description}</p>}</div><button onClick={() => setEdit(true)}>Modifier le service</button></div>
    <nav className="tabs" aria-label="Service">{Object.entries(tabs).map(([key,label]) => <a key={key} href={url('services',row.id,key)} aria-current={active === key ? 'page' : undefined}>{label}</a>)}</nav>
    {active === 'functions' && <Functions service={row}/>}
    {active === 'configuration' && <><Configuration row={row} endpoint={`/api/services/${row.id}/configuration`} reload={reload}/><Policy row={row} reload={reload}/>
      <Section title="Gestion du service"><Confirm label="Supprimer le service" message={`Supprimer « ${row.name} » et révoquer ses jetons ? Le service doit être vide de fonctions.`}
        action={async () => {await api(`/api/services/${row.id}`,{method:'DELETE'}); location.assign(url('namespaces',row.namespace_id));}}/></Section></>}
    {active === 'tokens' && <Tokens service={row}/>}
    {active === 'activity' && <Activity service={row}/>}
    {edit && <DialogForm title="Modifier le service" initial={{name:row.name,description:row.description}} onClose={() => setEdit(false)}
      onSubmit={async value => {await api(`/api/services/${row.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{...value,policy:row.policy}}); reload();}}>
      {(value,setValue) => <NamedFields value={value} setValue={setValue}/>}</DialogForm>}
  </>;
}

function Functions({service}) {
  const [page,setPage] = useState(0), [create,setCreate] = useState(false);
  const resource = useResource(`/api/services/${service.id}/functions?limit=${pageSize}&offset=${page * pageSize}`);
  return <><Section title="Fonctions" action={<button className="primary" onClick={() => setCreate(true)}><Plus aria-hidden="true"/>Créer une fonction</button>}>
    <Resource resource={resource}>{data => <>{!data.items.length ? <p className="empty">Aucune fonction dans ce service.</p> : <ul className="entity-list">{data.items.map(row =>
      <li key={row.id}><div><a href={url('functions',row.id)}>{row.name}</a><p className="mono">{row.config.handler}</p>
        {/* @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique | docs/DESIGN_SYSTEM_APP.md | docs/manual.md */}
        <a href={url('functions',row.id,'invocation-urls')} aria-label={`Adresses d’appel de ${row.name}`}>Adresses d’appel</a>
      </div><Badge tone={row.active_revision_id ? 'success' : 'neutral'}>{row.active_revision_id ? 'Déployée' : 'Brouillon'}</Badge></li>)}</ul>}
      <Pagination page={page} size={pageSize} count={data.items.length} change={setPage}/></>}</Resource></Section>
    {create && <DialogForm title="Créer une fonction" initial={{name:'',handler:'handler.handler'}} submitLabel="Créer" onClose={() => setCreate(false)}
      onSubmit={async value => {const row = await api(`/api/services/${service.id}/functions`,{method:'POST',body:{name:value.name,config:{handler:value.handler}}}); location.assign(url('functions',row.id));}}>
      {(value,setValue) => <><Field label="Nom"><input required pattern="[A-Za-z0-9][A-Za-z0-9_-]*" maxLength={63} value={value.name} onChange={e => setValue({...value,name:e.target.value})}/></Field>
        <Field label="Handler"><input required value={value.handler} onChange={e => setValue({...value,handler:e.target.value})}/></Field></>}
    </DialogForm>}
  </>;
}

function KeyEditor({rows,setRows,secret = false}) {
  function change(index,key,value) {setRows(rows.map((row,i) => i === index ? {...row,[key]:value} : row));}
  return <div className="stack">{rows.map((row,index) => <div className="key-row" key={row.key}>
    <Field label={`Nom ${index + 1}`}><input required pattern="[A-Za-z_][A-Za-z0-9_]*" maxLength={128} value={row.name} onChange={e => change(index,'name',e.target.value)}/></Field>
    <Field label={`Valeur ${index + 1}`}><input type={secret ? 'password' : 'text'} autoComplete={secret ? 'new-password' : 'off'} value={row.value} onChange={e => change(index,'value',e.target.value)}/></Field>
    <button type="button" aria-label={`Retirer la ligne ${index + 1}`} onClick={() => setRows(rows.filter((_,i) => i !== index))}>Retirer</button>
  </div>)}<button type="button" onClick={() => setRows([...rows,{key:crypto.randomUUID(),name:'',value:''}])}>Ajouter une ligne</button></div>;
}

function mapping(rows) {
  const names = rows.map(r => r.name);
  if (new Set(names).size !== names.length) throw new Error('Chaque nom doit être unique.');
  return Object.fromEntries(rows.map(r => [r.name,r.value]));
}

export function Configuration({row,endpoint,reload,wrap = value => value}) {
  const [mode,setMode] = useState(null), [saved,setSaved] = useState('');
  async function write(value) {await api(endpoint,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:wrap(value)}); setSaved('Configuration enregistrée.'); reload();}
  return <><Success>{saved}</Success><Section title="Variables" action={<button onClick={() => setMode('environment')}>Modifier les variables</button>}>
    {!Object.keys(row.environment).length ? <p className="empty">Aucune variable à ce niveau.</p> : <Facts values={Object.entries(row.environment).map(([name,value]) => [name,<span className="mono">{value || 'Chaîne vide'}</span>])}/>}</Section>
    <Section title="Secrets" action={<button onClick={() => setMode('secrets')}>Ajouter ou remplacer des secrets</button>}>
      {!row.secret_names.length ? <p className="empty">Aucun secret à ce niveau.</p> : <ul className="entity-list">{row.secret_names.map(name => <li key={name}><span className="mono">{name}</span>
        <Confirm label={`Retirer ${name}`} message={`Retirer le secret « ${name} » de cette configuration ?`} action={() => write({secrets:{[name]:null}})}/></li>)}</ul>}</Section>
    {mode && <DialogForm title={mode === 'environment' ? 'Variables' : 'Secrets'}
      initial={{rows:mode === 'environment' ? Object.entries(row.environment).map(([name,value]) => ({key:name,name,value})) : [{key:'new',name:'',value:''}]}}
      onClose={() => setMode(null)} onSubmit={value => write({[mode]:mapping(value.rows)})}>
      {(value,setValue) => <KeyEditor rows={value.rows} setRows={rows => setValue({rows})} secret={mode === 'secrets'}/>}
    </DialogForm>}
  </>;
}

function Policy({row,reload}) {
  const [edit,setEdit] = useState(false), policy = row.policy;
  return <><Section title="Origines et adresses IP" action={<button onClick={() => setEdit(true)}>Modifier la politique</button>}>
    <Facts values={[
      ['Origines',policy.origins.length ? policy.origins.join(', ') : 'Aucune restriction d’origine'],
      ['Adresses et réseaux',policy.ips.length ? policy.ips.join(', ') : 'Aucune restriction IP'],
      ['Combinaison',policy.combination === 'and' ? 'Origine ET adresse IP' : 'Origine OU adresse IP'],
    ]}/></Section>
    {edit && <DialogForm title="Origines et adresses IP" initial={{origins:policy.origins.join('\n'),ips:policy.ips.join('\n'),combination:policy.combination}} onClose={() => setEdit(false)}
      onSubmit={async value => {const lines = text => text.split('\n').map(v => v.trim()).filter(Boolean);
        await api(`/api/services/${row.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,description:row.description,policy:{origins:lines(value.origins),ips:lines(value.ips),combination:value.combination}}}); reload();}}>
      {(value,setValue) => <><Field label="Origines autorisées" help="Une origine par ligne, par exemple https://app.exemple.fr."><textarea rows={4} value={value.origins} onChange={e => setValue({...value,origins:e.target.value})}/></Field>
        <Field label="Adresses IP ou réseaux CIDR" help="Une adresse ou un réseau par ligne."><textarea rows={4} value={value.ips} onChange={e => setValue({...value,ips:e.target.value})}/></Field>
        <Field label="Combinaison des restrictions"><select value={value.combination} onChange={e => setValue({...value,combination:e.target.value})}><option value="and">Origine ET adresse IP</option><option value="or">Origine OU adresse IP</option></select></Field></>}
    </DialogForm>}
  </>;
}

function Tokens({service}) {
  const [create,setCreate] = useState(false), [fresh,setFresh] = useState([]), [copied,setCopied] = useState(null), [copyError,setCopyError] = useState(null);
  const [page,setPage] = useState(0);
  const resource = useResource(`/api/services/${service.id}/tokens?limit=${pageSize}&offset=${page * pageSize}`);
  function created(data) {setFresh(previous => [data,...previous]); setCopied(null); setCopyError(null); resource.reload();}
  return <>{fresh.map(token => <Section key={token.id} title={`Jeton « ${token.name} »`}>
    <div className="stack"><Field label={`Valeur de ${token.name}`} help="Valeur générée par la plateforme, disponible une seule fois."><input className="mono" readOnly value={token.token}/></Field>
    <div className="actions"><button onClick={async () => {try {await navigator.clipboard.writeText(token.token); setCopied(token.id);} catch {setCopyError(new Error('Copie impossible. Sélectionnez la valeur pour la copier.'));}}}><Copy aria-hidden="true"/>Copier</button>
      <button onClick={() => setFresh(previous => previous.filter(row => row.id !== token.id))}>Fermer la valeur</button></div><Success>{copied === token.id ? 'Jeton copié.' : ''}</Success><ErrorMessage error={copyError}/></div></Section>)}
    <Section title="Jetons du service" action={<button className="primary" onClick={() => setCreate(true)}><KeyRound aria-hidden="true"/>Créer un jeton</button>}>
      <Resource resource={resource}>{data => <>{!data.items.length ? <p className="empty">Aucun jeton dans ce service.</p> : <ul className="entity-list">{data.items.map(token => {
        const active = !token.revoked_at && (!token.expires_at || token.expires_at > Date.now()/1000);
        return <li key={token.id}><div className="stack"><div><h3>{token.name}</h3><p className="mono">{token.prefix}…</p></div>
          <Facts values={[
            ['Droits',token.rights.map(r => rightsNames[r]).join(', ')], ['Portée',token.function_ids ? `${token.function_ids.length} fonction(s)` : 'Toutes les fonctions du service'],
            ['Expiration',token.expires_at ? stamp(token.expires_at) : 'Sans expiration'], ['Dernier usage',stamp(token.last_used_at)],
          ]}/>{active && <div className="actions"><Confirm label="Révoquer" name={token.name} message={`Révoquer immédiatement le jeton « ${token.name} » ?`}
            action={async () => {await api(`/api/tokens/${token.id}/revoke`,{method:'POST'}); setFresh(previous => previous.filter(row => row.id !== token.id)); resource.reload();}}/>
            <Confirm label="Renouveler" name={token.name} message={`Renouveler « ${token.name} » ? Sa valeur actuelle sera immédiatement révoquée.`}
              action={async () => created(await api(`/api/tokens/${token.id}/rotate`,{method:'POST'}))}/></div>}</div>
          <Badge tone={active ? 'success' : 'neutral'}>{token.revoked_at ? 'Révoqué' : active ? 'Actif' : 'Expiré'}</Badge></li>;
      })}</ul>}<Pagination page={page} size={pageSize} count={data.items.length} change={setPage}/></>}</Resource>
    </Section>
    {create && <TokenForm service={service} onClose={() => setCreate(false)} onCreated={created}/>}
  </>;
}

function TokenForm({service,onClose,onCreated}) {
  const [page,setPage] = useState(0);
  const functions = useResource(`/api/services/${service.id}/functions?limit=${pageSize}&offset=${page * pageSize}`);
  return <DialogForm title="Créer un jeton" initial={{name:'',rights:['read'],scope:'all',function_ids:[],expires:''}} submitLabel="Créer le jeton" onClose={onClose}
    confirmation={value => `Créer « ${value.name} » sur le service « ${service.name} », avec les droits ${value.rights.map(r => rightsNames[r]).join(', ')} et une portée sur ${value.scope === 'all' ? 'toutes ses fonctions' : `${value.function_ids.length} fonction(s) sélectionnée(s)`} ?`}
    onSubmit={async value => {if (value.scope === 'selected' && !value.function_ids.length) throw new Error('Sélectionnez au moins une fonction.');
      onCreated(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:value.name,rights:value.rights,function_ids:value.scope === 'all' ? null : value.function_ids,
        expires_at:value.expires ? new Date(value.expires).getTime()/1000 : null}}));}}>
    {(value,setValue) => <><Field label="Nom du jeton"><input required maxLength={100} value={value.name} onChange={e => setValue({...value,name:e.target.value})}/></Field>
      <fieldset><legend>Droits</legend>{Object.entries(rightsNames).map(([right,label]) => <label className="check" key={right}><input type="checkbox" checked={value.rights.includes(right)} onChange={e => setValue({...value,rights:e.target.checked ? [...value.rights,right] : value.rights.filter(r => r !== right)})}/>{label}</label>)}</fieldset>
      <Field label="Portée"><select value={value.scope} onChange={e => setValue({...value,scope:e.target.value})}><option value="all">Toutes les fonctions du service</option><option value="selected">Fonctions sélectionnées</option></select></Field>
      {value.scope === 'selected' && <Resource resource={functions}>{data => <>{data.items.length ? <fieldset><legend>Fonctions autorisées — {value.function_ids.length} sélectionnée(s)</legend>{data.items.map(row => <label className="check" key={row.id}><input type="checkbox" checked={value.function_ids.includes(row.id)}
        onChange={e => setValue({...value,function_ids:e.target.checked ? [...value.function_ids,row.id] : value.function_ids.filter(id => id !== row.id)})}/>{row.name}</label>)}</fieldset> : <p>Aucune fonction disponible.</p>}
        <Pagination page={page} size={pageSize} count={data.items.length} change={setPage}/></>}</Resource>}
      <Field label="Expiration (heure locale)" help="Laisser vide pour un jeton sans expiration."><input type="datetime-local" value={value.expires} onChange={e => setValue({...value,expires:e.target.value})}/></Field>
    </>}
  </DialogForm>;
}

function Activity({service}) {
  const [page,setPage] = useState(0);
  const resource = useResource(`/api/services/${service.id}/audit?limit=${pageSize}&offset=${page * pageSize}`);
  return <Section title="Activité du service"><Resource resource={resource}>{data => <>{!data.items.length ? <p className="empty">Aucun événement.</p> :
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Journal d’activité"><table><thead><tr><th>Date</th><th>Événement</th><th>Acteur</th><th>Objet</th></tr></thead><tbody>{data.items.map(row =>
      <tr key={row.id}><td className="mono">{stamp(row.created_at)}</td><td>{row.action}</td><td>{row.actor_kind === 'admin' ? 'Administrateur' : 'Jeton'}<p className="mono">{row.actor_id}</p></td><td className="mono">{row.object_id}</td></tr>)}</tbody></table></div>}
    <Pagination page={page} size={pageSize} count={data.items.length} change={setPage}/></>}</Resource></Section>;
}
