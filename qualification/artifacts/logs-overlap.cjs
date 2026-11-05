// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const fs=require('node:fs'),secret=process.env.QUALIFICATION_SYNTHETIC_SECRET;
if (!secret || process.env.QUALIFICATION_SECRET_SUFFIX!==secret.at(-2)) throw new Error('Missing overlapping configuration');
fs.writeSync(1,'x'.repeat(65536-Buffer.byteLength(secret)+1));
fs.writeSync(1,secret.slice(0,-1));
fs.writeSync(1,'y'.repeat(4096));
exports.handler=()=>({statusCode:200,body:'overlap'});
