// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation | docs/FUNCTION_VERSION_REGISTRY.md#lecture-autorisée
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,mkdtemp,cp,rename,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';

const run=promisify(execFile),root=new URL('../',import.meta.url),output=new URL('../.local/e2e/',import.meta.url);
const base='https://serverless.lelabs.tech',phase=process.argv[2],stateFile=new URL('function-version-registry-private.json',output);
assert(['prepare','verify','persist','cleanup','cleanup-local'].includes(phase));
const reportFile=new URL(`function-version-registry-${phase}.json`,output),checks=[],evidence=[];
let state,admin,caller,session,completed=false;
await mkdir(output,{recursive:true,mode:0o700});
async function save(){await writeFile(reportFile,JSON.stringify({target:base,phase,completed,skipped:0,checks,evidence,
  namespace_id:state?.namespace?.id,function_ids:state?.functions?.map(f=>f.id),revision_ids:state?.revisions?.map(r=>r.id)},null,2)+'\n',{mode:0o600});}
async function persist(){const pending=new URL('function-version-registry-private.pending',output);await writeFile(pending,JSON.stringify(state)+'\n',{mode:0o600});await rename(pending,stateFile);}
async function check(name,action){try{await action();checks.push({name,status:'passed'});console.log('PASS',name);await save();}catch(e){checks.push({name,status:'failed',error:e.name});throw e;}}
async function call(url,{method='GET',body,bytes,headers={},token,anonymous=false,status=200}={}){
  const r=await (token||anonymous?caller:admin).fetch(url,{method,data:bytes??body,headers:{
    ...(token?{'X-Serverless-Token':token}:anonymous?{}:{Origin:base,'X-CSRF-Token':session?.csrf_token}),
    ...(bytes?{'Content-Type':'application/zip'}:{}),...headers}});
  assert([status].flat().includes(r.status()),`${method} ${url}: ${r.status()} au lieu de ${status}`);
  const text=await r.text();assert(!state?.secret || !text.includes(state.secret),'Secret exposé');return JSON.parse(text);
}
async function until(action){const end=Date.now()+120000;while(Date.now()<end){const v=await action();if(v)return v;await new Promise(r=>setTimeout(r,200));}assert.fail('Cycle de vie réel non terminé');}
async function token(service,name,rights,extra={}){const r=await call(`/api/services/${service.id}/tokens`,{method:'POST',status:201,body:{name,rights,...extra}});state.tokens.push(r);await persist();return r;}
async function create(name){const fn=await call(`/api/services/${state.service.id}/functions`,{method:'POST',status:201,body:{name,
  config:{handler:'version-registry.handler',memory_mib:128,timeout_seconds:3,idle_seconds:1,storage:{data:{enabled:true,quota_mib:8}}},
  configuration:{environment:{REGISTRY_LOCAL:'function-value'},secrets:{}}}});state.functions.push(fn);await persist();return fn;}
