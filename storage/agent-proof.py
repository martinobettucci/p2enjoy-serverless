# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#réalisation-et-preuves
# @verifies docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#opérations-et-baux | docs/STORAGE_AGENT.md#santé-et-reprise
"""Real DEV agent protocol, FUSE and Docker proof. Root is the fault operator."""
import copy
import hashlib
import json
import os
from pathlib import Path
import pwd
import select
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parent
IMAGE='python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d'
UNIT='p2enjoy-storage-dev.service'
ACCOUNT=pwd.getpwnam('spark-docker')
REPORT=ROOT/('agent-limits-proof.json' if '--limits' in sys.argv else 'agent-proof.json')
RESULTS=[];FUNCTIONS=[];CONSUMERS=[];CONTAINERS=[]
REPORT.write_text(json.dumps({'completed':False,'state':'running','cleanup':False,'skipped':0})+'\n')
INSTALLATION=str(uuid4())
CONFIG={'data':{'enabled':True,'quota_mib':2},'cache':{'enabled':True,'quota_mib':2}}
CONFIG_NAMES=['SERVERLESS_STORAGE_ROOT_HOST','SERVERLESS_STORAGE_SOCKET_DIR_HOST']
RPC_CODE='''import socket,sys
s=socket.socket(socket.AF_UNIX);s.settimeout(60);s.connect(sys.argv[1]);s.sendall(sys.stdin.buffer.read());print(s.makefile('rb').readline(65537).decode(),end='')'''


def run(args,**kw):return subprocess.run(args,check=True,text=True,capture_output=True,timeout=90,**kw).stdout.strip()


def rpc(op=None,raw=None,denied=None,as_root=False,**fields):
    payload=raw if raw is not None else json.dumps({'op':op,**fields})+'\n'
    cmd=['/usr/bin/python3','-I','-c',RPC_CODE,str(SOCKET)]
    if not as_root:cmd=['runuser','-u',ACCOUNT.pw_name,'--',*cmd]
    response=json.loads(run(cmd,input=payload))
    if denied:
        assert response.get('ok') is False and response.get('error') in (denied if isinstance(denied,tuple) else (denied,)),response
        return response
    assert response.get('ok'),response
    return response['result']


def passed(name):
    RESULTS.append({'name':name,'status':'passed'});print('PASS '+name,flush=True)


def function(config=CONFIG):
    identifier=str(uuid4());FUNCTIONS.append(identifier)
    rpc('configure',function_id=identifier,configuration=config)
    return identifier


def acquire(identifier,config=CONFIG):
    consumer=str(uuid4());CONSUMERS.append(consumer)
    result=rpc('acquire',function_id=identifier,consumer_id=consumer,installation_id=INSTALLATION,configuration=config)
    return consumer,result


def release(consumer):
    result=rpc('release',consumer_id=consumer,installation_id=INSTALLATION)
    if consumer in CONSUMERS:CONSUMERS.remove(consumer)
    return result


