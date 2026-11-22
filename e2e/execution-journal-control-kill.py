# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
"""Kill only the exact observed DEV schema011 control, retaining the inherited lock."""
import fcntl,hashlib,json,os,signal,socket,stat,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
signal.alarm(45)
folder=Path(sys.argv[1]);fd=int(sys.argv[2]);info=folder.lstat()
assert folder.parent==Path('/run') and folder.name.startswith('serverless-restore-journal-cut-') and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
item=json.loads((folder/'identity.json').read_text());info=os.fstat(fd)
assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and [info.st_dev,info.st_ino]==item['lock_identity']
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==item['kill_sha256']
assert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in item['program_sha256']}==item['program_sha256']
assert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in item['official_sha256']}==item['official_sha256']
fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
result={'completed':False,'container_id':item['container_id'],'image':item['image'],'docker_client_joined':False}
def inspect():return json.loads(subprocess.check_output(item['docker']+['inspect',item['container_id']],text=True,timeout=5))[0]
try:
 current=inspect();assert current['Id']==item['container_id'] and current['Image']==item['image'] and current['State']['Running'] and current['State']['StartedAt']==item['started_at']
 try:
  p=subprocess.run(item['docker']+['kill','--signal','KILL',item['container_id']],capture_output=True,timeout=25)
 except subprocess.TimeoutExpired:
  result.update(docker_client_joined=False,error='docker_kill_timeout');raise
 result['docker_client_joined']=True
 assert p.returncode==0,'docker_kill_failed'
 current=inspect();assert not current['State']['Running'] and current['State']['ExitCode']==137 and current['State']['StartedAt']==item['started_at']
 result.update(completed=True,exit_code=137)
except Exception as error:result['error_type']=type(error).__name__
finally:
 path=folder/'kill-result.json';pending=folder/'kill-result.pending';pending.write_text(json.dumps(result)+'\n');os.chmod(pending,0o600);pending.replace(path)
assert result['completed'],'stop_outcome_unknown'
