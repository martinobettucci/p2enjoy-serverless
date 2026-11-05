// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
await new Promise(resolve=>setTimeout(resolve,25));
export const handler=async event=>({statusCode:200,body:JSON.stringify(event)});
export default handler;
