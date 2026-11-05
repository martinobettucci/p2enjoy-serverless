// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
import http from 'node:http';
import {fork} from 'node:child_process';

const maxLogs=64*1024, logs=[];
let logSize=0,truncated=false;
function capture(chunk) {
  const remaining=maxLogs-logSize;
  if (chunk.length>remaining) truncated=true;
  if (remaining>0) {const kept=chunk.subarray(0,remaining);logs.push(kept);logSize+=kept.length;}
}
function request(method,path,value) {
  return new Promise((resolve,reject)=>{
    const body=value===undefined?null:Buffer.from(JSON.stringify(value));
    const req=http.request({socketPath:'/protocol/control.sock',method,path,agent:false,
      headers:{'Content-Type':'application/json',...(body?{'Content-Length':body.length}:{}),Connection:'close'}},res=>{
      const chunks=[];let size=0;
      res.on('data',chunk=>{size+=chunk.length;if(size>256*1024)res.destroy(new Error('Response limit'));else chunks.push(chunk);});
      res.on('error',reject);
      res.on('end',()=>{
        if (res.statusCode!==200 && res.statusCode!==202) return reject(new Error('Protocol rejected'));
        try {resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));} catch(error) {reject(error);}
      });
    });
    req.setTimeout(5000,()=>req.destroy(new Error('Protocol timeout')));
    req.on('error',reject);req.end(body);
  });
}
try {
  const config=await request('GET','/configuration');
  const child=fork(new URL('./validate-child.mjs',import.meta.url),[],{
    cwd:'/code',execArgv:[],env:{},stdio:['ignore','pipe','pipe','ipc'],serialization:'json'});
  child.stdout.on('data',capture);child.stderr.on('data',capture);
  const result=await new Promise(resolve=>{
    let completion;
    child.on('message',message=>{
      if (completion) return;
      if (message?.type==='loaded' && typeof message.module==='string' && message.module.length<=512)
        completion={valid:true,module:message.module};
      else if (message?.type==='failed' && typeof message.code==='string')
        completion={valid:false,error:message.code};
    });
    child.on('error',()=>resolve({valid:false,error:'loader_start_failed'}));
    child.on('close',code=>resolve(completion && (!completion.valid || code===0)?completion:{valid:false,error:'loader_exited'}));
    child.send(config,error=>{if(error)resolve({valid:false,error:'loader_start_failed'});});
  });
  await request('POST','/result',{state:'done',...result,logs:Buffer.concat(logs).toString('base64'),logs_truncated:truncated});
} catch {process.exitCode=1;}
