// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_UNAVAILABLE.md#refus-et-reprise
// Original handler: durable records and public execution metadata only.
const fs=require('node:fs');
function read(file){try{return fs.readFileSync(file,'utf8');}catch(error){if(error.code==='ENOENT')return null;throw error;}}
function write(file,value){fs.writeFileSync(file,value);const fd=fs.openSync(file,'r');try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
exports.handler=async(event,context)=>{
 const input=JSON.parse(event.body||'{}');
 if(event.httpMethod==='POST'){if(typeof input.data==='string')write('/data/record',input.data);if(typeof input.cache==='string')write('/cache/record',input.cache);}
 const result={id:context.awsRequestId,method:event.httpMethod,path:event.path,body:input,trigger:event.headers?.['x-p2enjoy-trigger']??'http',slot:event.headers?.['x-p2enjoy-schedule-slot']??null,authorization_present:Boolean(event.headers?.authorization),data:read('/data/record'),cache:read('/cache/record')};
 console.log(JSON.stringify({event:'completed',...result}));
 return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(result)};
};
