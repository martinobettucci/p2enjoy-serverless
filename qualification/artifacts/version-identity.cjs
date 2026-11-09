// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md#calcul-opérateur-et-preuve-réelle
const dependency = require('./version-dependency.cjs');
exports.first = async () => ({statusCode:200, body:JSON.stringify({handler:'first',dependency:dependency.value})});
exports.second = async () => ({statusCode:200, body:JSON.stringify({handler:'second',dependency:dependency.value})});
