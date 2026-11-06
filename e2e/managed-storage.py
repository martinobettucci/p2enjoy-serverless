# @spec docs/BACKLOG.md#sls-040 | docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#instances-avec-baux-gérés
# @verifies docs/STORAGE_AGENT.md#instances-avec-baux-gérés
"""Real baked control driver, Docker handlers and storage; root operates DEV faults only."""
import asyncio
from contextlib import suppress
import json
import os
from pathlib import Path
import select
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from uuid import UUID,uuid4

ROOT=Path('/srv/p2enjoy-serverless');UNIT='p2enjoy-storage-dev.service'
CONFIG={'data':{'enabled':True,'quota_mib':1},'cache':{'enabled':True,'quota_mib':1}}


def emit(value):print(json.dumps(value),flush=True)


async def worker(installation):
    sys.path.insert(0,'/app')
    from app.managed_instances import ManagedInstance
    from app.storage_client import StorageClient,StorageError
    from app.validator import ValidationError
    owner=asyncio.current_task()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM,owner.cancel)
    storage=StorageClient('/storage-agent/agent.sock',os.environ['SERVERLESS_STORAGE_ROOT_HOST'])
    work=Path(tempfile.mkdtemp(prefix='storage-proof-',dir='/state'))
    host_work=Path(os.environ['SERVERLESS_STATE_HOST_PATH'])/work.name
    instances=[];functions=[];consumers=[];checks=[];completed=False;cleanup_errors=[]
    async def fault(operation,**fields):
        emit({'fault':operation,**fields})
        answer=json.loads(await asyncio.to_thread(sys.stdin.readline))
        assert answer=={'ok':True},'Opération de panne refusée'
    async def wait_for(predicate):
        async with asyncio.timeout(15):
            while not predicate():await asyncio.sleep(.01)
    def passed(name):
        checks.append({'name':name,'status':'passed'});emit({'passed':name})
    async def function(configuration=CONFIG):
        identifier=str(uuid4());functions.append(identifier)
        await storage.call('configure',function_id=identifier,configuration=configuration)
        return identifier
    def instance(identifier,configuration=CONFIG,**overrides):
        settings=dict(docker_socket='/docker.sock',image=os.environ['SERVERLESS_RUNTIME_IMAGE'],
            code=str(ROOT/'qualification/artifacts'),work=work,host_work=host_work,installation=installation,
            function_id=identifier,revision_id=str(uuid4()),handler='volume-operations.cjs.handler',
            function_name='volume-persistence',environment={},secrets={},storage=storage,storage_configuration=configuration)
        settings.update(overrides);item=ManagedInstance(**settings);instances.append(item);return item
    async def close(item):
        async with asyncio.timeout(40):
            while not await item.close():await asyncio.sleep(.2)
        assert item.removed and not item.lease_possible and not item.cleanup_error
        assert await item.call('GET','/containers/'+item.name+'/json',allowed=(404,))
        assert await item.call('GET','/networks/'+item.name,allowed=(404,))
        assert item.channel is None or not item.channel.exists()
        assert not any(row['consumer_id']==item.id for row in await storage.leases(installation))
    async def invoke(item,operation='read',name='record',status=200,**fields):
        result=await item.invoke({'operation':operation,'name':name,**fields},5)
        assert result['state']=='succeeded' and result['instance_available'],result
        assert result['handler_started'] and result['response']['statusCode']==status,result
        return json.loads(result['response']['body'])
    try:
        health=await storage.call('health');assert health['healthy'] and not health['leases']
        identifier=await function();item=await instance(identifier).start()
        assert item.name.startswith('serverless-function-volume-persistence-')
        inspected=await item.call('GET','/containers/'+item.container+'/json')
        mounts={m['Destination']:m for m in inspected['Mounts']}
        for kind in ('data','cache'):
            assert mounts['/'+kind]['Source']==str(storage.root/'mounts'/identifier/kind)
            assert mounts['/'+kind]['RW']
        assert (await storage.leases(installation))==[{'consumer_id':item.id,'function_id':identifier,'complete':True}]
        passed('Bail réel depuis le contrôle et binds limités aux montages FUSE')
        first=await invoke(item,'write',value='persistent')
        second=await invoke(item);assert second['value']=='persistent' and first['pid']!=second['pid']
        await invoke(item,'write',volume='cache',value='cached')
        await close(item);snapshot=await storage.call('status',function_id=identifier)
        assert snapshot['leases']==0 and all(v['phase']=='unmounted' for v in snapshot['volumes'].values())
        item=await instance(identifier).start()
        assert (await invoke(item))['value']=='persistent'
        assert (await invoke(item,volume='cache'))['value']=='cached'
        passed('Données et cache conservés entre enfants et recréations Docker')
        for kind in ('data','cache'):
            answer=await invoke(item,'fill',name='quota-limit',volume=kind,bytes=2*1024**2,status=507)
            assert answer['error']=='EDQUOT' and answer['errno']==-122
            assert (await storage.call('check',consumer_id=item.id,installation_id=installation))['volumes'][kind]['used']<=1024**2
            await invoke(item,'remove',name='quota-limit',volume=kind)
        passed('Quotas data et cache appliqués aux écritures réelles du handler')
        peer=await instance(identifier).start()
        await invoke(item,'write',value='shared');assert (await invoke(peer))['value']=='shared'
        await close(item);assert (await storage.call('status',function_id=identifier))['leases']==1
        assert (await invoke(peer))['value']=='shared'
        try:await storage.call('configure',function_id=identifier,configuration={**CONFIG,'data':{'enabled':True,'quota_mib':2}})
        except StorageError as error:assert str(error)=='volume_busy'
        else:raise AssertionError('Quota modifié sous un consommateur actif')
        other_id=await function();other=await instance(other_id).start()
        assert (await invoke(other,status=404))['error']=='ENOENT'
        await close(other);await close(peer)
        passed('Partage par fonction, isolation entre fonctions et mutation refusée sous bail')
        item=await instance(identifier).start()
        calls=await asyncio.gather(item.invoke({'operation':'read','name':'record'},5),
                                   item.invoke({'operation':'read','name':'record'},5),return_exceptions=True)
        assert sum(isinstance(r,ValidationError) and str(r)=='instance_unavailable' for r in calls)==1
        assert sum(isinstance(r,dict) and r.get('state')=='succeeded' for r in calls)==1
        assert (await invoke(item))['value']=='shared'
        try:await item.start()
        except ValidationError as error:assert str(error)=='instance_already_started'
        else:raise AssertionError('Second démarrage accepté')
        await close(item);passed('Invocations concurrentes et double démarrage refusés sans tuer le consommateur')
        bad=instance(identifier,image='sha256:'+'0'*64)
        try:await bad.start()
        except ValidationError:pass
        else:raise AssertionError('Image inexistante acceptée')
        await close(bad)
        for target,configuration,expected in [(identifier,{**CONFIG,'cache':{'enabled':False,'quota_mib':1}},'configuration_conflict'),
                                               (str(uuid4()),CONFIG,'function_unknown')]:
            refused=instance(target,configuration)
            try:await refused.start()
            except StorageError as error:assert str(error)==expected
            else:raise AssertionError('Acquisition invalide acceptée')
            assert refused.container is None;await close(refused)
        passed('Refus de stockage et échec du démarrage Docker sans bail abandonné')
        item=await instance(identifier).start()
        result=await item.invoke({'operation':'write-sleep','name':'deadline','value':'before-timeout','ms':30000},2)
        assert result['state']=='failed' and result['error']=='invocation_timeout' and result['handler_started']
        await close(item);item=await instance(identifier).start()
        assert (await invoke(item,name='deadline'))['value']=='before-timeout'
        await close(item);passed('Deadline, destruction et conservation des écritures acquittées')
        item=instance(identifier)
        await fault('pause_agent')
        starting=asyncio.create_task(item.start());await wait_for(lambda:item.lease_possible)
        await asyncio.sleep(.1);assert not starting.done() and item.container is None
        starting.cancel();await asyncio.sleep(0);starting.cancel()
        await fault('resume_agent')
        result=await asyncio.gather(starting,return_exceptions=True)
        assert isinstance(result[0],asyncio.CancelledError);await close(item)
        passed('Annulation répétée pendant acquisition réelle suspendue puis rejointe')
        item=await instance(identifier).start();await fault('pause_agent')
        invoking=asyncio.create_task(item.invoke({'operation':'read','name':'record'},5))
        await wait_for(lambda:item.managed_invoking);await asyncio.sleep(.1)
        assert not item.busy and not invoking.done()
        invoking.cancel();await asyncio.sleep(0);invoking.cancel();await fault('resume_agent')
        result=await asyncio.gather(invoking,return_exceptions=True)
        assert isinstance(result[0],asyncio.CancelledError);await close(item)
        passed('Annulation pendant contrôle du bail avant dispatch avec nettoyage complet')
        item=await instance(identifier).start()
        invoking=asyncio.create_task(item.invoke({'operation':'write-sleep','name':'fuse-loss','value':'kept','ms':30000},40))
        await wait_for(lambda:item.started_observed);await asyncio.sleep(.2)
        await fault('kill_volume',function_id=identifier)
        result=await invoking
        assert result['state']=='failed' and result['error'] in ('storage_unavailable','cleanup_failed') and result['handler_started']
        assert not result['instance_available'];await close(item)
        item=await instance(identifier).start();assert (await invoke(item,name='fuse-loss'))['value']=='kept'
        await close(item);passed('Mort du vrai démon FUSE, retrait du consommateur et réacquisition sans perte')
        item=await instance(identifier).start()
        invoking=asyncio.create_task(item.invoke({'operation':'write-sleep','name':'agent-loss','value':'kept','ms':30000},40))
        await wait_for(lambda:item.started_observed);await asyncio.sleep(.2)
        await fault('stop_agent');result=await invoking
        assert result['state']=='failed' and result['error']=='cleanup_failed' and result['handler_started']
        assert not result['instance_available'] and not item.removed and item.lease_possible
        assert await item.call('GET','/containers/'+item.name+'/json',allowed=(404,))
        await fault('start_agent')
        async with asyncio.timeout(20):
            while True:
                try:
                    if (await storage.call('health'))['ready']:break
                except StorageError:pass
                await asyncio.sleep(.2)
        await close(item);item=await instance(identifier).start()
        assert (await invoke(item,name='agent-loss'))['value']=='kept'
        await close(item)
        passed('Arrêt agent, nettoyage différé, socket retrouvé dans le même contrôle et reprise')
        disabled={'data':{'enabled':False,'quota_mib':1},'cache':{'enabled':False,'quota_mib':1}}
        no_volumes=await function(disabled);item=await instance(no_volumes,disabled).start()
        assert item.mounts=={} and (await invoke(item,status=404))['error']=='ENOENT'
        await close(item);passed('Volumes désactivés : aucun bind et bail libéré')
        for _ in range(51):
            consumer=str(uuid4());consumers.append((no_volumes,consumer))
            leased=await storage.acquire(no_volumes,consumer,installation,disabled)
            assert leased['paths']=={} and leased['generations']=={}
        entries=await storage.leases(installation)
        assert len(entries)==51 and {row['consumer_id'] for row in entries}=={consumer for _,consumer in consumers}
        for target,consumer in consumers:await storage.release_confirmed(target,consumer,installation)
        consumers.clear();assert not await storage.leases(installation)
        passed('Pagination du client de production sur 51 vrais baux puis libération confirmée')
        command=[sys.executable,'-B','-m','app.instances','--managed-storage','--docker-socket','/docker.sock',
            '--image',os.environ['SERVERLESS_RUNTIME_IMAGE'],'--code',str(ROOT/'qualification/artifacts'),
            '--work',str(work),'--host-work',str(host_work),'--installation',installation,'--function-id',identifier,
            '--revision-id',str(uuid4()),'--handler','volume-operations.cjs.handler','--function-name','volume-diagnostic']
        cli=await asyncio.create_subprocess_exec(*command,stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        frames=[{'environment':{},'secrets':{},'storage':CONFIG},
                {'operation':'invoke','event':{'operation':'read','name':'record'},'timeout_seconds':5}]
        output,errors=await asyncio.wait_for(cli.communicate((''.join(json.dumps(frame)+'\n' for frame in frames)).encode()),30)
        assert cli.returncode==0 and not errors,(cli.returncode,errors.decode()[:200])
        replies=[json.loads(line) for line in output.splitlines()]
        assert len(replies)==3 and replies[0]['ready'] and replies[2]=={'closed':True}
        assert replies[1]['state']=='succeeded' and json.loads(replies[1]['response']['body'])['value']=='shared'
        assert not await storage.leases(installation)
        passed('Diagnostic CLI géré : configuration stdin, vraie invocation puis fermeture sur EOF')
        completed=True
    except BaseException as error:
        emit({'failure':type(error).__name__+': '+str(error)[:2000]})
    finally:
        try:await fault('restore_agent')
        except (ValueError,AssertionError):
            # The root operator also restores the agent when its control pipe fails.
            async with asyncio.timeout(20):
                while True:
                    try:
                        if (await storage.call('health'))['ready']:break
                    except StorageError:pass
                    await asyncio.sleep(.2)
        for item in instances:
            try:await close(item)
            except BaseException as error:cleanup_errors.append(type(error).__name__)
        for target,consumer in consumers:
            try:await storage.release_confirmed(target,consumer,installation)
            except BaseException as error:cleanup_errors.append(type(error).__name__)
        for identifier in functions:
            try:
                await storage.call('archive',function_id=identifier)
                await storage.call('purge',function_id=identifier)
            except BaseException as error:cleanup_errors.append(type(error).__name__+': '+str(error))
        try:
            assert not await storage.leases(installation)
            assert not list(work.iterdir());work.rmdir()
        except BaseException as error:cleanup_errors.append(type(error).__name__)
        emit({'report':{'completed':completed and not cleanup_errors,'cleanup':not cleanup_errors,
            'passed':len(checks),'failed':int(not completed or bool(cleanup_errors)),'skipped':0,
            'checks':checks,'cleanup_errors':cleanup_errors,'installation_id':installation,'functions':functions}})


def parent():
    report=ROOT/'runtime/managed-storage-proof.json'
    report.write_text(json.dumps({'completed':False,'cleanup':False,'skipped':0})+'\n')
    assert os.getuid()==0 and Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV root requis'
    installation=str(uuid4());script='/tmp/managed-storage-'+UUID(installation).hex+'.py'
    docker=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
    def run(args,**kwargs):return subprocess.run(args,check=True,text=True,capture_output=True,timeout=90,**kwargs).stdout.strip()
    def unit(action):return run(['systemctl',action,UNIT])
    before=json.loads(run(docker+['inspect','serverless-api']))[0]['Id']
    directory=Path(run(docker+['exec','serverless-api','python','-B','-c',
        'import os;print(os.environ["SERVERLESS_STORAGE_SOCKET_DIR_HOST"])']));inode=directory.stat().st_ino
    run(docker+['exec','-i','serverless-api','python','-B','-c',
        'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text(sys.stdin.read())',script],input=Path(__file__).read_text())
    process=None;final=None
    try:
        process=subprocess.Popen(docker+['exec','-i','serverless-api','python','-B',script,'--worker',installation],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        deadline=time.monotonic()+240;buffer=b''
        def lines():
            nonlocal buffer
            while True:
                if b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1);yield line;continue
                if time.monotonic()>deadline:raise TimeoutError('Campagne stockage silencieuse ou trop longue')
                ready,_,_=select.select([process.stdout],[],[],1)
                if not ready:continue
                chunk=os.read(process.stdout.fileno(),65536)
                if not chunk:
                    assert not buffer,'Trame interrompue';return
                buffer+=chunk
                if len(buffer)>65536:raise ValueError('Trame trop grande')
        for line in lines():
            frame=json.loads(line)
            if 'fault' in frame:
                operation=frame['fault']
                if operation in ('pause_agent','resume_agent'):
                    run(['systemctl','kill','--kill-whom=main','--signal='+('STOP' if operation=='pause_agent' else 'CONT'),UNIT])
                elif operation in ('stop_agent','start_agent'):unit('stop' if operation=='stop_agent' else 'start')
                elif operation=='restore_agent':
                    subprocess.run(['systemctl','kill','--kill-whom=main','--signal=CONT',UNIT],capture_output=True)
                    unit('start')
                elif operation=='kill_volume':
                    identifier=str(UUID(frame['function_id']))
                    # Read-only registry access identifies the exact owned daemon; never edit durable state.
                    with sqlite3.connect('file:/srv/p2enjoy-serverless/storage-state/registry.sqlite3?mode=ro',uri=True) as db:
                        row=db.execute("SELECT daemon_pid,generation FROM volumes WHERE function_id=? AND kind='data' AND phase='mounted'",(identifier,)).fetchone()
                        assert db.execute('SELECT count(*) FROM leases WHERE function_id=? AND installation_id=?',(identifier,installation)).fetchone()[0]==1
                    assert row
                    arguments=Path('/proc/'+str(row[0])+'/cmdline').read_bytes().split(b'\0')
                    assert ('p2q-'+UUID(row[1]).hex).encode() in arguments
                    assert ('/srv/p2enjoy-serverless/storage-state/mounts/'+identifier+'/data').encode() in arguments
                    os.kill(row[0],signal.SIGKILL)
                else:raise AssertionError('Unknown fault operation')
                process.stdin.write(b'{"ok":true}\n');process.stdin.flush()
            elif 'report' in frame:final=frame['report']
            elif 'passed' in frame:print('PASS '+frame['passed'],flush=True)
            else:print(json.dumps(frame),flush=True)
        assert process.wait(timeout=30)==0 and final is not None,'Worker interrompu'
        final['control_container_unchanged']=json.loads(run(docker+['inspect','serverless-api']))[0]['Id']==before
        final['socket_directory_preserved']=directory.stat().st_ino==inode
        final['completed']=final['completed'] and final['control_container_unchanged'] and final['socket_directory_preserved']
        report.write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
        assert final['completed'],final
        print(json.dumps({key:final[key] for key in ('completed','cleanup','passed','failed','skipped')}),flush=True)
    finally:
        subprocess.run(['systemctl','kill','--kill-whom=main','--signal=CONT',UNIT],capture_output=True)
        unit('start')
        if process and process.poll() is None:
            # Stop the exact worker, not just the Docker client; its finally joins leases and Docker.
            stop="import os,signal,sys,pathlib\nfor p in pathlib.Path('/proc').iterdir():\n if p.name.isdigit() and int(p.name)!=os.getpid():\n  try: args=(p/'cmdline').read_bytes().split(b'\\0')\n  except OSError: continue\n  if sys.argv[1].encode() in args: os.kill(int(p.name),signal.SIGTERM)"
            run(docker+['exec','serverless-api','python','-B','-c',stop,script])
            remaining,_=process.communicate(timeout=45)
            for line in remaining.splitlines():
                with suppress(ValueError):
                    frame=json.loads(line)
                    if 'report' in frame:
                        frame['report']['completed']=False;report.write_text(json.dumps(frame['report'],ensure_ascii=False,indent=2)+'\n')
        run(docker+['exec','serverless-api','rm','-f',script])


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':asyncio.run(worker(str(UUID(sys.argv[2]))))
    else:parent()
