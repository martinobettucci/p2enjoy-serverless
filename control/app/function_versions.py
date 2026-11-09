# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md | docs/SCHEMA.md#autorité-des-versions-et-promotions
"""Function-scoped code identities, availability and explicit default selection."""
from contextlib import closing
import json
import re
import time
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request

from .db import audit
from .invocation_http import InvocationError
from .models import VersionDisposition

CODE_HASH = re.compile(r'[0-9a-f]{64}', re.ASCII)


def checked_hash(value):
    if not isinstance(value,str) or not CODE_HASH.fullmatch(value):
        raise InvocationError(404,'version_unavailable')
    return value


def default_code_hash(db,function):
    row=db.execute('SELECT code_hash FROM revisions WHERE id=? AND function_id=?',
                   (function['active_revision_id'],function['id'])).fetchone()
    return row['code_hash'] if row else None


def selected_revision(db,function,code_hash=None):
    """Call only after checking the function's scope; no fallback for a selector."""
    if code_hash is None:
        row=db.execute('''SELECT r.* FROM revisions r JOIN function_versions v
            ON v.function_id=r.function_id AND v.code_hash=r.code_hash
            WHERE r.id=? AND r.function_id=? AND r.deleted_at IS NULL
              AND r.stored_bytes>0 AND v.state='available' ''',
            (function['active_revision_id'],function['id'])).fetchone()
        return dict(row) if row else None
    checked_hash(code_hash)
    row=db.execute('''SELECT r.* FROM function_versions v JOIN revisions r ON r.id=v.revision_id
        AND r.function_id=v.function_id AND r.code_hash=v.code_hash
        WHERE v.function_id=? AND v.code_hash=? AND v.state='available'
          AND r.deleted_at IS NULL AND r.stored_bytes>0''',(function['id'],code_hash)).fetchone()
    if not row:raise InvocationError(404,'version_unavailable')
    return dict(row)


def live_function(db,key):
    row=db.execute('''SELECT f.* FROM functions f
        JOIN services s ON s.id=f.service_id AND s.deleted_at IS NULL
        JOIN namespaces n ON n.id=s.namespace_id AND n.deleted_at IS NULL
        WHERE f.id=? AND f.deleted_at IS NULL''',(str(key),)).fetchone()
    if not row:raise HTTPException(404,'Fonction ou service introuvable.')
    return dict(row)


def required_version(request,function):
    expected=request.headers.get('if-match')
    if expected is None:raise HTTPException(428,'If-Match est obligatoire pour cette opération.')
    if expected!=str(function['updated_at']):
        raise HTTPException(409,'La fonction a changé. Relisez sa version avant de poursuivre.')


def promotion_right(function,code_hash):
    return ('create' if function and function['first_promoted_at'] is None and
            function['first_published_code_hash']==code_hash else 'update')


def select_default(db,function,revision,now):
    config=json.loads(function['config_json'])
    if revision:config.update(handler=revision['handler'],runtime=revision['runtime'])
    db.execute('''UPDATE functions SET active_revision_id=?,config_json=?,updated_at=?,
        first_promoted_at=CASE WHEN ? IS NOT NULL THEN coalesce(first_promoted_at,?) ELSE first_promoted_at END
        WHERE id=?''',(revision['id'] if revision else None,json.dumps(config),now,
                       revision['id'] if revision else None,now,function['id']))


