// @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#réalisation-et-preuves
import YAML from 'yaml';
await new Promise(resolve=>setTimeout(resolve,20));
export async function handler(event,context) {
  return {statusCode:200,body:JSON.stringify({parsed:YAML.parse(event.body),remaining:context.getRemainingTimeInMillis()})};
}
