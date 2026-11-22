# @spec docs/BACKLOG.md#sls-128 | docs/CONSOLE_STORAGE.md
# @verifies docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOGS.md#conservation-par-service-et-budget
"""Read-only bounded observation of the actual control temporary filesystem."""
import hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
from uuid import UUID
from control_database import read_control
assert socket.gethostname()=='infra-serverless' and os.geteuid()==0
namespace,key,campaign=map(lambda x:str(UUID(x)),sys.argv[1:]);root=Path('/srv/p2enjoy-serverless')
with read_control(root/'state/control.sqlite3') as db:
 row=db.execute('SELECT n.description,n.id FROM namespaces n JOIN services s ON s.namespace_id=n.id JOIN functions f ON f.service_id=s.id WHERE f.id=?',(key,)).fetchone()
 assert row['id']==namespace and row['description']==campaign
args=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
container=json.loads(subprocess.check_output(args+['inspect','serverless-api'],text=True,timeout=10))[0]
assert container['State']['Running'] and container['State']['Health']['Status']=='healthy'
descendants=[container['State']['Pid']]
for parent in descendants:descendants.extend(map(int,Path('/proc',str(parent),'task',str(parent),'children').read_text().split()))
pids=[pid for pid in descendants if Path('/proc',str(pid),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')];assert len(pids)==1
pid=pids[0];proc=Path('/proc',str(pid));birth=lambda:proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]
identity={'pid':pid,'birth':birth(),'container_id':container['Id'],'image':container['Image'],'started_at':container['State']['StartedAt'],'cgroup_sha256':hashlib.sha256(proc.joinpath('cgroup').read_bytes()).hexdigest()}
def space():
 s=os.statvfs(proc/'root/tmp');return {'available_bytes':s.f_bavail*s.f_frsize,'total_bytes':s.f_blocks*s.f_frsize}
initial=space();result={'event':'temp-space-observation','identity':identity,'initial':initial,'minimum_available_bytes':initial['available_bytes'],'peak_files':[],'samples':0,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'application_data_read':False,'mutations':0}
print(json.dumps({'event':'ready','identity':identity}),flush=True);started=time.monotonic()
while time.monotonic()-started<12:
 assert birth()==identity['birth']
 current=space();result['samples']+=1
 if current['available_bytes']<result['minimum_available_bytes']:
  result['minimum_available_bytes']=current['available_bytes'];files=[]
  descriptors=list(proc.joinpath('fd').iterdir());assert len(descriptors)<=128
  for fd in descriptors:
   try:
    target=os.readlink(fd)
    if target.startswith('/tmp/etilqs_'):
     info=fd.stat();files.append({'fd':int(fd.name),'bytes':info.st_size,'allocated_bytes':info.st_blocks*512,'deleted':target.endswith(' (deleted)'),'sqlite_temporary_name':True})
   except FileNotFoundError:continue
  result['peak_files']=files;result['peak_after_seconds']=time.monotonic()-started
 time.sleep(.002)
assert hashlib.sha256(proc.joinpath('cgroup').read_bytes()).hexdigest()==identity['cgroup_sha256']
result.update(final=space(),elapsed_seconds=time.monotonic()-started,completed=True)
print(json.dumps(result),flush=True)
