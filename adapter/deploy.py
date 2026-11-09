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
from uuid import UUID,uuid4

# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
from function_code_hash import code_hash,PackageIdentityError

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


# @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#configuration-de-service-et-surcharges
def configure_service(client,service,target,configuration,report):
    result=report['service_configuration']
    if not configuration:return
    version=target.get('updated_at')
    if isinstance(version,bool) or not isinstance(version,(float,int)) or not math.isfinite(version) or version<=0:
        raise DeploymentError('invalid_service_response')
    body={**configuration}
    if 'secrets' in body:body['replace_secrets']=True
    result['state']='pending'
    try:
        row=client.request('PUT','/api/services/'+service+'/configuration',body=body,version=version)
        updated=row.get('updated_at')
        if (row.get('id')!=service or row.get('name')!=target['name'] or isinstance(updated,bool) or
                not isinstance(updated,(float,int)) or not math.isfinite(updated) or updated<=0):
            raise DeploymentError('invalid_service_response',uncertain=True)
    except DeploymentError as error:
        result['state']='unknown' if error.uncertain else 'failed';result['error']=error.public();raise
    result['state']='applied';result['updated_at']=updated


# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#api-et-calcul-commun
def invocation_urls(client,function_id,service_id,revision_id,code_hash):
    """Optional post-publication metadata, with a stable source across pages."""
    items=[];fingerprint=None;total=None
    for offset in range(0,513,5):
        page=client.request('GET',f'/api/functions/{function_id}/invocation-urls?version={code_hash}&limit=5&offset={offset}')
        if (page.get('function_id')!=function_id or page.get('service_id')!=service_id or
                page.get('revision_id')!=revision_id or page.get('function_state')!='published' or
                page.get('selection')!='version' or page.get('code_hash')!=code_hash):
            raise DeploymentError('invocation_catalogue_changed')
        source=page.get('source')
        if not isinstance(source,dict):raise DeploymentError('invalid_invocation_catalogue')
        if source.get('state')!='available':raise DeploymentError('invocation_domains_unavailable')
        sha=source.get('sha256');count=page.get('total');rows=page.get('items')
        if (not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha) or
                type(count) is not int or not 0<=count<=512 or
                page.get('offset')!=offset or page.get('limit')!=5 or not isinstance(rows,list) or
                len(rows)!=min(5,max(0,count-offset))):
            raise DeploymentError('invalid_invocation_catalogue')
        if fingerprint is None:fingerprint=sha;total=count
        elif (sha,count)!=(fingerprint,total):raise DeploymentError('invocation_catalogue_changed')
        for item in rows:
            if not isinstance(item,dict):raise DeploymentError('invalid_invocation_catalogue')
            domain=item.get('domain');transport=item.get('transport');entries=item.get('urls')
            if (not isinstance(domain,str) or len(domain)>253 or
                    not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',domain) or
                    transport not in ('http','https') or item.get('origin')!=transport+'://'+domain or
                    not isinstance(entries,list) or not 1<=len(entries)<=16 or
                    any(previous['domain']==domain for previous in items)):
                raise DeploymentError('invalid_invocation_catalogue')
            for entry in entries:
                if not isinstance(entry,dict):raise DeploymentError('invalid_invocation_catalogue')
                address=entry.get('url');methods=entry.get('methods');prefix=item['origin']+'/invoke/'+function_id+'@'+code_hash
                if (not isinstance(address,str) or not (address==prefix or
                        (address.startswith(prefix+'/') and re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',address[len(prefix)+1:]))) or
                        not isinstance(methods,list) or not methods or len(methods)>7 or
                        any(method not in ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS') for method in methods) or
                        len(set(methods))!=len(methods)):
                    raise DeploymentError('invalid_invocation_catalogue')
            items.append(item)
        if offset+len(rows)>=total:
            return {'state':'available','revision_id':revision_id,'code_hash':code_hash,'selection':'version',
                    'source_sha256':fingerprint,'items':items,'total':total}
    raise DeploymentError('invocation_catalogue_limit')


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
def publication_identity(published,function,artifact):
    validation=published.get('validation')
    if not isinstance(validation,dict):raise DeploymentError('invalid_publication_response',uncertain=True)
    try:
        expected=code_hash(artifact['inventory'],{'handler':function['config']['handler'],'runtime':function['config']['runtime'],
            'architecture':'linux-x64','image_id':validation.get('image_id'),'events':function['events']})['code_hash']
    except PackageIdentityError:raise DeploymentError('invalid_publication_descriptor',uncertain=True) from None
    if published.get('code_hash')!=expected:raise DeploymentError('publication_hash_mismatch',uncertain=True)
    if type(published.get('code_changed')) is not bool or type(published.get('version_restored')) is not bool:
        raise DeploymentError('invalid_publication_response',uncertain=True)
    if 'default_code_hash_at_publication' not in published:
        raise DeploymentError('invalid_publication_response',uncertain=True)
    target=published['default_code_hash_at_publication']
    if target is not None and (not isinstance(target,str) or not re.fullmatch('[0-9a-f]{64}',target)):
        raise DeploymentError('invalid_publication_response',uncertain=True)
    return expected


def deploy(plan,manifest,service,*,code_only=False):
    report={'service':plan['service'],'completed':False,'results':[],'warnings':plan['warnings'],
            'service_configuration':{'state':'preserved'},'mode':'code_only' if code_only else 'complete'}
    try:
        identifier(service);report['service_id']=service;client=Client()
        for function in plan['functions']:
            if code_only:
                json_payload({'handler':function['config']['handler'],'events':function['events']})
                continue
            json_payload({name:function[name] for name in ('config','configuration','events')})
            common=plan.get('service_configuration',{})
            effective={category:common.get(category,{})|function['configuration'][category] for category in ('environment','secrets')}
            json_payload({'config':function['config'],'configuration':effective,'events':function['events']})
            # The runtime bootstrap uses escaped JSON, which can exceed UTF-8 transport bytes.
            if len(json.dumps({'handler':'x'*256,'environment':effective['environment']|effective['secrets']}).encode())>256*1024:
                raise DeploymentError('configuration_body_too_large')
        if not code_only:json_payload(plan.get('service_configuration',{}))
        descriptor=package(plan,manifest.parent,manifest.parent/'.serverless-p2',manifest)
        target=client.request('GET','/api/services/'+service)
        if target.get('id')!=service or target.get('name')!=plan['service']:raise DeploymentError('service_mismatch')
        existing=list_functions(client,service)
        if not code_only:configure_service(client,service,target,plan.get('service_configuration',{}),report)
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
                if code_only:raise DeploymentError('code_only_function_not_found')
                mutation=True
                current=function_row(client.request('POST','/api/services/'+service+'/functions',
                    body={'name':function['name'],'config':function['config']},expected=201),service,function['name'])
                row['created']=True;key=current['id'];existing[function['name']]=key
                mutation=False
            row['function_id']=key
            mutation=True
            if code_only:
                row['deployment_id']=str(uuid4())
                candidate=client.request('POST','/api/functions/'+key+'/code-deployments',
                    body={'deployment_id':row['deployment_id'],'handler':function['config']['handler'],'events':function['events']},
                    version=current['updated_at'],expected=201)
                if candidate.get('id')!=row['deployment_id']:raise DeploymentError('invalid_candidate_response',uncertain=True)
            else:
                candidate=client.request('POST','/api/functions/'+key+'/deployments',
                    body={name:function[name] for name in ('config','configuration','events')},version=current['updated_at'],expected=201)
            candidate_id=identifier(candidate.get('id'));row['deployment_id']=candidate_id
            if candidate.get('function_id')!=key or candidate.get('state')!='prepared':raise DeploymentError('invalid_candidate_response')
            published=client.request('PUT','/api/deployments/'+candidate_id+'/artifact',archive=content)
            if published.get('id')!=candidate_id or published.get('function_id')!=key or published.get('state')!='published':
                raise DeploymentError('invalid_publication_response')
            row['revision_id']=identifier(published.get('revision_id'))
            row['code_hash']=publication_identity(published,function,descriptor['artifacts'][function['name']])
            row['code_changed']=published['code_changed'];row['version_restored']=published['version_restored']
            row['default_code_hash_at_publication']=published['default_code_hash_at_publication']
            row['function_version_at_publication']=published.get('result_function_version')
            row['state']='published'
        except DeploymentError as error:
            # A malformed successful mutation response can follow a committed write.
            row['state']='unknown' if error.uncertain or (mutation and error.status is None and error.code.startswith('invalid_')) else 'failed'
            row['error']=error.public()
        except OSError:
            row['error']={'code':'artifact_unavailable'}
        # @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#api-et-calcul-commun
        # No optional GET failure can reclassify an already committed publication.
        if row['state']=='published':
            try:row['invocation_urls']=invocation_urls(client,key,service,row['revision_id'],row['code_hash'])
            except DeploymentError as error:
                row['invocation_urls']={'state':'unavailable','error':error.public()}
    report['completed']=all(row['state']=='published' for row in report['results'])
    return report


# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#promotion-et-droits | docs/FUNCTION_VERSION_EXECUTION.md#catalogue-cli-console-et-manuel
def promote(function_id,selected_hash):
    report={'function_id':function_id,'code_hash':selected_hash,'completed':False,'state':'failed'}
    mutation=False
    try:
        identifier(function_id)
        if not isinstance(selected_hash,str) or not re.fullmatch('[0-9a-f]{64}',selected_hash):
            raise DeploymentError('invalid_code_hash')
        client=Client()
        current=client.request('GET','/api/functions/'+function_id)
        service=identifier(current.get('service_id'));function_row(current,service)
        if current['id']!=function_id:raise DeploymentError('invalid_function_response')
        mutation=True
        result=client.request('POST',f'/api/functions/{function_id}/versions/{selected_hash}/promote',version=current['updated_at'])
        if (result.get('function_id')!=function_id or result.get('code_hash')!=selected_hash or
                result.get('default_code_hash')!=selected_hash or type(result.get('changed')) is not bool):
            raise DeploymentError('invalid_promotion_response',uncertain=True)
        report.update(state='promoted',completed=True,revision_id=identifier(result.get('revision_id')),
                      function_version=result.get('function_version'),changed=result['changed'])
    except DeploymentError as error:
        report['state']='unknown' if error.uncertain or (mutation and error.status is None and error.code.startswith('invalid_')) else 'failed'
        report['error']=error.public()
    return report
