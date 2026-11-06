# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
# @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
"""Run the deployed validator CLI against real Docker and original Node artefacts."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

ROOT=Path('/srv/p2enjoy-serverless')
REPORT=ROOT/'runtime'/'validation-proof.json'
REPORT.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
checks=[];completed=False;work=None;fixture=None;process=None
installation=str(uuid.uuid4())


def run(args,*,input=None,timeout=60,check=True):
    result=subprocess.run(args,input=input,text=True,capture_output=True,timeout=timeout,cwd=ROOT)
    if check and result.returncode:raise RuntimeError('Échec commande '+args[0]+' code '+str(result.returncode))
    return result


def passed(name):
    checks.append({'name':name,'status':'passed'});print('PASS',name,flush=True)


def containers():
    return run(['docker','ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation]).stdout.split()


def command(handler):
    return ['python3','-B','-m','control.app.validator','--image',image,'--code',str(code),
            '--work',str(work),'--handler',handler,'--installation',installation]


def validate(handler,error=None,config=None):
    response=run(command(handler),input=json.dumps(config or configuration),timeout=40,check=False)
    assert response.returncode in (0,1),'Pilote interrompu'
    assert not response.stderr,'Traceback ou diagnostic brut inattendu'
    result=json.loads(response.stdout)
    assert result.get('container_removed') is True,'Conteneur non supprimé'
    assert not containers(),'Conteneur de validation survivant'
    assert result.get('error')==error,(handler,result.get('error'),error)
    assert result['valid']==(error is None),(handler,result['valid'])
    assert response.returncode==(1 if error else 0)
    for value in configuration['secrets'].values():assert value not in response.stdout,'Secret dans le résultat'
    assert len(result.get('logs','').encode())<=65536
    return result


try:
    image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime:dev']).stdout.strip()
    fixture_image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime-qualification:dev']).stdout.strip()
    cell=json.loads(run(['docker','exec','serverless-api','python','-c',
        'import os,json; print(json.dumps({k:os.environ[k] for k in ("QUALIFICATION_PUBLIC_LABEL","QUALIFICATION_SYNTHETIC_SECRET")}))']).stdout)
    assert all(cell.values()),'Configuration réelle absente'
    configuration={'environment':{'QUALIFICATION_PUBLIC_LABEL':cell['QUALIFICATION_PUBLIC_LABEL']},
                   'secrets':{'QUALIFICATION_SYNTHETIC_SECRET':cell['QUALIFICATION_SYNTHETIC_SECRET']}}
    work=Path(tempfile.mkdtemp(prefix='vp-',dir=ROOT/'state'))
    code=work/'code';code.mkdir()
    fixture=run(['docker','create','--network','none',fixture_image]).stdout.strip()
    run(['docker','cp',fixture+':/fixtures/.',str(code)])
    run(['docker','rm',fixture]);fixture=None
    cases=[('good.cjs.handler',None,'CommonJS export propre calculé'),
           ('legacy.handler',None,'CommonJS JS sans type déclaré'),
           ('detected.handler',None,'ESM JS détecté par Node'),
           ('good.mjs.handler',None,'ESM avec await au chargement'),
           ('good.mjs.default',None,'Export ESM default callable'),
           ('esm/entry.handler',None,'JS sous package type module sans extension'),
           ('good.handler','module_ambiguous','Résolution ambiguë refusée'),
           ('absent.handler','module_missing','Module absent refusé'),
           ('good.cjs.absent','handler_not_callable','Export absent refusé'),
           ('inherited.cjs.handler','handler_not_callable','Export hérité refusé'),
           ('inherited.cjs.number','handler_not_callable','Export non callable refusé'),
           ('only-function.cjs.default','handler_not_callable','Default synthétique CJS refusé'),
           ('default-object.mjs.handler','handler_not_callable','Objet default ESM sans export nommé refusé'),
           ('esm-marker.mjs.handler','handler_not_callable','Marqueur module.exports ESM non assimilé à CJS'),
           ('then.mjs.handler','import_invalid_namespace','Résultat import then non namespace refusé'),
           ('dependency.cjs.handler',None,'Vraie dépendance YAML packagée chargée'),
           ('missing-dependency.cjs.handler','dependency_missing','Dépendance absente refusée'),
           ('throws.cjs.handler','import_failed','Exception avec secret expurgée'),
           ('early-exit.cjs.handler','loader_exited','Exit zéro et faux résultat dans stdout refusés'),
           ('environment.cjs.handler',None,'Configuration réelle et confinement effectif cgroups/montages/réseau'),
           ('../good.handler','invalid_handler','Traversée du chemin de handler refusée')]
    for handler,error,name in cases:
        validate(handler,error);passed(name)
    (code/'node_modules').rename(code/'modules-hidden')
    try:validate('dependency.cjs.handler','dependency_missing')
    finally:(code/'modules-hidden').rename(code/'node_modules')
    passed('Retrait réel de la dépendance auparavant valide')
    (code/'linked.cjs').symlink_to(code/'good.cjs')
    validate('linked.cjs.handler','module_link');passed('Module lié refusé')
    (code/'directory.cjs').mkdir()
    validate('directory.cjs.handler','module_not_file');passed('Répertoire à la place du module refusé')
    for invalid in ({'environment':[]},{'environment':{'bad-key':'x'}},
                    {'environment':{'X':True}},{'environment':{'X':'x'*16385}},
                    {'environment':{'X':'one'},'secrets':{'X':'two'}},
                    {'environment':{'X':'x\0y'}},{'unexpected':'field'}):
        response=run(command('good.cjs.handler'),input=json.dumps(invalid),timeout=10,check=False)
        assert response.returncode==1 and not response.stderr
        assert json.loads(response.stdout)=={'valid':False,'error':'validation_input_or_prerequisite'}
        assert not containers()
    passed('Configurations malformées et limites refusées avant création Docker')
    result=validate('logs.cjs.handler')
    assert result['logs_truncated'] is True and result['logs'].startswith('[redacted]\n')
    assert result['logs'][len('[redacted]\n'):].strip('x')=='','Fragment secret conservé à la troncature'
    passed('Logs volumineux drainés et secret fractionné/tronqué expurgé')
    result=validate('logs-boundary.cjs.handler')
    assert result['logs_truncated'] and cell['QUALIFICATION_SYNTHETIC_SECRET'][:8] not in result['logs']
    passed('Secret complet proche de la coupe expurgé avant troncature')
    overlap={'environment':configuration['environment'],
             'secrets':configuration['secrets']|{'QUALIFICATION_SECRET_SUFFIX':cell['QUALIFICATION_SYNTHETIC_SECRET'][-2]}}
    result=validate('logs-overlap.cjs.handler',config=overlap)
    assert result['logs_truncated'] and cell['QUALIFICATION_SYNTHETIC_SECRET'][:8] not in result['logs']
    passed('Secrets superposés et troncature conservent les offsets bruts')
    result=validate('partial-connection.mjs.handler')
    assert result['elapsed_seconds']<5,'Nettoyage retardé par une connexion partielle'
    passed('Connexion partielle du descendant fermée avant nettoyage Docker')
    validate('malformed-result.mjs.handler')
    passed('Résultat privé malformé refusé sans traceback puis vrai résultat accepté')
    result=validate('logs-binary.cjs.handler')
    assert result['logs_truncated'] and result['logs'] and set(result['logs'])=={'\ufffd'}
    passed('Logs binaires convertis en UTF8 sans dépasser la borne de sortie')
    config={'environment':configuration['environment']|{'NODE_OPTIONS':'--require=/code/missing.cjs','LD_PRELOAD':'/missing.so'},
            'secrets':configuration['secrets']}
    validate('environment.cjs.handler',config=config);passed('Variables de bootstrap isolées du superviseur')
    for handler in ('loop.cjs.handler','await.mjs.handler'):
        result=validate(handler,'validation_timeout')
        assert 14.5<=result['elapsed_seconds']<=22,result['elapsed_seconds']
        passed('Échéance extérieure et nettoyage : '+handler)

    # One real validation with a detached descendant; observe from the real control.
    process=subprocess.Popen(command('descendant.cjs.handler'),cwd=ROOT,text=True,
                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.stdin.write(json.dumps(configuration));process.stdin.close();process.stdin=None
    observed=[];channel=None;deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        sockets=list(work.glob('v-*/control.sock'))
        active=containers()
        if sockets and active:
            channel=sockets[0]
            # Child and descendant must both exist before the timeout.
            top=run(['docker','top',active[0],'-eo','pid,ppid,args']).stdout.splitlines()[1:]
            if any('setInterval' in line for line in top):
                for line in top:
                    pid=int(line.split()[0]);stat=Path('/proc')/str(pid)/'stat'
                    if stat.exists():observed.append((pid,stat.read_text().split()[21]))
                break
        time.sleep(.1)
    assert channel and observed,'Descendant réel non observé'
    inside='/state/'+str(channel.relative_to(ROOT/'state'))
    program='''import socket,http.client,json
class U(http.client.HTTPConnection):
 def connect(self):
  self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.settimeout(3);self.sock.connect(%r)
results=[]
for method,path in [('GET','/status'),('GET','/configuration')]:
 c=U('localhost');c.request(method,path,body='{}',headers={'Content-Type':'application/json'});r=c.getresponse();results.append(r.status);r.read();c.close()
assert results==[202,409],results
# Real malformed requests against the production private protocol.
for raw in [b'GET /status HTTP/1.1\\r\\nHost: local\\r\\nHost: duplicate\\r\\n\\r\\n',
            b'POST /result HTTP/1.1\\r\\nContent-Length: 262145\\r\\n\\r\\n',
            b'GET /status HTTP/1.1\\r\\nX: '+b'x'*9000+b'\\r\\n\\r\\n']:
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(3);s.connect(%r);s.sendall(raw)
 try:assert not s.recv(1024)
 except ConnectionResetError:pass
 finally:s.close()
held=[]
try:
 for _ in range(4):
  s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(3);s.connect(%r);s.sendall(b'GET /status HTTP/1.1\\r\\n');held.append(s)
 import time;time.sleep(.05)
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(3);s.connect(%r);s.sendall(b'GET /status HTTP/1.1\\r\\n\\r\\n')
 try:assert not s.recv(1024)
 except ConnectionResetError:pass
 finally:s.close()
finally:
 for s in held:s.close()
print(json.dumps(results))
'''%(inside,inside,inside,inside)
    states=json.loads(run(['docker','exec','serverless-api','python','-c',program]).stdout)
    assert states==[202,409],states
    stdout,stderr=process.communicate(timeout=35)
    assert not stderr and process.returncode==1
    result=json.loads(stdout)
    assert result['error']=='validation_timeout' and result['container_removed'] is True
    assert not containers()
    for pid,birth in observed:
        stat=Path('/proc')/str(pid)/'stat'
        assert not stat.exists() or stat.read_text().split()[21]!=birth,'Processus de validation survivant'
    passed('UDS depuis le vrai contrôle, configuration unique, descendants détruits')
    assert not list(work.glob('v-*')),'Répertoire de protocole survivant'
    health=run(['docker','inspect','--format','{{.State.Health.Status}}','serverless-api']).stdout.strip()
    assert health=='healthy'
    passed('Contrôle sain et absence de ressources de validation survivantes')
    completed=True
finally:
    if process and process.poll() is None:
        try:process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:process.communicate(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=5)
    if fixture:run(['docker','rm','-f',fixture])
    for container in containers():run(['docker','rm','-f',container])
    if work:shutil.rmtree(work)
    REPORT.write_text(json.dumps({'completed':completed,'checks':checks,'failed':0 if completed else 1,
        'skipped':0,'image_id':locals().get('image'),'fixture_image_id':locals().get('fixture_image')},indent=2)+'\n')
