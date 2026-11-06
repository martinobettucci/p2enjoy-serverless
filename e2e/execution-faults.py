# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#reprise-et-observations
# @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#reprise-et-observations
"""Bounded operator observations/faults for one API-created invocation campaign."""
import fcntl,json,os,re,select,shlex,signal,socket,sqlite3,subprocess,sys,time
from contextlib import closing
from pathlib import Path
from uuid import UUID,uuid4
from control_database import read_control,ControlWriter

assert os.geteuid()==0 and socket.gethostname()=='infra-serverless','dev_spark_required'
mode,function=sys.argv[1:3];assert str(UUID(function))==function
values={}
for line in Path('/etc/spark/env').read_text().splitlines():
    parts=shlex.split(line,comments=True)
    if len(parts)==1 and '=' in parts[0]:
        key,value=parts[0].split('=',1)
        if key in ('SERVERLESS_STATE_HOST_PATH','SERVERLESS_DOCKER_SOCKET_HOST','SERVERLESS_STORAGE_ROOT_HOST'):values[key]=value
state=Path(values['SERVERLESS_STATE_HOST_PATH'])
def connect():
    return read_control(state/'control.sqlite3',timeout=.2)
def docker(*args):
    return subprocess.check_output(['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST'],*args],text=True,timeout=30)
def emit(value):print(json.dumps(value),flush=True)
with connect() as db:
    fn=db.execute('SELECT f.id,f.service_id,f.deleted_at,n.name FROM functions f JOIN services s ON s.id=f.service_id JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=?',(function,)).fetchone()
    assert fn and re.fullmatch(r'invocation-[0-9a-f]{8}',fn['name']),'owned_campaign_required'
    installation=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]

def inspect(target=function):
    with connect() as db:
        rows=[dict(row) for row in db.execute('SELECT id,revision_id,state,cpu_nanos,memory_mib FROM execution_instances WHERE function_id=?',(target,))]
        invocations=[dict(row) for row in db.execute('SELECT id,state,instance_id,handler_started,error_code FROM invocations WHERE function_id=? ORDER BY created_at DESC,id DESC LIMIT 100',(target,))]
        active=db.execute("SELECT count(*) FROM invocations WHERE function_id=? AND state IN ('receiving','queued','admitted','running')",(target,)).fetchone()[0]
        reserved={row[0] for row in db.execute('SELECT id FROM execution_instances')}
        global_reservations=dict(db.execute('SELECT count(*) AS instances,coalesce(sum(cpu_nanos),0) AS cpu_nanos,coalesce(sum(memory_mib),0) AS memory_mib FROM execution_instances').fetchone())
        orphan_channels=sum(path.name not in reserved for path in (state/'execution').iterdir())
    with closing(sqlite3.connect('file:'+str(Path(values['SERVERLESS_STORAGE_ROOT_HOST'])/'registry.sqlite3')+'?mode=ro',uri=True)) as db:
        leases=[{'consumer_id':row[0],'complete':bool(json.loads(row[1]))} for row in db.execute('SELECT consumer_id,mounts_json FROM leases WHERE installation_id=? AND function_id=?',(installation,target))]
    containers=[]
    for key in docker('ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation,'--filter','label=tech.p2enjoy.serverless.kind=instance','--filter','label=tech.p2enjoy.serverless.function='+target).split():
        item=json.loads(docker('inspect',key))[0];labels=item['Config']['Labels'];host=item['HostConfig']
        assert labels['tech.p2enjoy.serverless.installation']==installation and labels['tech.p2enjoy.serverless.function']==target
        containers.append({'id':key,'instance_id':labels['tech.p2enjoy.serverless.instance'],'running':item['State']['Running'],
                           'cpu_nanos':host['NanoCpus'],'memory_bytes':host['Memory'],'memory_swap_bytes':host['MemorySwap'],'pids_limit':host['PidsLimit'],
                           'readonly_root':host['ReadonlyRootfs'],'cap_drop':host['CapDrop'],'security_opt':host['SecurityOpt']})
    networks=[]
    for key in docker('network','ls','-q','--filter','label=tech.p2enjoy.serverless.installation='+installation,'--filter','label=tech.p2enjoy.serverless.kind=instance-network','--filter','label=tech.p2enjoy.serverless.function='+target).split():
        item=json.loads(docker('network','inspect',key))[0];labels=item['Labels']
        assert labels['tech.p2enjoy.serverless.installation']==installation and labels['tech.p2enjoy.serverless.function']==target
        networks.append(item['Id'])
    return {'instances':rows,'invocations':invocations,'containers':containers,'networks':networks,'leases':leases,'active_invocations':active,
            'global_reservations':global_reservations,'reserved_channel_count':sum((state/'execution'/row['id']).exists() for row in rows),'unreferenced_channel_count':orphan_channels}

def restart_guard():
    unit='serverless-restore-control-'+uuid4().hex
    subprocess.run(['systemd-run','--quiet','--collect','--unit='+unit,'--on-active=45s','--timer-property=AccuracySec=100ms',
        '/usr/sbin/runuser','-u','spark-docker','--','/usr/bin/docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST'],'start','serverless-api'],check=True,timeout=15)
    return unit

