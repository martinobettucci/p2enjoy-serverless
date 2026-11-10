// @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#preuves-e2e-attendues
// Original handlers retain their admitted code while the promoted hash changes.
async function observe(marker, event, context) {
  const started = Date.now();
  await new Promise(resolve => setTimeout(resolve, 20000));
  const observation = {marker, request_id:context.awsRequestId, started_at_ms:started,
    completed_at_ms:Date.now(), method:event.httpMethod, path:event.path,
    body:JSON.parse(event.body), trigger:event.headers?.['x-p2enjoy-trigger'],
    slot:event.headers?.['x-p2enjoy-schedule-slot']};
  console.log(JSON.stringify(observation));
  return {statusCode:200, body:JSON.stringify(observation)};
}
exports.primary = (event, context) => observe('scheduled-version-A', event, context);
exports.secondary = (event, context) => observe('scheduled-version-B', event, context);
