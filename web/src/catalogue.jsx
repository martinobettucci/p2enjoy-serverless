// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
// URL state, bounded selectors and read-only catalogue share this contract.
import React, {useEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, RefreshCw} from 'lucide-react';
import {api} from './api';
import {Badge, DialogForm, ErrorMessage, Field, Section} from './ui';

const size=25, maximumPage=Math.floor(2147483647/size)+1;
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const defaults={q:'',namespace_id:'',service_id:'',state:'',sort:'name_asc',page:1};
const sorts={name_asc:'Nom croissant',name_desc:'Nom décroissant',updated_desc:'Modification récente',updated_asc:'Modification ancienne'};

export function catalogueQuery(raw){
  if(raw.length>4096)throw new Error('Contexte du catalogue invalide.');
  const params=new URLSearchParams(raw),value={...defaults},seen=new Set();
  for(const [key,item] of params){
    if(!Object.hasOwn(defaults,key)||seen.has(key))throw new Error('Contexte du catalogue invalide.');
    seen.add(key);if(!item)continue;
    if(key==='q'){
      if([...item].length>200||/[\p{Cc}\p{Cf}\p{Cs}]/u.test(item))throw new Error('Recherche limitée à 200 caractères sans caractère de contrôle.');
      value.q=item.trim().replace(/\s+/gu,' ');if(value.q.split(' ').length>8)throw new Error('La recherche accepte au plus huit mots.');
    }else if(key==='namespace_id'||key==='service_id'){
      if(!uuid.test(item))throw new Error('Filtre du catalogue invalide.');value[key]=item;
    }else if(key==='state'){
      if(!['draft','published'].includes(item))throw new Error('État du catalogue invalide.');value.state=item;
    }else if(key==='sort'){
      if(!Object.hasOwn(sorts,item))throw new Error('Tri du catalogue invalide.');value.sort=item;
    }else if(key==='page'){
      if(!/^[0-9]+$/.test(item)||!Number.isSafeInteger(Number(item))||Number(item)<1||Number(item)>maximumPage)throw new Error('Page du catalogue invalide.');
      value.page=Number(item);
    }
  }
  const canonical=new URLSearchParams();
  for(const key of Object.keys(defaults))if(value[key]!==defaults[key])canonical.set(key,String(value[key]));
  return {value,query:canonical.toString()};
}

export function catalogueReturn(){
  const values=new URLSearchParams(location.search).getAll('catalogue');
  if(values.length!==1)return null;
  try{return '/console/functions'+(catalogueQuery(values[0]).query?'?'+catalogueQuery(values[0]).query:'');}catch{return null;}
}

export function withCatalogue(href){
  const target=catalogueReturn();
  if(!target)return href;
  const value=new URL(href,location.origin);value.searchParams.set('catalogue',target.split('?')[1]||'');
  return value.pathname+value.search;
}

function currentLocation(){
  try{return {...catalogueQuery(location.search.slice(1)),error:null,errorSource:null};}
  catch(error){return {value:{...defaults},query:'',error,errorSource:'url'};}
}

function useRead(url){
  const [revision,setRevision]=useState(0),[state,setState]=useState({key:null,loading:true});
  useEffect(()=>{
    if(!url){setState({key:null,loading:false});return;}
    let current=true;const controller=new AbortController();setState({key:url,loading:true});
    api(url,{signal:controller.signal}).then(data=>{if(current)setState({key:url,loading:false,data});}).catch(error=>{
      if(!current)return;if(!error.status)error.message='Impossible de joindre le serveur. Vérifiez la connexion puis réessayez.';
      setState({key:url,loading:false,error});
    });
    return()=>{current=false;controller.abort();};
  },[url,revision]);
  return {...(state.key===url?state:{loading:true}),reload:()=>{setState({key:url,loading:true});setRevision(v=>v+1);}};
}

function Pages({page,total,pageSize,change,label='Pagination des fonctions'}){
  const pages=Math.max(1,Math.ceil(total/pageSize));
  return <nav className="pagination" aria-label={label}>
    <button type="button" disabled={page<=1} onClick={()=>change(page-1)}><ChevronLeft aria-hidden="true"/>Précédente</button>
    <span>Page {page} sur {pages}</span>
    <button type="button" disabled={page>=pages} onClick={()=>change(page+1)}>Suivante<ChevronRight aria-hidden="true"/></button>
  </nav>;
}

