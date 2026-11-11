# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#fermeture-du-lecteur-malgré-une-erreur-native-de-detach
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#fermeture-du-lecteur-malgré-une-erreur-native-de-detach
"""Freeze only the owned temporary control and independently thaw after tracer exit."""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path('/srv/p2enjoy-serverless')
sys.path.insert(0, str(ROOT/'e2e'))
from source_observer_deadlines import atomic, command, context, process, same_control, sha, unit_name


def definition(item, identifier):
    return json.loads(command(item['docker']+['inspect', identifier]))[0]


def arm(campaign, receipt, target, observer):
    work, item, helper = context(campaign)
    wrapper = json.loads((work/'source-observer-command.json').read_text())
    assert wrapper['campaign']==campaign and wrapper['mode']=='detach-failure' and wrapper['phase']=='running'
    own = process(os.getpid())
    assert own['parent_pid']==wrapper['wrapper']['pid'] and process(own['parent_pid'])['birth']==wrapper['wrapper']['birth']
    assert Path('/proc/self/cmdline').read_bytes()==b'\0'.join(v.encode() for v in wrapper['argv'][5:])+b'\0'
    control = process(receipt['pid'])
    assert control['birth']==receipt['birth'] and control['tracer_pid']==own['pid'] and observer.stopped
    assert receipt['initial_counts']=={'total':2,'terminal':0} and len(receipt['running'])==2
    assert all(v['state']=='running' and v['handler_started'] and v['completed_at'] is None for v in receipt['running'])
    frozen = work/'source-observer-detach-actor.py'
    shutil.copyfile(__file__, frozen); os.chmod(frozen, 0o600)
    identity = {'campaign':campaign,'mode':'detach-failure','unit':unit_name(campaign),
        'operator':own,'control':control,'container_id':receipt['container_id'],'image':receipt['image'],
        'window':receipt['window'],'function_ids':sorted(v['function_id'] for v in receipt['running']),
        'operator_source_sha256':sha(ROOT/'e2e/invocation-source-retention-observer.py'),
        'actor_source_sha256':sha(frozen),'wait_source_sha256':sha(ROOT/'e2e/schedule_firing_volume_replay.py'),
        'wrapper_deadline_monotonic':wrapper['deadline_monotonic']}
    atomic(work/'source-observer-deadline-identity.json', identity)
    command(['systemd-run','--quiet','--no-block','--unit='+identity['unit'],
        '--property=Type=oneshot','--property=RemainAfterExit=yes','--property=TimeoutStartSec=30',
        '/usr/bin/python3','-B',str(frozen),'actor',campaign])
    end = time.monotonic()+3
    while not (work/'source-observer-actor-ready.json').exists():
        assert time.monotonic()<end, 'detach_actor_not_ready'
        time.sleep(.01)
    ready = json.loads((work/'source-observer-actor-ready.json').read_text())
    assert ready['completed'] and ready['operator']==own and ready['mode']=='detach-failure'
    actor = process(ready['actor']['pid'])
    assert actor['birth']==ready['actor']['birth'] and identity['unit'] in actor['cgroup'] and actor['cgroup']!=own['cgroup']
    identity['actor_ready']=ready; receipt['deadline_fault']=identity; atomic(target,receipt)
    assert wrapper['deadline_monotonic']-time.monotonic()>20, 'detach_setup_margin_exhausted'
    assert same_control(item,helper,identity)['tracer_pid']==own['pid']
    command(item['docker']+['pause', identity['container_id']])
    assert definition(item,identity['container_id'])['State']['Paused']
    receipt['detach_fault_pause']={'paused':True,'monotonic':time.monotonic()}
    observer.resume()
    waited,status = os.waitpid(control['pid'],os.WNOHANG)
    receipt['detach_fault_pending_status']={'pid':waited,'status':status,'monotonic':time.monotonic()}
    if waited:observer.stopped=os.WIFSTOPPED(status)
    atomic(target,receipt)
    assert waited==0, 'detach_stop_already_pending'
    observer.detach_failure_campaign=campaign


def pause_wait(campaign, observer, deadline):
    """Hold this real wait past its caller's real deadline using native signals."""
    entered=time.monotonic()
    work,item,helper=context(campaign)
    identity=json.loads((work/'source-observer-deadline-identity.json').read_text())
    assert identity['campaign']==campaign and identity['mode']=='detach-failure'
    own=process(os.getpid()); assert own['pid']==identity['operator']['pid'] and own['birth']==identity['operator']['birth']
    assert observer.pid==identity['control']['pid'] and observer.attached and not observer.stopped and observer.memory is None
    assert sha(ROOT/'e2e/schedule_firing_volume_replay.py')==identity['wait_source_sha256']
    assert same_control(item,helper,identity)['tracer_pid']==own['pid']
    assert definition(item,identity['container_id'])['State']['Paused']
    assert 0<deadline-entered<=5 and time.monotonic()<deadline, 'detach_wait_gate_deadline_missed'
    gate={'campaign':campaign,'operator':own,'control':identity['control'],'entered_monotonic':entered,
        'deadline_monotonic':deadline,'memory_closed':True,'observer_stopped':False,
        'signal_mask':sorted(int(v) for v in signal.pthread_sigmask(signal.SIG_BLOCK,set())),
        'signal':int(signal.SIGSTOP),'wait_source_sha256':identity['wait_source_sha256']}
    atomic(work/'source-detach-wait-stop.json',gate)
    os.kill(os.getpid(),signal.SIGSTOP)


