// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#conservation-par-service-et-budget
// @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// Fill actual bounded journals through the original handler; never SQL-seed them.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {endpoint,match,until} from './execution-journal-harness.mjs';
import {inspectJournal} from './execution-journal-native.mjs';

const BYTE_LIMIT=16*1024**2;
const metadataBytes=line=>Buffer.byteLength(JSON.stringify({line,time_source:'invocation_completion'}));

async function corpus(c,name) {
  await c.retireServices();
  const empty=await inspectJournal(c);assert.equal(empty.journal.event_count,0);assert.equal(empty.journal.payload_bytes,0);
  const service=await c.service('journal-'+name),fn=await c.function(service,'journal-'+name+'-handler',{
    min_instances:1,max_instances:1,idle_seconds:60,timeout_seconds:30,queue_timeout_seconds:10,
  });
  const token=await c.mint(service),version=await c.publish(fn,'journal-'+name);await c.promote(fn,version.code_hash);
  await until(async()=>{const value=await c.value(endpoint(fn)+'/instances');return value.items.length===1 && value.items[0].state==='ready';},'warm_budget_instance_missing');
  async function invoke(body) {
    const response=await c.invoke(fn,token,body);const record=await c.terminal(fn,response.id);
    assert.equal(record.state,'succeeded');assert(record.handler_started && record.logs_collection_state==='collected');return record;
  }
  await invoke({mode:'silent'});
  return {service,fn,token,invoke};
}

export async function eventBudget(c) {
  const {fn,invoke}=await corpus(c,'event-count-corpus');
  const before=await inspectJournal(c);const sample=await invoke({mode:'line',text:'calibrate-event-count'});
  const calibrated=await inspectJournal(c);
  const overhead=calibrated.journal.event_count-before.journal.event_count-1;
  assert(overhead>0 && overhead<20);
  const remaining=10000-calibrated.journal.event_count,calls=Math.ceil(remaining/(1024+overhead));
  let lines=remaining-calls*overhead;assert(lines>=0);
  const ids=[];
  for(let index=0;index<calls;index++) {
    const count=Math.min(1024,lines);lines-=count;
    const row=await invoke({mode:'lines',count});ids.push(row.id);
    console.log('JOURNAL event-budget',index+1,'/',calls);
  }
  assert.equal(lines,0);
  const exact=await inspectJournal(c);assert.equal(exact.journal.event_count,10000);
  assert.equal(exact.journal.evicted_sequence,calibrated.journal.evicted_sequence);
  assert(exact.journal.payload_bytes<BYTE_LIMIT);
  const page=await c.value(endpoint(fn)+'/logs?limit=20');assert.equal(page.total,10000);
  const candidate=randomUUID(),current=await c.value(endpoint(fn));c.deployments.push(candidate);await c.save();
  await c.value(endpoint(fn)+'/code-deployments',{method:'POST',status:201,headers:match(current.updated_at),body:{deployment_id:candidate,handler:'execution-journal.cjs.handler'}});
  const plus=await inspectJournal(c);assert.equal(plus.journal.event_count,10000);
  const oldest=exact.events[0];assert(!plus.events.some(row=>row.id===oldest.id));
  assert.equal(plus.journal.evicted_sequence,oldest.sequence);
  const added=plus.events.filter(row=>!exact.events.some(old=>old.id===row.id));
  assert.equal(added.length,1);assert.equal(added[0].deployment_id,candidate);assert.equal(added[0].kind,'publication.prepared');
  await c.value(endpoint(fn)+'/logs?snapshot='+encodeURIComponent(page.snapshot),{status:410});
  c.observations.push({scenario:'actual-10000-event-boundary',function_id:fn.id,calibration_invocation_id:sample.id,
    invocations:ids,overhead_per_call:overhead,exact_count:10000,plus_one_candidate_id:candidate,
    evicted_event_id:oldest.id,evicted_sequence:oldest.sequence,payload_before:exact.journal.payload_bytes,payload_after:plus.journal.payload_bytes});
  await c.retireServices();
}

function lengthsFor(delta,overhead) {
  for(let count=1;count<=16;count++) {
    const metadata=Array.from({length:count},(_,index)=>metadataBytes(index+1)).reduce((sum,item)=>sum+item,0);
    let remaining=delta-overhead-metadata;
    if(remaining<0 || remaining>count*4095)continue;
    const lengths=Array.from({length:count},()=>{const value=Math.min(4095,remaining);remaining-=value;return value;});
    assert.equal(remaining,0);return lengths;
  }
  assert.fail('real_message_lengths_cannot_represent_byte_boundary');
}

function bytePlan(initial,overhead) {
  const minimum=overhead+metadataBytes(1),full=Array(16).fill(4095);
  const maximum=overhead+full.reduce((sum,length,index)=>sum+length+metadataBytes(index+1),0);
  const remaining=BYTE_LIMIT-initial;
  const count=Math.max(0,Math.floor((remaining-minimum)/maximum));
  const result=Array.from({length:count},()=>[...full]);
  const rest=remaining-count*maximum;
  if(rest>=maximum) {
    result.push(lengthsFor(Math.floor(rest/2),overhead),lengthsFor(Math.ceil(rest/2),overhead));
  } else result.push(lengthsFor(rest,overhead));
  assert(result.at(-1).some(value=>value<4095));
  assert.equal(initial+result.reduce((sum,lengths)=>sum+overhead+lengths.reduce((part,length,index)=>part+length+metadataBytes(index+1),0),0),BYTE_LIMIT);
  return result;
}

