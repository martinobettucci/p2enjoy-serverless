// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
// @verifies docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
// Docker service DNS is invariant. This client never starts or imports application code.
const origin = 'http://qualification:8080';
async function request(route, { method = 'GET', value, raw, headers = {} } = {}) {
  const result = await fetch(`${origin}${route}`, { method, headers,
    body: raw === undefined ? (value === undefined ? undefined : JSON.stringify(value)) : raw,
    signal: AbortSignal.timeout(10000) });
  const bytes = Buffer.from(await result.arrayBuffer());
  const contentType = result.headers.get('content-type') || '';
  return { status: result.status, headers: result.headers, bytes,
    body: bytes.length && contentType.includes('application/json') ? JSON.parse(bytes.toString()) : null };
}
const call = (name, options) => request(`/functions/${name}`, options);
module.exports = { request, call };
