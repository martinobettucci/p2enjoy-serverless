// @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
// Original handler used through the public gateway to prove actual revisions,
// configuration and data persistence without returning the synthetic secret.
const fs=require('node:fs');
const {createHash}=require('node:crypto');
exports.handler=async(event,context)=>{
  let count=null;
  if(event.queryStringParameters?.mode==='counter'){
    try{count=Number(fs.readFileSync('/data/publication-counter','utf8'));}
    catch(error){if(error.code!=='ENOENT')throw error;count=0;}
    if(event.httpMethod==='POST'){count++;fs.writeFileSync('/data/publication-counter',String(count));}
  }
  return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify({
    revision:require('./revision.json').revision,functionVersion:context.functionVersion,
    memory:context.memoryLimitInMB,label:process.env.PUBLIC_LABEL,count,
    secret_sha256:createHash('sha256').update(process.env.QUALIFICATION_SYNTHETIC_SECRET || '').digest('hex'),
  })};
};
