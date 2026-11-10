// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_ADMISSION.md#campagne-et-discriminants
// Original Docker handlers: real waiting, durable writes and deadline observation.
const fs = require('node:fs');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function metadata(event,context,usage) {
  return {usage,id:context.awsRequestId,method:event.httpMethod,path:event.path,
    trigger:event.headers?.['x-p2enjoy-trigger']??'http',slot:event.headers?.['x-p2enjoy-schedule-slot']??null,
    authorization_present:Boolean(event.headers?.authorization),body:JSON.parse(event.body||'{}')};
}
function complete(value) {
  const result={...value,completed_at_ms:Date.now()};console.log(JSON.stringify({event:'completed',...result}));
  return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(result)};
}
exports.longRunning=async(event,context)=>{
  const value={...metadata(event,context,'overlap'),started_at_ms:Date.now()};
  console.log(JSON.stringify({event:'started',...value}));await sleep(315000);return complete(value);
};
exports.capacity=async(event,context)=>complete({...metadata(event,context,'capacity'),started_at_ms:Date.now()});
exports.exclusive=async(event,context)=>{
  const value={...metadata(event,context,'exclusive'),started_at_ms:Date.now()},file='/data/schedule-records.ndjson';
  if(!value.body.read_only){fs.appendFileSync(file,JSON.stringify({id:value.id,trigger:value.trigger})+'\n');const fd=fs.openSync(file,'r');try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
  value.counter=fs.existsSync(file)?fs.readFileSync(file,'utf8').trim().split('\n').length:0;
  console.log(JSON.stringify({event:'started',...value}));
  if(value.body.release_at_ms)await sleep(Math.max(0,Math.min(40000,value.body.release_at_ms-Date.now())));
  return complete(value);
};
exports.deadline=async(event,context)=>{
  const value={...metadata(event,context,'deadline'),started_at_ms:Date.now()};console.log(JSON.stringify({event:'started',...value}));
  if(value.trigger==='schedule')await sleep(5000);return complete(value);
};
