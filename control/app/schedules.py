# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULES.md#réalisation-du-moteur-et-migration-009 | docs/SCHEMA.md
"""Durable UTC schedule ownership and authorized, bounded observations."""
import asyncio
from contextlib import closing, suppress
from dataclasses import dataclass
import json
import logging
import sqlite3
import time
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from .auth import Actor
from .invocation_http import InvocationError
from .schedule_calendar import boundary, compile_cron, next_firing, window_slots

logger = logging.getLogger('p2enjoy.control')


@dataclass(frozen=True)
class ScheduleAuthorization:
    firing_id: str

    @property
    def actor(self):
        return Actor('schedule', self.firing_id)


def check_schedule(db, call, function):
    """Private capability is minted only by the scheduler, never from HTTP input."""
    firing = db.execute('''SELECT t.*,g.retired_at FROM schedule_firings t
        JOIN schedule_generations g ON g.id=t.generation_id
        WHERE t.id=? AND t.function_id=? AND t.state IN ('claimed','dispatched')''',
        (call.authorization.firing_id, function['id'])).fetchone()
    if (not firing or firing['retired_at'] is not None or
            firing['code_hash'] != call.requested_code_hash or
            (firing['invocation_id'] is not None and firing['invocation_id'] != call.id)):
        raise InvocationError(409, 'schedule_changed')
    revision = db.execute('SELECT code_hash FROM revisions WHERE id=?', (function['active_revision_id'],)).fetchone()
    if not revision or revision['code_hash'] != firing['code_hash']:
        raise InvocationError(409, 'schedule_changed')
    return firing


