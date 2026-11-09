# @spec docs/BACKLOG.md#sls-020 | docs/SCHEMA.md
# Connections, short transactions, migrations and secret-free audit records.
from contextlib import contextmanager, closing
import json
from pathlib import Path
import sqlite3
import time
import uuid

# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation
from function_code_hash import code_hash, PackageIdentityError


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_UPGRADE.md#constat-et-décision
def historical_code_hash(inventory,handler,runtime,architecture,image_id,events,stored_bytes,deleted_at,active,purge_committed=False):
    files=json.loads(inventory)
    if files==[] and deleted_at is not None and not active and (stored_bytes==0 or purge_committed):
        return None
    if not files:raise PackageIdentityError('historical_inventory_missing')
    return code_hash(files,{'handler':handler,'runtime':runtime,'architecture':architecture,
                            'image_id':image_id,'events':json.loads(events)})['code_hash']


class Database:
    def __init__(self,root: Path):
        root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.path=root/'control.sqlite3'

    def connect(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=5000')
        return db

    @contextmanager
    def transaction(self,*,busy_timeout=5000):
        db=self.connect()
        try:
            db.execute('PRAGMA busy_timeout='+str(int(busy_timeout)))
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        finally:
            db.close()

    def one(self,sql,args=()):
        with closing(self.connect()) as db:
            row=db.execute(sql,args).fetchone()
        return dict(row) if row else None

    def all(self,sql,args=()):
        with closing(self.connect()) as db:
            rows=db.execute(sql,args).fetchall()
        return [dict(row) for row in rows]

    def migrate(self):
        db=self.connect()
        try:
            db.create_function('historical_code_hash',10,historical_code_hash,deterministic=True)
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at REAL NOT NULL)')
            for path in sorted((Path(__file__).parent.parent/'migrations').glob('*.sql')):
                if db.execute('SELECT 1 FROM schema_migrations WHERE version=?',(path.name,)).fetchone():continue
                # Migration names originate from the shipped directory, not input.
                script='BEGIN IMMEDIATE;\n'+path.read_text()+f"\nINSERT INTO schema_migrations VALUES ('{path.name}',{time.time()});\nCOMMIT;"
                db.executescript(script)
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        finally:
            db.close()


def audit(db,actor,action,object_id=None,service_id=None,detail=None):
    db.execute('INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?)',(
        str(uuid.uuid4()),actor.kind,actor.id,service_id,action,object_id,
        time.time(),json.dumps(detail or {},separators=(',',':'))))
