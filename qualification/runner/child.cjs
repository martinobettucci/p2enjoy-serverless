// @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
'use strict';
process.once('message', ({ handler, event, deadline, requestId, functionName }) => {
  let completed = false;
  const finish = (error, result) => {
    if (completed) return;
    completed = true;
    const message = error ? { error: 'handler_error' } : { result };
    process.send(message, () => process.exit(0));
  };
  try {
    const fn = require('../src/handlers.cjs')[handler.split('.').at(-1)];
    if (typeof fn !== 'function') throw new Error('Unknown fixture handler');
    const context = { awsRequestId: requestId, functionName,
      getRemainingTimeInMillis: () => Math.max(0, deadline - Date.now()) };
    process.send({ type: 'handler-started' }, () => { try {
    const returned = fn(event, context, finish);
    if (returned && typeof returned.then === 'function') returned.then(value => finish(null, value), finish);
    else if (returned !== undefined) finish(null, returned);
    } catch (error) { finish(error); } });
  } catch (error) { finish(error); }
});
