# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion
# @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#connexion
# Real separate loopback source addresses exercise the global login cap.
import http.client
import json
from pathlib import Path
import subprocess
import urllib.parse

assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
Path('/srv/p2enjoy-serverless/control/.proof-login-capacity.json').write_text('{"completed":false,"error":"Campagne non terminée"}\n')
pending=[];checks=[];completed=False


def call(source,path,cookie=None):
    connection=http.client.HTTPConnection('127.0.0.1',18090,timeout=15,source_address=(source,0))
    try:
        connection.request('GET',path,headers={'Accept':'application/json',**({'Cookie':'__Host-p2-flow='+cookie} if cookie else {})})
        response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
    finally:connection.close()


def cancel(source,state):
    assert call(source,'/auth/retour?state='+state+'&error=access_denied',state)[0]==401
    pending.remove((source,state))


try:
    refused=False
    for index in range(260):
        source='127.23.'+str(index//8//250)+'.'+str(index//8%250+1)
        status,headers,body=call(source,'/auth/login')
        if status==429:
            assert json.loads(body)['error']=='Trop de connexions en cours. Réessayez dans quelques instants.'
            refused=True;break
        assert status==303
        state=urllib.parse.parse_qs(urllib.parse.urlsplit(headers['location']).query)['state'][0]
        pending.append((source,state))
    assert refused and 1<=len(pending)<=256
    # Observation only: prove the aggregate includes existing genuine flows.
    code='import sqlite3; db=sqlite3.connect("file:/state/control.sqlite3?mode=ro",uri=True); print(db.execute("SELECT count(*) FROM login_flows").fetchone()[0])'
    result=subprocess.run(['docker','exec','p2enjoy-serverless-dev-control-1','python','-B','-c',code],check=True,capture_output=True,text=True,timeout=10)
    assert int(result.stdout)==256
    checks.append({'name':'256 flows réels : le suivant est refusé globalement','status':'passed'})
    cancel(*pending[0])
    source='127.24.0.1';status,headers,body=call(source,'/auth/login')
    assert status==303
    pending.append((source,urllib.parse.parse_qs(urllib.parse.urlsplit(headers['location']).query)['state'][0]))
    checks.append({'name':'La consommation libère réellement une place','status':'passed'})
    completed=True
except BaseException as error:
    checks.append({'name':'Campagne interrompue','status':'failed','error':type(error).__name__})
    raise
finally:
    failures=0
    for entry in list(pending):
        try:cancel(*entry)
        except Exception:failures+=1
    Path('/srv/p2enjoy-serverless/control/.proof-login-capacity.json').write_text(json.dumps({'completed':completed and failures==0,'checks':checks,'cleanup_errors':failures,'skipped':0},indent=2)+'\n')
    assert failures==0
for check in checks:print('PASS',check['name'])
