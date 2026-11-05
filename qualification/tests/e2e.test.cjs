// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
// @verifies docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { randomUUID, pbkdf2 } = require('node:crypto');
const derive = require('node:util').promisify(pbkdf2);
const net = require('node:net');
const http = require('node:http');
const { setTimeout: pause } = require('node:timers/promises');
const { request, call } = require('./http.cjs');
const key = `e2e-${randomUUID()}`;
const keys = new Set([key]);
const resource = (name, suffix = '') => { const id = key + suffix; keys.add(id); return `${name}?key=${id}`; };
before(async () => {
  assert.ok(process.env.QUALIFICATION_BUSINESS_TOKEN, 'PRECONDITION: actual cell business token required');
  assert.ok(process.env.QUALIFICATION_SYNTHETIC_SECRET, 'PRECONDITION: actual cell secret required');
  assert.equal(process.env.QUALIFICATION_PUBLIC_LABEL, 'qualification-dev');
  const health = await request('/healthz');
  assert.equal(health.status, 200);
  assert.equal(health.body.kind, 'qualification-reference-runner');
});
after(async () => {
  for (const id of keys) for (const name of ['state', 'cache', 'worker']) {
    assert.equal((await call(`${name}?key=${id}`, { method: 'DELETE' })).status, 200, `cleanup ${name}`);
  }
  assert.equal((await call(resource('state'))).body.count, 0);
  assert.equal((await call(resource('worker'))).status, 404);
});

