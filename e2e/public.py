# @spec docs/CONTROL.md#connexion | docs/BACKLOG.md#sls-020
# @verifies docs/CONTROL.md#connexion | docs/BACKLOG.md#sls-020
# A sequential HTTPS client of the deployed control and its real OIDC provider.
import http.cookiejar
import http.client
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE='https://serverless.lelabs.tech'
ISSUER='https://oauth.lelabs.tech/realms/lelabs'
discovered=None
results=[]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class Client:
    def __init__(self):
        self.cookies=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPCookieProcessor(self.cookies))

    def call(self,path,method='GET',data=None,headers=None):
        headers={'Accept':'application/json',**(headers or {})}
        if data is not None:
            data=json.dumps(data).encode();headers['Content-Type']='application/json'
        req=urllib.request.Request(BASE+path,data=data,method=method,headers=headers)
        try:response=self.opener.open(req,timeout=20)
        except urllib.error.HTTPError as error:response=error
        with response:return response.status,response.headers,response.read()


def check(name,fn):
    started=time.monotonic()
    try:fn()
    except BaseException as error:
        results.append({'name':name,'status':'failed','error':type(error).__name__})
        raise
    else:
        results.append({'name':name,'status':'passed','duration_seconds':round(time.monotonic()-started,3)})
        print('PASS',name,flush=True)


def status(response,wanted):
    assert response[0]==wanted, f'HTTP {response[0]} au lieu de {wanted}'
    return response


def login(client):
    code,headers,body=status(client.call('/auth/login'),303)
    target=urllib.parse.urlsplit(headers['Location'])
    assert target.scheme=='https' and target.hostname=='oauth.lelabs.tech'
    assert discovered,'Découverte OIDC requise avant le parcours de connexion'
    assert urllib.parse.urlunsplit(target._replace(query='',fragment=''))==discovered['authorization_endpoint']
    query=urllib.parse.parse_qs(target.query)
    assert query['client_id']==['p2enjoy-serverless-dev']
    assert query['redirect_uri']==[BASE+'/auth/retour']
    assert query['response_type']==['code']
    assert query['code_challenge_method']==['S256']
    assert set(query['scope'][0].split())=={'openid','profile','email'}
    for field in ('state','nonce','code_challenge'):assert re.fullmatch(r'[A-Za-z0-9_-]{43}',query[field][0])
    cookie=headers['Set-Cookie']
    assert all(value in cookie for value in ('__Host-p2-flow=','HttpOnly','Secure','SameSite=lax','Path=/'))
    return query['state'][0]


def health():
    response=status(Client().call('/healthz'),200)
    assert json.loads(response[2])['status']=='ok'
    assert response[1]['Cache-Control']=='no-store'
    assert response[1]['X-Content-Type-Options']=='nosniff'
    assert response[1]['Referrer-Policy']=='no-referrer'
    assert "frame-ancestors 'none'" in response[1]['Content-Security-Policy']
    uuid.UUID(response[1]['X-Request-ID'])


def discovery():
    global discovered
    with urllib.request.urlopen(ISSUER+'/.well-known/openid-configuration',timeout=20) as response:
        assert response.status==200
        discovered=json.load(response)
    assert discovered['issuer']==ISSUER
    for key in ('authorization_endpoint','token_endpoint','end_session_endpoint','jwks_uri'):
        parsed=urllib.parse.urlsplit(discovered[key])
        assert parsed.scheme=='https' and parsed.netloc=='oauth.lelabs.tech' and not parsed.username
    assert 'code' in discovered['response_types_supported']
    assert 'S256' in discovered['code_challenge_methods_supported']
    assert {'openid','profile','email'}<=set(discovered['scopes_supported'])
    assert {'client_secret_post','client_secret_basic'}<=set(discovered['token_endpoint_auth_methods_supported'])
    with urllib.request.urlopen(discovered['jwks_uri'],timeout=20) as response:
        assert response.status==200
        keys=json.load(response)['keys']
    assert any(key.get('use')=='sig' and key.get('alg') in ('RS256','ES256') and
               key.get('kty') in ('RSA','EC') and key.get('kid') for key in keys)


def assets():
    client=Client()
    html=status(client.call('/'),200)[2].decode()
    assert '<html lang="fr">' in html
    paths=re.findall(r'(?:src|href)="(/assets/[^\"]+)"',html)
    assert len(paths)>=2
    for path in paths:assert len(status(client.call(path),200)[2])>100
    assert '<svg' in status(client.call('/favicon.svg'),200)[2].decode()
    status(client.call('/console/namespaces/'+str(uuid.uuid4())),200)


