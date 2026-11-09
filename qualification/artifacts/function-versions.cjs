// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
const fs = require('node:fs');
const {createHash} = require('node:crypto');
const marker = require('./version-marker.json');
if (marker.validation_delay_ms) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,Math.min(12000,marker.validation_delay_ms));

function append(directory,record) {
  const file=directory+'/version-invocations.ndjson';
  fs.appendFileSync(file,JSON.stringify(record)+'\n');
  const fd=fs.openSync(file,'r');try {fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
  return fs.readFileSync(file,'utf8').trim().split('\n').length;
}

async function execute(exportName,event) {
  const record={marker:marker.value,handler:exportName,id:event.requestContext.requestId};
  console.log(JSON.stringify({event:'version.started',...record}));
  const persistent=process.env.VERSIONS_PERSIST==='yes';
  const counter=persistent ? append('/data',record) : null;
  const cacheCounter=persistent ? append('/cache',record) : null;
  const delay=Number(event.queryStringParameters?.delay_ms || 0);
  if (Number.isFinite(delay) && delay>0) await new Promise(resolve=>setTimeout(resolve,Math.min(8000,delay)));
  return {statusCode:200,headers:{'Content-Type':'application/json','X-Serverless-Code-Hash':'handler-supplied-value'},
    body:JSON.stringify({...record,counter,cacheCounter,common:process.env.VERSIONS_COMMON,local:process.env.VERSIONS_LOCAL,
      secret_sha256:createHash('sha256').update(process.env.VERSIONS_SECRET || '').digest('hex'),
      authorization_present:Boolean(event.headers?.authorization),path:event.path})};
}
exports.primary=event=>execute('primary',event);
exports.secondary=event=>execute('secondary',event);
