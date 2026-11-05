// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const yaml=require('yaml');
if (yaml.parse('runtime: node24').runtime!=='node24') throw new Error('Dependency did not run');
exports.handler=async()=>({statusCode:200,body:yaml.stringify({valid:true})});
