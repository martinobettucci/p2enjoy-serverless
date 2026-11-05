// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
export function then(resolve) {resolve({handler:()=>({statusCode:200,body:'not a module namespace'})});}
export const handler=()=>({statusCode:200,body:'module'});
