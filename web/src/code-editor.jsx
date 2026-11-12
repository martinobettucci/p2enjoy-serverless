// @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md#app-ds-001--édition-de-source-sur-place-prévue-pour-sls-070 | docs/manual.md#modifier-le-code-dans-la-console
import React, {useEffect, useLayoutEffect, useRef, useState} from 'react';
import {ChevronLeft, ChevronRight, FileCode, Folder, RefreshCw, Search, X} from 'lucide-react';
import {api} from './api';
import {Badge, Confirm, DialogForm, ErrorMessage, Facts, Field, Section, Success} from './ui';
import {Candidate} from './publications';
import {withCatalogue} from './catalogue';
import {confirmNavigation, registerNavigationGuard} from './navigation-guard';

const size=5, textLimit=1024**2;
const stamp=value=>new Date(value*1000).toLocaleString('fr-FR');
const code=value=><span className="mono">{value}</span>;
const hash=value=>value ? code(value) : 'Aucune version';
const bytes=value=>new TextEncoder().encode(value).byteLength;
const displayText=value=>value.replace(/\r\n?/g,'\n');
const activeCandidate=row=>['prepared','receiving','validating'].includes(row?.state);
function readable(error) {
  if (!error.status) error.message='Impossible de joindre le serveur. Relisez son état avant une nouvelle opération.';
  return error;
}

// Textarea offsets refer to normalized LF characters. Map edits back to exact
// source boundaries so unchanged CRLF, CR, mixed lines and final bytes survive.
function sourceOffset(raw,position) {
  let visible=0,index=0;
  while(index<raw.length && visible<position) {if(raw[index]==='\r'&&raw[index+1]==='\n') index++;index++;visible++;}
  return index;
}
function editSource(raw,next,input) {
  const previous=displayText(raw);
  if(input?.value===previous) {
    let {start,end,type}=input;
    if(start===end&&type.startsWith('delete')) {
      const removed=previous.length-next.length;
      if(type.endsWith('Backward'))start=Math.max(0,start-removed);
      else if(type.endsWith('Forward'))end=Math.min(previous.length,end+removed);
    }
    const inserted=next.length-(previous.length-(end-start));
    if(inserted>=0&&next.slice(0,start)===previous.slice(0,start)&&next.slice(start+inserted)===previous.slice(end)) {
      const newline=raw.match(/\r\n|\r|\n/)?.[0]||'\n';
      return raw.slice(0,sourceOffset(raw,start))+next.slice(start,start+inserted).replace(/\n/g,newline)+raw.slice(sourceOffset(raw,end));
    }
  }
  return editUnlocatedSource(raw,next);
}
function editUnlocatedSource(raw,next) {
  const previous=displayText(raw);let start=0,end=0;
  while(start<previous.length&&start<next.length&&previous[start]===next[start]) start++;
  while(end<previous.length-start&&end<next.length-start&&previous[previous.length-end-1]===next[next.length-end-1]) end++;
  const newline=raw.match(/\r\n|\r|\n/)?.[0] || '\n';
  return raw.slice(0,sourceOffset(raw,start))+next.slice(start,next.length-end).replace(/\n/g,newline)+raw.slice(sourceOffset(raw,previous.length-end));
}
function lineStyle(raw) {
  const forms=new Set(raw.match(/\r\n|\r|\n/g)||[]);
  return forms.size>1 ? 'Mixtes, conservées' : forms.has('\r\n') ? 'CRLF' : forms.has('\r') ? 'CR' : forms.has('\n') ? 'LF' : 'Aucune fin de ligne';
}
function writeAddress(changes) {
  const url=new URL(location.href);
  for(const [name,value] of Object.entries(changes)) {if(value) url.searchParams.set(name,value);else url.searchParams.delete(name);}
  history.replaceState(null,'',url);
}
function Pages({name,page,total,disabled,change}) {
  if(!total)return null;
  const pages=Math.max(1,Math.ceil(total/size));
  return <nav className="pagination" aria-label={`Pagination ${name}`}>
    <button type="button" disabled={disabled||!page} onClick={()=>change(page-1)}><ChevronLeft aria-hidden="true"/>Précédente</button>
    <span>Page {page+1} sur {pages}</span>
    <button type="button" disabled={disabled||page+1>=pages} onClick={()=>change(page+1)}>Suivante<ChevronRight aria-hidden="true"/></button>
  </nav>;
}

function UnsavedChanges({functionName,decide}) {
  const dialog=useRef(null),origin=useRef(document.activeElement),cancel=useRef(null),heading=React.useId();
  useEffect(()=>{dialog.current.showModal();document.body.classList.add('dialog-open');cancel.current?.focus();return()=>{
    document.body.classList.remove('dialog-open');if(origin.current?.isConnected&&!origin.current.matches(':disabled'))origin.current.focus();
  };},[]);
  function finish(proceed) {dialog.current.close();decide(proceed);}
  return <dialog ref={dialog} aria-labelledby={heading} onCancel={event=>{event.preventDefault();finish(false);}}>
    <div className="dialog-heading"><h2 id={heading}>Modifications non enregistrées</h2><button onClick={()=>finish(false)} aria-label="Fermer la confirmation"><X aria-hidden="true"/></button></div>
    <div className="form-content"><p>Le fichier de « {functionName} » contient des saisies non enregistrées. Les abandonner pour continuer ?</p></div>
    <div className="dialog-actions"><button ref={cancel} onClick={()=>finish(false)}>Conserver la saisie</button><button className="danger" onClick={()=>finish(true)}>Continuer sans enregistrer</button></div>
  </dialog>;
}

