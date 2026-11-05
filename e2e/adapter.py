# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#preuves
# @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#outil-et-manifeste | docs/DEPLOYMENT.md#artefact
# Execute the real CLI against original project files, inspect its actual ZIPs.
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import yaml

ROOT=Path(__file__).resolve().parent.parent
REPORT=ROOT/'.local/e2e/adapter.json'
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
checks=[];completed=False
baseline=yaml.safe_load((ROOT/'qualification/serverless.platform.yml').read_text())


def invoke(project,command='plan',options=(),success=True,filename='serverless.yml'):
    result=subprocess.run([sys.executable,'-m','adapter',command,'--config',str(project/filename),*options],
                          cwd=ROOT,text=True,capture_output=True,timeout=90)
    assert (result.returncode==0)==success,f'{command} : code {result.returncode}, succès attendu {success}'
    if success:return json.loads(result.stdout)
    assert 'Traceback' not in result.stderr
    return result.stderr


def manifest(project,data):
    (project/'serverless.yml').write_text(yaml.safe_dump(data,sort_keys=False))


def check(name,action):
    started=time.monotonic()
    try:action()
    except BaseException as error:
        checks.append({'name':name,'status':'failed','error':type(error).__name__});raise
    checks.append({'name':name,'status':'passed','duration_seconds':round(time.monotonic()-started,3)})
    print('PASS',name,flush=True)


