// @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @spec docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-120 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// @verifies docs/BACKLOG.md#sls-072 | docs/BACKLOG.md#sls-120 | docs/EXECUTION_LOGS.md#api-droits-et-snapshots | docs/EXECUTION_LOGS.md#collecte-et-événements
// Real HTTPS cases. This module defines cases; only the serial campaign runs them.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {request} from 'playwright';
import {base,endpoint,match,until,delay,sha,adminConnection,diagnosis} from './execution-journal-harness.mjs';
import {inspectJournal,JournalSqlBarrier,JournalControlCut} from './execution-journal-native.mjs';

const logPath=fn=>endpoint(fn)+'/logs';
const policyPath=service=>'/api/services/'+service.id+'/log-policy';
const parameters=value=>new URLSearchParams(Object.entries(value).map(([key,item])=>[key,String(item)]));
const pending=(campaign,promise)=>campaign.track(promise);
const outcome=async promise=>{const result=await promise;if(result.error)throw result.error;return result.value;};

export class JournalApiCases {
  constructor(campaign,credentials) {this.c=campaign;this.credentials=credentials;this.calls={};this.secretService='journal-private-service-'+randomUUID();this.secretFunction='journal-private-function-'+randomUUID();}
  async log(fn,filters={},options={}) {return this.c.value(logPath(fn)+'?'+parameters(filters),options);}
  async policy(service,minutes,version) {
    const old=await this.c.value(policyPath(service));
    return this.c.value(policyPath(service),{method:'PUT',headers:match(version ?? old.version),body:{retention_minutes:minutes}});
  }
  async application(fn,id,options={}) {
    const query={source:'application',invocation:id};
    return this.exportRows(fn,query,options);
  }
  async exportRows(fn,filters={},options={}) {
    const first=await this.log(fn,filters,options);const rows=[];let offset=0;
    do {
      const lot=await this.c.call(logPath(fn)+'/export?'+parameters({snapshot:first.snapshot,format:'jsonl',offset}),{...options,json:false});
      assert(lot.headers['cache-control'].includes('no-store') && lot.headers['x-content-type-options']==='nosniff');
      assert.equal(lot.headers['x-log-snapshot'],first.snapshot);assert(lot.data.length<=1024**2);
      const selected=lot.data.toString('utf8').trimEnd();const items=selected?selected.split('\n').map(value=>JSON.parse(value)):[];
      assert.equal(Number(lot.headers['x-log-count']),items.length);assert(items.length<=1000);
      rows.push(...items);
      const partial=lot.headers['x-log-partial'];assert(['true','false'].includes(partial));
      const next=lot.headers['x-log-next-offset'];
      if(partial==='false'){assert.equal(next,'');break;}
      assert(Number(next)>offset && Number(next)<=10000);offset=Number(next);
    } while(offset<=10000);
    assert.equal(rows.length,first.total);assert.equal(new Set(rows.map(row=>row.id)).size,rows.length);return rows;
  }
  async invoke(mode,extra={},fn=this.fn,token=this.reader,status=200) {
    const value=await this.c.invoke(fn,token,{mode,...extra},status);
    const record=await this.c.terminal(fn,value.id);
    assert.equal(record.http_status,status);if(fn.id===this.fn.id)this.calls[mode]=value.id;return {...value,record};
  }
  async configure(fn,change) {
    const row=await this.c.value(endpoint(fn));
    return this.c.value(endpoint(fn),{method:'PUT',headers:match(row.updated_at),body:{name:row.name,config:{...row.config,...change}}});
  }

  async prepare() {
    const native=await inspectJournal(this.c,'baseline');
    assert.equal(native.migrations.length,11);assert.equal(native.migrations.at(-1),'011_execution_logs.sql');
    assert(Object.values(native.counts).every(value=>value===0));
    this.image=native.containers['serverless-api'].image;
    this.service=await this.c.service('journal-application-and-platform',{secrets:{JOURNAL_SERVICE_SECRET:this.secretService}});
    this.fn=await this.c.function(this.service,'journal-original-handler',{}, {secrets:{JOURNAL_FUNCTION_SECRET:this.secretFunction}});
    this.reader=await this.c.mint(this.service);
    this.version=await this.c.publish(this.fn,'journal-original');await this.c.promote(this.fn,this.version.code_hash);
  }

  async formats() {
    const silent=await this.invoke('silent');assert.equal(silent.record.logs_collection_state,'collected');assert.equal(silent.record.logs,'');
    assert.deepEqual(await this.application(this.fn,silent.id),[]);
    const text=await this.invoke('text');
    const messages=await this.application(this.fn,text.id);
    assert.equal(messages.length,3);assert(messages.some(row=>row.message==='Première ligne — été 😀'));
    assert(messages.some(row=>row.message==='<script>globalThis.journalInjected = true</script>'));
    assert(messages.every(row=>row.source==='application' && row.severity===null && row.observed_at===text.record.completed_at));
    const json=await this.invoke('json'),structured=await this.application(this.fn,json.id);
    assert.equal(structured.length,1);assert.equal(structured[0].message_format,'json');assert.equal(structured[0].severity,'info');
    for(const lexeme of ['9007199254740993','1.2300','1e+30','\\u00e9'])assert(structured[0].message.includes(lexeme));
    const levels=await this.invoke('levels'),rows=await this.application(this.fn,levels.id);
    assert.equal(rows.length,15);
    const count=level=>rows.filter(row=>row.severity===level).length;
    assert.deepEqual(['trace','debug','info','warning','error','fatal'].map(count),[1,1,1,2,2,1]);
    assert.equal(count(null),7);assert.equal(rows.filter(row=>row.message_format==='text').length,3);
    assert(rows.every(row=>row.metadata.time_source==='invocation_completion' && row.code_hash===this.version.code_hash && row.invocation_id===levels.id));
    this.c.observations.push({scenario:'actual-collection-states',silent:silent.id,text:text.id,json:json.id,levels:levels.id,
      text_sha256:sha(text.record.logs),levels_sha256:sha(levels.record.logs),application_events:rows.length});
  }