if mode=='inspect':emit(inspect())
elif mode=='rejection-evidence':
    identifiers=sys.argv[3:];assert 1<=len(identifiers)<=10 and all(str(UUID(key))==key for key in identifiers)
    with connect() as db:
        observations=[]
        for key in identifiers:
            row=db.execute('SELECT id,state,handler_started FROM invocations WHERE id=? AND function_id=?',(key,function)).fetchone();assert row
            observations.append(dict(row))
    logs=subprocess.run(['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST'],'logs','--tail','1000','serverless-api'],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True,timeout=15).stdout
    events=[]
    for line in logs.splitlines():
        if not line.startswith('{'):continue
        try:row=json.loads(line)
        except ValueError:continue
        if row.get('event')=='execution.rejection_pending' and row.get('invocation_id') in identifiers:
            events.append({key:row[key] for key in ('event','invocation_id','state','error_code','http_status')})
    emit({'invocations':observations,'events':events})
elif mode=='finalization-evidence':
    identifier=sys.argv[3];assert str(UUID(identifier))==identifier
    with connect() as db:
        invocation=db.execute('SELECT state,handler_started FROM invocations WHERE id=? AND function_id=?',(identifier,function)).fetchone();assert invocation
    logs=subprocess.run(['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST'],'logs','--tail','1000','serverless-api'],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True,timeout=15).stdout
    events=[]
    for line in logs.splitlines():
        if not line.startswith('{'):continue
        try:row=json.loads(line)
        except ValueError:continue
        if row.get('event')=='execution.finalization_pending' and row.get('invocation_id')==identifier:
            events.append({key:row[key] for key in ('event','invocation_id','result_state')})
    emit({'invocation_id':identifier,'state':invocation['state'],'handler_started':bool(invocation['handler_started']),'pending_result_observed':any(row['result_state']=='succeeded' for row in events),'events':events})
elif mode=='hold-database':
    signal.alarm(60)
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        with connect() as db:active=db.execute("SELECT id FROM invocations WHERE function_id=? AND state='running' AND handler_started=1 ORDER BY created_at DESC LIMIT 1",(function,)).fetchone()
        if active:break
        time.sleep(.05)
    else:raise RuntimeError('handler_not_observed')
    db=ControlWriter(state/'control.sqlite3',timeout=.2)
    try:
        observed=db.rows('SELECT state,handler_started FROM invocations WHERE id=?',(active['id'],))[0]
        assert observed['state']=='running' and observed['handler_started']==1,'dispatch_changed_before_lock'
        emit({'event':'writer-locked','invocation_id':active['id'],'identity':db.identity,'operator_uid':os.geteuid()})
        ready,_,_=select.select([sys.stdin],[],[],45)
        assert ready and sys.stdin.readline().strip()=='release','release_required'
    finally:
        db.close();emit({'event':'writer-released'})
