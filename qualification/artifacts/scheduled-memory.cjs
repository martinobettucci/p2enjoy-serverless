// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_MEMORY_VERSION.md#campagne-réelle
// Original real handler retains its allocation long enough for Docker inspection.
exports.allocation=async(event,context)=>{
  const value={usage:'memory-allocation',id:context.awsRequestId,started_at_ms:Date.now(),
    memory_mib:Number(context.memoryLimitInMB),method:event.httpMethod,path:event.path,
    body:JSON.parse(event.body||'{}'),trigger:event.headers?.['x-p2enjoy-trigger']??'http',
    slot:event.headers?.['x-p2enjoy-schedule-slot']??null,authorization_present:Boolean(event.headers?.authorization)};
  console.log(JSON.stringify({event:'started',...value}));await new Promise(resolve=>setTimeout(resolve,20000));
  const result={...value,completed_at_ms:Date.now()};console.log(JSON.stringify({event:'completed',...result}));
  return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(result)};
};
