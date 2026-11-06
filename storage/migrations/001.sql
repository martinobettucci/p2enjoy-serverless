-- @spec docs/BACKLOG.md#sls-050 | docs/SCHEMA.md#registre-local-de-stockage | docs/STORAGE_AGENT.md#registre-et-chemins
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS functions(
 id TEXT PRIMARY KEY,
 state TEXT NOT NULL CHECK(state IN ('active','archived','purging','purged')),
 version INTEGER NOT NULL DEFAULT 0,
 config_json TEXT NOT NULL,
 pending_json TEXT
);
CREATE TABLE IF NOT EXISTS volumes(
 function_id TEXT NOT NULL REFERENCES functions(id),
 kind TEXT NOT NULL CHECK(kind IN ('data','cache')),
 quota INTEGER NOT NULL CHECK(quota>=0),
 enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
 generation TEXT,
 phase TEXT NOT NULL DEFAULT 'unmounted',
 daemon_quota INTEGER,
 daemon_pid INTEGER,
 daemon_birth TEXT,
 daemon_boot TEXT,
 daemon_binary TEXT,
 usage INTEGER,
 error TEXT,
 PRIMARY KEY(function_id,kind)
);
CREATE TABLE IF NOT EXISTS leases(
 consumer_id TEXT PRIMARY KEY,
 installation_id TEXT NOT NULL,
 function_id TEXT NOT NULL REFERENCES functions(id),
 config_json TEXT NOT NULL,
 mounts_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS leases_function ON leases(function_id);
CREATE TABLE IF NOT EXISTS probes(
 id INTEGER PRIMARY KEY CHECK(id=1),
 pid INTEGER NOT NULL,birth TEXT NOT NULL,boot TEXT NOT NULL,command_json TEXT NOT NULL
);
