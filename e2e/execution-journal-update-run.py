# @spec docs/BACKLOG.md#sls-126 | docs/EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-du-diagnostic-de-maintenance--sls-1265
# @spec docs/BACKLOG.md#sls-124 | docs/EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-du-focus--sls-124
# @spec docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-de-code-compatible011--sls-128
# @verifies docs/BACKLOG.md#sls-124 | docs/BACKLOG.md#sls-128 | docs/EXECUTION_LOG_DEPLOYMENT.md#mise-à-jour-de-code-compatible011--sls-128
"""Launch one guarded DEV compatible011 code update, preserve its primary and final receipts."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value):
    temporary=path.with_name(path.name+'.pending')
    with temporary.open('w') as stream:
        os.fchmod(stream.fileno(),0o600);json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def remote(arguments,*,input=None,timeout=15):
    assert all(isinstance(value,str) and '\0' not in value for value in arguments)
    # Values in these command arguments are validated paths, UUIDs, SHA and fixed
    # properties. POSIX quoting preserves ExecStopPost as exactly one argument.
    import shlex
    return subprocess.run(SSH+[' '.join(shlex.quote(value) for value in arguments)],input=input,
        text=True,capture_output=True,timeout=timeout,check=True).stdout


def observe(folder,operator_sha,helper_sha):
    program='folder='+repr(folder)+'\noperator_sha='+repr(operator_sha)+'\nhelper_sha='+repr(helper_sha)+'\n'+'''import hashlib,json,os,re,stat,subprocess
from pathlib import Path
folder=Path(folder);info=folder.lstat()
assert folder.parent==Path('/run') and re.fullmatch('serverless-update-journal-code-[0-9a-f]{32}',folder.name)
assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700
assert hashlib.sha256((folder/'operator.py').read_bytes()).hexdigest()==operator_sha
assert hashlib.sha256((folder/'control_database.py').read_bytes()).hexdigest()==helper_sha
names=['LoadState','ActiveState','SubState','MainPID','ControlPID','ControlGroup','Result','ExecMainCode','ExecMainStatus']
command=subprocess.run(['systemctl','show',folder.name+'.service',*['--property='+name for name in names]],capture_output=True,text=True,timeout=5)
state=dict(line.split('=',1) for line in command.stdout.splitlines())
assert command.returncode==0 or (state.get('LoadState')=='not-found' and state.get('ActiveState')=='inactive')
files={}
for name in ('identity.json','unit-apply.json','unit-finalize.json','success.json','primary-failure.json','finalization.json','final-backup.json'):
 path=folder/name
 if path.exists():
  info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<262144
  files[name]=json.loads(path.read_text())
group=state.get('ControlGroup') or files.get('unit-apply.json',{}).get('ControlGroup') or files.get('unit-finalize.json',{}).get('ControlGroup')
members=None;group_exists=None
if group:
 assert group.startswith('/') and '..' not in Path(group).parts
 path=Path('/sys/fs/cgroup')/group.lstrip('/');group_exists=path.exists()
 members=sorted({int(value) for entry in path.rglob('cgroup.procs') for value in entry.read_text().split()}) if group_exists else []
print(json.dumps({'unit':folder.name,'state':state,'files':files,'cgroup':group,'cgroup_exists':group_exists,'cgroup_members':members}))
'''
    return json.loads(remote(['python3','-B','-'],input=program,timeout=10))


def main():
    assert len(sys.argv) in (2,3),'private_built_image_receipt_required'
    profile=sys.argv[2] if len(sys.argv)==3 else 'purge-rollback'
    assert profile in ('purge-rollback','journal-focus','maintenance-diagnostics')
    proof=Path(sys.argv[1]).resolve();assert proof.is_relative_to(ROOT/'.local/e2e') and proof.is_file() and not proof.is_symlink()
    built=json.loads(proof.read_text());assert built['kind']=='static-image-inspection-not-e2e' and built['inspection_container_removed']
    image=built['image'];assert re.fullmatch('sha256:[0-9a-f]{64}',image)
    manifest=built['inspection']
    for name,digest in manifest['backend'].items():assert sha(ROOT/name)==digest,'image_source_changed_since_build'
    operator=ROOT/'e2e/execution-journal-deploy.py';helper=ROOT/'e2e/control_database.py'
    operator_sha=sha(operator);helper_sha=sha(helper)
    report=ROOT/'.local/e2e'/('execution-journal-code-update-'+uuid4().hex+'.json')
    result={'completed':False,'update_profile':profile,'stage':'prepare-intent','image':image,'built_receipt':str(proof),'built_receipt_sha256':sha(proof),
        'operator_sha256':operator_sha,'database_helper_sha256':helper_sha,'observations':[],'database_restored':False}
    save(report,result)
    try:
        # The remote original must match before creating frozen copies or backups.
        check='import hashlib;from pathlib import Path;assert hashlib.sha256(Path("/srv/p2enjoy-serverless/e2e/execution-journal-deploy.py").read_bytes()).hexdigest()=='+repr(operator_sha)+';assert hashlib.sha256(Path("/srv/p2enjoy-serverless/e2e/control_database.py").read_bytes()).hexdigest()=='+repr(helper_sha)
        remote(['python3','-B','-c',check])
        prepared=json.loads(remote(['python3','-B','/srv/p2enjoy-serverless/e2e/execution-journal-deploy.py',{'journal-focus':'prepare-ui-update','maintenance-diagnostics':'prepare-diagnostics-update'}.get(profile,'prepare-update'),image],input=json.dumps(manifest),timeout=100))
        assert prepared['prepared'] and prepared['completed'] and prepared['mode']=='code-update' and prepared['update_profile']==profile;result['preparation']=prepared
        folder=prepared['folder'];unit=prepared['unit'];assert folder=='/run/'+unit and re.fullmatch('serverless-update-journal-code-[0-9a-f]{32}',unit)
        command=['systemd-run','--quiet','--service-type=exec','--unit='+unit,
            '--property=User=root','--property=Group=root','--property=Restart=no','--property=RemainAfterExit=no',
            '--property=KillMode=control-group','--property=KillSignal=SIGKILL','--property=SendSIGKILL=yes',
            '--property=RuntimeMaxSec=140s','--property=TimeoutStopSec=200s',
            '--property=StandardOutput=journal','--property=StandardError=journal',
            '--property=ExecStopPost=/usr/bin/python3 -I '+folder+'/operator.py finalize '+folder,
            '/usr/bin/python3','-I',folder+'/operator.py','apply',folder]
        result.update(stage='launch-intent',unit=unit,folder=folder,launch_arguments=command);save(report,result)
        # No --pipe/--pty/--wait/--collect: terminal lifetime does not own the
        # service, and its primary result stays observable until it is collected.
        try:remote(command,timeout=15);result['launch_acknowledged']=True
        except (subprocess.SubprocessError,OSError) as error:
            result['launch_acknowledged']=False;result['launch_error_type']=type(error).__name__
        result['stage']='observing-same-unit';save(report,result)
        deadline=time.monotonic()+600
        while True:
            assert time.monotonic()<deadline,'supervised_deployment_observation_deadline'
            observed=observe(folder,operator_sha,helper_sha)
            state=observed['state'];files=observed['files']
            result['observations'].append({'at_ns':time.time_ns(),'state':state,'cgroup_members':observed['cgroup_members'],
                'primary_success_seen':'success.json' in files,'finalization_seen':'finalization.json' in files})
            result['last_observed']=observed;save(report,result)
            terminal=state.get('ActiveState') in ('inactive','failed') and state.get('MainPID','0')=='0' and state.get('ControlPID','0')=='0'
            if terminal:
                assert state.get('ActiveState')=='inactive' and state.get('Result')=='success','deployment_unit_did_not_exit_successfully'
                assert observed['cgroup_members']==[],'deployment_cgroup_not_joined'
                assert 'finalization.json' in files,'deployment_finalization_receipt_missing'
                final=files['finalization.json'];assert final['completed'],'deployment_finalization_failed'
                success=files.get('success.json');assert success and success['completed'],'primary_deployment_did_not_succeed'
                assert final['service_result']=='success' and final['exit_code']=='exited' and final['exit_status']=='0','primary_service_failed_before_finalization'
                assert final['control']==success['control'] and final['control']['image']==image
                assert success['snapshot']['versions'][-1]=='011_execution_logs.sql' and len(success['snapshot']['versions'])==11
                result.update(completed=True,stage='joined',control=success['control'],finalization=final,
                    cgroup_joined=True,unit_inactive=True,migration_applied=False,code_updated=True);save(report,result);break
            time.sleep(1)
        print(json.dumps({'completed':True,'report':str(report),'unit':unit,'control':result['control'],
            'backup':prepared['initial_backup'],'cgroup_joined':True,'database_restored':False}))
    except BaseException as error:
        result.update(failure_type=type(error).__name__,failure_message_sha256=hashlib.sha256(str(error).encode()).hexdigest())
        save(report,result)
        print(json.dumps({'completed':False,'report':str(report),'unit':result.get('unit'),'stage':result['stage'],'failure_type':type(error).__name__}))
        raise


if __name__=='__main__':main()
