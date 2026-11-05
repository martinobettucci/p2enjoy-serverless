// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
// All declarations implement this synthetic fixture contract. No client code/data.
'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID, timingSafeEqual, createHash, pbkdf2Sync } = require('node:crypto');
const { setTimeout: wait } = require('node:timers/promises');

function response(value, statusCode = 200) {
  return { statusCode, headers: { 'content-type': 'application/json' }, body: JSON.stringify(value) };
}
function body(event) {
  try {
    const value = JSON.parse(event.body || '{}');
    return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
  }
  catch { return null; }
}
function resourceFile(event, directory, base) {
  const key = event.queryStringParameters?.key;
  if (key === undefined) return path.join(directory, `${base}.json`);
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(key)) return null;
  return path.join(directory, `${base}.${key}.json`);
}
async function read(file, fallback) {
  try { return JSON.parse(await fs.readFile(file, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return fallback; throw error; }
}
async function write(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.${randomUUID()}.tmp`;
  await fs.writeFile(temporary, JSON.stringify(value), { mode: 0o600 });
  await fs.rename(temporary, file);
}

exports.echo = async (event, context) => response({
  method: event.httpMethod, path: event.path,
  query: event.queryStringParameters, body: event.body,
  multiValueQuery: event.multiValueQueryStringParameters,
  requestContext: event.requestContext,
  isBase64Encoded: event.isBase64Encoded,
  tag: event.headers['x-qualification-tag'] || null,
  requestId: context.awsRequestId, functionName: context.functionName,
  remainingMs: context.getRemainingTimeInMillis(),
  secretPresent: Boolean(process.env.QUALIFICATION_SYNTHETIC_SECRET),
  businessTokenPresent: Boolean(process.env.QUALIFICATION_BUSINESS_TOKEN),
});

exports.binary = async () => ({
  statusCode: 200, headers: { 'content-type': 'application/octet-stream' },
  body: Buffer.from([0, 1, 127, 255]).toString('base64'), isBase64Encoded: true,
});

exports.callback = (event, context, callback) => {
  const mode = body(event)?.mode;
  if (mode === 'sync') return response({ completion: 'sync' });
  if (mode === 'error') { callback(new Error('qualification callback error')); return; }
  if (mode === 'late') { setTimeout(() => callback(null, response({ completion: 'late' })), 20); return; }
  callback(null, response({ completion: 'callback', requestId: context.awsRequestId }));
  callback(null, response({ completion: 'ignored' }));
  return Promise.resolve(response({ completion: 'also-ignored' }));
};

exports.business = async (event) => {
  const expected = process.env.QUALIFICATION_BUSINESS_TOKEN;
  if (!expected) return response({ error: 'business_auth_unconfigured', layer: 'handler' }, 503);
  const supplied = event.headers.authorization?.match(/^Bearer (.+)$/)?.[1] || '';
  const expectedBytes = Buffer.from(expected);
  const suppliedBytes = Buffer.from(supplied);
  if (suppliedBytes.length !== expectedBytes.length || !timingSafeEqual(suppliedBytes, expectedBytes)) {
    return response({ error: 'business_unauthorized', layer: 'handler' }, 401);
  }
  return response({ allowed: true, layer: 'handler' });
};

exports.configuration = async () => response({
  label: process.env.QUALIFICATION_PUBLIC_LABEL || 'qualification',
  secretPresent: Boolean(process.env.QUALIFICATION_SYNTHETIC_SECRET),
});

exports.state = async (event) => {
  const file = resourceFile(event, process.env.QUALIFICATION_DATA_DIR, 'counter');
  if (!file) return response({ error: 'invalid_resource_key' }, 400);
  if (event.httpMethod === 'DELETE') {
    await fs.rm(file, { force: true });
    return response({ deleted: true });
  }
  const current = await read(file, { count: 0 });
  if (event.httpMethod === 'POST') {
    const payload = body(event);
    const increment = payload?.increment === undefined ? 1 : payload.increment;
    if (!payload || !Number.isSafeInteger(increment) || increment < 1 || increment > 10) {
      return response({ error: 'invalid_increment' }, 400);
    }
    if (!Number.isSafeInteger(current.count + increment)) return response({ error: 'counter_limit' }, 409);
    current.count += increment;
    await write(file, current);
  } else if (event.httpMethod !== 'GET') return response({ error: 'method_not_allowed' }, 405);
  return response(current);
};

exports.cache = async (event) => {
  const file = resourceFile(event, process.env.QUALIFICATION_CACHE_DIR, 'cache');
  if (!file) return response({ error: 'invalid_resource_key' }, 400);
  if (event.httpMethod === 'DELETE') {
    await fs.rm(file, { force: true });
    return response({ invalidated: true });
  }
  if (event.httpMethod !== 'GET') return response({ error: 'method_not_allowed' }, 405);
  let value = await read(file, null);
  const hit = value !== null;
  if (!value) { value = { generation: randomUUID(), value: 'reconstructible' }; await write(file, value); }
  return response({ ...value, hit });
};

exports.worker = async (event, context) => {
  const file = resourceFile(event, process.env.QUALIFICATION_DATA_DIR, 'job');
  if (!file) return response({ error: 'invalid_resource_key' }, 400);
  if (event.httpMethod === 'DELETE') {
    await fs.rm(file, { force: true });
    return response({ deleted: true });
  }
  let state = await read(file, null);
  if (event.httpMethod === 'GET') return state ? response(state) : response({ error: 'job_not_found' }, 404);
  if (event.httpMethod !== 'POST') return response({ error: 'method_not_allowed' }, 405);
  const payload = body(event);
  if (!payload) return response({ error: 'invalid_payload' }, 400);
  if (payload.items !== undefined) {
    if (!Array.isArray(payload.items) || payload.items.length < 1 || payload.items.length > 128 ||
        payload.items.some(item => typeof item !== 'string' || item.length > 128)) {
      return response({ error: 'invalid_items' }, 400);
    }
    const fingerprint = createHash('sha256').update(JSON.stringify(payload.items)).digest('hex');
    if (state && state.fingerprint !== fingerprint) return response({ error: 'job_input_conflict' }, 409);
    if (!state) {
      state = { fingerprint, items: payload.items, next: 0, total: payload.items.length, results: [] };
      // Persist acceptance before spending the remaining invocation budget.
      await write(file, state);
    }
  }
  if (!state) return response({ error: 'items_required' }, 400);
  const before = state.next;
  const startedRemainingMs = context.getRemainingTimeInMillis();
  while (state.next < state.total && context.getRemainingTimeInMillis() > 250) {
    const digest = pbkdf2Sync(state.items[state.next], 'p2enjoy-qualification', 100000, 32, 'sha256').toString('hex');
    state.results.push({ index: state.next, digest });
    state.next += 1;
    await write(file, state);
  }
  return response({ ...state, processed: state.next - before,
    startedRemainingMs, remainingMs: context.getRemainingTimeInMillis(),
    complete: state.next === state.total });
};

exports.failure = (event) => {
  const kind = body(event)?.kind;
  if (kind === 'invalid-response') return { statusCode: 200, body: { invalid: true } };
  if (kind === 'invalid-status') return { statusCode: 999, body: '' };
  if (kind === 'exit') process.exit(7);
  if (kind === 'reject') return Promise.reject(new Error('synthetic rejection'));
  throw new Error('synthetic failure');
};
exports.sleep = async (event) => {
  const payload = body(event);
  if (!payload) return response({ error: 'invalid_payload' }, 400);
  const milliseconds = payload.milliseconds === undefined ? 10 : payload.milliseconds;
  if (!Number.isInteger(milliseconds) || milliseconds < 0 || milliseconds > 5000) {
    return response({ error: 'invalid_duration' }, 400);
  }
  await wait(milliseconds);
  return response({ sleptMs: milliseconds });
};
exports.spin = () => { while (true) { /* Deliberately non-cooperative fixture, killed by parent. */ } };

exports.relay = async (event, context) => {
  const payload = body(event);
  if (!payload) return response({ error: 'invalid_payload' }, 400);
  const target = payload.target === undefined ? 'echo' : payload.target;
  if (!['echo', 'failure', 'sleep'].includes(target)) return response({ error: 'invalid_peer' }, 400);
  const destination = new URL(`/functions/${target}?from=relay`, process.env.QUALIFICATION_INTERNAL_ORIGIN);
  const result = await fetch(destination, {
    method: 'POST', headers: { 'content-type': 'application/json', 'x-qualification-tag': context.awsRequestId },
    body: JSON.stringify(payload.payload || { message: 'qualification relay' }),
    signal: AbortSignal.timeout(Math.max(1, context.getRemainingTimeInMillis() - 100)),
  });
  return response({ upstreamStatus: result.status, parentRequestId: context.awsRequestId, child: await result.json() }, result.ok ? 200 : result.status);
};
