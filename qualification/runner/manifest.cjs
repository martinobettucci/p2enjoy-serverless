// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const YAML = require('yaml');
const root = path.resolve(__dirname, '..');

function loadManifest(text = fs.readFileSync(path.join(root, 'serverless.yml'), 'utf8')) {
  const data = YAML.parse(text, { maxAliasCount: 0, uniqueKeys: true });
  if (data?.service !== 'p2enjoy-qualification' || data.provider?.name !== 'p2enjoy'
      || data.provider.runtime !== 'nodejs24.x' || !data.functions) throw new Error('Invalid fixture manifest');
  const allowed = new Set(['handler', 'timeout', 'memorySize', 'events', 'p2enjoy']);
  const ids = new Set();
  for (const [name, fn] of Object.entries(data.functions)) {
    if (!/^[a-z][a-z0-9-]*$/.test(name) || Object.keys(fn).some(key => !allowed.has(key))) throw new Error('Unsupported function field');
    if (!/^src\/handlers\.[a-zA-Z]+$/.test(fn.handler)) throw new Error('Invalid fixture handler');
    if (!(fn.timeout >= 0.1 && fn.timeout <= 5) || ![128, 256].includes(fn.memorySize)) throw new Error('Invalid resource declaration');
    const event = fn.events?.[0]?.http;
    if (fn.events?.length !== 1 || event?.path !== name || !['any', 'get', 'post'].includes(event.method)) throw new Error('Invalid fixture event');
    const extension = fn.p2enjoy || {};
    if (Object.keys(extension).some(key => !['functionId', 'storage', 'environmentKeys'].includes(key))) throw new Error('Unsupported extension');
    if (extension.storage && !['data', 'cache'].includes(extension.storage)) throw new Error('Invalid storage');
    const id = extension.functionId || `qlf-${name}-v1`;
    if (!/^qlf-[a-z0-9-]+$/.test(id) || ids.has(id)) throw new Error('Invalid or duplicate function ID');
    ids.add(id);
    const environmentKeys = extension.environmentKeys || [];
    if (!Array.isArray(environmentKeys) || environmentKeys.some(key => !['QUALIFICATION_PUBLIC_LABEL', 'QUALIFICATION_SYNTHETIC_SECRET', 'QUALIFICATION_BUSINESS_TOKEN'].includes(key))) throw new Error('Invalid environment key');
    fn.functionId = id;
    fn.environmentKeys = environmentKeys;
  }
  return data;
}
module.exports = { loadManifest, root };