  async scopes() {
    const c=this.c;
    const second=await c.function(this.service,'journal-other-function');
    const version=await c.publish(second,'journal-other');await c.promote(second,version.code_hash);
    const sibling=await this.invoke('text',{},second,this.reader);
    const other=await c.service('journal-foreign-service');const otherReader=await c.mint(other);
    const limited=await c.mint(this.service,['read'],[this.fn.id]);
    const scopes=[{token:undefined,anonymous:true,status:401},{token:'',status:401},{token:'invalid-journal-token',status:401},
      {token:otherReader.token,status:403}];
    for(const right of ['create','update','delete'])scopes.push({token:(await c.mint(this.service,[right])).token,status:403});
    for(const scope of scopes) {
      for(const suffix of ['','/export?format=jsonl'])await c.call(logPath(this.fn)+suffix,{...scope,json:scope.status!==200});
      await c.call(policyPath(this.service),scope);
    }
    const own=await this.log(this.fn,{}, {token:limited.token});assert(own.total>0);
    await c.call(logPath(second),{token:limited.token,status:403});
    const visible=await c.value('/api/services/'+this.service.id+'/logs?limit=20',{token:limited.token});
    assert(visible.total>0 && visible.items.every(row=>row.function_id===this.fn.id));
    await this.log(this.fn,{snapshot:visible.snapshot},{token:limited.token,status:403});
    await c.call('/api/services/'+other.id+'/logs',{token:limited.token,status:403});
    await c.call('/api/functions/'+randomUUID()+'/logs',{token:limited.token,status:403});
    await c.call('/api/functions/'+randomUUID()+'/logs',{status:404});
    await this.log(this.fn,{snapshot:own.snapshot},{token:this.reader.token,status:403});
    const revoked=await c.mint(this.service,['read'],[this.fn.id]);
    const gate=await new JournalSqlBarrier(c,this.image).start();
    const heldRead=pending(c,this.log(this.fn,{}, {token:revoked.token,status:401}));
    await gate.held();await c.value('/api/tokens/'+revoked.id+'/revoke',{method:'POST'});
    await gate.close();await outcome(heldRead);
    const revokedSnapshot=await c.call(logPath(this.fn),{token:revoked.token,status:401});assert.equal(revokedSnapshot.status,401);
    this.c.observations.push({scenario:'scoped-read-and-accepted-revocation',limited_token_id:limited.id,revoked_token_id:revoked.id,
      other_function_id:second.id,other_invocation_id:sibling.id,gate:gate.unit});
  }

  async filters() {
    const c=this.c,id=this.calls.levels,record=await c.value(endpoint(this.fn)+'/invocations/'+id);
    const selected=await this.log(this.fn,{source:'application',severity:'error',invocation:id,instance:record.instance_id,
      version:record.resolved_code_hash,kind:'application.message',state:'succeeded',q:'explicite',limit:1,offset:0});
    assert.equal(selected.total,2);assert.equal(selected.items.length,1);
    const next=await this.log(this.fn,{snapshot:selected.snapshot,offset:1,limit:1});
    assert.equal(next.total,2);assert.notEqual(next.items[0].id,selected.items[0].id);
    await this.invoke('json');
    const stable=await this.log(this.fn,{snapshot:selected.snapshot,offset:1,limit:1});assert.deepEqual(stable.items,next.items);
    const all=await this.exportRows(this.fn,{source:'application',invocation:id});
    assert.equal(all.length,15);assert(all.every((row,index)=>!index || row.observed_at<=all[index-1].observed_at));
    assert.equal((await this.log(this.fn,{source:'application',invocation:id,q:'EXPlicite'})).total,0);
    assert.equal((await this.log(this.fn,{source:'application',invocation:id,severity:'unknown'})).total,7);
    assert.equal((await this.log(this.fn,{from:0,to:604800,limit:20,offset:10000,q:'é'.repeat(200)})).total,0);
    const invalid=[{from:0,to:604800.001},{from:'NaN'},{to:'Infinity'},{from:'2026-11-22T10:00:00+01:00'},
      {source:'stderr'},{severity:'INFO'},{state:'invented'},{invocation:'not-uuid'},{instance:randomUUID().toUpperCase()},
      {version:'a'.repeat(63)},{version:'A'.repeat(64)},{kind:'../private'},{q:'é'.repeat(201)},
      {limit:0},{limit:21},{offset:10001},{offset:-1},{format:'jsonl'},{snapshot:selected.snapshot,q:'changed'},
      {snapshot:selected.snapshot,cursor:selected.follow_cursor},{cursor:'tampered'}];
    for(const query of invalid)await this.log(this.fn,query,{status:422});
    await c.value(logPath(this.fn)+'?limit=1&limit=2',{status:422});
    await c.value(logPath(this.fn)+'?unknown=value',{status:422});
    const tampered=selected.snapshot.slice(0,-2)+'aa';await this.log(this.fn,{snapshot:tampered},{status:422});
    const page=await this.log(this.fn,{source:'platform',limit:20});assert(page.items.every(row=>row.source==='platform'));
    this.c.observations.push({scenario:'literal-combined-filters-and-stable-pages',invocation_id:id,matched:selected.total,
      page_ids:[selected.items[0].id,next.items[0].id],invalid_queries:invalid.length+3});
  }

