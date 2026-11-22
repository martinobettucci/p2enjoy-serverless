// @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// Shared real SSO/API lifecycle; each campaign owns and purges its exact UUIDs.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,mkdtemp,readFile,writeFile,rename,rm} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {chromium,request} from 'playwright';

const execute=promisify(execFile);
export const base='https://serverless.lelabs.tech';
export const sha=value=>createHash('sha256').update(value).digest('hex');
export const match=value=>({'If-Match':String(value)});
export const endpoint=row=>'/api/functions/'+row.id;
export const delay=milliseconds=>new Promise(resolve=>setTimeout(resolve,milliseconds));
export function diagnosis(error) {
  return {type:error.name,message_sha256:sha(String(error.message)),
    source_line:String(error.stack || '').match(/execution-journal[^:]*:(\d+)/)?.[1]};
}

export async function privateInput() {
  const input=createInterface({input:process.stdin});
  try {
    const line=await new Promise((resolve,reject)=>{
      input.once('line',resolve);input.once('close',()=>reject(new Error('private_input_missing')));
    });
    const value=JSON.parse(line);
    assert(typeof value.username==='string' && typeof value.password==='string');return value;
  } finally {input.close();}
}

export async function until(action,label,seconds=90) {
  const deadline=Date.now()+seconds*1000;
  while(Date.now()<deadline) {
    const result=await action();if(result)return result;await delay(200);
  }
  throw new Error(label);
}

export async function adminConnection(browser,credentials) {
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  let admin;
  try {
    const page=await context.newPage();await page.goto(base);
    await page.getByRole('link',{name:'Se connecter avec le SSO',exact:true}).click();
    await page.waitForURL('https://oauth.lelabs.tech/**');
    await page.locator('input[name=username]').fill(credentials.username);
    await page.locator('input[type=password]').fill(credentials.password);
    await page.locator('input[name=login],input[type=submit],button[type=submit]').first().click();
    await page.waitForURL(base+'/**',{timeout:90000});
    await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
    const state=await context.storageState();
    state.cookies=state.cookies.filter(row=>row.domain==='serverless.lelabs.tech' && row.name==='__Host-p2-session');
    state.origins=[];assert.equal(state.cookies.length,1);
    admin=await request.newContext({baseURL:base,storageState:state,timeout:120000});
    const session=await (await admin.get('/api/session')).json();assert(session.authenticated);
    return {context,page,admin,session};
  } catch(error) {await admin?.dispose();await context.close();throw error;}
  finally {credentials=null;}
}

export class JournalCampaign {
  constructor(kind) {
    assert(['api','ui'].includes(kind));
    this.kind=kind;this.id=randomUUID();this.prefix='execution-journal-'+kind+'-'+this.id;
    this.output=new URL('../.local/e2e/',import.meta.url);this.report=new URL(this.prefix+'.json',this.output);
    this.checks=[];this.observations=[];this.captures={};this.creations=[];this.functions=[];
    this.services=[];this.tokens=[];this.deployments=[];this.cleanupErrors=[];
    this.pendingOperations=[];this.saveTail=Promise.resolve();
    this.localCloseTail=Promise.resolve();this.localClosed=new Set();
    this.completed=false;this.cleanup=false;this.scenariosPassed=false;this.stage=null;this.failure=null;
  }

