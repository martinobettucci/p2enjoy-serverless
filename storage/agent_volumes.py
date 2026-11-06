# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#opérations-et-baux
"""Durable volume operations; every mount and quota preparation is a real process."""
import asyncio
from contextlib import contextmanager,suppress
import fcntl
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import time
from uuid import uuid4

from agent_system import StorageError,System,private_directory,uuid

MIB=1024**2
DEFAULT={'data':{'enabled':False,'quota_mib':64},'cache':{'enabled':False,'quota_mib':64}}


def canonical(data):return json.dumps(data,sort_keys=True,separators=(',',':'))


def configuration(value):
    if not isinstance(value,dict) or set(value)!={'data','cache'}:raise StorageError('invalid_configuration')
    for row in value.values():
        if not isinstance(row,dict) or set(row)!={'enabled','quota_mib'} or type(row['enabled']) is not bool or type(row['quota_mib']) is not int or not 1<=row['quota_mib']<=65536:
            raise StorageError('invalid_configuration')
    return value


async def joined(awaitable):
    task=asyncio.ensure_future(awaitable);cancelled=False
    while not task.done():
        try:await asyncio.shield(task)
        except asyncio.CancelledError:cancelled=True
    result=task.result()
    if cancelled:raise asyncio.CancelledError
    return result


