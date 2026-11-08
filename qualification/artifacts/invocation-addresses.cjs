// @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#qualification-réelle-et-autorité
// Original executable fixture: observe the real gateway's path and code revision.
const revision = require('./revision.json');
exports.handler = async event => ({statusCode:200,headers:{'Content-Type':'application/json'},
  body:JSON.stringify({revision:revision.name,path:event.path,method:event.httpMethod})});
