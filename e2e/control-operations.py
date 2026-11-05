# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves
# @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#configuration | docs/SCHEMA.md
# Real immutable control image, real SQLite and real OIDC discovery on DEV only.
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
ROOT=Path('/srv/p2enjoy-serverless/control')
(ROOT/'.proof-control-operations.json').write_text('{"completed":false,"error":"Campagne non terminée"}\n')
checks=[];completed=False
project='p2enjoy-control-proof-'+uuid.uuid4().hex[:10]
work=Path(tempfile.mkdtemp(prefix='operations-',dir=ROOT))
state=work/'state';state.mkdir(mode=0o700)
compose=work/'compose.json'
cmd=['python','-B','-m','uvicorn','app.main:app','--host','0.0.0.0','--port','18090',
     '--workers','1','--no-access-log','--no-proxy-headers']
secrets=[]


def run(args,timeout=60,check=True):
    result=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
    if check and result.returncode:
        # Never include docker inspect/config output or environment in errors.
        raise RuntimeError('Échec de commande '+args[0]+' (code '+str(result.returncode)+')')
    return result


image=run(['docker','inspect','--format','{{.Image}}','p2enjoy-serverless-dev-control-1']).stdout.strip()
base=['docker','compose','-p',project,'-f',str(compose)]


def start(alter=None,readonly=False):
    command=cmd
    if alter:
        command=['python','-B','-c','import os; '+alter+'; os.execvp("python",'+repr(cmd)+')']
    compose.write_text(json.dumps({'services':{'control':{
        'image':image,'env_file':['/etc/spark/env','/run/spark/secrets'],
        'volumes':[str(state)+':/state'+(':ro' if readonly else '')],
        'read_only':True,'tmpfs':['/tmp:size=16m,mode=1777,noexec,nosuid'],
        'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],
        'mem_limit':'512m','cpus':1,'pids_limit':64,'init':True,
        'command':command,'logging':{'driver':'json-file','options':{'max-size':'1m','max-file':'1'}}}}}))
    run(base+['up','-d','--force-recreate'])
    return run(base+['ps','-aq','control']).stdout.strip()


def status(container):
    return json.loads(run(['docker','inspect','--format','{{json .State}}',container]).stdout)


def logs(container):
    result=run(['docker','logs',container]);value=result.stdout+result.stderr
    for secret in secrets:assert secret not in value,'Valeur secrète présente dans les journaux'
    return value


def request(path,expected,method='GET',body=None):
    program='''import urllib.request,urllib.error,json
try:r=urllib.request.urlopen(urllib.request.Request('http://control:18090'+%r,method=%r,data=%r,headers={'Content-Type':'application/json'}),timeout=15)
except urllib.error.HTTPError as e:r=e
print(json.dumps({'status':r.status,'request_id':r.headers.get('X-Request-ID'),'body':r.read().decode()}))
'''%(path,method,json.dumps(body).encode() if body is not None else None)
    result=run(['docker','run','--rm','--network',project+'_default','--read-only',
                '--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','32',
                '--memory','128m',image,'python','-B','-c',program],timeout=30)
    response=json.loads(result.stdout)
    assert response['status']==expected,f'HTTP {response["status"]}, attendu {expected}'
    return response


def ready(container):
    for _ in range(80):
        if status(container)['Status']=='exited':raise RuntimeError('Contrôle de preuve arrêté au démarrage')
        result=run(['docker','exec',container,'python','-B','-c',
                    'import urllib.request; urllib.request.urlopen("http://127.0.0.1:18090/healthz",timeout=1).read()'],check=False)
        if result.returncode==0:return
        time.sleep(.25)
    raise RuntimeError('Contrôle de preuve indisponible')


def passed(name):
    checks.append({'name':name,'status':'passed'});print('PASS',name,flush=True)


def failure(name,alter,message,readonly=False):
    container=start(alter,readonly)
    for _ in range(80):
        current=status(container)
        if current['Status']=='exited':break
        time.sleep(.25)
    else:raise AssertionError('Le démarrage aurait dû être refusé : '+name)
    assert current['ExitCode']!=0
    output=logs(container)
    if message.lower() not in output.lower():
        diagnostics=[line.strip() for line in output.splitlines() if 'Error:' in line or 'Exception:' in line]
        raise AssertionError('Diagnostic attendu absent : '+name+' ; '+str(diagnostics[-1:]))
    passed(name)


