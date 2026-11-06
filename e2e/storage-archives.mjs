// @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle
// @verifies docs/BACKLOG.md#sls-050 | docs/PLATFORM.md#stockage
// Explicit operator purge of one campaign-owned function after its normal HTTP deletion.
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

export async function purgeStorageArchive(functionId,namespaceId){
  for(const id of [functionId,namespaceId])assert.match(id,/^[0-9a-f-]{36}$/);
  const {stdout}=await promisify(execFile)('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J',
    'ubuntu@51.158.54.202','root@10.77.0.24','python3','-B',
    '/srv/p2enjoy-serverless/e2e/function-storage-faults.py','archive-cleanup',functionId,namespaceId],
    {timeout:90000,maxBuffer:1024*1024});
  const result=JSON.parse(stdout.trim());assert.equal(result.purged,true);
  return {function_id:functionId,namespace_id:namespaceId,...result};
}
