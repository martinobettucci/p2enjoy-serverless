-- @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#persistance-concurrence-et-conservation | docs/SCHEMA.md
CREATE TABLE code_drafts (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL REFERENCES functions(id),
 actor_kind TEXT NOT NULL CHECK(actor_kind IN ('admin','token')), actor_id TEXT NOT NULL,
 base_revision_id TEXT REFERENCES revisions(id), base_function_version REAL NOT NULL,
 base_descriptor_json TEXT NOT NULL, handler TEXT NOT NULL,
 changes_cipher TEXT NOT NULL, change_bytes INTEGER NOT NULL CHECK(change_bytes>=0),
 version INTEGER NOT NULL CHECK(version>=1), created_at REAL NOT NULL, updated_at REAL NOT NULL,
 last_deployment_id TEXT REFERENCES deployments(id), last_publication_version INTEGER,
 UNIQUE(function_id,actor_kind,actor_id),
 CHECK((last_deployment_id IS NULL)=(last_publication_version IS NULL))
);
CREATE INDEX code_draft_base ON code_drafts(base_revision_id);
CREATE INDEX code_draft_actor ON code_drafts(actor_kind,actor_id);
CREATE TRIGGER inserted_draft_base BEFORE INSERT ON code_drafts
WHEN NEW.base_revision_id IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM revisions WHERE id=NEW.base_revision_id AND function_id=NEW.function_id)
BEGIN SELECT RAISE(ABORT,'invalid_draft_base'); END;
CREATE TRIGGER immutable_draft_base BEFORE UPDATE OF function_id,actor_kind,actor_id,base_revision_id ON code_drafts
WHEN NEW.function_id IS NOT OLD.function_id OR NEW.actor_kind IS NOT OLD.actor_kind
 OR NEW.actor_id IS NOT OLD.actor_id OR NEW.base_revision_id IS NOT OLD.base_revision_id
BEGIN SELECT RAISE(ABORT,'immutable_draft_owner_and_base'); END;
CREATE TRIGGER retained_draft_base BEFORE UPDATE OF deleted_at ON revisions
WHEN NEW.deleted_at IS NOT NULL AND EXISTS(SELECT 1 FROM code_drafts WHERE base_revision_id=OLD.id)
BEGIN SELECT RAISE(ABORT,'draft_base_is_retained'); END;