test('deployed catalog exposes twelve functions and honestly reports platform limits', async () => {
  const result = await request('/catalog');
  assert.equal(result.status, 200);
  assert.equal(result.body.functions.length, 12);
  assert.equal(result.body.perFunctionMemoryEnforced, false);
  assert.equal(result.body.platformImplemented, false);
});
test('real HTTP invocation preserves event and runtime context', async () => {
  const first = await call('echo?item=one', { method: 'POST', value: { message: 'independent application' }, headers: { 'x-qualification-tag': 'trace-1' } });
  assert.equal(first.status, 200);
  assert.equal(first.body.method, 'POST');
  assert.equal(first.body.query.item, 'one');
  assert.equal(JSON.parse(first.body.body).message, 'independent application');
  assert.equal(first.body.tag, 'trace-1');
  assert.ok(first.body.remainingMs > 0 && first.body.remainingMs <= 2000);
  assert.equal(first.headers.get('x-qualification-request-id'), first.body.requestId);
  assert.notEqual(first.body.requestId, (await call('echo')).body.requestId);
});
test('real binary request and response preserve bytes', async () => {
  const bytes = Buffer.from([0, 1, 127, 255]);
  const echoed = await call('echo', { method: 'POST', raw: bytes, headers: { 'content-type': 'application/octet-stream' } });
  assert.equal(echoed.body.isBase64Encoded, true);
  assert.deepEqual(Buffer.from(echoed.body.body, 'base64'), bytes);
  assert.deepEqual((await call('binary')).bytes, bytes);
});
test('callback and Promise complete the actual invocation once', async () => {
  const result = await call('callback', { method: 'POST' });
  assert.equal(result.status, 200);
  assert.equal(result.body.completion, 'callback');
});
test('counter creates, persists, validates and deletes a real named resource', async () => {
  assert.equal((await call(resource('state'))).body.count, 0);
  assert.equal((await call(resource('state'), { method: 'POST', value: { increment: 2 } })).body.count, 2);
  assert.equal((await call(resource('state'))).body.count, 2);
  assert.equal((await call(resource('state'), { method: 'POST', value: { increment: -1 } })).status, 400);
  assert.equal((await call(resource('state'), { method: 'DELETE' })).body.deleted, true);
  assert.equal((await call(resource('state'))).body.count, 0);
});
test('real cache hit and invalidation preserve a separate counter', async () => {
  await call(resource('state'), { method: 'POST', value: { increment: 2 } });
  const first = (await call(resource('cache'))).body;
  assert.equal(first.hit, false);
  assert.equal((await call(resource('cache'))).body.generation, first.generation);
  assert.equal((await call(resource('cache'), { method: 'DELETE' })).body.invalidated, true);
  const rebuilt = (await call(resource('cache'))).body;
  assert.equal(rebuilt.hit, false);
  assert.notEqual(rebuilt.generation, first.generation);
  assert.equal((await call(resource('state'))).body.count, 2);
});
test('one contention scenario sends two real HTTP writes without loss', async () => {
  const before = (await call(resource('state'))).body.count;
  const pending = [call(resource('state'), { method: 'POST', value: { increment: 1 } }),
    call(resource('state'), { method: 'POST', value: { increment: 1 } })];
  const results = [];
  for (const response of pending) results.push(await response);
  assert.deepEqual(results.map(result => result.body.count).sort((a, b) => a - b), [before + 1, before + 2]);
  assert.equal((await call(resource('state'))).body.count, before + 2);
});
test('real computation checkpoints, resumes and rejects changed job inputs', async () => {
  const items = Array.from({ length: 64 }, (_, index) => `qualification-item-${index}`);
  let result = await call(resource('worker'), { method: 'POST', value: { items } });
  assert.equal(result.status, 200);
  assert.ok(result.body.next > 0 && result.body.next < items.length, 'first request performs work and checkpoints before completion');
  assert.ok(result.body.remainingMs > 0);
  assert.equal((await call(resource('worker'), { method: 'POST', value: { items: ['changed'] } })).status, 409);
  let previous = result.body.next;
  for (let attempt = 0; attempt < 32 && !result.body.complete; attempt += 1) {
    result = await call(resource('worker'), { method: 'POST', value: {} });
    assert.equal(result.status, 200);
    assert.equal(result.body.next - previous, result.body.processed);
    assert.ok(result.body.next > previous);
    previous = result.body.next;
  }
  assert.equal(result.body.complete, true);
  const job = (await call(resource('worker'))).body;
  assert.equal(job.results.length, items.length);
  assert.deepEqual(job.results.map(row => row.index), items.map((_, index) => index));
  for (const row of job.results) assert.equal(row.digest, (await derive(items[row.index], 'p2enjoy-qualification', 100000, 32, 'sha256')).toString('hex'));
  assert.equal((await call(resource('worker'), { method: 'POST', value: {} })).body.processed, 0);
});
test('real invalid resource names and malformed inputs are refused', async () => {
  for (const name of ['state', 'cache', 'worker']) assert.equal((await call(`${name}?key=..%2Fescape`)).status, 400);
  assert.equal((await call('sleep', { method: 'POST', value: { milliseconds: -1 } })).status, 400);
  assert.equal((await call('sleep', { method: 'POST', raw: '{broken' })).status, 400);
  assert.equal((await call(resource('worker'), { method: 'POST', value: { items: [] } })).status, 400);
});
test('real exceptions, Promise rejection and process exit remain distinct', async () => {
  for (const kind of ['throw', 'reject', 'exit']) {
    const result = await call('failure', { method: 'POST', value: { kind } });
    assert.equal(result.status, 500);
    assert.equal(result.body.error, kind === 'exit' ? 'handler_exit' : 'handler_error');
    assert.equal((await call('echo')).status, 200);
  }
});
test('actual CPU loop and sleep are interrupted after handler entry and reaped', async () => {
  for (const [name, value] of [['spin', {}], ['sleep', { milliseconds: 3000 }]]) {
    const started = Date.now();
    const result = await call(name, { method: 'POST', value });
    assert.equal(result.status, 504);
    assert.equal(result.body.error, 'invocation_timeout');
    assert.equal(result.headers.get('x-qualification-handler-started'), 'true');
    assert.ok(Date.now() - started < 3500);
    assert.equal((await request('/healthz')).body.activeInvocations, 0);
    assert.equal((await call('echo')).status, 200);
  }
});
test('real function-to-function call correlates both executions', async () => {
  const result = await call('relay', { method: 'POST', value: { target: 'echo' } });
  assert.equal(result.status, 200);
  assert.equal(result.body.upstreamStatus, 200);
  assert.equal(result.body.child.tag, result.body.parentRequestId);
  assert.notEqual(result.body.child.requestId, result.body.parentRequestId);
});
test('relay propagates real peer failure and real peer timeout without a fake server', async () => {
  const failed = await call('relay', { method: 'POST', value: { target: 'failure', payload: { kind: 'throw' } } });
  assert.equal(failed.status, 500);
  assert.equal(failed.body.child.error, 'handler_error');
  const timedOut = await call('relay', { method: 'POST', value: { target: 'sleep', payload: { milliseconds: 3000 } } });
  assert.equal(timedOut.status, 504);
  assert.equal(timedOut.body.child.error, 'invocation_timeout');
  assert.equal((await call('relay', { method: 'POST', value: { target: 'https://invalid.example' } })).status, 400);
});
test('unknown route and invalid method refuse before invocation', async () => {
  for (const [result, status] of [[await call('missing'), 404], [await call('binary', { method: 'POST' }), 405]]) {
    assert.equal(result.status, status);
    assert.equal(result.headers.get('x-qualification-request-id'), null);
  }
});
test('oversized request receives real 413 and next invocation succeeds', async () => {
  const result = await call('echo', { method: 'POST', raw: 'x'.repeat(300000) });
  assert.equal(result.status, 413);
  assert.equal(result.headers.get('x-qualification-request-id'), null);
  assert.equal((await call('echo')).status, 200);
});
test('configuration reflects the actual cell environment without fabricated injection', async () => {
  const result = await call('configuration');
  assert.equal(result.body.label, process.env.QUALIFICATION_PUBLIC_LABEL || 'qualification');
  assert.equal(result.body.secretPresent, Boolean(process.env.QUALIFICATION_SYNTHETIC_SECRET));
  assert.equal((await call('echo')).body.secretPresent, false);
});
test('missing credentials or configuration never grant business access', async () => {
  const result = await call('business', { method: 'POST' });
  assert.equal(result.status, process.env.QUALIFICATION_BUSINESS_TOKEN ? 401 : 503);
  assert.equal((await call('business', { method: 'POST', headers: { authorization: 'Bearer qualification-user' } })).status,
    process.env.QUALIFICATION_BUSINESS_TOKEN ? 401 : 503);
});
test('real configured business credential grants access and a wrong credential is rejected',
  async () => {
    const result = await call('business', { method: 'POST', headers: { authorization: `Bearer ${process.env.QUALIFICATION_BUSINESS_TOKEN}` } });
    assert.equal(result.status, 200);
    assert.equal(result.body.allowed, true);
    const wrong = await call('business', { method: 'POST', headers: { authorization: `Bearer ${randomUUID()}` } });
    assert.equal(wrong.status, 401);
  });
