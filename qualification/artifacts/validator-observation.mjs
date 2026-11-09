// @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#plan-séquentiel-avant-code
// @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
// Original executable fixture: real imports, rejection/deadline and stored counts.
import fs from 'node:fs';
import {createHash} from 'node:crypto';

const configuration=JSON.parse(fs.readFileSync(new URL('./validation-mode.json',import.meta.url),'utf8'));
if(!['success','reject','timeout'].includes(configuration.mode))throw new Error('unknown_validation_mode');
fs.writeFileSync('/tmp/validator-name-import.json',JSON.stringify({mode:configuration.mode,pid:process.pid}));
await new Promise(resolve=>setTimeout(resolve,configuration.mode==='timeout'?60000:5000));
if(configuration.mode==='reject')throw new Error('original_validation_rejection');

export async function handler(){
  const next=directory=>{const path=directory+'/validator-name-counter.json';const count=fs.existsSync(path)?JSON.parse(fs.readFileSync(path,'utf8')).count+1:1;fs.writeFileSync(path,JSON.stringify({count}));return count;};
  return {statusCode:200,body:JSON.stringify({mode:configuration.mode,public_value:process.env.VALIDATOR_NAME_PUBLIC,
    secret_sha256:createHash('sha256').update(process.env.VALIDATOR_NAME_SECRET??'').digest('hex'),data_count:next('/data'),cache_count:next('/cache')})};
}