  async projection() {
    const secret=await this.invoke('secrets'),rows=await this.application(this.fn,secret.id);
    const exposed=JSON.stringify({record:secret.record,rows});
    assert(!exposed.includes(this.secretService) && !exposed.includes(this.secretFunction));assert(rows.length===2);
    for(const size of [4096,4097]) {
      const sample=await this.invoke('line',{text:'é'.repeat(size>>1)+(size%2?'a':'')});
      const selected=await this.application(this.fn,sample.id);assert.equal(selected.length,1);
      assert.equal(Buffer.byteLength(selected[0].message),4096);assert.equal(selected[0].message_truncated,size>4096);
      assert.equal(sample.record.logs_truncated,false);assert.equal(Buffer.byteLength(sample.record.logs),size+1);
    }
    // @spec docs/BACKLOG.md#sls-120 | docs/EXECUTION_LOGS.md#collecte-et-événements
    // Capture limits and redaction limits are proved separately through real functions.
    const c=this.c,plainService=await c.service('journal-raw-buffer-boundary');
    const plainFunction=await c.function(plainService,'journal-raw-buffer-handler');
    const plainReader=await c.mint(plainService,['read'],[plainFunction.id]);
    const plainVersion=await c.publish(plainFunction,'journal-raw-buffer');await c.promote(plainFunction,plainVersion.code_hash);
    const secretLengths=[Buffer.byteLength(this.secretService),Buffer.byteLength(this.secretFunction)];
    const guardedSuffix=Math.max(...secretLengths)-1;
    for(const knownSecrets of [false,true])for(const size of [65535,65536,65537]) {
      const fn=knownSecrets?this.fn:plainFunction,reader=knownSecrets?this.reader:plainReader;
      const sample=await this.invoke('bytes',{bytes:size},fn,reader),selected=await this.application(fn,sample.id);
      const expected=Math.min(size,65536)-(knownSecrets && size>65536?guardedSuffix:0);
      const observed=Buffer.byteLength(sample.record.logs);
      c.observations.push({scenario:'real-buffer-boundary',function_id:fn.id,invocation_id:sample.id,
        with_effective_secrets:knownSecrets,requested_bytes:size,observed_bytes:observed,expected_bytes:expected,
        secret_lengths:knownSecrets?secretLengths:[],logs_truncated:sample.record.logs_truncated,
        buffer_sha256:sha(sample.record.logs)});await c.save();
      assert.equal(observed,expected);assert.equal(sample.record.logs_truncated,size>65536);
      assert(/^a+$/.test(sample.record.logs));assert.equal(sample.record.logs_collection_state,'collected');
      assert.equal(selected.length,1);assert.equal(selected[0].message.length,4096);assert(selected[0].message_truncated);
      assert.equal(selected[0].collection_truncated,size>65536);assert.equal(selected[0].projection_truncated,false);
    }
    const boundary=await this.invoke('line',{text:'a'.repeat(65536-8)+this.secretFunction});
    const boundaryRows=await this.application(this.fn,boundary.id);
    const partialPresent=boundary.record.logs.includes(this.secretFunction.slice(0,8));
    c.observations.push({scenario:'real-secret-crossing-capture-boundary',invocation_id:boundary.id,
      observed_bytes:Buffer.byteLength(boundary.record.logs),guarded_suffix_bytes:guardedSuffix,
      partial_secret_prefix_present:partialPresent,logs_truncated:boundary.record.logs_truncated,
      buffer_sha256:sha(boundary.record.logs)});await c.save();
    assert.equal(Buffer.byteLength(boundary.record.logs),65536-guardedSuffix);assert(boundary.record.logs_truncated);
    assert(/^a+$/.test(boundary.record.logs));assert.equal(partialPresent,false);
    assert.equal(boundaryRows.length,1);assert(boundaryRows[0].collection_truncated && boundaryRows[0].message_truncated);
    for(const count of [1024,1025]) {
      const sample=await this.invoke('lines',{count}),selected=await this.application(this.fn,sample.id);
      assert.equal(selected.length,1024);assert.equal(selected.filter(row=>row.projection_truncated).length,count>1024?1:0);
      assert.equal(selected.find(row=>row.metadata.line===1024).projection_truncated,count>1024);
      assert.equal(sample.record.logs_truncated,false);
      if(count===1024)this.shortExportInvocation=sample.id;
    }
    for(let index=0;index<20;index++)await this.invoke('batch',{lengths:Array(16).fill(4095)});
    this.c.observations.push({scenario:'real-projection-boundaries',message_bytes:[4096,4097],buffer_bytes:[65535,65536,65537],
      projected_lines:[1024,1025],redacted_secret_sha256:[sha(this.secretService),sha(this.secretFunction)],large_export_calls:20});
  }

  async expiration() {
    const c=this.c,service=await c.service('journal-sixty-second-retention'),fn=await c.function(service,'journal-retention-handler');
    const reader=await c.mint(service),version=await c.publish(fn,'journal-sixty-seconds');await c.promote(fn,version.code_hash);
    const sample=await this.invoke('text',{},fn,reader);
    const original=await c.value(policyPath(service));assert.equal(original.retention_minutes,10080);
    const short=await this.policy(service,1);assert.equal(short.version,original.version+1);
    const before=await this.log(fn,{source:'application'});assert.equal(before.total,3);
    await until(async()=>Date.now()/1000>sample.record.completed_at+60.2,'real_retention_minute_not_elapsed',70);
    await this.log(fn,{snapshot:before.snapshot},{status:410});
    assert.equal((await this.log(fn,{source:'application'})).total,0);
    const native=await until(async()=>{
      const value=await inspectJournal(c);const call=value.invocations.find(row=>row.id===sample.id);
      return call?.logs_collection_state==='expired' && call.log_bytes===0?value:null;
    },'expired_buffer_not_physically_cleared',15);
    assert(!native.events.some(row=>row.invocation_id===sample.id));
    const long=await this.policy(service,10080);assert(long.effective_floor>=short.effective_floor);
    const record=await c.value(endpoint(fn)+'/invocations/'+sample.id);
    assert.equal(record.logs,'');assert.equal(record.logs_collection_state,'expired');assert.equal(record.state,'succeeded');assert(record.handler_started);
    assert.equal((await this.log(fn,{source:'application'})).total,0);
    assert((await this.log(this.fn)).total>0,'other_service_logs_were_expired');
    c.observations.push({scenario:'real-one-minute-expiration',function_id:fn.id,invocation_id:sample.id,completed_at:sample.record.completed_at,
      observed_after:Date.now()/1000,initial_minutes:original.retention_minutes,floor_before:short.effective_floor,floor_after_increase:long.effective_floor});
  }

