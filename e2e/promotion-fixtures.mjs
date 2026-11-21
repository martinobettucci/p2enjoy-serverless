// @spec docs/BACKLOG.md#sls-109 | docs/MODERN_CLIENT_PROMOTION_REGRESSIONS.md#décisions-détaillées-du-21-novembre-2026-avant-code
// @verifies docs/BACKLOG.md#sls-109 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
import assert from 'node:assert/strict';

// Explicit API setup only. Upload helpers never call this on their own.
export async function promotePublishedFunction(call,functionId,published,evidence){
  assert.equal(published.state,'published');assert.equal(published.function_id,functionId);
  assert.match(published.code_hash,/^[0-9a-f]{64}$/);
  const versions=await call(`/api/functions/${functionId}/versions?limit=100`);
  const version=versions.items.find(row=>row.code_hash===published.code_hash);
  assert(version);assert.equal(version.state,'available');assert.equal(version.revision_id,published.revision_id);
  assert.equal(versions.active_code_hash,published.default_code_hash_at_publication);
  const before=await call(`/api/functions/${functionId}`);
  const result=await call(`/api/functions/${functionId}/versions/${published.code_hash}/promote`,{
    method:'POST',headers:{'If-Match':String(before.updated_at)},
  });
  const after=await call(`/api/functions/${functionId}`),selected=await call(`/api/functions/${functionId}/versions?limit=100`);
  evidence.push({scenario:'explicit-default-promotion',function_id:functionId,
    candidate_id:published.id??published.deployment_id,revision_id:published.revision_id,code_hash:published.code_hash,
    default_before:versions.active_code_hash,active_revision_before:before.active_revision_id,
    etag_used:before.updated_at,result,active_revision_after:after.active_revision_id,default_after:selected.active_code_hash});
  assert.equal(result.function_id,functionId);assert.equal(result.code_hash,published.code_hash);
  assert.equal(result.revision_id,published.revision_id);assert.equal(result.default_code_hash,published.code_hash);
  assert.equal(after.active_revision_id,published.revision_id);assert.equal(selected.active_code_hash,published.code_hash);
  assert.equal(after.updated_at,result.function_version);assert(after.first_promoted_at);
  return result;
}
