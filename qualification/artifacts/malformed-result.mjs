// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
import http from 'node:http';
const body=JSON.stringify({state:'done',valid:false,error:[]});
await new Promise((resolve,reject)=>{
  const req=http.request({socketPath:'/protocol/control.sock',path:'/result',method:'POST',agent:false,
    headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(body)}},res=>{
    res.resume();reject(new Error('Malformed result accepted'));
  });
  req.setTimeout(1000,()=>req.destroy(new Error('Timeout')));
  req.on('error',error=>error.code==='ECONNRESET'?resolve():reject(error));req.end(body);
});
export const handler=()=>({statusCode:200,body:'invalid result refused'});
