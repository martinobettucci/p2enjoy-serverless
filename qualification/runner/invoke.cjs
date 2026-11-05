// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
const { fork } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const path = require('node:path');
const fs = require('node:fs/promises');

function errorResult(error, statusCode = 500) {
  return { statusCode, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ error, layer: 'reference-runner' }) };
}
function createInvoker({ manifest, dataRoot, cacheRoot, environment = {}, origin = () => '', onEvent = () => {} }) {
  const queues = new Map();
  const active = new Set();
  let closing = false;
  async function execute(name, event) {
    if (closing) return errorResult('runner_stopping', 503);
    const fn = manifest.functions[name];
    const env = {};
    for (const key of fn.environmentKeys) if (environment[key] !== undefined) env[key] = environment[key];
    if (fn.p2enjoy?.storage) {
      const directory = path.join(fn.p2enjoy.storage === 'data' ? dataRoot : cacheRoot, fn.functionId);
      await fs.mkdir(directory, { recursive: true });
      env[fn.p2enjoy.storage === 'data' ? 'QUALIFICATION_DATA_DIR' : 'QUALIFICATION_CACHE_DIR'] = directory;
    }
    if (name === 'relay') env.QUALIFICATION_INTERNAL_ORIGIN = origin();
    if (closing) return errorResult('runner_stopping', 503);
    const requestId = randomUUID();
    const started = Date.now();
    const deadline = started + fn.timeout * 1000;
    return new Promise((resolve) => {
      const child = fork(path.join(__dirname, 'child.cjs'), [], { env, stdio: ['ignore', 'ignore', 'ignore', 'ipc'] });
      active.add(child);
      let outcome;
      let finished = false;
      let handlerStarted = false;
      const timer = setTimeout(() => {
        if (!outcome) { outcome = errorResult('invocation_timeout', 504); child.kill('SIGKILL'); }
      }, Math.max(1, deadline - Date.now()));
      const finish = () => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        active.delete(child);
        const result = outcome || errorResult('handler_exit');
        onEvent({ function: name, requestId, statusCode: result.statusCode, handlerStarted, durationMs: Date.now() - started });
        resolve({ ...result, headers: { ...result.headers, 'x-qualification-request-id': requestId,
          'x-qualification-handler-started': String(handlerStarted) } });
      };
      child.on('message', (message) => {
        if (message.type === 'handler-started') { handlerStarted = true; return; }
        if (outcome) return;
        const value = message.result;
        outcome = message.error ? errorResult(message.error) :
          value && Number.isInteger(value.statusCode) && value.statusCode >= 200 && value.statusCode <= 599 && typeof value.body === 'string'
            ? value : errorResult('invalid_handler_response');
        // Reap the invocation even if callbacks leave timers or work behind.
        child.kill('SIGKILL');
      });
      child.once('error', () => { outcome = errorResult('spawn_error'); finish(); });
      child.once('close', finish);
      child.send({ handler: fn.handler, event, deadline, requestId, functionName: name }, error => {
        if (error && !outcome) { outcome = errorResult('dispatch_error'); child.kill('SIGKILL'); }
      });
    });
  }
  return {
    invoke(name, event) {
      if (!Object.hasOwn(manifest.functions, name)) return Promise.resolve(errorResult('function_not_found', 404));
      if (closing) return Promise.resolve(errorResult('runner_stopping', 503));
      // Serial per function, independent queues allow relay -> echo without deadlock.
      const previous = queues.get(name) || Promise.resolve();
      const next = previous.catch(() => {}).then(() => execute(name, event));
      queues.set(name, next);
      next.finally(() => { if (queues.get(name) === next) queues.delete(name); }).catch(() => {});
      return next;
    },
    activeCount: () => active.size,
    async close() {
      closing = true;
      for (const child of active) child.kill('SIGKILL');
      await Promise.allSettled([...queues.values()]);
    },
  };
}
module.exports = { createInvoker, errorResult };