async function bundle(value){const project=new URL(`code-${value}/`,state.work);await mkdir(project,{recursive:true});
  await cp(new URL('../qualification/artifacts/version-registry.cjs',import.meta.url),new URL('version-registry.cjs',project));
  await writeFile(new URL('version-marker.json',project),JSON.stringify({value})+'\n');
  const config=new URL('serverless.yml',project);await writeFile(config,JSON.stringify({service:'version-registry',provider:{name:'p2enjoy',runtime:'nodejs24.x'},functions:{probe:{handler:'version-registry.handler'}},package:{patterns:['!**','version-registry.cjs','version-marker.json']}}));
  await run('python3',['-B','-m','adapter','package','--config',config.pathname],{cwd:root.pathname});
  const descriptor=JSON.parse(await readFile(new URL('.serverless-p2/deployment.json',project),'utf8'));
  return new URL('.serverless-p2/'+descriptor.artifacts.probe.file,project).pathname;
}
async function publish(fn,file){const current=await call(`/api/functions/${fn.id}`),candidate=await call(`/api/functions/${fn.id}/code-deployments`,{method:'POST',status:201,
  headers:{'If-Match':String(current.updated_at)},body:{deployment_id:randomUUID(),handler:'version-registry.handler'}});
  const published=await call(`/api/deployments/${candidate.id}/artifact`,{method:'PUT',bytes:await readFile(file)});
  assert.equal(published.state,'published');assert(published.validation.valid&&published.validation.container_removed);
  const revision=(await call(`/api/functions/${fn.id}/revisions`)).items.find(r=>r.id===published.revision_id);assert(revision);
  state.revisions.push(revision);await persist();return revision;
}
async function expectedHash(revision,file){const execution=new URL('execution-'+revision.id+'.json',state.work),destination=new URL('extracted-'+revision.id+'/',state.work);
  await writeFile(execution,JSON.stringify(Object.fromEntries(['handler','runtime','architecture','image_id','events'].map(k=>[k,revision[k]]))));
  const {stdout}=await run('python3',['-B','function_code_hash.py','--archive',file,'--destination',destination.pathname,'--execution',execution.pathname],{cwd:root.pathname});
  const hash=JSON.parse(stdout).code_hash;await removeDirectory(destination);return hash;
}
async function removeDirectory(directory){
  await run('python3',['-B','-c',"import os,sys;from pathlib import Path;from control.app.artifacts import open_directory,remove_tree;p=Path(sys.argv[1]);s=p.lstat();fd=open_directory(p.parent)\ntry:remove_tree(fd,p.name,(s.st_dev,s.st_ino))\nfinally:os.close(fd)",new URL(directory).pathname],{cwd:root.pathname});
}
async function removeWork(){const directory=new URL(state.work);assert.equal(new URL('../',directory).pathname,outPath());assert(/^function-version-registry-[A-Za-z0-9]+$/.test(directory.pathname.split('/').filter(Boolean).at(-1)));await removeDirectory(directory);}
function outPath(){return output.pathname;}
async function invoke(fn,marker){const r=await call(`/invoke/${fn.id}`,{token:state.read.token});assert.equal(r.marker,marker);assert.equal(r.common,'service-value');assert.equal(r.local,'function-value');assert.equal(r.secret_sha256,createHash('sha256').update(state.secret).digest('hex'));return r;}
async function idle(fn){await until(async()=>!(await call(`/api/functions/${fn.id}/instances`)).items.some(r=>r.state!=='stopped'));}
async function purge(fn){await call(`/api/functions/${fn.id}`,{method:'DELETE'});await until(async()=>!(await call(`/api/archives/${fn.id}`)).storage_operation);
  const row=await call(`/api/archives/${fn.id}`),op=await call(`/api/archives/${fn.id}/purge`,{method:'POST',status:[200,202],headers:{'If-Match':String(row.updated_at)},body:{operation_id:randomUUID(),confirm_name:row.name}});
  const done=await until(async()=>{const r=await call(`/api/storage-operations/${op.id}`);assert.notEqual(r.state,'aborted');return r.state==='completed'?r:null;});
  const archive=await call(`/api/archives/${fn.id}`);assert.equal(archive.revision_count,0);assert.equal(archive.artifact_bytes,0);evidence.push({purged_function_id:fn.id,operation_id:done.id});
}
await save();
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('admin-session.json',output),'utf8')),timeout:180000});
  caller=await request.newContext({baseURL:base,timeout:180000});session=await call('/api/session');assert.equal(session.authenticated,true,'Session SSO réelle requise');
  if(phase==='prepare'){
    state={secret:'registry-private-'+randomUUID(),tokens:[],functions:[],revisions:[],work:new URL((await mkdtemp(new URL('function-version-registry-',output).pathname))+'/','file:').href};await persist();
    await check('Schéma antérieur : A, alias A, B et rollback réels avec données',async()=>{
      const prefix='version-registry-'+randomUUID().slice(0,8);state.namespace=await call('/api/namespaces',{method:'POST',status:201,body:{name:prefix}});await persist();
      state.service=await call(`/api/namespaces/${state.namespace.id}/services`,{method:'POST',status:201,body:{name:'version-history'}});await persist();
      state.service=await call(`/api/services/${state.service.id}/configuration`,{method:'PUT',headers:{'If-Match':String(state.service.updated_at)},body:{environment:{REGISTRY_COMMON:'service-value'},secrets:{REGISTRY_SECRET:state.secret}}});
      state.read=await token(state.service,'invocation-and-history',['read']);state.live=await create('persistent-code-history');
      state.aFile=await bundle('A');state.bFile=await bundle('B');
      const a=await publish(state.live,state.aFile),alias=await publish(state.live,state.aFile),b=await publish(state.live,state.bFile);
      assert.notEqual(a.id,alias.id);assert.equal(a.archive_sha256,alias.archive_sha256);
      state.hashA=await expectedHash(a,state.aFile);state.hashB=await expectedHash(b,state.bFile);assert.notEqual(state.hashA,state.hashB);
      const before=await invoke(state.live,'B'),fn=await call(`/api/functions/${state.live.id}`);
      await call(`/api/functions/${fn.id}/rollback`,{method:'POST',headers:{'If-Match':String(fn.updated_at)},body:{revision_id:alias.id}});
      const after=await invoke(fn,'A');assert.equal(after.counter,before.counter+1);state.counter=after.counter;state.active=alias.id;await idle(fn);await persist();
      evidence.push({aliases:[a.id,alias.id],other_revision:b.id,active_revision_id:state.active,hash_a:state.hashA,hash_b:state.hashB,counter:state.counter});
    });
    await check('Schéma antérieur : purge effective créant un tombstone sans inventaire',async()=>{state.purged=await create('purged-before-hash');await publish(state.purged,state.aFile);await purge(state.purged);await persist();});
  }else{
    state=JSON.parse(await readFile(stateFile,'utf8'));
    if(phase==='verify'){
      await check('Migration : alias, cible, code, configuration et données conservés',async()=>{
        const fn=await call(`/api/functions/${state.live.id}`);assert.equal(fn.active_revision_id,state.active);
        const revisions=(await call(`/api/functions/${fn.id}/revisions`,{token:state.read.token})).items;
        for(const old of state.revisions.filter(r=>r.function_id===fn.id)){
          const row=revisions.find(r=>r.id===old.id);assert(row);const {code_hash,...previous}=row;assert.deepEqual(previous,{...old,active:old.id===state.active});
          assert.equal(code_hash,old.archive_sha256===state.revisions[0].archive_sha256?state.hashA:state.hashB);
        }
        const data=await invoke(fn,'A');assert.equal(data.counter,state.counter+1);state.counter=data.counter;
        const versions=await call(`/api/functions/${fn.id}/versions`,{token:state.read.token});assert.equal(versions.total,2);assert.equal(versions.active_code_hash,state.hashA);assert.equal(versions.active_revision_id,state.active);
        const a=versions.items.find(r=>r.code_hash===state.hashA);assert.equal(a.revision_count,2);assert.equal(a.revision_id,state.active);assert(a.active&&a.state==='available');
        assert.deepEqual(Object.keys(versions).sort(),['function_id','service_id','active_revision_id','active_code_hash','items','total','limit','offset'].sort());
        evidence.push({migrated_versions:versions,counter:data.counter});await idle(fn);await persist();
      });
      await check('Registre : droits CRUD, portée, révocation, inconnue et bornes',async()=>{
        const id=state.live.id,path=`/api/functions/${id}/versions`;
        await call(path,{anonymous:true,status:401});await call(path,{token:'invalid',status:401});
        for(const right of ['create','update','delete']){const t=await token(state.service,right,[right]);await call(path,{token:t.token,status:403});}
        state.peer=await create('other-function');const scoped=await token(state.service,'other-function-read',['read'],{function_ids:[state.peer.id]});await call(path,{token:scoped.token,status:403});
        const foreign=await call(`/api/namespaces/${state.namespace.id}/services`,{method:'POST',status:201,body:{name:'foreign-service'}});state.foreign=foreign;await persist();
        const foreignRead=await token(foreign,'foreign-read',['read']);await call(path,{token:foreignRead.token,status:403});
        const allowed=await token(state.service,'scoped-history',['read'],{function_ids:[id]});assert.equal((await call(path,{token:allowed.token})).total,2);
        await call(`/api/tokens/${allowed.id}/revoke`,{method:'POST'});await call(path,{token:allowed.token,status:401});
        await call(`/api/functions/${randomUUID()}/versions`,{status:404});await call(`/api/functions/${randomUUID()}/versions`,{token:state.read.token,status:403});
        for(const query of ['limit=0','limit=101','offset=-1','offset=10001','limit=word'])await call(path+'?'+query,{token:state.read.token,status:422});
        const empty=await call(`/api/functions/${state.peer.id}/versions`,{token:state.read.token});assert.equal(empty.total,0);assert.equal(empty.active_code_hash,null);assert.deepEqual(empty.items,[]);
      });
      await check('Nouvelles publications : hash calculé serveur et pagination stable',async()=>{
        const fn=state.live;
        for(const label of ['C','D','E','F']){const file=await bundle(label),revision=await publish(fn,file),expected=await expectedHash(revision,file);assert.equal(revision.code_hash,expected);}
        const all=await call(`/api/functions/${fn.id}/versions?limit=100`);assert.equal(all.total,6);assert.equal(all.items.length,6);
        const pages=[];for(let offset=0;offset<7;offset+=2){const p=await call(`/api/functions/${fn.id}/versions?limit=2&offset=${offset}`,{token:state.read.token});assert.equal(p.total,6);assert.equal(p.limit,2);assert.equal(p.offset,offset);pages.push(...p.items);}
        assert.deepEqual(pages,all.items);assert.equal(new Set(pages.map(r=>r.code_hash)).size,6);
        const empty=await call(`/api/functions/${fn.id}/versions?offset=10000`);assert.deepEqual(empty.items,[]);assert.equal(empty.total,6);
        state.beforeRestart=all;await persist();evidence.push({versions:all});
      });
      await check('Alias supprimés : disponibilité groupée sans perdre le hash',async()=>{
        const fn=state.live,aliases=state.revisions.filter(r=>r.function_id===fn.id&&r.archive_sha256===state.revisions[0].archive_sha256);
        await call(`/api/functions/${fn.id}/revisions/${aliases[0].id}`,{method:'DELETE'});
        let a=(await call(`/api/functions/${fn.id}/versions`)).items.find(r=>r.code_hash===state.hashA);
        // Six versions put A on the second page; request the full bounded catalogue.
        a=(await call(`/api/functions/${fn.id}/versions?limit=100`)).items.find(r=>r.code_hash===state.hashA);assert.equal(a.state,'available');assert.equal(a.revision_id,aliases[1].id);assert.equal(a.revision_count,2);
        await call(`/api/functions/${fn.id}/revisions/${aliases[1].id}`,{method:'DELETE'});
        a=(await call(`/api/functions/${fn.id}/versions?limit=100`)).items.find(r=>r.code_hash===state.hashA);assert.equal(a.state,'deleted');assert.equal(a.revision_count,2);assert.equal(a.revision_id,aliases[0].id);assert.equal(a.active,false);
        state.beforeRestart=await call(`/api/functions/${fn.id}/versions?limit=100`);await persist();evidence.push({deleted_version:a});
      });
    }else if(phase==='persist'){
      await check('Redémarrage réel : catalogue et exécution persistants',async()=>{
        const versions=await call(`/api/functions/${state.live.id}/versions?limit=100`);assert.deepEqual(versions,state.beforeRestart);
        const after=await invoke(state.live,'F');assert.equal(after.counter,state.counter+1);state.counter=after.counter;await idle(state.live);await persist();evidence.push({counter:after.counter,versions});
      });
    }else if(phase==='cleanup-local'){
      await check('Reprise du seul nettoyage local des paquets readonly',async()=>{await removeWork();await rm(stateFile);evidence.push({local_work_removed:true,private_state_removed:true,no_remote_mutation:true});});
    }else{
      await check('Nettoyage par suppression et purge publiques des seules fixtures',async()=>{
        for(const fn of state.functions.filter(fn=>fn.id!==state.purged.id)){await idle(fn);await purge(fn);}
        for(const t of state.tokens)await call(`/api/tokens/${t.id}/revoke`,{method:'POST'});
        for(const service of [state.service,state.foreign].filter(Boolean))await call(`/api/services/${service.id}`,{method:'DELETE'});
        await call(`/api/namespaces/${state.namespace.id}`,{method:'DELETE'});await removeWork();await rm(stateFile);
      });
    }
  }
  completed=true;
}finally{await save();await admin?.dispose();await caller?.dispose();}