test('real configured secret reaches only the declared function without response leakage',
  async () => {
    const result = await call('configuration');
    assert.equal(result.body.secretPresent, true);
    assert.equal((await call('echo')).body.secretPresent, false);
    assert.equal(JSON.stringify(result.body).includes(process.env.QUALIFICATION_SYNTHETIC_SECRET), false);
  });

// Live observation bounds synchronization; no response or dependency is substituted.
async function until(predicate, label, timeout = 8000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) { if (await predicate()) return; await pause(25); }
  assert.fail(`Timed out: ${label}`);
}
function rawRequest(route, { method = 'POST', length = 2, headers = {} } = {}) {
  let req;
  const response = new Promise((resolve, reject) => {
    req = http.request(`http://qualification:8080${route}`, { method,
      headers: { 'content-length': length, ...headers } }, res => {
      const chunks = []; res.on('data', c => chunks.push(c));
      res.on('end', () => { try { const bytes = Buffer.concat(chunks); resolve({ status: res.statusCode,
        headers: res.headers, bytes, body: bytes.length && (res.headers['content-type'] || '').includes('application/json') ? JSON.parse(bytes.toString()) : null }); } catch(error) { reject(error); } });
      res.on('error', reject);
    });
    req.on('error', reject);
    req.setTimeout(8000, () => req.destroy(new Error('Real HTTP request timed out')));
  });
  response.catch(() => {});
  req.flushHeaders();
  return { req, response };
}