def docker(mounts,code,background=False):
    name='storage-agent-proof-'+uuid4().hex;CONTAINERS.append(name)
    command=['runuser','-u',ACCOUNT.pw_name,'--','docker','--host','unix:///run/user/'+str(ACCOUNT.pw_uid)+'/docker.sock',
        'run','--name',name,'--network','none','--user','0:0','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--memory','128m','--pids-limit','32','--cpus','.25']
    for destination,source in mounts.items():command+=['--mount',f'type=bind,src={source},dst={destination}']
    command +=[IMAGE,'python','-I','-c',code]
    if background:return name,subprocess.Popen(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:return run(command)
    finally:remove(name)


def remove(name):
    command=['runuser','-u',ACCOUNT.pw_name,'--','docker','--host','unix:///run/user/'+str(ACCOUNT.pw_uid)+'/docker.sock']
    run(command+['rm','-f',name]);CONTAINERS.remove(name)


def living(mounts):
    name,process=docker(mounts,"import time;handle=open('/data/keep','rb');print('READY',flush=True);time.sleep(300)",background=True)
    readable,_,_=select.select([process.stdout],[],[],15)
    assert readable and process.stdout.readline().strip()=='READY'
    return name,process


def disconnected(name,process):
    code="from pathlib import Path;import errno\ntry:Path('/data/keep').read_bytes()\nexcept OSError as e:assert e.errno==errno.ENOTCONN,e;print('OK')\nelse:raise AssertionError('old bind still healthy')"
    command=['runuser','-u',ACCOUNT.pw_name,'--','docker','--host','unix:///run/user/'+str(ACCOUNT.pw_uid)+'/docker.sock']
    assert run(command+['inspect','--format','{{.State.Running}}',name])=='true'
    assert run(command+['exec',name,'python','-I','-c',code])=='OK'
    remove(name);process.communicate(timeout=10)
    absent=subprocess.run(command+['inspect',name],capture_output=True,text=True)
    assert absent.returncode!=0


def registry(query,args=()):
    with sqlite3.connect('file:'+str(STATE/'registry.sqlite3')+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        return [dict(row) for row in db.execute(query,args)]


def ready():
    until=time.monotonic()+20
    while time.monotonic()<until:
        try:
            result=rpc('health')
            if result['ready']:return result
        except (OSError,ValueError,subprocess.SubprocessError):pass
        time.sleep(.1)
    raise AssertionError('agent readiness deadline')


def main():
    assert os.getuid()==0 and Path('/etc/hostname').read_text().strip()=='infra-serverless'
    health=ready();assert health['healthy'] and health['leases']==0 and health['mounted_or_reserved']==0,health
    baseline=health['allocated_bytes']
    pid=int(run(['systemctl','show','-p','MainPID','--value',UNIT]))
    assert os.readlink(f'/proc/{pid}/ns/mnt')==os.readlink('/proc/1/ns/mnt')
    status=Path(f'/proc/{pid}/status').read_text()
    assert int(next(x for x in status.splitlines() if x.startswith('CapEff:')).split()[1],16)==1<<21
    assert SOCKET.stat().st_mode&0o777==0o600 and SOCKET.parent.stat().st_mode&0o777==0o700
    passed('private-socket-capability-and-host-mount-namespace')
    rpc('health',as_root=True,denied='peer_denied');passed('reject-root-peer-uid')
    for payload,code in [('{"op":"health","op":"health"}\n','duplicate_key'),('[]\n','invalid_request'),('{"op":"health","path":"/tmp"}\n','invalid_fields'),('{"op":"status","function_id":"../x"}\n','invalid_uuid'),('{"op":"health","x":NaN}\n','invalid_json')]:rpc(raw=payload,denied=code)
    passed('reject-malformed-and-unknown-protocol-fields')
    identifier=function();snap=rpc('status',function_id=identifier)
    assert snap['version']==1 and all(v['phase']=='unmounted' for v in snap['volumes'].values())
    assert rpc('configure',function_id=identifier,configuration=CONFIG)==snap
    rpc('configure',function_id=identifier,configuration=CONFIG,expected_version=0,denied='version_conflict')
    passed('atomic-configuration-idempotence-and-version')
    consumer,lease=acquire(identifier)
    assert rpc('acquire',function_id=identifier,consumer_id=consumer,installation_id=INSTALLATION,configuration=CONFIG)==lease
    assert rpc('check',consumer_id=consumer,installation_id=INSTALLATION)['healthy']
    rpc('release',consumer_id=consumer,installation_id=str(uuid4()),denied='lease_owner')
    rpc('acquire',function_id=identifier,consumer_id=consumer,installation_id=str(uuid4()),configuration=CONFIG,denied='lease_conflict')
    passed('durable-idempotent-lease-and-owner-refusals')
    changed=copy.deepcopy(CONFIG);changed['data']['quota_mib']=3
    rpc('configure',function_id=identifier,configuration=changed,denied='volume_busy')
    rpc('archive',function_id=identifier,denied='volume_busy')
    rpc('clear-cache',function_id=identifier,denied='volume_busy')
    passed('reject-mutations-under-live-lease')
    output=docker(lease['paths'],'''from pathlib import Path
import errno,os
Path('/data/keep').write_bytes(b'd'*131072)
Path('/cache/keep').write_bytes(b'cache')
try:Path('/data/too-big').write_bytes(b'x'*3145728)
except OSError as e:assert e.errno==errno.EDQUOT,e
else:raise AssertionError('quota not enforced')
Path('/data/too-big').unlink()
print('OK')''')
    assert output=='OK'
    measures=rpc('check',consumer_id=consumer,installation_id=INSTALLATION)['volumes']
    assert measures['data']['used']==135168 and measures['cache']['used']==8192,measures
    passed('docker-write-quota-and-logical-usage')
    consumer2,second=acquire(identifier);assert second['generations']==lease['generations']
    release(consumer);assert rpc('check',consumer_id=consumer2,installation_id=INSTALLATION)['healthy']
    release(consumer2);assert all(v['phase']=='unmounted' for v in rpc('status',function_id=identifier)['volumes'].values())
    consumer,third=acquire(identifier);assert third['generations']!=lease['generations']
    assert docker(third['paths'],"from pathlib import Path;assert Path('/data/keep').read_bytes()==b'd'*131072;assert Path('/cache/keep').read_bytes()==b'cache';print('OK')")=='OK'
    release(consumer);passed('shared-leases-last-release-and-persistence')
    disabled=copy.deepcopy(CONFIG);disabled['data']['enabled']=False;disabled['cache']['enabled']=False
    rpc('configure',function_id=identifier,configuration=disabled)
    assert rpc('health')['allocated_bytes']==baseline+4*1024**2
    rpc('configure',function_id=identifier,configuration=CONFIG)
    consumer,lease=acquire(identifier)
    assert docker(lease['paths'],"from pathlib import Path;assert Path('/data/keep').stat().st_size==131072;print('OK')")=='OK'
    release(consumer);passed('disable-retains-allocation-and-files')
    rpc('clear-cache',function_id=identifier)
    consumer,lease=acquire(identifier)
    assert docker(lease['paths'],"from pathlib import Path;assert Path('/data/keep').exists();assert list(Path('/cache').iterdir())==[];print('OK')")=='OK'
    release(consumer);passed('explicit-cache-clear-preserves-data')
    consumer,lease=acquire(identifier)
    docker(lease['paths'],"from pathlib import Path;Path('/data/large').write_bytes(b'a'*1200000);print('OK')")
    release(consumer)
    before=rpc('status',function_id=identifier)
    smaller=copy.deepcopy(CONFIG);smaller['data']['quota_mib']=1
    rpc('configure',function_id=identifier,configuration=smaller,denied='quota_below_usage')
    after=rpc('status',function_id=identifier)
    assert after['configuration']==before['configuration'] and after['version']==before['version'] and not after['pending']
    assert all(v['phase']=='unmounted' for v in after['volumes'].values())
    passed('second-volume-failure-compensates-first-candidate')
    consumer,lease=acquire(identifier)
    daemon=registry("SELECT daemon_pid FROM volumes WHERE function_id=? AND kind='data'",(identifier,))[0]['daemon_pid']
    os.kill(daemon,signal.SIGSTOP)
    started=time.monotonic();rpc('check',consumer_id=consumer,installation_id=INSTALLATION,denied=('probe_failed','mount_changed'))
    assert time.monotonic()-started<5
    assert not rpc('health')['healthy']
    assert registry("SELECT error FROM volumes WHERE function_id=? AND kind='data'",(identifier,))[0]['error']=='probe_failed'
    os.kill(daemon,signal.SIGCONT)
    rpc('check',consumer_id=consumer,installation_id=INSTALLATION,denied='mount_changed')
    release(consumer);passed('blocked-fuse-probe-bounded-and-degraded-until-drain')
    consumer,lease=acquire(identifier)
    daemon=registry("SELECT daemon_pid FROM volumes WHERE function_id=? AND kind='data'",(identifier,))[0]['daemon_pid']
    name,process=living(lease['paths'])
    os.kill(daemon,signal.SIGKILL)
    rpc('check',consumer_id=consumer,installation_id=INSTALLATION,denied=('mount_unavailable','mount_changed'))
    disconnected(name,process)
    release(consumer)
    consumer,renewed=acquire(identifier)
    assert renewed['generations']!=lease['generations']
    assert docker(renewed['paths'],"from pathlib import Path;assert Path('/data/large').stat().st_size==1200000;print('OK')")=='OK'
    release(consumer);passed('fuse-death-recovery-and-acknowledged-data')
    consumer,lease=acquire(identifier)
    name,process=living(lease['paths'])
    run(['systemctl','restart',UNIT]);ready()
    assert rpc('status',function_id=identifier)['leases']==1
    rpc('check',consumer_id=consumer,installation_id=INSTALLATION,denied='mount_changed')
    disconnected(name,process)
    release(consumer)
    consumer,lease=acquire(identifier)
    assert docker(lease['paths'],"from pathlib import Path;assert Path('/data/large').stat().st_size==1200000;print('OK')")=='OK'
    release(consumer);passed('service-restart-retains-leases-and-data')
    rpc('archive',function_id=identifier)
    rpc('acquire',function_id=identifier,consumer_id=str(uuid4()),installation_id=INSTALLATION,configuration=CONFIG,denied='function_archived')
    assert rpc('health')['allocated_bytes']==baseline+4*1024**2
    rpc('purge',function_id=identifier)
    assert rpc('status',function_id=identifier)['state']=='purged'
    rpc('configure',function_id=identifier,configuration=CONFIG,denied='function_archived')
    assert rpc('health')['allocated_bytes']==baseline
    passed('archive-purge-budget-and-tombstone')


def limits():
    health=ready();assert health['healthy'] and not health['leases'] and not health['allocated_bytes']
    agent_id=health['installation_id']
    rpc('quiesce',installation_id=str(uuid4()),denied='installation_conflict')
    assert rpc('quiesce',installation_id=agent_id)['quiesced']
    assert rpc('health')['quiesced']
    rpc('configure',function_id=str(uuid4()),configuration=CONFIG,denied='maintenance_active')
    assert rpc('leases',installation_id=INSTALLATION)=={'leases':[],'next':None}
    assert not rpc('resume',installation_id=agent_id)['quiesced']
    passed('atomic-maintenance-gate-and-readable-state')
    pid=int(run(['systemctl','show','-p','MainPID','--value',UNIT]))
    executable=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')[-2].decode()
    second=subprocess.run(['systemd-run','--quiet','--wait','--pipe','--collect','--uid='+ACCOUNT.pw_name,
        '--property=EnvironmentFile=/etc/spark/env','--property=EnvironmentFile=/run/spark/secrets',
        '/usr/bin/python3','-I','-B',executable],capture_output=True,text=True,timeout=20)
    assert second.returncode!=0 and 'storage_start_failed' in second.stderr,(second.stdout,second.stderr)
    assert int(run(['systemctl','show','-p','MainPID','--value',UNIT]))==pid and rpc('health')['healthy']
    passed('second-agent-refused-by-durable-root-lock')
    rpc(raw='x'*20000,denied='request_too_large')
    client='''import socket,sys,json,time
path=sys.argv[1]
def connect():
 s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(path);return s
sockets=[connect() for _ in range(16)]
time.sleep(.15)
extra=connect();assert extra.recv(1)==b'';extra.close()
for s in sockets:s.sendall(b'{"op":"health"}\\n')
for s in sockets:
 assert json.loads(s.makefile('rb').readline())['ok'];s.close()
slow=connect();start=time.monotonic();reply=json.loads(slow.makefile('rb').readline());assert reply=={'ok':False,'error':'read_timeout'};assert 2.5<time.monotonic()-start<4.5;slow.close()
print('OK')'''
    assert run(['runuser','-u',ACCOUNT.pw_name,'--','python3','-I','-c',client,str(SOCKET)])=='OK'
    passed('request-size-connection-limit-and-slow-client-deadline')
    single={'data':{'enabled':True,'quota_mib':1},'cache':{'enabled':False,'quota_mib':1}}
    identifier=function(single)
    consumer=str(uuid4());CONSUMERS.append(consumer)
    request={'op':'acquire','function_id':identifier,'consumer_id':consumer,'installation_id':INSTALLATION,'configuration':single}
    client="import socket,sys;s=socket.socket(socket.AF_UNIX);s.connect(sys.argv[1]);s.sendall(sys.argv[2].encode()+b'\\n');s.close()"
    run(['runuser','-u',ACCOUNT.pw_name,'--','python3','-I','-c',client,str(SOCKET),json.dumps(request)])
    until=time.monotonic()+10
    while time.monotonic()<until:
        snapshot=rpc('status',function_id=identifier)
        if snapshot['leases']==1 and snapshot['volumes']['data']['phase']=='mounted':break
        time.sleep(.05)
    assert snapshot['leases']==1 and snapshot['volumes']['data']['phase']=='mounted',snapshot
    lease=rpc(**request);assert lease['generations']['data']==snapshot['volumes']['data']['generation']
    rpc('quiesce',installation_id=agent_id,denied='maintenance_busy')
    for _ in range(50):acquire(identifier,single)
    page=rpc('leases',installation_id=INSTALLATION);assert len(page['leases'])==50 and page['next']
    tail=rpc('leases',installation_id=INSTALLATION,after=page['next']);assert len(tail['leases'])==1 and tail['next'] is None
    assert {x['consumer_id'] for x in page['leases']+tail['leases']}==set(CONSUMERS)
    for consumer in tuple(CONSUMERS):release(consumer)
    passed('lost-acquire-response-idempotence-and-lease-pagination')
    rpc('archive',function_id=identifier);rpc('purge',function_id=identifier)
    capacity=rpc('health')['budget_bytes']//1024**2
    big={'data':{'enabled':True,'quota_mib':capacity-1},'cache':{'enabled':True,'quota_mib':1}}
    identifier=function(big)
    transfer=copy.deepcopy(big);transfer['data']['quota_mib']-=1;transfer['cache']['quota_mib']+=1
    rpc('configure',function_id=identifier,configuration=transfer,denied='storage_budget')
    assert rpc('status',function_id=identifier)['configuration']==big
    disabled=copy.deepcopy(big);disabled['data']['enabled']=False;disabled['cache']['enabled']=False
    rpc('configure',function_id=identifier,configuration=disabled)
    assert rpc('health')['allocated_bytes']==capacity*1024**2
    rpc('archive',function_id=identifier)
    refused=str(uuid4());FUNCTIONS.append(refused)
    rpc('configure',function_id=refused,configuration=single,denied='storage_budget')
    assert rpc('health')['allocated_bytes']==capacity*1024**2
    rpc('purge',function_id=identifier)
    rpc('configure',function_id=refused,configuration=single)
    rpc('archive',function_id=refused);rpc('purge',function_id=refused)
    passed('global-budget-disabled-archives-and-temporary-increase')
    created=[];leases=[]
    maximum=rpc('health')['max_mounts']
    for _ in range(maximum):
        identifier=function(single);created.append(identifier)
        consumer,_=acquire(identifier,single);leases.append(consumer)
    assert rpc('health')['mounted_or_reserved']==maximum
    # Configuration itself needs a real candidate slot and must compensate on refusal.
    refused=str(uuid4());FUNCTIONS.append(refused)
    rpc('configure',function_id=refused,configuration=single,denied='mount_limit')
    assert not rpc('status',function_id=refused)['pending'] and rpc('status',function_id=refused)['leases']==0
    release(leases.pop())
    rpc('configure',function_id=refused,configuration=single)
    consumer,_=acquire(refused,single);leases.append(consumer);created.append(refused)
    assert rpc('health')['mounted_or_reserved']==maximum
    for consumer in leases:release(consumer)
    for identifier in created:rpc('archive',function_id=identifier);rpc('purge',function_id=identifier)
    passed('real-mount-limit-reservations-compensation-and-reuse')
    identifier=function(single)
    target=STATE/'mounts'/identifier/'data'
    run(['mount','-t','tmpfs','-o',f'size=1m,mode=700,uid={ACCOUNT.pw_uid},gid={ACCOUNT.pw_gid}','storage-proof-foreign',str(target)])
    try:
        (target/'foreign').write_text('preserve')
        rpc('acquire',function_id=identifier,consumer_id=str(uuid4()),installation_id=INSTALLATION,configuration=single,denied='foreign_mount')
        assert (target/'foreign').read_text()=='preserve'
        run(['systemctl','restart',UNIT]);ready()
        assert (target/'foreign').read_text()=='preserve'
        assert any(str(target) in line and 'storage-proof-foreign' in line for line in Path('/proc/self/mountinfo').read_text().splitlines())
    finally:run(['umount',str(target)])
    until=time.monotonic()+10
    while time.monotonic()<until and not rpc('health')['healthy']:time.sleep(.1)
    consumer,lease=acquire(identifier,single);release(consumer)
    rpc('archive',function_id=identifier);rpc('purge',function_id=identifier)
    passed('foreign-mount-refused-and-preserved-across-restart')
    wide={'data':{'enabled':True,'quota_mib':32},'cache':{'enabled':True,'quota_mib':32}}
    identifier=function(wide);consumer,lease=acquire(identifier,wide)
    docker(lease['paths'],"from pathlib import Path;import os;[(Path('/cache')/str(i)).mkdir() for i in range(4200)];os.chmod('/cache',0);Path('/data/keep').write_text('preserve');print('OK')")
    release(consumer)
    rpc('clear-cache',function_id=identifier)
    consumer,lease=acquire(identifier,wide)
    assert docker(lease['paths'],"from pathlib import Path;assert list(Path('/cache').iterdir())==[];assert Path('/data/keep').read_text()=='preserve';print('OK')")=='OK'
    release(consumer)
    reduced=copy.deepcopy(wide);reduced['data']['quota_mib']=1;reduced['cache']['quota_mib']=1
    rpc('configure',function_id=identifier,configuration=reduced)
    consumer,lease=acquire(identifier,reduced)
    assert rpc('check',consumer_id=consumer,installation_id=INSTALLATION)['volumes']['data']['quota']==1024**2
    release(consumer)
    rpc('configure',function_id=identifier,configuration=wide)
    consumer,lease=acquire(identifier,wide)
    assert rpc('check',consumer_id=consumer,installation_id=INSTALLATION)['volumes']['data']['quota']==32*1024**2
    docker(lease['paths'],"import os;os.chmod('/data',0);os.chmod('/cache',0);print('OK')")
    release(consumer);rpc('archive',function_id=identifier);rpc('purge',function_id=identifier)
    assert not (STATE/'backings'/identifier).exists() and not (STATE/'mounts'/identifier).exists()
    passed('wide-tree-and-chmod-zero-cleanup-resize-and-purge')


config=json.loads(run(['systemd-run','--quiet','--wait','--pipe','--collect','--property=EnvironmentFile=/etc/spark/env',
    '--property=EnvironmentFile=/run/spark/secrets','/usr/bin/python3','-I','-c','import json,os;print(json.dumps({n:os.environ[n] for n in '+repr(CONFIG_NAMES)+'}))']))
STATE=Path(config[CONFIG_NAMES[0]]);SOCKET=Path(config[CONFIG_NAMES[1]])/'agent.sock'
error=None;cleanup=False
try:
    if '--limits' in sys.argv:limits()
    else:main()
except BaseException as failure:
    error=type(failure).__name__+': '+str(failure);print(error,file=sys.stderr,flush=True)
finally:
    try:
        for name in tuple(CONTAINERS):remove(name)
        for row in registry('SELECT daemon_pid FROM volumes WHERE daemon_pid IS NOT NULL'):
            try:os.kill(row['daemon_pid'],signal.SIGCONT)
            except ProcessLookupError:pass
        for consumer in tuple(CONSUMERS):release(consumer)
        for identifier in FUNCTIONS:
            row=rpc('status',function_id=identifier)
            if row['state']=='active':rpc('archive',function_id=identifier)
            if row['state']!='purged':rpc('purge',function_id=identifier)
        cleanup=not CONSUMERS and not CONTAINERS and rpc('health')['leases']==0 and rpc('health')['mounted_or_reserved']==0
    except BaseException as failure:
        error=(error or '')+'; cleanup: '+type(failure).__name__+': '+str(failure)
    report={'completed':error is None and cleanup,'passed':len(RESULTS),'failed':int(error is not None),'skipped':0,'cleanup':cleanup,
        'error':error,'results':RESULTS,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if error or not cleanup:raise SystemExit(1)