function ParentChoices({kind,namespaceId,value,onChange}){
  const [search,setSearch]=useState(''),[query,setQuery]=useState(''),[page,setPage]=useState(1);
  const results=useRef(null),focusAfterPage=useRef(false);
  const title=kind==='namespaces'?'namespace':'service';
  useEffect(()=>{const timer=setTimeout(()=>{setQuery(search);setPage(1);},300);return()=>clearTimeout(timer);},[search]);
  const params=new URLSearchParams({q:query,limit:'5',offset:String((page-1)*5)});
  if(kind==='services'&&namespaceId)params.set('namespace_id',namespaceId);
  const resource=useRead('/api/catalogue/'+kind+'?'+params);
  useEffect(()=>{if(!resource.loading&&focusAfterPage.current){focusAfterPage.current=false;results.current?.focus();}},[resource.loading,resource.data,resource.error]);
  const changePage=value=>{focusAfterPage.current=true;results.current?.focus();setPage(value);};
  return <div className="stack catalogue-choice"><Field label={`Rechercher un ${title}`}><input type="search" maxLength={200} value={search} onChange={e=>setSearch(e.target.value)}/></Field>
    <label className="check"><input type="radio" name="catalogue-parent" checked={!value.id} onChange={()=>onChange({id:'',name:''})}/>{kind==='namespaces'?'Tous les namespaces':'Tous les services'}</label>
    <h3 tabIndex={-1} ref={results}>Résultats de recherche</h3>
    {resource.loading?<p role="status">Recherche des {kind==='namespaces'?'namespaces':'services'}…</p>:resource.error?<><ErrorMessage error={resource.error}/><button type="button" onClick={resource.reload}>Réessayer</button></>:<>
      <p role="status">{resource.data.total} {kind==='namespaces'?'namespace':'service'}{resource.data.total>1?'s':''}</p>
      {!resource.data.items.length?<p className="empty">Aucun résultat.</p>:<ul className="catalogue-options">{resource.data.items.map(row=><li key={row.id}><label className="check">
        <input type="radio" name="catalogue-parent" checked={value.id===row.id} onChange={()=>onChange(row)}/>
        <span>{row.name}{row.namespace_name&&<small>{row.namespace_name}</small>}</span>
      </label></li>)}</ul>}
      <Pages page={page} total={resource.data.total} pageSize={5} change={changePage} label={`Pagination des ${kind==='namespaces'?'namespaces':'services'}`}/>
    </>}
    {value.id&&<p className="muted">Choix : {value.name}{value.namespace_name?' · '+value.namespace_name:''}</p>}
  </div>;
}

