// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_RETENTION.md#capture-authentique-avant-vieillissement
// Real delayed response makes the handler's running interval observable before tracing.
exports.handler = async (event, context) => {
  const observation = {marker:'scheduled-retention-source',request_id:context.awsRequestId,
    method:event.httpMethod,path:event.path,body:JSON.parse(event.body),
    trigger:event.headers?.['x-p2enjoy-trigger'],slot:event.headers?.['x-p2enjoy-schedule-slot'],
    authorization_present:Boolean(event.headers?.authorization),platform_token_present:Boolean(event.headers?.['x-serverless-token'])};
  await new Promise(resolve => setTimeout(resolve, 2000));
  console.log(JSON.stringify(observation));
  return {statusCode:200,body:JSON.stringify(observation)};
};
