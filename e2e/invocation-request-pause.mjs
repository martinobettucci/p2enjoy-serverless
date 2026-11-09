// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#barrière-native-de-pause-et-libération
// @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#barrière-native-de-pause-et-libération
// All helpers exercise original fixtures through the real platform and native observer.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,mkdtemp,cp,rm} from 'node:fs/promises';
import {spawn,execFile} from 'node:child_process';
import {createInterface} from 'node:readline';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {request} from 'playwright';

const root=fileURLToPath(new URL('../',import.meta.url)),out=path.join(root,'.local/e2e');
const base='https://serverless.lelabs.tech',nonce=randomUUID(),prefix='invocation-route-pause-'+nonce.slice(0,8);
const ssh=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const helper='/srv/p2enjoy-serverless/e2e/invocation-request-pause.py';
const checks=[],observations=[],guards=[],cleanupErrors=[],tokens=[],operatorErrors=[];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let admin,caller,session,namespace,service,fn,revision,work,read,image,completed=false,purged,failure;
await mkdir(out,{recursive:true,mode:0o700});
const report=path.join(out,'invocation-request-pause.json');
await writeFile(report,JSON.stringify({completed:false,checks:[],skipped:0})+'\n');
async function until(action,message,timeout=40000){
  const deadline=Date.now()+timeout;
  while(true){const value=await action();if(value)return value;assert(Date.now()<deadline,message);await sleep(100);}
}
function command(file,args,options={}){
  return new Promise(resolve=>{
    const child=execFile(file,args,{cwd:root,timeout:180000,maxBuffer:2*1024*1024,...options},(error,stdout,stderr)=>resolve({code:error?.code??0,stdout,stderr}));
    child.stdin.end();
  });
}
async function api(url,{method='GET',body,status=200,headers={}}={}){
  const response=await admin.fetch(url,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??'',...headers}});
  assert((Array.isArray(status)?status:[status]).includes(response.status()),'platform_api_status');
  return response.json();
}
function args(mode,extra=[]){return ['python3','-B',helper,mode,namespace.id,service.id,fn.id,nonce,image,...extra];}
async function remote(mode,unit){
  const result=await command('ssh',[...ssh,...args(mode,[unit])]);
  if(result.code!==0)operatorErrors.push({mode,exit_code:result.code,stderr:result.stderr});
  assert.equal(result.code,0,'pause_remote_operator_failed');return JSON.parse(result.stdout);
}
async function quiet(){
  await until(async()=>{
    const all=await api('/api/functions?limit=100');assert.equal(all.total,1);assert.equal(all.items[0].id,fn.id);
    const instances=await api(`/api/functions/${fn.id}/instances?limit=100`),calls=await api(`/api/functions/${fn.id}/invocations?limit=100`);
    return !instances.items.length&&!calls.items.some(row=>['receiving','queued','admitted','running'].includes(row.state));
  },'fixture_not_quiet');
}
async function arm(mode){
  await quiet();
  const child=spawn('ssh',[...ssh,...args(mode)],{cwd:root,stdio:['pipe','pipe','pipe']});
  const events=[];let ended=false,exitCode,stderr='',protocolError=false;
  const lines=createInterface({input:child.stdout});
  lines.on('line',line=>{try{events.push(JSON.parse(line));}catch{protocolError=true;}});
  child.stderr.on('data',bytes=>{stderr+=bytes.toString();});child.stdin.on('error',()=>{});
  const done=new Promise(resolve=>{
    child.once('close',code=>{ended=true;exitCode=code;resolve(code);});
    child.once('error',()=>{ended=true;exitCode=-1;resolve(-1);});
  });
  const value={mode,events,restored:false,diagnostic:()=>({mode,events,exit_code:exitCode,stderr,restored:value.restored}),
    async wait(event){return until(()=>{assert(!protocolError,'native_protocol_invalid');const row=events.find(v=>v.event===event);assert(row||!ended,'native_observer_ended_before_gate');return row;},'native_event_missing:'+event);},
    send(text){child.stdin.write(text+'\n');},
    async finish(){
      const code=await done;
      assert(mode==='pause'?code===0:[137,255].includes(code),'native_helper_exit');
      if(mode==='loss')assert(events.some(v=>v.event==='observer-loss'&&v.signal==='SIGKILL'));
      const armed=events.find(v=>v.event==='guard-armed');assert(armed);
      const resumed=await until(async()=>{
        const v=await remote('evidence',armed.unit);
        return v.event==='resumed'&&['inactive','unknown'].includes(v.service_state)?v:false;
      },'independent_resume_missing',40000);
      assert(resumed.healthy&&resumed.tracer_absent&&resumed.control_start_unchanged&&resumed.reference_unchanged);
      assert.equal(resumed.independent,mode==='loss');
      if(mode==='loss')assert(resumed.observer_gone);
      const disarmed=await remote('disarm',armed.unit);assert(['inactive','unknown'].includes(disarmed.timer_state)&&['inactive','unknown'].includes(disarmed.service_state));
      assert(!tokens.some(token=>JSON.stringify(events).includes(token)||stderr.includes(token)));
      value.restored=true;value.receipt={mode,events,exit_code:code,resumed:disarmed};return value.receipt;
    },
    async recover(){
      child.stdin.end();
      const armed=events.find(v=>v.event==='guard-armed');
      if(armed){
        const resumed=await remote('recover',armed.unit);await done;
        assert(resumed.healthy&&resumed.tracer_absent&&resumed.control_start_unchanged&&resumed.reference_unchanged);
        assert(['inactive','unknown'].includes(resumed.timer_state)&&['inactive','unknown'].includes(resumed.service_state));
        value.restored=true;
      }
      else {await done;assert.fail('guard_identity_unknown_fixture_retained');}
    }};
  guards.push(value);await value.wait('armed');return value;
}
async function check(name,action){
  try{await action();checks.push({name,status:'passed'});console.log('PASS',name);}
  catch(error){checks.push({name,status:'failed',error:error.name});throw error;}
}
try{
  admin=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(path.join(out,'admin-session.json'),'utf8')),timeout:120000});
  caller=await request.newContext({baseURL:base,timeout:120000});
  session=await(await admin.get('/api/session')).json();assert(session.authenticated,'real_admin_session_required');
  assert.equal((await api('/api/functions?limit=1')).total,0);
  const inspected=await command('ssh',[...ssh,'runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api']);
  assert.equal(inspected.code,0);image=inspected.stdout.trim();assert(/^sha256:[0-9a-f]{64}$/.test(image));
  namespace=await api('/api/namespaces',{method:'POST',body:{name:prefix,description:nonce},status:201});
  service=await api(`/api/namespaces/${namespace.id}/services`,{method:'POST',body:{name:'request-pause-fixture',description:nonce},status:201});
  const full=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'publish-pause-fixture',rights:['read','create','update']},status:201})).token;tokens.push(full);
  work=await mkdtemp(path.join(out,'invocation-request-code-'));
  await cp(path.join(root,'qualification/artifacts/invocation-addresses.cjs'),path.join(work,'handler.cjs'));
  await writeFile(path.join(work,'revision.json'),JSON.stringify({name:'pause'}));
  await writeFile(path.join(work,'serverless.yml'),JSON.stringify({service:service.name,provider:{name:'p2enjoy',runtime:'node24',minScale:0,maxScale:1,p2enjoy:{idle_seconds:1}},functions:{'route-entry':{handler:'handler.handler'}},package:{patterns:['!**','*.cjs','revision.json']}}));
  const deployed=await command('python3',['-B','-m','adapter','deploy','--config',path.join(work,'serverless.yml'),'--service',service.id],{env:{...process.env,P2_SERVERLESS_URL:base,P2_SERVERLESS_TOKEN:full}});
  assert.equal(deployed.code,0);assert(!tokens.some(token=>deployed.stdout.includes(token)||deployed.stderr.includes(token)));
  const result=JSON.parse(deployed.stdout);assert(result.completed&&result.results.length===1);fn={id:result.results[0].function_id};revision=result.results[0].revision_id;assert(revision);
  read=(await api(`/api/services/${service.id}/tokens`,{method:'POST',body:{name:'read-pause-fixture',rights:['read'],function_ids:[fn.id]},status:201})).token;tokens.push(read);
  for(const mode of ['pause','loss'])await check(mode==='pause'?'GET HTTPS réellement retenu puis libéré, même révision et deux domaines':'SIGKILL du traceur retenu : même GET repris par le timer indépendant',async()=>{
    const observer=await arm(mode);let settled=false;
    const pending=caller.get(`/api/functions/${fn.id}/invocation-urls?limit=5&offset=0`,{headers:{'X-Serverless-Token':read}});
    pending.then(()=>{settled=true;},()=>{settled=true;});observer.pending=pending;
    const gated=await observer.wait('gated');assert.equal(gated.revision_id,revision);assert(!settled,'real_request_must_be_held');
    observer.send(mode==='pause'?'release':'lose-observer');
    const receipt=await observer.finish();const response=await pending;assert.equal(response.status(),200);
    const catalogue=await response.json();assert.equal(catalogue.source.state,'available');assert.equal(catalogue.total,2);assert.equal(catalogue.revision_id,revision);
    assert.deepEqual(catalogue.items.map(v=>v.domain).sort(),['functions.lelabs.tech','serverless.lelabs.tech']);
    observations.push({mode,gated,receipt,catalogue,admitted_request_completed:true,request_was_pending_at_gate:true});
  });
  completed=true;
}catch(error){failure={name:error.name,message:error.message};throw error;}
finally{
  for(const guard of guards)if(!guard.restored){try{await guard.recover();}catch(error){cleanupErrors.push({resource:'native-guard',error:error.name});}}
  await Promise.allSettled(guards.map(v=>v.pending).filter(Boolean));
  if(!cleanupErrors.length&&admin&&session?.authenticated){
    try{
      if(service){
        const rows=(await api(`/api/services/${service.id}/functions?limit=100`)).items;assert(rows.length<=1&&rows.every(v=>v.name==='route-entry'));
        for(const row of rows){
          fn??={id:row.id};await api(`/api/functions/${row.id}`,{method:'DELETE'});const archive=await api(`/api/archives/${row.id}`);
          let operation=await api(`/api/archives/${row.id}/purge`,{method:'POST',body:{operation_id:randomUUID(),confirm_name:archive.name},headers:{'If-Match':String(archive.updated_at)},status:[200,202]});
          await until(async()=>{operation=await api(`/api/storage-operations/${operation.id}`);assert.notEqual(operation.state,'failed');return operation.state==='completed';},'purge_not_completed',90000);
          purged={function_id:row.id,operation_id:operation.id};
        }
        await api(`/api/services/${service.id}`,{method:'DELETE'});
      }
      if(namespace)await api(`/api/namespaces/${namespace.id}`,{method:'DELETE'});
    }catch(error){cleanupErrors.push({resource:'fixture',error:error.name});}
  }
  if(work&&!cleanupErrors.length)await rm(work,{recursive:true,force:true});
  await admin?.dispose();await caller?.dispose();
  const value={completed:completed&&!cleanupErrors.length,cleanup:!cleanupErrors.length,checks,observations,skipped:0,cleanup_errors:cleanupErrors,
    prefix,ownership_nonce:nonce,namespace_id:namespace?.id,service_id:service?.id,function_ids:fn?[fn.id]:[],revision_id:revision,purged,
    guard_receipts:guards.map(v=>v.receipt??v.diagnostic()),operator_errors:operatorErrors,failure,route_changes:0,work_retained:Boolean(work&&cleanupErrors.length)};
  const raw=JSON.stringify(value,null,2);assert(!tokens.some(token=>raw.includes(token)),'private_credential_in_report');
  await writeFile(report,raw+'\n');assert.equal(cleanupErrors.length,0,'cleanup_required');
}
