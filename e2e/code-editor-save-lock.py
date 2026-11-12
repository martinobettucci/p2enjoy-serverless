# @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#fenêtre-réelle-de-sauvegarde--décision-avant-banc
# @verifies docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#fenêtre-réelle-de-sauvegarde--décision-avant-banc
"""A real, bounded, zero-write SQLite lock for the campaign's sole live function."""
import json
import os
from pathlib import Path
import select
import signal
import socket
import sys
import time
from uuid import UUID
from control_database import ControlWriter,read_control

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
assert len(sys.argv) in (4,7)
mode=sys.argv[1];assert mode in ('hold','probe','stop')
namespace,function=(str(UUID(value)) for value in sys.argv[2:4])
control=Path('/srv/p2enjoy-serverless/state/control.sqlite3')
signal.alarm(8)

def birth(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def emit(value):print(json.dumps(value),flush=True)
def scope(db):
    row=db.execute('''SELECT f.id,f.updated_at,f.active_revision_id,n.id namespace_id,n.name namespace_name
        FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id
        WHERE f.id=? AND n.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL AND n.deleted_at IS NULL''',(function,namespace)).fetchone()
    assert row and row['namespace_name'].startswith('edition-console-'),'campaign_scope_required'
    assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NULL').fetchone()[0]==1,'sole_live_function_required'
    assert db.execute('SELECT count(*) FROM execution_instances').fetchone()[0]==0,'no_instances_required'
    assert db.execute("SELECT count(*) FROM invocations WHERE completed_at IS NULL").fetchone()[0]==0,'no_live_invocations_required'
    return {k:row[k] for k in ('id','updated_at','active_revision_id','namespace_id')}|{'draft_versions':[v[0] for v in db.execute('SELECT version FROM code_drafts WHERE function_id=? ORDER BY id',(function,))]}

with read_control(control) as db:before=scope(db)
if mode=='stop':
    assert len(sys.argv)==7
    pid=int(sys.argv[4]);expected_birth=sys.argv[5];kind=sys.argv[6];assert pid>1 and kind in ('term','kill')
    descriptor=os.pidfd_open(pid)
    try:
        assert birth(pid)==expected_birth,'helper_birth_changed'
        command=Path('/proc',str(pid),'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
        assert Path(os.fsdecode(command[0])).name=='python3'
        assert [os.fsdecode(v) for v in command[1:]]==['-B',str(Path(__file__).resolve()),'hold',namespace,function],'helper_command_changed'
        signal.pidfd_send_signal(descriptor,signal.SIGTERM if kind=='term' else signal.SIGKILL)
        ready,_,_=select.select([descriptor],[],[],5);assert ready,'helper_exit_unconfirmed'
        emit({'event':'helper-stopped','pid':pid,'birth':expected_birth,'signal':kind,'native_exit_confirmed':True})
    finally:os.close(descriptor)
else:
    assert len(sys.argv)==4
    started=time.monotonic();reason='probe';writer=ControlWriter(control)
    try:
        current=scope(writer.db)
        if mode=='hold':assert current==before,'campaign_changed_before_lock'
        assert writer.db.total_changes==0
        if mode=='hold':
            emit({'event':'lock-held','pid':os.getpid(),'birth':birth(os.getpid()),'identity':writer.identity,'scope':current,'max_wait_seconds':3,'sql_changes':0})
            deadline=time.monotonic()+3;received=b''
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:reason='deadline';break
                ready,_,_=select.select([sys.stdin],[],[],remaining)
                if not ready:reason='deadline';break
                chunk=os.read(sys.stdin.fileno(),32-len(received))
                if not chunk:reason='owner-eof';break
                received+=chunk
                if b'\n' in received:
                    if received==b'release\n':reason='released';break
                    reason='invalid-input';raise ValueError('invalid_release_command')
                if len(received)==32:reason='invalid-input';raise ValueError('release_command_limit')

        assert writer.db.total_changes==0
    finally:
        changes=writer.db.total_changes if writer.db is not None else None
        writer.close()
        emit({'event':'lock-released' if mode=='hold' else 'writer-probe','reason':reason,'elapsed_seconds':time.monotonic()-started,'sql_changes':changes,'scope':current,'connection_closed':writer.db is None})