test('catalog describes every deployed handler, stable ID and resource declaration', async () => {
  const c = (await request('/catalog')).body;
  assert.equal(c.service, 'p2enjoy-qualification'); assert.equal(c.runtime, 'nodejs24.x');
  const specs = { echo: [2,null], binary: [2,null], callback: [2,null], business: [2,null],
    configuration: [2,null], state: [2,'data'], cache: [2,'cache'], worker: [1,'data'],
    failure: [1,null], sleep: [1,null], spin: [0.4,null], relay: [3,null] };
  assert.deepEqual(c.functions.map(f => f.name).sort(), Object.keys(specs).sort());
  for (const f of c.functions) assert.deepEqual(f, { name: f.name, functionId: `qlf-${f.name}-v1`,
    handler: `src/handlers.${f.name}`, timeoutSeconds: specs[f.name][0], declaredMemoryMiB:128, storage:specs[f.name][1] });
});
test('HTTP event preserves repeated, empty, Unicode queries and peer context', async () => {
  const r = await call('echo?item=un&item=deux&empty=&unicode=%C3%A9%20%26%3D', {method:'POST',raw:'bonjour é'});
  assert.deepEqual(r.body.query, {item:'deux',empty:'',unicode:'é &='});
  assert.deepEqual(r.body.multiValueQuery.item,['un','deux']);
  assert.equal(r.body.path,'/functions/echo'); assert.equal(r.body.functionName,'echo');
  assert.equal(r.body.body,'bonjour é'); assert.equal(r.body.isBase64Encoded,false);
  assert.equal(r.body.requestContext.stage,'dev'); assert.ok(r.body.requestContext.identity.sourceIp);
  assert.equal((await call('echo')).body.body,'');
  const h = await call('echo',{method:'HEAD'}); assert.equal(h.status,200); assert.equal(h.bytes.length,0);
});
test('all route restrictions return exact refusals without starting a handler', async () => {
  for (const name of ['binary','configuration']) assert.equal((await call(name,{method:'POST'})).status,405);
  for (const name of ['callback','business','failure','sleep','spin','relay']) assert.equal((await call(name)).status,405);
  for (const path of ['/healthz','/catalog']) assert.equal((await request(path,{method:'POST'})).status,404);
  for (const path of ['/unknown','/functions/echo/','/functions/UPPER','/functions/%ZZ']) assert.equal((await request(path)).status,404);
  for (const name of ['state','cache','worker']) assert.equal((await call(resource(name),{method:'PUT'})).status,405);
  assert.equal((await call(resource('cache'),{method:'POST',value:{}})).status,405);
});
test('HTTP body accepts exactly 256 KiB and refuses the next byte including streamed chunks', async () => {
  assert.equal((await call('echo',{method:'POST',raw:'x'.repeat(262144)})).status,200);
  assert.equal((await call('echo',{method:'POST',raw:'x'.repeat(262145)})).status,413);
  const r=rawRequest('/functions/echo',{length:262145});
  r.req.write('x'.repeat(131072)); r.req.end('y'.repeat(131073));
  assert.equal((await r.response).status,413);
  assert.equal((await call('echo')).status,200);
});
test('callbacks exercise synchronous return, late completion, and callback error', async () => {
  for(const mode of ['sync','late']) assert.equal((await call('callback',{method:'POST',value:{mode}})).body.completion,mode);
  const r=await call('callback',{method:'POST',value:{mode:'error'}});
  assert.equal(r.status,500);assert.equal(r.body.error,'handler_error');
  for (const kind of ['invalid-response','invalid-status']) {
    const bad=await call('failure',{method:'POST',value:{kind}});
    assert.equal(bad.status,500);assert.equal(bad.body.error,'invalid_handler_response');
  }
});
test('counter rejects invalid increments and non-object JSON without changing persisted data', async () => {
  const r=resource('state','-bounds');
  assert.equal((await call(r,{method:'POST',value:{}})).body.count,1);
  assert.equal((await call(r,{method:'POST',value:{increment:10}})).body.count,11);
  for(const increment of [0,11,-1,1.5,'2',true,null]) assert.equal((await call(r,{method:'POST',value:{increment}})).status,400);
  for(const value of [null,[],true,3,'text']) assert.equal((await call(r,{method:'POST',value})).status,400);
  assert.equal((await call(r,{method:'POST',raw:'{'})).status,400);
  assert.equal((await call(r)).body.count,11);
  assert.equal((await call(resource('state','-other'))).body.count,0);
});
test('resource key grammar accepts its bounds and rejects unsafe or oversized keys', async () => {
  const good=['z',`bound-${randomUUID()}-`+'x'.repeat(21)]; assert.equal(good[1].length,64);
  for(const id of good){ if(id!=='z') keys.add(id); assert.equal((await call(`state?key=${id}`)).status,200); }
  for(const id of ['', 'x'.repeat(65), '../escape','with space','é','-prefix'])
    for(const name of ['state','cache','worker']) assert.equal((await call(`${name}?key=${encodeURIComponent(id)}`)).status,400);
  assert.equal((await call('state')).status,200);
});
test('cache hit, independent keys, and repeated deletes have observable real effects', async () => {
  const r=resource('cache','-bounds'); const a=(await call(r)).body;
  const b=(await call(r)).body; assert.equal(a.hit,false);assert.equal(b.hit,true);
  assert.equal(a.generation,b.generation);assert.equal(a.value,b.value);
  assert.notEqual((await call(resource('cache','-other'))).body.generation,a.generation);
  for(let i=0;i<2;i++) assert.equal((await call(r,{method:'DELETE'})).status,200);
  assert.equal((await call(r)).body.hit,false);
  for(let i=0;i<2;i++) assert.equal((await call(resource('state','-absent'),{method:'DELETE'})).status,200);
});
test('worker refuses absent inputs, malformed jobs and changes without overwriting accepted work', async () => {
  const r=resource('worker','-bounds');
  assert.equal((await call(r)).status,404);
  assert.equal((await call(r,{method:'POST',value:{}})).body.error,'items_required');
  for(const items of [null,[],{},'text',Array(129).fill('a'),[1],['x'.repeat(129)]])
    assert.equal((await call(r,{method:'POST',value:{items}})).status,400);
  for(const value of [null,[],true,4,'x']) assert.equal((await call(r,{method:'POST',value})).status,400);
  assert.equal((await call(r,{method:'POST',raw:'{'})).status,400);
  const items=['x'.repeat(128)]; const a=await call(r,{method:'POST',value:{items}});
  assert.equal(a.status,200);assert.equal(a.body.complete,true);
  const again=await call(r,{method:'POST',value:{items}});assert.equal(again.body.processed,0);
  assert.equal((await call(r,{method:'POST',value:{items:['different']}})).status,409);
  assert.deepEqual((await call(r)).body.results,a.body.results);
  assert.equal((await call(r,{method:'DELETE'})).status,200);assert.equal((await call(r)).status,404);
});
test('worker accepts 128 items and computes every result across real checkpoints', async () => {
  const items=Array.from({length:128},(_,i)=>`upper-${i}`);const r=resource('worker','-max');
  let next=await call(r,{method:'POST',value:{items}});assert.equal(next.status,200);
  const partial=(await call(r)).body;assert.ok(partial.next>0 && partial.next<128);
  for(let attempt=0;attempt<80&&!next.body.complete;attempt++) { next=await call(r,{method:'POST',value:{}});assert.equal(next.status,200); }
  assert.equal(next.body.complete,true);assert.equal(next.body.results.length,128);
  for(const [i,row] of next.body.results.entries()) { assert.equal(row.index,i);assert.equal(row.digest,(await derive(items[i],'p2enjoy-qualification',100000,32,'sha256')).toString('hex')); }
});
test('sleep executes defaults and valid durations and refuses all malformed durations', async () => {
  assert.equal((await call('sleep',{method:'POST',value:{}})).body.sleptMs,10);
  for(const milliseconds of [0,20]) assert.equal((await call('sleep',{method:'POST',value:{milliseconds}})).body.sleptMs,milliseconds);
  for(const milliseconds of [-1,5001,1.5,'10',true,null]) assert.equal((await call('sleep',{method:'POST',value:{milliseconds}})).status,400);
  for(const value of [null,[],true,1,'text']) assert.equal((await call('sleep',{method:'POST',value})).status,400);
  assert.equal((await call('sleep',{method:'POST',value:{milliseconds:5000}})).status,504);
});
test('relay handles default peer, payload, real successful sleep, and malformed inputs', async () => {
  const a=await call('relay',{method:'POST',value:{payload:{text:'through actual HTTP'}}});
  assert.equal(a.body.upstreamStatus,200);assert.deepEqual(JSON.parse(a.body.child.body),{text:'through actual HTTP'});
  assert.equal(a.body.child.query.from,'relay');
  const b=await call('relay',{method:'POST',value:{target:'sleep',payload:{milliseconds:0}}});
  assert.equal(b.status,200);assert.equal(b.body.child.sleptMs,0);
  for(const value of [null,[],true,1,'text',{target:4},{target:null},{target:''},{target:'missing'}]) assert.equal((await call('relay',{method:'POST',value})).status,400);
  assert.equal((await call('relay',{method:'POST',raw:'{'})).status,400);
});
test('business checks bearer syntax and equal-length incorrect confidential credentials', async () => {
  const token=process.env.QUALIFICATION_BUSINESS_TOKEN;
  const wrong=(token[0]==='a'?'b':'a')+token.slice(1);
  for(const authorization of ['Basic '+token,'Bearer '+wrong,'Bearer short','Bearer']) {
    const r=await call('business',{method:'POST',headers:{authorization}});
    assert.equal(r.status,401);assert.equal(r.body.layer,'handler');assert.equal(r.body.error,'business_unauthorized');
    assert.equal(r.bytes.toString().includes(token),false);
  }
  const echo=await call('echo');assert.equal(echo.body.businessTokenPresent,false);
});
test('real saturation refuses request 17 and returns to normal after accepted requests drain', async () => {
  const holds=[];
  try {
    for(let i=0;i<16;i++){const h=rawRequest('/functions/echo');h.req.write('x');holds.push(h);}
    await until(async()=> (await request('/healthz')).body.pendingRequests===16,'sixteen real admissions');
    const busy=await call('echo');assert.equal(busy.status,429);assert.equal(busy.body.error,'reference_runner_busy');
    assert.equal(busy.headers.get('x-qualification-request-id'),null);
  } finally { for(const h of holds) h.req.end('x');for(const h of holds) assert.equal((await h.response).status,200); }
  await until(async()=> (await request('/healthz')).body.pendingRequests===0,'queue drained');
  assert.equal((await call('echo')).status,200);
});
test('relay propagates a real 429 from its peer under actual admission saturation', async () => {
  const holds=[];
  try {
    for(let i=0;i<15;i++){const h=rawRequest('/functions/echo');h.req.write('x');holds.push(h);}
    await until(async()=> (await request('/healthz')).body.pendingRequests===15,'fifteen real admissions');
    const busy=await call('relay',{method:'POST',value:{target:'echo'}});
    assert.equal(busy.status,429);assert.equal(busy.body.upstreamStatus,429);assert.equal(busy.body.child.error,'reference_runner_busy');
  } finally {for(const h of holds) h.req.end('x');for(const h of holds) assert.equal((await h.response).status,200);}
});
test('queued invocation gets its own deadline after the preceding real timeout', async () => {
  const first=call('sleep',{method:'POST',value:{milliseconds:5000}});
  await until(async()=> (await request('/healthz')).body.activeInvocations===1,'sleep active');
  const second=call('sleep',{method:'POST',value:{milliseconds:20}});
  assert.equal((await first).status,504);const result=await second;assert.equal(result.status,200);assert.equal(result.body.sleptMs,20);
});
test('real client disconnect releases body admission and leaves an accepted handler bounded', async () => {
  const incomplete=rawRequest('/functions/echo');incomplete.req.write('x');
  await until(async()=> (await request('/healthz')).body.pendingRequests===1,'incomplete body admitted');
  incomplete.req.destroy();await incomplete.response.catch(()=>{});
  await until(async()=> (await request('/healthz')).body.pendingRequests===0,'incomplete body released');
  const data=JSON.stringify({milliseconds:5000});const active=rawRequest('/functions/sleep',{length:Buffer.byteLength(data)});active.req.end(data);
  await until(async()=> (await request('/healthz')).body.activeInvocations===1,'accepted sleep active');
  active.req.destroy();await active.response.catch(()=>{});
  await until(async()=> (await request('/healthz')).body.pendingRequests===0 && (await request('/healthz')).body.activeInvocations===0,'disconnected invocation reaped');
  assert.equal((await call('echo')).status,200);
});
test('real server expires an incomplete body and releases its admission', async () => {
  const held=rawRequest('/functions/echo');held.req.setTimeout(15000);held.req.write('x');
  try {
    await until(async()=> (await request('/healthz')).body.pendingRequests===1,'slow body admitted');
    const result=await held.response;assert.equal(result.status,408);
    await until(async()=> (await request('/healthz')).body.pendingRequests===0,'server expired body released');
  } finally {held.req.destroy();}
});
test('real server expires incomplete HTTP headers', async () => {
  const result=await new Promise((resolve,reject)=>{
    const socket=net.connect(8080,'qualification');let text='';
    socket.setTimeout(9000,()=>socket.destroy(new Error('Header timeout was not enforced')));
    socket.on('connect',()=>socket.write('GET /healthz HTTP/1.1\r\nHost: qualification\r\nX-Unfinished: '));
    socket.on('data',chunk=>{text+=chunk.toString();});
    socket.on('end',()=>resolve(text));socket.on('error',reject);
  });
  assert.match(result,/^HTTP\/1\.1 408 /);assert.equal((await call('echo')).status,200);
});
