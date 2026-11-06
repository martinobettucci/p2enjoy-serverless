# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#instances-avec-baux-gérés
"""Bounded production client of the host storage agent; mutations are never replayed."""
import asyncio
from contextlib import suppress
import json
import os
from pathlib import Path
import re
import sys
from uuid import UUID


class StorageError(Exception):
    def __init__(self,code,*,uncertain=False):
        super().__init__(code);self.uncertain=uncertain


def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('duplicate_key')
        value[key]=item
    return value


def identifier(value):
    if not isinstance(value,str) or str(UUID(value))!=value:raise ValueError('invalid_uuid')
    return value


def volumes(value):
    if not isinstance(value,dict) or set(value)!={'data','cache'}:raise ValueError('invalid_storage_configuration')
    result={}
    for kind,item in value.items():
        if not isinstance(item,dict) or set(item)!={'enabled','quota_mib'} or type(item['enabled']) is not bool or type(item['quota_mib']) is not int or not 1<=item['quota_mib']<=65536:
            raise ValueError('invalid_storage_configuration')
        result[kind]=dict(item)
    return result


class StorageClient:
    def __init__(self,socket_path,root_host):
        self.socket=Path(socket_path);self.root=Path(root_host)
        if any(not p.is_absolute() or '..' in p.parts or p==Path('/') for p in (self.socket,self.root)):
            raise ValueError('invalid_storage_path')

    async def call(self,operation,**fields):
        payload=(json.dumps({'op':operation,**fields},separators=(',',':'),allow_nan=False)+'\n').encode()
        if len(payload)>16384:raise StorageError('storage_request_limit')
        writer=None;sent=False
        try:
            timeout=10 if operation in ('health','status','leases','check') else 60
            async with asyncio.timeout(timeout):
                reader,writer=await asyncio.open_unix_connection(self.socket,limit=65536)
                writer.write(payload);sent=True;await writer.drain()
                line=await reader.readuntil(b'\n')
                if len(line)>65536:raise ValueError('response_limit')
                result=json.loads(line,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
                if not isinstance(result,dict) or type(result.get('ok')) is not bool:raise ValueError('invalid_response')
                if result['ok']:
                    if set(result)!={'ok','result'} or not isinstance(result['result'],dict):raise ValueError('invalid_response')
                    return result['result']
                if set(result)!={'ok','error'} or not isinstance(result['error'],str) or not re.fullmatch('[a-z_]{1,64}',result['error']):raise ValueError('invalid_response')
                raise StorageError(result['error'])
        except (OSError,TimeoutError,asyncio.IncompleteReadError,asyncio.LimitOverrunError):
            raise StorageError('storage_transport',uncertain=sent) from None
        except (ValueError,UnicodeError,RecursionError):raise StorageError('storage_protocol',uncertain=sent) from None
        finally:
            if writer:
                writer.close()
                with suppress(OSError,TimeoutError):await asyncio.wait_for(writer.wait_closed(),1)

    async def leases(self,installation):
        installation=identifier(installation);result=[];after=None
        for _ in range(1024):
            page=await self.call('leases',installation_id=installation,**({'after':after} if after else {}))
            rows=page.get('leases');following=page.get('next')
            if set(page)!={'leases','next'} or not isinstance(rows,list) or len(rows)>50:raise StorageError('storage_protocol')
            previous=after or ''
            for row in rows:
                if not isinstance(row,dict) or set(row)!={'consumer_id','function_id','complete'}:raise StorageError('storage_protocol')
                try:identifier(row['consumer_id']);identifier(row['function_id'])
                except (ValueError,TypeError,AttributeError):raise StorageError('storage_protocol') from None
                if row['consumer_id']<=previous or type(row['complete']) is not bool:raise StorageError('storage_protocol')
                previous=row['consumer_id'];result.append(row)
            if following is None:return result
            if len(rows)!=50 or following!=previous:raise StorageError('storage_protocol')
            after=following
        raise StorageError('storage_protocol')

    async def acquire(self,function,consumer,installation,configuration):
        configuration=volumes(configuration)
        result=await self.call('acquire',function_id=identifier(function),consumer_id=identifier(consumer),
                               installation_id=identifier(installation),configuration=configuration)
        enabled={kind for kind,item in configuration.items() if item['enabled']}
        try:
            if set(result)!={'consumer_id','paths','generations'} or result['consumer_id']!=consumer:raise ValueError()
            if set(result['paths'])!={'/'+kind for kind in enabled} or set(result['generations'])!=enabled:raise ValueError()
            for kind in enabled:
                identifier(result['generations'][kind])
                if result['paths']['/'+kind]!=str(self.root/'mounts'/function/kind):raise ValueError()
        except (ValueError,KeyError,TypeError,AttributeError):raise StorageError('storage_protocol',uncertain=True) from None
        return result

    async def release_confirmed(self,function,consumer,installation):
        released=await self.call('release',consumer_id=identifier(consumer),installation_id=identifier(installation))
        if released.get('released') is not True or type(released.get('already_released')) is not bool:
            raise StorageError('storage_protocol',uncertain=True)
        if any(row['consumer_id']==consumer for row in await self.leases(installation)):
            raise StorageError('storage_cleanup_pending')
        try:snapshot=await self.call('status',function_id=function)
        except StorageError as error:
            if str(error)=='function_unknown':return
            raise
        if (snapshot.get('id')!=function or type(snapshot.get('pending')) is not bool or
                type(snapshot.get('leases')) is not int or snapshot['leases']<0 or
                not isinstance(snapshot.get('volumes'),dict) or set(snapshot['volumes'])-{'data','cache'} or
                any(not isinstance(row,dict) or row.get('phase') not in ('unmounted','starting','mounted','stopping','failed')
                    for row in snapshot['volumes'].values())):
            raise StorageError('storage_protocol')
        if snapshot['pending'] or (snapshot['leases']==0 and any(row['phase']!='unmounted' for row in snapshot['volumes'].values())):
            raise StorageError('storage_cleanup_pending')


async def main():
    # Operator access to Docker is required to run this CLI in the control image.
    client=StorageClient('/storage-agent/agent.sock',os.environ['SERVERLESS_STORAGE_ROOT_HOST'])
    line=sys.stdin.buffer.readline(16385)
    if len(line)>16384 or not line.endswith(b'\n'):raise ValueError('invalid_frame')
    request=json.loads(line,object_pairs_hook=unique);operation=request.pop('op')
    try:print(json.dumps({'ok':True,'result':await client.call(operation,**request)}),flush=True)
    except StorageError as error:
        print(json.dumps({'ok':False,'error':str(error),'uncertain':error.uncertain}),flush=True);return 1
    return 0


if __name__=='__main__':
    try:raise SystemExit(asyncio.run(main()))
    except (ValueError,KeyError,TypeError):raise SystemExit('storage_client_input')
