# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#instances-avec-baux-gérés
# @verifies docs/STORAGE_AGENT.md#instances-avec-baux-gérés
"""Prove installed-root protection using the real DEV console and stopped agent."""
import json
from pathlib import Path
import shlex
import subprocess
import time
import urllib.request
from uuid import uuid4

REPORT=Path('.local/e2e/storage-installation.json');REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text('{"completed":false,"cleanup":false,"skipped":0}\n')
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24']
BASE='http://127.0.0.1:5175/api/v1/sparks/infra-serverless/suggestions';QUERY='?server=spark-experiment'
KEY='SERVERLESS_STORAGE_ROOT_HOST';UNIT='p2enjoy-storage-dev.service'


def remote(code):
    guard='from pathlib import Path\nassert Path("/etc/hostname").read_text().strip()=="infra-serverless"\n'
    result=subprocess.run(SSH+['python3 -I -B -'],input=guard+code,text=True,capture_output=True,timeout=60)
    if result.returncode:raise RuntimeError('Commande SPARK échouée : '+result.stderr[-1000:])
    return json.loads(result.stdout)


def configure(value):
    code='''import json
p=Path('/etc/spark/env.?');lines=p.read_text().splitlines() if p.exists() else []
lines=[line for line in lines if not line.startswith(KEY+'=')]
lines.append(KEY+'='+VALUE);p.write_text('\\n'.join(lines)+'\\n');print('{}')
'''.replace('KEY',repr(KEY)).replace('VALUE',repr(value))
    remote(code)
    with urllib.request.urlopen(BASE+QUERY,timeout=20) as response:rows=json.load(response)['suggestions']
    row=next(row for row in rows if row['kind']=='variables')
    keep=[i+1 for i,line in enumerate(row['body'].splitlines()) if not line.startswith(KEY+'=')]
    payload={'sha256':row['sha256'],'entries':[{'name':KEY,'value':value,'secret':False}],'conserver':keep}
    request=urllib.request.Request(BASE+'/variables/apply'+QUERY,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=30) as response:json.load(response)


def service(action):
    return remote('import subprocess,json\nsubprocess.run(["systemctl",'+repr(action)+','+repr(UNIT)+'],check=True,timeout=40)\nprint("{}")')


def health():
    return remote('''import subprocess,json
command=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock',
         'exec','-i','serverless-api','python','-B','-m','app.storage_client']
answer=subprocess.run(command,input='{"op":"health"}\\n',text=True,capture_output=True,timeout=15)
print(answer.stdout)
''')


before=remote('''import json,subprocess
unit=Path('/etc/systemd/system/p2enjoy-storage-dev.service').read_text()
root=json.loads(next(line.removeprefix('# StorageRoot: ') for line in unit.splitlines() if line.startswith('# StorageRoot: ')))
print(json.dumps({'root':root,'unit':unit,'container':subprocess.check_output(['runuser','-u','spark-docker','--','docker',
'--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Id}}','serverless-api'],text=True).strip()}))
''')
initial=health();assert initial['ok'] and initial['result']['healthy'] and not initial['result']['leases']
candidate='/srv/p2enjoy-serverless/storage-rejected-root-'+uuid4().hex
failure=None;completed=False;restored=False
try:
    service('stop');configure(candidate)
    result=remote('''import subprocess,json
result=subprocess.run(['python3','-I','-B','/srv/p2enjoy-serverless/storage/install-dev.py'],text=True,capture_output=True,timeout=30)
assert result.returncode!=0 and 'changing an installed storage root requires explicit migration' in result.stderr
assert not Path(CANDIDATE).exists()
assert Path('/etc/systemd/system/p2enjoy-storage-dev.service').read_text()==UNIT_TEXT
print(json.dumps({'refused':True,'new_root_created':False,'unit_unchanged':True}))
'''.replace('CANDIDATE',repr(candidate)).replace('UNIT_TEXT',repr(before['unit'])))
    completed=True
except BaseException as error:
    failure=type(error).__name__+': '+str(error)[:1000]
finally:
    try:
        configure(before['root']);service('start');deadline=time.monotonic()+20
        while True:
            current=health()
            if current.get('ok') and current['result']['healthy']:break
            assert time.monotonic()<deadline,'Agent non rétabli'
            time.sleep(.2)
        assert current['result']['installation_id']==initial['result']['installation_id']
        verification=remote('''import subprocess,json,shlex
configured={}
for line in Path('/etc/spark/env').read_text().splitlines():
 bits=shlex.split(line,comments=True)
 if len(bits)==1 and bits[0].startswith('SERVERLESS_STORAGE_ROOT_HOST='):configured['root']=bits[0].split('=',1)[1]
assert configured['root']==EXPECTED
container=subprocess.check_output(['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock',
'inspect','--format','{{.Id}}','serverless-api'],text=True).strip()
assert container==CONTAINER
print(json.dumps({'official_root_restored':True,'control_container_unchanged':True}))
'''.replace('EXPECTED',repr(before['root'])).replace('CONTAINER',repr(before['container'])))
        restored=True
    finally:
        REPORT.write_text(json.dumps({'completed':completed and restored,'cleanup':restored,'failed':int(not completed or not restored),
            'skipped':0,'passed':int(completed),'failure':failure,
            'checks':[{'name':'Racine différente refusée avec agent arrêté, restauration par console et identité conservée',
                       'status':'passed' if completed and restored else 'failed'}]},ensure_ascii=False,indent=2)+'\n')
assert completed and restored,failure
print('PASS Racine installée protégée à l’arrêt ; variable officielle et agent rétablis')