  async policies() {
    const c=this.c,path=policyPath(this.service),old=await c.value(path);
    const functionVersion=(await c.value(endpoint(this.fn))).updated_at;
    await c.value(path,{method:'PUT',body:{retention_minutes:10079},status:428});
    for(const change of [{retention_minutes:0},{retention_minutes:10081},{retention_minutes:1.5},{retention_minutes:'1'},{retention_minutes:1,unknown:true}])
      await c.value(path,{method:'PUT',headers:match(old.version),body:change,status:422});
    for(const headers of [{'X-CSRF-Token':''},{'X-CSRF-Token':'invalid'},{Origin:'https://untrusted.invalid'}])
      await c.value(path,{method:'PUT',body:{retention_minutes:1},headers:{...match(old.version),...headers},status:403});
    for(const rights of [['read'],['update'],['create'],['delete']]) {
      const token=await c.mint(this.service,rights);
      await c.value(path,{method:'PUT',token:token.token,headers:match(old.version),body:{retention_minutes:1},status:403});
    }
    const noop=await this.policy(this.service,old.retention_minutes);assert.equal(noop.changed,false);assert.equal(noop.version,old.version);assert.equal(noop.updated_at,old.updated_at);
    // @spec docs/BACKLOG.md#sls-121 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
    const heldRead=(gate,expectedStatus)=>{
      const observed={scenario:'policy-concurrent-read-http',gate:gate.unit,http_status:null,settled:false};
      const started=performance.now();c.observations.push(observed);
      const reading=pending(c,(async()=>{
        let response,data;
        try {
          response=await c.admin.get(logPath(this.fn),{headers:{Origin:base,'X-CSRF-Token':c.session.csrf_token}});
          observed.http_status=response.status();data=await response.json();
          if(/^log_[a-z_]+$/.test(data?.error || ''))observed.public_error=data.error;
        } catch(error) {observed.failure=diagnosis(error);throw error;}
        finally {observed.elapsed_ms=performance.now()-started;observed.settled=true;await c.save();}
        assert.equal(response.status(),expectedStatus);return data;
      })());
      return {reading,observed};
    };
    const finishBoundary=(held,name,comm,wal)=>{
      assert.equal(held.readers.length,1);const row=held.readers[0];
      assert.equal(row.syscall,157);assert.equal(row.command,15);assert.equal(row.syscall_phase,'entry');
      assert.equal(row.boundary,name);assert.equal(row.comm,comm);
      assert.equal(row.application_buffers_read,false);assert.equal(row.registers_or_results_modified,false);
      if(wal) {
        assert.equal(row.wal_acquired.syscall_result,0);assert.equal(row.wal_acquired.lock_type,1);
        assert.equal(row.wal_released.syscall_result,0);assert.equal(row.wal_released.lock_type,2);
        assert.equal(row.wal_acquired.inode,row.wal_released.inode);
      }
      return row;
    };
    {
      const before=await c.value(path),gate=await new JournalSqlBarrier(c,this.image,1,'read-result').start();
      const read=heldRead(gate,410),held=await gate.held();finishBoundary(held,'read-result','journal-read',false);
      assert.equal(read.observed.settled,false);
      const changed=await this.policy(this.service,before.retention_minutes-1,before.version);
      assert.equal(changed.version,before.version+1);assert.equal(read.observed.settled,false);
      await gate.close();const result=await outcome(read.reading);assert.equal(result.error,'log_policy_changed');
      c.observations.push({scenario:'policy-accepted-before-read-decision',gate:gate.unit,boundary:held.readers[0],
        before_version:before.version,after_version:changed.version,http_status:read.observed.http_status});await c.save();
    }
    {
      const before=await c.value(path),gate=await new JournalSqlBarrier(c,this.image,1,'read-decision').start();
      const read=heldRead(gate,200),held=await gate.held();const boundary=finishBoundary(held,'read-decision','journal-verify',true);
      assert.equal(read.observed.settled,false);
      const changed=await this.policy(this.service,before.retention_minutes-1,before.version);
      assert.equal(changed.version,before.version+1);assert.equal(read.observed.settled,false);
      await gate.close();const result=await outcome(read.reading);assert(result.total>0);
      await this.log(this.fn,{snapshot:result.snapshot},{status:410});
      await c.value(path,{method:'PUT',headers:match(before.version),body:{retention_minutes:1},status:409});
      assert.equal((await c.value(path)).version,changed.version);
      c.observations.push({scenario:'policy-committed-after-read-decision-before-response',gate:gate.unit,boundary,
        before_version:before.version,after_version:changed.version,http_status:read.observed.http_status,
        returned_snapshot_refused_after_commit:true});await c.save();
    }
    {
      const before=await c.value(path),nativeBefore=await inspectJournal(c);
      const client=await request.newContext({baseURL:base,storageState:await c.admin.storageState(),timeout:120000});
      let settled=false;
      try {
        const gate=await new JournalSqlBarrier(c,this.image,1,'policy-commit').start();
        const writing=pending(c,client.put(path,{data:{retention_minutes:before.retention_minutes-1},
          headers:{Origin:base,'X-CSRF-Token':c.session.csrf_token,...match(before.version)}}).finally(()=>{settled=true;}));
        const held=await gate.held(),boundary=finishBoundary(held,'policy-commit','journal-write',true);
        assert.equal(settled,false);
        const committed=await c.value(path),nativeCommitted=await inspectJournal(c);
        assert.equal(committed.version,before.version+1);assert.equal(committed.retention_minutes,before.retention_minutes-1);
        assert.equal(nativeCommitted.audit_counts['service.log_retention'],nativeBefore.audit_counts['service.log_retention']+1);
        assert.equal(settled,false);await client.dispose();await gate.close();
        const lost=await writing;assert(lost.error && !lost.value,'lost_policy_response_was_acknowledged');
        const after=await c.value(path),nativeAfter=await inspectJournal(c);
        assert.equal(after.version,committed.version);assert.equal(after.retention_minutes,committed.retention_minutes);
        assert.equal(nativeAfter.audit_counts['service.log_retention'],nativeCommitted.audit_counts['service.log_retention']);
        c.observations.push({scenario:'policy-response-lost-after-native-commit-no-replay',gate:gate.unit,boundary,
          before_version:before.version,after_version:after.version,acknowledged:false,
          audit_count_before:nativeBefore.audit_counts['service.log_retention'],audit_count_after:nativeAfter.audit_counts['service.log_retention']});
        await c.save();
      } finally {await client.dispose();}
    }
    assert.equal((await c.value(endpoint(this.fn))).updated_at,functionVersion);
    const authority=await adminConnection(c.browser,this.credentials);
    try {
      const before=await c.value(path),nativeBefore=await inspectJournal(c);
      const gate=await new JournalSqlBarrier(c,this.image,1,'write').start();
      const writing=pending(c,authority.admin.put(path,{data:{retention_minutes:1},headers:{Origin:base,
        'X-CSRF-Token':authority.session.csrf_token,...match(before.version)}}));
      await gate.held();
      const logout=await authority.admin.post('/auth/logout',{headers:{Origin:base,'X-CSRF-Token':authority.session.csrf_token}});
      assert.equal(logout.status(),200);assert((await logout.json()).signed_out);
      await gate.close();const response=await outcome(writing);assert.equal(response.status(),401);
      const after=await c.value(path),nativeAfter=await inspectJournal(c);
      assert.equal(after.version,before.version);assert.equal(after.retention_minutes,before.retention_minutes);
      assert.equal(nativeAfter.audit_counts['service.log_retention'],nativeBefore.audit_counts['service.log_retention']);
      c.observations.push({scenario:'policy-writer-session-revoked-during-native-io',gate:gate.unit,
        before_version:before.version,after_version:after.version,logout_http_status:logout.status(),write_http_status:response.status()});
    } finally {await authority.admin.dispose();await authority.context.close();}
  }

