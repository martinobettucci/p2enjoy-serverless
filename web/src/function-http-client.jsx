// @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md#app-ds-002--composition-de-requête-http | docs/manual.md#tester-une-fonction
// Ephemeral HTTP workspace: no request, credential or result is persisted.
import React,{useEffect,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight,Copy,Download,Plus,RefreshCw,Send,Square,Trash2} from 'lucide-react';
import {api} from './api';
import {Badge,Confirm,DialogForm,ErrorMessage,Facts,Field,Section,Success} from './ui';
import {withCatalogue} from './catalogue';
import {registerNavigationGuard} from './navigation-guard';

const requestLimit=1024**2,responseLimit=6*1024**2,previewLimit=64*1024,pageSize=5;
const reservedHeaders=new Set(['connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade','content-length','host','x-serverless-request-id','cookie','cookie2','x-csrf-token','x-serverless-token','x-request-id','x-serverless-code-hash','accept-encoding','forwarded','x-real-ip','x-forwarded-for','x-forwarded-host','x-forwarded-proto','access-control-request-method','access-control-request-headers']);
const encoder=new TextEncoder(),blank=()=>({name:'',value:''});
const cleanPairs=pairs=>pairs.filter(v=>v.name!==''||v.value!=='');
const stamp=value=>new Date(value*1000).toLocaleString('fr-FR');
const bytes=value=>new Intl.NumberFormat('fr-FR').format(value)+' octets';
function base64(raw){let binary='';for(let n=0;n<raw.length;n+=32768)binary+=String.fromCharCode(...raw.subarray(n,n+32768));return btoa(binary);}
function unbase64(value){if(typeof value!=='string'||value.length>4*Math.ceil(responseLimit/3))throw new Error('Réponse hors limite.');const binary=atob(value);const raw=Uint8Array.from(binary,c=>c.charCodeAt(0));if(raw.length>responseLimit)throw new Error('Réponse hors limite.');return raw;}
function invocationPath(functionId,version,path){return '/invoke/'+functionId+(version===null?'':'@'+version)+(path?'/'+path:'');}
function exactUrl(origin,functionId,version,path,query){const url=new URL(origin+invocationPath(functionId,version,path));url.search=new URLSearchParams(cleanPairs(query).map(v=>[v.name,v.value])).toString();return url.href;}
const shell=value=>"'"+value.replaceAll("'","'\\''")+"'";

function PairFields({title,pairs,setPairs,limit,sensitive=false}){
 return <fieldset className="tester-pairs"><legend>{title}</legend><div className="stack">
  {pairs.map((pair,index)=><div className="tester-pair" key={index}>
   <Field label={`Nom ${title.toLowerCase()} ${index+1}`}><input value={pair.name} maxLength={sensitive?128:8192} autoComplete="off" spellCheck={false} onChange={e=>setPairs(pairs.map((v,n)=>n===index?{...v,name:e.target.value}:v))}/></Field>
   <Field label={`Valeur ${title.toLowerCase()} ${index+1}`}><input type={sensitive&&/authorization|token|secret|key/i.test(pair.name)?'password':'text'} value={pair.value} maxLength={8192} autoComplete="off" spellCheck={false} onChange={e=>setPairs(pairs.map((v,n)=>n===index?{...v,value:e.target.value}:v))}/></Field>
   <button type="button" aria-label={`Retirer ${title.toLowerCase()} ${index+1}`} onClick={()=>setPairs(pairs.filter((_,n)=>n!==index))}><Trash2 aria-hidden="true"/>Retirer</button>
  </div>)}
  <button type="button" disabled={pairs.length>=limit} onClick={()=>setPairs([...pairs,blank()])}><Plus aria-hidden="true"/>Ajouter {title==='Paramètres'?'un paramètre':'un en-tête'}</button>
 </div></fieldset>;
}

