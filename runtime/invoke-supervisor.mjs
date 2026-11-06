// @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#canal-privé-et-terminaison
import http from 'node:http';
import {fork} from 'node:child_process';
import {readdir,readFile,statfs} from 'node:fs/promises';

const protocolLimit=10*1024*1024,maxLogs=64*1024;
let key;
function fatal(error) {
  const codes={protocol_limit:120,protocol_rejected:121,cleanup_failed:122,storage_mount_missing:123,protocol_timeout:125};
  process.exit(codes[error?.message]??126);
}
function exchange(method,path,value) {
  return new Promise((resolve,reject)=>{
    const body=value===undefined?null:Buffer.from(JSON.stringify(value));
    if (body && body.length>protocolLimit) return reject(new Error('protocol_limit'));
    const req=http.request({socketPath:'/protocol/control.sock',method,path,agent:false,
      headers:{'Content-Type':'application/json',Connection:'close',...(key?{'X-Instance-Key':key}:{}),
        ...(body?{'Content-Length':body.length}:{})}},res=>{
      const chunks=[];let size=0;
      res.on('data',chunk=>{size+=chunk.length;if(size>protocolLimit)res.destroy(new Error('protocol_limit'));else chunks.push(chunk);});
      res.on('error',reject);
      res.on('end',()=>{
        if (res.statusCode===204) return resolve(null);
        if (![200,202].includes(res.statusCode)) return reject(new Error('protocol_rejected'));
        try {resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));} catch(error) {reject(error);}
      });
    });
    req.setTimeout(5000,()=>req.destroy(new Error('protocol_timeout')));
    req.on('error',reject);req.end(body);
  });
}

async function applicationProcesses() {
  const result=[];
  for (const name of await readdir('/proc')) {
    if (!/^[0-9]+$/.test(name)) continue;
    const pid=Number(name);if (pid===1 || pid===process.pid) continue;
    try {
      const status=await readFile(`/proc/${pid}/stat`,'utf8');
      result.push({pid,state:status.slice(status.lastIndexOf(')')+2).split(' ')[0]});
    } catch(error) {if (!['ENOENT','ESRCH'].includes(error.code)) throw error;}
  }
  return result;
}

async function reap() {
  const deadline=process.hrtime.bigint()+2000000000n;
  do {
    const processes=await applicationProcesses();
    if (!processes.length) return;
    for (const {pid,state} of processes) {
      if (state==='Z') continue;
      try {process.kill(pid,'SIGKILL');} catch(error) {if (error.code!=='ESRCH') throw error;}
    }
    await new Promise(resolve=>setTimeout(resolve,10));
  } while (process.hrtime.bigint()<deadline);
  throw new Error('cleanup_failed');
}

async function invoke(job) {
  const deadline=BigInt(job.deadline_ns),logs=[];let size=0,truncated=false,started=false,startReport=Promise.resolve();
  const capture=chunk=>{
    const kept=Math.min(maxLogs-size,chunk.length);
    if (kept>0) {logs.push(chunk.subarray(0,kept));size+=kept;}
    if (kept<chunk.length) truncated=true;
  };
  // Exiting the namespace's init child makes Docker stop the whole container.
  const remaining=Number((deadline-process.hrtime.bigint())/1000000n);
  if (remaining<=0) process.exit(124);
  const timer=setTimeout(()=>process.exit(124),remaining);
  const child=fork(new URL('./invoke-child.mjs',import.meta.url),[],{
    cwd:'/code',env:{},execArgv:[],stdio:['ignore','pipe','pipe','ipc'],serialization:'json'});
  child.stdout.on('data',capture);child.stderr.on('data',capture);
  const closed=new Promise(resolve=>child.once('close',resolve));
  const result=await new Promise(resolve=>{
    let settled=false;
    const finish=value=>{if (!settled) {settled=true;resolve(value);}};
    child.on('message',message=>{
      if (message?.type==='started' && !started) {
        started=true;startReport=exchange('POST','/started',{invocation_id:job.invocation_id});
        startReport.catch(fatal);return;
      }
      if (message?.type==='completed' && message.response) finish({state:'succeeded',response:message.response});
      else if (message?.type==='failed' && typeof message.error==='string') finish({state:'failed',error:message.error});
    });
    child.once('error',()=>finish({state:'failed',error:'child_start_failed'}));
    child.once('close',()=>finish({state:'failed',error:'handler_exited'}));
    child.send({handler:job.handler,environment:job.environment,event:job.event,
      context:job.context,deadline_ns:job.deadline_ns},error=>{if(error)finish({state:'failed',error:'child_start_failed'});});
  });
  await reap();await closed;await startReport;clearTimeout(timer);
  return {invocation_id:job.invocation_id,...result,handler_started:started,
    logs:Buffer.concat(logs).toString('base64'),logs_truncated:truncated};
}

try {
  const bootstrap=await exchange('POST','/bootstrap',{monotonic_ns:process.hrtime.bigint().toString()});
  key=bootstrap.key;
  for (const mount of bootstrap.mounts) {
    const info=await statfs(mount,{bigint:true});
    if (info.type!==0x65735546n) throw new Error('storage_mount_missing');
  }
  await reap();
  while (true) {
    const job=await exchange('GET','/next');
    if (job) await exchange('POST','/result',await invoke(job));
  }
} catch(error) {fatal(error);}
