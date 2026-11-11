# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md | docs/SCHEMA.md#commandes-publiques-de-stockage
"""Authorized storage observations, durable discard commands and archived functions."""
from contextlib import closing
import time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter,HTTPException,Query,Request
from fastapi.responses import JSONResponse
from pydantic import Field

from .db import audit
from .deployments import blocking,required_version
from .artifacts import ArtifactError
from .models import Strict
from .storage_client import StorageError
from .validator import ValidationError


class CacheClear(Strict):
    operation_id:UUID


class ArchivePurge(CacheClear):
    confirm_name:str=Field(min_length=1,max_length=63)


class StorageManagement:
    def __init__(self,database,identity,vault,operations,deployments):
        self.db,self.identity,self.vault=database,identity,vault
        self.operations,self.deployments=operations,deployments
        self.execution_reconciled=False

    @staticmethod
    def command(row):
        if row is None:return None
        fields=('id','function_id','kind','state','phase','created_at','completed_at',
                'expected_function_version','result_version','error_code')
        return {key:row[key] for key in fields}

    def latest(self,key):
        return self.command(self.db.one('SELECT * FROM storage_commands WHERE function_id=? ORDER BY created_at DESC,id LIMIT 1',(key,)))

    @staticmethod
    def archive_sql():
        return '''SELECT f.id,f.name,f.service_id,s.name service_name,s.namespace_id,n.name namespace_name,
            f.created_at,f.updated_at,f.deleted_at,f.purged_at,
            (SELECT count(*) FROM revisions r WHERE r.function_id=f.id AND r.deleted_at IS NULL) revision_count,
            (SELECT coalesce(sum(stored_bytes),0) FROM revisions r WHERE r.function_id=f.id)+
            (SELECT coalesce(sum(reserved_bytes),0) FROM deployments d WHERE d.function_id=f.id) artifact_bytes
            FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id'''

    def archive(self,key):
        row=self.db.one(self.archive_sql()+' WHERE f.id=? AND f.deleted_at IS NOT NULL',(key,))
        if not row:raise HTTPException(404,'Archive de fonction introuvable.')
        return row

    async def administrator(self,request,mutation=False):
        if request.headers.get('x-serverless-token') is not None:
            raise HTTPException(403,'Les archives exigent une session administrateur.')
        return await self.identity.admin(request,mutation)

    async def authorization(self,request,key,kind):
        if kind=='purge':await self.administrator(request,True)
        function=self.db.one('SELECT * FROM functions WHERE id=?',(key,))
        authorization=await self.identity.operation(request,function['service_id'] if function else '','update',key)
        if not function:raise HTTPException(404,'Fonction introuvable.')
        if kind=='clear-cache' and function['deleted_at'] is not None:raise HTTPException(404,'Fonction introuvable.')
        if kind=='purge' and function['deleted_at'] is None:raise HTTPException(409,'Supprimez la fonction avant de purger ses archives.')
        return authorization

    async def observation(self,key):
        try:
            snapshot=await self.operations.snapshot(key)
            if snapshot is None:return {'available':True,'registered':False,'volumes':{}}
            return {'available':True,'registered':True,**{k:snapshot[k] for k in ('state','version','pending','leases')},
                    'volumes':{kind:{name:volume[name] for name in ('enabled','quota_bytes','phase','last_measured_used_bytes','error')}
                               for kind,volume in snapshot['volumes'].items() if kind in ('data','cache')}}
        except StorageError as error:
            return {'available':False,'error_code':str(error)}

    def finish(self,row,state):
        now=time.time()
        with self.db.transaction() as db:
            db.execute('UPDATE storage_commands SET state=?,phase=NULL,completed_at=?,error_code=? WHERE id=?',
                       (state,now,'operation_aborted' if state=='aborted' else None,row['id']))
            if row['kind']=='purge' and state=='completed':
                db.execute('UPDATE functions SET purged_at=? WHERE id=?',(now,row['function_id']))
                # An invalidated upload could finish its diagnostic after the decision.
                # artifacts() has now joined the shared owner; no publisher can remain.
                db.execute('UPDATE deployments SET configuration_cipher=NULL,validation_json=NULL WHERE function_id=?',(row['function_id'],))
            db.execute('DELETE FROM function_operations WHERE id=?',(row['id'],))

    def phase(self,row,phase,error=None):
        with self.db.transaction() as db:
            db.execute('UPDATE storage_commands SET phase=?,error_code=? WHERE id=?',(phase,error,row['id']))
            db.execute('UPDATE function_operations SET error_code=? WHERE id=?',(error,row['id']))

    async def artifacts(self,key):
        deployment=self.deployments
        if deployment.busy:return False
        if self.db.one('SELECT 1 FROM execution_instances WHERE function_id=?',(key,)):
            raise StorageError('artifact_instance_retained')
        if self.db.one("SELECT 1 FROM deployments WHERE function_id=? AND state IN ('prepared','receiving','validating')",(key,)):
            raise StorageError('artifact_candidate_retained')
        deployment.cleaning=True
        try:
            if deployment.cleanup_error:
                await blocking(deployment.reconcile_docker)
                await deployment.clean_channels()
            rows=self.db.all('SELECT id FROM revisions WHERE function_id=? AND deleted_at IS NOT NULL',(key,))
            # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication
            rows+=self.db.all("SELECT id FROM deployments WHERE function_id=? AND state IN ('failed','expired','published') AND id NOT IN (SELECT id FROM revisions)",(key,))
            for item in rows:
                await blocking(deployment.remove,deployment.root,str(UUID(item['id'])))
                with self.db.transaction() as db:
                    db.execute('UPDATE revisions SET stored_bytes=0 WHERE id=? AND function_id=? AND deleted_at IS NOT NULL',(item['id'],key))
                    db.execute("UPDATE deployments SET reserved_bytes=0 WHERE id=? AND function_id=? AND state IN ('failed','expired','published')",(item['id'],key))
            return True
        except (OSError,ArtifactError,ValidationError,RuntimeError):raise StorageError('artifact_cleanup_pending') from None
        finally:deployment.cleaning=False

    async def resolve(self,row):
        command=self.db.one('SELECT * FROM storage_commands WHERE id=?',(row['id'],))
        if not command or command['installation_id']!=self.operations.installation:raise StorageError('operation_owner')
        if row['decision']=='abort':
            self.finish(row,'aborted');return True
        if row['decision']!='commit' or command['state']!='pending':raise StorageError('operation_conflict')
        if not self.execution_reconciled:return False
        if command['storage_absent'] and await self.operations.snapshot(row['function_id']) is not None:
            raise StorageError('storage_state_changed')
        if command['phase']=='volumes':
            if not command['storage_absent']:
                expected={'function_id':row['function_id'],'operation_id':row['id'],
                          'installation_id':command['installation_id'],'kind':row['kind'],'expected_version':row['storage_version']}
                result=await self.operations.storage.call('start-discard',**expected)
                if any(result.get(k)!=v for k,v in expected.items()):raise StorageError('storage_protocol',uncertain=True)
                state=result.get('state');version=result.get('version')
                if (state not in ('pending','completed') or type(version) is not int or
                        version!=row['storage_version']+(state=='completed')):raise StorageError('storage_protocol',uncertain=True)
                if state=='pending':
                    if result.get('phase') not in ('stopping','erasing','finalizing'):raise StorageError('storage_protocol',uncertain=True)
                    error=result.get('error_code')
                    if error is not None and (not isinstance(error,str) or len(error)>64 or not error.replace('_','').isalpha()):
                        raise StorageError('storage_protocol',uncertain=True)
                    self.phase(row,'volumes',error);return False
                if result.get('error_code') is not None or result.get('phase') is not None:raise StorageError('storage_protocol',uncertain=True)
            if row['kind']=='clear-cache':
                self.finish(row,'completed');return True
            self.phase(row,'artifacts')
        elif command['phase']!='artifacts':raise StorageError('operation_conflict')
        if not await self.artifacts(row['function_id']):return False
        if command['storage_absent'] and await self.operations.snapshot(row['function_id']) is not None:
            raise StorageError('storage_state_changed')
        self.finish(row,'completed');return True

    async def start(self,request,key,data,kind):
        key=str(key);identifier=str(data.operation_id)
        authorization=await self.authorization(request,key,kind)
        expected=request.headers.get('if-match')
        if expected is None:raise HTTPException(428,'If-Match est obligatoire pour cette opération.')
        existing=self.db.one('SELECT * FROM storage_commands WHERE id=?',(identifier,))
        if kind=='purge' and data.confirm_name!=self.archive(key)['name']:
            raise HTTPException(422,'Le nom de confirmation doit correspondre exactement à la fonction.')
        if existing:
            if (existing['function_id']!=key or existing['kind']!=kind or str(existing['expected_function_version'])!=expected):
                raise HTTPException(409,'Cet identifiant correspond à une autre commande.')
            return self.response(existing)
        if self.db.one('SELECT 1 FROM function_operations WHERE id=?',(identifier,)):
            raise HTTPException(409,'Cet identifiant appartient déjà à une opération.')
        async with self.operations.responsibility(identifier,pending_response=True):
            with self.db.transaction() as db:
                function=dict(db.execute('SELECT * FROM functions WHERE id=?',(key,)).fetchone())
                service=dict(db.execute('SELECT * FROM services WHERE id=?',(function['service_id'],)).fetchone())
                self.identity.recheck(db,authorization,service['id'],'update',key);required_version(request,function)
                if function['purged_at'] is not None:raise HTTPException(409,'Cette archive est déjà purgée.')
                if kind=='clear-cache' and (function['deleted_at'] is not None or service['deleted_at'] is not None):
                    raise HTTPException(404,'Fonction introuvable.')
                self.operations.reserve(db,identifier,function,service,kind=kind)
                db.execute('INSERT INTO storage_commands (id,function_id,service_id,installation_id,kind,state,phase,expected_function_version,created_at) VALUES (?,?,?,?,?,\'preparing\',\'draining\',?,?)',
                           (identifier,key,service['id'],self.operations.installation,kind,function['updated_at'],time.time()))
            await self.operations.prepare(identifier)
            authorization=await self.authorization(request,key,kind)
            with self.db.transaction() as db:
                function=dict(db.execute('SELECT * FROM functions WHERE id=?',(key,)).fetchone())
                service=dict(db.execute('SELECT * FROM services WHERE id=?',(function['service_id'],)).fetchone())
                self.identity.recheck(db,authorization,service['id'],'update',key)
                self.operations.verify(db,identifier,function,service)
                now=max(time.time(),function['updated_at']+0.000001)
                db.execute('UPDATE functions SET updated_at=? WHERE id=?',(now,key))
                if kind=='purge':
                    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#archivage-restauration-et-suppression
                    # @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#persistance-concurrence-et-conservation
                    db.execute('DELETE FROM code_drafts WHERE function_id=?',(key,))
                    db.execute("UPDATE function_versions SET state='deleted',updated_at=? WHERE function_id=?",(now,key))
                    db.execute("UPDATE functions SET config_json='{}',environment_json='{}',secrets_cipher=? WHERE id=?",(self.vault.seal({}),key))
                    db.execute("UPDATE revisions SET deleted_at=coalesce(deleted_at,?),inventory_json='[]',events_json='{}' WHERE function_id=?",(now,key))
                    db.execute("UPDATE deployments SET configuration_cipher=NULL,events_json='{}',validation_json=NULL WHERE function_id=?",(key,))
                db.execute("UPDATE storage_commands SET state='pending',phase='volumes',result_version=?,error_code=NULL WHERE id=?",(now,identifier))
                self.operations.commit(db,identifier)
                audit(db,authorization.actor,'function.cache_clear' if kind=='clear-cache' else 'function.purge',key,service['id'],{'operation_id':identifier})
        return self.response(self.db.one('SELECT * FROM storage_commands WHERE id=?',(identifier,)))

    def response(self,row):
        return JSONResponse(self.command(row),status_code=202 if row['state'] in ('preparing','pending') else 200,
                            headers={'Location':'/api/storage-operations/'+row['id']})

    def routes(self):
        api=APIRouter(prefix='/api')

        @api.get('/functions/{key}/storage')
        async def storage(request:Request,key:UUID):
            key=str(key);row=self.db.one('SELECT id,service_id,name,updated_at FROM functions WHERE id=? AND deleted_at IS NULL',(key,))
            await self.identity.authorize(request,row['service_id'] if row else '','read',key)
            if not row:raise HTTPException(404,'Fonction introuvable.')
            return {**row,'storage':await self.observation(key),'storage_operation':self.operations.summary(key),'command':self.latest(key)}

        @api.post('/functions/{key}/cache-clear')
        async def clear_cache(request:Request,key:UUID,data:CacheClear):
            return await self.start(request,key,data,'clear-cache')

        @api.get('/archives')
        async def archives(request:Request,state:Literal['retained','purged','all']='retained',
                           limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=2147483647),service_id:UUID|None=None):
            await self.administrator(request)
            where=' WHERE f.deleted_at IS NOT NULL';args=[]
            if state!='all':where+=' AND f.purged_at IS '+('NULL' if state=='retained' else 'NOT NULL')
            if service_id:where+=' AND f.service_id=?';args.append(str(service_id))
            with closing(self.db.connect()) as db:
                db.execute('BEGIN')
                total=db.execute('SELECT count(*) FROM functions f'+where,args).fetchone()[0]
                items=[dict(row) for row in db.execute(self.archive_sql()+where+' ORDER BY f.deleted_at DESC,f.id LIMIT ? OFFSET ?',(*args,limit,offset))]
            return {'items':items,'total':total,'limit':limit,'offset':offset}

        @api.get('/archives/{key}')
        async def archive(request:Request,key:UUID):
            await self.administrator(request);key=str(key);row=self.archive(key)
            return {**row,'storage':await self.observation(key),'storage_operation':self.operations.summary(key),'command':self.latest(key)}

        @api.post('/archives/{key}/purge')
        async def purge(request:Request,key:UUID,data:ArchivePurge):
            return await self.start(request,key,data,'purge')

        @api.get('/storage-operations/{key}')
        async def command(request:Request,key:UUID):
            row=self.db.one('SELECT * FROM storage_commands WHERE id=?',(str(key),))
            if request.headers.get('x-serverless-token') is None:await self.identity.admin(request)
            else:
                function=self.db.one('SELECT id FROM functions WHERE id=? AND deleted_at IS NULL',(row['function_id'],)) if row else None
                await self.identity.authorize(request,row['service_id'] if row else '','update',row['function_id'] if row else '')
                if row['kind']!='clear-cache' or not function:raise HTTPException(403,'Cette commande exige une session administrateur.')
            if not row:raise HTTPException(404,'Opération de stockage introuvable.')
            return self.command(row)

        return api
