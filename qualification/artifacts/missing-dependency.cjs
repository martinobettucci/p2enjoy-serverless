// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
require('./dependency-that-does-not-exist.cjs');
exports.handler=async()=>({statusCode:200,body:'unreachable'});
