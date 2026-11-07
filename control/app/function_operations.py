# @spec docs/BACKLOG.md#sls-050 | docs/ADMISSION.md#raccordement-des-mutations-du-contrôle
# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
"""Durable public mutations and confirmation of the actual host volume agent."""
import asyncio
from contextlib import asynccontextmanager,suppress
import json
import logging
import sqlite3
import time

from fastapi import HTTPException

from .instances import joined
from .storage_client import StorageClient,StorageError,volumes

logger=logging.getLogger('p2enjoy.control')


def storage_configuration(config):
    return volumes({kind:config['storage'][kind] for kind in ('data','cache')})


def storage_failure(error):
    code=str(error)
    if code in ('quota_below_usage','invalid_configuration'):
        return HTTPException(422,'Le quota demandé est inférieur aux données présentes ou invalide.')
    if code in ('storage_budget','storage_free_space'):
        return HTTPException(507,'Le budget ou la marge libre de stockage est insuffisant.')
    if code in ('volume_busy','operation_pending','version_conflict','configuration_conflict','function_archived'):
        return HTTPException(409,'Le stockage de la fonction est occupé ou a changé. Relisez son état avant de poursuivre.')
    return HTTPException(503,'Le stockage est temporairement indisponible ; la modification ne peut pas être confirmée.')


