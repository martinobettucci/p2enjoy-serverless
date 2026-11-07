-- @spec docs/BACKLOG.md#sls-064 | docs/SCHEMA.md#reçus-deffacement
BEGIN IMMEDIATE;
CREATE TABLE discard_receipts(
 function_id TEXT PRIMARY KEY REFERENCES functions(id),
 operation_id TEXT NOT NULL UNIQUE,
 installation_id TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('purge','clear-cache')),
 expected_version INTEGER NOT NULL CHECK(expected_version>=0),
 version INTEGER NOT NULL CHECK(version>expected_version)
);
PRAGMA user_version=4;
COMMIT;
