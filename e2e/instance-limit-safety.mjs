// @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#refus-avant-toute-mutation
// @verifies docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#preuve-ciblée-du-refus
// Original namespace, real SSO session, HTTPS and actual read-only SPARK operator.
import assert from 'node:assert/strict';
import {randomUUID, createHash} from 'node:crypto';
import {mkdir, writeFile, rename, access} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {request} from 'playwright';
const root=new URL('../',import.meta.url),out=new URL('../.local/e2e/',import.meta.url),report=new URL('instance-limit-safety.json',out),base='https://serverless.lelabs.tech';
const checks=[],cleanupErrors=[],observations=[];
let admin,session,namespace,before,after,completed=false,cleanup=false;
const digest=value=>createHash('sha256').update(value).digest('hex');
async function save(){const p=new URL('instance-limit-safety.pending',out);await writeFile(p,JSON.stringify({completed:completed&&cleanup&&!cleanupErrors.length,unit_complete:false,checks,skipped:0,cleanup,cleanup_errors:cleanupErrors,namespace_id:namespace?.id,observations,before,after},null,2)+'\n',{mode:0o600});await rename(p,report);}
async function api(path,{method='GET',body,status=200}={}){const response=await admin.fetch(path,{method,data:body,headers:{Origin:base,'X-CSRF-Token':session?.csrf_token??''}});assert.equal(response.status(),status,method+' '+path);return response.json();}
async function check(name,action){try{await action();checks.push({name,status:'passed'});}catch(error){checks.push({name,status:'failed',failure_type:error.name,message_sha256:digest(String(error.message))});throw error;}finally{await save();}}
function helper(input,inspect=false){const r=spawnSync('python3',['-B','e2e/instance-limit-guard.py',namespace.id,...(inspect?['--inspect']:[])],{cwd:root.pathname,input,encoding:'utf8',timeout:75000,maxBuffer:1024*1024});assert(!r.error);assert.equal(r.signal,null);assert.equal(r.stderr,'');const lines=r.stdout.trim().split('\n');assert.equal(lines.length,1);return {exit_code:r.status,...JSON.parse(lines[0])};}
await mkdir(out,{recursive:true,mode:0o700});let exists=true;try{await access(report);}catch(error){assert.equal(error.code,'ENOENT');exists=false;}assert(!exists,'existing_report_requires_inspection_no_automatic_replay');
try{
 admin=await request.newContext({baseURL:base,storageState:new URL('admin-session.json',out).pathname,timeout:30000});
 await check('Précontrôle réel, namespace original et budgets officiels/consommés',async()=>{session=await api('/api/session');assert(session.authenticated&&session.csrf_token);namespace=await api('/api/namespaces',{method:'POST',body:{name:'invocation-'+randomUUID().slice(0,8)},status:201});const r=helper('',true);assert.equal(r.exit_code,0);assert(r.completed);before=r.inspection;observations.push({scenario:'inspect',result:r});});
 await check('Entrée restore puis EOF refusées sans proposition, recréation ni mutation',async()=>{for(const [name,input] of [['restore','restore\n'],['eof','']]){const r=helper(input);assert.equal(r.exit_code,2);assert.equal(r.event,'instance-limit-blocked');assert.equal(r.code,'active_environment_precondition_unavailable');assert.equal(r.mutation_count,0);assert.equal(r.completed,false);assert.deepEqual(r.inspection,before);observations.push({scenario:name,result:r});}const r=helper('',true);assert.equal(r.exit_code,0);after=r.inspection;assert.deepEqual(after,before);});
 completed=true;
}finally{
 if(namespace){try{await api('/api/namespaces/'+namespace.id,{method:'DELETE'});const response=await admin.get('/api/namespaces/'+namespace.id);assert.equal(response.status(),404);cleanup=true;}catch(error){cleanupErrors.push({failure_type:error.name,message_sha256:digest(String(error.message))});}}
 await save();await admin?.dispose();
}
assert(completed&&cleanup&&!cleanupErrors.length);console.log(JSON.stringify({completed:true,unit_complete:false,groups:checks.length,refusals:observations.filter(v=>v.result.event==='instance-limit-blocked').length,skipped:0,cleanup_errors:0}));
