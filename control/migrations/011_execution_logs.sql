-- @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#modèle-et-migration-011 | docs/SCHEMA.md
ALTER TABLE invocations ADD COLUMN logs_collection_state TEXT NOT NULL DEFAULT 'pending'
 CHECK(logs_collection_state IN ('pending','collected','unavailable','not_started','expired','unknown'));
UPDATE invocations SET logs_collection_state=CASE WHEN logs<>'' THEN 'collected' ELSE 'unknown' END;

CREATE TABLE execution_log_state (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1), collection_id TEXT NOT NULL UNIQUE,
 started_at REAL NOT NULL, event_count INTEGER NOT NULL DEFAULT 0 CHECK(event_count>=0),
 payload_bytes INTEGER NOT NULL DEFAULT 0 CHECK(payload_bytes>=0),
 evicted_sequence INTEGER NOT NULL DEFAULT 0 CHECK(evicted_sequence>=0)
);
INSERT INTO execution_log_state(singleton,collection_id,started_at) VALUES
 (1,lower(hex(randomblob(4))||'-'||hex(randomblob(2))||'-4'||substr(hex(randomblob(2)),2)||'-'||
   substr('89ab',(random() & 3)+1,1)||substr(hex(randomblob(2)),2)||'-'||hex(randomblob(6))),
 CAST(strftime('%s','now') AS REAL));

CREATE TABLE service_log_policies (
 service_id TEXT PRIMARY KEY REFERENCES services(id), retention_minutes INTEGER NOT NULL DEFAULT 10080
 CHECK(retention_minutes BETWEEN 1 AND 10080), version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),
 updated_at REAL NOT NULL, expiration_floor REAL NOT NULL DEFAULT 0,
 prune_generation INTEGER NOT NULL DEFAULT 0 CHECK(prune_generation>=0),
 prune_reason TEXT CHECK(prune_reason IN ('retention','purge','capacity','visibility')),
 capacity_evicted_sequence INTEGER NOT NULL DEFAULT 0 CHECK(capacity_evicted_sequence>=0),
 pruned_sequence INTEGER NOT NULL DEFAULT 0 CHECK(pruned_sequence>=0)
);
INSERT INTO service_log_policies(service_id,updated_at)
 SELECT id,CAST(strftime('%s','now') AS REAL) FROM services WHERE deleted_at IS NULL;

CREATE TABLE execution_log_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
 observation_key TEXT NOT NULL UNIQUE, service_id TEXT NOT NULL REFERENCES services(id),
 function_id TEXT, source TEXT NOT NULL CHECK(source IN ('application','platform')),
 kind TEXT NOT NULL, severity TEXT CHECK(severity IN ('trace','debug','info','warning','error','fatal')),
 state TEXT, observed_at REAL NOT NULL, invocation_id TEXT, request_id TEXT,
 instance_id TEXT, revision_id TEXT, code_hash TEXT, deployment_id TEXT, operation_id TEXT,
 message TEXT NOT NULL, metadata_json TEXT NOT NULL, message_format TEXT NOT NULL CHECK(message_format IN ('text','json')),
 message_truncated INTEGER NOT NULL DEFAULT 0 CHECK(message_truncated IN (0,1)),
 collection_truncated INTEGER NOT NULL DEFAULT 0 CHECK(collection_truncated IN (0,1)),
 projection_truncated INTEGER NOT NULL DEFAULT 0 CHECK(projection_truncated IN (0,1)),
 payload_bytes INTEGER NOT NULL CHECK(payload_bytes>0)
);
CREATE INDEX execution_log_service_time ON execution_log_events(service_id,observed_at DESC,sequence DESC);
CREATE INDEX execution_log_function_time ON execution_log_events(function_id,observed_at DESC,sequence DESC);
CREATE INDEX execution_log_invocation ON execution_log_events(invocation_id,sequence);
CREATE INDEX execution_log_retention ON execution_log_events(service_id,observed_at,sequence);
