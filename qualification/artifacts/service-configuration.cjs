// @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuves-et-manuel
// Original handler used through the public gateway, without returning secret values.
const {createHash}=require('node:crypto');
exports.handler=async event=>{
  const label=process.env.SHARED_LABEL??null,local=process.env.LOCAL_LABEL??null;
  const secret=process.env.SHARED_SECRET;
  const secret_sha256=secret===undefined?null:createHash('sha256').update(secret).digest('hex');
  const delay=Number(event.queryStringParameters?.delay??0);
  if(delay>0&&delay<=5000)await new Promise(resolve=>setTimeout(resolve,delay));
  return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify({label,local,secret_sha256})};
};
