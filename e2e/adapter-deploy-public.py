# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#commande-deploy
# @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#commande-deploy
"""Real CLI processes and the public DEV API; no successful identity is substituted."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
REPORT=ROOT/'.local/e2e/adapter-deploy-public.json'
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
checks=[];completed=False
target='https://serverless.lelabs.tech'
credential='p2-e2e-invalid-'+uuid4().hex
service=str(uuid4())


def check(name,action):
    started=time.monotonic()
    try:action()
    except BaseException as error:
        checks.append({'name':name,'status':'failed','error':type(error).__name__});raise
    checks.append({'name':name,'status':'passed','duration_seconds':round(time.monotonic()-started,3)})
    print('PASS',name,flush=True)


try:
    sensitive=os.environ['QUALIFICATION_SYNTHETIC_SECRET'];assert sensitive
    with tempfile.TemporaryDirectory(prefix='p2-deploy-public-') as directory:
        project=Path(directory)
        shutil.copytree(ROOT/'qualification/src',project/'src')
        shutil.copy2(ROOT/'qualification/package.json',project/'package.json')
        data={'service':'qualification-deploy-public','provider':{'name':'p2enjoy','runtime':'nodejs24.x',
              'secret':{'QUALIFICATION_SYNTHETIC_SECRET':'${env:QUALIFICATION_SYNTHETIC_SECRET}'}},
              'functions':{'echo':{'handler':'src/handlers.echo'}},
              'package':{'patterns':['!**','src/**','package.json']}}
        config=project/'serverless.yml';config.write_text(json.dumps(data))

        def invoke(*,environment=None,options=None,expected=1):
            env=dict(os.environ);env.update(P2_SERVERLESS_URL=target,P2_SERVERLESS_TOKEN=credential)
            for key,value in (environment or {}).items():
                if value is None:env.pop(key,None)
                else:env[key]=value
            args=options if options is not None else ['deploy','--service',service]
            result=subprocess.run([sys.executable,'-B','-m','adapter',*args,'--config',str(config)],cwd=ROOT,
                env=env,capture_output=True,text=True,timeout=90)
            assert result.returncode==expected,f'Code {result.returncode}, attendu {expected}'
            combined=result.stdout+result.stderr
            assert 'Traceback' not in combined and sensitive not in combined and credential not in combined
            return result

        def options():
            invoke(options=['deploy'],expected=2)
            for command in ('plan','package'):invoke(options=[command,'--service',service],expected=2)
        check('CLI réelle : service obligatoire pour deploy uniquement',options)

        def identifiers():
            for value in ('not-an-id','AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA','../functions',credential):
                result=json.loads(invoke(options=['deploy','--service',value]).stdout)
                assert not result['completed'] and result['error']['code']=='invalid_identifier'
                assert 'service_id' not in result
        check('UUID de service invalide refusé avant mutation',identifiers)

        for title,endpoint in [
            ('HTTP',target.replace('https:','http:')),
            ('Identifiants URL','https://private-user:private-password@serverless.lelabs.tech'),
            ('Chemin URL',target+'/api'),('Query URL',target+'?x=1'),('Fragment URL',target+'#fragment'),
            ('Port invalide',target+':65536'),('Port zéro',target+':0'),('Caractère de contrôle',target+'\n')]:
            def invalid_origin(endpoint=endpoint):
                result=json.loads(invoke(environment={'P2_SERVERLESS_URL':endpoint}).stdout)
                assert result['error']['code']=='invalid_https_origin' and result['results']==[]
            check(title+' refusé par la vraie CLI',invalid_origin)

        def invalid_tokens():
            for value in (None,'','invalid\r\nheader','non-ascii-é','x'*4097):
                result=json.loads(invoke(environment={'P2_SERVERLESS_TOKEN':value}).stdout)
                assert result['error']['code']=='missing_or_invalid_service_token'
        check('Jeton absent ou impropre à un en-tête refusé localement',invalid_tokens)

        def missing_environment():
            result=invoke(environment={'QUALIFICATION_SYNTHETIC_SECRET':None})
            assert 'QUALIFICATION_SYNTHETIC_SECRET' in result.stderr
            assert not result.stdout
        check('Valeur de manifeste absente : échec de résolution avant réseau',missing_environment)

        def large_configuration():
            original=data['provider']['environment'] if 'environment' in data['provider'] else None
            data['provider']['environment']={f'KEY_{i}':'x'*4096 for i in range(128)}
            config.write_text(json.dumps(data))
            try:
                result=json.loads(invoke().stdout)
                assert result['error']['code']=='configuration_body_too_large' and result['results']==[]
                assert not (project/'.serverless-p2').exists()
            finally:
                if original is None:data['provider'].pop('environment')
                else:data['provider']['environment']=original
                config.write_text(json.dumps(data))
        check('Configuration résolue trop grande refusée avant packaging et mutation',large_configuration)

        def actual_rejection():
            result=json.loads(invoke().stdout)
            assert result['error']=={'code':'http_401','status':401}
            assert not result['completed'] and result['results']==[]
            descriptor=project/'.serverless-p2/deployment.json'
            assert descriptor.is_file() and sensitive not in descriptor.read_text()
            assert credential not in descriptor.read_text()
            assert len(json.loads(descriptor.read_text())['artifacts'])==1
        check('Véritable HTTPS DEV : jeton invalide refusé 401 après packaging',actual_rejection)
    completed=True
finally:
    REPORT.write_text(json.dumps({'completed':completed,'target':target,
        'scope':'CLI deploy : prérequis, packaging, TLS et refus réel 401 ; aucune publication authentifiée',
        'checks':checks,'skipped':0},ensure_ascii=False,indent=2)+'\n')
