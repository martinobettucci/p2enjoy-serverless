-- @spec docs/BACKLOG.md#sls-020 | docs/SCHEMA.md
-- Initial durable objects, service credentials, OAuth sessions and audit.
CREATE TABLE security_metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE namespaces (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 created_at REAL NOT NULL, updated_at REAL NOT NULL, deleted_at REAL
);
CREATE UNIQUE INDEX namespace_name ON namespaces(name) WHERE deleted_at IS NULL;
CREATE TABLE services (
 id TEXT PRIMARY KEY, namespace_id TEXT NOT NULL REFERENCES namespaces(id),
 name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 policy_json TEXT NOT NULL DEFAULT '{}', environment_json TEXT NOT NULL DEFAULT '{}',
 secrets_cipher TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL, deleted_at REAL
);
CREATE UNIQUE INDEX service_name ON services(namespace_id,name) WHERE deleted_at IS NULL;
CREATE TABLE functions (
 id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id), name TEXT NOT NULL,
 config_json TEXT NOT NULL, environment_json TEXT NOT NULL DEFAULT '{}', secrets_cipher TEXT NOT NULL,
 active_revision_id TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL, deleted_at REAL
);
CREATE UNIQUE INDEX function_name ON functions(service_id,name) WHERE deleted_at IS NULL;
CREATE TABLE service_tokens (
 id TEXT PRIMARY KEY, service_id TEXT NOT NULL REFERENCES services(id), name TEXT NOT NULL,
 digest TEXT NOT NULL UNIQUE, prefix TEXT NOT NULL, rights_json TEXT NOT NULL,
 function_ids_json TEXT, expires_at REAL, revoked_at REAL, created_at REAL NOT NULL, last_used_at REAL
);
CREATE INDEX token_service ON service_tokens(service_id,created_at);
CREATE TABLE login_flows (
 state_digest TEXT PRIMARY KEY, verifier_cipher TEXT NOT NULL, nonce TEXT NOT NULL, expires_at REAL NOT NULL
);
CREATE TABLE sessions (
 digest TEXT PRIMARY KEY, subject TEXT NOT NULL, display_name TEXT NOT NULL,
 csrf_digest TEXT NOT NULL, tokens_cipher TEXT NOT NULL, access_expires_at REAL NOT NULL,
 created_at REAL NOT NULL, expires_at REAL NOT NULL
);
CREATE INDEX session_expiry ON sessions(expires_at);
CREATE TABLE audit_events (
 id TEXT PRIMARY KEY, actor_kind TEXT NOT NULL, actor_id TEXT NOT NULL, service_id TEXT,
 action TEXT NOT NULL, object_id TEXT, created_at REAL NOT NULL, detail_json TEXT NOT NULL
);
CREATE INDEX audit_service_time ON audit_events(service_id,created_at);
