// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const fs=require('node:fs'),secret=process.env.QUALIFICATION_SYNTHETIC_SECRET;
if (!secret || secret.length<8) throw new Error('Missing actual secret');
const tail=Math.floor(Buffer.byteLength(secret)/2);
fs.writeSync(1,'x'.repeat(65536-Buffer.byteLength(secret)-tail));
fs.writeSync(1,secret);
fs.writeSync(1,'y'.repeat(tail+4096));
exports.handler=()=>({statusCode:200,body:'boundary'});
