-- @spec docs/BACKLOG.md#sls-074 | docs/SCHEMA.md#identité-du-code-des-révisions | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#constat-et-décision
ALTER TABLE revisions ADD COLUMN code_hash TEXT
    CHECK (code_hash IS NULL OR (length(code_hash)=64 AND code_hash NOT GLOB '*[^0-9a-f]*'));

-- The server registers this canonical calculator before starting migrations.
-- UUID aliases and every existing reference stay intact.
UPDATE revisions SET code_hash=historical_code_hash(
    inventory_json,handler,runtime,architecture,image_id,events_json,stored_bytes,deleted_at,
    EXISTS(SELECT 1 FROM functions f WHERE f.active_revision_id=revisions.id),
    EXISTS(
        SELECT 1 FROM functions f
        JOIN function_operations o ON o.function_id=f.id AND o.service_id=f.service_id
        JOIN storage_commands c ON c.id=o.id AND c.function_id=f.id AND c.service_id=f.service_id
        WHERE f.id=revisions.function_id AND f.deleted_at IS NOT NULL
          AND f.active_revision_id IS NULL
          AND revisions.inventory_json='[]' AND revisions.events_json='{}'
          AND o.kind='purge' AND o.decision='commit'
          AND c.kind='purge' AND c.state='pending' AND c.phase IN ('volumes','artifacts')
          AND c.installation_id=(SELECT value FROM security_metadata WHERE name='installation-id')
          AND c.result_version=f.updated_at
          AND c.expected_function_version=o.expected_function_version));

CREATE INDEX revision_code_hash ON revisions(function_id,code_hash,created_at,id);

CREATE TRIGGER revision_code_hash_required BEFORE INSERT ON revisions
WHEN NEW.code_hash IS NULL
BEGIN SELECT RAISE(ABORT,'revision_code_hash_required'); END;

CREATE TRIGGER revision_code_hash_immutable BEFORE UPDATE OF code_hash ON revisions
WHEN OLD.code_hash IS NOT NULL AND NEW.code_hash IS NOT OLD.code_hash
BEGIN SELECT RAISE(ABORT,'revision_code_hash_immutable'); END;
