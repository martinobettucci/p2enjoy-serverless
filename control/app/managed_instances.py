# @spec docs/BACKLOG.md#sls-040 | docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#instances-avec-baux-gérés
"""Docker instances whose lifetime owns a real durable storage lease."""
import asyncio
import time
from uuid import UUID,uuid4

from .instances import Instance,joined
from .storage_client import StorageError,volumes
from .validator import ValidationError


class ManagedInstance(Instance):
    def __init__(self,*,storage,storage_configuration,**kwargs):
        if 'mounts' in kwargs:raise ValidationError('managed_mounts_required')
        super().__init__(**kwargs)
        self.storage=storage;self.storage_configuration=volumes(storage_configuration)
        self.lease_possible=False;self.storage_lock=asyncio.Lock();self.managed_started=False
        self.managed_close_task=None;self.managed_invoking=False

    async def start(self):
        if self.managed_started or self.closing:raise ValidationError('instance_already_started')
        self.managed_started=True
        try:
            async with self.storage_lock:
                if self.closing:raise ValidationError('instance_stopped')
                self.lease_possible=True
                leased=await joined(self.storage.acquire(self.function_id,self.id,self.installation,self.storage_configuration))
                self.mounts=leased['paths']
            return await super().start()
        except BaseException:
            await self.close();raise

    async def storage_health(self):
        result=await self.storage.call('check',consumer_id=self.id,installation_id=self.installation)
        if result.get('healthy') is not True:raise StorageError('storage_unavailable')
        return result

    async def watch_storage(self):
        while True:
            await asyncio.sleep(.5)
            await self.storage_health()

    async def invoke(self,event,timeout_seconds,invocation_id=None):
        if self.managed_invoking or self.busy or self.closing or not self.ready.is_set():raise ValidationError('instance_unavailable')
        invocation_id=str(UUID(invocation_id)) if invocation_id else str(uuid4());started=time.monotonic()
        self.managed_invoking=True;invocation=None;watcher=None
        try:
            await self.storage_health()
            invocation=asyncio.create_task(super().invoke(event,timeout_seconds,invocation_id))
            watcher=asyncio.create_task(self.watch_storage())
            await asyncio.wait((invocation,watcher),return_when=asyncio.FIRST_COMPLETED)
            if watcher.done():
                watcher.result()
                raise ValidationError('storage_watch_stopped')
            result=invocation.result()
            if result['instance_available']:await self.storage_health()
            if watcher.done():watcher.result()
            return result
        except StorageError:
            removed=await self.close()
            result=await joined(invocation) if invocation else {
                'invocation_id':invocation_id,'instance_id':self.id,'handler_started':False,
                'logs':'','logs_truncated':False,'elapsed_seconds':round(time.monotonic()-started,6)}
            return {**result,'state':'failed','error':'storage_unavailable' if removed else 'cleanup_failed',
                    'instance_available':False,'container_removed':removed}
        except BaseException:
            async def finish():
                if invocation:
                    invocation.cancel()
                    await asyncio.gather(invocation,return_exceptions=True)
                await self.close()
            await joined(finish());raise
        finally:
            try:
                if watcher:
                    watcher.cancel()
                    await joined(asyncio.gather(watcher,return_exceptions=True))
            finally:self.managed_invoking=False

    async def close(self):
        self.closing=True;self.wake.set()
        if self.managed_close_task is None or (self.managed_close_task.done() and not self.managed_close_task.cancelled() and self.managed_close_task.result() is False):
            self.managed_close_task=asyncio.create_task(self.close_managed())
        return await joined(self.managed_close_task)

    async def close_managed(self):
        async with self.storage_lock:
            removed=await super().close()
            if removed and self.lease_possible:
                try:await self.storage.release_confirmed(self.function_id,self.id,self.installation)
                except StorageError:removed=False
                else:self.lease_possible=False
            self.removed=removed;self.cleanup_error=not removed
            return removed
