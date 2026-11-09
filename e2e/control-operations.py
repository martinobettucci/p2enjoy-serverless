# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md#périmètre-et-fidélité
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md#périmètre-et-fidélité
# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves
# @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#configuration | docs/SCHEMA.md
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#preuve-native-du-host-et-des-clients-de-panne
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#preuve-native-du-host-et-des-clients-de-panne
# Real immutable control image, real SQLite and real OIDC discovery on DEV only.
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid
from urllib.parse import urlsplit

assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
ROOT=Path('/srv/p2enjoy-serverless/control')
(ROOT/'.proof-control-operations.json').write_text('{"completed":false,"error":"Campagne non terminée"}\n')
checks=[];completed=False
project='p2enjoy-control-proof-'+uuid.uuid4().hex[:10]
http_clients=0
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


image=run(['docker','inspect','--format','{{.Image}}','serverless-api']).stdout.strip()
# Read only the public origin, never the rest of the effective environment.
public_url=run(['docker','exec','serverless-api','python','-B','-c',
                'import os; print(os.environ["SERVERLESS_PUBLIC_URL"])']).stdout.strip()
canonical_host=urlsplit(public_url).netloc
assert public_url.startswith('https://') and canonical_host
docker_socket=run(['docker','inspect','--format','{{range .Mounts}}{{if eq .Destination "/docker.sock"}}{{.Source}}{{end}}{{end}}','serverless-api']).stdout.strip()
storage_channel=run(['docker','inspect','--format','{{range .Mounts}}{{if eq .Destination "/storage-agent"}}{{.Source}}{{end}}{{end}}','serverless-api']).stdout.strip()
assert docker_socket,'Montage Docker du contrôle absent'
assert storage_channel,'Canal réel de stockage absent'
base=['docker','compose','-p',project,'-f',str(compose)]


