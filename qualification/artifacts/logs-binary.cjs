// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
require('node:fs').writeSync(1,Buffer.alloc(40000,255));
exports.handler=()=>({statusCode:200,body:'binary logs'});