class Schedules:
    def __init__(self, execution):
        self.execution = execution
        self.db, self.identity = execution.db, execution.identity
        self.task = None
        self.closing = False
        self.maintenance_error = False
        self.recovery_until = 0

    async def ready(self):
        self.recovery_until = boundary(time.time())
        with self.db.transaction() as db:
            db.execute('INSERT OR IGNORE INTO schedule_cursor VALUES(1,?)', (self.recovery_until,))
            db.execute("""UPDATE schedule_firings SET state='failed',error_code='control_interrupted',completed_at=?
                WHERE state='claimed' AND invocation_id IS NULL""", (time.time(),))
        self.task = asyncio.create_task(self.maintain())

    def finish(self, db):
        # An earlier dispatch failure may leave a claim with no invocation. It
        # stays terminal rather than being sent on a later maintenance pass.
        db.execute("UPDATE schedule_firings SET state='failed',error_code='execution_unavailable',completed_at=? WHERE state='claimed' AND invocation_id IS NULL",(time.time(),))
        rows = db.execute('''SELECT t.id,i.state,i.error_code,i.http_status FROM schedule_firings t
            JOIN invocations i ON i.id=t.invocation_id
            WHERE t.completed_at IS NULL AND i.completed_at IS NOT NULL''').fetchall()
        for row in rows:
            state = 'succeeded' if row['state'] == 'succeeded' else (
                'refused_capacity' if row['error_code'] in ('queue_full', 'queue_timeout', 'minimum_budget_exceeded')
                else 'refused_changed' if row['error_code'] == 'schedule_changed'
                else 'failed')
            db.execute('UPDATE schedule_firings SET state=?,error_code=?,completed_at=? WHERE id=?',
                       (state, row['error_code'], time.time(), row['id']))

    def claim_window(self, window, downtime):
        claimed = []
        now = time.time()
        with self.db.transaction(busy_timeout=0) as db:
            cursor = db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
            if window != cursor + 300:
                return []
            generations = db.execute('''SELECT * FROM schedule_generations
                WHERE activated_at<? AND (retired_at IS NULL OR retired_at>?) ORDER BY id''',
                (window, window - 300)).fetchall()
            for generation in generations:
                for index, declaration in enumerate(json.loads(generation['events_json'])['schedules']):
                    if not declaration['enabled']:
                        continue
                    slots = window_slots(compile_cron(declaration['cron']), window,
                                         generation['activated_at'], generation['retired_at'])
                    if not slots:
                        continue
                    # Overlap is per declaration of this function, across generations
                    # with the same cron/index; a changed expression is a new schedule.
                    overlap = db.execute('''SELECT 1 FROM schedule_firings t
                        WHERE t.function_id=? AND t.schedule_index=? AND t.expression=?
                        AND t.completed_at IS NULL''',
                        (generation['function_id'], index, declaration['cron'])).fetchone()
                    state = ('skipped_downtime' if downtime else 'refused_changed' if generation['retired_at'] is not None
                             else 'skipped_overlap' if overlap else 'claimed')
                    identifier = str(uuid4())
                    db.execute('''INSERT INTO schedule_firings
                        (id,generation_id,function_id,schedule_index,origin,expression,code_hash,nominal_at,
                         window_at,coalesced,state,claimed_at,completed_at,delay_seconds)
                        VALUES(?,?,?,?,'manifest',?,?,?,?,?,?,?,?,?)''',
                        (identifier,generation['id'],generation['function_id'],index,declaration['cron'],
                         generation['code_hash'],slots[-1],window,len(slots),state,now,
                         None if state == 'claimed' else now,now-slots[-1]))
                    if state == 'claimed':
                        claimed.append(identifier)
            db.execute('UPDATE schedule_cursor SET window_at=? WHERE singleton=1', (window,))
        return claimed

    def dispatch(self, identifier):
        firing = self.db.one('SELECT * FROM schedule_firings WHERE id=?', (identifier,))
        call = None
        try:
            call = self.execution.receive(firing['function_id'], ScheduleAuthorization(identifier),
                                          'POST', '/', None, '127.0.0.1', firing['code_hash'])
            headers = [(b'content-type', b'application/json'), (b'x-p2enjoy-trigger', b'schedule'),
                       (b'x-p2enjoy-schedule-slot', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(firing['nominal_at'])).encode())]
            self.execution.enqueue(call, headers, b'', b'{}')
        except (HTTPException, sqlite3.Error) as error:
            code = error.detail if isinstance(error, InvocationError) else 'execution_unavailable'
            capacity = code in ('queue_full', 'queue_timeout', 'schedule_capacity')
            state = 'refused_capacity' if capacity else 'refused_changed' if code == 'schedule_changed' else 'refused_unavailable'
            if call and not call.admitted:
                # Ownership stays with execution if SQL is temporarily unavailable.
                with suppress(sqlite3.Error):
                    self.execution.reject(call, error.status_code if isinstance(error, HTTPException) else 503, code)
            with self.db.transaction(busy_timeout=0) as db:
                db.execute('UPDATE schedule_firings SET state=?,error_code=?,completed_at=? WHERE id=? AND invocation_id IS NULL',
                           (state, code, time.time(), identifier))

    async def tick(self):
        now = time.time()
        with self.db.transaction(busy_timeout=0) as db:
            self.finish(db)
        current = boundary(now)
        cursor = self.db.one('SELECT window_at FROM schedule_cursor WHERE singleton=1')['window_at']
        # Bound recovery work; the persistent cursor allows continuation next tick.
        for window in range(cursor + 300, min(current, cursor + 20 * 300) + 1, 300):
            downtime = window <= self.recovery_until or now - window > 5
            for identifier in self.claim_window(window, downtime):
                self.dispatch(identifier)
        with self.db.transaction(busy_timeout=0) as db:
            db.execute('DELETE FROM schedule_firings WHERE completed_at<?', (now - 7 * 86400,))
            db.execute('''DELETE FROM schedule_firings WHERE id IN
                (SELECT id FROM schedule_firings WHERE completed_at IS NOT NULL
                 ORDER BY completed_at DESC,id DESC LIMIT -1 OFFSET 10000)''')
            db.execute('''DELETE FROM schedule_generations WHERE retired_at<? AND NOT EXISTS
                (SELECT 1 FROM schedule_firings WHERE generation_id=schedule_generations.id)''', (now - 7 * 86400,))

    async def maintain(self):
        while not self.closing:
            try:
                await self.tick()
                self.maintenance_error = False
            except Exception as error:
                self.maintenance_error = True
                logger.error(json.dumps({'event':'schedules.maintenance_failed','error_type':type(error).__name__}))
            await asyncio.sleep(.5)

    async def close(self):
        self.closing = True
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task

    async def authorize(self, request, key):
        function = self.db.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL', (str(key),))
        authorization = await self.identity.operation(request, function['service_id'] if function else '', 'read', str(key))
        return authorization

    def authorized_function(self, db, authorization, key):
        row = db.execute('''SELECT f.* FROM functions f JOIN services s ON s.id=f.service_id
            JOIN namespaces n ON n.id=s.namespace_id
            WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL AND n.deleted_at IS NULL''', (str(key),)).fetchone()
        self.identity.recheck(db, authorization, row['service_id'] if row else '', 'read', str(key))
        if not row:
            raise HTTPException(404, 'Fonction introuvable.')
        return row

    def routes(self):
        api = APIRouter()

        @api.get('/api/functions/{key}/schedules')
        async def declarations(request:Request,key:UUID):
            authorization = await self.authorize(request,key)
            with closing(self.db.connect()) as db:
                db.execute('BEGIN')
                self.authorized_function(db,authorization,key)
                generation = db.execute('SELECT * FROM schedule_generations WHERE function_id=? AND retired_at IS NULL',(str(key),)).fetchone()
                now = time.time()
                cursor = db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
                # A nominal earlier than now may still belong to the next
                # unprocessed five-minute window. Never forecast a recovered gap.
                oldest = boundary(now) - (300 if now - boundary(now) <= 5 else 0)
                after = max(cursor,self.recovery_until,oldest,generation['activated_at'] if generation else now)
                items = []
                if generation:
                    for index, item in enumerate(json.loads(generation['events_json'])['schedules']):
                        last = db.execute('''SELECT * FROM schedule_firings WHERE generation_id=? AND schedule_index=?
                            ORDER BY window_at DESC,id DESC LIMIT 1''',(generation['id'],index)).fetchone()
                        items.append(dict(item, index=index, origin='manifest', code_hash=generation['code_hash'],
                                          activated_at=generation['activated_at'],
                                          next=next_firing(compile_cron(item['cron']),after) if item['enabled'] else None,
                                          last_firing=dict(last) if last else None))
                return {'function_id':str(key),'timezone':'UTC','resolution_seconds':300,'items':items}

        @api.get('/api/functions/{key}/schedule-firings')
        async def firings(request:Request,key:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
            authorization = await self.authorize(request,key)
            with closing(self.db.connect()) as db:
                db.execute('BEGIN')
                self.authorized_function(db,authorization,key)
                rows = db.execute('''SELECT * FROM schedule_firings WHERE function_id=?
                    ORDER BY window_at DESC,id DESC LIMIT ? OFFSET ?''',(str(key),limit,offset)).fetchall()
                total = db.execute('SELECT count(*) FROM schedule_firings WHERE function_id=?',(str(key),)).fetchone()[0]
                return {'items':[dict(row) for row in rows],'total':total,'limit':limit,'offset':offset}

        return api
