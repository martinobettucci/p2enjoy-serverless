// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_INSTANCE_REUSE.md#campagne-réelle
// Original handler: bounded real HTTP occupation and public invocation markers.
exports.handler=async(event,context)=>{
 const body=JSON.parse(event.body||'{}');
 const value={id:context.awsRequestId,method:event.httpMethod,path:event.path,body,trigger:event.headers?.['x-p2enjoy-trigger']??'http',slot:event.headers?.['x-p2enjoy-schedule-slot']??null,authorization_present:Boolean(event.headers?.authorization),started_at_ms:Date.now()};
 console.log(JSON.stringify({event:'started',...value}));
 if(value.trigger==='http'&&Number.isFinite(body.release_at_ms))await new Promise(resolve=>setTimeout(resolve,Math.max(0,Math.min(45000,body.release_at_ms-Date.now()))));
 const result={...value,completed_at_ms:Date.now()};console.log(JSON.stringify({event:'completed',...result}));
 return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(result)};
};
