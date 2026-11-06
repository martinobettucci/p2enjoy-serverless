# @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#canal-privé-et-terminaison
# @verifies docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#canal-privé-et-terminaison
"""Exercise concurrent production driver methods against real Docker and Unix sockets."""
import asyncio
from contextlib import suppress
import http.client
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

ROOT=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(ROOT))
from control.app.instances import Instance
from control.app.validator import UnixHTTP,ValidationError
REPORT=ROOT/'runtime'/'lifecycle-proof.json'
REPORT.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
checks=[];completed=False;work=None;fixture=None;installation=str(uuid4());instances=[];image=None


def run(args):
    result=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=30)
    if result.returncode:raise RuntimeError('Commande échouée '+args[0])
    return result.stdout


def owned(kind='container'):
    args=['docker','ps','-aq'] if kind=='container' else ['docker','network','ls','-q']
    return run(args+['--filter','label=tech.p2enjoy.serverless.installation='+installation]).split()


def passed(name):
    checks.append({'name':name,'status':'passed'});print('PASS',name,flush=True)


def instance():
    item=Instance(docker_socket='/run/user/1001/docker.sock',image=image,code=code,work=work,installation=installation,
        function_id=str(uuid4()),revision_id=str(uuid4()),handler='invoke.cjs.handler',function_name='lifecycle-proof',environment={},secrets={})
    instances.append(item);return item


async def wait_for(predicate,timeout=10):
    deadline=time.monotonic()+timeout
    while not predicate():
        assert time.monotonic()<deadline,'Transition non observée'
        await asyncio.sleep(0)


def private(item,path,body,headers=None):
    connection=UnixHTTP(item.channel/'control.sock',3)
    try:
        connection.request('POST',path,body=json.dumps(body),headers={'Content-Type':'application/json','X-Instance-Key':item.key,**(headers or {})})
        response=connection.getresponse();response.read();return response.status
    except (http.client.RemoteDisconnected,ConnectionResetError):return None
    finally:connection.close()


async def absent(item):
    assert item.removed and not item.cleanup_error
    assert await item.call('GET','/containers/'+item.name+'/json',allowed=(404,))
    assert await item.call('GET','/networks/'+item.name,allowed=(404,))
    assert item.channel is None or not item.channel.exists()


