// @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#interface-et-preuves
const yaml = require('yaml');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {createHash} = require('node:crypto');
const settings = yaml.parse(readFileSync(join(__dirname, 'réglages.yml'), 'utf8'));
const binary = readFileSync(join(__dirname, 'payload.bin'));
exports.handler = async () => ({statusCode:200, headers:{'content-type':'application/json'}, body:JSON.stringify({
  format:'commonjs', message:settings.message,
  binary_sha256:createHash('sha256').update(binary).digest('hex'), label:process.env.EDITOR_LABEL
})});
