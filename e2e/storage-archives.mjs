// @spec docs/BACKLOG.md#sls-106 | docs/REGRESSION_ARTIFACT_CLEANUP.md#diagnostic-recoupé-et-décision-avant-code
// @verifies docs/BACKLOG.md#sls-106 | docs/REGRESSION_ARTIFACT_CLEANUP.md#correction-bornée
// @spec docs/BACKLOG.md#sls-050 | docs/CONSOLE_STORAGE.md#api-et-représentations
// Public purge of one campaign-owned function, followed by a real read-only DEV inspection.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {readFile,open,rename,mkdir} from 'node:fs/promises';
import {constants} from 'node:fs';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {request} from 'playwright';

const base='https://serverless.lelabs.tech',output=new URL('../.local/e2e/',import.meta.url),run=promisify(execFile);
const canonical=value=>typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
export async function purgeStorageArchive(functionId,namespaceId){
  assert(canonical(functionId)&&canonical(namespaceId));
  const client=await request.newContext({baseURL:base,storageState:JSON.parse(await readFile(new URL('purge-admin-session.json',output),'utf8')),timeout:30000});
  let session,operation,receiptPath,record;
  async function persist(){
    if(!receiptPath)return;
    const pending=new URL(receiptPath.pathname+'.pending','file:'),stream=await open(pending,'w',0o600);
    try{await stream.writeFile(JSON.stringify(record,null,2)+'\n');await stream.sync();}finally{await stream.close();}
    await rename(pending,receiptPath);
    const directory=await open(output,constants.O_RDONLY|constants.O_DIRECTORY);
    try{await directory.sync();}finally{await directory.close();}
  }
  async function api(path,{method='GET',body,headers={}}={}){
    const response=await client.fetch(path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token,...headers}});
    assert([200,202].includes(response.status()),method+' '+path+': '+response.status());return response.json();
  }
  try{
    session=await api('/api/session');assert(session.authenticated,'real_purge_session_required');
    function owned(value){
      assert.equal(value.id,functionId);assert.equal(value.namespace_id,namespaceId);
      assert(/^(?:qa-[0-9a-f]{8}|ui-[0-9a-f]{8}x{52}|invocation-[0-9a-f]{8}|publication-ui-[0-9a-f]{8})$/.test(value.namespace_name),'owned_campaign_required');
      assert(value.deleted_at);return value;
    }
    let archive=owned(await api('/api/archives/'+functionId));
    const guardDeadline=Date.now()+120000;
    while(archive.storage_operation&&archive.storage_operation.kind!=='purge'){
      assert(Date.now()<guardDeadline,'archive_operation_not_settled');
      await new Promise(resolve=>setTimeout(resolve,300));archive=owned(await api('/api/archives/'+functionId));
    }
    if(archive.purged_at){assert.equal(archive.command?.kind,'purge');assert.equal(archive.command.state,'completed');operation=archive.command.id;}
    else if(archive.storage_operation){assert.equal(archive.storage_operation.kind,'purge');operation=archive.storage_operation.id;}
    else operation=randomUUID();
    assert(canonical(operation));
    await mkdir(output,{recursive:true,mode:0o700});receiptPath=new URL('archive-purge-'+operation+'.json',output);
    // Retain a preceding observation instead of replacing its provenance on an idempotent call.
    try{const prior=JSON.parse(await readFile(receiptPath,'utf8'));assert.equal(prior.function_id,functionId);assert.equal(prior.namespace_id,namespaceId);receiptPath=new URL('archive-purge-'+operation+'-observation-'+randomUUID()+'.json',output);}catch(error){if(error.code!=='ENOENT')throw error;}
    record={completed:false,function_id:functionId,namespace_id:namespaceId,operation_id:operation,before_artifact_bytes:archive.artifact_bytes};await persist();
    if(!archive.purged_at&&!archive.storage_operation){
      record.post_attempted=true;await persist();
      const posted=await api('/api/archives/'+functionId+'/purge',{method:'POST',body:{operation_id:operation,confirm_name:archive.name},headers:{'If-Match':String(archive.updated_at)}});
      assert.equal(posted.id,operation);record.posted=posted;await persist();
    }
    const deadline=Date.now()+120000;
    while(true){const value=await api('/api/storage-operations/'+operation);assert.equal(value.function_id,functionId);assert.equal(value.kind,'purge');record.command=value;await persist();assert.notEqual(value.state,'aborted');if(value.state==='completed')break;assert(Date.now()<deadline,'public_purge_not_completed');await new Promise(resolve=>setTimeout(resolve,300));}
    archive=owned(await api('/api/archives/'+functionId));assert(archive.purged_at);assert.equal(archive.artifact_bytes,0);assert.equal(archive.revision_count,0);assert.equal(archive.storage_operation,null);
    const {stdout}=await run('ssh',['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/archive-purge-inspect.py',functionId,namespaceId,operation],{timeout:90000,maxBuffer:1024*1024});
    const physical=JSON.parse(stdout);assert(physical.completed&&physical.control_purged&&Object.values(physical.physical).every(Boolean));
    record.completed=true;record.physical=physical;await persist();
    return {function_id:functionId,namespace_id:namespaceId,operation_id:operation,purged:true,artifact_bytes:0,physical,
      receipt:{path:receiptPath.pathname,sha256:createHash('sha256').update(await readFile(receiptPath)).digest('hex')}};
  }catch(error){if(record){record.error={type:error.name};await persist();}throw error;}
  finally{await client.dispose();}
}