  async exports() {
    const c=this.c;
    const small=await this.log(this.fn,{source:'application',invocation:this.shortExportInvocation});assert.equal(small.total,1024);
    const lot=await c.call(logPath(this.fn)+'/export?'+parameters({snapshot:small.snapshot,format:'jsonl'}),{json:false});
    assert.equal(lot.headers['x-log-count'],'1000');assert.equal(lot.headers['x-log-partial'],'true');assert.equal(lot.headers['x-log-next-offset'],'1000');
    const tail=await c.call(logPath(this.fn)+'/export?'+parameters({snapshot:small.snapshot,format:'jsonl',offset:1000}),{json:false});
    assert.equal(tail.headers['x-log-count'],'24');assert.equal(tail.headers['x-log-partial'],'false');
    const first=await this.log(this.fn,{source:'application',q:'a'.repeat(200)});
    assert(first.total>=320);
    const large=await c.call(logPath(this.fn)+'/export?'+parameters({snapshot:first.snapshot,format:'jsonl'}),{json:false});
    const parsed=large.data.toString('utf8').trimEnd().split('\n').map(value=>JSON.parse(value));
    assert(large.data.length<=1024**2 && parsed.length<1000 && large.headers['x-log-partial']==='true');
    const second=await c.call(logPath(this.fn)+'/export?'+parameters({snapshot:first.snapshot,format:'jsonl',offset:large.headers['x-log-next-offset']}),{json:false});
    const next=JSON.parse(second.data.toString('utf8').split('\n')[0]);
    assert(large.data.length+Buffer.byteLength(JSON.stringify(next)+'\n')>1024**2);
    const text=await c.call(logPath(this.fn)+'/export?'+parameters({source:'application',invocation:this.calls.text,format:'text'}),{json:false});
    assert(text.headers['content-type'].startsWith('text/plain'));assert(text.headers['content-disposition'].includes('attachment;'));
    assert.equal(text.data.toString('utf8').trimEnd().split('\n').length,3);assert(text.data.toString('utf8').includes('"<script>'));
    await c.call(logPath(this.fn)+'/export?format=csv',{status:422});
    await c.call(logPath(this.fn)+'/export?'+parameters({cursor:first.follow_cursor}),{status:422});
    const other=await c.mint(this.service,['read']);
    await c.call(logPath(this.fn)+'/export?'+parameters({snapshot:first.snapshot}),{token:other.token,status:403});
    const revoked=await c.mint(this.service,['read']);const own=await this.log(this.fn,{}, {token:revoked.token});
    await c.value('/api/tokens/'+revoked.id+'/revoke',{method:'POST'});
    await c.call(logPath(this.fn)+'/export?'+parameters({snapshot:own.snapshot}),{token:revoked.token,status:401});
    c.observations.push({scenario:'actual-export-limits',event_lots:[1000,24],byte_lot:{events:parsed.length,bytes:large.data.length},
      formats:['jsonl','text'],jsonl_sha256:sha(large.data),text_sha256:sha(text.data)});
  }

