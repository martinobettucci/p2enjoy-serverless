// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues
// Original real-runtime witness; only fixed trigger metadata is logged.
exports.handler = async (event, context) => {
  const observation = {marker:'scheduled-original-A',request_id:context.awsRequestId,
    method:event.httpMethod,path:event.path,body:JSON.parse(event.body),
    trigger:event.headers?.['x-p2enjoy-trigger'],slot:event.headers?.['x-p2enjoy-schedule-slot'],
    authorization_present:Boolean(event.headers?.authorization),platform_token_present:Boolean(event.headers?.['x-serverless-token'])};
  console.log(JSON.stringify(observation));
  return {statusCode:200,body:JSON.stringify(observation)};
};