try:
    container=start();ready(container)
    env=json.loads(run(['docker','inspect','--format','{{json .Config.Env}}',container]).stdout)
    secrets=[entry.split('=',1)[1] for entry in env if entry.split('=',1)[0] in ('OIDC_CLIENT_SECRET','SERVERLESS_MASTER_KEY')]
    assert len(secrets)==2 and all(secrets)
    assert json.loads(request('/healthz',200)['body'])['status']=='ok'
    request('/api/namespaces',401)
    config=json.loads(run(['docker','inspect','--format','{{json .HostConfig}}',container]).stdout)
    assert config['ReadonlyRootfs'] and config['CapDrop']==['ALL']
    assert config['Memory']==512*1024*1024 and config['PidsLimit']==64
    assert not config.get('Privileged') and not config.get('PortBindings')
    passed('Même image réelle, entrée HTTP et confinement Docker')
    for key in ('SERVERLESS_PUBLIC_URL','OIDC_ISSUER','OIDC_CLIENT_ID','OIDC_CLIENT_SECRET','SERVERLESS_MASTER_KEY'):
        failure('Configuration requise absente : '+key,'os.environ.pop('+repr(key)+',None)', 'Missing cell configuration: '+key)
    failure('URL publique HTTP refusée',"os.environ['SERVERLESS_PUBLIC_URL']='http://serverless-dev.lelabs.tech'",'absolute HTTPS')
    failure('Sous-chemin public refusé',"os.environ['SERVERLESS_PUBLIC_URL']+='/subpath'",'root path')
    failure('Issuer étranger refusé',"os.environ['OIDC_ISSUER']='https://example.org/realm'",'realm lelabs autorisé')
    failure('Clé maîtresse malformée refusée',"os.environ['SERVERLESS_MASTER_KEY']='invalid'",'Fernet key')
    failure('CIDR de proxy malformé refusé',"os.environ['SERVERLESS_TRUSTED_PROXIES']='invalid'",'CIDR valides')
    failure('Clé différente refusée sur la base existante',
            "from cryptography.fernet import Fernet; os.environ['SERVERLESS_MASTER_KEY']=Fernet.generate_key().decode()",'clé maîtresse ne correspond pas')
    failure('Métadonnées non inscriptibles refusées',None,'unable to open database file',readonly=True)
    container=start();ready(container)
    assert json.loads(request('/healthz',200)['body'])['status']=='ok'
    passed('Reprise de la même base avec la clé officielle')
    # Hold a real SQLite writer lock. The application must fail at its own timeout.
    lock=subprocess.Popen(['docker','exec',container,'python','-u','-B','-c',
        'import sqlite3,time; db=sqlite3.connect("/state/control.sqlite3"); db.execute("BEGIN IMMEDIATE"); print("LOCKED",flush=True); time.sleep(12); db.rollback()'],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert lock.stdout.readline().strip()=='LOCKED'
        request('/auth/login',503)
    finally:
        lock.communicate(timeout=20)
        assert lock.returncode==0
    assert 'database.unavailable' in logs(container)
    request('/api/session',200)
    passed('Verrou réel SQLite : refus 503 puis récupération')
    # Readiness alone does not write. A genuine login/callback verifies writes resumed.
    program='''import urllib.request,urllib.error,urllib.parse
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
client=urllib.request.build_opener(NoRedirect())
try:client.open('http://control:18090/auth/login')
except urllib.error.HTTPError as r:
 assert r.code==303
 state=urllib.parse.parse_qs(urllib.parse.urlsplit(r.headers['Location']).query)['state'][0]
try:client.open(urllib.request.Request('http://control:18090/auth/retour?state='+state+'&error=access_denied',headers={'Cookie':'__Host-p2-flow='+state}))
except urllib.error.HTTPError as r:assert r.code==401
else:raise AssertionError('Callback non refusé')
'''
    run(['docker','run','--rm','--network',project+'_default','--read-only','--cap-drop','ALL',image,'python','-B','-c',program])
    logs(container)
    passed('Écriture reprise et aucune valeur secrète dans les journaux')
    marker='validation-sensitive-'+uuid.uuid4().hex
    response=request('/api/namespaces',422,'POST',{'name':'invalid name','unknown':marker})
    output=logs(container)
    assert marker not in output and marker not in response['body']
    assert any(response['request_id'] in line and '"status": 422' in line for line in output.splitlines())
    passed('Refus de validation journalisé sans valeur du corps')
    completed=True
except BaseException as error:
    checks.append({'name':'Campagne interrompue','status':'failed','error':type(error).__name__})
    raise
finally:
    cleanup=run(base+['down','--remove-orphans'],check=False)
    clean=cleanup.returncode==0
    if clean:shutil.rmtree(work)
    (ROOT/'.proof-control-operations.json').write_text(json.dumps({'image':image,'completed':completed and clean,'checks':checks,'cleanup':clean,'skipped':0},indent=2,ensure_ascii=False)+'\n')
    assert clean,'Nettoyage du seul projet de preuve requis'
