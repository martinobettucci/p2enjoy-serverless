// @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#interface-et-preuves
import yaml from 'yaml';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const settings = yaml.parse(readFileSync(new URL('réglages.yml', import.meta.url), 'utf8'));
const binary = readFileSync(new URL('payload.bin', import.meta.url));
export const handler = async () => ({statusCode:200, headers:{'content-type':'application/json'}, body:JSON.stringify({
  format:'esm', message:settings.message,
  binary_sha256:createHash('sha256').update(binary).digest('hex'), label:process.env.EDITOR_LABEL
})});
