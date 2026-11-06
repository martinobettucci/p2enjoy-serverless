# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#installation-et-canal-opérateur
"""Install the protected storage bundle in the authorized DEV cell only."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import sqlite3
import stat
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
UNIT='p2enjoy-storage-dev.service'
FILES=('agent.py','agent_system.py','agent_volumes.py','migrations/001.sql','migrations/002.sql','migrations/003.sql','p2-quota')


def run(*args,**kwargs):return subprocess.run(args,check=True,text=True,capture_output=True,**kwargs).stdout.strip()


def main():
    if os.getuid()!=0 or Path('/etc/hostname').read_text().strip()!='infra-serverless':raise RuntimeError('authorized DEV root required')
    account=pwd.getpwnam('spark-docker')
    names=['SERVERLESS_STORAGE_ROOT_HOST','SERVERLESS_STORAGE_SOCKET_DIR_HOST']
    config=json.loads(run('systemd-run','--quiet','--wait','--pipe','--collect',
        '--property=EnvironmentFile=/etc/spark/env','--property=EnvironmentFile=/run/spark/secrets',
        '/usr/bin/python3','-I','-c','import json,os;print(json.dumps({n:os.environ[n] for n in '+repr(names)+'}))'))
    root=Path(config[names[0]]);directory=Path(config[names[1]])
    unit_path=Path('/etc/systemd/system')/UNIT
    active=subprocess.run(['systemctl','is-active','--quiet',UNIT]).returncode==0
    if unit_path.exists():
        recorded=[line.removeprefix('# StorageRoot: ') for line in unit_path.read_text().splitlines() if line.startswith('# StorageRoot: ')]
        if len(recorded)>1 or (recorded and json.loads(recorded[0])!=str(root)):
            raise RuntimeError('changing an installed storage root requires explicit migration')
        if not recorded and not active:raise RuntimeError('start the installed agent to establish its storage root before upgrade')
    if not root.is_absolute() or '..' in root.parts or not root.is_relative_to('/srv/p2enjoy-serverless') or root==Path('/srv/p2enjoy-serverless'):
        raise RuntimeError('storage root must be a dedicated DEV project directory')
    if directory.parent!=Path('/srv/p2enjoy-serverless') or not directory.name.replace('-','').isalnum() or directory==root or root.is_relative_to(directory):
        raise RuntimeError('socket directory must be a separate private DEV project directory')
    for path in (*root.parents,root):
        if path.is_symlink():raise RuntimeError('symlink in storage root')
    if root.exists():
        info=root.stat()
        if info.st_uid!=account.pw_uid or stat.S_IMODE(info.st_mode)!=0o700:raise RuntimeError('storage root permissions')
    else:
        root.mkdir(mode=0o700);os.chown(root,account.pw_uid,account.pw_gid)
    if directory.is_symlink():raise RuntimeError('symlink in socket directory')
    if directory.exists():
        info=directory.stat()
        if not directory.is_dir() or info.st_uid!=account.pw_uid or stat.S_IMODE(info.st_mode)!=0o700:
            raise RuntimeError('socket directory permissions')
    else:
        directory.mkdir(mode=0o700);os.chown(directory,account.pw_uid,account.pw_gid)
    registry=root/'registry.sqlite3'
    if registry.exists():
        with sqlite3.connect('file:'+str(registry)+'?mode=ro',uri=True) as db:
            if db.execute('SELECT count(*) FROM leases').fetchone()[0] or db.execute('SELECT count(*) FROM functions WHERE pending_json IS NOT NULL').fetchone()[0]:
                raise RuntimeError('drain leases and pending operations before maintenance')
    active_directory=directory
    if active:
        pid=int(run('systemctl','show','--property=MainPID','--value',UNIT))
        process_values={key.decode():value.decode() for entry in Path('/proc',str(pid),'environ').read_bytes().split(b'\0')
                        if b'=' in entry for key,value in [entry.split(b'=',1)] if key.decode() in names}
        if process_values.get(names[0])!=str(root):raise RuntimeError('changing an active storage root requires explicit migration')
        active_directory=Path(process_values[names[1]])
        script='''import json,socket,sys
s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(sys.argv[1]);s.sendall(b'{"op":"health"}\\n');line=s.makefile('rb').readline(65537);print(line.decode())'''
        health=json.loads(run('runuser','-u',account.pw_name,'--','/usr/bin/python3','-I','-c',script,str(active_directory/'agent.sock')))
        if not health.get('ok') or not health['result']['healthy'] or health['result']['leases'] or health['result']['mounted_or_reserved']:
            raise RuntimeError('healthy idle storage required before maintenance')
    digest=hashlib.sha256()
    for name in FILES:digest.update(name.encode()+b'\0'+(ROOT/name).read_bytes())
    bundle=Path('/usr/local/lib/p2enjoy-serverless/storage')/digest.hexdigest()
    bundle.mkdir(parents=True,exist_ok=True,mode=0o755)
    for name in FILES:
        target=bundle/name;target.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        content=(ROOT/name).read_bytes()
        if target.exists() and target.read_bytes()!=content:raise RuntimeError('immutable bundle mismatch')
        if not target.exists():target.write_bytes(content)
        os.chown(target,0,0);target.chmod(0o755 if name=='p2-quota' else 0o644)
    unit=f'''# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#propriété-et-exécution
# StorageRoot: {json.dumps(str(root))}
[Unit]
Description=P2Enjoy storage DEV
After=local-fs.target
[Service]
Type=simple
User={account.pw_name}
Group={account.pw_gid}
UMask=0077
EnvironmentFile=/etc/spark/env
EnvironmentFile=/run/spark/secrets
ExecStart=/usr/bin/python3 -I -B {bundle}/agent.py
AmbientCapabilities=CAP_SYS_ADMIN
CapabilityBoundingSet=CAP_SYS_ADMIN
NoNewPrivileges=yes
PrivateMounts=no
KillMode=control-group
TimeoutStopSec=30
Restart=on-failure
RestartSec=2
MemoryMax=1G
TasksMax=1024
LimitNOFILE=4096
[Install]
WantedBy=multi-user.target
'''
    def maintenance(operation):
        script='''import socket,sys
s=socket.socket(socket.AF_UNIX);s.settimeout(10);s.connect(sys.argv[1]);s.sendall(sys.argv[2].encode()+b'\\n');print(s.makefile('rb').readline(65537).decode())'''
        response=json.loads(run('runuser','-u',account.pw_name,'--','/usr/bin/python3','-I','-c',script,str(active_directory/'agent.sock'),json.dumps({'op':operation,'installation_id':health['result']['installation_id']})))
        if not response.get('ok'):raise RuntimeError('storage maintenance refused: '+response.get('error','invalid_response'))
    try:
        if active:maintenance('quiesce')
        unit_path.write_text(unit);unit_path.chmod(0o644)
        run('systemctl','daemon-reload');run('systemctl','enable',UNIT);run('systemctl','restart',UNIT)
    except BaseException:
        if active:
            try:maintenance('resume')
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):pass
        raise
    print(json.dumps({'service':UNIT,'bundle_sha256':digest.hexdigest(),'bundle':str(bundle),'started':True}))


if __name__=='__main__':main()