export function FunctionCatalogue(){
  const [locationState,setLocationState]=useState(currentLocation),[search,setSearch]=useState(()=>currentLocation().value.q);
  const [picker,setPicker]=useState(null),[labels,setLabels]=useState({});
  const results=useRef(null),focusResults=useRef(false);
  const filters=locationState.value;
  const write=(value,{replace=false,focus=false}={})=>{
    let next;
    try{const params=new URLSearchParams();for(const [key,item] of Object.entries(value))if(item!==defaults[key])params.set(key,String(item));next={...catalogueQuery(params.toString()),error:null,errorSource:null};}
    catch(error){setLocationState(previous=>({...previous,error,errorSource:'search'}));return;}
    history[replace?'replaceState':'pushState'](null,'','/console/functions'+(next.query?'?'+next.query:''));
    focusResults.current=focus;setLocationState(next);
  };
  useEffect(()=>{
    const popped=()=>{const value=currentLocation();setLocationState(value);setSearch(value.value.q);};
    addEventListener('popstate',popped);return()=>removeEventListener('popstate',popped);
  },[]);
  useEffect(()=>{
    if(search===filters.q){if(locationState.errorSource==='search')setLocationState(previous=>({...previous,error:null,errorSource:null}));return;}
    const timer=setTimeout(()=>{
      try{
        const normalized=catalogueQuery(new URLSearchParams({q:search}).toString()).value.q;
        if(normalized===filters.q){if(locationState.errorSource==='search')setLocationState(previous=>({...previous,error:null,errorSource:null}));return;}
        write({...filters,q:normalized,page:1},{replace:true});
      }catch(error){setLocationState(previous=>({...previous,error,errorSource:'search'}));}
    },300);
    return()=>clearTimeout(timer);
  },[search,filters]);
  const params=new URLSearchParams({q:filters.q,sort:filters.sort,limit:String(size),offset:String((filters.page-1)*size)});
  for(const key of ['namespace_id','service_id','state'])if(filters[key])params.set(key,filters[key]);
  const resource=useRead(locationState.error?null:'/api/functions?'+params);
  useEffect(()=>{
    if(!resource.data)return;
    setLabels(resource.data.selected);
    const last=Math.max(1,Math.ceil(resource.data.total/size));
    if(filters.page>last){write({...filters,page:last},{replace:true,focus:true});return;}
    if(focusResults.current){focusResults.current=false;results.current?.focus();}
  },[resource.data]);
  const selected=resource.error?.status===401?{}:labels;
  const label=(kind)=>!filters[kind+'_id']?'Tous les '+(kind==='namespace'?'namespaces':'services'):
    selected[kind]?.id===filters[kind+'_id']?(selected[kind].available===false?(kind==='namespace'?'Namespace indisponible':'Service indisponible'):
      selected[kind].name+(selected[kind].namespace_name?' · '+selected[kind].namespace_name:'')):(kind==='namespace'?'Namespace sélectionné':'Service sélectionné');
  const active=Boolean(filters.q||filters.namespace_id||filters.service_id||filters.state);
  const functionHref=id=>'/console/functions/'+id+'?'+new URLSearchParams({catalogue:locationState.query});
  return <><div className="page-title"><div><h1>Fonctions</h1><p>Catalogue des fonctions de vos services.</p></div><a className="button" href="/console/namespaces">Organiser les namespaces</a></div>
    <Section title="Rechercher et filtrer"><div className="catalogue-search"><Field label="Rechercher une fonction"><input type="search" maxLength={200} value={search} onChange={e=>setSearch(e.target.value)} placeholder="Nom, service, namespace, handler ou identifiant"/></Field>
      <div className="form-grid"><Field label="État"><select value={filters.state} onChange={e=>write({...filters,state:e.target.value,page:1})}><option value="">Tous les états</option><option value="draft">Brouillon</option><option value="published">Déployée</option></select></Field>
        <Field label="Trier par"><select value={filters.sort} onChange={e=>write({...filters,sort:e.target.value,page:1})}>{Object.entries(sorts).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></Field></div>
      <div className="catalogue-filters">{['namespace','service'].map(kind=><div key={kind} className="field"><span>{kind==='namespace'?'Namespace':'Service'}</span><button type="button" aria-label={`Choisir un ${kind}`} onClick={()=>setPicker(kind)}>{label(kind)}</button></div>)}</div>
      {(active||locationState.error||filters.sort!=='name_asc')&&<button type="button" onClick={()=>{setSearch('');setLabels({});write({...defaults});}}>Réinitialiser les filtres</button>}
      <ErrorMessage error={locationState.error}/>
    </div></Section>
    <section className="panel" aria-labelledby="catalogue-results"><div className="section-heading"><h2 id="catalogue-results" ref={results} tabIndex={-1}>Résultats</h2>
      <button type="button" onClick={resource.reload} disabled={Boolean(locationState.error)}><RefreshCw aria-hidden="true"/>{resource.error?'Réessayer':'Actualiser'}</button></div>
      {!locationState.error&&<div aria-busy={resource.loading}>{resource.loading?<div className="loading" role="status">Recherche des fonctions…<span/><span/><span/></div>:resource.error?<ErrorMessage error={resource.error}/>:<>
        <p className="muted catalogue-total" role="status">{resource.data.total} fonction{resource.data.total>1?'s':''}{active?' correspondant aux filtres':''}</p>
        {!resource.data.items.length?<p className="empty">{active?'Aucune fonction ne correspond aux filtres.':'Aucune fonction. Créez un service et une fonction depuis Namespaces.'}</p>:<div className="table-scroll catalogue-scroll" role="region" aria-label="Résultats des fonctions" tabIndex={0}><table className="catalogue-table"><thead><tr><th>Fonction</th><th>Service</th><th>Namespace</th><th>Handler</th><th>État</th><th>Modification</th></tr></thead>
          <tbody>{resource.data.items.map(row=><tr key={row.id}><td><a href={functionHref(row.id)}>{row.name}</a></td><td><a href={'/console/services/'+row.service.id+'/functions'}>{row.service.name}</a></td><td><a href={'/console/namespaces/'+row.namespace.id}>{row.namespace.name}</a></td><td className="mono">{row.handler}</td><td><Badge tone={row.state==='published'?'success':'neutral'}>{row.state==='published'?'Déployée':'Brouillon'}</Badge></td><td><time dateTime={new Date(row.updated_at*1000).toISOString()}>{new Date(row.updated_at*1000).toLocaleString('fr-FR')}</time></td></tr>)}</tbody>
        </table></div>}
        <Pages page={filters.page} total={resource.data.total} pageSize={size} change={page=>write({...filters,page},{focus:true})}/>
      </>}</div>}
    </section>
    {picker&&<DialogForm key={picker} title={picker==='namespace'?'Namespace':'Service'} initial={!filters[picker+'_id']?{id:'',name:''}:selected[picker]?.id===filters[picker+'_id']?selected[picker]:{id:filters[picker+'_id'],name:label(picker)}} submitLabel="Appliquer" onClose={()=>setPicker(null)}
      onSubmit={value=>{setLabels(previous=>({...previous,[picker]:value}));write({...filters,[picker+'_id']:value.id,...(picker==='namespace'?{service_id:''}:{}),page:1});}}>
      {(value,setValue)=><ParentChoices kind={picker==='namespace'?'namespaces':'services'} namespaceId={filters.namespace_id} value={value} onChange={setValue}/>}
    </DialogForm>}
  </>;
}
