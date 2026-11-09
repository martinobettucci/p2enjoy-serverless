# @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#réalisation-et-preuves
# @verifies docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#instance-et-processus | docs/EXECUTION.md#événement-réponse-et-journaux
"""Real production CLI, Docker and original handlers; no substitute server."""
import base64
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
from uuid import uuid4

ROOT=Path('/srv/p2enjoy-serverless');REPORT=ROOT/'runtime'/'instances-proof.json'
REPORT.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
checks=[];completed=False;work=None;fixture=None;clients=[];installation=str(uuid4());image=None;fixture_image=None


def run(args,*,timeout=60,check=True):
    p=subprocess.run(args,text=True,capture_output=True,cwd=ROOT,timeout=timeout)
    if check and p.returncode:raise RuntimeError('Commande échouée '+args[0]+' '+str(p.returncode))
    return p


def owned(kind='container'):
    args=['docker','ps','-aq'] if kind=='container' else ['docker','network','ls','-q']
    return run(args+['--filter','label=tech.p2enjoy.serverless.installation='+installation]).stdout.split()


def passed(name):
    checks.append({'name':name,'status':'passed'});print('PASS',name,flush=True)


class Client:
    def __init__(self,handler='invoke.cjs.handler',*,memory=256,cpu=.25,config=None,network='bridge',expect_ready=True):
        self.function_id=str(uuid4());self.revision_id=str(uuid4());self.ready=None;self.buffer=bytearray();self.secrets=(configuration if config is None else config).get('secrets',{})
        args=['python3','-B','-m','control.app.instances','--image',image,'--code',str(code),'--work',str(work),
              '--installation',installation,'--function-id',self.function_id,'--revision-id',self.revision_id,
              '--handler',handler,'--function-name','invocation-proof','--memory-mib',str(memory),'--cpu',str(cpu),'--network',network]
        self.p=subprocess.Popen(args,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        clients.append(self);self.send(configuration if config is None else config)
        self.ready=self.read(30)
        if expect_ready:assert self.ready.get('ready') is True,self.ready

    def send(self,data):
        self.p.stdin.write(json.dumps(data,ensure_ascii=False).encode()+b'\n');self.p.stdin.flush()

    def read(self,timeout=40):
        deadline=time.monotonic()+timeout;offset=0
        with selectors.DefaultSelector() as selector:
            selector.register(self.p.stdout,selectors.EVENT_READ)
            while self.buffer.find(b'\n',offset)<0:
                assert time.monotonic()<deadline,'Réponse du pilote absente'
                assert selector.select(max(.01,deadline-time.monotonic())),'Échéance du pilote'
                chunk=os.read(self.p.stdout.fileno(),65536)
                assert chunk,'Pilote fermé sans réponse'
                offset=len(self.buffer);self.buffer.extend(chunk)
                assert len(self.buffer)<=40*1024**2,'Réponse diagnostic excessive'
        line,self.buffer=self.buffer.split(b'\n',1)
        value=json.loads(line)
        def inspect(item):
            if isinstance(item,str):
                for secret in self.secrets.values():assert not secret or secret not in item,'Secret exposé'
            elif isinstance(item,dict):
                for child in item.values():inspect(child)
            elif isinstance(item,list):
                for child in item:inspect(child)
        inspect(value);return value

    def invoke(self,event,timeout=5):
        self.send({'operation':'invoke','event':event,'timeout_seconds':timeout});return self.read(timeout+25)

    def success(self,event,timeout=5):
        result=self.invoke(event,timeout)
        assert result.get('state')=='succeeded',(event.get('operation'),result.get('error'),result.get('elapsed_seconds'))
        assert result['handler_started'] is True and result['instance_available'] is True
        assert result['instance_id']==self.ready['instance_id']
        assert len(result['logs'].encode())<=65536
        return result

    def stop(self,signum=None):
        if self.p.poll() is None:
            if signum:self.p.send_signal(signum)
            else:self.send({'operation':'close'})
            answer=self.read(20)
            assert answer=={'closed':True},answer
        self.p.wait(timeout=10)
        stderr=self.p.stderr.read()
        assert not stderr,{'diagnostic_inattendu':True,'future_non_recue':b'exception was never retrieved' in stderr,
                           'coroutine_non_attendue':b'was never awaited' in stderr,'traceback':b'Traceback' in stderr}
        assert self.p.returncode==0,self.p.returncode
        self.absent()

    def absent(self):
        assert self.ready and self.ready.get('container_id')
        assert run(['docker','inspect',self.ready['container_id']],check=False).returncode!=0
        if self.ready['network_id']:assert run(['docker','network','inspect',self.ready['network_id']],check=False).returncode!=0
        assert not Path(self.ready['channel']).exists(),'Canal survivant'


def content(result):return json.loads(result['response']['body'])


def same_processes(client):
    top=run(['docker','top',client.ready['container_id'],'-eo','pid,ppid,comm']).stdout.splitlines()[1:]
    assert sorted(int(line.split()[0]) for line in top)==client.ready['baseline_pids'],'Processus résiduel'


def started(client,marker,timeout=5):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if run(['docker','exec',client.ready['container_id'],'test','-f',marker],check=False).returncode==0:return
        time.sleep(.05)
    raise AssertionError('Début effectif non observé')


try:
    image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime:dev']).stdout.strip()
    fixture_image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime-qualification:dev']).stdout.strip()
    cell=json.loads(run(['docker','exec','serverless-api','python','-c',
        'import os,json;print(json.dumps({k:os.environ[k] for k in ("QUALIFICATION_PUBLIC_LABEL","QUALIFICATION_SYNTHETIC_SECRET","SERVERLESS_PUBLIC_URL")}))']).stdout)
    assert all(cell.values()),'Configuration officielle manquante'
    configuration={'environment':{'QUALIFICATION_PUBLIC_LABEL':cell['QUALIFICATION_PUBLIC_LABEL'],'QUALIFICATION_TARGET_URL':cell['SERVERLESS_PUBLIC_URL']},
                   'secrets':{'QUALIFICATION_SYNTHETIC_SECRET':cell['QUALIFICATION_SYNTHETIC_SECRET']}}
    work=Path(tempfile.mkdtemp(prefix='ip-',dir=ROOT/'state'));code=work/'code';code.mkdir()
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
    fixture=run(['docker','create','--name','serverless-invocation-fixture-source-'+installation[:8],'--network','none',fixture_image]).stdout.strip()
    run(['docker','cp',fixture+':/fixtures/.',str(code)]);run(['docker','rm',fixture]);fixture=None
    c=Client()
    first=c.success({'operation':'echo','body':'original','headers':{'authorization':'business-value'}})
    one=content(first);two=content(c.success({'operation':'echo'}))
    assert one['calls']==two['calls']==1 and one['pid']!=two['pid']
    assert one['event']['headers']['authorization']=='business-value'
    assert one['context']['awsRequestId']==first['invocation_id'] and one['context']['functionVersion']==c.revision_id
    assert one['context']['functionName']=='invocation-proof' and one['context']['memoryLimitInMB']=='256'
    assert 0<one['context']['remaining']<=5000 and one['secret_present']
    assert one['label']==cell['QUALIFICATION_PUBLIC_LABEL']
    assert one['environment']==sorted(configuration['environment']|configuration['secrets'])
    passed('Conteneur chaud, enfant neuf, événement et contexte réels')
    for operation,expected in [('callback','callback'),('double','first'),('promise','promise')]:
        assert content(c.success({'operation':operation}))==expected
    passed('Callback et Promise : première terminaison conservée')
    for character,size in [('\0',1024**2),('é',512*1024),('\n',1024**2)]:
        body=character*size;result=content(c.success({'operation':'digest','body':body},15))
        assert result=={'bytes':len(body.encode()),'sha256':hashlib.sha256(body.encode()).hexdigest()}
    passed('Entrées UTF-8 de 1 Mio avec expansion JSON')
    for character in ('\0','\n','x'):
        result=c.success({'operation':'body','character':character,'size':6*1024**2},20)
        assert result['response']['body']==character*(6*1024**2)
    passed('Réponses texte de 6 Mio exacts, NUL et retours à la ligne inclus')
    result=c.success({'operation':'binary'})['response']
    assert result['isBase64Encoded'] is True and base64.b64decode(result['body'])==bytes([0,255,10,128])
    passed('Réponse binaire canonique')
    result=c.success({'operation':'headers'})['response']
    assert result['headers']==[['x-one','new'],['x-one','second'],['x-end','end'],['x-preserve','kept']],result['headers']
    passed('En-têtes multiples et retrait des champs hop-by-hop et CORS')
    invalid=[None,{}, {'statusCode':199,'body':''},{'statusCode':600,'body':''},{'statusCode':True,'body':''},
             {'statusCode':200,'body':False},{'statusCode':200,'body':'YQ','isBase64Encoded':True},
             {'statusCode':200,'body':'','headers':{'X-Test':'bad\nvalue'}},
             {'statusCode':200,'body':'','headers':{'X-Test':'a','x-test':'b'}},
             {'statusCode':200,'body':'','multiValueHeaders':{'X-Test':['x']*129}},
             {'statusCode':200,'body':'','headers':{'X-Test':'x'*32768}}]
    for value in invalid:
        result=c.invoke({'operation':'invalid','value':value});assert result.get('error')=='invalid_handler_response',result.get('error')
    result=c.invoke({'operation':'body','character':'x','size':6*1024**2+1},20)
    assert result.get('error')=='invalid_handler_response'
    passed('Réponses malformées et dépassements de corps/en-têtes refusés')
    for operation in ('throw','reject','exit'):
        result=c.invoke({'operation':operation})
        assert result.get('error')==('handler_exited' if operation=='exit' else 'handler_error'),result.get('error')
        assert result['instance_available'] and result['handler_started']
    passed('Exception, rejet et sortie sans résultat distincts, instance réutilisable')
    logged=c.success({'operation':'logs'});assert '[redacted]' in logged['logs'] and 'stderr' in logged['logs']
    assert c.success({'operation':'echo'})['logs']==''
    logged=c.success({'operation':'many-logs'});assert logged['logs_truncated'] and logged['logs'].startswith('[redacted]')
    logged=c.success({'operation':'binary-logs'});assert logged['logs_truncated'] and set(logged['logs'])=={'\ufffd'}
    passed('Logs bornés, stdout/stderr, secrets expurgés et remise à zéro')
    confined=content(c.success({'operation':'confinement'}))
    assert all(value=='EROFS' for value in confined['writes'].values()) and not confined['docker']
    assert confined['tmp']=='yes' and confined['secret_present'] and confined['platform_environment']==[]
    assert content(c.success({'operation':'private'}))['statuses']==[409,403,403,403]
    info=json.loads(run(['docker','inspect',c.ready['container_id']]).stdout)[0];host=info['HostConfig']
    assert host['ReadonlyRootfs'] and host['Memory']==host['MemorySwap']==256*1024**2
    assert host['NanoCpus']==250000000 and host['PidsLimit']==64 and host['Init'] and host['CapDrop']==['ALL']
    assert 'no-new-privileges:true' in host['SecurityOpt'] and not host.get('PortBindings')
    assert not any('QUALIFICATION_' in value for value in info['Config']['Env'])
    passed('Confinement effectif, clé privée inaccessible et limites Docker appliquées')
    c.send({'operation':'stats'});stats=c.read();assert 0<stats['memory_usage_bytes']<stats['memory_limit_bytes']==256*1024**2
    assert stats['cpu_usage_ns']>0 and 0<stats['pids_current']<=64
    passed('Consommations mémoire, CPU et PIDs mesurées par Docker')
    result=content(c.success({'operation':'egress'},10));assert result['status']==200 and result['body']['status']=='ok'
    passed('Sortie réseau réelle vers la santé HTTPS de la plateforme')
    descendant=content(c.success({'operation':'descendant'},8))
    same_processes(c)
    assert run(['docker','exec',c.ready['container_id'],'test','-d','/proc/'+str(descendant['pid'])],check=False).returncode!=0
    before=run(['docker','exec',c.ready['container_id'],'cat','/tmp/descendant-ticks']).stdout
    time.sleep(.15)
    after=run(['docker','exec',c.ready['container_id'],'cat','/tmp/descendant-ticks']).stdout
    assert before and before==after
    assert content(c.success({'operation':'echo'}))['calls']==1
    passed('Descendant détaché arrêté avant réutilisation du conteneur')
    result=content(c.success({'operation':'pids'},10));assert result['limit'] and 0<result['created']<64
    same_processes(c);c.success({'operation':'echo'});passed('Saturation réelle des PIDs, récolte et reprise')
    c.stop();passed('Fermeture confirmée du conteneur, du réseau et du canal')
    for handler,expected in [('invoke.cjs.sync','sync'),('invoke.cjs.callback','async-callback')]:
        c=Client(handler);assert content(c.success({}))==expected;c.stop()
    passed('Retour synchrone et callback asynchrone sans Promise')
    c=Client('invoke.mjs.handler');result=content(c.success({'body':'hello: world\n'}))
    assert result['parsed']=={'hello':'world'} and result['remaining']>0;c.stop()
    passed('Handler ESM avec await et véritable dépendance YAML')
    c=Client('throws.cjs.handler');result=c.invoke({});assert result.get('error')=='import_failed' and result['handler_started'] is False;c.stop()
    passed('Erreur réelle d’import distinguée du début du handler')
    c=Client(config={'environment':configuration['environment']|{'NODE_OPTIONS':'--require=/code/missing.cjs','LD_PRELOAD':'/missing.so'},'secrets':configuration['secrets']})
    c.success({'operation':'echo'});c.stop();passed('Variables de bootstrap injectées uniquement après lancement de l’enfant')
    escaped=cell['QUALIFICATION_SYNTHETIC_SECRET']+'\n"\\'
    c=Client(config={'environment':configuration['environment'],'secrets':{'QUALIFICATION_SYNTHETIC_SECRET':escaped}})
    assert '[redacted]' in c.success({'operation':'logs'})['logs']
    for operation in ('throw','reject'):assert c.invoke({'operation':operation}).get('error')=='handler_error'
    c.stop();passed('Secret dérivé avec caractères JSON échappés expurgé après décodage')
    c=Client(memory=128,cpu=.05);c.success({'operation':'echo'},15);c.stop();passed('Allocation minimale réelle 128 Mio et 0,05 CPU')
    for operation in ('spin','descendant'):
        c=Client();c.send({'operation':'invoke','event':{'operation':operation,'hang':True},'timeout_seconds':2})
        deadline=time.monotonic()+1.8;observed=False
        while time.monotonic()<deadline:
            marker='/tmp/started' if operation=='spin' else '/tmp/descendant-ready'
            if run(['docker','exec',c.ready['container_id'],'test','-f',marker],check=False).returncode==0:observed=True;break
            time.sleep(.05)
        assert observed,'Début réel non observé'
        result=c.read();assert result.get('error')=='invocation_timeout' and result['handler_started'] is True,result.get('handler_started')
        assert result['container_removed'] and 1.8<=result['elapsed_seconds']<10
        c.absent();c.stop();passed('Timeout avec effet observé et destruction : '+operation)
    c=Client();dispatch=time.monotonic();c.send({'operation':'invoke','event':{'operation':'late'},'timeout_seconds':5})
    started(c,'/tmp/late-started');c.p.send_signal(signal.SIGSTOP)
    try:
        deadline=dispatch+4.5
        while True:
            top=run(['docker','top',c.ready['container_id'],'-eo','pid,ppid,comm']).stdout.splitlines()[1:]
            if sorted(int(line.split()[0]) for line in top)==c.ready['baseline_pids']:break
            assert time.monotonic()<deadline,'Résultat et récolte non observés avant échéance'
            time.sleep(.05)
        time.sleep(max(0,dispatch+5.3-time.monotonic()))
    finally:c.p.send_signal(signal.SIGCONT)
    result=c.read();assert result.get('error')=='invocation_timeout' and result['container_removed'];c.stop()
    passed('Résultat livré à un contrôle suspendu refusé après sa reprise hors délai')
    c=Client(memory=128);since=str(int(time.time()));result=c.invoke({'operation':'memory'},10)
    events=run(['docker','events','--since',since,'--until',str(int(time.time())+1),'--filter','container='+c.ready['container_id'],'--filter','event=oom','--format','{{.Action}}']).stdout
    assert 'oom' in events.splitlines(),'Aucun OOM réel observé'
    assert result['state']=='failed' and result['error'] in ('memory_exceeded','handler_exited','runtime_exited'),result.get('error')
    if result['instance_available']:c.success({'operation':'echo'})
    c.stop();passed('Saturation mémoire effective observée dans les événements Docker')
    for sig,active in [(signal.SIGTERM,True),(signal.SIGINT,False)]:
        c=Client()
        if active:
            c.send({'operation':'invoke','event':{'operation':'sleep','ms':30000},'timeout_seconds':40});started(c,'/tmp/sleep-started')
        c.stop(sig);passed('Signal '+sig.name+' avec stdin ouvert et nettoyage confirmé')
    c=Client();c.send({'operation':'invoke','event':{'operation':'sleep','ms':30000},'timeout_seconds':40})
    started(c,'/tmp/sleep-started');run(['docker','kill',c.ready['container_id']]);result=c.read()
    assert result.get('error')=='runtime_exited' and result['container_removed'];c.stop()
    passed('Disparition réelle du superviseur pendant le handler et nettoyage confirmé')
    for handler in ('loop.cjs.handler','await.mjs.handler'):
        c=Client(handler);result=c.invoke({},2)
        assert result.get('error')=='invocation_timeout' and result['handler_started'] is None and result['container_removed']
        c.stop();passed('Import bloquant compris dans la deadline : '+handler)
    ordinary=work/'ordinary';ordinary.mkdir()
    c=Client(config=configuration|{'mounts':{'/data':str(ordinary)}},expect_ready=False)
    assert c.ready=={'closed':True};assert c.read().get('error')=='instance_start_failed'
    c.p.wait(timeout=10);assert c.p.returncode==1 and not c.p.stderr.read() and not owned()
    passed('Répertoire ordinaire refusé à la place du montage FUSE')
    assert not owned() and not owned('network')
    completed=True
finally:
    for c in clients:
        if c.p.poll() is None:
            c.p.terminate()
            try:c.p.communicate(timeout=20)
            except subprocess.TimeoutExpired:c.p.kill();c.p.communicate(timeout=5)
    for container in owned():run(['docker','rm','-f',container])
    for network in owned('network'):run(['docker','network','rm',network])
    if fixture:run(['docker','rm','-f',fixture])
    cleanup=not owned() and not owned('network')
    if work:shutil.rmtree(work)
    completed=completed and cleanup
    REPORT.write_text(json.dumps({'completed':completed,'cleanup':cleanup,'passed':len(checks),'failed':0 if completed else 1,
        'skipped':0,'scope':'Production instance driver and Docker; public admission and storage integration pending',
        'image':image,'fixture_image':fixture_image,'checks':checks},ensure_ascii=False,indent=2)+'\n')
    assert cleanup,'Ressource de qualification survivante'