def erase(path):
    """Delete the detached tree with one open directory per depth, never symlinks."""
    path=Path(path)
    if not path.exists():return
    parent=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stack=[];opened=set()
    try:
        os.chmod(path.name,0o700,dir_fd=parent,follow_symlinks=False)
        root=os.open(path.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
        opened.add(root);stack.append((root,parent,path.name,os.scandir(root)))
        while stack:
            fd,parent_fd,name,entries=stack[-1]
            entry=next(entries,None)
            if entry is None:
                entries.close();os.close(fd);opened.remove(fd);stack.pop()
                os.rmdir(name,dir_fd=parent_fd);continue
            if entry.is_dir(follow_symlinks=False):
                os.chmod(entry.name,0o700,dir_fd=fd,follow_symlinks=False)
                child=os.open(entry.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                opened.add(child);stack.append((child,fd,entry.name,os.scandir(child)))
            else:os.unlink(entry.name,dir_fd=fd)
    finally:
        for *_,entries in stack:entries.close()
        for fd in opened:
            with suppress(OSError):os.close(fd)
        os.close(parent)


class Volumes:
    def __init__(self,root,binary,budget,reserve,max_mounts):
        self.root=private_directory(root);self.budget=budget;self.reserve=reserve;self.max_mounts=max_mounts
        self.lock=asyncio.Lock();self.ready=False;self.last_error=None;self.closed=False
        self.owner=os.open(self.root/'agent.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:fcntl.flock(self.owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self.owner);raise StorageError('agent_already_running') from None
        for name in ('backings','mounts','trash'):
            path=self.root/name
            private_directory(path,create=not path.exists())
        path=self.root/'registry.sqlite3'
        if path.exists() and (not stat.S_ISREG(path.lstat().st_mode) or path.lstat().st_nlink!=1):raise StorageError('invalid_registry')
        self.db=sqlite3.connect(path,isolation_level=None,timeout=1);self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        version=self.db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0,1,2,3):raise StorageError('registry_version')
        if version==0:
            self.db.executescript((Path(__file__).parent/'migrations/001.sql').read_text())
            self.db.execute('PRAGMA user_version=1')
        if version<2:self.db.executescript((Path(__file__).parent/'migrations/002.sql').read_text())
        if version<3:self.db.executescript((Path(__file__).parent/'migrations/003.sql').read_text())
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES('installation',?)",(str(uuid4()),))
        self.id=self.db.execute("SELECT value FROM metadata WHERE name='installation'").fetchone()[0]
        self.system=System(root,binary,self.db)

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:yield;self.db.execute('COMMIT')
        except BaseException:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise

    def function(self,identifier):
        identifier=uuid(identifier);row=self.db.execute('SELECT * FROM functions WHERE id=?',(identifier,)).fetchone()
        if not row:raise StorageError('function_unknown')
        return row

    def rows(self,identifier):
        return self.db.execute('SELECT * FROM volumes WHERE function_id=? ORDER BY kind',(identifier,)).fetchall()

    def row(self,identifier,kind):
        return self.db.execute('SELECT * FROM volumes WHERE function_id=? AND kind=?',(identifier,kind)).fetchone()

    def leased(self,identifier):
        return self.db.execute('SELECT count(*) FROM leases WHERE function_id=?',(identifier,)).fetchone()[0]

    def allocated(self):
        used=self.db.execute('SELECT coalesce(sum(quota),0) FROM volumes').fetchone()[0]
        for row in self.db.execute('SELECT pending_json FROM functions WHERE pending_json IS NOT NULL'):
            used+=json.loads(row[0]).get('extra',0)
        return used

    def version(self,row,expected):
        if expected is not None and (type(expected) is not int or expected!=row['version']):raise StorageError('version_conflict')

    def snapshot(self,identifier):
        function=self.function(identifier);volumes={}
        for row in self.rows(identifier):
            volumes[row['kind']]={'enabled':bool(row['enabled']),'quota_bytes':row['quota'],'phase':row['phase'],
                'generation':row['generation'],'last_measured_used_bytes':row['usage'],'error':row['error']}
        return {'id':identifier,'state':function['state'],'version':function['version'],'configuration':json.loads(function['config_json']),
                'pending':bool(function['pending_json']),'leases':self.leased(identifier),'volumes':volumes}

    def health(self):
        pending=self.db.execute('SELECT count(*) FROM functions WHERE pending_json IS NOT NULL').fetchone()[0]
        failed=self.db.execute("SELECT count(*) FROM volumes WHERE phase='failed'").fetchone()[0]
        leases=self.db.execute('SELECT count(*) FROM leases').fetchone()[0]
        slots=self.db.execute("SELECT count(*) FROM volumes WHERE phase!='unmounted'").fetchone()[0]
        return {'ready':self.ready and not self.closed,'healthy':self.ready and not self.closed and not pending and not failed and not self.last_error,
                'installation_id':self.id,'pending_functions':pending,'failed_volumes':failed,'leases':leases,
                'mounted_or_reserved':slots,'max_mounts':self.max_mounts,'allocated_bytes':self.allocated(),
                'budget_bytes':self.budget,'reserve_bytes':self.reserve,'error':self.last_error}

    def directories(self,row):
        backing,mount=self.system.paths(row)
        for parent in (backing.parent,mount.parent):private_directory(parent,create=not parent.exists())
        if not backing.exists():private_directory(backing,create=True)
        if backing.is_symlink() or not backing.is_dir() or backing.stat().st_uid!=os.getuid():raise StorageError('unsafe_backing')
        private_directory(mount,create=not mount.exists())
        return backing,mount

    async def mount(self,row,quota=None):
        quota=quota if quota is not None else row['quota']
        if row['phase']=='mounted':
            if row['daemon_quota']!=quota:raise StorageError('quota_generation_conflict')
            await self.measure(row);return self.row(row['function_id'],row['kind'])
        if row['phase']!='unmounted':raise StorageError('volume_unavailable')
        slots=self.db.execute("SELECT count(*) FROM volumes WHERE phase!='unmounted'").fetchone()[0]
        if slots>=self.max_mounts:raise StorageError('mount_limit')
        if self.system.mounted(row):raise StorageError('unexpected_mount')
        self.directories(row)
        generation=str(uuid4())
        self.db.execute("UPDATE volumes SET phase='starting',generation=?,daemon_quota=?,daemon_pid=NULL,daemon_birth=NULL,daemon_boot=?,daemon_binary=?,error=NULL WHERE function_id=? AND kind=?",
            (generation,quota,self.system.boot,str(self.system.binary),row['function_id'],row['kind']))
        row=self.row(row['function_id'],row['kind'])
        try:
            await self.system.launch(row)
            deadline=time.monotonic()+10
            while True:
                row=self.row(row['function_id'],row['kind'])
                if self.system.mounted(row):break
                if not self.system.identity(row):raise StorageError('mount_start_failed')
                if time.monotonic()>=deadline:raise StorageError('mount_start_timeout')
                await asyncio.sleep(.02)
            data=await self.system.probe(row)
            self.db.execute("UPDATE volumes SET phase='mounted',usage=?,error=NULL WHERE function_id=? AND kind=?",
                (data['used'],row['function_id'],row['kind']))
            return self.row(row['function_id'],row['kind'])
        except (StorageError,OSError) as error:
            self.failed(row,error);raise

    def failed(self,row,error):
        code=str(error) if isinstance(error,StorageError) else 'storage_io_error'
        self.db.execute("UPDATE volumes SET phase='failed',error=? WHERE function_id=? AND kind=?",(code,row['function_id'],row['kind']))

    async def measure(self,row):
        try:
            result=await self.system.probe(row)
            self.db.execute('UPDATE volumes SET usage=?,error=NULL WHERE function_id=? AND kind=?',(result['used'],row['function_id'],row['kind']))
            return result
        except (StorageError,OSError) as error:self.failed(row,error);raise

    async def stop(self,row):
        if self.leased(row['function_id']):raise StorageError('volume_busy')
        self.db.execute("UPDATE volumes SET phase='stopping' WHERE function_id=? AND kind=?",(row['function_id'],row['kind']))
        try:
            if self.system.mounted(row) and self.system.identity(row):
                with suppress(StorageError):await self.measure(row)
            await self.system.stop(self.row(row['function_id'],row['kind']))
            self.db.execute("UPDATE volumes SET phase='unmounted',generation=NULL,daemon_quota=NULL,daemon_pid=NULL,daemon_birth=NULL,daemon_boot=NULL,daemon_binary=NULL,error=NULL WHERE function_id=? AND kind=?",(row['function_id'],row['kind']))
        except (StorageError,OSError) as error:self.failed(row,error);raise

    async def compensate(self,identifier):
        if self.leased(identifier):raise StorageError('volume_busy')
        errors=[]
        for row in self.rows(identifier):
            try:await self.stop(row)
            except (StorageError,OSError):errors.append(row['kind'])
        if errors:raise StorageError('cleanup_pending')
        pending=json.loads(self.function(identifier)['pending_json'] or '{}')
        await self.remove_created(identifier,pending)
        self.db.execute('UPDATE functions SET pending_json=NULL WHERE id=?',(identifier,))

    def created_volumes(self,identifier,value):
        created={}
        for kind,item in value.items():
            if item['enabled'] and not self.row(identifier,kind):
                backing,mount=self.system.paths({'function_id':identifier,'kind':kind})
                created[kind]={'backing':not backing.exists(),'mount':not mount.exists(),
                               'backing_parent':not backing.parent.exists(),'mount_parent':not mount.parent.exists()}
        return created

    async def remove_created(self,identifier,pending):
        # Never recursively delete a preparation's paths: a new file prevents abort.
        parents=set()
        for kind,created in pending.get('created',{}).items():
            row=self.row(identifier,kind)
            if row and (row['phase']!='unmounted' or row['quota']!=0):raise StorageError('cleanup_pending')
            backing,mount=self.system.paths({'function_id':identifier,'kind':kind})
            for name,path in [('backing',backing),('mount',mount)]:
                if created[name]:
                    try:
                        path.rmdir()
                        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                        try:os.fsync(fd)
                        finally:os.close(fd)
                    except FileNotFoundError:pass
                    except OSError:raise StorageError('preparation_not_empty') from None
                if created[name+'_parent']:parents.add(path.parent)
        for path in parents:
            try:
                path.rmdir()
                fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                try:os.fsync(fd)
                finally:os.close(fd)
            except FileNotFoundError:pass
            except OSError:raise StorageError('preparation_not_empty') from None
        with self.transaction():
            for kind in pending.get('created',{}):
                self.db.execute('DELETE FROM volumes WHERE function_id=? AND kind=? AND quota=0',(identifier,kind))

    async def probe_configuration(self,identifier,value):
        for row in self.rows(identifier):
            desired=value[row['kind']]['quota_mib']*MIB
            if row['phase']!='unmounted':await self.stop(row)
            if row['quota']:
                mounted=await self.mount(self.row(identifier,row['kind']))
                usage=(await self.measure(mounted))['used']
                await self.stop(mounted)
                if usage>desired:raise StorageError('quota_below_usage')
            candidate=await self.mount(self.row(identifier,row['kind']),desired)
            await self.stop(candidate)

    def preparation_extra(self,identifier,value):
        extra=0
        for kind,item in value.items():
            row=self.row(identifier,kind)
            if row or item['enabled']:extra+=max(0,item['quota_mib']*MIB-(row['quota'] if row else 0))
        if self.allocated()+extra>self.budget:raise StorageError('storage_budget')
        space=os.statvfs(self.root)
        if extra and space.f_bavail*space.f_frsize<self.reserve+extra:raise StorageError('storage_free_space')
        return extra

    # @spec docs/ADMISSION.md#configuration-de-stockage-en-deux-phases
    def configuration_operation(self,identifier,operation,installation):
        identifier=uuid(identifier);operation=uuid(operation);installation=uuid(installation)
        function=self.function(identifier)
        pending=json.loads(function['pending_json'] or '{}')
        if pending.get('operation')=='configuration-prepared' and pending['operation_id']==operation:
            if pending['installation_id']!=installation:raise StorageError('operation_owner')
            return {'function_id':identifier,'operation_id':operation,'installation_id':installation,
                    'state':pending['phase'],'configuration':pending['configuration'],
                    'expected_version':pending['expected_version'],'version':function['version']}
        row=self.db.execute('SELECT * FROM configuration_receipts WHERE function_id=? AND operation_id=?',(identifier,operation)).fetchone()
        if not row:raise StorageError('operation_unknown')
        if row['installation_id']!=installation:raise StorageError('operation_owner')
        return {'function_id':identifier,'operation_id':operation,'installation_id':installation,
                'state':row['decision'],'configuration':json.loads(row['configuration_json']),
                'expected_version':row['expected_version'],'version':row['version']}

    async def prepare_configuration(self,identifier,operation,installation,value,expected):
        identifier=uuid(identifier);operation=uuid(operation);installation=uuid(installation);value=configuration(value)
        if type(expected) is not int or expected<0:raise StorageError('invalid_version')
        existing=self.db.execute('SELECT * FROM functions WHERE id=?',(identifier,)).fetchone()
        if existing:
            try:result=self.configuration_operation(identifier,operation,installation)
            except StorageError as error:
                if str(error)!='operation_unknown':raise
            else:
                if result['configuration']!=value or result['expected_version']!=expected:raise StorageError('operation_conflict')
                return result
        elif expected!=0:raise StorageError('version_conflict')
        self.operation_available(operation)
        # The version remains monotone, even after abandoning a new empty function.
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO functions VALUES(?,'active',0,?,NULL)",(identifier,canonical(DEFAULT)))
        function=self.function(identifier);self.version(function,expected)
        if function['state']!='active':raise StorageError('function_archived')
        if function['pending_json']:raise StorageError('operation_pending')
        if self.leased(identifier):raise StorageError('volume_busy')
        pending={'operation':'configuration-prepared','operation_id':operation,'installation_id':installation,
                 'phase':'preparing','configuration':value,'expected_version':expected,
                 'created':self.created_volumes(identifier,value),'extra':self.preparation_extra(identifier,value)}
        with self.transaction():
            self.db.execute('UPDATE functions SET pending_json=? WHERE id=?',(canonical(pending),identifier))
            for kind in pending['created']:
                self.db.execute('INSERT INTO volumes(function_id,kind,quota,enabled) VALUES(?,?,0,0)',(identifier,kind))
        try:
            await self.probe_configuration(identifier,value)
            pending['phase']='prepared'
            self.db.execute('UPDATE functions SET pending_json=? WHERE id=?',(canonical(pending),identifier))
        except BaseException:
            await joined(self.resolve_configuration(identifier,operation,installation,'aborted'));raise
        return self.configuration_operation(identifier,operation,installation)

    def receipt(self,identifier,pending,decision):
        version=self.function(identifier)['version']+1
        self.db.execute('UPDATE functions SET pending_json=NULL,version=? WHERE id=?',(version,identifier))
        self.db.execute('INSERT INTO configuration_receipts VALUES(?,?,?,?,?,?,?) ON CONFLICT(function_id) DO UPDATE SET '
                        'operation_id=excluded.operation_id,installation_id=excluded.installation_id,configuration_json=excluded.configuration_json,'
                        'expected_version=excluded.expected_version,decision=excluded.decision,version=excluded.version',
                        (identifier,pending['operation_id'],pending['installation_id'],canonical(pending['configuration']),pending['expected_version'],decision,version))

    def operation_available(self,operation):
        if self.db.execute('SELECT 1 FROM configuration_receipts WHERE operation_id=?',(operation,)).fetchone():raise StorageError('operation_conflict')
        for row in self.db.execute('SELECT pending_json FROM functions WHERE pending_json IS NOT NULL'):
            if json.loads(row['pending_json']).get('operation_id')==operation:raise StorageError('operation_conflict')

    def abandon_unseen(self,identifier,operation,installation,value,expected):
        self.operation_available(operation)
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO functions VALUES(?,'active',0,?,NULL)",(identifier,canonical(DEFAULT)))
            function=self.function(identifier);self.version(function,expected)
            if function['state']!='active':raise StorageError('function_archived')
            if function['pending_json']:raise StorageError('operation_pending')
            if self.leased(identifier):raise StorageError('volume_busy')
            pending={'operation_id':operation,'installation_id':installation,'configuration':value,'expected_version':expected}
            self.receipt(identifier,pending,'aborted')
        return self.configuration_operation(identifier,operation,installation)

    async def resolve_configuration(self,identifier,operation,installation,decision,unseen=None):
        identifier=uuid(identifier);operation=uuid(operation);installation=uuid(installation)
        if unseen is not None:
            value=configuration(unseen['configuration']);expected=unseen['expected_version']
            if type(expected) is not int or expected<0:raise StorageError('invalid_version')
        try:result=self.configuration_operation(identifier,operation,installation)
        except StorageError as error:
            if decision!='aborted' or unseen is None or str(error) not in ('function_unknown','operation_unknown'):raise
            return self.abandon_unseen(identifier,operation,installation,value,expected)
        if unseen is not None and (result['configuration']!=value or result['expected_version']!=expected):raise StorageError('operation_conflict')
        if result['state'] in ('committed','aborted'):
            if result['state']!=decision:raise StorageError('operation_decided')
            return result
        if self.leased(identifier):raise StorageError('volume_busy')
        pending=json.loads(self.function(identifier)['pending_json'])
        if decision=='committed':
            if pending['phase']!='prepared':raise StorageError('preparation_incomplete')
            for row in self.rows(identifier):
                if row['phase']!='unmounted' or self.system.mounted(row):raise StorageError('cleanup_pending')
            with self.transaction():
                for row in self.rows(identifier):
                    item=pending['configuration'][row['kind']]
                    self.db.execute('UPDATE volumes SET quota=?,enabled=? WHERE function_id=? AND kind=?',
                                    (item['quota_mib']*MIB,int(item['enabled']),identifier,row['kind']))
                self.db.execute('UPDATE functions SET config_json=? WHERE id=?',(canonical(pending['configuration']),identifier))
                self.receipt(identifier,pending,decision)
        else:
            pending['phase']='aborting'
            self.db.execute('UPDATE functions SET pending_json=? WHERE id=?',(canonical(pending),identifier))
            for row in self.rows(identifier):await self.stop(row)
            await self.remove_created(identifier,pending)
            with self.transaction():self.receipt(identifier,pending,decision)
        return self.configuration_operation(identifier,operation,installation)

    async def configure(self,identifier,value,expected=None):
        identifier=uuid(identifier);value=configuration(value)
        with self.transaction():
            self.db.execute("INSERT OR IGNORE INTO functions VALUES(?,'active',0,?,NULL)",(identifier,canonical(DEFAULT)))
        function=self.function(identifier);self.version(function,expected)
        if function['state']!='active':raise StorageError('function_archived')
        if function['pending_json']:raise StorageError('operation_pending')
        if json.loads(function['config_json'])==value:return self.snapshot(identifier)
        if self.leased(identifier):raise StorageError('volume_busy')
        extra=self.preparation_extra(identifier,value);created=self.created_volumes(identifier,value)
        with self.transaction():
            self.db.execute('UPDATE functions SET pending_json=? WHERE id=?',(canonical({'operation':'configure','configuration':value,'extra':extra,'created':created}),identifier))
            for kind,item in value.items():
                if item['enabled']:self.db.execute("INSERT OR IGNORE INTO volumes(function_id,kind,quota,enabled) VALUES(?,?,0,0)",(identifier,kind))
        try:
            await self.probe_configuration(identifier,value)
            with self.transaction():
                for row in self.rows(identifier):
                    item=value[row['kind']]
                    self.db.execute('UPDATE volumes SET quota=?,enabled=? WHERE function_id=? AND kind=?',(item['quota_mib']*MIB,int(item['enabled']),identifier,row['kind']))
                self.db.execute('UPDATE functions SET version=version+1,config_json=?,pending_json=NULL WHERE id=?',(canonical(value),identifier))
        except BaseException:
            await joined(self.compensate(identifier));raise
        return self.snapshot(identifier)

    async def acquire(self,identifier,consumer,installation,value):
        identifier=uuid(identifier);consumer=uuid(consumer);installation=uuid(installation);value=configuration(value)
        function=self.function(identifier)
        if function['state']!='active':raise StorageError('function_archived')
        if function['pending_json']:raise StorageError('operation_pending')
        if json.loads(function['config_json'])!=value:raise StorageError('configuration_conflict')
        existing=self.db.execute('SELECT * FROM leases WHERE consumer_id=?',(consumer,)).fetchone()
        if existing and (existing['function_id']!=identifier or existing['installation_id']!=installation or json.loads(existing['config_json'])!=value):raise StorageError('lease_conflict')
        if existing:
            await self.check(consumer,installation)
            return {'consumer_id':consumer,**json.loads(existing['mounts_json'])}
        if not existing:self.db.execute('INSERT INTO leases VALUES(?,?,?,?,?)',(consumer,installation,identifier,canonical(value),'{}'))
        paths={};generations={}
        try:
            for kind,item in value.items():
                if not item['enabled']:continue
                row=self.row(identifier,kind)
                if not row or row['quota']!=item['quota_mib']*MIB or not row['enabled']:raise StorageError('configuration_conflict')
                row=await self.mount(row)
                _,mount=self.system.paths(row);paths['/'+kind]=str(mount);generations[kind]=row['generation']
            self.db.execute('UPDATE leases SET mounts_json=? WHERE consumer_id=?',(canonical({'paths':paths,'generations':generations}),consumer))
            return {'consumer_id':consumer,'paths':paths,'generations':generations}
        except BaseException:
            # No consumer may be created until a successful complete reply is received.
            if not existing:
                self.db.execute('DELETE FROM leases WHERE consumer_id=?',(consumer,))
                if not self.leased(identifier):
                    for row in self.rows(identifier):
                        with suppress(StorageError,OSError):await joined(self.stop(row))
            raise

    async def release(self,consumer,installation):
        consumer=uuid(consumer);installation=uuid(installation)
        row=self.db.execute('SELECT * FROM leases WHERE consumer_id=?',(consumer,)).fetchone()
        if not row:return {'released':True,'already_released':True}
        if row['installation_id']!=installation:raise StorageError('lease_owner')
        identifier=row['function_id'];self.db.execute('DELETE FROM leases WHERE consumer_id=?',(consumer,))
        errors=[]
        if not self.leased(identifier):
            for volume in self.rows(identifier):
                try:await self.stop(volume)
                except (StorageError,OSError):errors.append(volume['kind'])
        if errors:raise StorageError('cleanup_pending')
        return {'released':True,'already_released':False}

    async def check(self,consumer,installation):
        row=self.db.execute('SELECT * FROM leases WHERE consumer_id=?',(uuid(consumer),)).fetchone()
        if not row or row['installation_id']!=uuid(installation):raise StorageError('lease_unknown')
        leased=json.loads(row['mounts_json']);observations={}
        expected={kind for kind,item in json.loads(row['config_json']).items() if item['enabled']}
        if set(leased)!={'paths','generations'} or set(leased['generations'])!=expected or set(leased['paths'])!={'/'+kind for kind in expected}:
            raise StorageError('lease_needs_reconciliation')
        for kind,generation in leased.get('generations',{}).items():
            volume=self.row(row['function_id'],kind)
            if volume['generation']!=generation or volume['phase']!='mounted':raise StorageError('mount_changed')
            observations[kind]=await self.measure(volume)
        return {'healthy':True,'volumes':observations}

    async def archive(self,identifier,expected=None):
        function=self.function(identifier);self.version(function,expected)
        if function['pending_json']:raise StorageError('operation_pending')
        if function['state']=='archived':return self.snapshot(identifier)
        if function['state']!='active':raise StorageError('function_archived')
        if self.leased(identifier):raise StorageError('volume_busy')
        for row in self.rows(identifier):await self.stop(row)
        value=json.loads(function['config_json'])
        for item in value.values():item['enabled']=False
        with self.transaction():
            self.db.execute("UPDATE functions SET state='archived',version=version+1,config_json=? WHERE id=?",(canonical(value),identifier))
            self.db.execute('UPDATE volumes SET enabled=0 WHERE function_id=?',(identifier,))
        return self.snapshot(identifier)

    async def discard(self,identifier,operation,expected=None):
        function=self.function(identifier);self.version(function,expected)
        if function['pending_json']:raise StorageError('operation_pending')
        if self.leased(identifier):raise StorageError('volume_busy')
        if operation=='purge' and function['state']=='purged':return self.snapshot(identifier)
        if operation=='purge' and function['state']!='archived':raise StorageError('archive_required')
        if operation=='clear-cache' and function['state']!='active':raise StorageError('function_archived')
        if operation=='clear-cache' and not self.row(identifier,'cache'):return self.snapshot(identifier)
        for row in self.rows(identifier):await self.stop(row)
        pending={'operation':operation,'trash':str(uuid4()),'extra':0}
        self.db.execute('UPDATE functions SET pending_json=?,state=? WHERE id=?',(canonical(pending),'purging' if operation=='purge' else function['state'],identifier))
        await self.finish_discard(identifier,pending)
        return self.snapshot(identifier)

    async def finish_discard(self,identifier,pending):
        if self.leased(identifier):raise StorageError('volume_busy')
        source=self.root/'backings'/identifier
        if pending['operation']=='clear-cache':source=source/'cache'
        destination=self.root/'trash'/uuid(pending['trash'])
        if source.exists() and destination.exists():raise StorageError('cleanup_ambiguous')
        if source.exists():
            if not stat.S_ISDIR(source.lstat().st_mode):raise StorageError('unsafe_discard_path')
            # Moving a directory across parents also needs write permission on
            # that directory to update '..', even when its owner may chmod it.
            os.chmod(source,0o700,follow_symlinks=False)
            os.rename(source,destination)
            for path in (source.parent,destination.parent):
                fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(fd)
                finally:os.close(fd)
        await joined(asyncio.to_thread(erase,destination))
        if destination.exists():raise StorageError('cleanup_pending')
        fd=os.open(destination.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        if pending['operation']=='clear-cache':
            private_directory(source,create=not source.exists())
            with self.transaction():
                self.db.execute("UPDATE volumes SET usage=0,error=NULL WHERE function_id=? AND kind='cache'",(identifier,))
                self.db.execute('UPDATE functions SET pending_json=NULL,version=version+1 WHERE id=?',(identifier,))
        else:
            mount=self.root/'mounts'/identifier
            if mount.exists():
                for child in mount.iterdir():child.rmdir()
                mount.rmdir()
            with self.transaction():
                self.db.execute('DELETE FROM volumes WHERE function_id=?',(identifier,))
                self.db.execute("UPDATE functions SET state='purged',pending_json=NULL,version=version+1 WHERE id=?",(identifier,))

    async def recover(self):
        self.last_error=None
        await self.system.reap_probe()
        for function in self.db.execute('SELECT * FROM functions WHERE pending_json IS NOT NULL').fetchall():
            try:
                pending=json.loads(function['pending_json'])
                await self.recover_operation(function['id'],pending)
            except (StorageError,OSError,sqlite3.Error):self.last_error='recovery_pending'
        for row in self.db.execute('SELECT * FROM volumes').fetchall():
            try:
                if not self.leased(row['function_id']):await self.stop(row)
                elif row['phase']=='mounted':await self.measure(row)
                else:self.failed(row,StorageError('lease_needs_reconciliation'))
            except (StorageError,OSError,sqlite3.Error):self.last_error='recovery_pending'
        self.ready=True

    async def maintain(self):
        # Give waiting mutations a turn between volumes; a 64-volume sweep must
        # not monopolize the global lock for the sum of all probe deadlines.
        async with self.lock:
            await self.system.reap_probe()
            keys=[(r['function_id'],r['kind']) for r in self.db.execute("SELECT function_id,kind FROM volumes WHERE phase!='unmounted'")]
        for identifier,kind in keys:
            async with self.lock:
                row=self.row(identifier,kind)
                if not row or row['phase']=='unmounted':continue
                if not self.leased(identifier):
                    try:await self.stop(row)
                    except (StorageError,OSError):pass
                elif row['phase']=='mounted':
                    try:await self.measure(row)
                    except (StorageError,OSError):pass
            await asyncio.sleep(0)
        async with self.lock:
            identifiers=[r[0] for r in self.db.execute('SELECT id FROM functions WHERE pending_json IS NOT NULL')]
        for identifier in identifiers:
            async with self.lock:
                function=self.function(identifier)
                if function['pending_json'] and not self.leased(identifier):
                    try:
                        pending=json.loads(function['pending_json'])
                        await self.recover_operation(identifier,pending)
                    except (StorageError,OSError):pass
            await asyncio.sleep(0)
        async with self.lock:
            failed=self.db.execute("SELECT 1 FROM volumes WHERE phase='failed' LIMIT 1").fetchone()
            pending=self.db.execute('SELECT 1 FROM functions WHERE pending_json IS NOT NULL LIMIT 1').fetchone()
            self.last_error='recovery_pending' if failed or pending else None

    async def recover_operation(self,identifier,pending):
        if pending['operation']=='configure':await self.compensate(identifier)
        elif pending['operation']=='configuration-prepared':
            if pending['phase']=='aborting':
                await self.resolve_configuration(identifier,pending['operation_id'],pending['installation_id'],'aborted')
            else:
                for row in self.rows(identifier):
                    if row['phase']!='unmounted':await self.stop(row)
        elif pending['operation'] in ('purge','clear-cache'):await self.finish_discard(identifier,pending)
        else:raise StorageError('unknown_pending_operation')

    def close(self):
        self.closed=True;self.db.close();os.close(self.owner)
