// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#api-droits-et-snapshots | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
// Validate the data used by the journal before rendering or acknowledging a write.
const object=value=>value!==null && typeof value==='object' && !Array.isArray(value);
const finite=value=>typeof value==='number' && Number.isFinite(value);
const integer=value=>Number.isSafeInteger(value) && value>=0;

export function incompleteJournalResponse() {
  const error=new Error('La réponse du serveur est incomplète ou invalide. Relisez le résultat avant toute nouvelle écriture.');
  error.responseInvalid=true;return error;
}

export function journalResponse(value) {
  if(!object(value) || !Array.isArray(value.items) || !integer(value.total) || !integer(value.limit) ||
     value.items.length>value.limit || !['history','follow'].includes(value.mode) || typeof value.snapshot!=='string' ||
     typeof value.follow_cursor!=='string' || typeof value.partial!=='boolean' || !object(value.period) ||
     !finite(value.period.from) || !finite(value.period.to) || !object(value.collection) ||
     !finite(value.collection.started_at) || !finite(value.collection.available_from) ||
     !integer(value.collection.prune_generation) || !integer(value.collection.retention_minutes) ||
     !value.items.every(item=>object(item) && typeof item.id==='string' && typeof item.message==='string' &&
       finite(item.observed_at) && object(item.metadata)))throw incompleteJournalResponse();
  return value;
}

export function retentionResponse(value,serviceId) {
  if(!object(value) || value.service_id!==serviceId || !Number.isSafeInteger(value.version) || value.version<1 ||
     !Number.isSafeInteger(value.retention_minutes) || value.retention_minutes<1 || value.retention_minutes>10080 ||
     !finite(value.effective_floor) || (value.updated_at!==null && !finite(value.updated_at)))throw incompleteJournalResponse();
  return value;
}