function VersionChoice({functionId,onClose,choose}) {
  const [page,setPage]=useState(0),[state,setState]=useState({loading:true}),[selected,setSelected]=useState('');
  const [revision,setRevision]=useState(0),heading=useRef(null),focus=useRef(false);
  useEffect(()=>{let current=true;const controller=new AbortController();setState({loading:true});
    api(`/api/functions/${functionId}/versions?limit=${size}&offset=${page*size}`,{signal:controller.signal}).then(data=>{if(current)setState({data});}).catch(error=>{if(current)setState({error:readable(error)});});
    return()=>{current=false;controller.abort();};
  },[functionId,page,revision]);
  useEffect(()=>{if(!state.loading&&focus.current){focus.current=false;heading.current?.focus();}},[state]);
  return <DialogForm title="Choisir une version source" initial={{}} submitLabel="Ouvrir cette source" onClose={onClose}
    onSubmit={()=>{if(!selected)throw new Error('Sélectionnez un hash conservé.');return choose(selected);}}>
    {()=> <><h3 ref={heading} tabIndex={-1}>Versions de la fonction</h3>
      {state.loading?<p role="status">Lecture des versions…</p>:state.error?<><ErrorMessage error={state.error}/><button type="button" onClick={()=>setRevision(v=>v+1)}>Réessayer</button></>:<>
        {!state.data.total?<p className="empty">Aucune version publiée.</p>:<ul className="editor-source-options">{state.data.items.map(row=><li key={row.code_hash}>
          <label className="check"><input type="radio" name="editor-source" value={row.code_hash} disabled={row.state==='deleted'||!row.stored_bytes} checked={selected===row.code_hash} onChange={()=>setSelected(row.code_hash)}/>
            <span><span className="mono">{row.code_hash}</span><small>{row.handler} · {row.state==='deleted'?'Supprimée':row.state==='archived'?'Archivée':'Disponible'}{row.active?' · Cible par défaut':''}</small></span></label>
        </li>)}</ul>}
        <Pages name="des versions sources" page={page} total={state.data.total} change={v=>{focus.current=true;setPage(v);}}/>
        {selected&&<p>Source choisie : {code(selected)}</p>}
      </>}
    </>}
  </DialogForm>;
}

