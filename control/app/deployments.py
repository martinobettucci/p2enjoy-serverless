# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle | docs/SCHEMA.md#déploiements-et-révisions
"""Authenticated publication, bounded admission and installation-owned recovery."""
import asyncio
from contextlib import closing,suppress,contextmanager
import fcntl
import json
import logging
import os
from pathlib import Path
import shutil
import stat
import sqlite3
import sys
import time
from urllib.parse import urlencode
from uuid import UUID,uuid4

# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation
from function_code_hash import code_hash

from fastapi import APIRouter,HTTPException,Query,Request
from starlette.requests import ClientDisconnect

from .artifacts import MAX_ZIP,MAX_TOTAL,MAX_ENTRIES,ArtifactError,open_directory,remove_tree
from .db import audit
from .function_operations import storage_configuration
from .models import CodeDeploymentCreate,DeploymentCreate,Rollback
from .validator import Docker,ValidationError,application_environment,validate,LIMIT
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md
from .function_versions import FunctionVersions,default_code_hash,selected_revision

RESERVATION=MAX_ZIP+MAX_TOTAL+(2*MAX_ENTRIES+2)*4096
MARGIN=1024**3
SOCKET='/docker.sock'
METHODS=['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS']
logger=logging.getLogger('p2enjoy.control')


async def joined(awaitable):
    task=asyncio.ensure_future(awaitable)
    cancelled=False
    while not task.done():
        try:await asyncio.shield(task)
        except asyncio.CancelledError:cancelled=True
    result=task.result()
    if cancelled:raise asyncio.CancelledError
    return result


async def blocking(function,*args):return await joined(asyncio.to_thread(function,*args))


def required_version(request,row):
    expected=request.headers.get('if-match')
    if expected is None:raise HTTPException(428,'If-Match est obligatoire pour cette opération.')
    if expected!=str(row['updated_at']):raise HTTPException(409,'La fonction a changé. Relisez sa version avant de poursuivre.')


def get(db,table,key):
    row=db.execute(f'SELECT * FROM {table} WHERE id=? AND deleted_at IS NULL',(str(key),)).fetchone()
    if not row:raise HTTPException(404,'Ressource introuvable.')
    return dict(row)


# @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#configuration-de-service-et-surcharges
def effective_configuration(vault,service,configuration):
    environment=json.loads(service['environment_json'])|configuration['environment']
    secrets=vault.open(service['secrets_cipher'])|{key:value for key,value in configuration['secrets'].items() if value is not None}
    try:
        combined=application_environment(environment,secrets)
        if len(json.dumps({'handler':'x'*256,'environment':combined}).encode())>LIMIT:raise ValidationError('configuration_limit')
    except ValidationError:raise HTTPException(422,'La configuration effective de service et de fonction dépasse les limites ou présente une collision.') from None
    return environment,secrets