def start(alter=None,readonly=False):
    command=cmd
    if alter:
        command=['python','-B','-c','import os; '+alter+'; os.execvp("python",'+repr(cmd)+')']
    compose.write_text(json.dumps({'services':{'control':{
        'image':image,'env_file':['/etc/spark/env','/run/spark/secrets'],
        'volumes':[str(state)+':/state'+(':ro' if readonly else ''),docker_socket+':/docker.sock',storage_channel+':/storage-agent:ro'],
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
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
    global http_clients
    http_clients+=1
    program='''import urllib.request,urllib.error,json
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
client=urllib.request.build_opener(NoRedirect())
try:r=client.open(urllib.request.Request('http://control:18090'+%r,method=%r,data=%r,headers={'Content-Type':'application/json','Host':%r}),timeout=15)
except urllib.error.HTTPError as e:r=e
print(json.dumps({'status':r.status,'request_id':r.headers.get('X-Request-ID'),'body':r.read().decode()}))
'''%(path,method,json.dumps(body).encode() if body is not None else None,canonical_host)
    result=run(['docker','run','--rm','--name','serverless-control-http-client-'+project.rsplit('-',1)[-1]+'-'+str(http_clients),'--network',project+'_default','--read-only',
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
    metadata=json.loads(run(['docker','exec',container,'python','-B','-c',
        'import sqlite3,json; db=sqlite3.connect("/state/control.sqlite3"); print(json.dumps({"versions":[r[0] for r in db.execute("SELECT version FROM schema_migrations ORDER BY version")],"installation":db.execute("SELECT value FROM security_metadata WHERE name=?",("installation-id",)).fetchone()[0],"integrity":db.execute("PRAGMA integrity_check").fetchone()[0]}))']).stdout)
    # @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#migration-et-conservation
    assert metadata['versions']==['001_control.sql','002_login_limits.sql','003_deployments.sql','004_function_operations.sql','005_execution.sql','006_storage_commands.sql','007_function_code_hash.sql','008_function_versions.sql'] and metadata['integrity']=='ok'
    uuid.UUID(metadata['installation']);passed('Huit migrations réelles, intégrité SQLite et UUID d’installation')
    competing=run(base+['run','--rm','--name','serverless-control-lock-contender-'+project.rsplit('-',1)[-1],'--no-deps','control'],timeout=20,check=False)
    assert competing.returncode!=0 and 'Un contrôle possède déjà cet état' in competing.stderr
    ready(container);passed('Second contrôle réel refusé par le verrou exclusif')
    for key in ('SERVERLESS_PUBLIC_URL','OIDC_ISSUER','OIDC_CLIENT_ID','OIDC_CLIENT_SECRET','SERVERLESS_MASTER_KEY'):
        failure('Configuration requise absente : '+key,'os.environ.pop('+repr(key)+',None)', 'Missing cell configuration: '+key)
    for key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST','SERVERLESS_RUNTIME_IMAGE'):
        failure('Configuration de publication absente : '+key,'os.environ.pop('+repr(key)+',None)',key)
    for key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST'):
        failure('Chemin de cellule relatif refusé : '+key,'os.environ['+repr(key)+']="relative/path"',key)
    for key in ('SERVERLESS_STORAGE_ROOT_HOST','SERVERLESS_STORAGE_SOCKET_DIR_HOST'):
        failure('Configuration de stockage absente : '+key,'os.environ.pop('+repr(key)+',None)',key)
        failure('Chemin de stockage relatif refusé : '+key,'os.environ['+repr(key)+']="relative/path"',key)
    for name,expression in [('run',repr('/run/private-socket')),('racine','os.environ["SERVERLESS_STORAGE_ROOT_HOST"]'),
                            ('sous-répertoire','os.environ["SERVERLESS_STORAGE_ROOT_HOST"]+"/socket"'),
                            ('parent',repr('/srv/p2enjoy-serverless'))]:
        failure('Canal de stockage incompatible : '+name,
                'os.environ["SERVERLESS_STORAGE_SOCKET_DIR_HOST"]='+expression,'distinct des données et hors de /run')
    failure('Image mutable refusée',"os.environ['SERVERLESS_RUNTIME_IMAGE']='node:24'",'empreinte Docker immuable')
    failure('Image immuable absente refusée',"os.environ['SERVERLESS_RUNTIME_IMAGE']='sha256:'+'0'*64",'docker_http_404')
    for value in ('511','65537','invalid'):
        failure('Budget d’artefacts invalide : '+value,'os.environ["SERVERLESS_ARTIFACT_BUDGET_MIB"]='+repr(value),'SERVERLESS_ARTIFACT_BUDGET_MIB')
    # @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
    # @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
    for key,values in {
        'SERVERLESS_FUNCTION_CPU_BUDGET':('NaN','.049','64.1','invalid'),
        'SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB':('127','1048577','invalid'),
        'SERVERLESS_FUNCTION_INSTANCE_LIMIT':('0','257','invalid'),
        'SERVERLESS_WAITING_CALL_LIMIT':('0','4097','invalid'),
        'SERVERLESS_FUNCTION_WAITING_CALL_LIMIT':('0','257','invalid')}.items():
        for value in values:failure('Budget d’exécution refusé : '+key+'='+value,'os.environ['+repr(key)+']='+repr(value),'Budgets d’exécution de cellule invalides')
    failure('File par fonction supérieure au plafond global',
            "os.environ['SERVERLESS_WAITING_CALL_LIMIT']='1'; os.environ['SERVERLESS_FUNCTION_WAITING_CALL_LIMIT']='2'",'Budgets d’exécution de cellule invalides')
    failure('URL publique HTTP refusée',"os.environ['SERVERLESS_PUBLIC_URL']='http://serverless.lelabs.tech'",'absolute HTTPS')
    failure('Sous-chemin public refusé',"os.environ['SERVERLESS_PUBLIC_URL']+='/subpath'",'root path')
    failure('Issuer étranger refusé',"os.environ['OIDC_ISSUER']='https://example.org/realm'",'realm lelabs autorisé')
    failure('Clé maîtresse malformée refusée',"os.environ['SERVERLESS_MASTER_KEY']='invalid'",'Fernet key')
    failure('CIDR de proxy malformé refusé',"os.environ['SERVERLESS_TRUSTED_PROXIES']='invalid'",'CIDR valides')
    failure('Clé différente refusée sur la base existante',
            "from cryptography.fernet import Fernet; os.environ['SERVERLESS_MASTER_KEY']=Fernet.generate_key().decode()",'clé maîtresse ne correspond pas')
    failure('Métadonnées non inscriptibles refusées',None,'Read-only file system',readonly=True)
    container=start();ready(container)
    installation=run(['docker','exec',container,'python','-B','-c',
        'import sqlite3; print(sqlite3.connect("/state/control.sqlite3").execute("SELECT value FROM security_metadata WHERE name=?",("installation-id",)).fetchone()[0])']).stdout.strip()
    assert installation==metadata['installation']
    assert json.loads(request('/healthz',200)['body'])['status']=='ok'
    passed('Reprise de la même base avec la clé officielle')
    # Hold a real SQLite writer lock. The application must fail at its own timeout.
    lock=subprocess.Popen(['docker','exec',container,'python','-u','-B','-c',
        'import sqlite3,time; db=sqlite3.connect("/state/control.sqlite3"); db.execute("BEGIN IMMEDIATE"); print("LOCKED",flush=True); time.sleep(12); db.rollback()'],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert lock.stdout.readline().strip()=='LOCKED'
        refused=request('/auth/login',503)
    finally:
        lock.communicate(timeout=20)
        assert lock.returncode==0
    diagnostics=[json.loads(line) for line in logs(container).splitlines() if line.startswith('{')]
    diagnostic=next(row for row in diagnostics if row.get('event')=='database.unavailable' and row.get('request_id')==refused['request_id'])
    assert diagnostic['sqlite_errorname']=='SQLITE_BUSY'
    assert diagnostic['source']['file']=='db.py' and diagnostic['source']['function']=='transaction'
    assert isinstance(diagnostic['source']['line'],int) and diagnostic['source']['line']>0
    request('/api/session',200)
    passed('Verrou réel SQLite : refus 503 puis récupération')
    maintenance_lock=subprocess.Popen(['docker','exec','-i',container,'python','-u','-B','-c',
        'import sqlite3; db=sqlite3.connect("/state/control.sqlite3"); db.execute("BEGIN IMMEDIATE"); print("LOCKED",flush=True); input(); db.rollback()'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert maintenance_lock.stdout.readline().strip()=='LOCKED'
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            result=run(['docker','exec',container,'python','-B','-c',
                'import urllib.request,urllib.error;\ntry: r=urllib.request.urlopen("http://127.0.0.1:18090/healthz",timeout=10)\nexcept urllib.error.HTTPError as e:r=e\nprint(r.status)'])
            if result.stdout.strip()=='503' and 'deployment.cleanup_failed' in logs(container):break
            time.sleep(.5)
        else:raise AssertionError('La panne de maintenance SQLite doit dégrader la santé')
        assert 'deployment.cleanup_failed' in logs(container)
    finally:
        maintenance_lock.communicate(input='RELEASE\n',timeout=20);assert maintenance_lock.returncode==0
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        result=run(['docker','exec',container,'python','-B','-c',
            'import urllib.request; urllib.request.urlopen("http://127.0.0.1:18090/healthz",timeout=10).read()'],check=False)
        if result.returncode==0:break
        time.sleep(.5)
    else:raise AssertionError('La maintenance ne reprend pas après libération du verrou réel')
    passed('Maintenance SQLite réellement bloquée : santé dégradée puis reprise automatique')
    # Readiness alone does not write. A genuine login/callback verifies writes resumed.
    program='''import urllib.request,urllib.error,urllib.parse
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
client=urllib.request.build_opener(NoRedirect())
host=HOST
try:client.open(urllib.request.Request('http://control:18090/auth/login',headers={'Host':host}))
except urllib.error.HTTPError as r:
 assert r.code==303
 state=urllib.parse.parse_qs(urllib.parse.urlsplit(r.headers['Location']).query)['state'][0]
try:client.open(urllib.request.Request('http://control:18090/auth/retour?state='+state+'&error=access_denied',headers={'Cookie':'__Host-p2-flow='+state,'Host':host}))
except urllib.error.HTTPError as r:assert r.code==401
else:raise AssertionError('Callback non refusé')
'''.replace('HOST',repr(canonical_host))
    run(['docker','run','--rm','--name','serverless-control-cookie-client-'+project.rsplit('-',1)[-1],'--network',project+'_default','--read-only','--cap-drop','ALL',image,'python','-B','-c',program])
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
