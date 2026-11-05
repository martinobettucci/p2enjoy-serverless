-- @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/SCHEMA.md#identités
ALTER TABLE login_flows ADD COLUMN client_address TEXT NOT NULL DEFAULT '';
CREATE INDEX login_flows_client ON login_flows(client_address, expires_at);
CREATE TABLE login_rate (
    client_address TEXT PRIMARY KEY,
    window_start REAL NOT NULL,
    attempts INTEGER NOT NULL CHECK(attempts >= 0)
);