  async correlations() {
    const c=this.c;
    const business=await this.invoke('status',{status:500},this.fn,this.reader,500);
    assert.equal(business.record.state,'succeeded');
    const businessEvents=await this.exportRows(this.fn,{invocation:business.id});
    assert.equal(businessEvents.find(row=>row.kind==='invocation.completed').metadata.classification,'application_response');
    const code=await this.invoke('error',{},this.fn,this.reader,502);
    assert.equal(code.record.error_code,'handler_error');assert.equal(code.record.logs_collection_state,'collected');
    assert.equal((await this.exportRows(this.fn,{invocation:code.id})).find(row=>row.kind==='invocation.completed').metadata.classification,'code');
    const exited=await this.invoke('exit',{},this.fn,this.reader,502);
    assert.equal(exited.record.error_code,'handler_exited');
    await this.configure(this.fn,{timeout_seconds:.2,idle_seconds:0,min_instances:0});
    const timeout=await this.invoke('delay',{milliseconds:3000},this.fn,this.reader,504);
    const timed=await this.exportRows(this.fn,{invocation:timeout.id});
    assert.equal(timed.find(row=>row.kind==='invocation.timeout').metadata.classification,'timeout');
    await this.configure(this.fn,{timeout_seconds:10,queue_timeout_seconds:0});
    const long=pending(c,this.invoke('delay',{milliseconds:3000}));
    await until(async()=>{
      const values=await c.value(endpoint(this.fn)+'/invocations?limit=20');return values.items.find(row=>row.completed_at===null && row.handler_started);
    },'real_handler_not_running');
    const rejected=await this.invoke('silent',{},this.fn,this.reader,429);assert.equal(rejected.record.logs_collection_state,'not_started');
    assert.equal((await this.exportRows(this.fn,{invocation:rejected.id})).find(row=>row.kind==='invocation.completed').metadata.classification,'admission');
    await outcome(long);
    await until(async()=>!(await c.value(endpoint(this.fn)+'/instances')).total,'instances_not_extinguished');
    const cycles=await this.exportRows(this.fn,{source:'platform'});
    for(const kind of ['publication.prepared','publication.published','function.version_promote','instance.reserved','instance.started','instance.available','instance.stopped'])
      assert(cycles.some(row=>row.kind===kind),'missing_journal_kind:'+kind);
    const cache=await c.value(endpoint(this.fn)+'/cache-clear',{method:'POST',status:[200,202],headers:match((await c.value(endpoint(this.fn))).updated_at),body:{operation_id:randomUUID()}});
    await until(async()=>{const row=await c.value('/api/storage-operations/'+cache.id);assert.notEqual(row.state,'aborted');return row.state==='completed';},'cache_command_not_completed');
    const storage=await this.exportRows(this.fn,{source:'platform'});assert(storage.some(row=>row.operation_id===cache.id && row.state==='completed'));
    const sibling=this.c.functions.find(row=>row.service_id===this.service.id && row.id!==this.fn.id);assert(sibling);
    const before=await c.value('/api/services/'+this.service.id+'/logs?limit=20');await c.purge(sibling);
    await c.value('/api/services/'+this.service.id+'/logs?'+parameters({snapshot:before.snapshot}),{status:410});
    const visible=await c.value('/api/services/'+this.service.id+'/logs?source=application&limit=20');assert(visible.items.every(row=>row.function_id!==sibling.id));
    const preserved=await this.log(this.fn,{invocation:business.id});
    // @spec docs/BACKLOG.md#sls-125 | docs/EXECUTION_LOGS.md#modèle-et-migration-011
    c.observations.push({scenario:'post-sibling-purge-correlation-diagnostic',function_id:this.fn.id,purged_sibling_id:sibling.id,
      invocation_id:business.id,expected_code_hash:this.version.code_hash,resolved_code_hash:business.record.resolved_code_hash,
      total:preserved.total,items:preserved.items.map(({id,kind,state,function_id,invocation_id,code_hash})=>({id,kind,state,function_id,invocation_id,code_hash}))});
    await c.save();assert.equal(preserved.total,5);assert.equal(preserved.items.length,5);
    assert.deepEqual(preserved.items,businessEvents,'sibling_purge_changed_retained_events');
    assert.equal(business.record.resolved_code_hash,this.version.code_hash);
    assert.deepEqual(new Set(preserved.items.map(row=>row.kind)),new Set(['invocation.received','invocation.queued','invocation.admitted','invocation.dispatched','invocation.completed']));
    for(const row of preserved.items) {
      assert.equal(row.function_id,this.fn.id);assert.equal(row.invocation_id,business.id);
      if(['invocation.received','invocation.queued'].includes(row.kind)) {
        assert.equal(row.code_hash,null);assert.equal(row.revision_id,null);assert.equal(row.instance_id,null);
      } else {
        assert.equal(row.code_hash,this.version.code_hash);assert.equal(row.revision_id,this.version.revision_id);
        assert.equal(row.instance_id,business.record.instance_id);
      }
    }
    c.observations.push({scenario:'typed-execution-and-storage-correlation',business_response_id:business.id,code_error_id:code.id,
      exited_id:exited.id,timeout_id:timeout.id,admission_id:rejected.id,cache_operation_id:cache.id,purged_sibling_id:sibling.id});
  }

