# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#commande-deploy
"""Sequential HTTPS publication; credentials and resolved values stay in memory."""
import hashlib
import http.client
import json
import math
import os
import re
import ssl
import stat
from urllib.parse import urlsplit
from uuid import UUID

from .archive import MAX_ZIP,open_source,package

MAX_RESPONSE=8*1024*1024
PAGE_SIZE=10


class DeploymentError(Exception):
    def __init__(self,code,*,status=None,retry_after=None,uncertain=False):
        super().__init__(code)
        self.code,self.status,self.retry_after,self.uncertain=code,status,retry_after,uncertain

    def public(self):
        result={'code':self.code}
        if self.status is not None:result['status']=self.status
        if self.retry_after is not None:result['retry_after_seconds']=self.retry_after
        return result


def identifier(value):
    try:
        if not isinstance(value,str) or str(UUID(value))!=value:raise ValueError
    except (ValueError,TypeError,AttributeError):raise DeploymentError('invalid_identifier') from None
    return value


def json_payload(body):
    payload=json.dumps(body,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    if len(payload)>256*1024:raise DeploymentError('configuration_body_too_large')
    return payload


class Client:
    def __init__(self):
        endpoint=os.environ.get('P2_SERVERLESS_URL','')
        self.token=os.environ.get('P2_SERVERLESS_TOKEN','')
        try:
            parsed=urlsplit(endpoint)
            if (parsed.scheme!='https' or not parsed.hostname or parsed.username is not None or parsed.password is not None or
                parsed.path not in ('','/') or parsed.query or parsed.fragment or '?' in endpoint or '#' in endpoint or
                any(ord(c)<33 or ord(c)>126 for c in endpoint)):
                raise ValueError
            self.host,self.port=parsed.hostname,443 if parsed.port is None else parsed.port
            if not 1<=self.port<=65535:raise ValueError
        except ValueError:raise DeploymentError('invalid_https_origin') from None
        if not self.token or len(self.token)>4096 or any(ord(c)<33 or ord(c)>126 for c in self.token):
            raise DeploymentError('missing_or_invalid_service_token')
        self.context=ssl.create_default_context()

    def request(self,method,path,*,body=None,archive=None,version=None,expected=200):
        headers={'X-Serverless-Token':self.token,'Accept':'application/json','User-Agent':'p2enjoy-adapter/1'}
        payload=None
        if body is not None:
            payload=json_payload(body)
            headers['Content-Type']='application/json'
        if archive is not None:payload=archive;headers['Content-Type']='application/zip'
        if version is not None:headers['If-Match']=str(version)
        connection=http.client.HTTPSConnection(self.host,self.port,timeout=480 if archive is not None else 30,context=self.context)
        try:
            connection.request(method,path,body=payload,headers=headers)
            response=connection.getresponse()
            if response.status!=expected:
                retry=response.getheader('Retry-After','')
                retry=int(retry) if re.fullmatch(r'[0-9]{1,5}',retry) else None
                # No redirect or mutation retry, and no remote body enters an error.
                raise DeploymentError('http_'+str(response.status),status=response.status,retry_after=retry,
                                      uncertain=method!='GET' and not 400<=response.status<500)
            raw=response.read(MAX_RESPONSE+1)
            if len(raw)>MAX_RESPONSE:raise DeploymentError('response_too_large',uncertain=method!='GET')
            try:result=json.loads(raw)
            except (ValueError,UnicodeError,RecursionError):raise DeploymentError('invalid_response',uncertain=method!='GET') from None
            if not isinstance(result,dict):raise DeploymentError('invalid_response',uncertain=method!='GET')
            return result
        except ssl.SSLCertVerificationError:raise DeploymentError('tls_verification_failed') from None
        except (OSError,http.client.HTTPException):raise DeploymentError('network_error',uncertain=method!='GET') from None
        finally:connection.close()


def function_row(row,service,name=None):
    if not isinstance(row,dict):raise DeploymentError('invalid_function_response')
    identifier(row.get('id'))
    version=row.get('updated_at')
    if (row.get('service_id')!=service or not isinstance(row.get('name'),str) or
        not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,62}',row['name']) or
        isinstance(version,bool) or not isinstance(version,(int,float)) or not math.isfinite(version) or version<=0 or
        (name is not None and row['name']!=name)):
        raise DeploymentError('invalid_function_response')
    return row