try:
    with tempfile.TemporaryDirectory(prefix='p2enjoy-adapter-real-') as directory:
        project=Path(directory)/'project';project.mkdir()
        shutil.copytree(ROOT/'qualification/src',project/'src')
        shutil.copy2(ROOT/'qualification/package.json',project/'package.json')
        manifest(project,baseline)

        def nominal():
            plan=invoke(project);assert plan['service']=='p2enjoy-qualification' and len(plan['functions'])==12
            indexed={row['name']:row for row in plan['functions']}
            assert indexed['spin']['config']['timeout_seconds']==.4
            assert indexed['worker']['config']['storage']['data']=={'enabled':True,'quota_mib':8}
            assert indexed['business']['secret_names']==['QUALIFICATION_BUSINESS_TOKEN']
            assert indexed['configuration']['environment_names']==['QUALIFICATION_PUBLIC_LABEL']
            assert all('configuration' not in row for row in plan['functions'])
            assert 'runtime_validation' not in plan
        check('Plan réel des douze fonctions : ressources et noms de configuration',nominal)

        def packaged():
            result=invoke(project,'package');assert result['functions']==12 and result['runtime_validation']=='pending'
            descriptor=json.loads((project/'.serverless-p2/deployment.json').read_text())
            assert len(descriptor['artifacts'])==12
            assert 'secrets' not in json.dumps(descriptor)
            for name,artifact in descriptor['artifacts'].items():
                archive=project/'.serverless-p2'/artifact['file']
                assert hashlib.sha256(archive.read_bytes()).hexdigest()==artifact['sha256']
                with zipfile.ZipFile(archive) as zipped:
                    assert set(zipped.namelist())=={'package.json','src/handlers.cjs'}
                    for row in artifact['inventory']:
                        content=zipped.read(row['path'])
                        assert content==(project/row['path']).read_bytes()
                        assert len(content)==row['size'] and hashlib.sha256(content).hexdigest()==row['sha256']
            previous={name:artifact['sha256'] for name,artifact in descriptor['artifacts'].items()}
            invoke(project,'package')
            current=json.loads((project/'.serverless-p2/deployment.json').read_text())
            assert {name:artifact['sha256'] for name,artifact in current['artifacts'].items()}==previous
        check('ZIP réels : contenu, inventaire, exclusions et reproductibilité',packaged)

        def inheritance():
            data=copy.deepcopy(baseline)
            data['provider']['env']={'BASE':'provider','REMOVED':'base','ON':'plain'}
            data['provider']['secret']={'PRIVATE':'qualification-sensitive-marker'}
            data['functions']={'CamelCase':{'handler':'src/handlers.echo','env':{'REMOVED':None,'LOCAL':'function'}},
                               'empty':{'handler':'src/handlers.echo','env':{}},
                               'null':{'handler':'src/handlers.echo','env':None}}
            manifest(project,data);plan=invoke(project)
            rows={row['name']:row for row in plan['functions']}
            assert rows['CamelCase']['environment_names']==['BASE','LOCAL','ON']
            assert rows['empty']['environment_names']==rows['null']['environment_names']==['BASE','ON','REMOVED']
            assert all(row['secret_names']==['PRIVATE'] for row in rows.values())
            assert 'qualification-sensitive-marker' not in json.dumps(plan)
            invoke(project,'package')
            assert 'qualification-sensitive-marker' not in (project/'.serverless-p2/deployment.json').read_text()
        check('Héritage vide/null, retrait de clé, casse et confidentialité du descripteur',inheritance)

        def scaleway():
            data=copy.deepcopy(baseline);data['provider']={'name':'scaleway','runtime':'node20','env':{},'secret':{},'scwToken':'provider-sensitive-marker'}
            data['plugins']=['serverless-scaleway-functions'];data['configValidationMode']='off'
            data['functions']={'job':{'handler':'src/handlers.echo','memoryLimit':128,'timeout':'0.4s','minScale':0,'maxScale':2,
                                      'httpOption':'enabled','privacy':'public','custom_domains':[],
                                      'events':[{'schedule':{'rate':'*/5 2 * * 1-5','enabled':False}}]}}
            manifest(project,data);invoke(project,success=False)
            invoke(project,options=('--runtime','node24'),success=False)
            plan=invoke(project,options=('--runtime','node24','--accept-provider-differences'))
            fn=plan['functions'][0]
            assert fn['config']['timeout_seconds']==.4 and fn['config']['memory_mib']==128
            assert fn['events']['schedules']==[{'cron':'*/5 2 * * 1-5','enabled':False,'timezone':'UTC'}]
            assert fn['events']['http'][0]['implicit'] is True
            assert len(plan['warnings'])>=6 and 'provider-sensitive-marker' not in json.dumps(plan)
        check('Conversion et différences fournisseur explicites, cron et HTTP implicite',scaleway)

        for title,mutate in [
            ('Alias contradictoires',lambda d:d['provider'].update(env={},environment={})),
            ('Collision variable et secret',lambda d:d['provider'].update(env={'SAME':'a'},secret={'SAME':'b'})),
            ('Variable non chaîne',lambda d:d['provider'].update(env={'FLAG':True})),
            ('Référence non prise en charge',lambda d:d['provider'].update(env={'VALUE':'${file:secret}'})),
            ('Champ inconnu',lambda d:d['functions']['echo'].update(unsupported=True)),
            ('Timeout hors borne',lambda d:d['functions']['echo'].update(timeout=0)),
            ('Mémoire booléenne',lambda d:d['functions']['echo'].update(memorySize=True)),
            ('Entier de 400 chiffres',lambda d:d['functions']['echo'].update(memorySize=10**399)),
            ('Stockage activé sans quota',lambda d:d['functions']['state']['p2enjoy']['storage']['data'].pop('quota_mib')),
            ('CPU non fini',lambda d:d['functions']['echo'].update(p2enjoy={'cpu':float('nan')})),
            ('Concurrence supérieure au maximum',lambda d:d['functions']['echo'].update(p2enjoy={'concurrency':2})),
            ('Cron hors plage',lambda d:d['functions']['echo'].update(events=[{'schedule':{'rate':'60 * * * *'}}])),
            ('Chemin de handler sortant',lambda d:d['functions']['echo'].update(handler='../outside.echo')),
            ('Glob avancé non supporté',lambda d:d.update(package={'patterns':['src/{a,b}.js']})),
        ]:
            def negative(mutate=mutate):
                data=copy.deepcopy(baseline);mutate(data);manifest(project,data);invoke(project,success=False)
            check(title+' refusé par la vraie CLI',negative)

        def malformed():
            for text in ('service: a\nservice: b\n','service: &value example\nprovider: *value\n',
                         'service: [broken, qualification-sensitive-marker\n',
                         'service: example\nprovider:\n  memorySize: '+('9'*5000)+'\n'):
                (project/'serverless.yml').write_text(text)
                error=invoke(project,success=False)
                assert 'qualification-sensitive-marker' not in error
        check('YAML dupliqué, alias et syntaxe refusés sans valeur sensible',malformed)

        def missing():
            data=copy.deepcopy(baseline);data['package']={'patterns':['!**','package.json']};manifest(project,data)
            invoke(project,'package',success=False)
        check('Module effectivement exclu de l’archive refusé',missing)

        def unsafe_sources():
            data=copy.deepcopy(baseline);data['functions']={'echo':data['functions']['echo']};data['package']={'patterns':[]};manifest(project,data)
            outside=Path(directory)/'outside';outside.write_text('outside-source-marker')
            link=project/'escape';link.symlink_to(outside)
            try:invoke(project,'package',success=False)
            finally:link.unlink()
            unsafe=project/'unsafe\nname';unsafe.write_text('invalid-path')
            try:invoke(project,'package',success=False)
            finally:unsafe.unlink()
            (project/'.env').write_text('SECRET=private-config-marker')
            (project/'.aws').mkdir();(project/'.aws/credentials').write_text('private-config-marker')
            invoke(project,'package')
            descriptor=json.loads((project/'.serverless-p2/deployment.json').read_text())
            artifact=descriptor['artifacts']['echo']
            with zipfile.ZipFile(project/'.serverless-p2'/artifact['file']) as archive:
                assert not any('.env' in name or '.aws' in name or '.serverless-p2' in name or 'serverless.yml' in name for name in archive.namelist())
        check('Vrais liens et noms dangereux refusés ; fichiers confidentiels exclus',unsafe_sources)

        def alternate_manifest():
            data=copy.deepcopy(baseline);data['functions']={'echo':data['functions']['echo']};data['package']={'patterns':[]}
            marker='alternate-manifest-confidential-value';data['provider']['secret']={'PRIVATE':marker}
            for name in ('deploy.yml','manifest.json'):
                config=project/name;config.write_text(yaml.safe_dump(data))
                linked=project/'config-copy.txt';os.link(config,linked)
                try:
                    invoke(project,'package',filename=name)
                    descriptor=json.loads((project/'.serverless-p2/deployment.json').read_text())
                    assert marker not in json.dumps(descriptor)
                    with zipfile.ZipFile(project/'.serverless-p2'/descriptor['artifacts']['echo']['file']) as archive:
                        assert name not in archive.namelist() and linked.name not in archive.namelist()
                        assert all(marker.encode() not in archive.read(member) for member in archive.namelist())
                finally:config.unlink();linked.unlink()
        check('Manifeste alternatif et son vrai lien physique exclus avec leurs valeurs',alternate_manifest)

        def output_race():
            data=copy.deepcopy(baseline);data['functions']={'echo':data['functions']['echo']};data['package']={'patterns':[]};manifest(project,data)
            large=project/'a-large.bin'
            with large.open('wb') as stream:stream.truncate(48*1024*1024)
            witness=Path(directory)/'witness';witness.mkdir()
            (witness/'deployment.json').write_text('untouched-witness')
            output=project/'.serverless-p2';moved=Path(directory)/'moved-output'
            process=subprocess.Popen([sys.executable,'-m','adapter','package','--config',str(project/'serverless.yml')],
                                     cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            changed=False
            try:
                deadline=time.monotonic()+10
                while process.poll() is None and time.monotonic()<deadline:
                    if list(output.glob('.building-*')):
                        output.rename(moved);output.symlink_to(witness,target_is_directory=True);changed=True;break
                    time.sleep(.001)
                assert changed,'La course doit avoir réellement remplacé la sortie pendant le packaging.'
                stdout,stderr=process.communicate(timeout=90)
                assert process.returncode==1 and 'Traceback' not in stderr
                assert (witness/'deployment.json').read_text()=='untouched-witness'
                assert sorted(p.name for p in witness.iterdir())==['deployment.json']
            finally:
                if process.poll() is None:process.kill();process.communicate(timeout=10)
                if changed:output.unlink();moved.rename(output)
                large.unlink()
        check('Remplacement réel de la sortie pendant le packaging : refus sans écriture extérieure',output_race)

        def oversized():
            path=project/'too-large.bin'
            with path.open('wb') as stream:stream.truncate(64*1024*1024+1)
            try:invoke(project,'package',success=False)
            finally:path.unlink()
        check('Fichier réel supérieur à 64 Mio refusé',oversized)
    completed=True
finally:
    REPORT.write_text(json.dumps({'completed':completed,'scope':'CLI plan/package, sans preuve runtime ni upload','checks':checks,'skipped':0},ensure_ascii=False,indent=2)+'\n')
