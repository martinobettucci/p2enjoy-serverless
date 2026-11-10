// @spec docs/DESIGN_SYSTEM.md | docs/BACKLOG.md#sls-020 | docs/CONTROL.md#gestion | docs/PLATFORM.md | docs/DESIGN_SYSTEM_APP.md
// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#parcours-et-adresses | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#console-et-manuel | docs/manual.md
import React, {useState} from 'react';
import {api} from './api';
import {Badge, Confirm, DialogForm, Facts, Field, Resource, Section, useResource} from './ui';
import {Configuration, url} from './management';
import {ExecutionObservations} from './observations';
import {CodePublications} from './publications';
import {FunctionStorage} from './storage';
// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
import {InvocationUrls} from './invocation-urls';
// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#facette-planifications | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#planifications-du-manifeste
import {FunctionSchedules} from './schedules';
// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#parcours-et-adresses | docs/DESIGN_SYSTEM_APP.md
import {catalogueReturn,withCatalogue} from './catalogue';

const limits = [
  ['memory_mib','Mémoire (Mio)',128,8192,1],
  ['timeout_seconds','Durée maximale d’invocation (s)',.1,86400,'any'],
  ['idle_seconds','Inactivité avant extinction (s)',0,86400,'any'],
  ['min_instances','Instances minimales',0,32,1],
  ['max_instances','Instances maximales',1,32,1],
  ['concurrency','Invocations simultanées',1,32,1],
  ['queue_timeout_seconds','Attente maximale en file (s)',0,300,'any'],
];

export function FunctionPage({id,tab}) {
  const resource = useResource(`/api/functions/${id}`);
  return <Resource resource={resource}>{row => <FunctionView row={row} tab={tab} reload={resource.reload}/>}</Resource>;
}

// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#console-et-domaine-canonique | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
function FunctionView({row:initialRow,tab,reload}) {
  const [row,setRow] = useState(initialRow);
  const active = ['code','storage','instances','invocations','invocation-urls','schedules'].includes(tab) ? tab : 'configuration';
  const [mode,setMode] = useState(null), config = row.config, storage = config.storage;
  async function update(change) {await api(`/api/functions/${row.id}`,{method:'PUT',headers:{'If-Match':String(row.updated_at)},body:{name:row.name,config,...change}}); reload();}
  return <>{catalogueReturn()&&<p className="catalogue-back"><a href={catalogueReturn()}>Revenir au catalogue</a></p>}
    <nav className="breadcrumb" aria-label="Fil d’Ariane"><a href="/console/namespaces">Namespaces</a><span>/</span><a href={url('services',row.service_id,'functions')}>Fonctions du service</a><span>/</span><span>{row.name}</span></nav>
    <div className="page-title"><h1>{row.name}</h1><Badge tone={row.active_revision_id ? 'success' : 'neutral'}>{row.active_revision_id ? 'Déployée' : 'Brouillon'}</Badge></div>
    <nav className="tabs" aria-label="Fonction">{Object.entries({configuration:'Configuration',code:'Code et révisions','invocation-urls':'Adresses d’appel',schedules:'Planifications',storage:'Stockage',instances:'Instances',invocations:'Invocations'}).map(([key,label]) => <a key={key} href={withCatalogue(url('functions',row.id,key === 'configuration' ? '' : key))} aria-current={active === key ? 'page' : undefined}>{label}</a>)}</nav>
    {active === 'schedules' ? <FunctionSchedules functionId={row.id}/> : active === 'invocation-urls' ? <InvocationUrls functionId={row.id}/> : active === 'code' ? <CodePublications functionId={row.id} onFunction={setRow}/> : active === 'storage' ? <FunctionStorage functionId={row.id}/> : active !== 'configuration' ? <ExecutionObservations key={active} functionId={row.id} kind={active}/> : <>
    <Section title="Identité" action={<button onClick={() => setMode('identity')}>Modifier l’identité</button>}>
      <Facts values={[
        ['Nom',row.name],['Runtime',config.runtime],['Handler',<span className="mono">{config.handler}</span>],['Identifiant stable',<span className="mono">{row.id}</span>],
      ]}/></Section>
    <Section title="Exécution" action={<button onClick={() => setMode('execution')}>Modifier l’exécution</button>}>
      <Facts values={[
        ['Mémoire allouée',`${config.memory_mib} Mio`],['Plafond CPU',`${config.cpu} CPU`],['Durée maximale d’invocation',`${config.timeout_seconds} s`],['Inactivité avant extinction',`${config.idle_seconds} s`],
        ['Instances minimales',config.min_instances],['Instances maximales',config.max_instances],['Invocations simultanées',config.concurrency],['Attente maximale en file',`${config.queue_timeout_seconds} s`],
      ]}/></Section>
    <Section title="Stockage" action={<button onClick={() => setMode('storage')}>Modifier le stockage</button>}>
      <Facts values={[
        ['Données permanentes',storage.data.enabled ? `${storage.data.quota_mib} Mio alloués` : 'Désactivées'],
        ['Cache reconstructible',storage.cache.enabled ? `${storage.cache.quota_mib} Mio alloués` : 'Désactivé'],
        ['Accès aux données',storage.concurrency === 'exclusive' ? 'Exclusif' : 'Partagé'],
      ]}/></Section>
    <Configuration row={row} endpoint={`/api/functions/${row.id}`} reload={reload} wrap={configuration => ({name:row.name,config,configuration})}/>
    <Section title="Gestion de la fonction"><Confirm label="Supprimer la fonction" message={`Supprimer « ${row.name} » et archiver ses données permanentes ?`}
      action={async () => {await api(`/api/functions/${row.id}`,{method:'DELETE'}); location.assign(catalogueReturn()||url('services',row.service_id,'functions'));}}/></Section>
    {mode === 'identity' && <DialogForm title="Identité" initial={{name:row.name,handler:config.handler}} onClose={() => setMode(null)}
      onSubmit={value => update({name:value.name,config:{...config,handler:value.handler}})}>
      {(value,setValue) => <><Field label="Nom"><input required pattern="[A-Za-z0-9][A-Za-z0-9_-]*" maxLength={63} value={value.name} onChange={e => setValue({...value,name:e.target.value})}/></Field>
        <Field label="Handler"><input required maxLength={256} value={value.handler} onChange={e => setValue({...value,handler:e.target.value})}/></Field></>}
    </DialogForm>}
    {mode === 'execution' && <DialogForm title="Exécution" initial={Object.fromEntries(['cpu',...limits.map(v => v[0])].map(key => [key,config[key]]))}
      onClose={() => setMode(null)} onSubmit={value => update({config:{...config,...Object.fromEntries(Object.entries(value).map(([key,v]) => [key,Number(v)]))}})}>
      {(value,setValue) => <><Field label="Plafond CPU" help="De 0,05 à 1 CPU par instance.">
        <input type="number" required min="0.05" max="1" step="any" value={value.cpu} onChange={e => setValue({...value,cpu:e.target.value})}/></Field>
        <div className="form-grid">{limits.map(([key,label,min,max,step]) => <Field key={key} label={label}><input type="number" required min={min} max={max} step={step} value={value[key]} onChange={e => setValue({...value,[key]:e.target.value})}/></Field>)}</div></>}
    </DialogForm>}
    {mode === 'storage' && <DialogForm title="Stockage" initial={storage} onClose={() => setMode(null)}
      onSubmit={value => update({config:{...config,storage:{...value,data:{...value.data,quota_mib:Number(value.data.quota_mib)},cache:{...value.cache,quota_mib:Number(value.cache.quota_mib)}}}})}>
      {(value,setValue) => <>{[['data','Données permanentes'],['cache','Cache reconstructible']].map(([key,label]) => <fieldset key={key}><legend>{label}</legend>
        <label className="check"><input type="checkbox" checked={value[key].enabled} onChange={e => setValue({...value,[key]:{...value[key],enabled:e.target.checked}})}/>Activer</label>
        <Field label="Allocation (Mio)"><input type="number" min={1} max={65536} step={1} required value={value[key].quota_mib} onChange={e => setValue({...value,[key]:{...value[key],quota_mib:e.target.value}})}/></Field>
      </fieldset>)}<Field label="Accès aux données"><select value={value.concurrency} onChange={e => setValue({...value,concurrency:e.target.value})}><option value="exclusive">Exclusif</option><option value="shared">Partagé</option></select></Field></>}
    </DialogForm>}
  </>}
  </>;
}
