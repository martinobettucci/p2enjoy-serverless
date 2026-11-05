// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const fs=require('node:fs'),secret=process.env.QUALIFICATION_SYNTHETIC_SECRET;
if (!secret) throw new Error('Missing actual secret');
fs.writeSync(1,secret.slice(0,3));fs.writeSync(1,secret.slice(3));fs.writeSync(1,'\n');
fs.writeSync(1,'x'.repeat(65536-secret.length-4));
fs.writeSync(1,secret);
fs.writeSync(1,'y'.repeat(200000));
exports.handler=()=>({statusCode:200,body:'logs'});
