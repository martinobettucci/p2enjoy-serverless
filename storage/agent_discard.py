# @spec docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#états-et-effets
"""Correlated, recoverable storage erasure with a single bounded worker."""
import asyncio
import json
import os
import sqlite3
import stat
import sys
from uuid import uuid4

from agent_system import StorageError,private_directory,uuid


def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


class Discards:
    def __init__(self,volumes,erase,joined):
        self.volumes=volumes;self.erase=erase;self.joined=joined
        self.worker=None;self.stopping=False;self.last_identifier=''

    def pending(self,identifier):
        value=json.loads(self.volumes.function(identifier)['pending_json'] or '{}')
        return value if value.get('operation') in ('purge','clear-cache') and 'operation_id' in value else None

    def save(self,identifier,pending):
        self.volumes.db.execute('UPDATE functions SET pending_json=? WHERE id=?',
                                (json.dumps(pending,sort_keys=True,separators=(',',':')),identifier))

    def query(self,identifier,operation,installation):
        identifier=uuid(identifier);operation=uuid(operation);installation=uuid(installation)
        function=self.volumes.function(identifier);pending=self.pending(identifier)
        if pending and pending['operation_id']==operation:
            row={**pending,'kind':pending['operation'],'version':function['version'],'state':'pending'}
        else:
            receipt=self.volumes.db.execute('SELECT * FROM discard_receipts WHERE function_id=? AND operation_id=?',
                                           (identifier,operation)).fetchone()
            if not receipt:raise StorageError('operation_unknown')
            row={**dict(receipt),'state':'completed','phase':None,'error_code':None}
        if row['installation_id']!=installation:raise StorageError('operation_owner')
        return {'function_id':identifier,'operation_id':operation,'installation_id':installation,
                **{key:row[key] for key in ('kind','state','phase','error_code','expected_version','version')}}

    def complete(self,identifier,pending):
        """Called in the same transaction as the final physical-state metadata."""
        v=self.volumes;version=v.function(identifier)['version']+1
        v.db.execute('UPDATE functions SET pending_json=NULL,version=? WHERE id=?',(version,identifier))
        v.db.execute('INSERT INTO discard_receipts VALUES(?,?,?,?,?,?) ON CONFLICT(function_id) DO UPDATE SET '
                     'operation_id=excluded.operation_id,installation_id=excluded.installation_id,kind=excluded.kind,'
                     'expected_version=excluded.expected_version,version=excluded.version',
                     (identifier,pending['operation_id'],pending['installation_id'],pending['operation'],pending['expected_version'],version))

    def start(self,identifier,operation,installation,kind,expected):
        v=self.volumes;identifier=uuid(identifier);operation=uuid(operation);installation=uuid(installation)
        if kind not in ('purge','clear-cache'):raise StorageError('invalid_discard_kind')
        if type(expected) is not int or expected<0:raise StorageError('invalid_version')
        try:result=self.query(identifier,operation,installation)
        except StorageError as error:
            if str(error)!='operation_unknown':raise
        else:
            if result['kind']!=kind or result['expected_version']!=expected:raise StorageError('operation_conflict')
            return result
        v.operation_available(operation)
        function=v.function(identifier);v.version(function,expected)
        if function['pending_json']:raise StorageError('operation_pending')
        if v.leased(identifier):raise StorageError('volume_busy')
        if kind=='purge' and function['state'] not in ('archived','purged'):raise StorageError('archive_required')
        if kind=='clear-cache' and function['state']!='active':raise StorageError('function_archived')
        pending={'operation':kind,'operation_id':operation,'installation_id':installation,'expected_version':expected,
                 'phase':'stopping','error_code':None,'trash':str(uuid4()),'extra':0}
        with v.transaction():
            if function['state']=='purged' or (kind=='clear-cache' and not v.row(identifier,'cache')):
                self.complete(identifier,pending)
            else:
                self.save(identifier,pending)
                if kind=='purge':v.db.execute("UPDATE functions SET state='purging' WHERE id=?",(identifier,))
        result=self.query(identifier,operation,installation)
        self.schedule()
        return result

    def schedule(self):
        """Called under the registry lock; round-robin prevents a failed tree starving others."""
        if self.worker is not None:
            if not self.worker.done():return
            finished=self.worker;self.worker=None
            try:finished.result()
            except sqlite3.Error:
                print(json.dumps({'event':'storage_discard_worker_failed','function_id':self.last_identifier,
                                  'error_code':'registry_unavailable'}),file=sys.stderr,flush=True)
                raise
        if self.stopping:return
        identifiers=[r[0] for r in self.volumes.db.execute('SELECT id FROM functions WHERE pending_json IS NOT NULL ORDER BY id')
                     if self.pending(r[0])]
        if not identifiers:return
        identifier=next((value for value in identifiers if value>self.last_identifier),identifiers[0])
        self.last_identifier=identifier
        self.worker=asyncio.create_task(self.run(identifier))

    async def run(self,identifier):
        v=self.volumes
        try:
            async with v.lock:
                pending=self.pending(identifier)
                if not pending:return
                if v.leased(identifier):raise StorageError('volume_busy')
                source=v.root/'backings'/identifier
                if pending['operation']=='clear-cache':source=source/'cache'
                destination=v.root/'trash'/uuid(pending['trash'])
                if pending['phase']=='stopping':
                    for row in v.rows(identifier):await v.stop(row)
                    if source.exists() and destination.exists():raise StorageError('cleanup_ambiguous')
                    if source.exists():
                        if not stat.S_ISDIR(source.lstat().st_mode):raise StorageError('unsafe_discard_path')
                        os.chmod(source,0o700,follow_symlinks=False);os.rename(source,destination)
                    # Repeated fsync also covers a crash after rename but before the phase commit.
                    for path in (source.parent,destination.parent):
                        if path.exists():sync_directory(path)
                    pending['phase']='erasing'
                pending['error_code']=None;self.save(identifier,pending)
            if pending['phase']=='erasing':
                await self.joined(asyncio.to_thread(self.erase,destination))
                if destination.exists():raise StorageError('cleanup_pending')
                sync_directory(destination.parent)
                async with v.lock:
                    pending['phase']='finalizing';self.save(identifier,pending)
            async with v.lock:
                if pending['operation']=='clear-cache':
                    private_directory(source,create=not source.exists());sync_directory(source.parent)
                else:
                    mount=v.root/'mounts'/identifier
                    if mount.exists():
                        for child in mount.iterdir():child.rmdir()
                        mount.rmdir()
                    sync_directory(mount.parent)
                with v.transaction():
                    if pending['operation']=='clear-cache':
                        v.db.execute("UPDATE volumes SET usage=0,error=NULL WHERE function_id=? AND kind='cache'",(identifier,))
                    else:
                        v.db.execute('DELETE FROM volumes WHERE function_id=?',(identifier,))
                        v.db.execute("UPDATE functions SET state='purged' WHERE id=?",(identifier,))
                    self.complete(identifier,pending)
        except (StorageError,OSError,sqlite3.Error) as error:
            async with v.lock:
                pending=self.pending(identifier)
                if pending:
                    pending['error_code']=str(error) if isinstance(error,StorageError) else 'storage_io_error'
                    self.save(identifier,pending)
                v.last_error='recovery_pending'

    async def finish(self):
        self.stopping=True
        if self.worker is not None:await self.joined(self.worker)
