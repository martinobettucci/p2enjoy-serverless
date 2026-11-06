# @spec docs/BACKLOG.md#sls-010 | docs/PLATFORM.md#stockage
# @verifies docs/BACKLOG.md#sls-010 | docs/PLATFORM.md#stockage
# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#registre-et-chemins
# @verifies docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#registre-et-chemins
# Serial real FUSE/Docker proof, run only by the principal on the DEV Spark.
import hashlib
import ctypes
import json
import os
from pathlib import Path
import shutil
import signal
import select
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parent
IMAGE='python:3.14-slim@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d'
LIMIT=1024*1024
RESULTS=[]


def unmount(path):
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.umount2(os.fsencode(path),0)!=0:
        error=ctypes.get_errno()
        raise OSError(error,os.strerror(error))


def mounted(path):
    return any(f' {path} ' in line and ' - fuse.p2quota ' in line for line in Path('/proc/self/mountinfo').read_text().splitlines())


def launch(backing,mount,log):
    p=subprocess.Popen([str(ROOT/'p2-quota'),'-direct','-backing',str(backing),'-mount',str(mount),'-bytes',str(LIMIT)],stdout=log,stderr=log)
    deadline=time.monotonic()+10
    while p.poll() is None and not mounted(mount) and time.monotonic()<deadline:
        time.sleep(.02)
    if not mounted(mount):
        if p.poll() is None: p.terminate();p.wait(10)
        raise RuntimeError('FUSE mount failed; see daemon log')
    return p


def stop(p):
    if p.poll() is None:
        p.terminate();p.wait(10)
    assert p.returncode==0,p.returncode


def client_command(a,b):
    args=['docker','--host',f'unix:///run/user/{os.getuid()}/docker.sock','run','--rm','--network','none','--user','0:0','--read-only',
          '--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m',
          '--pids-limit','32','--cpus','.25',
          '--mount',f'type=bind,src={ROOT}/client.py,dst=/client.py,readonly',
          '--mount',f'type=bind,src={a},dst=/data-a',
          '--mount',f'type=bind,src={b},dst=/data-b',IMAGE,'python','/client.py']
    return args


def client(a,b,mode=None):
    args=client_command(a,b)
    if mode: args.append(mode)
    r=subprocess.run(args,capture_output=True,text=True,timeout=100)
    try: data=json.loads(r.stdout)
    except json.JSONDecodeError: raise RuntimeError(f'client transport: {r.stderr[:1000]} {r.stdout[:500]}')
    if isinstance(data,list): RESULTS.extend(data)
    else: RESULTS.append(data)
    if r.returncode: print('client failed',json.dumps(data),r.stderr[:1000],flush=True)


