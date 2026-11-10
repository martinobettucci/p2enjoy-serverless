-- @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009 | docs/SCHEMA.md
CREATE TABLE schedule_generations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 function_id TEXT NOT NULL REFERENCES functions(id),
 revision_id TEXT NOT NULL,
 code_hash TEXT NOT NULL,
 events_json TEXT NOT NULL,
 activated_at REAL NOT NULL,
 retired_at REAL
);
CREATE UNIQUE INDEX schedule_current ON schedule_generations(function_id) WHERE retired_at IS NULL;
CREATE INDEX schedule_windows ON schedule_generations(activated_at,retired_at);
INSERT INTO schedule_generations(function_id,revision_id,code_hash,events_json,activated_at)
 SELECT f.id,r.id,r.code_hash,r.events_json,CAST(strftime('%s','now') AS REAL)
 FROM functions f JOIN revisions r ON r.id=f.active_revision_id WHERE f.deleted_at IS NULL;
CREATE TRIGGER schedule_promotion AFTER UPDATE OF active_revision_id,deleted_at ON functions
 WHEN OLD.active_revision_id IS NOT NEW.active_revision_id OR OLD.deleted_at IS NOT NEW.deleted_at
 BEGIN
  UPDATE schedule_generations SET retired_at=NEW.updated_at
   WHERE function_id=NEW.id AND retired_at IS NULL;
  INSERT INTO schedule_generations(function_id,revision_id,code_hash,events_json,activated_at)
   SELECT NEW.id,r.id,r.code_hash,r.events_json,NEW.updated_at FROM revisions r
   WHERE r.id=NEW.active_revision_id AND NEW.deleted_at IS NULL;
 END;
CREATE TABLE schedule_cursor (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1), window_at INTEGER NOT NULL CHECK(window_at%300=0)
);
CREATE TABLE schedule_firings (
 id TEXT PRIMARY KEY,
 generation_id INTEGER NOT NULL REFERENCES schedule_generations(id),
 function_id TEXT NOT NULL REFERENCES functions(id),
 schedule_index INTEGER NOT NULL CHECK(schedule_index>=0 AND schedule_index<16),
 origin TEXT NOT NULL CHECK(origin IN ('manifest','console')),
 expression TEXT NOT NULL,
 code_hash TEXT NOT NULL,
 nominal_at INTEGER NOT NULL,
 window_at INTEGER NOT NULL CHECK(window_at%300=0),
 coalesced INTEGER NOT NULL CHECK(coalesced>0),
 state TEXT NOT NULL CHECK(state IN ('claimed','dispatched','succeeded','failed','skipped_downtime','skipped_overlap') OR state GLOB 'refused_*'),
 claimed_at REAL NOT NULL,
 dispatched_at REAL,
 completed_at REAL,
 delay_seconds REAL,
 invocation_id TEXT UNIQUE,
 error_code TEXT,
 UNIQUE(generation_id,schedule_index,window_at)
);
CREATE INDEX schedule_firing_history ON schedule_firings(function_id,window_at,id);
CREATE INDEX schedule_firing_active ON schedule_firings(state,completed_at);
ALTER TABLE invocations ADD COLUMN trigger TEXT NOT NULL DEFAULT 'http' CHECK(trigger IN ('http','schedule','job','manual'));
ALTER TABLE invocations ADD COLUMN schedule_firing_id TEXT;
ALTER TABLE invocations ADD COLUMN schedule_origin TEXT;
ALTER TABLE invocations ADD COLUMN schedule_expression TEXT;
ALTER TABLE invocations ADD COLUMN schedule_slot INTEGER;
