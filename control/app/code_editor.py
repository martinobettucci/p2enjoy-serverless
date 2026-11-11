# @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md | docs/SCHEMA.md
"""Private encrypted patches over immutable artifacts; publication uses real Docker validation."""
from contextlib import contextmanager
import asyncio
import difflib
import hashlib
import io
import json
import os
import shutil
import stat
import time
import unicodedata
from typing import Literal
from uuid import UUID,uuid4
import zipfile

from fastapi import APIRouter,HTTPException,Query,Request
from pydantic import Field,ValidationError,field_validator,model_validator

from .artifacts import ArtifactError,BLOCK,MAX_ENTRIES,MAX_TOTAL,MAX_ZIP,open_directory,parent_fd,path_name
from .db import audit
from .deployments import MARGIN,blocking,required_version
from .function_versions import live_function,default_code_hash
from .models import Strict,CodeDeploymentCreate,Events,FunctionConfig

TEXT_LIMIT=1024**2
PATCH_LIMIT=4*1024**2
PATCH_FILES=128
CIPHER_LIMIT=64*1024**2


def checked_path(value,*,directory=False):
    if directory and value=='':return value
    try:
        name,is_directory,_=path_name(value.encode('utf8'),0x800)
        if is_directory:raise ValueError
    except (ArtifactError,UnicodeError,ValueError):
        raise HTTPException(422,'Chemin relatif de fichier ou dossier invalide.') from None
    return name


def text_bytes(value):
    try:raw=value.encode('utf8')
    except UnicodeError:raise HTTPException(422,'Le texte doit être un UTF-8 valide.') from None
    if len(raw)>TEXT_LIMIT:raise HTTPException(413,'Un fichier éditable est limité à 1 Mio UTF-8.')
    if any(unicodedata.category(c)=='Cc' and c not in '\t\r\n' for c in value):
        raise HTTPException(422,'Ce contenu contient des contrôles binaires.')
    return raw


class DraftCreate(Strict):
    base_code_hash:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')


class FileChange(Strict):
    action:Literal['write','delete','revert']
    path:str=Field(min_length=1,max_length=512)
    text:str|None=None

    @model_validator(mode='after')
    def content(self):
        if (self.action=='write') != (self.text is not None):
            raise ValueError('Seule une écriture exige un texte explicite.')
        return self


class DraftSave(Strict):
    handler:str|None=Field(default=None,min_length=3,max_length=256)
    file:FileChange|None=None

    @field_validator('handler')
    @classmethod
    def handler_path(cls,value):return FunctionConfig.handler_path(value) if value is not None else None

    @model_validator(mode='after')
    def mutation(self):
        if self.handler is None and self.file is None:raise ValueError('Aucune modification fournie.')
        return self


class DraftPublish(Strict):
    deployment_id:UUID
    draft_version:int=Field(ge=1,strict=True)


def descriptor(revision):
    if revision is None:return None
    return {k:revision[k] for k in ('id','code_hash','handler','runtime','architecture','image_id','created_at')}|{
        'events':json.loads(revision['events_json'])}


def inventory(revision):return {v['path']:v for v in json.loads(revision['inventory_json'])} if revision else {}