class FunctionOperations:
    def __init__(self,settings,database):
        self.database=database
        self.storage=StorageClient('/storage-agent/agent.sock',settings.storage_root_host)
        self.installation=None;self.task=None;self.live={};self.closing=False;self.agent_ready=False;self.cleanup_error=False
        self.execution=None;self.discards=None;self.resolving=set()

    def minimum_budget(self,db,function_id,config):
        if self.execution:self.execution.minimum_budget(db,function_id,config)

    async def ready(self,installation):
        self.installation=installation
        await self.sweep()
        self.task=asyncio.create_task(self.maintain())

    async def close(self):
        self.closing=True
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):await joined(self.task)
        owners=set(self.live.values())-{asyncio.current_task()}
        for owner in owners:owner.cancel()
        if owners:await joined(asyncio.gather(*owners,return_exceptions=True))

    @staticmethod
    def function_available(db,function,own_operation=None):
        row=db.execute('SELECT id FROM function_operations WHERE function_id=?',(function,)).fetchone()
        if row and row['id']!=own_operation:raise HTTPException(409,'Une opération de stockage est en cours pour cette fonction.')

    @staticmethod
    def service_available(db,service):
        if db.execute('SELECT 1 FROM function_operations WHERE service_id=?',(service,)).fetchone():
            raise HTTPException(409,'Une opération de fonction doit être terminée avant de modifier ce service.')

    def reserve(self,db,operation,function,service,configuration=None,*,kind=None):
        identifier=function['id'];self.function_available(db,identifier)
        db.execute('INSERT INTO function_operations VALUES (?,?,?,?,\'undecided\',?,NULL,?,?,?,NULL)',
            (operation,identifier,service['id'],kind or ('configuration' if configuration is not None else 'archive'),
             json.dumps(volumes(configuration)) if configuration is not None else None,
             function.get('updated_at'),service['updated_at'],time.time()))

    def verify(self,db,operation,function,service):
        row=db.execute('SELECT * FROM function_operations WHERE id=?',(operation,)).fetchone()
        if not row or row['decision']!='undecided':raise HTTPException(409,'Cette opération ne peut plus publier sa modification.')
        if (row['function_id']!=function['id'] or row['service_id']!=service['id'] or
                row['expected_function_version']!=function.get('updated_at') or row['expected_service_version']!=service['updated_at']):
            raise HTTPException(409,'La fonction ou le service a changé pendant cette opération.')
        return dict(row)

    @staticmethod
    def commit(db,operation):
        if db.execute("UPDATE function_operations SET decision='commit',error_code=NULL WHERE id=? AND decision='undecided'",(operation,)).rowcount!=1:
            raise HTTPException(409,'La décision de stockage a changé.')

    def summary(self,function):
        return self.database.one('SELECT id,kind,decision,error_code FROM function_operations WHERE function_id=?',(function,))

    async def snapshot(self,function):
        try:result=await self.storage.call('status',function_id=function)
        except StorageError as error:
            if str(error)=='function_unknown':return None
            raise
        if (result.get('id')!=function or type(result.get('version')) is not int or result['version']<0 or
                result.get('state') not in ('active','archived','purging','purged') or type(result.get('pending')) is not bool or
                type(result.get('leases')) is not int or result['leases']<0):raise StorageError('storage_protocol')
        return result

    def receipt(self,row,result,decision):
        expected={'function_id':row['function_id'],'operation_id':row['id'],'installation_id':self.installation,
                  'configuration':json.loads(row['configuration_json']),'expected_version':row['storage_version']}
        if any(result.get(key)!=value for key,value in expected.items()):raise StorageError('storage_protocol',uncertain=True)
        version=row['storage_version']+(0 if decision=='prepared' else 1)
        if result.get('state')!=decision or type(result.get('version')) is not int or result['version']!=version:
            raise StorageError('storage_protocol',uncertain=True)

    async def prepare(self,operation):
        row=self.database.one('SELECT * FROM function_operations WHERE id=?',(operation,))
        if not row or row['decision']!='undecided':raise StorageError('operation_conflict')
        if self.execution:await self.execution.drain(row['function_id'])
        snapshot=await self.snapshot(row['function_id'])
        if snapshot:
            allowed=(('archived','purged') if row['kind']=='purge' else
                     ('active',) if row['kind'] in ('configuration','clear-cache') else ('active','archived','purged'))
            if snapshot['state'] not in allowed:raise StorageError('function_archived')
            if snapshot['pending']:raise StorageError('operation_pending')
            if snapshot['leases']:raise StorageError('volume_busy')
        version=snapshot['version'] if snapshot else 0
        with self.database.transaction() as db:
            if db.execute("UPDATE function_operations SET storage_version=? WHERE id=? AND decision='undecided' AND storage_version IS NULL",(version,operation)).rowcount!=1:
                raise StorageError('operation_conflict')
            if row['kind'] in ('clear-cache','purge'):
                db.execute('UPDATE storage_commands SET storage_absent=? WHERE id=?',(int(snapshot is None),operation))
        row['storage_version']=version
        if row['kind']=='configuration':
            result=await joined(self.storage.call('prepare-configuration',function_id=row['function_id'],operation_id=operation,
                installation_id=self.installation,configuration=json.loads(row['configuration_json']),expected_version=version))
            self.receipt(row,result,'prepared')

    async def resolve(self,operation):
        if operation in self.resolving:return False
        self.resolving.add(operation)
        try:return await self._resolve(operation)
        finally:self.resolving.discard(operation)

    async def _resolve(self,operation):
        try:
            # A publication without volume changes owns no storage intention.
            # Confirm absence by reading; taking a writer lock here could mask
            # an already published revision with a false abandonment response.
            if not self.database.one('SELECT 1 FROM function_operations WHERE id=?',(operation,)):return True
            with self.database.transaction() as db:
                db.execute("UPDATE function_operations SET decision='abort' WHERE id=? AND decision='undecided'",(operation,))
                raw=db.execute('SELECT * FROM function_operations WHERE id=?',(operation,)).fetchone()
                if not raw:return True
                row=dict(raw)
            if row['kind']=='configuration':
                if row['storage_version'] is None:
                    if row['decision']!='abort':raise StorageError('operation_conflict')
                else:
                    fields={'function_id':row['function_id'],'operation_id':operation,'installation_id':self.installation}
                    if row['decision']=='abort':fields.update(configuration=json.loads(row['configuration_json']),expected_version=row['storage_version'])
                    result=await self.storage.call(row['decision']+'-configuration',**fields)
                    self.receipt(row,result,'committed' if row['decision']=='commit' else 'aborted')
            elif row['kind'] in ('clear-cache','purge'):
                if self.discards is None:raise StorageError('storage_protocol')
                return await self.discards.resolve(row)
            elif row['kind']=='archive' and row['decision']=='commit':
                snapshot=await self.snapshot(row['function_id'])
                if snapshot and snapshot['state'] not in ('archived','purged'):
                    await self.storage.call('archive',function_id=row['function_id'],expected_version=row['storage_version'])
                    snapshot=await self.snapshot(row['function_id'])
                if snapshot and (snapshot['state'] not in ('archived','purged') or snapshot['pending'] or snapshot['leases'] or
                        any(value['phase']!='unmounted' for value in snapshot['volumes'].values())):raise StorageError('storage_cleanup_pending')
            elif row['kind']!='archive':raise StorageError('storage_protocol')
            with self.database.transaction() as db:db.execute('DELETE FROM function_operations WHERE id=? AND decision=?',(operation,row['decision']))
            return True
        except (StorageError,sqlite3.Error) as error:
            code=str(error) if isinstance(error,StorageError) else 'control_database_unavailable'
            self.cleanup_error=True
            if isinstance(error,StorageError) and error.uncertain:self.agent_ready=False
            with suppress(sqlite3.Error):
                with self.database.transaction() as db:
                    db.execute('UPDATE function_operations SET error_code=? WHERE id=?',(code,operation))
                    db.execute('UPDATE storage_commands SET error_code=? WHERE id=?',(code,operation))
            logger.error(json.dumps({'event':'function.storage_pending','operation_id':operation,'error_code':code}))
            return False

    @asynccontextmanager
    async def responsibility(self,operation,*,pending_response=False):
        if self.closing:raise HTTPException(503,'Le contrôle est en cours d’arrêt.')
        self.live[operation]=asyncio.current_task();failed=False
        try:yield
        except StorageError as error:
            failed=True;raise storage_failure(error) from None
        except BaseException:
            failed=True;raise
        finally:
            try:resolved=await joined(self.resolve(operation))
            finally:self.live.pop(operation,None)
            if not resolved and not failed and not pending_response:
                row=self.database.one('SELECT function_id,decision FROM function_operations WHERE id=?',(operation,))
                committed=bool(row and row['decision']=='commit')
                headers={'X-Serverless-Operation-ID':operation,'X-Serverless-Mutation-Committed':str(committed).lower()}
                if row:headers['X-Serverless-Function-ID']=row['function_id']
                message=('La modification est enregistrée ; la confirmation du stockage est en attente. Relisez la fonction avant une nouvelle tentative.'
                    if committed else 'La modification est abandonnée ; son nettoyage de stockage doit être confirmé avant une nouvelle tentative.')
                raise HTTPException(503,message,headers=headers)

    async def sweep(self):
        for row in self.database.all('SELECT id FROM function_operations ORDER BY created_at,id'):
            if row['id'] not in self.live:await self.resolve(row['id'])
        try:
            health=await self.storage.call('health')
            self.agent_ready=health.get('ready') is True and health.get('failed_volumes')==0
        except StorageError:self.agent_ready=False
        self.cleanup_error=bool(self.database.one('SELECT 1 FROM function_operations WHERE error_code IS NOT NULL LIMIT 1'))

    async def maintain(self):
        while True:
            await asyncio.sleep(5)
            try:await self.sweep()
            except Exception:
                self.cleanup_error=True
                logger.error(json.dumps({'event':'function.storage_maintenance_failed'}))