  // @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#préparation-après-acquisition-des-lecteurs--sls-1265
  // @verifies docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#préparation-après-acquisition-des-lecteurs--sls-1265
  async prepareHeldReaders(gate,mode) {
    const c=this.c,started=performance.now(),deadline=Math.min(started+1000,gate.startedMonotonic+45000-5000);
    const record={scenario:'reader-acquisition-health-preparation',gate:gate.unit,mode,
      started_at_ms:Date.now(),started_after_gate_ms:started-gate.startedMonotonic,
      budget_ms:deadline-started,probes:[],ready:false};
    c.observations.push(record);
    try {
      assert(deadline>started,'reader_preparation_budget_exhausted');
      for(let index=0;index<21;index++) {
        assert.equal(gate.exit,null,'reader_helper_exited_during_preparation');
        const before=performance.now(),remaining=Math.floor(deadline-before);assert(remaining>0,'reader_preparation_deadline');
        const probe={index,at_ms:Date.now(),after_gate_ms:before-gate.startedMonotonic,timeout_ms:remaining};record.probes.push(probe);
        let response;
        try {
          response=await c.caller.get('/healthz',{timeout:remaining,maxRedirects:0});
          const raw=await response.body();probe.http_status=response.status();probe.body_bytes=raw.length;probe.body_sha256=sha(raw);
          assert(raw.length<=16384,'reader_preparation_health_body_too_large');
          const data=JSON.parse(raw.toString('utf8'));if(typeof data.error==='string')probe.error_sha256=sha(data.error);
          assert(performance.now()<=deadline,'reader_preparation_response_after_deadline');
          if(response.status()===200) {
            assert.equal(data.status,'ok');assert.equal(data.component,'control');
            assert.equal(gate.exit,null,'reader_helper_exited_during_preparation');record.ready=true;break;
          }
          assert.equal(response.status(),503,'reader_preparation_unexpected_status');
          assert(['Les planifications doivent être réconciliées.','Les instances doivent être réconciliées avant la reprise.'].includes(data.error),'reader_preparation_unrelated_failure');
        } catch(error) {probe.failure=diagnosis(error);throw error;}
        finally {probe.elapsed_ms=performance.now()-before;await response?.dispose();}
        const wait=Math.min(50,deadline-performance.now());assert(wait>0,'reader_preparation_deadline');await delay(wait);
      }
      assert(record.ready,'reader_preparation_probe_bound');
      assert(performance.now()<=deadline,'reader_preparation_disposal_after_deadline');
    } finally {record.finished_at_ms=Date.now();record.elapsed_ms=performance.now()-started;await c.save();}
  }

  async readers() {
    const c=this.c;
    for(const mode of ['release','eof','kill']) {
      const baseline=await c.call('/healthz',{anonymous:true});
      c.observations.push({scenario:'reader-health-before-acquisition',mode,http_status:baseline.status,at_ms:Date.now()});
      const gate=await new JournalSqlBarrier(c,this.image,2,'reader-start').start();
      // @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
      c.observations.push({scenario:'reader-wave',mode,gate:gate.unit});
      const reads=[0,1].map(index=>{
        const observed={scenario:'reader-http-result',mode,gate:gate.unit,index,http_status:null,settled:false};
        c.observations.push(observed);const started=performance.now();
        return pending(c,(async()=>{
          let response,data;
          try {
            response=await c.admin.get(logPath(this.fn),{headers:{Origin:base,'X-CSRF-Token':c.session.csrf_token}});
            observed.http_status=response.status();data=await response.json();
            if(/^log_[a-z_]+$/.test(data?.error || ''))observed.public_error=data.error;
          } catch(error) {observed.failure=diagnosis(error);throw error;}
          finally {observed.elapsed_ms=performance.now()-started;observed.settled=true;await c.save();}
          assert.equal(response.status(),503);return data;
        })());
      });
      const held=await gate.held();assert.equal(new Set(held.readers.map(row=>row.tid)).size,2);
      for(const row of held.readers) {
        assert.equal(row.boundary,'reader-start');assert.equal(row.syscall,157);assert.equal(row.command,15);
        assert.equal(row.syscall_phase,'exit');assert.equal(row.syscall_result,0);assert.equal(row.comm,'journal-read');
        assert.equal(row.name_assignment_initial,true);assert.equal(row.application_buffers_read,false);assert.equal(row.registers_or_results_modified,false);
      }
      await this.prepareHeldReaders(gate,mode);
      const third=await c.call(logPath(this.fn),{status:429});assert.equal(third.headers['retry-after'],'2');
      assert.equal((await c.call('/healthz',{anonymous:true})).status,200);
      await delay(2100);
      await c.call(logPath(this.fn),{status:429});
      if(mode==='kill'){await gate.action('kill');await gate.close({release:false,allowKilled:true});}
      else if(mode==='eof'){gate.process.stdin.end();await gate.close({release:false});}
      else await gate.close();
      const results=await Promise.all(reads.map(outcome));assert(results.every(result=>result.error==='log_read_timeout'));
      assert((await this.log(this.fn)).total>0);
    }
    await this.readerFault();
    c.observations.push({scenario:'bounded-real-readers',readers:2,third_status:429,deadline_status:503,native_errno:24});
  }

