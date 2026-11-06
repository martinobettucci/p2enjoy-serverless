// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
await new Promise(resolve=>setTimeout(resolve,4000));
export const handler=async event=>({statusCode:200,body:JSON.stringify(event)});
