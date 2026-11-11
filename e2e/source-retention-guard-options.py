# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#parcours-réel
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#parcours-réel
"""Real DEV 2700s guard and incompatible-option refusals for protected retention."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
from uuid import uuid4

NATIVE = r'''
import hashlib,json,os,select,signal,socket,subprocess,tempfile,time,uuid
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');helper=root/'e2e/storage-legacy-environment.py';history=root/'qualification-history'
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
checks=[];events=[];child=None;campaign=None;buffer=b'';stage='preflight';cleanup=False

def services():
 rows=json.loads(subprocess.check_output(D+['inspect','serverless-api','serverless-runtime-reference'],text=True,timeout=20))
 return [{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status'],'running':v['State']['Running']} for v in rows]

def until_event(name,seconds):
 global buffer
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  while b'\n' in buffer:
   line,buffer=buffer.split(b'\n',1);value=json.loads(line);events.append(value)
   if value.get('event')==name:return value
  readable=select.select([child.stdout],[],[],min(1,max(0,end-time.monotonic())))[0]
  if readable:
   data=os.read(child.stdout.fileno(),65536);assert data,'driver_ended_before_event';buffer+=data
 raise TimeoutError('guard_event_deadline')

def main():
 global child,campaign,stage,cleanup
 signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('guard_options_deadline')));signal.alarm(250)
 before=services();assert all(v['running'] and v['health']=='healthy' for v in before)
 refusals=[]
 for mode,options,reason in [
  ('instance-limit',['--guard-seconds=120','--guard-seconds=2700'],'one_guard_duration_required'),
  ('instance-limit',['--guard-seconds=1800','--guard-seconds=2700'],'one_guard_duration_required'),
  ('function-version-purge',['--guard-seconds=2700'],'guard_duration_requires_instance_limit'),
  ('instance-limit',['--guard-seconds=2700','--firing-history=schedule-firing-volume-5d3595f228964f4e848a8974004e8c0f','--firing-observation=count'],'firing_replay_guard_duration')]:
  stage='invalid-options';identifier=str(uuid.uuid4());result=subprocess.run(['python3','-B',str(helper),mode,identifier,before[0]['image'],*options],capture_output=True,timeout=40)
  assert result.returncode==1 and reason.encode() in result.stderr,'expected_guard_refusal_missing'
  assert all(not (history/(prefix+identifier)).exists() for prefix in ['storage-absence-','function-version-purge-','function-version-unknown-first-','instance-limit-'])
  assert services()==before,'invalid_options_changed_services'
  refusal={'mode':mode,'options':options,'reason':reason,'exit_code':1,'stderr_sha256':hashlib.sha256(result.stderr).hexdigest(),'campaign_directory_absent':True};refusals.append(refusal);checks.append({'name':'Refus avant mutation : '+reason,'status':'passed'})
 stage='default-window';campaign=str(uuid.uuid4())
 with tempfile.TemporaryFile() as errors:
  child=subprocess.Popen(['python3','-B',str(helper),'instance-limit',campaign,before[0]['image'],'--guard-seconds=2700'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors)
  armed=until_event('guard-armed',120);assert armed['guard_seconds']==2700 and 'OnActiveUSec=45min' in armed['timer_schedule'];ready=until_event('instance-limit-ready',120)
  assert ready['container']['image']==before[0]['image'] and ready['container']['id']!=before[0]['id']
  assert ready['capacity']['original_control_stopped'] and ready['capacity']['official_configuration_unchanged']
  assert all(not ready['capacity'][key] for key in ['functions','instances','invocations','firings','containers'])
  child.stdin.write(b'{"op":"restore"}\n');child.stdin.close();stage='restore'
  restored=until_event('restored',100);assert child.wait(timeout=30)==0
  assert all(restored[k] for k in ['directories_identical','databases_identical','artifacts_identical','configuration_unchanged','agent_healthy','control_healthy','reference_unchanged','temporary_directories_removed']) and not restored['independent']
  status=json.loads(subprocess.check_output(['python3','-B',str(helper),'status',campaign],text=True,timeout=40));assert status['restored'] and not status['driver_alive'] and status['timer_state'] in ('inactive','unknown') and status['service_state'] in ('inactive','unknown')
  after=services();assert before[1]==after[1];assert all(before[0][k]==after[0][k] for k in ['id','image','health','running']);cleanup=True
  checks.append({'name':'Durée2700 réellement programmée, même image, restitution nominale jointe','status':'passed'})
  signal.alarm(0);return {'completed':True,'cleanup':True,'checks':checks,'refusals':refusals,'events':events,'before_services':before,'after_services':after,'terminal_status':{k:status[k] for k in ['restored','driver_alive','timer_state','service_state']},'restoration':restored,'explicit_guard_seconds':2700,'campaign':campaign}
try:print(json.dumps(main()))
except BaseException as error:
 signal.alarm(0);rescue=None
 if child is not None:
  try:
   if not child.stdin.closed:child.stdin.close()
   result=subprocess.run(['python3','-B',str(helper),'restore',campaign],capture_output=True,text=True,timeout=150);rescue={'exit_code':result.returncode,'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest()};child.wait(timeout=30)
  except BaseException as restore_error:rescue={'failure':type(restore_error).__name__}
 print(json.dumps({'completed':False,'cleanup':cleanup,'checks':checks,'events':events,'stage':stage,'failure':type(error).__name__,'rescue':rescue}));raise SystemExit(1)
'''


def main():
    root=Path(__file__).resolve().parent.parent;out=root/'.local/e2e';out.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=out/('source-retention-guard-options-'+uuid4().hex+'.json');state={'completed':False,'started_at_ns':time.time_ns(),'operator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};path.write_text(json.dumps(state)+'\n');path.chmod(0o600)
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24','python3 -B -'],input=NATIVE,text=True,capture_output=True,timeout=420)
    receipt=json.loads(result.stdout) if result.stdout.strip().startswith('{') else {'completed':False,'failure':'native_protocol_failure'}
    state.update(completed=result.returncode==0 and receipt['completed'],exit_code=result.returncode,receipt=receipt,finished_at_ns=time.time_ns(),stderr_sha256=hashlib.sha256(result.stderr.encode()).hexdigest());path.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps({'completed':state['completed'],'report':str(path),'receipt':receipt}));assert state['completed'],'guard_options_failed_no_automatic_replay'


if __name__=='__main__':main()
