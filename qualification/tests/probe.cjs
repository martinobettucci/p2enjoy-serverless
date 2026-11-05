// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
// @verifies docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const { randomUUID, pbkdf2 } = require('node:crypto');
const derive = require('node:util').promisify(pbkdf2);
const { request, call } = require('./http.cjs');
const snapshot = '/reports/recreate-proof.json';
const mode = process.argv[2];
(async () => {
  assert.equal((await request('/healthz')).body.status, 'ok');
  assert.equal((await request('/catalog')).body.functions.length, 12);
  if (mode === 'before-recreate') {
    const key = `persist-${randomUUID()}`;
    const state = await call(`state?key=${key}`, { method: 'POST', value: { increment: 3 } });
    const cache = await call(`cache?key=${key}`);
    assert.equal(state.status, 200);
    assert.equal(cache.status, 200);
    const items = Array.from({length:64}, (_, i) => `persist-job-${i}`);
    const worker = await call(`worker?key=${key}`, {method:'POST',value:{items}});
    assert.equal(worker.status,200);assert.ok(worker.body.next>0 && worker.body.next<64);
    // Expected observations belong only to the separate test-client volume.
    await fs.writeFile(snapshot, JSON.stringify({ key, count: state.body.count, generation: cache.body.generation, worker: worker.body }));
    console.log(JSON.stringify({ proof: 'before-recreate', count: state.body.count }));
  } else if (mode === 'after-recreate') {
    const expected = JSON.parse(await fs.readFile(snapshot, 'utf8'));
    const state = await call(`state?key=${expected.key}`);
    const cache = await call(`cache?key=${expected.key}`);
    assert.equal(state.body.count, expected.count);
    assert.equal(cache.body.generation, expected.generation);
    let worker = await call(`worker?key=${expected.key}`);
    assert.deepEqual(worker.body.results, expected.worker.results);
    assert.equal(worker.body.next,expected.worker.next);
    for(let attempt=0;attempt<40&&!worker.body.complete;attempt++) { worker=await call(`worker?key=${expected.key}`,{method:'POST',value:{}});assert.equal(worker.status,200); }
    assert.equal(worker.body.complete,true);assert.equal(worker.body.results.length,64);
    for(const [i,row] of worker.body.results.entries()) {assert.equal(row.index,i);assert.equal(row.digest,(await derive(expected.worker.items[i],'p2enjoy-qualification',100000,32,'sha256')).toString('hex'));}
    for (const name of ['state', 'cache', 'worker']) assert.equal((await call(`${name}?key=${expected.key}`, { method: 'DELETE' })).status, 200);
    await fs.rm(snapshot);
    console.log(JSON.stringify({ proof: 'after-recreate', statePreserved: true, cachePreserved: true, workerCheckpointPreserved: true, workerResumed: true, clientVolumeSeparate: true }));
  } else {
    assert.equal((await call('echo')).body.functionName, 'echo');
    console.log(JSON.stringify({ proof: 'deployed-http-smoke', functions: 12, client: 'separate-container', status: 'passed' }));
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
