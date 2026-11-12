// @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md#réalisation-et-preuves
// Original executable HTTP fixture; published normally and invoked through the gateway.
const {createHash}=require('node:crypto');
const {gzipSync}=require('node:zlib');
const marker='__PACKAGE_MARKER__';
exports.handler=async(event,context)=>{
 const query=event.queryStringParameters||{},headers=event.headers||{};
 const raw=event.isBase64Encoded?Buffer.from(event.body||'','base64'):Buffer.from(event.body||'','utf8');
 const delay=Math.min(10,Math.max(0,Number(query.delay)||0));
 if(delay)await new Promise(resolve=>setTimeout(resolve,delay*1000));
 console.log(JSON.stringify({marker,requestId:context.awsRequestId,phase:'handler-completed'}));
 if(query.kind==='redirect')return{statusCode:307,headers:{Location:query.target},body:'Destination non suivie'};
 if(query.kind==='binary'){
  const length=Math.min(6*1024**2,Math.max(0,Number(query.size)||4096));
  const bytes=Buffer.alloc(length);for(let n=0;n<bytes.length;n++)bytes[n]=n%256;
  return{statusCode:200,headers:{'Content-Type':'application/octet-stream'},isBase64Encoded:true,body:bytes.toString('base64')};
 }
 if(query.kind==='oversized')return{statusCode:200,headers:{'Content-Type':'application/octet-stream'},isBase64Encoded:true,body:Buffer.alloc(6*1024**2+1,120).toString('base64')};
 if(query.kind==='gzip')return{statusCode:200,headers:{'Content-Type':'text/plain','Content-Encoding':'gzip'},isBase64Encoded:true,body:gzipSync(Buffer.alloc(6*1024**2+1,120)).toString('base64')};
 if(query.kind==='headers')return{statusCode:200,headers:Object.fromEntries([['Content-Type','text/plain'],...Array.from({length:127},(_,n)=>['X-Response-'+n,'value-'+n])]),body:'Headers received'};
 if(query.kind==='html')return{statusCode:200,headers:{'Content-Type':'text/html'},body:'<svg onload="window.__unexpectedExecution=true"><text>Texte échappé</text></svg>'};
 return{statusCode:Number(query.status)||200,headers:{'Content-Type':'application/json','X-Fixture-Marker':marker},body:JSON.stringify({
  marker,requestId:context.awsRequestId,source_ip:event.requestContext.identity.sourceIp,method:event.httpMethod,path:event.path,query:event.multiValueQueryStringParameters,
  body_bytes:raw.length,body_sha256:createHash('sha256').update(raw).digest('hex'),body_base64:raw.length<=8192?raw.toString('base64'):null,
  authorization_sha256:createHash('sha256').update(headers.authorization||'').digest('hex'),
  cookie_present:Boolean(headers.cookie),platform_token_present:Boolean(headers['x-serverless-token']),
  custom:headers['x-http-client-example']||null
 })};
};
