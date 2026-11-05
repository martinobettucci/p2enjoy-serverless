// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
// @verifies docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const assert = require('node:assert/strict');
const { loadManifest } = require('./manifest.cjs');
const handlers = require('../src/handlers.cjs');
const manifest = loadManifest();
for (const [name, config] of Object.entries(manifest.functions)) {
  assert.equal(typeof handlers[config.handler.split('.').at(-1)], 'function', name);
}
console.log(JSON.stringify({ service: manifest.service, functions: Object.keys(manifest.functions).length, manifest: 'valid', source: 'synthetic-only' }));
