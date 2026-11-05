// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
import {spawn} from 'node:child_process';
import {access} from 'node:fs/promises';
const script=`const net=require('node:net'),fs=require('node:fs');
const s=net.connect('/protocol/control.sock',()=>{s.write('GET /status HTTP/1.1\\r\\n');fs.writeFileSync('/tmp/partial-ready','yes');});
s.on('error',()=>{});setInterval(()=>{},1000);`;
spawn(process.execPath,['-e',script],{detached:true,stdio:'ignore'}).unref();
let ready=false;
for(let attempt=0;attempt<100;attempt++) {
  try {await access('/tmp/partial-ready');ready=true;break;} catch {}
  await new Promise(resolve=>setTimeout(resolve,10));
}
if(!ready)throw new Error('Descendant did not connect');
export const handler=()=>({statusCode:200,body:'partial connection held'});
