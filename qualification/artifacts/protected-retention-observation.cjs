// @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#parcours-réel
// Actual HTTP and cron handlers meet at a real bounded wall-clock rendezvous.
exports.handler=async(event,context)=>{
 const body=JSON.parse(event.body),trigger=event.headers?.['x-p2enjoy-trigger'];
 const slot=event.headers?.['x-p2enjoy-schedule-slot'];
 const target=trigger==='schedule'?Date.parse(slot)+3000:body.hold_until;
 if(target!==undefined){
  const delay=target-Date.now();
  if(!Number.isFinite(delay)||delay<0||delay>10000)throw new Error('rendezvous_outside_real_window');
  await new Promise(resolve=>setTimeout(resolve,delay));
 }
 const result={marker:'protected-retention-observation',request_id:context.awsRequestId,
  sequence:body.sequence??null,trigger:trigger??'http',slot:slot??null};
 console.log(JSON.stringify(result));
 return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(result)};
};
