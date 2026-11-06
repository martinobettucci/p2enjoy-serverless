// @spec docs/BACKLOG.md#sls-061 | docs/CONSOLE_EXECUTION.md#preuves-attendues
// Original application code, packaged and invoked through the public platform.
const fs = require('node:fs');
const delay = Number(process.env.OBSERVATION_IMPORT_DELAY_MS || 0);
if (delay) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,delay);
exports.handler = async event => {
  const input = JSON.parse(event.body || '{}');
  if (input.action === 'delay') await new Promise(resolve => setTimeout(resolve,input.ms));
  if (['logs','many-logs'].includes(input.action)) {
    fs.writeSync(1,'Première ligne\n<script>window.observationInjected=true</script>\n');
    fs.writeSync(1,process.env.OBSERVATION_SECRET+'\n');
    fs.writeSync(2,'Dernière ligne sur stderr\n');
    if (input.action === 'many-logs') fs.writeSync(1,'ligne-sans-espace'.repeat(10000));
  }
  if (input.action === 'error') throw new Error(process.env.OBSERVATION_SECRET);
  return {statusCode:input.status || 200,body:JSON.stringify({ok:true,action:input.action || 'echo'})};
};