function VersionChoice({functionId,onClose,choose}){
 const [page,setPage]=useState(0),[selected,setSelected]=useState('default'),[revision,setRevision]=useState(0),[state,setState]=useState({loading:true});
 const heading=useRef(null),focus=useRef(false);
 useEffect(()=>{let current=true;const controller=new AbortController();setState({loading:true});
  api(`/api/functions/${functionId}/versions?limit=${pageSize}&offset=${page*pageSize}`,{signal:controller.signal})
   .then(data=>{if(current)setState({data});})
   .catch(error=>{if(current)setState({error:new Error(error.status?error.message:'Lecture des versions indisponible. Réessayez.')});});
  return()=>{current=false;controller.abort();};
 },[functionId,page,revision]);
 useEffect(()=>{if(!state.loading&&focus.current){focus.current=false;heading.current?.focus();}},[state]);
 return <DialogForm title="Version à tester" initial={{}} submitLabel="Utiliser cette version" onClose={onClose} onSubmit={()=>choose(selected==='default'?null:selected)}>
  {()=> <><label className="check"><input type="radio" name="tester-version" checked={selected==='default'} onChange={()=>setSelected('default')}/>Cible promue courante</label>
   <h3 ref={heading} tabIndex={-1}>Versions de la fonction</h3>
   {state.loading?<p role="status">Lecture des versions…</p>:state.error?<><ErrorMessage error={state.error}/><button type="button" onClick={()=>setRevision(v=>v+1)}>Réessayer</button></>:<>
    {!state.data.total?<p className="empty">Aucune version publiée.</p>:<ul className="editor-source-options">{state.data.items.map(row=><li key={row.code_hash}><label className="check">
     <input type="radio" name="tester-version" checked={selected===row.code_hash} disabled={row.state!=='available'||!row.stored_bytes} onChange={()=>setSelected(row.code_hash)}/>
     <span><span className="mono">{row.code_hash}</span><small>{row.state==='available'?'Disponible':row.state==='archived'?'Archivée':'Supprimée'}{row.active?' · Cible promue':''}</small></span>
    </label></li>)}</ul>}
    {state.data.total>0&&<nav className="pagination" aria-label="Pagination des versions à tester"><button type="button" disabled={!page} onClick={()=>{focus.current=true;setPage(v=>v-1);}}><ChevronLeft aria-hidden="true"/>Précédente</button><span>Page {page+1} sur {Math.max(1,Math.ceil(state.data.total/pageSize))}</span><button type="button" disabled={(page+1)*pageSize>=state.data.total} onClick={()=>{focus.current=true;setPage(v=>v+1);}}>Suivante<ChevronRight aria-hidden="true"/></button></nav>}
   </>}
  </>}
 </DialogForm>;
}

async function browserInvoke(url,data,signal){
 const headers=new Headers(data.headers.map(v=>[v.name,v.value]));headers.set('X-Serverless-Token',data.token);
 const response=await fetch(url,{method:data.method,headers,body:['GET','HEAD'].includes(data.method)?undefined:Uint8Array.from(atob(data.body_base64),c=>c.charCodeAt(0)),
  credentials:'omit',redirect:'manual',mode:'cors',cache:'no-store',referrerPolicy:'no-referrer',signal});
 if(response.type==='opaqueredirect'||response.type==='opaque')return {state:'unconfirmed',error:response.type==='opaqueredirect'?'redirect_hidden':'cors_unreadable',status:null};
 const reader=response.body?.getReader(),blocks=[];let length=0,truncated=false;
 try{if(reader){while(true){const next=await reader.read();if(next.done)break;const room=responseLimit-length,part=next.value.subarray(0,room);blocks.push(part);length+=part.length;if(next.value.length>room){truncated=true;break;}}}}
 finally{if(reader){await reader.cancel().catch(()=>{});reader.releaseLock();}}
 const raw=new Uint8Array(length);let at=0;for(const block of blocks){raw.set(block,at);at+=block.length;}
 const returned=[];let headerBytes=0,headersTruncated=false;
 for(const [name,value]of response.headers){if(returned.length>=128||headerBytes+encoder.encode(name+value).length>32768){headersTruncated=true;break;}returned.push({name,value});headerBytes+=encoder.encode(name+value).length;}
 return {state:'response',status:response.status,headers:returned,body_base64:base64(raw),body_bytes:raw.length,body_truncated:truncated,headers_truncated:headersTruncated,
  request_id:response.headers.get('X-Serverless-Request-ID'),code_hash:response.headers.get('X-Serverless-Code-Hash'),body_representation:'browser-decoded'};
}

