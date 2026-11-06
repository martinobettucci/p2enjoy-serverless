# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#entrée-http
"""HTTP policy and Lambda envelopes shared by initial checks and admission."""
import base64
import ipaddress
import json
from urllib.parse import parse_qsl,urlsplit

from fastapi import HTTPException

from .auth import SESSION_COOKIE,FLOW_COOKIE
from .instances import HEADER_NAME,WITHHELD


class InvocationError(HTTPException):
    def __init__(self,status,code):super().__init__(status,code)


def canonical_origin(value):
    if not isinstance(value,str) or not value or any(ord(c)<=32 or ord(c)>=127 for c in value) or '\\' in value:
        raise ValueError('Origine HTTP(S) invalide.')
    url=urlsplit(value)
    if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.path or url.query or url.fragment or '*' in value:
        raise ValueError('Une origine contient uniquement protocole, hôte et port.')
    port=url.port
    if port==0 or url.netloc.endswith(':'):raise ValueError('Port d’origine invalide.')
    host=url.hostname.lower()
    if ':' in host:host='['+str(ipaddress.IPv6Address(host))+']'
    default=443 if url.scheme=='https' else 80
    return f'{url.scheme}://{host}'+(f':{port}' if port is not None and port!=default else '')


def canonical_network(value):
    if '%' in value:raise ValueError('Adresse avec zone interdite.')
    network=ipaddress.ip_network(value,strict=False)
    if isinstance(network,ipaddress.IPv6Network) and network.prefixlen>=96 and network.network_address.ipv4_mapped:
        return str(ipaddress.IPv4Network((network.network_address.ipv4_mapped,network.prefixlen-96),strict=False))
    return str(network)


def policy_allows(policy,origin,source_ip):
    tests=[]
    if policy['origins']:tests.append(origin is not None and origin in policy['origins'])
    if policy['ips']:tests.append(any(ipaddress.ip_address(source_ip) in ipaddress.ip_network(cidr) for cidr in policy['ips']))
    return not tests or (all(tests) if policy['combination']=='and' else any(tests))


def declared_path(revision,path,method):
    if not revision:raise InvocationError(409,'function_not_deployed')
    events=json.loads(revision['events_json'])['http']
    matches=[event for event in events if (event['implicit'] if path is None else event['path']==path)]
    if not matches:raise InvocationError(404,'route_not_found')
    for event in matches:
        if method in event['methods']:return '/'+event['path']
    raise InvocationError(405,'method_not_allowed')


def preflight_headers(values):
    if len(values)>1:raise InvocationError(400,'invalid_preflight')
    value=values[0] if values else ''
    if len(value.encode())>4096:raise InvocationError(400,'invalid_preflight')
    names=[name.strip().lower() for name in value.split(',')] if value else []
    if len(names)>64 or len(names)!=len(set(names)):raise InvocationError(400,'invalid_preflight')
    forbidden=WITHHELD|{'cookie','x-csrf-token','x-request-id'}
    if any(not HEADER_NAME.fullmatch(name) or name in forbidden or name.startswith(('proxy-','sec-')) for name in names):
        raise InvocationError(400,'invalid_preflight')
    return names


def event_envelope(method,path,raw_headers,query,body,source_ip,identifier):
    headers={};connection=set()
    for raw_name,raw_value in raw_headers:
        if raw_name.lower()==b'connection':connection.update(x.strip().lower() for x in raw_value.decode('latin1').split(','))
    withheld=WITHHELD|connection|{'x-serverless-token','x-csrf-token','x-request-id'}
    for raw_name,raw_value in raw_headers:
        name=raw_name.decode('latin1').lower();value=raw_value.decode('latin1')
        if name in withheld:continue
        if name=='cookie':
            value='; '.join(part.strip() for part in value.split(';') if part.strip().split('=',1)[0] not in (SESSION_COOKIE,FLOW_COOKIE))
            if not value:continue
        headers.setdefault(name,[]).append(value)
    parameters={}
    for name,value in parse_qsl(query.decode('latin1'),keep_blank_values=True):parameters.setdefault(name,[]).append(value)
    content_type=headers.get('content-type',[''])[-1].split(';',1)[0].lower()
    textual=(content_type.startswith('text/') or content_type in ('application/json','application/xml','application/x-www-form-urlencoded') or content_type.endswith(('+json','+xml')))
    encoded=bool(body) and not textual
    if not encoded:
        try:value=body.decode('utf8')
        except UnicodeError:encoded=True
    if encoded:value=base64.b64encode(body).decode()
    return {'httpMethod':method,'path':path,'headers':{k:v[-1] for k,v in headers.items()} or None,
            'multiValueHeaders':headers or None,'queryStringParameters':{k:v[-1] for k,v in parameters.items()} or None,
            'multiValueQueryStringParameters':parameters or None,'body':value,'isBase64Encoded':encoded,
            'requestContext':{'identity':{'sourceIp':source_ip},'requestId':identifier}}
