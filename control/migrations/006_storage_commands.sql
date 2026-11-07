-- @spec docs/BACKLOG.md#sls-065 | docs/SCHEMA.md#commandes-publiques-de-stockage
ALTER TABLE functions ADD COLUMN purged_at REAL;
ALTER TABLE function_operations RENAME TO previous_function_operations;
DROP INDEX function_operation_service;
CREATE TABLE function_operations (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL UNIQUE,
 service_id TEXT NOT NULL REFERENCES services(id),
 kind TEXT NOT NULL CHECK(kind IN ('configuration','archive','clear-cache','purge')),
 decision TEXT NOT NULL CHECK(decision IN ('undecided','commit','abort')),
 configuration_json TEXT, storage_version INTEGER CHECK(storage_version>=0),
 expected_function_version REAL, expected_service_version REAL NOT NULL,
 created_at REAL NOT NULL, error_code TEXT,
 CHECK((kind='configuration' AND configuration_json IS NOT NULL) OR
       (kind IN ('archive','clear-cache','purge') AND configuration_json IS NULL))
);
INSERT INTO function_operations SELECT * FROM previous_function_operations;
DROP TABLE previous_function_operations;
CREATE INDEX function_operation_service ON function_operations(service_id);
CREATE TABLE storage_commands (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL REFERENCES functions(id),
 service_id TEXT NOT NULL REFERENCES services(id), installation_id TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('clear-cache','purge')),
 state TEXT NOT NULL CHECK(state IN ('preparing','pending','completed','aborted')),
 phase TEXT CHECK(phase IN ('draining','volumes','artifacts')),
 storage_absent INTEGER NOT NULL DEFAULT 0 CHECK(storage_absent IN (0,1)),
 expected_function_version REAL NOT NULL, result_version REAL,
 created_at REAL NOT NULL, completed_at REAL, error_code TEXT
);
CREATE INDEX storage_command_function ON storage_commands(function_id,created_at DESC,id);