export function FunctionHttpTester({functionId,functionName}){
 const initial=useRef(new URLSearchParams(location.search));
 const [version,setVersion]=useState(()=>{const all=initial.current.getAll('version');return all.length?(all.length===1?all[0]:'invalid'):null;});
 const [page,setPage]=useState(0),[revision,setRevision]=useState(0),[catalogue,setCatalogue]=useState({loading:true});
 const [origin,setOrigin]=useState(''),[path,setPath]=useState(''),[method,setMethod]=useState('GET'),[query,setQuery]=useState([blank()]),[headers,setHeaders]=useState([]);
 const [context,setContext]=useState('server'),[declaredOrigin,setDeclaredOrigin]=useState(location.origin),[bodyKind,setBodyKind]=useState('none'),[text,setText]=useState(''),[file,setFile]=useState(null),[fileReading,setFileReading]=useState(false);
 const [token,setToken]=useState(''),[temporary,setTemporary]=useState(null),[tokenBusy,setTokenBusy]=useState(false),[tokenNotice,setTokenNotice]=useState('');
 const [wait,setWait]=useState(30),[busy,setBusy]=useState(false),[result,setResult]=useState(null),[error,setError]=useState(null),[notice,setNotice]=useState(''),[dialog,setDialog]=useState(false);
 const mounted=useRef(true),request=useRef(null),fileGeneration=useRef(0),resultHeading=useRef(null),destinationHeading=useRef(null),accessHeading=useRef(null),focusCatalogue=useRef(false);
 useEffect(()=>{mounted.current=true;const onUnload=e=>{if(request.current){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',onUnload);
  const unregister=registerNavigationGuard(async()=>!request.current||window.confirm('Arrêter l’attente et quitter le testeur ? Le handler déjà admis peut continuer.'));
  return()=>{mounted.current=false;fileGeneration.current++;request.current?.abort();unregister();window.removeEventListener('beforeunload',onUnload);};
 },[]);
 useEffect(()=>{let current=true;const controller=new AbortController();setCatalogue({loading:true});setOrigin('');setResult(null);setNotice('');
  api(`/api/functions/${functionId}/invocation-urls?limit=${pageSize}&offset=${page*pageSize}${version===null?'':'&version='+encodeURIComponent(version)}`,{signal:controller.signal}).then(data=>{
   if(!current)return;const last=Math.max(0,Math.ceil(data.total/pageSize)-1);if(page>last){setPage(last);return;}
   if(data.source.state!=='available')throw new Error('Le catalogue des domaines est indisponible. Réessayez sa lecture.');
   setCatalogue({data});setOrigin(data.items[0]?.origin||'');
  }).catch(error=>{if(current)setCatalogue({error:new Error(error.status===404?'La version demandée est inconnue, archivée ou supprimée. Choisissez une version disponible.':error.status?error.message:'Impossible de lire les domaines d’appel. Réessayez.')});});
  return()=>{current=false;controller.abort();};
 },[functionId,version,page,revision]);
 useEffect(()=>{if(!catalogue.loading&&focusCatalogue.current){focusCatalogue.current=false;destinationHeading.current?.focus();}},[catalogue]);
 function chooseVersion(value){setVersion(value);setPage(0);setDialog(false);setResult(null);const address=new URL(location.href);if(value===null)address.searchParams.delete('version');else address.searchParams.set('version',value);history.replaceState(null,'',address);}
 const selectedDomain=catalogue.data?.items.find(v=>v.origin===origin),destinations=selectedDomain?.urls||[];
 let url='';try{if(origin)url=exactUrl(origin,functionId,version,path,query);}catch{/* Invalid composition is reported before send. */}
 const selectedPath=entry=>new URL(entry.url).pathname.slice(invocationPath(functionId,version,'').length).replace(/^\//,'');
 async function selectFile(event){const chosen=event.target.files?.[0]||null,generation=++fileGeneration.current;setFile(null);setFileReading(false);setError(null);
  if(!chosen){setFileReading(false);return;}if(chosen.size>requestLimit){setError(new Error('Le fichier dépasse 1 Mio.'));event.target.value='';return;}
  setFileReading(true);try{const raw=new Uint8Array(await chosen.arrayBuffer());if(mounted.current&&generation===fileGeneration.current)setFile({name:chosen.name,raw});}
  catch{if(mounted.current&&generation===fileGeneration.current)setError(new Error('Impossible de lire le fichier. Sélectionnez-le à nouveau.'));}
  finally{if(mounted.current&&generation===fileGeneration.current)setFileReading(false);}
 }
 function composition(){
  if(!origin||!selectedDomain)throw new Error('Choisissez un domaine du catalogue courant.');
  if(!token)throw new Error('Fournissez un jeton Read ou créez un jeton temporaire.');
  if(version!==null&&!/^[0-9a-f]{64}$/.test(version))throw new Error('Choisissez un hash valide.');
  if(path&&!/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/.test(path))throw new Error('Le chemin est relatif, sans segment vide ni caractère spécial.');
  if(!/^[\x21-\x7e]{1,512}$/.test(token))throw new Error('Le jeton doit être une valeur ASCII sans espace.');
  const parameters=cleanPairs(query),requestHeaders=cleanPairs(headers);
  if(parameters.length>128||parameters.some(v=>v.name.length>8192||v.value.length>8192)||parameters.reduce((n,v)=>n+encoder.encode(v.name+v.value).length,0)>8192)throw new Error('Les paramètres sont limités à 128 couples et 8 Kio UTF-8.');
  const names=new Set();
  for(const pair of requestHeaders){const name=pair.name.toLowerCase();
   if(pair.name.length>128||!/^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/.test(pair.name)||reservedHeaders.has(name)||name==='origin'||/^(proxy-|sec-|x-forwarded-)/.test(name))throw new Error('Un en-tête est invalide ou réservé. Utilisez les champs Jeton et Origine déclarée.');
   if(names.has(name))throw new Error('Un en-tête ne peut pas être présent deux fois.');names.add(name);
   if(pair.value.length>8192||pair.value!==pair.value.trim()||/[\x00-\x1f\x7f\u0100-\uffff]/.test(pair.value))throw new Error('Une valeur d’en-tête contient un caractère interdit ou des espaces de bordure.');
  }
  let raw=new Uint8Array();if(bodyKind==='file'){if(!file)throw new Error('Choisissez le fichier à envoyer.');raw=file.raw;}else if(bodyKind!=='none'){if(bodyKind==='json')try{JSON.parse(text);}catch{throw new Error('Le corps JSON est invalide. Corrigez-le avant l’envoi.');}raw=encoder.encode(text);}
  if(raw.length>requestLimit)throw new Error('Le corps dépasse 1 Mio.');if(raw.length&&['GET','HEAD'].includes(method))throw new Error('Choisissez une méthode acceptant un corps, ou un corps absent.');
  if(bodyKind!=='none'&&!requestHeaders.some(v=>v.name.toLowerCase()==='content-type'))requestHeaders.push({name:'Content-Type',value:bodyKind==='json'?'application/json':bodyKind==='text'?'text/plain; charset=utf-8':'application/octet-stream'});
  if(context==='server'&&declaredOrigin){let parsed;try{parsed=new URL(declaredOrigin);}catch{throw new Error('L’origine déclarée doit contenir uniquement protocole, hôte et port.');}
   if(!['http:','https:'].includes(parsed.protocol)||parsed.username||parsed.password||parsed.origin!==declaredOrigin||/[^\x21-\x7e]|[\\*]/.test(declaredOrigin))throw new Error('L’origine déclarée doit contenir uniquement protocole, hôte et port.');
   requestHeaders.push({name:'Origin',value:declaredOrigin});}
  if(requestHeaders.length>64||requestHeaders.reduce((n,v)=>n+v.name.length+v.value.length,0)>16384)throw new Error('Les en-têtes sont limités à 64 et 16 Kio, y compris les champs calculés.');
  return {origin,version,path:path||null,query:parameters,method,headers:requestHeaders,token,body_base64:base64(raw),max_response_wait_seconds:Number(wait)};
 }
 async function issueToken(){if(tokenBusy||request.current)return;setTokenBusy(true);setTokenNotice('');try{const value=await api(`/api/functions/${functionId}/test-token`,{method:'POST',body:{}});if(mounted.current){setToken(value.token);setTemporary(value);setTokenNotice('Jeton Read temporaire créé.');}}catch(error){throw error.status?error:new Error('Création non confirmée. Consultez les jetons du service avant toute nouvelle création.');}finally{if(mounted.current)setTokenBusy(false);}}
 async function revokeToken(){if(!temporary||tokenBusy||request.current)return;setTokenBusy(true);setTokenNotice('');try{await api(`/api/tokens/${temporary.id}/revoke`,{method:'POST'});setToken('');setTemporary(null);setTokenNotice('Jeton temporaire révoqué.');requestAnimationFrame(()=>accessHeading.current?.focus());}catch(error){throw error.status?error:new Error('Révocation non confirmée. Consultez les jetons du service avant toute nouvelle action.');}finally{if(mounted.current)setTokenBusy(false);}}
 async function send(event){event.preventDefault();if(request.current||fileReading||tokenBusy)return;setError(null);setNotice('');setResult(null);let data;
  try{data=composition();}catch(error){setError(error);return;}
  const controller=new AbortController(),started=performance.now();request.current=controller;setBusy(true);let timedOut=false;
  const timer=setTimeout(()=>{timedOut=true;controller.abort();},Number(wait)*1000+ (context==='server'?5000:0));
  try{const response=context==='server'?await api(`/api/functions/${functionId}/test-invocation`,{method:'POST',body:data,signal:controller.signal}):await browserInvoke(exactUrl(origin,functionId,version,path,query),data,controller.signal);
   if(!mounted.current)return;if(!['response','unconfirmed'].includes(response.state))throw new Error('Réponse du testeur illisible.');
   const raw=response.state==='response'?unbase64(response.body_base64):null;setResult({...response,raw,context,elapsed:response.duration_ms??performance.now()-started});
  }catch(error){if(mounted.current){if(context==='server'&&error.status)setError(error);else setResult({state:'unconfirmed',error:controller.signal.aborted?(timedOut?'response_wait_expired':'wait_cancelled'):context==='browser'?'cors_unreadable':'transport_unavailable',context,elapsed:performance.now()-started});}}
  finally{clearTimeout(timer);if(request.current===controller)request.current=null;if(mounted.current){setBusy(false);requestAnimationFrame(()=>resultHeading.current?.focus());}}
 }
 const resultBytes=result?.raw;const contentEncoding=result?.headers?.find(v=>v.name.toLowerCase()==='content-encoding')?.value;
 let preview=null;try{if(resultBytes){const prefix=resultBytes.subarray(0,previewLimit);const decoded=new TextDecoder('utf-8',{fatal:true}).decode(prefix,{stream:resultBytes.length>prefix.length});if(!/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(decoded))preview=decoded;}}catch{/* Non-text bytes retain their exact downloadable representation. */}
 const download=useRef(null),[downloadUrl,setDownloadUrl]=useState('');
 useEffect(()=>{if(!resultBytes){setDownloadUrl('');return;}const local=URL.createObjectURL(new Blob([resultBytes],{type:'application/octet-stream'}));download.current=local;setDownloadUrl(local);return()=>{URL.revokeObjectURL(local);download.current=null;};},[resultBytes]);
 const curl=url?['curl --request '+method,'--header '+shell('X-Serverless-Token: VOTRE_JETON_READ'),...cleanPairs(headers).map(v=>'--header '+shell(v.name+': VALEUR_A_FOURNIR')),...(bodyKind!=='none'?['--data-binary @corps.bin']:[]),shell(exactUrl(origin,functionId,version,path,cleanPairs(query).map(v=>({...v,value:'VALEUR_A_FOURNIR'}))))].join(' \\\n  '):'';
 async function copyCurl(){setNotice('');try{await navigator.clipboard.writeText(curl);setNotice('Exemple cURL avec valeurs à fournir copié.');}catch{setError(new Error('Copie refusée. Sélectionnez le texte de l’exemple cURL.'));}}
 return <div className="stack tester-workspace">
  <Section title="Destination" headingRef={destinationHeading} action={<button disabled={busy||catalogue.loading} onClick={()=>{focusCatalogue.current=true;setRevision(v=>v+1);}}><RefreshCw aria-hidden="true"/>Actualiser les adresses</button>}>
   <p><a href="/console/manual#tester-une-fonction">Consulter le manuel du testeur</a></p>
   <Facts values={[["Sélection",version===null?'Cible promue courante':<span className="mono">{version}</span>],["Hash courant",catalogue.data?.default_code_hash?<span className="mono">{catalogue.data.default_code_hash}</span>:'Aucune cible promue']]}/>
   <div className="actions"><button disabled={busy} onClick={()=>setDialog(true)}>Choisir la version à tester</button>{version!==null&&<button disabled={busy} onClick={()=>chooseVersion(null)}>Utiliser la cible promue</button>}</div>
   {catalogue.loading?<p role="status">Lecture des domaines d’appel…</p>:catalogue.error?<ErrorMessage error={catalogue.error}/>:!catalogue.data?.total?<p className="empty">Aucun domaine d’appel applicable.</p>:<>
    <Field label="Domaine d’appel"><select disabled={busy} value={origin} onChange={e=>{setOrigin(e.target.value);setResult(null);}}>{catalogue.data.items.map(v=><option key={v.origin} value={v.origin}>{v.origin}</option>)}</select></Field>
    <nav className="pagination" aria-label="Pagination des domaines à tester"><button disabled={busy||!page} onClick={()=>{focusCatalogue.current=true;setPage(v=>v-1);}}><ChevronLeft aria-hidden="true"/>Précédente</button><span>Page {page+1} sur {Math.max(1,Math.ceil(catalogue.data.total/pageSize))}</span><button disabled={busy||(page+1)*pageSize>=catalogue.data.total} onClick={()=>{focusCatalogue.current=true;setPage(v=>v+1);}}>Suivante<ChevronRight aria-hidden="true"/></button></nav>
    {!destinations.length?<p className="empty">Aucun endpoint HTTP pour cette sélection. Choisissez une version disponible ou publiez et promouvez son code.</p>:<Field label="Endpoint déclaré"><select disabled={busy} value={destinations.some(v=>selectedPath(v)===path)?path:'custom'} onChange={e=>{if(e.target.value!=='custom')setPath(e.target.value);}}><option value="custom">Chemin composé ci-dessous</option>{destinations.map(v=><option key={v.url} value={selectedPath(v)}>{selectedPath(v)||'Endpoint implicite'} · {v.methods.join(', ')}</option>)}</select></Field>}
   </>}
   {url&&<p className="mono invocation-url" aria-label="URL à appeler">{url}</p>}
  </Section>
  <Section title="Accès" headingRef={accessHeading}>
   <Field label="Jeton Read" help="Valeur conservée uniquement en mémoire de cette page."><input type="password" value={token} disabled={busy||tokenBusy} maxLength={512} autoComplete="off" spellCheck={false} onChange={e=>{setToken(e.target.value);setTemporary(null);setTokenNotice('');}}/></Field>
   {temporary&&<Facts values={[["Portée",functionName],["Droits",'Read'],["Expiration",stamp(temporary.expires_at)]]}/>}
   <div className="actions"><Confirm tone="primary" label="Créer un jeton Read temporaire" disabled={busy||tokenBusy} message={`Créer un jeton Read pour « ${functionName} », valable quinze minutes et limité à cette fonction ?`} action={issueToken}/>{temporary&&<Confirm label="Révoquer ce jeton temporaire" disabled={busy||tokenBusy} message={`Révoquer immédiatement ce jeton Read pour « ${functionName} » ?`} action={revokeToken}/>}</div>
   <Success>{tokenNotice}</Success>
  </Section>
  <Section title="Requête">
   <form onSubmit={send} className="stack"><fieldset className="form-fields stack" disabled={busy}>
    <div className="form-grid"><Field label="Contexte d’appel"><select value={context} onChange={e=>{setContext(e.target.value);setResult(null);}}><option value="server">Serveur de console</option><option value="browser">Navigateur · CORS</option></select></Field>
     <Field label="Origine déclarée" help={context==='browser'?'Origine réelle du navigateur.':'Origine transmise par le serveur ; vide pour ne pas en déclarer.'}><input readOnly={context==='browser'} value={context==='browser'?location.origin:declaredOrigin} onChange={e=>setDeclaredOrigin(e.target.value)} maxLength={280}/></Field>
     <Field label="Méthode HTTP"><select value={method} onChange={e=>setMethod(e.target.value)}>{['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'].map(v=><option key={v}>{v}</option>)}</select></Field>
     <Field label="Chemin relatif" help="Vide pour l’endpoint implicite ; par exemple commandes/creer."><input value={path} maxLength={256} autoComplete="off" spellCheck={false} onChange={e=>setPath(e.target.value)}/></Field></div>
    <PairFields title="Paramètres" pairs={query} setPairs={setQuery} limit={128}/><PairFields title="En-têtes" pairs={headers} setPairs={setHeaders} limit={64} sensitive/>
    <Field label="Corps de requête"><select value={bodyKind} onChange={e=>setBodyKind(e.target.value)}><option value="none">Absent</option><option value="text">Texte UTF-8</option><option value="json">JSON</option><option value="file">Fichier</option></select></Field>
    {['text','json'].includes(bodyKind)&&<Field label={bodyKind==='json'?'Contenu JSON':'Contenu texte'} help={`${bytes(encoder.encode(text).length)} sur ${bytes(requestLimit)}.`}><textarea className="tester-body mono" rows={8} maxLength={requestLimit} value={text} spellCheck={false} autoComplete="off" onChange={e=>setText(e.target.value)}/></Field>}
    {bodyKind==='file'&&<><Field label="Fichier à envoyer" help="1 Mio maximum."><input type="file" onChange={selectFile}/></Field>{fileReading?<p role="status">Lecture du fichier…</p>:file&&<p>{file.name} · {bytes(file.raw.length)}</p>}</>}
    <Field label="Attente maximale de réponse (s)" help="L’arrêt de l’attente ne garantit pas l’arrêt du handler."><input type="number" min={1} max={900} step={1} required value={wait} onChange={e=>setWait(e.target.value)}/></Field>
   </fieldset>
   <ErrorMessage error={error}/><div className="actions"><button className="primary" disabled={busy||tokenBusy||fileReading||catalogue.loading||Boolean(catalogue.error)||!origin} type="submit"><Send aria-hidden="true"/>{busy?'Appel en cours…':'Envoyer la requête'}</button>{busy&&<button type="button" onClick={()=>request.current?.abort()}><Square aria-hidden="true"/>Arrêter l’attente</button>}</div>
   </form>
   {curl&&<details><summary>Exemple cURL sans valeurs confidentielles</summary><pre className="invocation-log" tabIndex={0}>{curl}</pre><button disabled={busy} onClick={copyCurl}><Copy aria-hidden="true"/>Copier l’exemple cURL</button><Success>{notice}</Success></details>}
  </Section>
  <Section title="Réponse" headingRef={resultHeading}>
   {busy?<p role="status">Attente de la réponse de la passerelle…</p>:!result?<p className="empty">Aucun appel terminé dans cette page.</p>:<>
    <div className="actions"><Badge tone={result.state==='response'?(result.status<400?'success':'danger'):'neutral'}>{result.state==='response'?`HTTP ${result.status}`:'Issue inconnue'}</Badge><span>{result.elapsed.toLocaleString('fr-FR',{maximumFractionDigits:1})} ms · {result.context==='server'?'Serveur de console':'Navigateur'}</span></div>
    {result.state==='unconfirmed'?<p role="status">{result.error==='redirect_hidden'?'Redirection non suivie ; sa réponse est masquée par le navigateur.':result.error==='cors_unreadable'?'La réponse n’est pas lisible depuis le navigateur (CORS ou réseau).':'L’attente est terminée. Le handler peut continuer après son admission.'} Consultez les invocations avant tout nouvel envoi.</p>:<>
     <Facts values={[["Hash exécuté",result.code_hash?<span className="mono">{result.code_hash}</span>:'Non communiqué'],["Identifiant de requête",result.request_id?<span className="mono">{result.request_id}</span>:'Non communiqué'],["Corps conservé",bytes(resultBytes.length)]]}/>
     {result.body_truncated&&<p className="notice">Réponse tronquée à 6 Mio ; le téléchargement contient uniquement les octets conservés.</p>}
     {result.headers_truncated&&<p className="notice">Liste des en-têtes tronquée à sa limite de lecture.</p>}
     {contentEncoding&&<p className="muted">Content-Encoding : {contentEncoding}. Corps {result.body_representation==='wire'?'HTTP brut conservé par le serveur':'décodé nativement par le navigateur'}.</p>}
     <details><summary>En-têtes de réponse</summary><dl className="facts">{result.headers.map((v,n)=><div key={n}><dt className="mono">{v.name}</dt><dd className="mono">{v.value}</dd></div>)}</dl></details>
     {preview!==null?<><pre className="invocation-log tester-response" tabIndex={0} aria-label="Corps de réponse">{preview||'Corps vide.'}</pre>{resultBytes.length>previewLimit&&<p className="muted">Aperçu limité à 64 Kio. Téléchargez le corps conservé pour lire la suite.</p>}</>:<p>Corps binaire ; utilisez le téléchargement.</p>}
     {downloadUrl&&<a className="button" href={downloadUrl} download={contentEncoding&&result.body_representation==='wire'?'reponse-encodee.bin':'reponse.bin'}><Download aria-hidden="true"/>Télécharger le corps conservé</a>}
    </>}
    <div className="actions">{result.request_id&&<a href={withCatalogue(`/console/functions/${functionId}/invocations?invocation=${encodeURIComponent(result.request_id)}`)}>Ouvrir cette invocation et son journal</a>}<a href={withCatalogue(`/console/functions/${functionId}/invocations`)}>Consulter les invocations de la fonction</a></div>
   </>}
  </Section>
  {dialog&&<VersionChoice functionId={functionId} onClose={()=>setDialog(false)} choose={chooseVersion}/>}
 </div>;
}
