-- @spec docs/BACKLOG.md#sls-040 | docs/SCHEMA.md#réservations-et-invocations
CREATE TABLE execution_instances (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL REFERENCES functions(id),
 revision_id TEXT NOT NULL REFERENCES revisions(id), generation TEXT NOT NULL,
 cpu_nanos INTEGER NOT NULL CHECK(cpu_nanos>0), memory_mib INTEGER NOT NULL CHECK(memory_mib>0),
 state TEXT NOT NULL CHECK(state IN ('starting','ready','busy','draining','cleanup_failed')),
 snapshot_cipher TEXT NOT NULL, created_at REAL NOT NULL, ready_at REAL,
 last_used_at REAL NOT NULL, error_code TEXT
);
CREATE INDEX execution_function ON execution_instances(function_id,state);
CREATE TRIGGER retained_instance_revision BEFORE DELETE ON revisions
WHEN EXISTS (SELECT 1 FROM execution_instances WHERE revision_id=OLD.id)
BEGIN SELECT RAISE(ABORT,'instance_revision_is_retained'); END;
CREATE TRIGGER undeleted_instance_revision BEFORE UPDATE OF deleted_at ON revisions
WHEN NEW.deleted_at IS NOT NULL AND EXISTS (SELECT 1 FROM execution_instances WHERE revision_id=NEW.id)
BEGIN SELECT RAISE(ABORT,'instance_revision_is_retained'); END;
CREATE TABLE invocations (
 id TEXT PRIMARY KEY, actor_kind TEXT NOT NULL, actor_id TEXT NOT NULL,
 service_id TEXT NOT NULL REFERENCES services(id), function_id TEXT NOT NULL REFERENCES functions(id),
 revision_id TEXT, instance_id TEXT,
 state TEXT NOT NULL CHECK(state IN ('receiving','queued','admitted','running','succeeded','failed','rejected','disconnected','interrupted')),
 created_at REAL NOT NULL, queued_at REAL, admitted_at REAL, dispatched_at REAL, completed_at REAL,
 handler_started INTEGER CHECK(handler_started IN (0,1)), error_code TEXT, http_status INTEGER,
 logs TEXT NOT NULL DEFAULT '', logs_truncated INTEGER NOT NULL DEFAULT 0 CHECK(logs_truncated IN (0,1))
);
CREATE INDEX invocation_function ON invocations(function_id,created_at,id);
CREATE INDEX invocation_active ON invocations(state,completed_at);