elif mode=='graceful-stop':
    peer=sys.argv[3];assert str(UUID(peer))==peer and peer!=function
    with connect() as db:
        assert db.execute('SELECT 1 FROM functions WHERE id=? AND service_id=? AND deleted_at IS NULL',(peer,fn['service_id'])).fetchone()
    before=inspect();peer_before=inspect(peer)
    assert any(row['state']=='running' and row['handler_started']==1 for row in before['invocations'])
    assert any(row['state']=='ready' for row in peer_before['instances'])
    assert before['networks'] and before['leases'] and peer_before['networks'],'physical_resources_required'
    unit=restart_guard()
    stopper=None
    try:
        started_at=json.loads(docker('inspect','serverless-api'))[0]['State']['StartedAt']
        stopper=subprocess.Popen(['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST'],
            'stop','--time','20','serverless-api'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        deadline=time.monotonic()+25;lock_denied=0;lock_observations=[]
        with (state/'control.lock').open('rb') as lock:
            while stopper.poll() is None:
                assert time.monotonic()<deadline,'graceful_stop_timeout'
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:lock_denied+=1
                else:
                    try:
                        observed=[inspect(),inspect(peer)]
                        assert all(not row['containers'] and not row['networks'] and not row['leases'] and row['reserved_channel_count']==0 for row in observed),'lock_released_before_cleanup'
                        lock_observations.append({'resources_gone':True})
                    finally:fcntl.flock(lock,fcntl.LOCK_UN)
                time.sleep(.01)
        stopper.communicate(timeout=5);assert stopper.returncode==0 and lock_denied>0
        stopped=json.loads(docker('inspect','serverless-api'))[0]['State']
        assert not stopped['Running'] and stopped['ExitCode'] in (0,143),'graceful_exit_required'
        # Uvicorn re-raises SIGTERM after its completed lifespan, hence 143.
        lifecycle=subprocess.run(['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST'],
            'logs','--since',started_at,'--tail','1000','serverless-api'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True,timeout=15).stdout
        assert 'Application shutdown complete.' in lifecycle and 'Finished server process' in lifecycle,'lifespan_completion_required'
        with (state/'control.lock').open('rb') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            after=inspect();peer_after=inspect(peer)
            for observed in (after,peer_after):
                assert not observed['containers'] and not observed['networks'] and not observed['leases'] and observed['reserved_channel_count']==0
            assert after['instances'],'locked_database_reservation_required'
        emit({'event':'control-stopped','restart_guard':unit,'exit_code':stopped['ExitCode'],'lifespan_completed':True,'lock_released':True,'lock_denials_during_stop':lock_denied,'lock_observations':lock_observations,
              'before':before,'peer_before':peer_before,'after':after,'peer_after':peer_after})
    except BaseException:
        try:
            if stopper and stopper.poll() is None:stopper.communicate(timeout=30)
        finally:docker('start','serverless-api')
        raise
elif mode=='start-control':
    unit=sys.argv[3];assert re.fullmatch('serverless-restore-control-[0-9a-f]{32}',unit)
    docker('start','serverless-api')
    subprocess.run(['systemctl','stop',unit+'.timer'],check=True,timeout=15)
    emit({'event':'control-started','restart_guard':unit})
elif mode=='crash-control':
    before=inspect();assert any(row['state']=='running' and row['handler_started']==1 for row in before['invocations']),'active_handler_required'
    unit=restart_guard()
    try:
        docker('kill','serverless-api')
        item=json.loads(docker('inspect','serverless-api'))[0];assert not item['State']['Running'] and item['State']['ExitCode']==137
        emit({'event':'control-killed','before':before})
    finally:
        docker('start','serverless-api')
        subprocess.run(['systemctl','stop',unit+'.timer'],check=True,timeout=15)
        emit({'event':'control-started'})
else:raise ValueError('unknown_operation')
