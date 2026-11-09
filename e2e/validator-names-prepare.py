# @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#commandes-reproductibles-du-banc
# @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
import hashlib,json,runpy,subprocess,time
from pathlib import Path
r=runpy.run_path('e2e/execution-suite.py');old='sha256:178394abb337bd70ca9c18a139fc65ab2c1f83d3ad41eed5d5bf79bed2dc0f5e';expected=hashlib.sha256(subprocess.check_output(['git','show','ef4a900:control/app/validator.py'])).hexdigest();program='expected='+repr(expected)+'\nold='+repr(old)+'\n'+'''
import hashlib,json,socket,subprocess,time
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
d=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def cmd(a):return subprocess.check_output(a,text=True,timeout=30)
rows=json.loads(cmd(d+['inspect','serverless-api','serverless-runtime-reference']));assert rows[0]['Image']==old and all(v['State']['Health']['Status']=='healthy' for v in rows)
raw=cmd(d+['exec','serverless-api','python','-B','-c',"import hashlib;from pathlib import Path;print(hashlib.sha256(Path('/app/app/validator.py').read_bytes()).hexdigest())"]).strip();assert raw==expected
cmd(d+['tag',old,'p2enjoy-control:before-validator-names'])
print(json.dumps({'completed':True,'old_control_image':old,'old_validator_sha256':raw,'containers':{v['Name']:{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt']} for v in rows},'reference_tag':'p2enjoy-control:before-validator-names','official_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['/etc/spark/env','/run/spark/secrets','/etc/spark/routes']}}))
'''
v=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,text=True,capture_output=True,timeout=90);assert v.returncode==0,v.stderr[-1500:];p=Path('.local/e2e/validator-names-before-build.json');assert not p.exists();p.write_text(json.dumps(json.loads(v.stdout),indent=2)+'\n');print(v.stdout)
