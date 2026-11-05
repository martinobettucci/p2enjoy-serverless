// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const key=['han','dler'].join('');
module.exports[key]=async event=>({statusCode:200,body:JSON.stringify(event)});