// @spec docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#effacement-massif-des-anciens-logs--sls-128
// @verifies docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#effacement-massif-des-anciens-logs--sls-128
export async function byteBudget(c) {
  let plan,initialPayload,overhead,firstExact;
  for(const extra of [0,1]) {
    const {service,fn,invoke}=await corpus(c,'byte-volume-corpus');
    const before=await inspectJournal(c);const calibration=await invoke({mode:'silent'});
    const calibrated=await inspectJournal(c);
    const measured=calibrated.journal.payload_bytes-before.journal.payload_bytes;
    const actualPlatform=calibrated.events.filter(row=>row.invocation_id===calibration.id);
    assert(actualPlatform.every(row=>row.source==='platform'));
    assert.equal(actualPlatform.reduce((sum,row)=>sum+row.payload_bytes,0),measured);
    if(extra===0) {
      overhead=measured;initialPayload=calibrated.journal.payload_bytes;
      plan=bytePlan(initialPayload,overhead);
    } else {
      assert.equal(measured,overhead);assert.equal(calibrated.journal.payload_bytes,initialPayload);
    }
    const batches=plan.map(lengths=>[...lengths]);
    if(extra) {
      const last=batches.at(-1),index=last.findIndex(value=>value<4095);assert(index>=0);last[index]+=1;
    }
    const ids=[];let expected=initialPayload,prior;
    for(let index=0;index<batches.length;index++) {
      const lengths=batches[index];assert(lengths.reduce((sum,value)=>sum+value+1,0)<=65536);
      if(index===batches.length-1)prior=await inspectJournal(c);
      const row=await invoke({mode:'batch',lengths});ids.push(row.id);
      assert.equal(row.logs_truncated,false);
      expected+=overhead+lengths.reduce((sum,length,line)=>sum+length+metadataBytes(line+1),0);
      if(index%20===0 || index===batches.length-1)console.log('JOURNAL byte-budget',extra,index+1,'/',batches.length);
    }
    assert.equal(expected,BYTE_LIMIT+extra);
    const after=await inspectJournal(c);assert(after.journal.event_count<10000);
    const last=after.events.filter(row=>row.invocation_id===ids.at(-1));
    assert.equal(last.reduce((sum,row)=>sum+row.payload_bytes,0),expected-prior.journal.payload_bytes);
    assert.equal(last.filter(row=>row.source==='application').length,batches.at(-1).length);
    for(const row of last.filter(row=>row.source==='application')) {
      assert(!row.message_truncated && !row.collection_truncated && !row.projection_truncated);
      assert.equal(row.message_bytes,batches.at(-1)[row.metadata.line-1]);
      assert.equal(row.message_sha256,shaText('a'.repeat(row.message_bytes)));
    }
    if(extra===0) {
      assert.equal(after.journal.payload_bytes,BYTE_LIMIT);
      assert.equal(after.journal.evicted_sequence,calibrated.journal.evicted_sequence);
      firstExact={function_id:fn.id,event_count:after.journal.event_count,payload_bytes:after.journal.payload_bytes};
    } else {
      assert(after.journal.payload_bytes<=BYTE_LIMIT);
      const removed=prior.events.filter(row=>!after.events.some(current=>current.id===row.id));assert(removed.length>0);
      assert.equal(removed.reduce((sum,row)=>sum+row.payload_bytes,0),expected-after.journal.payload_bytes);
      assert.equal(after.journal.evicted_sequence,Math.max(...removed.map(row=>row.sequence)));
    }
    c.observations.push({scenario:extra?'actual-byte-boundary-plus-one':'actual-byte-boundary-exact',function_id:fn.id,
      calibration_id:calibration.id,initial_payload_bytes:initialPayload,platform_bytes_per_call:overhead,
      invocations:ids,batches,computed_unbounded_payload:expected,event_count:after.journal.event_count,
      payload_bytes:after.journal.payload_bytes,evicted_sequence:after.journal.evicted_sequence,first_exact:extra?firstExact:null});
    if(extra) {
      await c.value(endpoint(fn),{method:'DELETE'});
      await c.value('/api/services/'+service.id,{method:'DELETE'});service.retired=true;
      const cleared=await inspectJournal(c),calls=cleared.invocations.filter(row=>row.function_id===fn.id);
      assert(calls.length>0 && calls.every(row=>row.log_bytes===0 && row.logs_collection_state==='expired'));
      assert.equal(cleared.journal.event_count,0);assert.equal(cleared.journal.payload_bytes,0);
      assert(!cleared.functions.find(row=>row.id===fn.id).purged_at);
      c.observations.push({scenario:'byte-boundary-service-logs-cleared-before-physical-purge',
        function_id:fn.id,service_id:service.id,invocations:calls.length,legacy_log_bytes:0,event_count:0,payload_bytes:0});
      await c.save();
    }
    await c.retireServices();
  }
}

// Expected digest of public, synthetic message bytes, independent of product code.
import {createHash} from 'node:crypto';
function shaText(value) {return createHash('sha256').update(value).digest('hex');}
