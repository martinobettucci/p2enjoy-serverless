# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#identité-des-diagnostics-sqlite
"""Real operator SQLite access under the control database owner's identity."""
from contextlib import closing,contextmanager
import os
from pathlib import Path
import pwd
import signal
import sqlite3
import threading


@contextmanager
def control_owner(path):
    path=Path(path);account=pwd.getpwnam('spark-docker');info=path.stat()
    assert path.name=='control.sqlite3' and (info.st_uid,info.st_gid)==(account.pw_uid,account.pw_gid),'control_database_owner_required'
    assert threading.active_count()==1,'single_threaded_operator_required'
    uid,gid,groups=os.geteuid(),os.getegid(),os.getgroups()
    assert uid in (0,account.pw_uid),'control_identity_required'
    try:
        if uid==0:
            os.setgroups(os.getgrouplist(account.pw_name,account.pw_gid))
            os.setegid(account.pw_gid);os.seteuid(account.pw_uid)
        assert (os.geteuid(),os.getegid())==(account.pw_uid,account.pw_gid)
        yield
    finally:
        if uid==0:
            os.seteuid(uid);os.setegid(gid);os.setgroups(groups)
        assert (os.geteuid(),os.getegid(),os.getgroups())==(uid,gid,groups),'operator_identity_not_restored'


@contextmanager
def read_control(path,timeout=2):
    with control_owner(path):
        with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True,timeout=timeout,isolation_level=None)) as db:
            db.row_factory=sqlite3.Row
            yield db


class ControlWriter:
    """Hold a real writer without keeping the operator's effective identity changed."""
    def __init__(self,path,timeout=2):
        self.path=Path(path);self.db=None
        with control_owner(self.path):
            db=sqlite3.connect('file:'+str(path)+'?mode=rw',uri=True,timeout=timeout,isolation_level=None)
            try:
                db.row_factory=sqlite3.Row;db.execute('BEGIN IMMEDIATE')
                sidecars={suffix:Path(str(path)+suffix).stat().st_uid for suffix in ('-wal','-shm')}
                assert all(uid==os.geteuid() for uid in sidecars.values()),'control_sidecar_owner_mismatch'
                self.identity={'effective_uid':os.geteuid(),'effective_gid':os.getegid(),'sidecar_uids':sidecars}
                self.db=db
            except BaseException:db.close();raise

    def rows(self,sql,args=()):
        assert self.db is not None
        with control_owner(self.path):return [dict(row) for row in self.db.execute(sql,args)]

    def close(self):
        if self.db is None:return
        with control_owner(self.path):
            db,self.db=self.db,None
            try:
                if db.in_transaction:db.rollback()
            finally:db.close()

    def __enter__(self):return self
    def __exit__(self,*error):self.close()


# @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#observation-durable-des-intentions-par-les-gardes
class ControlObserver:
    """Keep one real connection open without retaining a read transaction."""
    def __init__(self,path):
        self.path=Path(path);self.db=None;self.identity=None;self.interruption_pending=False

    def open(self):
        assert self.db is None,'control_observer_already_open'
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGHUP,signal.SIGTERM,signal.SIGINT})
        try:
            with control_owner(self.path):
                db=sqlite3.connect('file:'+str(self.path)+'?mode=ro',uri=True,timeout=2,isolation_level=None)
                try:
                    db.row_factory=sqlite3.Row
                    with closing(db.execute('SELECT version FROM schema_migrations LIMIT 1')) as cursor:
                        assert cursor.fetchall(),'control_observer_schema_required'
                    assert not db.in_transaction,'control_observer_transaction_retained'
                    self.identity={'effective_uid':os.geteuid(),'effective_gid':os.getegid(),
                        'sidecar_uids':{suffix:Path(str(self.path)+suffix).stat().st_uid for suffix in ('-wal','-shm')}}
                    self.db=db
                except BaseException:db.close();raise
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)

    def rows(self,sql,args=()):
        assert self.db is not None,'control_observer_not_open'
        with control_owner(self.path):
            assert not self.db.in_transaction,'control_observer_transaction_retained'
            with closing(self.db.execute(sql,args)) as cursor:result=[dict(row) for row in cursor.fetchall()]
            assert not self.db.in_transaction,'control_observer_transaction_retained'
            return result

    def close(self,interrupt=False):
        if self.db is None:return
        previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGHUP,signal.SIGTERM,signal.SIGINT})
        try:
            with control_owner(self.path):
                if interrupt:
                    os.kill(os.getpid(),signal.SIGTERM)
                    self.interruption_pending=signal.SIGTERM in signal.sigpending()
                    assert self.interruption_pending,'operator_signal_not_queued'
                db,self.db=self.db,None
                try:assert not db.in_transaction,'control_observer_transaction_retained'
                finally:db.close()
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