def actor(campaign):
    work,item,helper = context(campaign)
    identity = json.loads((work/'source-observer-deadline-identity.json').read_text())
    assert identity['campaign']==campaign and identity['mode']=='detach-failure'
    assert sha(__file__)==identity['actor_source_sha256']
    assert sha(ROOT/'e2e/invocation-source-retention-observer.py')==identity['operator_source_sha256']
    assert sha(ROOT/'e2e/schedule_firing_volume_replay.py')==identity['wait_source_sha256']
    own = process(os.getpid()); expected=identity['operator']
    assert identity['unit'] in own['cgroup'] and own['cgroup']!=expected['cgroup']
    assert process(expected['pid'])['birth']==expected['birth']
    descriptor = os.pidfd_open(expected['pid'])
    receipt = {'completed':False,'campaign':campaign,'mode':'detach-failure','actor':own,
        'operator':expected,'signals_sent':[],'rescue_used':False}
    try:
        assert process(expected['pid'])['birth']==expected['birth']
        end=time.monotonic()+15
        atomic(work/'source-observer-actor-ready.json',dict(receipt,completed=True))
        gate_path=work/'source-detach-wait-stop.json'
        while not gate_path.exists():
            assert time.monotonic()<end and not select.select([descriptor],[],[],.01)[0], 'detach_wait_gate_missing'
        gate=json.loads(gate_path.read_text())
        assert gate['campaign']==campaign and gate['operator']['pid']==expected['pid'] and gate['operator']['birth']==expected['birth']
        assert gate['wait_source_sha256']==identity['wait_source_sha256'] and gate['memory_closed'] and not gate['observer_stopped']
        assert 0<gate['deadline_monotonic']-gate['entered_monotonic']<=5 and gate['signal']==int(signal.SIGSTOP)
        while True:
            stopped=process(expected['pid']); assert stopped['birth']==expected['birth']
            if stopped['state']=='T':break
            assert time.monotonic()<end and not select.select([descriptor],[],[],.01)[0], 'detach_operator_not_stopped'
        receipt['wait_gate']=gate;receipt['stopped']=stopped
        resume_at=gate['deadline_monotonic']+.25
        remaining=resume_at-time.monotonic();assert remaining>0 and resume_at<end, 'detach_resume_frontier_missed'
        assert not select.select([descriptor],[],[],remaining)[0], 'detach_operator_exited_before_resume'
        signal.pidfd_send_signal(descriptor,signal.SIGCONT)
        receipt['signals_sent'].append({'signal':int(signal.SIGCONT),'monotonic':time.monotonic(),'pidfd':True})
        atomic(work/'source-observer-actor.json',receipt)
        exited = bool(select.select([descriptor],[],[],max(0,end-time.monotonic()))[0])
        receipt['operator_pidfd_readable']=exited
        receipt['operator_exit_observed_monotonic']=time.monotonic()
        receipt['rescue_used']=not exited
        assert exited, 'detach_operator_not_terminal_before_rescue'
        receipt['control_after_exit']=same_control(item,helper,identity)
        assert receipt['control_after_exit']['tracer_pid']==0, 'detach_tracer_retained_after_operator_exit'
        receipt['paused_after_exit']=definition(item,identity['container_id'])['State']['Paused']
        assert receipt['paused_after_exit'], 'detach_control_thawed_before_operator_exit'
        receipt['completed']=True
    except BaseException as error:
        receipt['failure']={'type':type(error).__name__,'reason':str(error) if isinstance(error,AssertionError) else None}
    finally:
        try:
            if not select.select([descriptor],[],[],0)[0]:
                current=process(expected['pid']);assert current['birth']==expected['birth']
                if current['state']=='T':
                    signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                    receipt['rescue_used']=True;receipt['completed']=False
                    receipt.setdefault('rescue_signals',[]).append({'signal':int(signal.SIGCONT),'pidfd':True,'monotonic':time.monotonic()})
            same_control(item,helper,identity)
            if definition(item,identity['container_id'])['State']['Paused']:
                receipt['thaw_started_monotonic']=time.monotonic()
                command(item['docker']+['unpause',identity['container_id']],timeout=10)
            receipt['paused_after_thaw']=definition(item,identity['container_id'])['State']['Paused']
            receipt['thaw_finished_monotonic']=time.monotonic()
            assert not receipt['paused_after_thaw'], 'detach_control_still_paused'
        except BaseException as error:
            receipt['completed']=False
            receipt['thaw_error']={'type':type(error).__name__,'reason':str(error) if isinstance(error,AssertionError) else None}
        finally:
            os.close(descriptor); receipt['pidfd_closed']=True
            atomic(work/'source-observer-actor.json',receipt)
    print(json.dumps(receipt),flush=True)
    return receipt['completed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('actor',)); parser.add_argument('campaign')
    arguments=parser.parse_args(); raise SystemExit(0 if actor(arguments.campaign) else 1)
