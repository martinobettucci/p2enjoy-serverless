// @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#réalisation-et-preuves
// Original application handlers deployed and invoked over the real public gateway.
const fs=require('node:fs');
const {createHash}=require('node:crypto');
const runtimeCases=require('./invoke.cjs');
const volumeCases=require('./volume-operations.cjs');
const reply=value=>({statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
exports.handler=async(event,context,done)=>{
  const mode=event.queryStringParameters?.mode??'echo';
  const input=event.body&&!event.isBase64Encoded&&event.headers?.['content-type']?.startsWith('application/json')?JSON.parse(event.body):{};
  if(mode==='runtime')return runtimeCases.handler(input,context,done);
  if(mode==='volume')return volumeCases.handler(input,context,done);
  if(mode==='digest'){
    const bytes=event.isBase64Encoded?Buffer.from(event.body,'base64'):Buffer.from(event.body);
    return reply({bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),encoded:event.isBase64Encoded});
  }
  if(mode==='headers')return {statusCode:202,body:'headers',headers:{'Cache-Control':'private, max-age=17',
    'Content-Security-Policy':"default-src 'none'",'Vary':'Accept-Encoding','X-Request-ID':'forged',
    'X-Serverless-Request-ID':'forged','Access-Control-Allow-Origin':'*',Connection:'X-Transient','X-Transient':'remove'},
    multiValueHeaders:{'Set-Cookie':['business-a=1; Path=/','business-b=2; Path=/'],'X-Multiple':['first','second']}};
  if(mode==='counter'){
    let count=0;try{count=Number(fs.readFileSync('/data/counter','utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
    if(event.httpMethod==='POST'){count++;fs.writeFileSync('/data/counter',String(count));}
    if(input.ms)await new Promise(resolve=>setTimeout(resolve,input.ms));
    return reply({count,label:process.env.PUBLIC_LABEL});
  }
  if(mode==='delay')await new Promise(resolve=>setTimeout(resolve,input.ms??1000));
  return reply({event,context:{awsRequestId:context.awsRequestId,functionName:context.functionName,
    functionVersion:context.functionVersion,memoryLimitInMB:context.memoryLimitInMB,remaining:context.getRemainingTimeInMillis()},
    label:process.env.PUBLIC_LABEL,revision:require('./revision.json').revision});
};