  // @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async save() {
    this.saveTail=this.saveTail.then(async()=>{
      await mkdir(this.output,{recursive:true,mode:0o700});
      const pending=new URL(this.report.href+'.pending');
      await writeFile(pending,JSON.stringify({campaign:this.id,kind:this.kind,target:base,
        completed:this.completed,cleanup:this.cleanup,checks:this.checks,observations:this.observations,captures:this.captures,
        creations:this.creations,namespace_id:this.namespace?.id,service_ids:this.services.map(row=>row.id),
        function_ids:this.functions.map(row=>row.id),deployment_ids:this.deployments,
        cleanup_errors:this.cleanupErrors,local_closed:[...this.localClosed],skipped:0,stage:this.stage,failure:this.failure},null,2)+'\n',{mode:0o600});
      await rename(pending,this.report);
    });
    await this.saveTail;
  }

  // @spec docs/BACKLOG.md#sls-129 | docs/EXECUTION_LOGS.md#console-et-manuel
  // @verifies docs/BACKLOG.md#sls-129
  async capture(name,page=this.page,target) {
    assert(/^[a-z0-9-]+$/.test(name));
    if(target) {
      await target.scrollIntoViewIfNeeded();const box=await target.boundingBox(),viewport=page.viewportSize();
      assert(box && viewport && box.x>=-1 && box.y>=-1 && box.x+box.width<=viewport.width+1 && box.y+box.height<=viewport.height+1,'capture_target_outside_viewport');
      this.observations.push({scenario:'capture-framing',name,viewport,target:box,fully_in_view:true});
    }
    const filename='execution-journal-'+this.kind+'-'+this.id+'-'+name+'.jpg',destination=new URL(filename,this.output);
    await page.screenshot({path:destination.pathname,type:'jpeg',quality:85});this.captures[filename]=sha(await readFile(destination));await this.save();
  }

  async check(name,action) {
    this.stage=name;await this.save();
    try {await action();this.checks.push({name,status:'passed'});console.log('PASS',name);}
    catch(error){this.checks.push({name,status:'failed',...diagnosis(error)});throw error;}
    finally {await this.save();}
  }

  track(promise) {
    const owned=promise.then(value=>({value}),error=>({error}));
    this.pendingOperations.push(owned);return owned;
  }

  async joinPending() {await Promise.all(this.pendingOperations);}

  async open(credentials) {
    await mkdir(this.output,{recursive:true,mode:0o700});await this.save();
    this.work=await mkdtemp(new URL(this.prefix+'-',this.output).pathname);
    this.browser=await chromium.launch({headless:true});
    Object.assign(this,await adminConnection(this.browser,credentials));credentials=null;
    this.caller=await request.newContext({baseURL:base,timeout:120000});
    this.namespace=await this.create('namespace','/api/namespaces',{
      name:'execution-journal-'+this.kind+'-'+this.id.slice(0,8),description:this.id,
    });
  }

  async call(path,{method='GET',body,bytes,token,anonymous=false,status=200,headers={},json=true}={}) {
    const started=performance.now(),expected=[status].flat();
    const technical=token!==undefined;
    const client=technical || anonymous?this.caller:this.admin;
    const response=await client.fetch(path,{method,data:bytes===undefined?body:bytes,headers:{
      ...(technical?{'X-Serverless-Token':token}:anonymous?{}:{Origin:base,'X-CSRF-Token':this.session.csrf_token}),...headers,
    }});
    // @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
    // @verifies docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
    if(!expected.includes(response.status())) {
      try {
        const pathname=new URL(path,base).pathname;
        const template=pathname.replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi,'{id}');
        const publicRoute=template==='/healthz' || /^\/(?:api|auth)(?:\/(?:[a-z][a-z-]*|\{id\}))*$/.test(template);
        const raw=await response.body(),observation={scenario:'unexpected-control-http-result',method,
          ...(publicRoute?{route:template}:{route_sha256:sha(pathname)}),expected_statuses:expected,
          http_status:response.status(),elapsed_ms:performance.now()-started,body_bytes:raw.length,body_sha256:sha(raw)};
        if(raw.length<=16384) {
          let value;try{value=JSON.parse(raw.toString('utf8'));}catch(error){if(!(error instanceof SyntaxError))throw error;}
          if(typeof value?.error==='string') {
            observation.error_sha256=sha(value.error);
            if(['log_read_timeout','log_read_unavailable','log_policy_changed','log_collection_changed','log_snapshot_expired','log_authorization_context_changed','log_cursor_invalid','log_cursor_foreign'].includes(value.error))observation.public_error=value.error;
          }
        }
        this.observations.push(observation);await this.save();
      } catch(error) {this.observations.push({scenario:'unexpected-http-observation-failed',...diagnosis(error)});}
    }
    assert(expected.includes(response.status()),`unexpected_http_status:${method}:${response.status()}`);
    const data=json?await response.json():await response.body();
    return {data,status:response.status(),headers:response.headers()};
  }

  async value(path,options) {return (await this.call(path,options)).data;}

  async create(kind,path,body) {
    for(let offset=0;;offset+=100) {
      assert(offset<=10000,'creation_inventory_bound');
      const data=await this.value(path+'?limit=100&offset='+offset);
      assert(!data.items.some(row=>row.name===body.name),'owned_name_not_free');
      if(data.items.length<100)break;
    }
    const intent={kind,path,name:body.name,absent_before_post:true};this.creations.push(intent);await this.save();
    const response=await this.admin.post(path,{data:body,headers:{Origin:base,'X-CSRF-Token':this.session.csrf_token}});
    intent.status=response.status();await this.save();assert.equal(intent.status,201);
    const row=await response.json();assert.equal(typeof row.id,'string');intent.id=row.id;await this.save();return row;
  }

  async service(name,configuration) {
    const row=await this.create('service','/api/namespaces/'+this.namespace.id+'/services',{name,description:this.id});
    this.services.push(row);
    if(configuration)await this.value('/api/services/'+row.id+'/configuration',{method:'PUT',headers:match(row.updated_at),body:configuration});
    return row;
  }

  async function(service,name,config={},configuration={}) {
    const row=await this.create('function','/api/services/'+service.id+'/functions',{
      name,config:{handler:'execution-journal.cjs.handler',timeout_seconds:10,idle_seconds:0,cpu:.2,memory_mib:256,...config},configuration,
    });
    this.functions.push(row);return row;
  }

  async mint(service,rights=['read'],functionIds=null,extra={}) {
    const row=await this.create('token','/api/services/'+service.id+'/tokens',{
      name:'journal-'+this.kind+'-'+this.tokens.length,rights,function_ids:functionIds,...extra,
    });
    this.tokens.push(row);return row;
  }

  async publish(fn,marker,{handler='execution-journal.cjs.handler',uploadStatus=200}={}) {
    const archive=this.work+'/'+randomUUID()+'.zip';
    const receipt=JSON.parse((await execute('python3',['-B','e2e/execution-journal-package.py',archive,marker])).stdout);
    assert(receipt.all_crc_valid && receipt.entries===2);
    const current=await this.value(endpoint(fn)),identifier=randomUUID();
    this.deployments.push(identifier);await this.save();
    await this.value(endpoint(fn)+'/code-deployments',{method:'POST',status:201,headers:match(current.updated_at),body:{
      deployment_id:identifier,handler,events:{http:[{path:'journal',implicit:true,methods:['GET','POST']}],schedules:[]},
    }});
    const result=await this.value('/api/deployments/'+identifier+'/artifact',{method:'PUT',status:uploadStatus,
      bytes:await readFile(archive),headers:{'Content-Type':'application/zip'}});
    this.observations.push({scenario:'original-package',function_id:fn.id,deployment_id:identifier,receipt,status:uploadStatus});
    if(uploadStatus===200)assert.equal(result.state,'published');return result;
  }

  async promote(fn,hash) {
    await this.value(endpoint(fn)+'/versions/'+hash+'/promote',{method:'POST',headers:match((await this.value(endpoint(fn))).updated_at)});
  }

  async invoke(fn,token,body={},status=200,headers={}) {
    const result=await this.call('/invoke/'+fn.id,{method:'POST',token:typeof token==='string'?token:token.token,
      body,status,headers:{Origin:base,...headers}});
    const identifier=result.headers['x-serverless-request-id'];assert(identifier);
    this.observations.push({scenario:'gateway-call',function_id:fn.id,request_id:identifier,http_status:result.status,
      code_hash:result.headers['x-serverless-code-hash'] || null});
    return {...result,id:identifier};
  }

  async terminal(fn,identifier) {
    return until(async()=>{const row=await this.value(endpoint(fn)+'/invocations/'+identifier);return row.completed_at?row:null;},'invocation_not_terminal');
  }

  async purge(fn) {
    const response=await this.admin.get(endpoint(fn));
    if(response.status()===200)await this.value(endpoint(fn),{method:'DELETE'});else assert.equal(response.status(),404);
    await until(async()=>!(await this.value('/api/archives/'+fn.id)).storage_operation,'archive_operation_pending');
    const row=await this.value('/api/archives/'+fn.id);
    if(!row.purged_at) {
      const operation=await this.value('/api/archives/'+fn.id+'/purge',{method:'POST',status:[200,202],
        headers:match(row.updated_at),body:{operation_id:randomUUID(),confirm_name:row.name}});
      await until(async()=>{const current=await this.value('/api/storage-operations/'+operation.id);assert.notEqual(current.state,'aborted');return current.state==='completed';},'physical_purge_pending');
    }
    const final=await this.value('/api/archives/'+fn.id);assert(final.purged_at && final.artifact_bytes===0 && !final.storage_operation);
  }

  async reconcile() {
    for(const intent of this.creations) {
      if(!intent.id && (intent.status===undefined || intent.status===201 || intent.status>=500)) {
        for(let offset=0;;offset+=100) {
          assert(offset<=10000,'reconcile_inventory_bound');
          const data=await this.value(intent.path+'?limit=100&offset='+offset),rows=data.items.filter(row=>row.name===intent.name);
          assert(rows.length<=1);if(rows.length){intent.id=rows[0].id;break;}if(data.items.length<100)break;
        }
      }
      if(intent.id) {
        if(intent.kind==='namespace' && !this.namespace)this.namespace={id:intent.id};
        if(intent.kind==='service' && !this.services.some(row=>row.id===intent.id))this.services.push({id:intent.id});
        if(intent.kind==='function' && !this.functions.some(row=>row.id===intent.id))this.functions.push({id:intent.id});
        if(intent.kind==='token' && !this.tokens.some(row=>row.id===intent.id))this.tokens.push({id:intent.id});
      }
    }
    await this.save();
  }

  async retireServices() {
    for(const fn of this.functions)await this.purge(fn);
    for(const service of this.services) {
      if(service.retired)continue;
      await this.value('/api/services/'+service.id,{method:'DELETE'});service.retired=true;
    }
    await this.save();
  }

  // @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async closeLocal() {
    this.localCloseTail=this.localCloseTail.then(async()=>{
      for(const [phase,value,close] of [
        ['caller',this.caller,()=>this.caller.dispose()],['admin',this.admin,()=>this.admin.dispose()],
        ['browser-context',this.context,()=>this.context.close()],['browser',this.browser,()=>this.browser.close()],
        ['temporary-package',this.work,()=>rm(this.work,{recursive:true,force:true})],
      ]) {
        if(!value || this.localClosed.has(phase))continue;
        try {await close();this.localClosed.add(phase);}
        catch(error){this.cleanupErrors.push({phase,...diagnosis(error)});}
      }
      if(this.cleanupErrors.length){this.cleanup=false;this.completed=false;}
    });
    await this.localCloseTail;
  }

  // @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async close({nativeCleanup}={}) {
    try {
      assert((this.nativeSqlBarriers || []).every(owner=>owner.closed),'native_readers_not_joined_before_cleanup');
      assert((this.nativeCuts || []).every(owner=>owner.closed),'native_control_cut_not_joined_before_cleanup');
      await this.joinPending();
      if(this.admin && this.session) {
        const attempt=async(phase,action)=>{try{await action();}catch(error){this.cleanupErrors.push({phase,...diagnosis(error)});}};
        await attempt('reconcile',()=>this.reconcile());
        for(const fn of [...this.functions].reverse())await attempt('purge:'+fn.id,()=>this.purge(fn));
        for(const token of this.tokens)await attempt('revoke:'+token.id,()=>this.value('/api/tokens/'+token.id+'/revoke',{method:'POST'}));
        if(!this.cleanupErrors.length) {
          for(const service of [...this.services].reverse())await attempt('service:'+service.id,()=>service.retired?
            this.value('/api/services/'+service.id,{status:404}):this.value('/api/services/'+service.id,{method:'DELETE'}));
          if(this.namespace)await attempt('namespace',()=>this.value('/api/namespaces/'+this.namespace.id,{method:'DELETE'}));
          if(this.namespace)await attempt('native-cleanup',async()=>{assert.equal(typeof nativeCleanup,'function','native_cleanup_required');await nativeCleanup();this.nativeCleanupConfirmed=true;});
        }
        await attempt('logout',()=>this.value('/auth/logout',{method:'POST'}));
      }
    } finally {
      await this.closeLocal();
      this.cleanup=Boolean(this.nativeCleanupConfirmed && !this.cleanupErrors.length);
      this.completed=this.scenariosPassed && this.cleanup && !this.failure;await this.save();
    }
  }
}
