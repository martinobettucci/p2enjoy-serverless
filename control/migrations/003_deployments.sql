-- @spec docs/BACKLOG.md#sls-030 | docs/SCHEMA.md#déploiements-et-révisions
CREATE TABLE revisions (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL REFERENCES functions(id),
 handler TEXT NOT NULL, runtime TEXT NOT NULL, architecture TEXT NOT NULL,
 image_id TEXT NOT NULL, archive_sha256 TEXT NOT NULL, inventory_json TEXT NOT NULL,
 events_json TEXT NOT NULL, stored_bytes INTEGER NOT NULL CHECK(stored_bytes>=0),
 created_at REAL NOT NULL, deleted_at REAL
);
CREATE INDEX revision_function ON revisions(function_id,created_at);
CREATE TABLE deployments (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL REFERENCES functions(id),
 service_id TEXT NOT NULL REFERENCES services(id), actor_kind TEXT NOT NULL,
 actor_id TEXT NOT NULL, expected_function_version REAL NOT NULL,
 expected_service_version REAL NOT NULL, configuration_cipher TEXT, events_json TEXT NOT NULL,
 required_right TEXT NOT NULL CHECK(required_right IN ('create','update')),
 state TEXT NOT NULL CHECK(state IN ('prepared','receiving','validating','published','failed','expired')),
 error_code TEXT, validation_json TEXT, reserved_bytes INTEGER NOT NULL DEFAULT 0 CHECK(reserved_bytes>=0),
 created_at REAL NOT NULL, expires_at REAL NOT NULL, completed_at REAL,
 revision_id TEXT REFERENCES revisions(id)
);
CREATE INDEX deployment_function ON deployments(function_id,created_at);
CREATE INDEX deployment_state ON deployments(state,expires_at);
CREATE TRIGGER active_revision_reference BEFORE UPDATE OF active_revision_id ON functions
WHEN NEW.active_revision_id IS NOT NULL AND NOT EXISTS (
 SELECT 1 FROM revisions WHERE id=NEW.active_revision_id AND function_id=NEW.id AND deleted_at IS NULL
)
BEGIN SELECT RAISE(ABORT,'invalid_active_revision'); END;
CREATE TRIGGER inserted_revision_reference BEFORE INSERT ON functions
WHEN NEW.active_revision_id IS NOT NULL
BEGIN SELECT RAISE(ABORT,'initial_revision_must_be_null'); END;
CREATE TRIGGER retained_active_revision BEFORE DELETE ON revisions
WHEN EXISTS (SELECT 1 FROM functions WHERE active_revision_id=OLD.id)
BEGIN SELECT RAISE(ABORT,'active_revision_is_retained'); END;
CREATE TRIGGER undeleted_active_revision BEFORE UPDATE OF deleted_at ON revisions
WHEN NEW.deleted_at IS NOT NULL AND EXISTS (SELECT 1 FROM functions WHERE active_revision_id=NEW.id)
BEGIN SELECT RAISE(ABORT,'active_revision_is_retained'); END;