def list_functions(client,service):
    result={};seen=set()
    for offset in range(0,10001,PAGE_SIZE):
        page=client.request('GET',f'/api/services/{service}/functions?limit={PAGE_SIZE}&offset={offset}').get('items')
        if not isinstance(page,list) or len(page)>PAGE_SIZE:raise DeploymentError('invalid_function_list')
        for item in page:
            row=function_row(item,service)
            if row['id'] in seen or row['name'] in result:raise DeploymentError('function_list_changed')
            seen.add(row['id']);result[row['name']]=row['id']
        if len(page)<PAGE_SIZE:return result
    raise DeploymentError('function_list_limit')


def archive_bytes(root,function,artifact):
    filename=function['name']+'-'+artifact['sha256']+'.zip'
    if artifact['file']!=filename:raise DeploymentError('invalid_artifact_descriptor')
    fd=open_source(root,'.serverless-p2/'+filename)
    with os.fdopen(fd,'rb') as stream:
        row=os.fstat(stream.fileno())
        if not stat.S_ISREG(row.st_mode) or row.st_size!=artifact['size'] or not 0<row.st_size<=MAX_ZIP:
            raise DeploymentError('artifact_changed')
        content=stream.read(MAX_ZIP+1)
    if len(content)!=artifact['size'] or hashlib.sha256(content).hexdigest()!=artifact['sha256']:
        raise DeploymentError('artifact_changed')
    return content


def deploy(plan,manifest,service):
    report={'service':plan['service'],'completed':False,'results':[],'warnings':plan['warnings']}
    try:
        identifier(service);report['service_id']=service;client=Client()
        for function in plan['functions']:
            json_payload({name:function[name] for name in ('config','configuration','events')})
        descriptor=package(plan,manifest.parent,manifest.parent/'.serverless-p2',manifest)
        target=client.request('GET','/api/services/'+service)
        if target.get('id')!=service or target.get('name')!=plan['service']:raise DeploymentError('service_mismatch')
        existing=list_functions(client,service)
    except DeploymentError as error:
        report['error']=error.public();return report
    for function in plan['functions']:
        row={'name':function['name'],'state':'failed'};report['results'].append(row)
        mutation=False
        try:
            content=archive_bytes(manifest.parent,function,descriptor['artifacts'][function['name']])
            key=existing.get(function['name'])
            if key:
                current=function_row(client.request('GET','/api/functions/'+key),service,function['name'])
                if current['id']!=key:raise DeploymentError('invalid_function_response')
            else:
                mutation=True
                current=function_row(client.request('POST','/api/services/'+service+'/functions',
                    body={'name':function['name'],'config':function['config']},expected=201),service,function['name'])
                row['created']=True;key=current['id'];existing[function['name']]=key
                mutation=False
            row['function_id']=key
            mutation=True
            candidate=client.request('POST','/api/functions/'+key+'/deployments',
                body={name:function[name] for name in ('config','configuration','events')},version=current['updated_at'],expected=201)
            candidate_id=identifier(candidate.get('id'));row['deployment_id']=candidate_id
            if candidate.get('function_id')!=key or candidate.get('state')!='prepared':raise DeploymentError('invalid_candidate_response')
            published=client.request('PUT','/api/deployments/'+candidate_id+'/artifact',archive=content)
            if published.get('id')!=candidate_id or published.get('function_id')!=key or published.get('state')!='published':
                raise DeploymentError('invalid_publication_response')
            row['revision_id']=identifier(published.get('revision_id'));row['state']='published'
        except DeploymentError as error:
            # A malformed successful mutation response can follow a committed write.
            row['state']='unknown' if error.uncertain or (mutation and error.status is None and error.code.startswith('invalid_')) else 'failed'
            row['error']=error.public()
        except OSError:
            row['error']={'code':'artifact_unavailable'}
    report['completed']=all(row['state']=='published' for row in report['results'])
    return report
