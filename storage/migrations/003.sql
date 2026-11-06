-- @spec docs/BACKLOG.md#sls-050 | docs/SCHEMA.md#préparation-des-quotas-par-le-contrôle
BEGIN IMMEDIATE;
CREATE TABLE configuration_receipts(
 function_id TEXT PRIMARY KEY REFERENCES functions(id),
 operation_id TEXT NOT NULL UNIQUE,
 installation_id TEXT NOT NULL,
 configuration_json TEXT NOT NULL,
 expected_version INTEGER NOT NULL,
 decision TEXT NOT NULL CHECK(decision IN ('committed','aborted')),
 version INTEGER NOT NULL
);
PRAGMA user_version=3;
COMMIT;
