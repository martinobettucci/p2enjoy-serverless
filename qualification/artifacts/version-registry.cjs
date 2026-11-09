// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
const fs = require('node:fs');
const {createHash} = require('node:crypto');
const marker = require('./version-marker.json');
exports.handler = async () => {
  const file = '/data/version-counter';
  const counter = fs.existsSync(file) ? Number(fs.readFileSync(file,'utf8')) + 1 : 1;
  fs.writeFileSync(file,String(counter));
  const fd=fs.openSync(file,'r');try {fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
  return {statusCode:200,body:JSON.stringify({marker:marker.value,counter,
    common:process.env.REGISTRY_COMMON,local:process.env.REGISTRY_LOCAL,
    secret_sha256:createHash('sha256').update(process.env.REGISTRY_SECRET || '').digest('hex')})};
};