class Deployments:
    def __init__(self,settings,database,identity,vault,operations):
        self.settings,self.database,self.identity,self.vault=settings,database,identity,vault
        self.root=settings.state_dir/'artifacts';self.channels=settings.state_dir/'validation'
        self.lock=None;self.task=None;self.cleaning=False;self.cleanup_error=False;self.installation=None
        self.operations=operations
        # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication
        self.live_uploads=set();self.validation_lock=asyncio.Lock();self.versions=FunctionVersions(self)
        # @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#persistance-concurrence-et-conservation
        self.source_readers=0

    @property
    def busy(self):return self.cleaning or bool(self.live_uploads) or self.source_readers>0

    # @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#persistance-concurrence-et-conservation
    @contextmanager
    def source_reader(self):
        # Event-loop owned: acquisition precedes every await; blocking() joins IO before release.
        if self.cleaning or self.source_readers>=4:
            raise HTTPException(429,'Les lecteurs de code sont occupés.',headers={'Retry-After':'2'})
        self.source_readers+=1
        try:yield
        finally:self.source_readers-=1

    async def start(self):
        self.lock=os.open(self.settings.state_dir/'control.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:os.close(self.lock);self.lock=None;raise RuntimeError('Un contrôle possède déjà cet état.') from None

    async def ready(self):
        for path in (self.root,self.channels):
            path.mkdir(mode=0o700,exist_ok=True)
            fd=open_directory(path)
            try:os.fchmod(fd,0o700)
            finally:os.close(fd)
        with self.database.transaction() as db:
            row=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()
            self.installation=str(UUID(row['value'])) if row else str(uuid4())
            if not row:db.execute('INSERT INTO security_metadata VALUES (?,?)',('installation-id',self.installation))
        await blocking(self.reconcile_docker)
        with self.database.transaction() as db:
            db.execute("UPDATE deployments SET state='failed',error_code='control_interrupted',configuration_cipher=NULL,completed_at=? WHERE state IN ('receiving','validating')",(time.time(),))
        await self.clean(startup=True)
        if self.cleanup_error:raise RuntimeError('Le nettoyage des artefacts doit réussir avant la reprise.')
        self.task=asyncio.create_task(self.maintain())

    async def close(self):
        try:
            if self.task:
                self.task.cancel()
                with suppress(asyncio.CancelledError):await joined(self.task)
        finally:
            if self.lock is not None:os.close(self.lock);self.lock=None

    def reconcile_docker(self):
        docker=Docker(SOCKET)
        info=docker.call('GET','/info')
        if 'name=rootless' not in info.get('SecurityOptions',[]):raise RuntimeError('Le démon Docker attendu est rootless.')
        docker.image(self.settings.runtime_image)
        labels={'tech.p2enjoy.serverless.installation':self.installation,'tech.p2enjoy.serverless.kind':'validation'}
        query=urlencode({'all':'1','filters':json.dumps({'label':[key+'='+value for key,value in labels.items()]})})
        for item in docker.call('GET','/containers/json?'+query):
            key=item['Id'];row=docker.call('GET','/containers/'+key+'/json',allowed=(200,404))
            if not row or not row.get('Id'):continue
            if any(row.get('Config',{}).get('Labels',{}).get(name)!=value for name,value in labels.items()):
                raise RuntimeError('Propriété Docker incohérente pendant la reprise.')
            docker.call('DELETE','/containers/'+key+'?force=1&v=1',timeout=10,allowed=(204,404))
            docker.call('GET','/containers/'+key+'/json',allowed=(404,))

    def remove(self,root,key):
        # Every name originates from a UUID in our DB, or a separately owned channel.
        fd=open_directory(root)
        try:
            try:row=os.stat(key,dir_fd=fd,follow_symlinks=False)
            except FileNotFoundError:
                # @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
                # A preceding attempt may have removed the tree but failed its fsync.
                os.fsync(fd);return
            if not stat.S_ISDIR(row.st_mode):raise ArtifactError('cleanup_type')
            remove_tree(fd,key,(row.st_dev,row.st_ino));os.fsync(fd)
        finally:os.close(fd)

    def expire(self):
        with self.database.transaction() as db:
            db.execute("UPDATE deployments SET state='expired',error_code='candidate_expired',configuration_cipher=NULL,completed_at=? WHERE state='prepared' AND expires_at<=?",(time.time(),time.time()))

    # @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#décision-durable-et-répétition
    def purge_holds_artifacts(self,function):
        # Only the purge resolver may erase these files after rechecking storage.
        return self.database.one("SELECT 1 FROM function_operations WHERE function_id=? AND kind='purge'",(function,)) is not None

    async def clean_candidate(self,key):
        if self.database.one('SELECT 1 FROM revisions WHERE id=?',(key,)):return
        row=self.database.one('SELECT state,function_id,revision_id FROM deployments WHERE id=?',(key,))
        if row and row['state'] not in ('failed','expired','published'):return
        if row and row['state']=='published' and (not row['revision_id'] or row['revision_id']==key):return
        if row and self.purge_holds_artifacts(row['function_id']):return
        await blocking(self.remove,self.root,str(UUID(key)))
        with self.database.transaction() as db:
            db.execute("UPDATE deployments SET reserved_bytes=0 WHERE id=? AND state IN ('failed','expired','published')",(key,))

    async def clean(self,startup=False):
        if self.busy:return
        self.cleaning=True
        try:
            if self.cleanup_error:
                await blocking(self.reconcile_docker)
                await self.clean_channels()
            # With no live worker, these states can only belong to an interrupted operation.
            with self.database.transaction() as db:
                db.execute("UPDATE deployments SET state='failed',error_code='deployment_interrupted',configuration_cipher=NULL,completed_at=? WHERE state IN ('receiving','validating')",(time.time(),))
            self.expire()
            for row in self.database.all("SELECT id FROM deployments WHERE state IN ('failed','expired','published') AND reserved_bytes>0"):
                await self.clean_candidate(row['id'])
            # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#archivage-restauration-et-suppression
            # Availability is removed immediately; aliases remain retained until
            # their real consumers finish. The existing retention triggers stay.
            with self.database.transaction() as db:
                db.execute('''UPDATE revisions SET deleted_at=? WHERE deleted_at IS NULL
                    AND EXISTS(SELECT 1 FROM function_versions v WHERE v.function_id=revisions.function_id
                        AND v.code_hash=revisions.code_hash AND v.state='deleted')
                    AND NOT EXISTS(SELECT 1 FROM execution_instances i WHERE i.revision_id=revisions.id)
                    AND NOT EXISTS(SELECT 1 FROM functions f WHERE f.active_revision_id=revisions.id)
                    AND NOT EXISTS(SELECT 1 FROM code_drafts d WHERE d.base_revision_id=revisions.id)
                    AND NOT EXISTS(SELECT 1 FROM function_operations o WHERE o.function_id=revisions.function_id AND o.kind='purge')''',
                    (time.time(),))
            for row in self.database.all('SELECT id,function_id FROM revisions WHERE deleted_at IS NOT NULL AND stored_bytes>0'):
                if self.purge_holds_artifacts(row['function_id']):continue
                if self.database.one('SELECT 1 FROM execution_instances WHERE revision_id=?',(row['id'],)):continue
                if self.database.one('SELECT 1 FROM code_drafts WHERE base_revision_id=?',(row['id'],)):continue
                await blocking(self.remove,self.root,str(UUID(row['id'])))
                with self.database.transaction() as db:db.execute('UPDATE revisions SET stored_bytes=0 WHERE id=? AND deleted_at IS NOT NULL',(row['id'],))
            if startup:
                for path in self.root.iterdir():
                    try:key=str(UUID(path.name))
                    except ValueError:raise RuntimeError('Entrée inattendue dans la racine des artefacts.') from None
                    if key!=path.name:raise RuntimeError('Identifiant d’artefact non canonique.')
                    if not self.database.one('SELECT 1 FROM revisions WHERE id=?',(key,)):
                        await self.clean_candidate(key)
                await self.clean_channels()
            self.cleanup_error=False
        except (OSError,ArtifactError,ValidationError,sqlite3.Error,RuntimeError) as error:
            self.cleanup_error=True
            logger.error(json.dumps({'event':'deployment.cleanup_failed','error_type':type(error).__name__}))
        finally:self.cleaning=False

    async def clean_channels(self):
        for path in self.channels.iterdir():
            if not path.name.startswith('v-'):raise RuntimeError('Canal de validation inattendu.')
            await blocking(self.remove,self.channels,path.name)

    async def maintain(self):
        while True:
            await asyncio.sleep(30)
            await self.clean()

    def candidate(self,key):
        row=self.database.one('SELECT * FROM deployments WHERE id=?',(str(key),))
        if not row:raise HTTPException(404,'Déploiement introuvable.')
        return row

    async def access(self,request,row):
        authorization=await self.identity.operation(request,row['service_id'],row['required_right'],row['function_id'])
        actor=authorization.actor
        if actor.kind!='admin' and (actor.kind,actor.id)!=(row['actor_kind'],row['actor_id']):
            raise HTTPException(403,'Ce candidat appartient à une autre identité.')
        return authorization

    @staticmethod
    def public(row):
        fields=('id','function_id','service_id','state','error_code','created_at','expires_at','completed_at','revision_id',
                'code_hash','code_changed','version_restored','result_function_version','default_code_hash_at_publication','restore_code_hash','code_only')
        result={key:row[key] for key in fields}
        for key in ('code_changed','version_restored','code_only'):
            if result[key] is not None:result[key]=bool(result[key])
        result['validation']=json.loads(row['validation_json']) if row['validation_json'] else None
        return result

    def effective(self,service,configuration):
        return effective_configuration(self.vault,service,configuration)

    def verify(self,db,row,authorization,*,state=None,operation=None):
        self.identity.recheck(db,authorization,row['service_id'],row['required_right'],row['function_id'])
        function=get(db,'functions',row['function_id']);service=get(db,'services',row['service_id'])
        self.operations.function_available(db,function['id'],operation)
        if function['service_id']!=service['id']:raise HTTPException(409,'Le rattachement de la fonction a changé.')
        if state and row['state']!=state:raise HTTPException(409,'Ce candidat ne peut plus recevoir de publication.')
        if row['expires_at']<=time.time():raise HTTPException(409,'Ce candidat a expiré.')
        if (function['updated_at']!=row['expected_function_version'] or service['updated_at']!=row['expected_service_version']):
            raise HTTPException(409,'La fonction ou la configuration du service a changé pendant ce déploiement.')
        return function,service

    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#publication-et-déduplication
    def publication_version(self,db,function,candidate,identity,configuration):
        existing=db.execute('SELECT * FROM function_versions WHERE function_id=? AND code_hash=?',
                            (function['id'],identity)).fetchone()
        restore=candidate['restore_code_hash']
        if restore is not None and restore!=identity:
            raise HTTPException(422,'Le hash recalculé ne correspond pas à la version à réimporter.')
        if candidate['required_right']=='create' and function['first_published_code_hash'] is not None:
            if identity!=function['first_published_code_hash'] or not existing or existing['state']!='available' or restore:
                raise HTTPException(403,'Create ne permet que la première publication de cette fonction.')
            target_config=self.publication_configuration(function,candidate,configuration)
            if self.configuration_changed(function,target_config,configuration['configuration']):
                raise HTTPException(403,'Create ne permet pas de modifier une configuration déjà publiée.')
        if existing and existing['state']=='archived':
            raise HTTPException(409,'Cette version est archivée. Restaurez-la explicitement avant publication.')
        if existing and existing['state']=='available':
            selected_revision(db,function,identity)
        if existing and existing['state']=='deleted':
            if restore!=identity:raise HTTPException(409,'Cette version a été supprimée. Réimportez ce hash explicitement.')
            retained=db.execute('''SELECT 1 FROM revisions WHERE function_id=? AND code_hash=?
                AND (deleted_at IS NULL OR stored_bytes>0)''',(function['id'],identity)).fetchone()
            pending=db.execute('''SELECT 1 FROM deployments WHERE function_id=? AND code_hash=?
                AND id!=? AND reserved_bytes>0''',(function['id'],identity,candidate['id'])).fetchone()
            if retained or pending:raise HTTPException(409,'Le nettoyage de cette version doit terminer avant sa réimportation.')
        elif restore is not None:
            raise HTTPException(409,'La réimportation explicite concerne une version supprimée connue.')
        if not existing or existing['state']=='deleted':
            total=db.execute("SELECT count(*) FROM function_versions WHERE function_id=? AND state IN ('available','archived')",(function['id'],)).fetchone()[0]
            if total>=20:raise HTTPException(409,'La fonction conserve déjà vingt versions. Supprimez une version inactive.')
        return dict(existing) if existing else None

    def publication_configuration(self,function,candidate,configuration):
        previous=json.loads(function['config_json'])
        if candidate['code_only']:return previous
        # Handler/runtime describe the default, chosen only by promotion.
        return configuration['config']|{name:previous[name] for name in ('handler','runtime')}

    def configuration_changed(self,function,config,values):
        return (json.loads(function['config_json'])!=config or json.loads(function['environment_json'])!=values['environment'] or
                self.vault.open(function['secrets_cipher'])!={k:v for k,v in values['secrets'].items() if v is not None})

    def failed(self,key,code,validation=None):
        with self.database.transaction() as db:
            db.execute("UPDATE deployments SET state='failed',error_code=?,validation_json=?,configuration_cipher=NULL,completed_at=? WHERE id=? AND state!='published'",
                (code,json.dumps(validation) if validation else None,time.time(),key))

    async def extract(self,path):
        process=await asyncio.create_subprocess_exec(sys.executable,'-B','-m',__package__+'.artifacts',
            '--archive',str(path/'archive.zip'),'--destination',str(path/'code'),
            stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:
            async with asyncio.timeout(300):out,err=await process.communicate()
            if err or len(out)>24*1024**2:raise HTTPException(422,'La réponse d’extraction est invalide.')
            result=json.loads(out)
            if process.returncode or not result.get('ok'):
                raise HTTPException(422,'Archive refusée : '+str(result.get('error','extraction_failed')))
            return result
        except (ValueError,TimeoutError):raise HTTPException(422,'L’extraction est invalide ou a dépassé son délai.') from None
        finally:
            if process.returncode is None:
                process.kill();await joined(process.communicate())

    async def upload(self,request,key,operation,*,archive_stream=None):
        row=await self.read_candidate(request,key);authorization=await self.access(request,row)
        if archive_stream is None and request.headers.get('content-type','').split(';',1)[0].strip().lower()!='application/zip':
            raise HTTPException(415,'Un corps application/zip est requis.')
        if self.cleaning or len(self.live_uploads)>=4:
            raise HTTPException(429,'La capacité de publication est occupée.',headers={'Retry-After':'5'})
        if self.cleanup_error:raise HTTPException(503,'Un nettoyage de déploiement doit être repris.')
        admitted=False;key=str(key);path=self.root/key;validation=None;validation_started=False
        if key in self.live_uploads:raise HTTPException(409,'Ce candidat reçoit déjà une publication.')
        self.live_uploads.add(key)
        try:
            with self.database.transaction() as db:
                row=dict(db.execute('SELECT * FROM deployments WHERE id=?',(key,)).fetchone())
                self.verify(db,row,authorization,state='prepared')
                occupied=db.execute('SELECT coalesce(sum(stored_bytes),0) FROM revisions').fetchone()[0]
                occupied+=db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0]
                if occupied+RESERVATION>self.settings.artifact_budget:raise HTTPException(507,'Le budget de stockage des artefacts est insuffisant.')
                if shutil.disk_usage(self.root).free<RESERVATION+MARGIN:raise HTTPException(507,'La marge libre du disque est insuffisante.')
                db.execute("UPDATE deployments SET state='receiving',reserved_bytes=? WHERE id=?",(RESERVATION,key))
            admitted=True
            path.mkdir(mode=0o700)
            fd=open_directory(self.root)
            try:await blocking(os.fsync,fd)
            finally:os.close(fd)
            request.state.artifact_upload_authorized=True
            size=0
            with (path/'archive.zip').open('xb') as stream:
                async with asyncio.timeout(120):
                    async for chunk in (archive_stream if archive_stream is not None else request.stream()):
                        size+=len(chunk)
                        if size>MAX_ZIP:raise HTTPException(413,'L’archive dépasse 64 Mio.')
                        await blocking(stream.write,chunk)
                await blocking(stream.flush);await blocking(os.fsync,stream.fileno());os.fchmod(stream.fileno(),0o444)
            extracted=await self.extract(path)
            with self.database.transaction() as db:
                updated=db.execute("UPDATE deployments SET state='validating' WHERE id=? AND state='receiving'",(key,)).rowcount
                if not updated:raise HTTPException(409,'Le candidat a été invalidé pendant la réception.')
            configuration=self.vault.open(row['configuration_cipher'])
            service=self.database.one('SELECT * FROM services WHERE id=?',(row['service_id'],))
            environment,secrets=self.effective(service,configuration['configuration'])
            async with self.validation_lock:
                if self.cleanup_error:raise HTTPException(503,'Un nettoyage de déploiement doit être repris avant validation.')
                validation_started=True
                worker=asyncio.create_task(asyncio.to_thread(validate,docker_socket=SOCKET,image=self.settings.runtime_image,
                    code=self.settings.host_state_dir/'artifacts'/key/'code',work=self.channels,
                    host_work=self.settings.host_state_dir/'validation',handler=configuration['config']['handler'],
                    environment=environment,secrets=secrets,installation=self.installation))
                try:validation=await asyncio.shield(worker)
                except asyncio.CancelledError:
                    validation=await asyncio.shield(worker);raise
                finally:
                    # Publish the unresolved ownership before releasing the lock
                    # to an upload that was admitted before this failure.
                    if not validation or not validation.get('container_removed'):self.cleanup_error=True
            if not validation['valid'] or not validation['container_removed']:
                raise HTTPException(422,'Le chargement du handler a échoué : '+validation.get('error','validation_failed'))
            authorization=await self.access(request,row)
            stored=extracted['storage_charge_bytes']+4096
            if stored>RESERVATION:raise HTTPException(507,'La consommation réelle dépasse la réservation.')
            descriptor=configuration['config']
            identity=code_hash(extracted['inventory'],{'handler':descriptor['handler'],'runtime':descriptor['runtime'],
                'architecture':'linux-x64','image_id':validation['image_id'],'events':json.loads(row['events_json'])})['code_hash']
            with self.database.transaction() as db:
                current=dict(db.execute('SELECT * FROM deployments WHERE id=?',(key,)).fetchone())
                function,service=self.verify(db,current,authorization,state='validating')
                self.publication_version(db,function,current,identity,configuration)
                config=self.publication_configuration(function,current,configuration)
                storage_changed=storage_configuration(json.loads(function['config_json']))!=storage_configuration(config)
                if storage_changed:
                    self.operations.reserve(db,operation,function,service,storage_configuration(config))
            if storage_changed:
                await self.operations.prepare(operation)
                authorization=await self.access(request,row)
            with self.database.transaction() as db:
                current=dict(db.execute('SELECT * FROM deployments WHERE id=?',(key,)).fetchone())
                function,service=self.verify(db,current,authorization,state='validating',operation=operation)
                if storage_changed:self.operations.verify(db,operation,function,service)
                now=time.time();config=self.publication_configuration(function,current,configuration);values=configuration['configuration']
                self.operations.minimum_budget(db,function['id'],config)
                existing=self.publication_version(db,function,current,identity,configuration)
                reused=existing is not None and existing['state']=='available'
                restored=existing is not None and existing['state']=='deleted'
                revision_id=existing['revision_id'] if reused else key
                if not reused:
                    db.execute('''INSERT INTO revisions
                        (id,function_id,handler,runtime,architecture,image_id,archive_sha256,inventory_json,events_json,stored_bytes,created_at,deleted_at,code_hash)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL,?)''',
                        (key,function['id'],descriptor['handler'],descriptor['runtime'],'linux-x64',validation['image_id'],extracted['archive_sha256'],
                         json.dumps(extracted['inventory']),current['events_json'],stored,now,identity))
                    if restored:
                        db.execute("UPDATE function_versions SET revision_id=?,state='available',updated_at=? WHERE function_id=? AND code_hash=?",
                                   (key,now,function['id'],identity))
                    else:
                        db.execute("INSERT INTO function_versions(function_id,code_hash,revision_id,created_at,state,updated_at) VALUES(?,?,?,?,'available',?)",
                                   (function['id'],identity,key,now,now))
                if function['first_published_code_hash'] is None and function['first_promoted_at'] is None:
                    db.execute('UPDATE functions SET first_published_code_hash=? WHERE id=?',(identity,function['id']))
                changed=not current['code_only'] and self.configuration_changed(function,config,values)
                result_version=max(now,function['updated_at']+.000001) if changed else function['updated_at']
                if changed:
                    db.execute('UPDATE functions SET config_json=?,environment_json=?,secrets_cipher=?,updated_at=? WHERE id=?',
                        (json.dumps(config),json.dumps(values['environment']),self.vault.seal({k:v for k,v in values['secrets'].items() if v is not None}),result_version,function['id']))
                target=default_code_hash(db,function)
                db.execute("""UPDATE deployments SET state='published',reserved_bytes=?,configuration_cipher=NULL,
                    validation_json=?,completed_at=?,revision_id=?,code_hash=?,code_changed=?,version_restored=?,
                    result_function_version=?,default_code_hash_at_publication=? WHERE id=?""",
                    (RESERVATION if reused else 0,json.dumps(validation),now,revision_id,identity,int(existing is None),int(restored),result_version,target,key))
                if storage_changed:self.operations.commit(db,operation)
                audit(db,authorization.actor,'function.deploy',function['id'],function['service_id'],
                      {'deployment_id':key,'revision_id':revision_id,'code_hash':identity,'code_changed':existing is None,
                       'version_restored':restored,'configuration_changed':changed,'default_code_hash':target})
            return self.public(self.candidate(key))
        except BaseException as error:
            if admitted:
                code=('upload_interrupted' if isinstance(error,(asyncio.CancelledError,ClientDisconnect)) else
                      'upload_timeout' if isinstance(error,TimeoutError) else
                      'request_rejected' if isinstance(error,HTTPException) else 'deployment_failed')
                self.failed(key,code,validation)
            if isinstance(error,(OSError,ArtifactError,ValidationError,TimeoutError)):
                raise HTTPException(503,'Le déploiement n’a pas pu être achevé ; la révision précédente est conservée.') from None
            raise
        finally:
            try:
                if validation_started and (not validation or not validation.get('container_removed')):
                    self.cleanup_error=True
                elif admitted:
                    await joined(self.clean_candidate(key))
                    row=self.candidate(key)
                    if row['state'] in ('receiving','validating'):self.cleanup_error=True
            except (OSError,ArtifactError,sqlite3.Error):self.cleanup_error=True
            finally:self.live_uploads.discard(key)

    async def read_candidate(self,request,key):
        try:return self.candidate(key)
        except HTTPException:
            await self.identity.authorize(request,'','read')
            raise

    # @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#parcours-et-conservation
    async def prepare(self,request,key,data,*,editor_draft=None):
        function=self.database.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        right='update' if self.database.one('SELECT 1 FROM revisions WHERE function_id=?',(str(key),)) else 'create'
        authorization=await self.identity.operation(request,function['service_id'] if function else '',right,str(key))
        self.expire();now=time.time()
        code_only=isinstance(data,CodeDeploymentCreate)
        candidate=str(data.deployment_id) if code_only else str(uuid4())
        with self.database.transaction() as db:
            function=get(db,'functions',key);service=get(db,'services',function['service_id'])
            self.operations.function_available(db,str(key))
            current_right='update' if db.execute('SELECT 1 FROM revisions WHERE function_id=?',(str(key),)).fetchone() else 'create'
            if current_right!=right:raise HTTPException(409,'La fonction a reçu une première révision pendant la préparation.')
            self.identity.recheck(db,authorization,service['id'],right,str(key));required_version(request,function)
            if db.execute('SELECT 1 FROM deployments WHERE id=?',(candidate,)).fetchone():
                raise HTTPException(409,'Cet identifiant de publication existe déjà. Consultez son état.')
            if db.execute("SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')").fetchone()[0]>=64:
                raise HTTPException(429,'Trop de candidats en attente.',headers={'Retry-After':'60'})
            if db.execute("SELECT count(*) FROM deployments WHERE function_id=? AND state IN ('prepared','receiving','validating')",(str(key),)).fetchone()[0]>=8:
                raise HTTPException(429,'Cette fonction possède déjà huit candidats.',headers={'Retry-After':'60'})
            if code_only:
                config=json.loads(function['config_json'])|{'handler':data.handler}
                values={'environment':json.loads(function['environment_json']),'secrets':self.vault.open(function['secrets_cipher'])}
                revision=get(db,'revisions',function['active_revision_id']) if function['active_revision_id'] else None
                events=(data.events.model_dump() if data.events is not None else
                        json.loads(revision['events_json']) if revision else {'http':[],'schedules':[]})
            else:
                config=data.config.model_dump();values=data.configuration.model_dump();events=data.events.model_dump()
            self.effective(service,values)
            if not events['http']:events['http']=[{'path':function['name'],'methods':METHODS,'implicit':True}]
            db.execute('''INSERT INTO deployments
                (id,function_id,service_id,actor_kind,actor_id,expected_function_version,expected_service_version,
                 configuration_cipher,events_json,required_right,state,reserved_bytes,created_at,expires_at,code_only,restore_code_hash)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?)''',
                (candidate,str(key),service['id'],authorization.actor.kind,authorization.actor.id,function['updated_at'],service['updated_at'],
                 self.vault.seal({'config':config,'configuration':values}),json.dumps(events),right,'prepared',now,now+3600,int(code_only),data.restore_code_hash))
            # @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#publication-et-réponses-perdues
            if editor_draft is not None:
                draft_id,draft_version=editor_draft
                updated=db.execute('''UPDATE code_drafts SET last_deployment_id=?,last_publication_version=?
                    WHERE id=? AND function_id=? AND actor_kind=? AND actor_id=? AND version=?''',
                    (candidate,draft_version,draft_id,str(key),authorization.actor.kind,authorization.actor.id,draft_version)).rowcount
                if updated!=1:raise HTTPException(409,'Le brouillon a changé pendant sa reconstruction. Aucun candidat créé.')
            audit(db,authorization.actor,'deployment.prepare',str(key),service['id'],{'deployment_id':candidate})
        return self.public(self.candidate(candidate))

    def routes(self):
        api=APIRouter(prefix='/api')

        @api.post('/functions/{key}/deployments',status_code=201)
        async def prepare(request:Request,key:UUID,data:DeploymentCreate):
            return await self.prepare(request,key,data)

        @api.post('/functions/{key}/code-deployments',status_code=201)
        async def prepare_code(request:Request,key:UUID,data:CodeDeploymentCreate):
            return await self.prepare(request,key,data)

        @api.get('/functions/{key}/deployments')
        async def candidates(request:Request,key:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
            await self.identity.admin(request)
            self.expire()
            with closing(self.database.connect()) as db:
                db.execute('BEGIN')
                get(db,'functions',key)
                total=db.execute('SELECT count(*) FROM deployments WHERE function_id=?',(str(key),)).fetchone()[0]
                rows=db.execute('SELECT * FROM deployments WHERE function_id=? ORDER BY created_at DESC,id LIMIT ? OFFSET ?',(str(key),limit,offset)).fetchall()
                return {'items':[self.public(row) for row in rows],'total':total}

        @api.delete('/deployments/{key}')
        async def abandon(request:Request,key:UUID):
            row=await self.read_candidate(request,key);authorization=await self.access(request,row)
            self.expire()
            with self.database.transaction() as db:
                row=dict(db.execute('SELECT * FROM deployments WHERE id=?',(str(key),)).fetchone())
                self.identity.recheck(db,authorization,row['service_id'],row['required_right'],row['function_id'])
                get(db,'functions',row['function_id']);get(db,'services',row['service_id'])
                if row['state']!='prepared':raise HTTPException(409,'Seul un candidat en attente d’archive peut être abandonné.')
                db.execute("UPDATE deployments SET state='failed',error_code='candidate_abandoned',configuration_cipher=NULL,completed_at=? WHERE id=?",(time.time(),str(key)))
                audit(db,authorization.actor,'deployment.abandon',row['function_id'],row['service_id'],{'deployment_id':str(key)})
            return self.public(self.candidate(key))

        @api.get('/deployments/{key}')
        async def status(request:Request,key:UUID):
            row=await self.read_candidate(request,key);await self.access(request,row);self.expire()
            return self.public(self.candidate(key))

        @api.put('/deployments/{key}/artifact')
        async def upload(request:Request,key:UUID):
            operation=str(uuid4())
            async with self.operations.responsibility(operation):return await self.upload(request,key,operation)

        # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#lecture-autorisée
        async def read_authorization(request,key):
            function=self.database.one('SELECT service_id FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
            authorization=await self.identity.operation(request,function['service_id'] if function else '','read',str(key))
            if not function:raise HTTPException(404,'Fonction introuvable.')
            return authorization

        def readable_function(db,authorization,key):
            function=db.execute('''SELECT f.* FROM functions f
                JOIN services s ON s.id=f.service_id AND s.deleted_at IS NULL
                JOIN namespaces n ON n.id=s.namespace_id AND n.deleted_at IS NULL
                WHERE f.id=? AND f.deleted_at IS NULL''',(str(key),)).fetchone()
            if not function:raise HTTPException(404,'Fonction ou service introuvable.')
            self.identity.recheck(db,authorization,function['service_id'],'read',str(key))
            return function

        @api.get('/functions/{key}/revisions')
        async def revisions(request:Request,key:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
            authorization=await read_authorization(request,key)
            with closing(self.database.connect()) as db:
                db.execute('BEGIN')
                function=readable_function(db,authorization,key)
                rows=[dict(row) for row in db.execute('''SELECT id,function_id,handler,runtime,architecture,image_id,
                    archive_sha256,events_json,stored_bytes,created_at,code_hash FROM revisions
                    WHERE function_id=? AND deleted_at IS NULL ORDER BY created_at DESC,id LIMIT ? OFFSET ?''',(str(key),limit,offset))]
                for row in rows:row['events']=json.loads(row.pop('events_json'));row['active']=row['id']==function['active_revision_id']
                return {'items':rows}

        # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#promotion-et-droits
        @api.post('/functions/{key}/rollback')
        async def rollback(request:Request,key:UUID,data:Rollback):
            # Authorize Update before looking up any alias; the hash authority
            # then rechecks the credential and the parent in its own decision.
            await self.versions.authorization(request,key,'update')
            revision=self.database.one('SELECT code_hash FROM revisions WHERE id=? AND function_id=?',
                                       (str(data.revision_id),str(key)))
            if not revision or not revision['code_hash']:raise HTTPException(404,'Révision introuvable.')
            return await self.versions.promote(request,key,revision['code_hash'],legacy=True)

        @api.delete('/functions/{key}/revisions/{revision_id}')
        async def delete_revision(request:Request,key:UUID,revision_id:UUID):
            await self.versions.authorization(request,key,'update')
            revision=self.database.one('SELECT code_hash FROM revisions WHERE id=? AND function_id=?',
                                       (str(revision_id),str(key)))
            if not revision or not revision['code_hash']:raise HTTPException(404,'Révision introuvable.')
            from .models import VersionDisposition
            result=await self.versions.disposition(request,key,revision['code_hash'],'deleted',VersionDisposition())
            return {'deleted':True,**result}

        api.include_router(self.versions.routes(),prefix='')

        return api
