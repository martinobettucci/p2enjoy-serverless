# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#essai-interrompu-et-pilote-durable
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#essai-interrompu-et-pilote-durable
"""Kill the actual local proof worker, then verify its result and DEV restoration."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'.local/e2e'
WORKER=ROOT/'e2e/invocation-source-retention-worker.py'


def main():
    suite=runpy.run_path(str(ROOT/'e2e/execution-suite.py'))
    OUT.mkdir(mode=0o700,parents=True,exist_ok=True)
    target=OUT/('source-retention-worker-loss-'+uuid4().hex+'.json')
    report={'completed':False,'checks':[],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'started_at_ns':time.time_ns()}
    def save():
        pending=target.with_suffix('.pending');pending.write_text(json.dumps(report,indent=2)+'\n');pending.chmod(0o600);pending.replace(target)
    def check(name,action):
        try:action();report['checks'].append({'name':name,'status':'passed'});print('PASS',name,flush=True)
        except BaseException as error:
            report['checks'].append({'name':name,'status':'failed','type':type(error).__name__});raise
        finally:save()
    def until(action,message,seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            value=action()
            if value:return value
            time.sleep(.25)
        raise AssertionError(message)
    def command(*arguments):
        result=subprocess.run([sys.executable,'-B',str(WORKER),*arguments],capture_output=True,text=True,timeout=45)
        assert result.returncode==0,'worker_control_failed'
        return json.loads(result.stdout.strip().split('\n')[-1])
    def remote_status(campaign):
        result=subprocess.run(suite['SSH']+['root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py','status',campaign],capture_output=True,text=True,timeout=45)
        assert result.returncode==0,'remote_worker_window_state_failed'
        return json.loads(result.stdout)
    worker_id=None;campaign=None;folder=None;terminal=None
    save()
    try:
        report['before']=suite['snapshot'](str(target),False,include_adapter=True);save()
        credentials=suite['private_credentials']()
        started=subprocess.run([sys.executable,'-B',str(WORKER),'start'],input=credentials,capture_output=True,timeout=90);credentials=None
        assert started.returncode==0,'worker_start_failed'
        launch=json.loads(started.stdout.strip().splitlines()[-1]);assert launch['started']
        worker_id=launch['worker_id'];folder=OUT/('source-retention-worker-'+worker_id)
        report['launch']=launch;save()
        def launch_and_real_calls():
            observed=command('status',worker_id)
            assert observed['real_process_confirmed'] and observed['controller_ended']
            report['independent_observation']=observed
            last_notice=0
            def produced():
                nonlocal last_notice,campaign
                checkpoint=json.loads((folder/'checkpoint.json').read_text())
                assert not checkpoint.get('finished_at_ns'),'worker_ended_before_fault'
                reports=sorted(OUT.glob('invocation-source-retention-volume-*.json'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
                # The actual client PID belongs to this worker; its new report is created after worker start.
                paths=[p for p in reports if p.stat().st_mtime_ns>=checkpoint['started_at_ns']]
                if paths:
                    value=json.loads(paths[0].read_text())
                    if len(value['responses'])>=2 and len(value['function_ids'])==2:
                        campaign=value['campaign'];report['before_fault_client_report']=value;return True
                if time.monotonic()-last_notice>15:
                    print(json.dumps({'event':'waiting_for_real_source_retention_calls','worker_id':worker_id,'phase':checkpoint['phase']}),flush=True);last_notice=time.monotonic()
                return False
            until(produced,'real_http_calls_missing_before_worker_loss',360)
            report['worker_checkpoint_before_fault']=json.loads((folder/'checkpoint.json').read_text())
        check('Vrai SSO, appels et deux fonctions sous worker indépendant du contrôleur',launch_and_real_calls)
        def actual_loss():
            signalled=subprocess.run(['systemctl','--user','kill','--kill-whom=main','--signal=SIGKILL',launch['unit']],capture_output=True,timeout=15)
            assert signalled.returncode==0,'worker_sigkill_not_sent'
            def ended():
                observed=command('status',worker_id);state=observed['systemd']
                return observed if state.get('MainPID')=='0' and state.get('ActiveState')=='failed' else False
            observed=until(ended,'worker_sigkill_not_terminal',100);state=observed['systemd']
            assert state['Result']=='signal' and state['ExecMainCode']=='2' and state['ExecMainStatus']=='9'
            report['failed_systemd_observation']=observed
            finalized=command('finish',worker_id)
            assert finalized['finalized'] and not finalized['completed'] and finalized['main_process_ended']
            assert finalized['systemd_before_stop']==state
            report['finalization']=finalized
        check('SIGKILL réel et résultat système signal9 finalisé comme échec',actual_loss)
        def restoration():
            nonlocal terminal
            def restored():
                value=remote_status(campaign)
                return value if value['restored'] and not value['driver_alive'] and value['timer_state'] in ('inactive','unknown') and value['service_state'] in ('inactive','unknown') else False
            terminal=until(restored,'remote_window_not_restored_after_worker_loss',180)
            assert all(terminal['restoration'][key] for key in ('directories_identical','databases_identical','artifacts_identical','configuration_unchanged','agent_healthy','control_healthy','reference_unchanged','temporary_directories_removed'))
            cleanup=terminal['consumer_cleanup']
            assert len(cleanup['removed_containers'])==len(cleanup['removed_networks'])==len(cleanup['released_consumers'])==2
            report['remote_terminal_status']=terminal
            after=suite['snapshot'](str(target),False,include_adapter=True);report['after']=after
            assert all(report['before'][key]==after[key] for key in ('source_sha256','image','adapter_images')),'proof_sources_changed'
        check('Deux consommateurs retirés, originaux restitués et sources/images identiques',restoration)
        report['completed']=True
    except BaseException as error:
        report.update(failure_type=type(error).__name__,failure_message_sha256=hashlib.sha256(str(error).encode()).hexdigest())
    finally:
        try:
            if worker_id and terminal is None:
                try:
                    value=command('status',worker_id)
                    if value['systemd'].get('MainPID','0')!='0':
                        subprocess.run(['systemctl','--user','kill','--kill-whom=main','--signal=SIGKILL',launch['unit']],capture_output=True,timeout=15)
                except BaseException as error:report['local_stop_error']=type(error).__name__
                if campaign is None:
                    paths=[p for p in OUT.glob('invocation-source-retention-volume-*.json') if p.stat().st_mtime_ns>=report['started_at_ns']]
                    if len(paths)==1:campaign=json.loads(paths[0].read_text())['campaign']
                if campaign:
                    try:
                        result=subprocess.run(suite['SSH']+['root@10.77.0.24','python3','-B','/srv/p2enjoy-serverless/e2e/storage-legacy-environment.py','restore',campaign],capture_output=True,text=True,timeout=160)
                        report['rescue_exit_code']=result.returncode
                        if result.returncode==0:report['rescue_status']=remote_status(campaign)
                    except BaseException as error:report['remote_rescue_error']=type(error).__name__
                try:report['failed_run_finalization']=command('finish',worker_id)
                except BaseException as error:report['finalization_error']=type(error).__name__
        except BaseException as error:
            report.update(completed=False,cleanup_failure_type=type(error).__name__)
        finally:
            report['finished_at_ns']=time.time_ns();save()
    print(json.dumps({'completed':report['completed'],'groups':len(report['checks']),'worker_id':worker_id,'report':str(target)}),flush=True)
    assert report['completed'],'inspect_worker_loss_failure_before_next_scenario'


if __name__=='__main__':main()