def metadata(path,raw,mode):
    return {'path':path,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mode':mode}


def effective_inventory(base,changes):
    result=inventory(base)
    for path,change in changes.items():
        if change is None:result.pop(path,None)
        else:result[path]=metadata(path,change['text'].encode('utf8'),change['mode'])
    folders=set()
    for path in result:
        parts=path.split('/')
        for index in range(1,len(parts)):
            parent='/'.join(parts[:index])
            if parent in result:raise HTTPException(422,'Collision entre fichier et dossier.')
            folders.add(parent)
    if len(result)>MAX_ENTRIES or len(folders)>MAX_ENTRIES:
        raise HTTPException(413,'Trop de fichiers ou dossiers dans ce paquet.')
    if sum(v['size'] for v in result.values())>MAX_TOTAL:
        raise HTTPException(413,'Le paquet extrait dépasse 256 Mio.')
    return result


def file_description(item,raw=None):
    result=dict(item)|{'kind':'file','executable':bool(int(item['mode'],8)&0o111),
                       'dependency':'node_modules' in item['path'].split('/')}
    if item['size']>TEXT_LIMIT:return result|{'editable':False,'reason':'text_limit'}
    try:
        text=raw.decode('utf8')
        if any(unicodedata.category(c)=='Cc' and c not in '\t\r\n' for c in text):raise ValueError
    except (UnicodeError,ValueError):return result|{'editable':False,'reason':'binary'}
    return result|{'editable':True,'reason':None,'text':text}


class BoundedArchive(io.BytesIO):
    def write(self,data):
        if self.tell()+len(data)>MAX_ZIP:raise HTTPException(413,'Le ZIP reconstruit dépasse 64 Mio.')
        return super().write(data)


class CodeEditor:
    def __init__(self,deployments):
        self.deployments=deployments
        self.db,self.identity,self.vault=deployments.database,deployments.identity,deployments.vault
        self.building=False

    async def authorization(self,request,key):
        function=self.db.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        right='update' if self.db.one('SELECT 1 FROM revisions WHERE function_id=?',(str(key),)) else 'create'
        return await self.identity.operation(request,function['service_id'] if function else '',right,str(key)),right

    def checked(self,db,key,authorization,right):
        function=live_function(db,key)
        current='update' if db.execute('SELECT 1 FROM revisions WHERE function_id=?',(str(key),)).fetchone() else 'create'
        if current!=right:raise HTTPException(409,'La première publication a changé les droits requis. Relisez la fonction.')
        self.identity.recheck(db,authorization,function['service_id'],right,str(key))
        self.deployments.operations.function_available(db,str(key))
        return function

    def context(self,db,function):
        return {'function_id':function['id'],'function_version':function['updated_at'],
                'current_code_hash':default_code_hash(db,function)}

    def own(self,db,key,authorization,*,optional=False):
        row=db.execute('SELECT * FROM code_drafts WHERE function_id=? AND actor_kind=? AND actor_id=?',
                       (str(key),authorization.actor.kind,authorization.actor.id)).fetchone()
        if not row and not optional:raise HTTPException(404,'Aucun brouillon personnel enregistré.')
        return dict(row) if row else None

    def summary(self,row):
        if row is None:return None
        return {k:row[k] for k in ('id','version','handler','base_function_version','created_at','updated_at',
                                  'change_bytes','last_deployment_id','last_publication_version')}|{
            'base':json.loads(row['base_descriptor_json']),
            'changed_paths':len(self.vault.open(row['changes_cipher']))}

    @staticmethod
    def draft_version(request,row):
        value=request.headers.get('if-match')
        if value is None:raise HTTPException(428,'If-Match du brouillon est obligatoire.')
        if value!=str(row['version']):raise HTTPException(409,'Ce brouillon a changé. Conservez vos saisies et relisez sa version.')

    @staticmethod
    def base(db,row):
        if row['base_revision_id'] is None:return None
        revision=db.execute('SELECT * FROM revisions WHERE id=? AND function_id=? AND stored_bytes>0',
                            (row['base_revision_id'],row['function_id'])).fetchone()
        if not revision:raise HTTPException(409,'La base du brouillon est indisponible.')
        return dict(revision)

    @staticmethod
    def source(db,function,version):
        if version is not None:
            row=db.execute('''SELECT r.* FROM function_versions v JOIN revisions r ON r.id=v.revision_id
                AND r.function_id=v.function_id AND r.code_hash=v.code_hash
                WHERE v.function_id=? AND v.code_hash=? AND v.state IN ('available','archived')
                AND r.deleted_at IS NULL AND r.stored_bytes>0''',(function['id'],version)).fetchone()
            if not row:raise HTTPException(404,'Cette source de code est indisponible.')
            return dict(row)
        if function['active_revision_id']:
            row=db.execute('SELECT * FROM revisions WHERE id=? AND function_id=? AND deleted_at IS NULL AND stored_bytes>0',
                           (function['active_revision_id'],function['id'])).fetchone()
            if not row:raise HTTPException(409,'La source promue est indisponible.')
            return dict(row)
        return None

    @contextmanager
    def file_stream(self,base,item):
        root=open_directory(self.deployments.root/str(UUID(base['id']))/'code')
        parent=None;fd=None
        try:
            parent=parent_fd(root,item['path'].split('/')[:-1])
            fd=os.open(item['path'].split('/')[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            row=os.fstat(fd)
            if (not stat.S_ISREG(row.st_mode) or row.st_size!=item['size'] or
                    bool(row.st_mode&0o111)!=bool(int(item['mode'],8)&0o111)):
                raise ArtifactError('source_inventory_mismatch')
            with os.fdopen(fd,'rb') as stream:
                fd=None;yield stream
        finally:
            if fd is not None:os.close(fd)
            if parent is not None:os.close(parent)
            os.close(root)

    def read_bytes(self,base,item):
        # Large files are verified in bounded chunks, never accumulated in an editor response.
        if item['size']>TEXT_LIMIT:
            count=0;sha=hashlib.sha256()
            with self.file_stream(base,item) as stream:
                while block:=stream.read(BLOCK):
                    count+=len(block)
                    if count>item['size']:raise ArtifactError('source_inventory_mismatch')
                    sha.update(block)
            if count!=item['size'] or sha.hexdigest()!=item['sha256']:raise ArtifactError('source_inventory_mismatch')
            return None
        with self.file_stream(base,item) as stream:raw=stream.read(TEXT_LIMIT+1)
        if len(raw)!=item['size'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ArtifactError('source_inventory_mismatch')
        return raw

    def read_file(self,base,changes,path):
        files=effective_inventory(base,changes);item=files.get(path)
        if item is None:raise HTTPException(404,'Fichier introuvable.')
        change=changes.get(path)
        raw=change['text'].encode('utf8') if change else self.read_bytes(base,item)
        return file_description(item,raw)

    def tree(self,base,changes,directory,search,limit,offset):
        files=effective_inventory(base,changes);rows={};prefix=directory+'/' if directory else ''
        for path,item in files.items():
            if not path.startswith(prefix):continue
            tail=path[len(prefix):]
            if search:
                if search.casefold() in path.casefold():rows[path]=item|{'kind':'file'}
            elif '/' in tail:
                folder=prefix+tail.split('/')[0]
                rows[folder]={'kind':'directory','path':folder}
            else:rows[path]=item|{'kind':'file'}
        ordered=sorted(rows.values(),key=lambda v:(v['kind']!='directory',v['path']))
        result=[]
        for row in ordered[offset:offset+limit]:
            if row['kind']=='directory':result.append(row)
            else:
                view=self.read_file(base,changes,row['path']);view.pop('text',None);result.append(view)
        return {'items':result,'total':len(ordered),'limit':limit,'offset':offset,'directory':directory,'search':search}

    async def io(self,work,*args):
        try:return await blocking(work,*args)
        except (OSError,ArtifactError,zipfile.BadZipFile,zipfile.LargeZipFile):
            raise HTTPException(503,'Les fichiers de code ne sont pas lisibles de manière sûre.') from None

    def quota(self,db,cipher,*,previous=None):
        occupied=db.execute('SELECT coalesce(sum(length(changes_cipher)),0) FROM code_drafts').fetchone()[0]
        if occupied+len(cipher)-(len(previous) if previous else 0)>CIPHER_LIMIT:
            raise HTTPException(507,'Le budget des brouillons chiffrés est épuisé.')
        if shutil.disk_usage(self.deployments.root).free<MARGIN:
            raise HTTPException(507,'La marge libre du disque est insuffisante pour enregistrer le brouillon.')

    async def read(self,request,key,*,draft=False,path=None,directory='',search='',limit=25,offset=0,version=None):
        authorization,right=await self.authorization(request,key)
        checked_path(directory,directory=True)
        if path is not None:checked_path(path)
        with self.deployments.source_reader():
            with self.db.transaction() as db:
                function=self.checked(db,key,authorization,right);context=self.context(db,function)
                if draft:
                    row=self.own(db,key,authorization);base=self.base(db,row);changes=self.vault.open(row['changes_cipher'])
                    context.update(draft=self.summary(row),source=descriptor(base))
                else:
                    base=self.source(db,function,version);changes={}
                    versions=db.execute('''SELECT code_hash,state,updated_at FROM function_versions
                        WHERE function_id=? AND state IN ('available','archived') ORDER BY updated_at DESC,code_hash LIMIT ? OFFSET ?''',
                        (str(key),limit,offset)).fetchall()
                    total=db.execute("SELECT count(*) FROM function_versions WHERE function_id=? AND state IN ('available','archived')",(str(key),)).fetchone()[0]
                    context.update(source=descriptor(base),selection_required=base is None and right=='update',
                                   versions={'items':[dict(v) for v in versions],'total':total,'limit':limit,'offset':offset})
            result=await self.io(self.read_file,base,changes,path) if path is not None else await self.io(self.tree,base,changes,directory,search,limit,offset)
            with self.db.transaction() as db:self.checked(db,key,authorization,right)
            return context|({'file':result} if path is not None else {'tree':result})

    async def create(self,request,key,data):
        authorization,right=await self.authorization(request,key)
        with self.deployments.source_reader():
            with self.db.transaction() as db:
                function=self.checked(db,key,authorization,right);required_version(request,function)
                if self.own(db,key,authorization,optional=True):raise HTTPException(409,'Un brouillon personnel existe déjà. Ouvrez-le ou abandonnez-le.')
                if data.base_code_hash is None and right=='update':
                    raise HTTPException(422,'Choisissez explicitement une version source conservée.')
                base=self.source(db,function,data.base_code_hash) if data.base_code_hash is not None else None
                actor=authorization.actor
                if db.execute('SELECT count(*) FROM code_drafts').fetchone()[0]>=128:
                    raise HTTPException(429,'La plateforme conserve déjà 128 brouillons. Abandonnez un brouillon inutilisé.')
                if db.execute('SELECT count(*) FROM code_drafts WHERE actor_kind=? AND actor_id=?',(actor.kind,actor.id)).fetchone()[0]>=32:
                    raise HTTPException(429,'Cet acteur conserve déjà 32 brouillons.')
                cipher=self.vault.seal({});self.quota(db,cipher);now=time.time()
                handler=base['handler'] if base else json.loads(function['config_json'])['handler']
                db.execute('''INSERT INTO code_drafts (id,function_id,actor_kind,actor_id,base_revision_id,
                    base_function_version,base_descriptor_json,handler,changes_cipher,change_bytes,version,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,0,1,?,?)''',
                    (str(uuid4()),str(key),actor.kind,actor.id,base['id'] if base else None,function['updated_at'],
                     json.dumps(descriptor(base)),handler,cipher,now,now))
                audit(db,actor,'code_draft.create',str(key),function['service_id'])
                return self.context(db,function)|{'draft':self.summary(self.own(db,key,authorization))}

    def apply(self,base,changes,data):
        result=dict(changes)
        if data.file:
            mutation=data.file;path=checked_path(mutation.path);base_item=inventory(base).get(path)
            if mutation.action=='revert':
                result.pop(path,None)
            elif mutation.action=='delete':
                current=self.read_file(base,changes,path)
                if not current['editable']:raise HTTPException(422,'Seuls les fichiers texte éditables peuvent être retirés.')
                if base_item:result[path]=None
                else:result.pop(path,None)
            else:
                raw=text_bytes(mutation.text);mode=base_item['mode'] if base_item else '0o444'
                if base_item:
                    previous=file_description(base_item,self.read_bytes(base,base_item))
                    if not previous['editable']:raise HTTPException(422,'Ce fichier binaire ou hors limite ne peut pas être remplacé par l’éditeur.')
                    if raw==previous['text'].encode('utf8'):
                        result.pop(path,None)
                    else:result[path]={'text':mutation.text,'mode':mode}
                else:result[path]={'text':mutation.text,'mode':mode}
        size=sum(len(change['text'].encode('utf8')) for change in result.values() if change is not None)
        if len(result)>PATCH_FILES or size>PATCH_LIMIT:
            raise HTTPException(413,'Un brouillon est limité à 128 chemins et 4 Mio de texte UTF-8.')
        effective_inventory(base,result)
        return result,size

    async def save(self,request,key,data,authorization,right):
        with self.db.transaction() as db:
            self.checked(db,key,authorization,right);row=self.own(db,key,authorization);self.draft_version(request,row)
            base=self.base(db,row);changes=self.vault.open(row['changes_cipher'])
        updated,size=await self.io(self.apply,base,changes,data)
        handler=data.handler if data.handler is not None else row['handler']
        changed=updated!=changes or handler!=row['handler']
        cipher=self.vault.seal(updated) if changed else row['changes_cipher']
        with self.db.transaction() as db:
            function=self.checked(db,key,authorization,right);current=self.own(db,key,authorization);self.draft_version(request,current)
            if current['id']!=row['id']:raise HTTPException(409,'Le brouillon a été remplacé.')
            if changed:
                self.quota(db,cipher,previous=current['changes_cipher'])
                db.execute('UPDATE code_drafts SET handler=?,changes_cipher=?,change_bytes=?,version=version+1,updated_at=? WHERE id=?',
                           (handler,cipher,size,time.time(),row['id']))
                audit(db,authorization.actor,'code_draft.save',str(key),function['service_id'],{'draft_version':row['version']+1})
            return self.context(db,function)|{'draft':self.summary(self.own(db,key,authorization)),'changed':changed}

    def difference(self,base,changes,current,path,limit,offset):
        before=inventory(current);after=effective_inventory(base,changes);rows=[]
        for name in sorted(before.keys()|after.keys()):
            left,right=before.get(name),after.get(name)
            if left and right and all(left[k]==right[k] for k in ('size','sha256','mode')):continue
            rows.append({'path':name,'change':'added' if left is None else 'deleted' if right is None else 'modified',
                         'before':left,'after':right})
        result={'items':rows[offset:offset+limit],'total':len(rows),'limit':limit,'offset':offset}
        if path is None:return result
        left=self.read_file(current,{},path) if path in before else None
        right=self.read_file(base,changes,path) if path in after else None
        result['file']={'path':path,'before':{k:v for k,v in left.items() if k!='text'} if left else None,
                        'after':{k:v for k,v in right.items() if k!='text'} if right else None}
        if left is None and right is None:raise HTTPException(404,'Fichier absent de cette comparaison.')
        if any(v is not None and not v['editable'] for v in (left,right)):
            result['file'].update(reason='binary_or_text_limit',diff=None,truncated=False);return result
        lines=[(v['text'] if v else '').splitlines(keepends=True) for v in (left,right)]
        if any(len(v)>2000 for v in lines):
            result['file'].update(reason='line_limit',diff=None,truncated=False);return result
        pieces=[];length=0;truncated=False
        for line in difflib.unified_diff(*lines,fromfile='cible/'+path,tofile='brouillon/'+path):
            raw=line.encode('utf8')
            if length+len(raw)>128*1024:truncated=True;break
            pieces.append(line);length+=len(raw)
        result['file'].update(reason='output_limit' if truncated else None,diff=''.join(pieces),truncated=truncated,
                              before_final_newline=left['text'].endswith(('\n','\r')) if left else None,
                              after_final_newline=right['text'].endswith(('\n','\r')) if right else None)
        return result

    def archive(self,base,changes):
        files=effective_inventory(base,changes)
        if not files:raise HTTPException(422,'Ajoutez au moins un fichier avant publication.')
        with BoundedArchive() as output:
            with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as archive:
                for path,item in sorted(files.items()):
                    info=zipfile.ZipInfo(path,date_time=(1980,1,1,0,0,0));info.create_system=3
                    info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(stat.S_IFREG|int(item['mode'],8))<<16
                    info.file_size=item['size']
                    with archive.open(info,'w',force_zip64=False) as target:
                        change=changes.get(path)
                        if change is not None:target.write(change['text'].encode('utf8'))
                        else:
                            count=0;sha=hashlib.sha256()
                            with self.file_stream(base,item) as source:
                                while block:=source.read(BLOCK):
                                    count+=len(block)
                                    if count>item['size']:raise ArtifactError('source_inventory_mismatch')
                                    sha.update(block);target.write(block)
                            if count!=item['size'] or sha.hexdigest()!=item['sha256']:raise ArtifactError('source_inventory_mismatch')
            return output.getvalue()

    async def publish(self,request,key,data):
        authorization,right=await self.authorization(request,key)
        if self.building:raise HTTPException(429,'Une publication de brouillon est déjà en cours.',headers={'Retry-After':'5'})
        self.building=True
        try:
            with self.deployments.source_reader():
                with self.db.transaction() as db:
                    function=self.checked(db,key,authorization,right);required_version(request,function)
                    row=self.own(db,key,authorization)
                    if row['version']!=data.draft_version:raise HTTPException(409,'La version du brouillon a changé.')
                    base=self.base(db,row);changes=self.vault.open(row['changes_cipher'])
                archive=await self.io(self.archive,base,changes)
            events=json.loads(row['base_descriptor_json'])
            candidate=CodeDeploymentCreate(handler=row['handler'],deployment_id=data.deployment_id,
                                           events=Events.model_validate(events['events'] if events else {'http':[],'schedules':[]}))
            await self.deployments.prepare(request,key,candidate,editor_draft=(row['id'],row['version']))
            async def stream():
                for offset in range(0,len(archive),BLOCK):yield memoryview(archive)[offset:offset+BLOCK]
            operation=str(uuid4())
            async with self.deployments.operations.responsibility(operation):
                return await self.deployments.upload(request,str(data.deployment_id),operation,archive_stream=stream())
        finally:self.building=False

    def routes(self):
        api=APIRouter(prefix='/api/functions')

        @api.get('/{key}/code-sources')
        async def sources(request:Request,key:UUID,version:str|None=Query(None,pattern=r'^[0-9a-f]{64}$'),
                          directory:str=Query('',max_length=512),search:str=Query('',max_length=200),
                          limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0,le=20000)):
            return await self.read(request,key,version=version,directory=directory,search=search,limit=limit,offset=offset)

        @api.get('/{key}/code-sources/file')
        async def source_file(request:Request,key:UUID,path:str=Query(...,min_length=1,max_length=512),
                              version:str|None=Query(None,pattern=r'^[0-9a-f]{64}$')):
            return await self.read(request,key,version=version,path=path)

        @api.get('/{key}/code-draft')
        async def draft(request:Request,key:UUID):
            authorization,right=await self.authorization(request,key)
            with self.db.transaction() as db:
                function=self.checked(db,key,authorization,right)
                return self.context(db,function)|{'draft':self.summary(self.own(db,key,authorization,optional=True))}

        @api.post('/{key}/code-draft',status_code=201)
        async def create(request:Request,key:UUID,data:DraftCreate):return await self.create(request,key,data)

        @api.put('/{key}/code-draft')
        async def save(request:Request,key:UUID):
            authorization,right=await self.authorization(request,key)
            with self.db.transaction() as db:self.checked(db,key,authorization,right)
            with self.deployments.source_reader():
                request.state.source_edit_authorized=True
                try:
                    async with asyncio.timeout(30):data=DraftSave.model_validate(await request.json())
                except TimeoutError:raise HTTPException(408,'Le délai de réception du brouillon est dépassé.') from None
                except (ValueError,UnicodeError,ValidationError):raise HTTPException(422,'Données de brouillon invalides.') from None
                return await self.save(request,key,data,authorization,right)

        @api.delete('/{key}/code-draft')
        async def discard(request:Request,key:UUID):
            authorization,right=await self.authorization(request,key)
            with self.db.transaction() as db:
                function=self.checked(db,key,authorization,right);row=self.own(db,key,authorization);self.draft_version(request,row)
                db.execute('DELETE FROM code_drafts WHERE id=?',(row['id'],))
                audit(db,authorization.actor,'code_draft.discard',str(key),function['service_id'])
                return {'discarded':True}

        @api.get('/{key}/code-draft/files')
        async def files(request:Request,key:UUID,directory:str=Query('',max_length=512),search:str=Query('',max_length=200),
                        limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0,le=20000)):
            return await self.read(request,key,draft=True,directory=directory,search=search,limit=limit,offset=offset)

        @api.get('/{key}/code-draft/file')
        async def file(request:Request,key:UUID,path:str=Query(...,min_length=1,max_length=512)):
            return await self.read(request,key,draft=True,path=path)

        @api.get('/{key}/code-draft/diff')
        async def difference(request:Request,key:UUID,path:str|None=Query(None,min_length=1,max_length=512),
                             limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0,le=40000)):
            authorization,right=await self.authorization(request,key)
            if path is not None:checked_path(path)
            with self.deployments.source_reader():
                with self.db.transaction() as db:
                    function=self.checked(db,key,authorization,right);row=self.own(db,key,authorization)
                    base=self.base(db,row);current=self.source(db,function,None);changes=self.vault.open(row['changes_cipher'])
                    context=self.context(db,function)|{'draft':self.summary(row),'comparison':{'before':descriptor(current),'after':{
                        **(descriptor(base) or {}),'handler':row['handler']}}}
                result=await self.io(self.difference,base,changes,current,path,limit,offset)
                with self.db.transaction() as db:self.checked(db,key,authorization,right)
                return context|{'diff':result}

        @api.post('/{key}/code-draft/publish')
        async def publish(request:Request,key:UUID,data:DraftPublish):return await self.publish(request,key,data)
        return api
