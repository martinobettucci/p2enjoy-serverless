-- @spec docs/BACKLOG.md#sls-074 | docs/SCHEMA.md#autorité-des-versions-et-promotions | docs/FUNCTION_VERSION_EXECUTION.md#autorité-persistante-et-migration
ALTER TABLE functions ADD COLUMN first_published_code_hash TEXT
 CHECK(first_published_code_hash IS NULL OR (length(first_published_code_hash)=64 AND first_published_code_hash NOT GLOB '*[^0-9a-f]*'));
ALTER TABLE functions ADD COLUMN first_promoted_at REAL;

-- Every pre-008 publication really activated its revision, including tombstones
-- whose inventory has since been purged. Never infer first promotion from NULL
-- active_revision_id, and never substitute a later known hash for an unknown one.
UPDATE functions SET
 first_published_code_hash=(SELECT r.code_hash FROM revisions r WHERE r.function_id=functions.id ORDER BY r.created_at,r.id LIMIT 1),
 first_promoted_at=(SELECT min(r.created_at) FROM revisions r WHERE r.function_id=functions.id);

CREATE TABLE function_versions (
 function_id TEXT NOT NULL REFERENCES functions(id),
 code_hash TEXT NOT NULL CHECK(length(code_hash)=64 AND code_hash NOT GLOB '*[^0-9a-f]*'),
 revision_id TEXT NOT NULL REFERENCES revisions(id),
 created_at REAL NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('available','archived','deleted')),
 updated_at REAL NOT NULL,
 PRIMARY KEY(function_id,code_hash)
);
CREATE INDEX function_version_date ON function_versions(function_id,created_at DESC,code_hash);

INSERT INTO function_versions(function_id,code_hash,revision_id,created_at,state,updated_at)
WITH aliases AS (
 SELECT r.*,CASE WHEN f.active_revision_id=r.id THEN 1 ELSE 0 END AS active,
  CASE WHEN r.deleted_at IS NULL AND r.stored_bytes>0 THEN 1 ELSE 0 END AS available
 FROM revisions r JOIN functions f ON f.id=r.function_id WHERE r.code_hash IS NOT NULL
), ranked AS (
 SELECT *,row_number() OVER(PARTITION BY function_id,code_hash ORDER BY active DESC,available DESC,created_at,id) AS position,
  min(created_at) OVER(PARTITION BY function_id,code_hash) AS first_created_at,
  max(available) OVER(PARTITION BY function_id,code_hash) AS any_available
 FROM aliases
)
SELECT function_id,code_hash,id,first_created_at,
 CASE WHEN any_available=1 THEN 'available' ELSE 'deleted' END,first_created_at
FROM ranked WHERE position=1;

CREATE TRIGGER inserted_version_reference BEFORE INSERT ON function_versions
WHEN NOT EXISTS(SELECT 1 FROM revisions r WHERE r.id=NEW.revision_id AND r.function_id=NEW.function_id AND r.code_hash=NEW.code_hash)
BEGIN SELECT RAISE(ABORT,'invalid_version_revision'); END;
CREATE TRIGGER updated_version_reference BEFORE UPDATE OF function_id,code_hash,revision_id ON function_versions
WHEN NEW.function_id IS NOT OLD.function_id OR NEW.code_hash IS NOT OLD.code_hash OR
 NOT EXISTS(SELECT 1 FROM revisions r WHERE r.id=NEW.revision_id AND r.function_id=NEW.function_id AND r.code_hash=NEW.code_hash)
BEGIN SELECT RAISE(ABORT,'invalid_version_revision'); END;
CREATE TRIGGER available_active_version BEFORE UPDATE OF active_revision_id ON functions
WHEN NEW.active_revision_id IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM revisions r JOIN function_versions v ON v.function_id=r.function_id AND v.code_hash=r.code_hash
 WHERE r.id=NEW.active_revision_id AND r.function_id=NEW.id AND v.state='available')
BEGIN SELECT RAISE(ABORT,'active_version_unavailable'); END;
CREATE TRIGGER retained_active_version BEFORE UPDATE OF state ON function_versions
WHEN NEW.state!='available' AND EXISTS(
 SELECT 1 FROM functions f JOIN revisions r ON r.id=f.active_revision_id
 WHERE f.id=NEW.function_id AND r.code_hash=NEW.code_hash)
BEGIN SELECT RAISE(ABORT,'active_version_is_retained'); END;
CREATE TRIGGER first_published_hash_immutable BEFORE UPDATE OF first_published_code_hash ON functions
WHEN OLD.first_published_code_hash IS NOT NULL AND NEW.first_published_code_hash IS NOT OLD.first_published_code_hash
BEGIN SELECT RAISE(ABORT,'first_published_hash_immutable'); END;
CREATE TRIGGER first_promotion_immutable BEFORE UPDATE OF first_promoted_at ON functions
WHEN OLD.first_promoted_at IS NOT NULL AND NEW.first_promoted_at IS NOT OLD.first_promoted_at
BEGIN SELECT RAISE(ABORT,'first_promotion_immutable'); END;

ALTER TABLE deployments ADD COLUMN code_hash TEXT;
ALTER TABLE deployments ADD COLUMN code_changed INTEGER CHECK(code_changed IN (0,1));
ALTER TABLE deployments ADD COLUMN version_restored INTEGER CHECK(version_restored IN (0,1));
ALTER TABLE deployments ADD COLUMN result_function_version REAL;
ALTER TABLE deployments ADD COLUMN default_code_hash_at_publication TEXT;
ALTER TABLE deployments ADD COLUMN restore_code_hash TEXT;
ALTER TABLE deployments ADD COLUMN code_only INTEGER NOT NULL DEFAULT 0 CHECK(code_only IN (0,1));
UPDATE deployments SET code_hash=(SELECT r.code_hash FROM revisions r WHERE r.id=deployments.revision_id)
 WHERE revision_id IS NOT NULL;

ALTER TABLE invocations ADD COLUMN requested_code_hash TEXT;
ALTER TABLE invocations ADD COLUMN resolved_code_hash TEXT;
UPDATE invocations SET resolved_code_hash=(SELECT r.code_hash FROM revisions r WHERE r.id=invocations.revision_id);
