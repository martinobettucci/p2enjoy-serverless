-- @spec docs/BACKLOG.md#sls-050 | docs/SCHEMA.md#registre-local-de-stockage | docs/STORAGE_AGENT.md#santé-et-reprise
BEGIN IMMEDIATE;
ALTER TABLE probes RENAME TO probes_old;
CREATE TABLE probes(
 id INTEGER PRIMARY KEY CHECK(id=1),
 pid INTEGER,birth TEXT,boot TEXT NOT NULL,command_json TEXT NOT NULL
);
INSERT INTO probes SELECT * FROM probes_old;
DROP TABLE probes_old;
PRAGMA user_version=2;
COMMIT;
