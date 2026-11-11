# @spec docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#fermeture-du-lecteur-malgré-une-erreur-native-de-detach
# @verifies docs/BACKLOG.md#sls-078 | docs/INVOCATION_SOURCE_RETENTION_VOLUME.md#fermeture-du-lecteur-malgré-une-erreur-native-de-detach
"""Freeze only the owned temporary control and independently thaw after tracer exit."""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
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
        'actor_source_sha256':sha(frozen),'wrapper_deadline_monotonic':wrapper['deadline_monotonic']}
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


def actor(campaign):
    work,item,helper = context(campaign)
    identity = json.loads((work/'source-observer-deadline-identity.json').read_text())
    assert identity['campaign']==campaign and identity['mode']=='detach-failure'
    assert sha(__file__)==identity['actor_source_sha256']
    assert sha(ROOT/'e2e/invocation-source-retention-observer.py')==identity['operator_source_sha256']
    own = process(os.getpid()); expected=identity['operator']
    assert identity['unit'] in own['cgroup'] and own['cgroup']!=expected['cgroup']
    assert process(expected['pid'])['birth']==expected['birth']
    descriptor = os.pidfd_open(expected['pid'])
    receipt = {'completed':False,'campaign':campaign,'mode':'detach-failure','actor':own,
        'operator':expected,'signals_sent':[],'rescue_used':False}
    try:
        assert process(expected['pid'])['birth']==expected['birth']
        atomic(work/'source-observer-actor-ready.json',dict(receipt,completed=True))
        exited = bool(select.select([descriptor],[],[],15)[0])
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