async def main():
    for phase in ('image','network','container'):
        item=instance();starting=asyncio.create_task(item.start())
        await asyncio.sleep(0)
        if phase!='image':await wait_for(lambda:getattr(item,phase) is not None)
        assert not starting.done(),'Démarrage déjà achevé'
        closing=asyncio.create_task(item.close())
        results=await asyncio.gather(starting,closing,return_exceptions=True)
        assert results[1] is True
        assert results[0] is item or isinstance(results[0],ValidationError)
        await absent(item);passed('Fermeture concurrente au démarrage : '+phase)
    for phase in ('network','container'):
        item=instance();starting=asyncio.create_task(item.start())
        await wait_for(lambda:getattr(item,phase) is not None)
        assert starting.cancel();await asyncio.sleep(0);assert starting.cancel()
        result=await asyncio.gather(starting,return_exceptions=True)
        assert isinstance(result[0],asyncio.CancelledError)
        await absent(item);passed('Annulation répétée du démarrage : '+phase)
    item=await instance().start()
    invoking=asyncio.create_task(item.invoke({'operation':'sleep','ms':30000},40))
    await wait_for(lambda:item.started_observed)
    assert invoking.cancel();await asyncio.sleep(0);assert invoking.cancel()
    result=await asyncio.gather(invoking,return_exceptions=True)
    assert isinstance(result[0],asyncio.CancelledError)
    await absent(item);passed('Annulation répétée pendant invocation et destruction rejointe')
    item=await instance().start()
    invoking=asyncio.create_task(item.invoke({'operation':'sleep','ms':30000},40))
    await wait_for(lambda:item.started_observed)
    assert await item.close()
    result=await invoking
    assert result['error']=='instance_stopped' and result['handler_started'] is True and not result['instance_available']
    await absent(item);passed('Fermeture concurrente à une invocation active')
    item=await instance().start()
    try:await item.start()
    except ValidationError as error:assert str(error)=='instance_already_started'
    else:raise AssertionError('Second démarrage accepté')
    result=await item.invoke({'operation':'echo'},5);assert result['state']=='succeeded' and result['instance_available']
    assert await item.close();await absent(item);passed('Second démarrage refusé sans détruire l’instance prête')
    item=await instance().start();invoking=asyncio.create_task(item.invoke({'operation':'echo'},5))
    await wait_for(lambda:item.future is not None and item.future.done())
    assert not invoking.done(),'Phase de contrôle après résultat non observée'
    assert await item.close();result=await invoking
    assert result['state']=='succeeded' and not result['instance_available']
    await absent(item);passed('Réponse acceptée conservée pendant une fermeture concurrente')
    item=await instance().start()
    (item.channel/'owned-file').write_text('cleanup-proof');os.chmod(item.channel,0o500)
    assert await item.close() is False and item.cleanup_error and not item.removed and item.channel.exists()
    assert await item.call('GET','/containers/'+item.name+'/json',allowed=(404,))
    os.chmod(item.channel,0o700)
    assert await item.close() is True;await absent(item)
    passed('Échec réel de suppression du canal puis reprise du nettoyage')
    item=await instance().start()
    invoking=asyncio.create_task(item.invoke({'operation':'sleep','ms':5000},10))
    await wait_for(lambda:item.started_observed)
    foreign={'invocation_id':str(uuid4()),'handler_started':True,'state':'failed','error':'handler_error','logs':'','logs_truncated':False}
    assert await asyncio.to_thread(private,item,'/result',foreign) is None
    assert await asyncio.to_thread(private,item,'/started',{'invocation_id':str(uuid4())}) is None
    assert await asyncio.to_thread(private,item,'/result',{}, {'Content-Type':'text/plain'})==415
    assert await asyncio.to_thread(private,item,'/started',{'invocation_id':item.job['invocation_id']})==202
    def malformed():
        for raw in [b'GET /next HTTP/1.1\r\nHost: local\r\nHost: duplicate\r\n\r\n',
                    b'POST /result HTTP/1.1\r\nContent-Length: 10485761\r\n\r\n',
                    b'GET /next HTTP/1.1\r\nX-Large: '+b'x'*9000+b'\r\n\r\n']:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(3);connection.connect(str(item.channel/'control.sock'));connection.sendall(raw)
                try:assert not connection.recv(1024)
                except ConnectionResetError:pass
        held=[]
        try:
            for _ in range(4):
                connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connection.settimeout(3)
                connection.connect(str(item.channel/'control.sock'));connection.sendall(b'GET /next HTTP/1.1\r\n');held.append(connection)
            deadline=time.monotonic()+2
            while len(item.connections)<4:
                assert time.monotonic()<deadline,'Quatre connexions non observées'
                time.sleep(.01)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(3);connection.connect(str(item.channel/'control.sock'));connection.sendall(('POST /started HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\nX-Instance-Key: '+item.key+'\r\nContent-Length: '+str(len(json.dumps({'invocation_id':item.job['invocation_id']})))+'\r\n\r\n'+json.dumps({'invocation_id':item.job['invocation_id']})).encode())
                try:assert not connection.recv(1024)
                except ConnectionResetError:pass
        finally:
            for connection in held:connection.close()
    await asyncio.to_thread(malformed)
    result=await invoking
    assert result['state']=='succeeded' and result['instance_available']
    duplicate={**foreign,'invocation_id':result['invocation_id']}
    assert await asyncio.to_thread(private,item,'/result',duplicate)==409
    assert await asyncio.to_thread(private,item,'/started',{'invocation_id':result['invocation_id']})==409
    assert await item.close();await absent(item)
    passed('Canal réel : identifiants étrangers, doublons, tailles et connexions bornées')


try:
    image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime:dev']).strip()
    fixture_image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime-qualification:dev']).strip()
    work=Path(tempfile.mkdtemp(prefix='il-',dir=ROOT/'state'));code=work/'code';code.mkdir()
    fixture=run(['docker','create','--network','none',fixture_image]).strip()
    run(['docker','cp',fixture+':/fixtures/.',str(code)]);run(['docker','rm',fixture]);fixture=None
    def expired(signum,frame):raise TimeoutError('Échéance indépendante de campagne')
    signal.signal(signal.SIGALRM,expired);signal.alarm(90)
    asyncio.run(main());signal.alarm(0);assert not owned() and not owned('network');completed=True
finally:
    signal.alarm(0)
    for container in owned():run(['docker','rm','-f',container])
    for network in owned('network'):run(['docker','network','rm',network])
    if fixture:run(['docker','rm','-f',fixture])
    for item in instances:
        if item.channel and item.channel.exists():os.chmod(item.channel,0o700)
    if work:shutil.rmtree(work)
    cleanup=not owned() and not owned('network');completed=completed and cleanup
    REPORT.write_text(json.dumps({'completed':completed,'cleanup':cleanup,'passed':len(checks),'failed':0 if completed else 1,
        'skipped':0,'image':image,'fixture_image':fixture_image,'checks':checks},ensure_ascii=False,indent=2)+'\n')
    assert cleanup,'Ressource survivante'
