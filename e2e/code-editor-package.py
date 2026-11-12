# @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#interface-et-preuves
# Real locked YAML dependency from the unchanged reference container, packaged with original handlers.
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parent.parent
output=Path(sys.argv[1]).resolve()
assert output.parent.is_dir() and output.is_relative_to(ROOT/'.local/e2e') and not output.exists()
command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24',
         'runuser -u spark-docker -- docker --host unix:///run/user/1001/docker.sock exec serverless-runtime-reference tar -C /app -cf - node_modules/yaml']
result=subprocess.run(command,capture_output=True,check=True,timeout=60)
files={}
with tarfile.open(fileobj=io.BytesIO(result.stdout),mode='r:') as source:
    for member in source:
        if member.isdir():continue
        assert member.isfile() and member.name.startswith('node_modules/yaml/') and '..' not in member.name.split('/')
        assert 0<=member.size<=1024**2
        files[member.name]=source.extractfile(member).read()
assert json.loads(files['node_modules/yaml/package.json'])['version']=='2.9.1'
files.update({name:(ROOT/'qualification/artifacts'/name).read_bytes() for name in ('editor.cjs','editor.mjs')})
files['réglages.yml']='message: Bonjour depuis YAML\r\n'.encode()
files['payload.bin']=bytes(range(256))*16
files['sans-fin.txt']='Dernier caractère conservé : é'.encode()
files['lignes-identiques.txt']='a\r\n\nb'.encode()
files['fins-mixtes.txt']='première\r\ndeuxième\rtroisième\nfin'.encode()
with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=False) as archive:
    for path,data in sorted(files.items()):
        info=zipfile.ZipInfo(path,(1980,1,1,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(stat.S_IFREG|(0o555 if path=='editor.cjs' else 0o444))<<16
        archive.writestr(info,data)
print(json.dumps({'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                  'files':len(files),'yaml_version':'2.9.1','binary_sha256':hashlib.sha256(files['payload.bin']).hexdigest()}))
