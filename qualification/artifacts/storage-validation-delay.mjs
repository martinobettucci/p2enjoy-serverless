// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
// @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
import {readFile,writeFile} from 'node:fs/promises';

const revision=JSON.parse(await readFile(new URL('./revision.json',import.meta.url),'utf8')).revision;
await writeFile('/tmp/storage-validation-import.json',JSON.stringify({revision,pid:process.pid}));
await new Promise(resolve=>setTimeout(resolve,60000));
export const handler=async event=>({statusCode:200,body:JSON.stringify(event)});