def anonymous():
    client=Client()
    assert json.loads(status(client.call('/api/session'),200)[2])=={'authenticated':False}
    status(client.call('/api/namespaces'),401)
    status(client.call('/api/namespaces','POST',{'name':'not-created'}),401)
    status(client.call('/api/services/'+str(uuid.uuid4()),headers={'X-Serverless-Token':'invalid-real-request'}),401)
    status(client.call('/auth/logout','POST'),403)
    assert json.loads(status(client.call('/auth/logout','POST',headers={'Origin':BASE}),200)[2])['signed_out']


def bad_callbacks():
    client=Client()
    for state in ('','%C3%A9','x','x'*44):
        status(client.call('/auth/retour?state='+state,headers={'Cookie':'__Host-p2-flow=x'}),401)
    response=status(client.call('/auth/retour?state=%C3%A9',headers={'Accept':'text/html'}),303)
    parsed=urllib.parse.urlsplit(response[1]['Location'])
    assert parsed.netloc=='serverless.lelabs.tech' and parsed.path=='/'
    assert 'auth-error=' in parsed.fragment and not parsed.query


def real_flows():
    client=Client()
    first=login(client)
    second=login(client)
    assert first!=second
    # The old flow cannot complete in this browser; the current flow remains.
    status(client.call('/auth/retour?state='+first+'&error=access_denied'),401)
    # A failed callback clears the browser flow cookie, so begin a fresh attempt.
    third=login(client)
    status(client.call('/auth/retour?state='+third+'&error=access_denied'),401)
    status(client.call('/auth/retour?state='+third+'&error=access_denied'),401)
    current=login(client)
    # The real provider receives this invalid code with this client's real PKCE.
    status(client.call('/auth/retour?state='+current+'&code=qualification-invalid-code'),401)
    assert json.loads(client.call('/api/session')[2])=={'authenticated':False}


def bounded_bodies():
    status(Client().call('/api/namespaces','POST',{'name':'x','description':'x'*(257*1024)}),413)
    response=status(Client().call('/api/namespaces','POST',{'name':'bad name','unknown_secret':'must-not-be-returned'}),422)
    assert b'must-not-be-returned' not in response[2]
    connection=http.client.HTTPSConnection(urllib.parse.urlsplit(BASE).hostname,timeout=20)
    try:
        connection.request('POST','/api/namespaces',body=iter([b'{"name":"x","description":"',b'x'*(257*1024),b'"}']),
                           headers={'Content-Type':'application/json','Accept':'application/json'},encode_chunked=True)
        response=connection.getresponse()
        assert response.status==413,f'Corps chunked : HTTP {response.status} au lieu de 413'
        response.read()
    finally:connection.close()


# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
# @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#intégration-au-contrôle
def deployment_refusals():
    key=str(uuid.uuid4());client=Client()
    status(client.call('/api/functions/'+key+'/deployments','POST',{'config':{'handler':'handler.handler'}}),401)
    status(client.call('/api/deployments/'+key),401)
    status(client.call('/api/functions/'+key+'/revisions'),401)
    status(client.call('/api/functions/'+key+'/rollback','POST',{'revision_id':str(uuid.uuid4())}),401)
    status(client.call('/api/functions/'+key+'/revisions/'+str(uuid.uuid4()),'DELETE'),401)
    connection=http.client.HTTPSConnection(urllib.parse.urlsplit(BASE).hostname,timeout=5)
    try:
        # Declare a genuine large HTTP body, send none: auth must answer before requesting it.
        connection.putrequest('PUT','/api/deployments/'+key+'/artifact')
        connection.putheader('Content-Type','application/zip')
        connection.putheader('Content-Length',str(64*1024**2))
        connection.putheader('Expect','100-continue');connection.endheaders()
        response=connection.getresponse()
        assert response.status==401,f'Upload anonyme avant lecture : HTTP {response.status}'
        response.read()
    finally:connection.close()


if __name__=='__main__':
    output=Path('.local/e2e/public.json');output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
    completed=False
    try:
        for name,fn in [('Découverte OIDC et clés asymétriques réelles',discovery),
                        ('TLS, santé et en-têtes',health),('Document et ressources de la console',assets),
                        ('Refus anonymes',anonymous),('Callbacks malformés',bad_callbacks),
                        ('Flows réels et refus du fournisseur',real_flows),('Corps bornés et erreurs expurgées',bounded_bodies),
                        ('Routes de révision et upload anonyme refusé avant lecture',deployment_refusals)]:check(name,fn)
        completed=True
    finally:
        output.write_text(json.dumps({'target':BASE,'timestamp':time.time(),'completed':completed,'checks':results,'skipped':0},indent=2,ensure_ascii=False)+'\n')
