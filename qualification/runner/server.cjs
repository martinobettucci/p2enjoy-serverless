// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const http = require('node:http');
const path = require('node:path');
const { loadManifest, root } = require('./manifest.cjs');
const { createInvoker, errorResult } = require('./invoke.cjs');

function createReferenceServer() {
  const manifest = loadManifest();
  let pending = 0;
  let server;
  const invoker = createInvoker({
    manifest,
    dataRoot: path.join(root, '.state/data'),
    cacheRoot: path.join(root, '.state/cache'),
    environment: process.env,
    origin: () => `http://127.0.0.1:${server.address().port}`,
    onEvent: record => process.stdout.write(`${JSON.stringify(record)}\n`),
  });
  const send = (res, result) => {
    if (res.destroyed || res.writableEnded) return;
    res.writeHead(result.statusCode, result.headers);
    res.end(result.isBase64Encoded ? Buffer.from(result.body, 'base64') : result.body);
  };
  const json = (res, value) => send(res, { statusCode: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify(value) });
  server = http.createServer({ connectionsCheckingInterval: 250 }, async (req, res) => {
    let admitted = false;
    try {
      const url = new URL(req.url, 'http://reference.invalid');
      if (url.pathname === '/healthz' && req.method === 'GET') {
        return json(res, { status: 'ok', kind: 'qualification-reference-runner', activeInvocations: invoker.activeCount(), pendingRequests: pending });
      }
      if (url.pathname === '/catalog' && req.method === 'GET') {
        return json(res, { service: manifest.service, runtime: manifest.provider.runtime,
          platformImplemented: false, perFunctionMemoryEnforced: false,
          functions: Object.entries(manifest.functions).map(([name, fn]) => ({
            name, functionId: fn.functionId, handler: fn.handler, timeoutSeconds: fn.timeout,
            declaredMemoryMiB: fn.memorySize, storage: fn.p2enjoy?.storage || null,
          })) });
      }
      const name = /^\/functions\/([a-z][a-z0-9-]*)$/.exec(url.pathname)?.[1];
      if (!name || !Object.hasOwn(manifest.functions, name)) return send(res, errorResult('function_not_found', 404));
      const method = manifest.functions[name].events[0].http.method;
      if (method !== 'any' && method.toUpperCase() !== req.method) return send(res, errorResult('method_not_allowed', 405));
      if (pending >= 16) return send(res, errorResult('reference_runner_busy', 429));
      pending += 1;
      admitted = true;
      const chunks = [];
      let size = 0;
      for await (const chunk of req.iterator({ destroyOnReturn: false })) {
        size += chunk.length;
        if (size > 262144) { send(res, errorResult('payload_too_large', 413)); req.resume(); return; }
        chunks.push(chunk);
      }
      const content = Buffer.concat(chunks);
      const binary = (req.headers['content-type'] || '').split(';')[0] === 'application/octet-stream';
      const event = {
        httpMethod: req.method, path: url.pathname, headers: req.headers,
        queryStringParameters: Object.fromEntries(url.searchParams),
        multiValueQueryStringParameters: Object.fromEntries([...new Set(url.searchParams.keys())].map(key => [key, url.searchParams.getAll(key)])),
        body: content.toString(binary ? 'base64' : 'utf8'), isBase64Encoded: binary,
        requestContext: { stage: 'dev', identity: { sourceIp: req.socket.remoteAddress } },
      };
      send(res, await invoker.invoke(name, event));
    } catch { send(res, errorResult('reference_runner_error')); }
    finally { if (admitted) pending -= 1; }
  });
  server.requestTimeout = 10000;
  server.headersTimeout = 5000;
  server.maxRequestsPerSocket = 100;
  return {
    server,
    async listen(port = 8080, host = '127.0.0.1') {
      await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, host, resolve); });
      return `http://127.0.0.1:${server.address().port}`;
    },
    async close() {
      const stopped = new Promise(resolve => server.close(resolve));
      await invoker.close();
      server.closeAllConnections();
      await stopped;
    },
  };
}
if (require.main === module) {
  // Container-only entry point; Compose publishes this on host loopback exclusively.
  const app = createReferenceServer();
  app.listen(8080, '0.0.0.0').then(() => console.log(JSON.stringify({ status: 'ready', mode: 'dev', port: 8080 })));
  let stopping = false;
  for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, async () => {
    if (stopping) return;
    stopping = true;
    await app.close();
  });
}
module.exports = { createReferenceServer };