def crash_client(a,b,daemon):
    args=client_command(a,b)
    args.insert(args.index('--rm'),'-i')
    p=subprocess.Popen(args+['unavailable'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        ready,_,_=select.select([p.stdout],[],[],15)
        assert ready and p.stdout.readline().strip()=='READY','crash consumer failed to start'
        daemon.kill();daemon.wait(10)
        out,err=p.communicate('CHECK\n',timeout=15)
        assert p.returncode==0,(out,err)
        RESULTS.append(json.loads(out))
        # A new consumer must not silently bind the underlying empty directory.
        denied=subprocess.run(client_command(a,b)+['persist-read'],capture_output=True,text=True,timeout=15)
        assert denied.returncode!=0 and 'transport endpoint is not connected' in denied.stderr,denied.stderr
        RESULTS.append({'name':'new-container-rejects-disconnected-mount','status':'passed'})
    finally:
        if p.poll() is None:p.kill();p.wait(10)


def rejected(backing,mount,label,expected,limit=LIMIT):
    r=subprocess.run([str(ROOT/'p2-quota'),'-direct','-backing',str(backing),'-mount',str(mount),'-bytes',str(limit)],capture_output=True,text=True,timeout=10)
    assert r.returncode!=0 and expected in r.stderr,(label,r.stdout,r.stderr)
    RESULTS.append({'name':label,'status':'passed','detail':r.stderr.strip()})


work=Path(tempfile.mkdtemp(prefix='quota-proof-',dir=ROOT))
processes=[]
logs=[]
try:
    a,b=work/'mount-a',work/'mount-b'
    ba,bb=work/'backing-a',work/'backing-b'
    extra=work/'extra-mount'
    for p in (a,b,ba,bb,extra):p.mkdir(mode=0o700)
    for label,name in [('empty',''),('spaces','bad name'),('too-long','a'*129)]:
        result=subprocess.run([str(ROOT/'p2-quota'),'-direct','-backing',str(ba),'-mount',str(a),'-bytes',str(LIMIT),'-name',name],capture_output=True,text=True,timeout=10)
        assert result.returncode!=0 and 'invalid mount name' in result.stderr
        RESULTS.append({'name':'reject-mount-name-'+label,'status':'passed'})
    logs=[(work/'a.log').open('w'),(work/'b.log').open('w')]
    pa=launch(ba,a,logs[0]);processes.append(pa)
    pb=launch(bb,b,logs[1]);processes.append(pb)
    rejected(ba,extra,'exclusive-backing-lock','volume already owned')
    client(a,b)
    client(a,b,'persist-write')
    stop(pa)
    pa=launch(ba,a,logs[0]);processes.append(pa)
    client(a,b,'persist-read')
    client(a,b,'persist-write')
    crash_client(a,b,pa)
    unmount(a)
    pa=launch(ba,a,logs[0]);processes.append(pa)
    client(a,b,'persist-read')
    stop(pa);stop(pb)
    (ba/'oversize').write_bytes(b'x'*8192)
    rejected(ba,a,'refuse-limit-below-usage','quota smaller than existing usage',4096)
    (ba/'oversize').unlink()
    os.symlink('/etc/passwd',ba/'symlink')
    rejected(ba,a,'refuse-preexisting-symlink','unsupported link, type or nested filesystem')
    (ba/'symlink').unlink()
    (ba/'regular').write_bytes(b'x')
    os.link(ba/'regular',ba/'hard')
    rejected(ba,a,'refuse-preexisting-hardlink','unsupported link, type or nested filesystem')
    (ba/'hard').unlink();(ba/'regular').unlink()
    os.mkfifo(ba/'pipe')
    rejected(ba,a,'refuse-preexisting-special-file','unsupported link, type or nested filesystem')
    (ba/'pipe').unlink()
    rejected(ba,ba,'refuse-overlapping-paths','backing and mount must be separate trees')
    rejected(ba,a,'refuse-zero-quota','backing, mount and bytes',0)
    rejected(ba,a,'refuse-oversized-quota','backing, mount and bytes',(1<<50)+1)
    (extra/'sentinel').write_bytes(b'preserve me')
    rejected(ba,extra,'refuse-nonempty-mount','mount must be empty')
    assert (extra/'sentinel').read_bytes()==b'preserve me'
except Exception as exc:
    RESULTS.append({'name':'orchestration','status':'failed','error':str(exc)})
finally:
    for p in processes:
        if p.poll() is None:
            p.terminate()
            try:p.wait(10)
            except subprocess.TimeoutExpired:p.kill();p.wait(10)
    for path in (work/'mount-a',work/'mount-b',work/'extra-mount'):
        if mounted(path):
            try:unmount(path)
            except OSError as exc:RESULTS.append({'name':'cleanup-mount','status':'failed','error':str(exc)})
    for f in logs:f.close()
    report={'results':RESULTS,'failed':sum(r['status']!='passed' for r in RESULTS),'skipped':0,
            'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('main.go','Dockerfile','go.mod','go.sum','client.py','prove.py')},
            'binary_sha256':hashlib.sha256((ROOT/'p2-quota').read_bytes()).hexdigest(),
            'client_image':IMAGE,'daemon_logs':{p.name:p.read_text() for p in work.glob('*.log')}}
    (ROOT/'proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    # Never remove a path still mounted or touch anything outside this proof.
    if any(mounted(p) for p in (work/'mount-a',work/'mount-b',work/'extra-mount')):
        raise RuntimeError('mount remains: manual proof cleanup required')
    shutil.rmtree(work)
if report['failed']:raise SystemExit(1)