export function FunctionCodeEditor({functionId,functionName,onFunction}) {
  const prefix=`/api/functions/${functionId}`;
  const initial=useRef(new URLSearchParams(location.search));
  const [mode,setMode]=useState(initial.current.get('view')|| (initial.current.get('version')?'source':''));
  const [version,setVersion]=useState(initial.current.get('version')||'');
  const [context,setContext]=useState(null),[draft,setDraft]=useState(null),[contextError,setContextError]=useState(null),[reading,setReading]=useState(true);
  const [directory,setDirectory]=useState(''),[query,setQuery]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(0);
  const [tree,setTree]=useState({loading:true}),[treeRevision,setTreeRevision]=useState(0);
  const [path,setPath]=useState(initial.current.get('file')||''),[file,setFile]=useState(null),[fileLoading,setFileLoading]=useState(false),[fileError,setFileError]=useState(null);
  const [text,setText]=useState(''),[editing,setEditing]=useState(false),[busy,setBusy]=useState(false),[mutationError,setMutationError]=useState(null),[notice,setNotice]=useState('');
  const [conflict,setConflict]=useState(null),[needsReview,setNeedsReview]=useState(false),[serverCopy,setServerCopy]=useState(null);
  const [dialog,setDialog]=useState(null),[leave,setLeave]=useState(false);
  const [diff,setDiff]=useState(null),[diffError,setDiffError]=useState(null),[diffLoading,setDiffLoading]=useState(false),[diffPage,setDiffPage]=useState(0),[diffPath,setDiffPath]=useState('');
  const [selected,setSelected]=useState(initial.current.get('deployment')||''),[candidate,setCandidate]=useState(null),[candidateError,setCandidateError]=useState(null),[candidateReading,setCandidateReading]=useState(false),[candidateRevision,setCandidateRevision]=useState(0),[publishing,setPublishing]=useState(false);
  const mounted=useRef(true),busyRef=useRef(false),draftRef=useRef(null),dirtyRef=useRef(false),textRef=useRef(''),modeRef=useRef(mode),leaveResolver=useRef(null);
  const sourceGeneration=useRef(0),fileGeneration=useRef(0),diffGeneration=useRef(0),reviewGeneration=useRef(0);
  const pendingInput=useRef(null),textHistory=useRef({past:[],future:[]}),pathRef=useRef(path);
  const fileArea=useRef(null),fileHeading=useRef(null),treeHeading=useRef(null),focusFile=useRef(false),focusTree=useRef(false),focusEdit=useRef(false),[overflow,setOverflow]=useState(false);
  const [find,setFind]=useState(''),[match,setMatch]=useState(-1),[findNotice,setFindNotice]=useState('');
  const dirty=editing&&Boolean(file?.editable)&&text!==file.text;
  dirtyRef.current=dirty;textRef.current=text;draftRef.current=draft;modeRef.current=mode;pathRef.current=path;
  const locked=busy||reading||fileLoading||Boolean(contextError)||needsReview||Boolean(conflict);

  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;sourceGeneration.current++;fileGeneration.current++;diffGeneration.current++;leaveResolver.current?.(false);};},[]);
  function acceptDraft(value) {draftRef.current=value;setDraft(value);}
  function invalidateReview() {reviewGeneration.current++;setConflict(null);setServerCopy(null);}
  function installText(value) {setText(value);textHistory.current={past:[],future:[]};pendingInput.current=null;}
  function clearFile() {invalidateReview();fileGeneration.current++;setFile(null);setPath('');setText('');setEditing(false);setFileError(null);setFindNotice('');setMatch(-1);dirtyRef.current=false;writeAddress({file:''});}
  function askLeave() {
    if(!dirtyRef.current)return Promise.resolve(true);
    if(leaveResolver.current)return Promise.resolve(false);
    return new Promise(resolve=>{leaveResolver.current=resolve;setLeave(true);});
  }
  function decideLeave(proceed) {
    if(proceed) {dirtyRef.current=false;setText(file?.text||'');setEditing(false);}
    const resolve=leaveResolver.current;leaveResolver.current=null;setLeave(false);resolve?.(proceed);
  }
  useEffect(()=>{
    const remove=registerNavigationGuard(askLeave);
    function unload(event) {if(dirtyRef.current){event.preventDefault();event.returnValue='';}}
    function click(event) {
      const link=event.target.closest?.('a[href]');
      if(!dirtyRef.current||event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||!link||link.hasAttribute('download')||(link.target&&link.target!=='_self'))return;
      const destination=new URL(link.href,location.href);
      if(destination.origin===location.origin&&destination.pathname===location.pathname&&destination.search===location.search&&destination.hash)return;
      event.preventDefault();event.stopPropagation();const href=link.href;
      void confirmNavigation().then(proceed=>{if(proceed&&mounted.current)location.assign(href);});
    }
    window.addEventListener('beforeunload',unload);document.addEventListener('click',click,true);
    return()=>{remove();window.removeEventListener('beforeunload',unload);document.removeEventListener('click',click,true);};
  },[]);
  async function protectedAction(action) {if(await askLeave())return action();}

  async function loadContext({initialLoad=false}={}) {
    const generation=++sourceGeneration.current;setReading(true);setContextError(null);
    try {
      const fn=await api(prefix),summary=await api(prefix+'/code-draft');
      if(!mounted.current||generation!==sourceGeneration.current)return;
      const prior=draftRef.current;
      if(prior&&path&&(summary.draft?.id!==prior.id||summary.draft?.version!==prior.version)) {
        invalidateReview();setNeedsReview(true);
      } else acceptDraft(summary.draft);
      setContext({fn,...summary});onFunction(fn);
      if(initialLoad) {
        const surface=modeRef.current || (summary.draft?'draft':'source');
        setMode(surface==='draft'&&summary.draft?'draft':'source');modeRef.current=surface==='draft'&&summary.draft?'draft':'source';
        if(!initial.current.get('deployment')&&summary.draft?.last_deployment_id){setSelected(summary.draft.last_deployment_id);writeAddress({deployment:summary.draft.last_deployment_id});}
      }
      setTreeRevision(v=>v+1);
    } catch(error) {if(mounted.current&&generation===sourceGeneration.current)setContextError(readable(error));}
    finally {if(mounted.current&&generation===sourceGeneration.current)setReading(false);}
  }
  useEffect(()=>{void loadContext({initialLoad:true});},[functionId]);
  useEffect(()=>{
    if(!mode||!context)return;
    let current=true;const controller=new AbortController();setTree({loading:true});
    const params=new URLSearchParams({directory,search:query,limit:String(size),offset:String(page*size)});
    if(mode==='source'&&version)params.set('version',version);
    const endpoint=prefix+(mode==='draft'?'/code-draft/files':'/code-sources')+'?'+params;
    api(endpoint,{signal:controller.signal}).then(data=>{
      if(!current)return;
      const last=Math.max(0,Math.ceil(data.tree.total/size)-1);
      if(page>last){setPage(last);return;}
      setTree({data});
    }).catch(error=>{if(current)setTree({error:readable(error)});});
    return()=>{current=false;controller.abort();};
  },[mode,version,directory,query,page,treeRevision,Boolean(context)]);
  useEffect(()=>{if(!tree.loading&&focusTree.current){focusTree.current=false;treeHeading.current?.focus();}},[tree]);

  async function openFile(name,options={}) {
    if(!options.skipGuard&&!await askLeave())return;
    invalidateReview();const generation=++fileGeneration.current;setFileLoading(true);setFileError(null);setFindNotice('');setMatch(-1);setEditing(false);setPath(name);writeAddress({file:name});
    try {
      const surface=options.mode||modeRef.current;
      const endpoint=prefix+(surface==='draft'?'/code-draft/file':'/code-sources/file')+'?path='+encodeURIComponent(name)+(surface==='source'&&version?'&version='+encodeURIComponent(version):'');
      const data=await api(endpoint);
      if(!mounted.current||generation!==fileGeneration.current)return;
      setFile(data.file);installText(data.file.editable?data.file.text:'');
      if(surface==='draft'&&data.draft)acceptDraft(data.draft);
      focusFile.current=true;
    } catch(error) {if(mounted.current&&generation===fileGeneration.current){setFile(null);setFileError(readable(error));}}
    finally {if(mounted.current&&generation===fileGeneration.current)setFileLoading(false);}
  }
  const initialFileOpened=useRef(false);
  useEffect(()=>{if(context&&mode&&path&&!initialFileOpened.current){initialFileOpened.current=true;void openFile(path,{skipGuard:true});}},[Boolean(context),mode]);
  useLayoutEffect(()=>{if(!fileLoading&&focusFile.current){focusFile.current=false;fileHeading.current?.focus();}if(focusEdit.current&&editing){focusEdit.current=false;fileArea.current?.focus();}},[fileLoading,file,editing]);
  useEffect(()=>{
    const node=fileArea.current;if(!node)return;
    const measure=()=>setOverflow(node.scrollWidth>node.clientWidth+1),observer=new ResizeObserver(measure);observer.observe(node);measure();return()=>observer.disconnect();
  },[file,text,editing]);

  useEffect(()=>{
    const node=fileArea.current;if(!node)return;
    function beforeInput(event) {pendingInput.current={value:node.value,start:node.selectionStart,end:node.selectionEnd,type:event.inputType||''};}
    node.addEventListener('beforeinput',beforeInput);return()=>node.removeEventListener('beforeinput',beforeInput);
  },[file,editing]);
  function changeText(next) {
    const previous=textRef.current,input=pendingInput.current;pendingInput.current=null;
    const history=textHistory.current;
    let replacement;
    if(input?.type==='historyUndo'||input?.type==='historyRedo') {
      const origin=input.type==='historyUndo'?history.past:history.future;
      const destination=input.type==='historyUndo'?history.future:history.past;
      const index=origin.findLastIndex(value=>displayText(value)===next);
      if(index>=0){replacement=origin[index];destination.push(previous,...origin.slice(index+1).reverse());origin.splice(index);}
    }
    if(replacement===undefined){replacement=editSource(previous,next,input);history.past.push(previous);history.future=[];}
    textRef.current=replacement;setText(replacement);setMatch(-1);setFindNotice('');
  }

  async function chooseSurface(surface,hashValue=version) {
    if(!await askLeave())return;
    clearFile();setTree({loading:true});setMode(surface);modeRef.current=surface;setVersion(hashValue);setDirectory('');setQuery('');setSearch('');setPage(0);setNotice('');setDiff(null);setDiffError(null);
    writeAddress({view:surface,version:hashValue});
  }
  async function createDraft() {
    if(busyRef.current||locked)return;
    busyRef.current=true;setBusy(true);setMutationError(null);setNotice('');
    try {
      const result=await api(prefix+'/code-draft',{method:'POST',headers:{'If-Match':String(context.function_version)},body:{base_code_hash:tree.data?.source?.code_hash||null}});
      if(!mounted.current)return;acceptDraft(result.draft);setContext(prior=>({...prior,...result}));await chooseSurface('draft',version);setTreeRevision(v=>v+1);setNotice('Brouillon personnel créé.');
    } catch(error) {if(mounted.current){setMutationError(readable(error));if(!error.status||error.status>=500)setNeedsReview(true);}}
    finally {busyRef.current=false;if(mounted.current)setBusy(false);}
  }
  async function saveMutation(body,{preserveFile=false}={}) {
    if(busyRef.current||locked)throw new Error('Relisez le brouillon avant de poursuivre.');
    if(!draftRef.current)throw new Error('Créez ou ouvrez votre brouillon.');
    busyRef.current=true;setBusy(true);setMutationError(null);setNotice('');
    const previous=draftRef.current,submitted=body.file?.action==='write'?body.file.text:null;
    try {
      const result=await api(prefix+'/code-draft',{method:'PUT',headers:{'If-Match':String(previous.version)},body});
      const digest=submitted!==null?await crypto.subtle.digest('SHA-256',new TextEncoder().encode(submitted)):null;
      const fileHash=digest?[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join(''):null;
      if(!mounted.current)return result;
      acceptDraft(result.draft);setContext(prior=>({...prior,...result}));setTreeRevision(v=>v+1);setDiff(null);
      if(preserveFile&&submitted!==null)setFile(prior=>({...prior,text:submitted,size:bytes(submitted),sha256:fileHash}));
      setNotice(result.changed?'Brouillon enregistré.':'Contenu déjà enregistré.');return result;
    } catch(error) {
      if(mounted.current){setMutationError(readable(error));if(error.status===409||!error.status||error.status>=500)setNeedsReview(true);}
      throw error;
    } finally {busyRef.current=false;if(mounted.current)setBusy(false);}
  }
  async function saveFile() {
    if(bytes(text)>textLimit){setMutationError(new Error('Un fichier est limité à 1 Mio UTF-8.'));return;}
    try {await saveMutation({file:{action:'write',path,text}},{preserveFile:true});} catch(error) {setMutationError(readable(error));}
  }
  async function rereadDraft() {
    if(busyRef.current)return;
    const generation=++reviewGeneration.current,surface=modeRef.current,targetPath=pathRef.current;
    setReading(true);setMutationError(null);setConflict(null);setServerCopy(null);
    try {
      const summary=await api(prefix+'/code-draft');
      const copy=summary.draft&&surface==='draft'&&targetPath ? await api(prefix+'/code-draft/file?path='+encodeURIComponent(targetPath)).catch(error=>{if(error.status===404)return null;throw error;}) : null;
      if(!mounted.current||generation!==reviewGeneration.current)return;
      setContext(prior=>({...prior,...summary}));setServerCopy({file:copy?.file||null,surface,path:targetPath,generation});setConflict(summary.draft||{missing:true});setNeedsReview(true);
    } catch(error) {if(mounted.current&&generation===reviewGeneration.current)setMutationError(readable(error));}
    finally {if(mounted.current)setReading(false);}
  }
  function adoptServer(replaceText) {
    if(!conflict||conflict.missing)return;
    if(!serverCopy||serverCopy.generation!==reviewGeneration.current||serverCopy.path!==pathRef.current||serverCopy.surface!==modeRef.current)throw new Error('Relisez le fichier ouvert avant toute adoption.');
    const copy=serverCopy.file;
    if(!replaceText&&copy&&!copy.editable)throw new Error('Le fichier relu n’est plus éditable. Conservez votre saisie avant de choisir le contenu du serveur.');
    acceptDraft(conflict);setConflict(null);setNeedsReview(false);setMutationError(null);
    if(modeRef.current==='draft') {
      if(copy?.editable) {setFile(copy);if(replaceText){installText(copy.text);dirtyRef.current=false;}}
      else if(replaceText)clearFile();
      else if(pathRef.current)setFile(prior=>({...prior,text:'',size:0,sha256:null,executable:false,mode:'0o444',missing:true}));
    }
    setServerCopy(null);setTreeRevision(v=>v+1);setNotice('Version du serveur adoptée explicitement.');
  }
  async function removeDraft() {
    if(!await askLeave())return;
    if(busyRef.current||locked)throw new Error('Relisez le brouillon avant de l’abandonner.');
    busyRef.current=true;setBusy(true);setMutationError(null);setNotice('');
    try {await api(prefix+'/code-draft',{method:'DELETE',headers:{'If-Match':String(draftRef.current.version)}});if(!mounted.current)return;
      acceptDraft(null);clearFile();setMode('source');modeRef.current='source';writeAddress({view:'source'});setDiff(null);await loadContext();setNotice('Brouillon abandonné.');
    } catch(error){if(mounted.current){setMutationError(readable(error));if(error.status===409||!error.status||error.status>=500)setNeedsReview(true);}throw error;}
    finally {busyRef.current=false;if(mounted.current)setBusy(false);}
  }
  async function readDiff(pageValue=diffPage,pathValue=diffPath) {
    const generation=++diffGeneration.current;setDiffLoading(true);setDiffError(null);setDiff(null);setDiffPage(pageValue);setDiffPath(pathValue);
    try {
      const params=new URLSearchParams({limit:String(size),offset:String(pageValue*size)});if(pathValue)params.set('path',pathValue);
      const data=await api(prefix+'/code-draft/diff?'+params);
      if(!mounted.current||generation!==diffGeneration.current)return;
      const last=Math.max(0,Math.ceil(data.diff.total/size)-1);
      if(pageValue>last){void readDiff(last,pathValue);return;}setDiff(data);
    }catch(error){if(mounted.current&&generation===diffGeneration.current)setDiffError(readable(error));}
    finally{if(mounted.current&&generation===diffGeneration.current)setDiffLoading(false);}
  }

  useEffect(()=>{
    if(!selected)return;
    let current=true,timer;const controller=new AbortController();setCandidateReading(true);setCandidateError(null);
    async function read() {
      try {
        const row=await api('/api/deployments/'+encodeURIComponent(selected),{signal:controller.signal});
        if(row.function_id!==functionId)throw Object.assign(new Error('Cette tentative appartient à une autre fonction.'),{status:403});
        if(!current)return;setCandidate(row);setCandidateReading(false);
        if(['receiving','validating'].includes(row.state)||publishing)timer=setTimeout(read,1000);
      }catch(error){if(!current)return;setCandidate(null);setCandidateReading(false);
        if(error.status===404&&publishing)timer=setTimeout(read,1000);else setCandidateError(readable(error));}
    }
    void read();return()=>{current=false;controller.abort();clearTimeout(timer);};
  },[functionId,selected,candidateRevision,publishing]);
  async function publish() {
    if(busyRef.current||locked||dirtyRef.current||activeCandidate(candidate)||Boolean(candidateError)||candidateReading||Boolean(selected&&!candidate))throw new Error('Enregistrez vos saisies et relisez la tentative avant de publier.');
    busyRef.current=true;setBusy(true);setPublishing(true);setNotice('');setMutationError(null);setCandidate(null);setCandidateError(null);
    const identifier=crypto.randomUUID();writeAddress({deployment:identifier});setSelected(identifier);
    try {
      const result=await api(prefix+'/code-draft/publish',{method:'POST',headers:{'If-Match':String(context.function_version)},body:{deployment_id:identifier,draft_version:draftRef.current.version}});
      if(mounted.current){setCandidate(result);setNotice(result.code_changed?'Nouvelle version publiée.':'Code inchangé : version réutilisée.');}
    }catch(error){if(mounted.current)setMutationError(readable(error));}
    finally {busyRef.current=false;if(mounted.current){setBusy(false);setPublishing(false);setCandidateRevision(v=>v+1);void loadContext();}}
  }
  function findOccurrence(backward=false) {
    const value=displayText(text);if(!find){setFindNotice('Saisissez un texte à rechercher.');return;}
    const position=backward?(match===0?-1:value.lastIndexOf(find,match<0?value.length:match-1)):(value.indexOf(find,match<0?0:match+find.length));
    const index=position<0?(backward?value.lastIndexOf(find):value.indexOf(find)):position;
    setMatch(index);
    if(index<0){setFindNotice('Aucune occurrence.');return;}
    const before=value.slice(0,index),line=before.split('\n').length,column=index-(before.lastIndexOf('\n')+1)+1;
    fileArea.current?.focus();fileArea.current?.setSelectionRange(index,index+find.length);setFindNotice(`Occurrence ligne ${line}, colonne ${column}.`);
  }
  const fileBytes=bytes(text),selectionRequired=Boolean(tree.data?.selection_required);
  const source=tree.data?.source||null;
  return <div className="editor-view">
    <Section title="Source et brouillon" action={<button disabled={reading||busy} onClick={()=>{setNotice('');void loadContext();}}><RefreshCw aria-hidden="true"/>{contextError?'Réessayer':'Actualiser le contexte'}</button>}>
      {reading&&<p role="status">Lecture du contexte…</p>}<ErrorMessage error={contextError}/><ErrorMessage error={mutationError}/><Success>{notice}</Success>
      {context&&<div className="stack"><Facts values={[
        ['Surface ouverte',mode==='draft'?'Mon brouillon':'Code publié en lecture'],['Cible promue',hash(context.current_code_hash)],
        ['Base du brouillon',draft?draft.base?.code_hash?hash(draft.base.code_hash):'Départ vide initial':'Aucun brouillon personnel'],
        ...(draft?[['Handler du brouillon',code(draft.handler)],['Enregistrement du brouillon',String(draft.version)],['Dernière sauvegarde',stamp(draft.updated_at)],['Modifications enregistrées',`${draft.changed_paths} chemin(s) · ${draft.change_bytes} octets UTF-8`]]:[]),
      ]}/>
      <div className="actions"><button disabled={busy||reading} onClick={()=>void protectedAction(()=>setDialog('source'))}>Choisir une version source</button>
        {mode==='draft'?<button disabled={busy} onClick={()=>void chooseSurface('source')}>Lire le code publié</button>:draft?<button disabled={busy} onClick={()=>void chooseSurface('draft')}>Ouvrir mon brouillon</button>:<button className="primary" disabled={locked||tree.loading||Boolean(tree.error)||selectionRequired} onClick={createDraft}>Créer mon brouillon</button>}
      </div>
      {mode==='source'&&<p>Source sélectionnée : {tree.loading?'Lecture en cours…':source?hash(source.code_hash):selectionRequired?'Choisissez un hash conservé.':'Aucun code publié.'}</p>}
      {draft&&<div className="actions"><button disabled={locked} onClick={()=>setDialog('handler')}>Modifier le handler du brouillon</button>
        <Confirm label="Abandonner mon brouillon" message={`Abandonner le brouillon personnel de « ${functionName} » ? Le code publié sera conservé.`} disabled={locked} action={removeDraft}/>
      </div>}
      <p><a href="/console/manual#modifier-le-code-dans-la-console">Consulter le manuel de l’éditeur</a></p></div>}
      {(needsReview||conflict)&&<div className="confirm"><h3>Relecture nécessaire</h3><p>Vos saisies locales sont conservées. Vérifiez le brouillon du serveur avant une nouvelle sauvegarde.</p>
        <button disabled={busy||reading} onClick={rereadDraft}>Relire le brouillon serveur</button>
        {conflict?.missing&&<><p>Le brouillon a été abandonné. Conservez votre texte avant de changer de source.</p><button onClick={()=>void protectedAction(()=>{acceptDraft(null);setNeedsReview(false);setConflict(null);setServerCopy(null);clearFile();setMode('source');modeRef.current='source';writeAddress({view:'source'});setTreeRevision(v=>v+1);})}>Revenir aux sources</button></>}
        {conflict&&!conflict.missing&&<><Facts values={[["Enregistrement relu",conflict.version],["Base relue",hash(conflict.base?.code_hash)],["Handler relu",code(conflict.handler)]]}/>
          {serverCopy?.file?.editable&&<details><summary>Contenu du serveur</summary><pre className="invocation-log mono" tabIndex={0}>{serverCopy.file.text}</pre></details>}
          <div className="actions"><Confirm tone="primary" label="Adopter cette version en gardant ma saisie" message={`Utiliser l’enregistrement ${conflict.version} du brouillon pour votre prochaine sauvegarde explicite ?`} action={()=>adoptServer(false)}/>
            <Confirm label="Utiliser le texte du serveur" message="Remplacer vos saisies locales par le contenu relu du serveur ?" action={()=>adoptServer(true)}/></div>
        </>}
      </div>}
    </Section>

    {context&&<div className="editor-layout">
      <section className="panel" aria-labelledby="editor-tree-heading"><div className="section-heading"><h2 id="editor-tree-heading" tabIndex={-1} ref={treeHeading}>Fichiers {mode==='draft'?'du brouillon':'de la source'}</h2></div>
        <form className="stack" onSubmit={event=>{event.preventDefault();setQuery(search);setPage(0);setTreeRevision(v=>v+1);}}><Field label="Rechercher un chemin"><input type="search" maxLength={200} value={search} onChange={event=>setSearch(event.target.value)}/></Field><button disabled={busy}><Search aria-hidden="true"/>Rechercher</button></form>
        <nav className="editor-folders" aria-label="Dossiers du code"><button disabled={busy} onClick={()=>{setDirectory('');setPage(0);}}>Racine</button>{directory&&<><span className="mono">{directory}</span><button disabled={busy} onClick={()=>{setDirectory(directory.split('/').slice(0,-1).join('/'));setPage(0);}}>Dossier parent</button></>}</nav>
        {tree.loading?<p role="status">Lecture des fichiers…</p>:tree.error?<><ErrorMessage error={tree.error}/><button onClick={()=>setTreeRevision(v=>v+1)}>Réessayer la lecture des fichiers</button></>:<>
          <p className="muted">{tree.data?.tree.total||0} élément(s)</p>
          {!tree.data?.tree.items.length?<p className="empty">Aucun fichier dans cette sélection.</p>:<ul className="editor-files">{tree.data.tree.items.map(item=><li key={item.path}><button disabled={busy} aria-current={item.path===path?'true':undefined} onClick={()=>{
            if(item.kind==='directory'){setDirectory(item.path);setPage(0);}else void openFile(item.path);
          }}>{item.kind==='directory'?<Folder aria-hidden="true"/>:<FileCode aria-hidden="true"/>}<span><span className="mono">{item.path}</span>{item.kind==='file'&&<small>{item.size} octets{item.dependency?' · Dépendance':''}{!item.editable?item.reason==='binary'?' · Binaire':' · Hors limite':''}</small>}</span></button></li>)}</ul>}
          <Pages name="des fichiers" page={page} total={tree.data?.tree.total||0} disabled={busy} change={v=>{focusTree.current=true;setPage(v);}}/>
        </>}
        {mode==='draft'&&draft&&<button disabled={locked} onClick={()=>void protectedAction(()=>setDialog('file'))}>Ajouter un fichier</button>}
      </section>
      <section className="panel editor-file" aria-labelledby="editor-file-heading"><div className="section-heading"><h2 id="editor-file-heading" tabIndex={-1} ref={fileHeading}>{path||'Contenu du fichier'}</h2>{dirty&&<Badge tone="accent">Saisies non enregistrées</Badge>}</div>
        {fileLoading?<p role="status">Lecture du fichier…</p>:fileError?<><ErrorMessage error={fileError}/><button disabled={busy} onClick={()=>void openFile(path)}>Réessayer la lecture du fichier</button></>:file?<div className="stack">
          <Facts values={[["Taille enregistrée",file.missing?'Fichier absent du brouillon relu':`${file.size} octets`],["SHA256 enregistré",file.sha256?code(file.sha256):'Non enregistré'],["Exécutable",file.executable?'Oui':'Non'],["Type",file.dependency?'Dépendance packagée':file.editable?'Texte UTF-8':file.reason==='binary'?'Binaire':'Hors limite d’édition']]}/>
          {file.editable?<>
            <Field label="Rechercher dans le fichier" help="Recherche littérale, casse respectée."><input type="search" maxLength={200} value={find} onChange={event=>{setFind(event.target.value);setMatch(-1);setFindNotice('');}}/></Field>
            <div className="actions"><button onClick={()=>findOccurrence(true)}>Occurrence précédente</button><button onClick={()=>findOccurrence(false)}>Occurrence suivante</button></div><p role="status">{findNotice}</p>
            <Field label={editing?'Code en cours de saisie':'Code enregistré en lecture'} help={editing?'Enregistrer le fichier conserve ce texte dans votre brouillon.':mode==='draft'?'Contenu du brouillon enregistré sur le serveur.':'Contenu de la version source immuable.'}>
              <textarea ref={fileArea} className="editor-code mono" rows={18} wrap="off" spellCheck={false} autoCapitalize="off" autoCorrect="off" readOnly={!editing} value={displayText(text)} onChange={event=>changeText(event.target.value)}/>
            </Field>
            {overflow&&<p className="muted">Le code défile horizontalement dans son cadre.</p>}
            <p className={fileBytes>textLimit?'notice error':'muted'} role={fileBytes>textLimit?'alert':undefined}>{fileBytes} / {textLimit} octets UTF-8 · Fins de ligne : {lineStyle(text)}</p>
            {mode==='draft'&&<div className="actions">{editing?<><button className="primary" disabled={locked||fileBytes>textLimit} onClick={saveFile}>{busy?'Enregistrement…':'Enregistrer le fichier'}</button><button disabled={busy} onClick={()=>void protectedAction(()=>setEditing(false))}>Terminer l’édition</button></>:<button disabled={locked} onClick={()=>{focusEdit.current=true;setEditing(true);}}>Modifier le fichier</button>}
              <Confirm label="Retirer ce fichier" message={`Retirer « ${path} » du brouillon enregistré de « ${functionName} » ?`} disabled={locked||file.missing} action={async()=>{if(!await askLeave())return;await saveMutation({file:{action:'delete',path}});clearFile();}}/>
              <Confirm label="Rétablir depuis la base" message={`Rétablir « ${path} » depuis la base du brouillon ? Un fichier ajouté sera retiré.`} disabled={locked} action={async()=>{if(!await askLeave())return;await saveMutation({file:{action:'revert',path}});clearFile();}}/>
            </div>}
          </>:<p className="notice">{file.reason==='binary'?'Fichier binaire.':'Fichier supérieur à la limite d’édition de 1 Mio.'} Son contenu est conservé lors de la publication.</p>}
        </div>:<p className="empty">Choisissez un fichier dans l’arborescence.</p>}
      </section>
    </div>}

    {draft&&<Section title="Comparer le brouillon enregistré" action={<button disabled={busy||diffLoading} onClick={()=>void readDiff(0,'')}>{diffError?'Réessayer la comparaison':'Voir le diff avec la cible'}</button>}>
      <p>Comparaison avec la cible promue actuelle. Les saisies non enregistrées restent dans le fichier.</p>
      {diffLoading&&<p role="status">Lecture de la comparaison…</p>}<ErrorMessage error={diffError}/>
      {diff&&<div className="stack"><Facts values={[["Cible comparée",hash(diff.comparison.before?.code_hash)],["Base du brouillon",hash(diff.comparison.after?.code_hash)],["Handler comparé",diff.comparison.before?.handler||'Aucun'],["Handler du brouillon",diff.comparison.after.handler]]}/>
        {!diff.diff.total?<p className="empty">Aucun fichier différent.</p>:<ul className="editor-diff-list">{diff.diff.items.map(item=><li key={item.path}><button disabled={busy} onClick={()=>void readDiff(diffPage,item.path)}><span className="mono">{item.path}</span> · {({added:'Ajouté',deleted:'Retiré',modified:'Modifié'})[item.change]}</button></li>)}</ul>}
        <Pages name="du diff" page={diffPage} total={diff.diff.total} disabled={busy} change={v=>void readDiff(v,'')}/>
        {diff.diff.file&&<><h3 className="mono">{diff.diff.file.path}</h3>{diff.diff.file.diff!==null?<pre className="invocation-log mono" tabIndex={0} aria-label="Diff du fichier">{diff.diff.file.diff||'Contenu textuel identique.'}</pre>:<p>Diff textuel indisponible : {diff.diff.file.reason==='line_limit'?'plus de 2 000 lignes':'binaire ou hors limite d’édition'}.</p>}
          {diff.diff.file.truncated&&<p className="notice log-warning">Diff tronqué à 128 Kio.</p>}
          <Confirm label="Rétablir ce chemin depuis la base" message={`Rétablir « ${diff.diff.file.path} » depuis la base du brouillon de « ${functionName} » ? Un chemin ajouté sera retiré.`} disabled={locked} action={async()=>{if(!await askLeave())return;const target=diff.diff.file.path;await saveMutation({file:{action:'revert',path:target}});if(pathRef.current===target)clearFile();}}/></>}

      </div>}
    </Section>}

    {draft&&<Section title="Publier le brouillon enregistré">
      <div className="stack"><Facts values={[["Handler publié",code(draft.handler)],["Base",hash(draft.base?.code_hash)]]}/>
        {dirty&&<p className="notice">Enregistrez vos saisies avant de publier.</p>}
        <Confirm tone="primary" label="Publier le brouillon" message={`Publier le brouillon enregistré de « ${functionName} », base ${draft.base?.code_hash||'vide'}, handler ${draft.handler}, sans modifier sa cible promue ?`} disabled={locked||dirty||activeCandidate(candidate)||Boolean(candidateError)||candidateReading||Boolean(selected&&!candidate)} action={publish}/>
      </div>
    </Section>}
    {selected&&<Section title="Tentative suivie">
      <p className="mono">{selected}</p>{publishing&&<p role="status">Reconstruction, envoi et validation en cours…</p>}
      {candidateReading&&<p role="status">Lecture de la tentative…</p>}
      {!candidate&&!candidateError&&publishing&&<p>Préparation en cours. Le candidat n’est pas encore consultable.</p>}
      <ErrorMessage error={candidateError}/>
      {candidate&&<Candidate row={candidate} disabled={busy} abandon={async()=>{await api('/api/deployments/'+candidate.id,{method:'DELETE'});setCandidateRevision(v=>v+1);}}/>}
      {candidate?.state==='published'&&<div className="actions"><a href={withCatalogue(`/console/functions/${functionId}/invocation-urls?version=${candidate.code_hash}`)}>Adresses de la version publiée</a><a href={withCatalogue(`/console/functions/${functionId}/code?deployment=${candidate.id}`)}>Versions, promotion et retour à un hash</a></div>}
      <div className="actions"><button disabled={candidateReading} onClick={()=>setCandidateRevision(v=>v+1)}>Relire cette tentative</button>{!publishing&&!candidateReading&&!activeCandidate(candidate)&&<button onClick={()=>{setSelected('');setCandidate(null);setCandidateError(null);writeAddress({deployment:''});}}>Fermer le suivi</button>}</div>
    </Section>}

    {dialog==='source'&&<VersionChoice functionId={functionId} onClose={()=>setDialog(null)} choose={value=>chooseSurface('source',value)}/>}
    {dialog==='handler'&&draft&&<DialogForm title="Handler du brouillon" initial={{handler:draft.handler}} onClose={()=>setDialog(null)} onSubmit={value=>saveMutation({handler:value.handler})}>
      {(value,setValue)=><Field label="Handler" help="Chemin du module puis export, par exemple src/handler.run."><input required minLength={3} maxLength={256} value={value.handler} onChange={event=>setValue({handler:event.target.value})}/></Field>}
    </DialogForm>}
    {dialog==='file'&&<DialogForm title="Ajouter un fichier" initial={{path:''}} submitLabel="Ajouter le fichier" onClose={()=>setDialog(null)} onSubmit={async value=>{
      try {await api(prefix+'/code-draft/file?path='+encodeURIComponent(value.path));throw Object.assign(new Error('Ce fichier existe déjà. Ouvrez-le pour le modifier.'),{status:409});}
      catch(error){if(error.status!==404)throw error;}
      await saveMutation({file:{action:'write',path:value.path,text:''}});await openFile(value.path,{mode:'draft',skipGuard:true});
    }}>
      {(value,setValue)=><Field label="Chemin du nouveau fichier" help="Chemin relatif POSIX, 512 octets maximum ; un segment de 255 octets au plus."><input required maxLength={512} value={value.path} onChange={event=>setValue({path:event.target.value})}/></Field>}
    </DialogForm>}
    {leave&&<UnsavedChanges functionName={functionName} decide={decideLeave}/>}
  </div>;
}
