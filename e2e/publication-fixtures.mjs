// @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
import {mkdir,cp,writeFile,readFile} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));

export async function publicationArchive(work,name,handler='publication.handler') {
  const project=path.join(work,name);await mkdir(project);
  for(const file of ['publication.cjs','deployment-delay.mjs','log-secret-then-throw.cjs'])
    await cp(path.join(root,'qualification/artifacts',file),path.join(project,file));
  await writeFile(path.join(project,'revision.json'),JSON.stringify({revision:name}));
  const config=path.join(project,'serverless.yml');
  await writeFile(config,JSON.stringify({service:'publications',provider:{name:'p2enjoy',runtime:'nodejs24.x'},
    functions:{probe:{handler}},package:{patterns:['!**','*.cjs','*.mjs','revision.json']}}));
  await promisify(execFile)('python3',['-B','-m','adapter','package','--config',config],{cwd:root});
  const descriptor=JSON.parse(await readFile(path.join(project,'.serverless-p2/deployment.json'),'utf8'));
  const file=path.join(project,'.serverless-p2',descriptor.artifacts.probe.file),bytes=await readFile(file);
  return {file,bytes,sha256:createHash('sha256').update(bytes).digest('hex'),handler};
}
