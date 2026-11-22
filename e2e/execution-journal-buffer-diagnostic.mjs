// @spec docs/BACKLOG.md#sls-120 | docs/EXECUTION_LOGS.md#collecte-et-événements
// @verifies docs/BACKLOG.md#sls-120
// Observe actual post-redaction buffers; zero functional qualification groups.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {JournalCampaign,privateInput,diagnosis,sha,endpoint} from './execution-journal-harness.mjs';
import {inspectJournal} from './execution-journal-native.mjs';

const c=new JournalCampaign('api');
const serviceSecret='journal-private-service-'+randomUUID(),functionSecret='journal-private-function-'+randomUUID();
const observations=[];
try {
  await c.open(await privateInput());
  c.stage='Diagnostic120 : corpus original sans secrets puis avec deux secrets effectifs';await c.save();
  const native=await inspectJournal(c,'baseline');assert.equal(native.migrations.length,11);
  for(const withSecrets of [false,true]) {
    const service=await c.service(withSecrets?'buffer-with-effective-secrets':'buffer-without-effective-secrets',
      withSecrets?{secrets:{JOURNAL_SERVICE_SECRET:serviceSecret}}:undefined);
    const fn=await c.function(service,withSecrets?'buffer-known-secret-handler':'buffer-plain-handler',{},
      withSecrets?{secrets:{JOURNAL_FUNCTION_SECRET:functionSecret}}:{});
    const token=await c.mint(service,['read'],[fn.id]),marker=withSecrets?'buffer-known':'buffer-plain';
    const version=await c.publish(fn,marker);await c.promote(fn,version.code_hash);
    for(const sample of [
      ...[65535,65536,65537].map(bytes=>({label:'bytes-'+bytes,body:{mode:'bytes',bytes},requested_bytes:bytes})),
      {label:'secret-crosses-capture-boundary',body:{mode:'line',text:'a'.repeat(65536-8)+functionSecret},
        requested_bytes:65536-8+Buffer.byteLength(functionSecret)+1},
    ]) {
      c.stage='Diagnostic120 : '+(withSecrets?'avec secrets':'sans secret')+' / '+sample.label;await c.save();
      const result=await c.invoke(fn,token,sample.body),record=await c.terminal(fn,result.id);
      const rows=await c.value(endpoint(fn)+'/logs?source=application&invocation='+result.id+'&limit=20');
      const value={scenario:'buffer-sample',sample:sample.label,with_effective_secrets:withSecrets,
        function_id:fn.id,invocation_id:result.id,code_hash:result.headers['x-serverless-code-hash'],
        requested_bytes:sample.requested_bytes,observed_bytes:Buffer.byteLength(record.logs),
        logs_truncated:record.logs_truncated,collection_state:record.logs_collection_state,
        buffer_sha256:sha(record.logs),only_ascii_a:/^a*$/.test(record.logs),
        full_known_value_present:record.logs.includes(serviceSecret) || record.logs.includes(functionSecret),
        partial_known_prefix_present:record.logs.includes(functionSecret.slice(0,8)),
        effective_secret_lengths:withSecrets?[Buffer.byteLength(serviceSecret),Buffer.byteLength(functionSecret)]:[],
        journal_total:rows.total,journal_projection:rows.items.map(row=>({id:row.id,bytes:Buffer.byteLength(row.message),
          message_sha256:sha(row.message),message_truncated:row.message_truncated,collection_truncated:row.collection_truncated,
          projection_truncated:row.projection_truncated}))};
      observations.push(value);c.observations.push(value);await c.save();
      assert.equal(result.data.marker,marker);assert.equal(value.code_hash,version.code_hash);
      assert.equal(record.state,'succeeded');assert(record.handler_started && record.logs_collection_state==='collected');
      assert(value.observed_bytes<=65536 && typeof record.logs_truncated==='boolean');
      if(withSecrets)assert.equal(value.full_known_value_present,false);
      console.log(JSON.stringify({sample:sample.label,with_secrets:withSecrets,observed_bytes:value.observed_bytes,
        truncated:value.logs_truncated,partial_prefix_present:value.partial_known_prefix_present}));
    }
  }
  assert.equal(observations.length,8);c.scenariosPassed=true;
} catch(error) {c.failure=diagnosis(error);process.exitCode=1;}
finally {
  try {await c.close({nativeCleanup:async()=>{
    const result=await inspectJournal(c,'cleanup');c.observations.push({scenario:'native-complete-cleanup',result});
  }});} catch(error) {c.cleanupErrors.push({phase:'diagnostic-cleanup',...diagnosis(error)});c.completed=false;process.exitCode=1;await c.save();}
  if(!c.completed)process.exitCode=1;
}
console.log(JSON.stringify({completed:c.completed,groups:0,observations:observations.length,cleanup:c.cleanup,report:c.report.pathname}));
