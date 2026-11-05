// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
// @verifies docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const assert=require('node:assert/strict');
const {call}=require('./http.cjs');
(async()=>{
  assert.equal(Boolean(process.env.QUALIFICATION_BUSINESS_TOKEN),false);
  assert.equal(Boolean(process.env.QUALIFICATION_SYNTHETIC_SECRET),false);
  assert.equal(Boolean(process.env.QUALIFICATION_PUBLIC_LABEL),false);
  const c=await call('configuration');assert.equal(c.status,200);
  assert.deepEqual(c.body,{label:'qualification',secretPresent:false});
  const b=await call('business',{method:'POST'});assert.equal(b.status,503);assert.equal(b.body.error,'business_auth_unconfigured');
  console.log(JSON.stringify({configurationAbsent:'passed',cases:2}));
})().catch(()=>{console.error('Actual absent-configuration campaign failed');process.exitCode=1;});
