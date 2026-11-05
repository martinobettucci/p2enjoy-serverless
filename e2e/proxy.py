# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves | docs/PLATFORM_DEV.md#conservation-de-ladresse-cliente
# @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves | docs/PLATFORM_DEV.md#conservation-de-ladresse-cliente
# Real public ingress, direct Spark loopback and a real Docker network client.
import argparse
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

path=Path('.local/e2e/proxy.json');path.parent.mkdir(parents=True,exist_ok=True)
path.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
parser=argparse.ArgumentParser()
parser.add_argument('--expected-proxy',required=True)
args=parser.parse_args()
ids={}
for name,headers in [('public',{}),('public-forged',{
    'X-Forwarded-For':'192.0.2.10, 198.51.100.20','Forwarded':'for=192.0.2.99',
    'X-Real-IP':'192.0.2.77','X-Forwarded-Host':'wrong.example.com','X-Forwarded-Proto':'http'})]:
    try:r=urllib.request.urlopen(urllib.request.Request('https://serverless-dev.lelabs.tech/api/namespaces',headers=headers),timeout=15)
    except urllib.error.HTTPError as error:r=error
    assert r.status==401
    ids[r.headers['X-Request-ID']]=name;r.close()

source=r'''import json,urllib.request,urllib.error,subprocess
try:r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:18090/api/namespaces',headers={'X-Forwarded-For':'192.0.2.10'}),timeout=15)
except urllib.error.HTTPError as error:r=error
assert r.status==401
ids=ID_MAP;ids[r.headers['X-Request-ID']]='direct-loopback';r.close()
client="""import urllib.request,urllib.error
try:r=urllib.request.urlopen(urllib.request.Request('http://10.77.0.24:18090/api/namespaces',headers={'X-Forwarded-For':'192.0.2.10'}),timeout=15)
except urllib.error.HTTPError as error:r=error
assert r.status==401
print(r.headers['X-Request-ID']);r.close()
"""
result=subprocess.run(['docker','run','--rm','--name','p2enjoy-proxy-client-dev','--network','bridge',
 '--memory','64m','--pids-limit','32','--cpus','0.25','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
 'python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d','python','-B','-c',client],
 capture_output=True,text=True,check=True,timeout=30)
ids[result.stdout.strip()]='direct-container'
logs=subprocess.run(['docker','logs','--since','3m','p2enjoy-serverless-dev-control-1'],capture_output=True,text=True,check=True)
for line in (logs.stdout+'\n'+logs.stderr).splitlines():
 if '{' not in line:continue
 try:row=json.loads(line[line.index('{'):])
 except ValueError:continue
 if row.get('request_id') in ids:print(json.dumps({'source':ids[row['request_id']],**row}))
'''.replace('ID_MAP',repr(ids))
remote=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202',
                       'spark-docker@10.77.0.24','python3','-'],input=source,text=True,capture_output=True,check=True,timeout=60)
rows=[json.loads(line) for line in remote.stdout.splitlines() if line.strip()]
indexed={row['source']:row for row in rows}
assert len(indexed)==4,'Quatre chemins réels doivent avoir été mesurés.'
assert indexed['public']['transport_peer']==args.expected_proxy
assert indexed['public-forged']['transport_peer']==args.expected_proxy
assert indexed['public']['untrusted_forwarded_for']==indexed['public-forged']['untrusted_forwarded_for']
assert indexed['public']['untrusted_forwarded_for'] and '192.0.2.10' not in indexed['public']['untrusted_forwarded_for']
for kind in ('direct-loopback','direct-container'):
    assert indexed[kind]['transport_peer']!=args.expected_proxy
    assert indexed[kind]['untrusted_forwarded_for']==['192.0.2.10']
path=Path('.local/e2e/proxy.json');path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps({'completed':True,'expected_proxy':args.expected_proxy,'measurements':rows,'passed':4,'skipped':0},indent=2)+'\n')
print(json.dumps({'expected_proxy':args.expected_proxy,'peers':{key:row['transport_peer'] for key,row in indexed.items()},'passed':4,'skipped':0}))
