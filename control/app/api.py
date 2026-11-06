# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#gestion | docs/SCHEMA.md
# Management routes, service scope, safe representations and durable mutations.
import json
import secrets
import sqlite3
import time
from uuid import UUID,uuid4

from fastapi import APIRouter,HTTPException,Query,Request

from .auth import digest
from .db import audit
from .deployments import get as current_object
from .function_operations import storage_configuration
from .models import Configuration,FunctionCreate,Named,ServiceCreate,TokenCreate


def router(database,identity,vault,operations):
    api=APIRouter(prefix='/api')

    def get(table,key):
        row=database.one(f'SELECT * FROM {table} WHERE id=? AND deleted_at IS NULL',(str(key),))
        if not row:raise HTTPException(404,'Ressource introuvable.')
        return row

    def public(row):
        result=dict(row)
        for column in ('environment_json','policy_json','config_json'):
            if column in result:result[column.removesuffix('_json')]=json.loads(result.pop(column))
        if 'secrets_cipher' in result:result['secret_names']=sorted(vault.open(result.pop('secrets_cipher')))
        if 'config' in result:result['storage_operation']=operations.summary(result['id'])
        return result

    def configuration(row,data):
        env=data.environment if 'environment' in data.model_fields_set else json.loads(row.get('environment_json','{}'))
        secured=vault.open(row['secrets_cipher']) if row.get('secrets_cipher') else {}
        for name,value in data.secrets.items():
            if value is None:secured.pop(name,None)
            else:secured[name]=value
        if len(secured)>128:raise HTTPException(422,'La configuration ne peut contenir plus de 128 secrets.')
        if set(env)&set(secured):raise HTTPException(422,'Une variable ne peut pas être aussi un secret.')
        return json.dumps(env),vault.seal(secured)

    def current_version(request,row):
        expected=request.headers.get('if-match')
        if expected is not None and expected!=str(row['updated_at']):
            raise HTTPException(409,'Cet objet a été modifié dans une autre session. Conservez votre saisie puis rechargez ses valeurs.')

    async def function_actor(request,key,right):
        row=database.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        actor=await identity.authorize(request,row['service_id'] if row else '',right,str(key))
        if not row:raise HTTPException(404,'Fonction introuvable.')
        row=get('functions',key)
        get('services',row['service_id'])
        return row,actor

    async def function_authorization(request,key,right):
        row=database.one('SELECT * FROM functions WHERE id=? AND deleted_at IS NULL',(str(key),))
        authorization=await identity.operation(request,row['service_id'] if row else '',right,str(key))
        if not row:raise HTTPException(404,'Fonction introuvable.')
        return authorization

    def token_public(row):
        data=dict(row);data.pop('digest',None)
        data['rights']=json.loads(data.pop('rights_json'))
        restricted=data.pop('function_ids_json')
        data['function_ids']=json.loads(restricted) if restricted is not None else None
        return data

    def create_token(db,service_id,data,actor):
        identifiers=[str(value) for value in data.function_ids] if data.function_ids is not None else None
        if identifiers is not None:
            for key in identifiers:
                if not db.execute('SELECT 1 FROM functions WHERE id=? AND service_id=? AND deleted_at IS NULL',(key,service_id)).fetchone():
                    raise HTTPException(422,'La portée contient une fonction étrangère ou absente.')
        key=str(uuid4());value='p2s_'+secrets.token_urlsafe(32)
        row=(key,service_id,data.name,digest(value),value[:12],json.dumps(data.rights),
             json.dumps(identifiers) if identifiers is not None else None,data.expires_at,None,time.time(),None)
        db.execute('INSERT INTO service_tokens VALUES (?,?,?,?,?,?,?,?,?,?,?)',row)
        audit(db,actor,'token.create',key,service_id,{'rights':data.rights})
        result=token_public(db.execute('SELECT * FROM service_tokens WHERE id=?',(key,)).fetchone())
        result['token']=value
        return result

    @api.get('/namespaces')
    async def namespaces(request:Request,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        await identity.admin(request)
        return {'items':database.all('SELECT * FROM namespaces WHERE deleted_at IS NULL ORDER BY name,id LIMIT ? OFFSET ?',(limit,offset))}

    @api.post('/namespaces',status_code=201)
    async def create_namespace(request:Request,data:Named):
        actor=await identity.admin(request,True);key=str(uuid4());now=time.time()
        with database.transaction() as db:
            db.execute('INSERT INTO namespaces VALUES (?,?,?,?,?,NULL)',(key,data.name,data.description,now,now))
            audit(db,actor,'namespace.create',key)
        return public(get('namespaces',key))

    @api.get('/namespaces/{key}')
    async def read_namespace(request:Request,key:UUID):
        await identity.admin(request);return public(get('namespaces',key))

    @api.put('/namespaces/{key}')
    async def update_namespace(request:Request,key:UUID,data:Named):
        actor=await identity.admin(request,True);row=get('namespaces',key);current_version(request,row)
        with database.transaction() as db:
            db.execute('UPDATE namespaces SET name=?,description=?,updated_at=? WHERE id=?',(data.name,data.description,time.time(),str(key)))
            audit(db,actor,'namespace.update',str(key))
        return public(get('namespaces',key))

    @api.delete('/namespaces/{key}')
    async def delete_namespace(request:Request,key:UUID):
        actor=await identity.admin(request,True);get('namespaces',key)
        with database.transaction() as db:
            if db.execute('SELECT 1 FROM services WHERE namespace_id=? AND deleted_at IS NULL',(str(key),)).fetchone():raise HTTPException(409,'Supprimez d’abord les services de ce namespace.')
            db.execute('UPDATE namespaces SET deleted_at=? WHERE id=?',(time.time(),str(key)))
            audit(db,actor,'namespace.delete',str(key))
        return {'deleted':True}

    @api.get('/namespaces/{key}/services')
    async def services(request:Request,key:UUID,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        await identity.admin(request);get('namespaces',key)
        return {'items':[public(row) for row in database.all('SELECT * FROM services WHERE namespace_id=? AND deleted_at IS NULL ORDER BY name,id LIMIT ? OFFSET ?',(str(key),limit,offset))]}

    @api.post('/namespaces/{key}/services',status_code=201)
    async def create_service(request:Request,key:UUID,data:ServiceCreate):
        actor=await identity.admin(request,True);get('namespaces',key)
        service_id=str(uuid4());now=time.time()
        with database.transaction() as db:
            db.execute('INSERT INTO services VALUES (?,?,?,?,?,?,?,?,?,NULL)',(
                service_id,str(key),data.name,data.description,data.policy.model_dump_json(),'{}',vault.seal({}),now,now))
            audit(db,actor,'service.create',service_id,service_id)
        return public(get('services',service_id))

    @api.get('/services/{key}')
    async def read_service(request:Request,key:UUID):
        await identity.authorize(request,str(key),'read')
        return public(get('services',key))

    @api.put('/services/{key}')
    async def update_service(request:Request,key:UUID,data:ServiceCreate):
        actor=await identity.admin(request,True);row=get('services',key);current_version(request,row)
        with database.transaction() as db:
            operations.service_available(db,str(key))
            db.execute('UPDATE services SET name=?,description=?,policy_json=?,updated_at=? WHERE id=?',(
                data.name,data.description,data.policy.model_dump_json(),time.time(),str(key)))
            audit(db,actor,'service.update',str(key),str(key))
        return public(get('services',key))

    @api.delete('/services/{key}')
    async def delete_service(request:Request,key:UUID):
        actor=await identity.admin(request,True);get('services',key)
        with database.transaction() as db:
            operations.service_available(db,str(key))
            if db.execute('SELECT 1 FROM functions WHERE service_id=? AND deleted_at IS NULL',(str(key),)).fetchone():raise HTTPException(409,'Supprimez d’abord les fonctions de ce service.')
            db.execute('UPDATE services SET deleted_at=? WHERE id=?',(time.time(),str(key)))
            db.execute('UPDATE service_tokens SET revoked_at=? WHERE service_id=? AND revoked_at IS NULL',(time.time(),str(key)))
            audit(db,actor,'service.delete',str(key),str(key))
        return {'deleted':True}

    @api.put('/services/{key}/configuration')
    async def configure_service(request:Request,key:UUID,data:Configuration):
        actor=await identity.authorize(request,str(key),'update')
        if actor.functions is not None:raise HTTPException(403,'Un jeton limité à des fonctions ne modifie pas la configuration globale.')
        row=get('services',key);current_version(request,row);env,secured=configuration(row,data)
        with database.transaction() as db:
            operations.service_available(db,str(key))
            db.execute('UPDATE services SET environment_json=?,secrets_cipher=?,updated_at=? WHERE id=?',(env,secured,time.time(),str(key)))
            audit(db,actor,'service.configure',str(key),str(key))
        return public(get('services',key))

    @api.get('/services/{key}/functions')
    async def functions(request:Request,key:UUID,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        actor=await identity.authorize(request,str(key),'read');get('services',key)
        sql='SELECT * FROM functions WHERE service_id=? AND deleted_at IS NULL';args=[str(key)]
        if actor.functions is not None:
            sql+=' AND id IN ('+','.join('?' for _ in actor.functions)+')';args.extend(actor.functions)
        sql+=' ORDER BY name,id LIMIT ? OFFSET ?';args.extend([limit,offset])
        return {'items':[public(row) for row in database.all(sql,args)]}

    @api.post('/services/{key}/functions',status_code=201)
    async def create_function(request:Request,key:UUID,data:FunctionCreate):
        function_id=str(uuid4());operation=str(uuid4())
        authorization=await identity.operation(request,str(key),'create',function_id)
        if authorization.actor.functions is not None:raise HTTPException(403,'Create exige une portée sur le service entier.')
        env,secured=configuration({},data.configuration)
        async with operations.responsibility(operation):
            with database.transaction() as db:
                service=current_object(db,'services',key)
                identity.recheck(db,authorization,str(key),'create',function_id)
                if db.execute('SELECT 1 FROM functions WHERE service_id=? AND name=? AND deleted_at IS NULL',(str(key),data.name)).fetchone():
                    raise HTTPException(409,'Ce nom de fonction existe déjà dans ce service.')
                operations.reserve(db,operation,{'id':function_id},service,storage_configuration(data.config.model_dump()))
            await operations.prepare(operation)
            authorization=await identity.operation(request,str(key),'create',function_id)
            with database.transaction() as db:
                service=current_object(db,'services',key)
                identity.recheck(db,authorization,str(key),'create',function_id)
                operations.verify(db,operation,{'id':function_id},service)
                operations.minimum_budget(db,function_id,data.config.model_dump())
                now=time.time()
                db.execute('INSERT INTO functions VALUES (?,?,?,?,?,?,NULL,?,?,NULL)',(
                    function_id,str(key),data.name,data.config.model_dump_json(),env,secured,now,now))
                operations.commit(db,operation)
                audit(db,authorization.actor,'function.create',function_id,str(key))
        return public(get('functions',function_id))

    @api.get('/functions/{key}')
    async def read_function(request:Request,key:UUID):
        row,_=await function_actor(request,key,'read');return public(row)

    @api.put('/functions/{key}')
    async def update_function(request:Request,key:UUID,data:FunctionCreate):
        authorization=await function_authorization(request,key,'update');operation=str(uuid4())
        async with operations.responsibility(operation):
            with database.transaction() as db:
                row=current_object(db,'functions',key);service=current_object(db,'services',row['service_id'])
                identity.recheck(db,authorization,row['service_id'],'update',str(key));current_version(request,row)
                operations.function_available(db,str(key));previous=json.loads(row['config_json'])
                if row['active_revision_id'] and any(getattr(data.config,name)!=previous[name] for name in ('handler','runtime')):
                    raise HTTPException(409,'Un changement de handler ou de runtime exige un nouveau déploiement.')
                env,secured=configuration(row,data.configuration)
                changed=storage_configuration(previous)!=storage_configuration(data.config.model_dump())
                if changed:operations.reserve(db,operation,row,service,storage_configuration(data.config.model_dump()))
                else:
                    operations.minimum_budget(db,str(key),data.config.model_dump())
                    db.execute('UPDATE functions SET name=?,config_json=?,environment_json=?,secrets_cipher=?,updated_at=? WHERE id=?',(
                        data.name,data.config.model_dump_json(),env,secured,time.time(),str(key)))
                    audit(db,authorization.actor,'function.update',str(key),row['service_id'])
            if changed:
                await operations.prepare(operation)
                authorization=await identity.operation(request,row['service_id'],'update',str(key))
                with database.transaction() as db:
                    row=current_object(db,'functions',key);service=current_object(db,'services',row['service_id'])
                    identity.recheck(db,authorization,row['service_id'],'update',str(key))
                    operations.verify(db,operation,row,service)
                    operations.minimum_budget(db,str(key),data.config.model_dump())
                    db.execute('UPDATE functions SET name=?,config_json=?,environment_json=?,secrets_cipher=?,updated_at=? WHERE id=?',(
                        data.name,data.config.model_dump_json(),env,secured,time.time(),str(key)))
                    operations.commit(db,operation)
                    audit(db,authorization.actor,'function.update',str(key),row['service_id'])
        return public(get('functions',key))

    @api.delete('/functions/{key}')
    async def delete_function(request:Request,key:UUID):
        authorization=await function_authorization(request,key,'delete');operation=str(uuid4())
        async with operations.responsibility(operation):
            with database.transaction() as db:
                row=current_object(db,'functions',key);service=current_object(db,'services',row['service_id'])
                identity.recheck(db,authorization,row['service_id'],'delete',str(key));current_version(request,row)
                operations.reserve(db,operation,row,service)
            await operations.prepare(operation)
            authorization=await identity.operation(request,row['service_id'],'delete',str(key))
            with database.transaction() as db:
                row=current_object(db,'functions',key);service=current_object(db,'services',row['service_id'])
                identity.recheck(db,authorization,row['service_id'],'delete',str(key));operations.verify(db,operation,row,service)
                now=time.time()
                db.execute('UPDATE functions SET active_revision_id=NULL,deleted_at=?,updated_at=? WHERE id=?',(now,now,str(key)))
                db.execute("UPDATE deployments SET state='failed',error_code='function_deleted',configuration_cipher=NULL,completed_at=? WHERE function_id=? AND state IN ('prepared','receiving','validating')",(now,str(key)))
                operations.commit(db,operation)
                audit(db,authorization.actor,'function.delete',str(key),row['service_id'])
        return {'deleted':True,'data_policy':'archive'}

    @api.get('/services/{key}/tokens')
    async def tokens(request:Request,key:UUID,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        await identity.admin(request);get('services',key)
        return {'items':[token_public(row) for row in database.all('SELECT * FROM service_tokens WHERE service_id=? ORDER BY created_at DESC,id LIMIT ? OFFSET ?',(str(key),limit,offset))]}

    @api.post('/services/{key}/tokens',status_code=201)
    async def issue_token(request:Request,key:UUID,data:TokenCreate):
        actor=await identity.admin(request,True);get('services',key)
        with database.transaction() as db:return create_token(db,str(key),data,actor)

    @api.post('/tokens/{key}/revoke')
    async def revoke_token(request:Request,key:UUID):
        actor=await identity.admin(request,True)
        with database.transaction() as db:
            row=db.execute('SELECT * FROM service_tokens WHERE id=?',(str(key),)).fetchone()
            if not row:raise HTTPException(404,'Jeton introuvable.')
            db.execute('UPDATE service_tokens SET revoked_at=coalesce(revoked_at,?) WHERE id=?',(time.time(),str(key)))
            audit(db,actor,'token.revoke',str(key),row['service_id'])
        return {'revoked':True}

    @api.post('/tokens/{key}/rotate',status_code=201)
    async def rotate_token(request:Request,key:UUID):
        actor=await identity.admin(request,True)
        with database.transaction() as db:
            row=db.execute('SELECT * FROM service_tokens WHERE id=?',(str(key),)).fetchone()
            if not row:raise HTTPException(404,'Jeton introuvable.')
            if row['revoked_at'] is not None:raise HTTPException(409,'Ce jeton est déjà révoqué.')
            get('services',row['service_id'])
            if row['expires_at'] is not None and row['expires_at']<=time.time():raise HTTPException(409,'Ce jeton a expiré.')
            data=TokenCreate(name=row['name'],rights=json.loads(row['rights_json']),
                function_ids=json.loads(row['function_ids_json']) if row['function_ids_json'] else None,expires_at=row['expires_at'])
            db.execute('UPDATE service_tokens SET revoked_at=? WHERE id=?',(time.time(),str(key)))
            result=create_token(db,row['service_id'],data,actor)
            audit(db,actor,'token.rotate',str(key),row['service_id'],{'replacement_id':result['id']})
            return result

    @api.get('/services/{key}/audit')
    async def audit_events(request:Request,key:UUID,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
        actor=await identity.authorize(request,str(key),'read');get('services',key)
        sql='SELECT * FROM audit_events WHERE service_id=?';args=[str(key)]
        if actor.functions is not None:
            sql+=' AND object_id IN ('+','.join('?' for _ in actor.functions)+')';args.extend(actor.functions)
        rows=database.all(sql+' ORDER BY created_at DESC,id LIMIT ? OFFSET ?',[*args,limit,offset])
        for row in rows:row['detail']=json.loads(row.pop('detail_json'))
        return {'items':rows}

    return api
