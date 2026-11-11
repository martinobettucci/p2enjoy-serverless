// @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_RETENTION_VOLUME.md#parcours-et-discriminants
// Original handler: observable real execution for each numbered HTTP request.
exports.handler=async(event,context)=>{
 const {sequence}=JSON.parse(event.body);
 const result={marker:'retention-observation',request_id:context.awsRequestId,sequence};
 console.log(JSON.stringify(result));
 return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify(result)};
};
