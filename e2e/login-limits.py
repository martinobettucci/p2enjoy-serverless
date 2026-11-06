# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/SCHEMA.md#identités
# @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion | docs/SCHEMA.md#identités
# Run on the authorized DEV Spark: real ingress, real control and durable limits.
import http.cookiejar
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
BASE='https://serverless.lelabs.tech'
Path('/srv/p2enjoy-serverless/control/.proof-login-limits.json').write_text('{"completed":false,"error":"Campagne non terminée"}\n')
checks=[];completed=False
pending=[]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class Client:
    def __init__(self):
        self.jar=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPCookieProcessor(self.jar))

    def call(self,path,headers=None,base=BASE):
        try:r=self.opener.open(urllib.request.Request(base+path,headers={'Accept':'application/json',**(headers or {})}),timeout=15)
        except urllib.error.HTTPError as error:r=error
        with r:return r.status,r.headers,r.read()


def opened(client):
    response=client.call('/auth/login')
    assert response[0]==303,f'Ouverture refusée à {response[0]}'
    state=urllib.parse.parse_qs(urllib.parse.urlsplit(response[1]['Location']).query)['state'][0]
    pending.append((client,state));return state


def cancel(client,state):
    assert client.call('/auth/retour?state='+state+'&error=access_denied')[0]==401
    pending.remove((client,state))


def passed(name):
    checks.append({'name':name,'status':'passed'});print('PASS',name,flush=True)


started=time.time()
try:
    for _ in range(8):opened(Client())
    response=Client().call('/auth/login')
    assert response[0]==429 and response[1]['Retry-After']=='60'
    passed('Huit flows actifs par client, neuvième refusé')
    assert Client().call('/auth/login',{'X-Forwarded-For':'192.0.2.80','X-Real-IP':'192.0.2.81','Forwarded':'for=192.0.2.82'})[0]==429
    passed('Les en-têtes falsifiés ne contournent pas le quota')
    direct=Client();response=direct.call('/auth/login',base='http://127.0.0.1:18090')
    assert response[0]==303
    state=urllib.parse.parse_qs(urllib.parse.urlsplit(response[1]['Location']).query)['state'][0]
    # This non-browser client explicitly returns its own cookie for cleanup.
    assert direct.call('/auth/retour?state='+state+'&error=access_denied',{'Cookie':'__Host-p2-flow='+state},base='http://127.0.0.1:18090')[0]==401
    passed('Une autre adresse réelle reste autorisée pendant la saturation')
    for client,state in list(pending):cancel(client,state)
    repeated=Client()
    for _ in range(22):
        state=opened(repeated);cancel(repeated,state)
    assert repeated.call('/auth/login')[0]==429
    passed('Trente ouvertures par fenêtre, même après consommation des flows')
    subprocess.run(['docker','restart','serverless-api'],check=True,capture_output=True,timeout=45)
    for _ in range(60):
        try:
            if repeated.call('/healthz')[0]==200:break
        except (OSError,urllib.error.URLError):pass
        time.sleep(.25)
    else:raise RuntimeError('Le contrôle ne reprend pas')
    assert time.time()-started<55,'La preuve de persistance doit précéder l’expiration de la fenêtre'
    assert repeated.call('/auth/login')[0]==429
    passed('Le redémarrage Docker ne remet pas le compteur à zéro')
    print('WAIT expiration réelle de la fenêtre',flush=True)
    while time.time()<started+62:time.sleep(.5)
    state=opened(repeated);cancel(repeated,state)
    passed('La fenêtre expirée permet une nouvelle ouverture réelle')
    completed=True
except BaseException as error:
    checks.append({'name':'Campagne interrompue','status':'failed','error':type(error).__name__})
    raise
finally:
    cleanup_errors=0
    for client,state in list(pending):
        try:cancel(client,state)
        except Exception:cleanup_errors+=1
    Path('/srv/p2enjoy-serverless/control/.proof-login-limits.json').write_text(json.dumps({'completed':completed and cleanup_errors==0,'checks':checks,'cleanup_errors':cleanup_errors,'skipped':0},indent=2)+'\n')
    assert cleanup_errors==0,'Nettoyage des flows créés par la preuve requis'