  // @spec docs/BACKLOG.md#sls-127 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  // @verifies docs/BACKLOG.md#sls-127 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async readerFault() {
    const c=this.c,fault=await new JournalSqlBarrier(c,this.image,1,'fault').start();
    const started=performance.now();
    const refused=pending(c,(async()=>{
      const response=await c.admin.get(logPath(this.fn),{headers:{Origin:base,'X-CSRF-Token':c.session.csrf_token}});
      const data=await response.json();
      c.observations.push({scenario:'reader-fault-http-result',gate:fault.unit,http_status:response.status(),
        public_error:typeof data.error==='string'?data.error:null,elapsed_ms:performance.now()-started,settled:true});
      await c.save();assert.equal(response.status(),503);return data;
    })());
    const native=await fault.event('native-fault');assert(native.restored_before_Python && native.syscall_result===-24);
    assert.equal(native.restoration_after_open_attempt,2);
    assert.deepEqual(native.database_opens.map(row=>[row.access_mode,row.syscall_result,row.phase]),
      [[2,-24,'before-limit-restoration'],[0,-24,'before-limit-restoration']]);
    await fault.close({release:false});const data=await outcome(refused);assert.equal(data.error,'log_read_unavailable');
    assert((await this.log(this.fn)).total>0);
  }

  // @spec docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async followAndRestart() {
    const c=this.c,fn=await c.function(this.service,'journal-durable-counter',{
      timeout_seconds:30,idle_seconds:60,min_instances:1,storage:{data:{enabled:true,quota_mib:2},cache:{enabled:false},concurrency:'exclusive'},
    });
    const published=await c.publish(fn,'journal-durable-counter');await c.promote(fn,published.code_hash);
    const token=await c.mint(this.service,['read'],[fn.id]);
    const initial=await this.log(fn,{}, {token:token.token});
    const empty=await this.log(fn,{cursor:initial.follow_cursor},{token:token.token});assert.equal(empty.total,0);
    assert.equal(empty.mode,'follow');
    const foreign=await c.mint(this.service,['read'],[fn.id]);
    await this.log(fn,{cursor:empty.follow_cursor},{token:foreign.token,status:403});
    await this.log(fn,{cursor:empty.follow_cursor.slice(0,-2)+'aa'},{token:token.token,status:422});
    await until(async()=>{const row=await c.value(endpoint(fn)+'/instances');return row.items.length===1 && row.items[0].state==='ready';},'counter_warm_instance_not_ready');
    const gate=await new JournalControlCut(c,fn,this.image).start();
    const http=pending(c,c.caller.post('/invoke/'+fn.id,{data:{mode:'counter',milliseconds:20000},
      headers:{'X-Serverless-Token':token.token,Origin:base},timeout:120000}));
    const cut=await gate.event('cut');
    assert.equal(cut.native_signal,9);assert.equal(cut.exit_code,137);assert(cut.docker_mutator_joined);
    assert.equal(cut.counter.counter,1);assert.equal(cut.counter.invocation.function_id,fn.id);
    assert.equal(cut.counter.invocation.handler_started,1);assert.equal(cut.counter.invocation.state,'running');
    const acknowledgement=cut.counter.start_acknowledgement;
    assert(acknowledgement?.first_pending && acknowledgement.pending_polls>=1,'counter_pending_start_not_observed');
    assert.equal(acknowledgement.first_pending.invocation.id,cut.counter.request_id);
    assert.equal(acknowledgement.first_pending.invocation.function_id,fn.id);
    assert.equal(acknowledgement.first_pending.invocation.handler_started,null);
    assert.equal(acknowledgement.first_pending.receipt_sha256,cut.counter.receipt_sha256);
    assert(acknowledgement.first_pending.observed_at_ns<acknowledgement.accepted_at_ns);
    assert.equal(cut.counter.start_gate.boundary,'after-started-receive');
    assert.equal(cut.counter.start_gate.instance_id,cut.counter.invocation.instance_id);
    assert.equal(cut.counter.start_gate.namespace_scope,'runtime');assert.equal(cut.counter.start_gate.control_table_contains_inode,false);
    assert.equal(cut.counter.start_gate.netns_inode,cut.counter.start_gate.runtime.netns_inode);
    assert.notEqual(cut.counter.start_gate.netns_inode,cut.counter.start_gate.control_netns_inode);
    assert(cut.counter.start_gate.held_elapsed_ms>0 && cut.counter.start_gate.held_elapsed_ms<=1000,'counter_native_receive_hold_unbounded');
    assert.equal(cut.counter.start_gate.application_buffers_read,false);assert.equal(cut.counter.start_gate.registers_or_results_modified,false);
    const response=await outcome(http);assert.equal(response.status(),502);
    await gate.close({independent:true});
    await this.configure(fn,{min_instances:0,idle_seconds:0});
    const interrupted=await c.terminal(fn,cut.counter.request_id);
    assert.equal(interrupted.state,'interrupted');assert.equal(interrupted.error_code,'control_interrupted');
    assert.equal(interrupted.logs_collection_state,'unavailable');
    const read=await this.invoke('counter_read',{},fn,token);assert.equal(read.data.counter,1);
    assert.notEqual(read.id,cut.counter.request_id);
    await until(async()=>!(await c.value(endpoint(fn)+'/instances')).total,'counter_instance_not_extinguished');
    const events=[];let cursor=empty.follow_cursor;let last;
    for(let page=0;page<100;page++) {
      last=await this.log(fn,{cursor},{token:token.token});assert.equal(last.mode,'follow');
      assert.equal(last.collection.id,initial.collection.id);events.push(...last.items);cursor=last.follow_cursor;
      if(!last.partial)break;assert(page<99,'follow_recovery_batch_bound');
    }
    assert.equal(new Set(events.map(row=>row.id)).size,events.length);
    assert(events.some(row=>row.invocation_id===cut.counter.request_id && row.kind==='invocation.completed' && row.state==='interrupted'));
    assert(events.some(row=>row.invocation_id===read.id && row.kind==='invocation.completed' && row.state==='succeeded'));
    const repeated=await this.log(fn,{cursor:empty.follow_cursor},{token:token.token});
    assert.deepEqual(repeated.items,events.slice(0,repeated.items.length));
    const none=await this.log(fn,{cursor},{token:token.token});assert.equal(none.total,0);
    // A deliberate pause makes no request. The later explicit read catches the
    // real new sequence and does not inherit the initial historical `to` value.
    const next=await this.invoke('text',{},fn,token);
    const resumed=await this.log(fn,{cursor},{token:token.token});
    assert(resumed.items.some(row=>row.invocation_id===next.id && row.source==='application'));
    assert(resumed.items.every(row=>row.observed_at>=initial.period.to));
    const native=await inspectJournal(c),calls=native.invocations.filter(row=>row.function_id===fn.id);
    assert.deepEqual(new Set(calls.map(row=>row.id)),new Set([cut.counter.request_id,read.id,next.id]));
    assert.equal(calls.filter(row=>row.state==='interrupted').length,1);
    c.observations.push({scenario:'real-control-cut-follow-resume-without-replay',function_id:fn.id,gate:gate.unit,
      invocation_id:cut.counter.request_id,counter_read_id:read.id,paused_new_invocation_id:next.id,
      gateway_http_status:response.status(),persistent_counter:read.data.counter,follow_event_ids:events.map(row=>row.id),
      collection_id:initial.collection.id,independent_restore:true});
  }
}