class FunctionVersions:
    def __init__(self,deployments):
        self.deployments=deployments
        self.database,self.identity=deployments.database,deployments.identity
        self.operations=deployments.operations

    async def authorization(self,request,key,right):
        function=self.database.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        authorization=await self.identity.operation(request,function['service_id'] if function else '',right,str(key))
        if not function:raise HTTPException(404,'Fonction introuvable.')
        return authorization

    def checked_function(self,db,request,key,authorization,right,*,mutation=True):
        function=live_function(db,key)
        self.identity.recheck(db,authorization,function['service_id'],right,str(key))
        if mutation:
            required_version(request,function)
            self.operations.function_available(db,str(key))
        return function

    async def promote(self,request,key,code_hash,*,legacy=False):
        initial=self.database.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        right='update' if legacy else promotion_right(initial,code_hash)
        authorization=await self.authorization(request,key,right)
        with self.database.transaction() as db:
            function=self.checked_function(db,request,key,authorization,right)
            current_right='update' if legacy else promotion_right(function,code_hash)
            if current_right!=right:
                self.identity.recheck(db,authorization,function['service_id'],current_right,str(key))
            revision=selected_revision(db,function,code_hash)
            changed=default_code_hash(db,function)!=code_hash
            if changed:
                now=max(time.time(),function['updated_at']+.000001)
                select_default(db,function,revision,now)
                audit(db,authorization.actor,'function.rollback' if legacy else 'function.version_promote',
                      str(key),function['service_id'],{'code_hash':code_hash,'revision_id':revision['id']})
                function=live_function(db,key)
            else:
                # Equivalent historical aliases do not restart a pool or rewrite a pointer.
                revision=selected_revision(db,function)
            return {'function_id':str(key),'code_hash':code_hash,'revision_id':revision['id'],
                    'default_code_hash':code_hash,'function_version':function['updated_at'],'changed':changed}

    async def disposition(self,request,key,code_hash,state,data):
        authorization=await self.authorization(request,key,'update')
        with self.database.transaction() as db:
            function=self.checked_function(db,request,key,authorization,'update')
            checked_hash(code_hash)
            version=db.execute('SELECT * FROM function_versions WHERE function_id=? AND code_hash=?',
                               (str(key),code_hash)).fetchone()
            if not version:raise InvocationError(404,'version_unavailable')
            if state=='available' and version['state']=='deleted':
                raise HTTPException(409,'Le code a été supprimé. Réimportez ce hash explicitement.')
            replacement=data.replacement_code_hash
            active=default_code_hash(db,function)==code_hash
            if (replacement or data.disable_default) and (not active or state=='available'):
                raise HTTPException(422,'Un remplacement concerne seulement le retrait de la cible courante.')
            if replacement==code_hash:raise HTTPException(422,'La version de remplacement doit être différente.')
            revision=selected_revision(db,function,replacement) if replacement else None
            if active and state!='available' and not (revision or data.disable_default):
                raise HTTPException(409,'Choisissez un autre hash disponible ou désactivez explicitement la cible courante.')
            if state=='archived' and version['state']=='deleted':
                raise HTTPException(409,'Une version supprimée ne peut pas être archivée.')
            changed=version['state']!=state
            if changed:
                if state=='available':
                    retained=db.execute('SELECT 1 FROM revisions WHERE id=? AND deleted_at IS NULL AND stored_bytes>0',
                                        (version['revision_id'],)).fetchone()
                    if not retained:raise HTTPException(409,'Le code de cette archive n’est plus conservé.')
                now=max(time.time(),function['updated_at']+.000001)
                if active and state!='available':select_default(db,function,revision,now)
                else:db.execute('UPDATE functions SET updated_at=? WHERE id=?',(now,str(key)))
                db.execute('UPDATE function_versions SET state=?,updated_at=? WHERE function_id=? AND code_hash=?',
                           (state,now,str(key),code_hash))
                audit(db,authorization.actor,{'available':'version.restore','archived':'version.archive','deleted':'version.delete'}[state],
                      str(key),function['service_id'],{'code_hash':code_hash,'replacement_code_hash':replacement,
                                                       'disable_default':data.disable_default})
                function=live_function(db,key)
            result={'function_id':str(key),'code_hash':code_hash,'state':state,'changed':changed,
                    'function_version':function['updated_at'],'default_code_hash':default_code_hash(db,function)}
        if state=='deleted':
            await self.deployments.clean()
            result['cleanup_pending']=bool(self.deployments.cleanup_error or self.database.one(
                'SELECT 1 FROM revisions WHERE function_id=? AND code_hash=? AND (deleted_at IS NULL OR stored_bytes>0)',
                (str(key),code_hash)))
        return result

    async def catalogue(self,request,key,limit,offset):
        authorization=await self.authorization(request,key,'read')
        with closing(self.database.connect()) as db:
            db.execute('BEGIN')
            function=self.checked_function(db,request,key,authorization,'read',mutation=False)
            current=default_code_hash(db,function)
            total=db.execute('SELECT count(*) FROM function_versions WHERE function_id=?',(str(key),)).fetchone()[0]
            rows=db.execute('''SELECT v.code_hash,v.revision_id,v.created_at,v.updated_at,v.state,
                r.handler,r.runtime,r.architecture,r.image_id,r.archive_sha256,r.events_json,
                (SELECT count(*) FROM revisions a WHERE a.function_id=v.function_id AND a.code_hash=v.code_hash) AS revision_count,
                (SELECT coalesce(sum(stored_bytes),0) FROM revisions a WHERE a.function_id=v.function_id AND a.code_hash=v.code_hash) AS stored_bytes
                FROM function_versions v JOIN revisions r ON r.id=v.revision_id
                WHERE v.function_id=? ORDER BY v.created_at DESC,v.code_hash LIMIT ? OFFSET ?''',
                (str(key),limit,offset)).fetchall()
            items=[]
            for row in rows:
                item=dict(row);item['events']=json.loads(item.pop('events_json'));item['active']=item['code_hash']==current
                items.append(item)
            return {'function_id':str(key),'service_id':function['service_id'],'active_revision_id':function['active_revision_id'],
                    'active_code_hash':current,'first_published_code_hash':function['first_published_code_hash'],
                    'first_promoted_at':function['first_promoted_at'],'function_version':function['updated_at'],
                    'items':items,'total':total,'limit':limit,'offset':offset}

    def routes(self):
        api=APIRouter(prefix='/functions')

        @api.get('/{key}/versions')
        async def catalogue(request:Request,key:UUID,limit:int=Query(5,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
            return await self.catalogue(request,key,limit,offset)

        @api.post('/{key}/versions/{code_hash}/promote')
        async def promote(request:Request,key:UUID,code_hash:str):
            return await self.promote(request,key,code_hash)

        @api.post('/{key}/versions/{code_hash}/archive')
        async def archive(request:Request,key:UUID,code_hash:str,data:VersionDisposition):
            return await self.disposition(request,key,code_hash,'archived',data)

        @api.post('/{key}/versions/{code_hash}/restore')
        async def restore(request:Request,key:UUID,code_hash:str):
            return await self.disposition(request,key,code_hash,'available',VersionDisposition())

        @api.delete('/{key}/versions/{code_hash}')
        async def delete(request:Request,key:UUID,code_hash:str,data:VersionDisposition):
            return await self.disposition(request,key,code_hash,'deleted',data)

        return api
