#!/usr/bin/env python3
# @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
# @verifies docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
"""Real Docker/HTTP lifecycle and fault campaign, executed only on the DEV Spark."""
import concurrent.futures
import hashlib
import json
import pathlib
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPOSE = ['docker', 'compose', '-f', 'compose.dev.yml', '-f', 'compose.spark.yml', '--profile', 'dev']
IMAGE = 'p2enjoy-qualification:dev'
BASE = 'http://127.0.0.1:18080'
results = []

def command(args, check=True, timeout=30, data=None):
    r = subprocess.run(args, cwd=ROOT, input=data, text=True, capture_output=True, timeout=timeout)
    if check and r.returncode:
        raise AssertionError('Command failed: ' + ' '.join(args[:5]) + '\n' + r.stderr[-1500:])
    return r

def passed(name):
    results.append(name)
    print(json.dumps({'passed': name}), flush=True)

def request(route, method='GET', value=None, base=BASE, headers=None):
    data = None if value is None else json.dumps(value).encode()
    req = urllib.request.Request(base+route, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status, json.loads(r.read() or b'null'), dict(r.headers)
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null'), dict(e.headers)

def until(predicate, label, seconds=12):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            if predicate(): return
        except (urllib.error.URLError, ConnectionError, TimeoutError): pass
        time.sleep(.03)
    raise AssertionError('Timed out: '+label)

def app_id(): return command(COMPOSE+['ps','-q','qualification']).stdout.strip()

def inspect(cid): return json.loads(command(['docker','inspect',cid]).stdout)[0]

def no_children(cid):
    rows=command(['docker','top',cid,'-eo','pid,args']).stdout
    assert 'runner/child.cjs' not in rows, rows


def lifecycle():
    cid=app_id(); assert cid
    metadata=inspect(cid)
    assert metadata['State']['Health']['Status']=='healthy'
    assert metadata['Config']['User']=='node'
    assert metadata['HostConfig']['ReadonlyRootfs'] is True
    assert metadata['HostConfig']['Memory']==384*1024*1024
    assert metadata['HostConfig']['PidsLimit']==96
    assert metadata['HostConfig']['NanoCpus']==500000000
    assert metadata['HostConfig']['CapDrop']==['ALL']
    assert metadata['HostConfig']['PortBindings']['8080/tcp']==[{'HostIp':'127.0.0.1','HostPort':'18080'}]
    assert request('/healthz')[0]==200
    with socket.socket() as s:
        s.settimeout(1)
        assert s.connect_ex(('10.77.0.24',18080))!=0, 'service must not be exposed on Spark address'
    read_only=command(['docker','exec',cid,'node','-e',"try{require('fs').writeFileSync('/app/forbidden','x');process.exit(1)}catch(e){process.exit(e.code==='EROFS'?0:2)}"])
    assert read_only.returncode==0
    limits=json.loads(command(['docker','exec',cid,'node','-e',"const f=require('fs');console.log(JSON.stringify(['memory.max','cpu.max','pids.max'].map(n=>f.readFileSync('/sys/fs/cgroup/'+n,'utf8').trim())))"]).stdout)
    assert limits[0]==str(384*1024*1024) and limits[2]=='96'
    quota,period=map(int,limits[1].split()); assert quota/period==.5
    passed('non-root, read-only filesystem, actual cgroups and loopback-only HTTP')

    since=command(['date','-u','+%Y-%m-%dT%H:%M:%S.%NZ']).stdout.strip()
    expected={}
    cases=[('echo','POST',{'private':'must-not-appear-in-log'}),('callback','POST',{}),('failure','POST',{'kind':'throw'}),('failure','POST',{'kind':'exit'}),('spin','POST',{}),('configuration','GET',None)]
    # Secrets are read inside the app container solely to exercise its real auth.
    auth=command(['docker','exec',cid,'node','-e',"fetch('http://127.0.0.1:8080/functions/business',{method:'POST',headers:{authorization:'Bearer '+process.env.QUALIFICATION_BUSINESS_TOKEN}}).then(async r=>console.log(JSON.stringify({status:r.status,id:r.headers.get('x-qualification-request-id')})))"]).stdout
    auth=json.loads(auth);assert auth['status']==200;expected[auth['id']]=('business',200)
    for name,method,value in cases:
        status,body,headers=request('/functions/'+name,method,value)
        rid=next(v for k,v in headers.items() if k.lower()=='x-qualification-request-id')
        expected[rid]=(name,status)
        no_children(cid)
    log_result=command(['docker','logs','--since',since,cid]);logs=log_result.stdout+log_result.stderr
    records=[]
    for line in logs.splitlines():
        try: records.append(json.loads(line))
        except json.JSONDecodeError: pass
    for rid,(name,status) in expected.items():
        matches=[r for r in records if r.get('requestId')==rid]
        assert len(matches)==1 and matches[0]['function']==name and matches[0]['statusCode']==status
        assert matches[0]['durationMs']>=0 and matches[0]['handlerStarted'] is True
    assert 'must-not-appear-in-log' not in logs and 'Bearer ' not in logs
    # Comparison happens in container memory; no secret is printed or written.
    check_logs="let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>{for(const k of ['QUALIFICATION_BUSINESS_TOKEN','QUALIFICATION_SYNTHETIC_SECRET'])if(!process.env[k]||s.includes(process.env[k]))process.exit(1)})"
    command(['docker','exec','-i',cid,'node','-e',check_logs],data=logs)
    passed('real Docker logs correlated once per invocation without secret or body leakage; no surviving child')

    stop_since=command(['date','-u','+%Y-%m-%dT%H:%M:%S.%NZ']).stdout.strip()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        active=pool.submit(request,'/functions/sleep','POST',{'milliseconds':5000})
        until(lambda:request('/healthz')[1]['activeInvocations']==1,'active invocation')
        queued=pool.submit(request,'/functions/sleep','POST',{'milliseconds':0})
        until(lambda:request('/healthz')[1]['pendingRequests']==2,'queued invocation')
        started=time.monotonic()
        command(COMPOSE+['stop','--timeout','5','qualification'],timeout=12)
        assert time.monotonic()-started<6
        stopped=inspect(cid);assert stopped['State']['Status']=='exited' and stopped['State']['ExitCode']==0
        for future in (active,queued):
            try:
                status,body,_=future.result(timeout=3)
                assert (status,body['error']) in [(500,'handler_exit'),(503,'runner_stopping')]
                if future is queued: assert (status,body['error'])==(503,'runner_stopping')
            except (urllib.error.URLError,ConnectionError,TimeoutError): pass
        stop_log=command(['docker','logs','--since',stop_since,cid]).stdout
        sleeps=[json.loads(line) for line in stop_log.splitlines() if line.startswith('{') and json.loads(line).get('function')=='sleep']
        assert len(sleeps)==1, 'Queued invocation started during shutdown'
    command(COMPOSE+['up','-d','--wait','--wait-timeout','60','qualification'],timeout=70)
    assert request('/functions/echo')[0]==200; no_children(app_id())
    passed('actual SIGTERM with active and queued requests, bounded clean stop and healthy restart')


def fault_campaign():
    manifest=(ROOT/'serverless.yml').read_text()
    invalid={
      'YAML aliases': manifest+'\na: &a [1]\nb: *a\n',
      'invalid YAML': manifest+'\nbroken: [\n',
      'duplicate YAML key':manifest+'\nservice: duplicate\n',
      'invalid service':manifest.replace('service: p2enjoy-qualification','service: invalid'),
      'invalid provider':manifest.replace('name: p2enjoy','name: invalid',1),
      'invalid runtime':manifest.replace('nodejs24.x','unsupported'),
      'invalid function name':manifest.replace('  echo:\n','  ECHO:\n',1),
      'unknown field':manifest.replace('    timeout: 2','    unknown: true\n    timeout: 2',1),
      'invalid handler path':manifest.replace('src/handlers.echo','../escape.echo',1),
      'timeout below minimum':manifest.replace('    timeout: 2','    timeout: 0',1),
      'timeout above maximum':manifest.replace('    timeout: 2','    timeout: 6',1),
      'invalid memory':manifest.replace('memorySize: 128','memorySize: 1024',1),
      'event mismatch':manifest.replace('path: echo','path: other',1),
      'unsupported event method':manifest.replace('method: any','method: delete',1),
      'unknown extension':manifest.replace('functionId: qlf-state-v1','unknown: true, functionId: qlf-state-v1',1),
      'invalid storage':manifest.replace('storage: data','storage: unsafe',1),
      'invalid ID':manifest.replace('qlf-state-v1','../escape',1),
      'duplicate ID':manifest.replace('qlf-worker-v1','qlf-state-v1',1),
      'forbidden environment':manifest.replace('[QUALIFICATION_BUSINESS_TOKEN]','[PATH]',1),
      'non-array environment':manifest.replace('[QUALIFICATION_BUSINESS_TOKEN]','QUALIFICATION_BUSINESS_TOKEN',1),
      'missing functions': 'service: p2enjoy-qualification\nprovider: {name: p2enjoy, runtime: nodejs24.x}\n',
    }
    local=ROOT/'.local';local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='faults-',dir=local) as directory:
        p=pathlib.Path(directory)/'serverless.yml'
        name='p2enjoy-qualification-fault-'+uuid.uuid4().hex[:8]
        common=['docker','run','--name',name,'--read-only','--memory','384m','--cpus','.5','--pids-limit','96',
                '--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '--env-file','/etc/spark/env','--env-file','/run/spark/secrets',
                '--tmpfs','/app/.state/data:uid=1000,gid=1000,mode=0700',
                '--tmpfs','/app/.state/cache:uid=1000,gid=1000,mode=0700',
                '--mount',f'type=bind,src={p},dst=/app/serverless.yml,readonly']
        for label,text in invalid.items():
            p.write_text(text);p.chmod(0o644)
            try:
                r=command(common+['--rm',IMAGE],check=False,timeout=8)
                assert r.returncode==1 and 'Error' in r.stderr and '/app/' in r.stderr,'No genuine Node validation failure: '+label
            finally: command(['docker','rm','-f',name],check=False)
            passed('real container startup rejects '+label)
        # Same image with a genuinely absent per-function environment declaration.
        p.write_text(manifest.replace('[QUALIFICATION_BUSINESS_TOKEN]','[]').replace('[QUALIFICATION_PUBLIC_LABEL, QUALIFICATION_SYNTHETIC_SECRET]','[]'))
        try:
            cid=command(common+['-d','-p','127.0.0.1::8080',IMAGE]).stdout.strip()
            port=inspect(cid)['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort'];base='http://127.0.0.1:'+port
            until(lambda:request('/healthz',base=base)[0]==200,'isolated absent configuration')
            assert request('/functions/configuration',base=base)[1]=={'label':'qualification','secretPresent':False}
            s,b,_=request('/functions/business','POST',{},base=base);assert s==503 and b['error']=='business_auth_unconfigured'
            passed('actual deployment with absent function configuration fails closed and uses documented default')
        finally: command(['docker','rm','-f',name],check=False)
        # Same application image, real handler resolution, ephemeral data and real HTTP.
        p.write_text(manifest.replace('src/handlers.callback','src/handlers.missing',1))
        try:
            cid=command(common+['-d','-p','127.0.0.1::8080',IMAGE]).stdout.strip()
            port=inspect(cid)['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort'];base='http://127.0.0.1:'+port
            until(lambda: request('/healthz',base=base)[0]==200,'isolated real runner')
            s,b,h=request('/functions/callback','POST',{},base=base);assert s==500 and b['error']=='handler_error'
            assert next(v for k,v in h.items() if k.lower()=='x-qualification-handler-started')=='false'
            passed('missing real export fails before handler entry')
            seed="const f=require('fs');f.mkdirSync('/app/.state/data/qlf-state-v1',{recursive:true});f.writeFileSync('/app/.state/data/qlf-state-v1/counter.limit.json',JSON.stringify({count:Number.MAX_SAFE_INTEGER}));f.writeFileSync('/app/.state/data/qlf-state-v1/counter.corrupt.json','{');f.writeFileSync('/app/.state/data/qlf-state-v1/counter.unreadable.json','{}',{mode:0});"
            command(['docker','exec',cid,'node','-e',seed])
            s,b,_=request('/functions/state?key=limit','POST',{'increment':1},base=base);assert s==409 and b['error']=='counter_limit'
            for key in ['corrupt','unreadable']:
                s,b,_=request('/functions/state?key='+key,base=base);assert s==500 and b['error']=='handler_error'
            command(['docker','exec',cid,'node','-e',"require('fs').chmodSync('/app/.state/data/qlf-state-v1',0o500)"])
            s,b,_=request('/functions/state?key=readonly','POST',{'increment':1},base=base);assert s==500 and b['error']=='handler_error'
            assert request('/functions/echo',base=base)[0]==200
            command(['docker','update','--pids-limit','1',cid])
            try:
                s,b,_=request('/functions/echo',base=base);assert s==500 and b['error']=='spawn_error', (s,b)
            finally:command(['docker','update','--pids-limit','96',cid])
            assert request('/functions/echo',base=base)[0]==200
            passed('real cgroup process exhaustion refuses fork and recovers after restoring capacity')
            passed('real isolated storage refuses counter overflow, corrupt JSON, unreadable file and denied write')
        finally: command(['docker','rm','-f',name],check=False)

try:
    lifecycle()
    fault_campaign()
finally:
    # Leave only the authorized development app running, even after a failed assertion.
    command(COMPOSE+['up','-d','--wait','--wait-timeout','60','qualification'],timeout=70)
    assert request('/healthz')[0]==200
print(json.dumps({'operations':'passed','cases':len(results),'checks':results}))
