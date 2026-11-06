-- @spec docs/BACKLOG.md#sls-050 | docs/SCHEMA.md#intentions-des-mutations-publiques
CREATE TABLE function_operations (
 id TEXT PRIMARY KEY, function_id TEXT NOT NULL UNIQUE,
 service_id TEXT NOT NULL REFERENCES services(id),
 kind TEXT NOT NULL CHECK(kind IN ('configuration','archive')),
 decision TEXT NOT NULL CHECK(decision IN ('undecided','commit','abort')),
 configuration_json TEXT, storage_version INTEGER CHECK(storage_version>=0),
 expected_function_version REAL, expected_service_version REAL NOT NULL,
 created_at REAL NOT NULL, error_code TEXT,
 CHECK((kind='configuration' AND configuration_json IS NOT NULL) OR (kind='archive' AND configuration_json IS NULL))
);
CREATE INDEX function_operation_service ON function_operations(service_id);
