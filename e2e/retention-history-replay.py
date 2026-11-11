# @spec docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md
# @verifies docs/BACKLOG.md#sls-078 | docs/RETENTION_HISTORY_REPLAY.md#sources-exactes-et-exclusivité
"""Verify authentic sealed retention witnesses before an exclusive DEV replay."""
import argparse
from contextlib import closing
import fcntl
import importlib.util
import shutil
import subprocess
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import sqlite3
import stat
import time
from uuid import UUID

ROOT = Path('/srv/p2enjoy-serverless')
HISTORY = ROOT / 'qualification-history'
SOURCE_ID = 'schedule-retention-9a2a4cd1eb134c20b4e1c5a1a1bdc7c0'
TERMINAL_ID = 'schedule-terminal-history-a3993b7d64f14650933cf03960c3d3b0'
CALL_FIELDS = 'id,function_id,revision_id,instance_id,state,error_code,http_status,handler_started,created_at,completed_at,logs,trigger,resolved_code_hash,schedule_firing_id,schedule_slot'
EVIDENCE = {SOURCE_ID: 'schedule-retention-capture-dev-2026-11-11.json',
            TERMINAL_ID: 'schedule-terminal-history-capture-dev-2026-11-11.json'}


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def protected_file(path, legacy_json=False):
    info = path.lstat()
    assert path.resolve() == path and stat.S_ISREG(info.st_mode), 'canonical_regular_file_required'
    permitted = {(0, 0o400)}
    if legacy_json:
        permitted.add((0, 0o600))
    assert (info.st_uid, stat.S_IMODE(info.st_mode)) in permitted, 'protected_source_file_required'


def immutable(path):
    protected_file(path)
    assert all(not os.path.lexists(str(path) + suffix) for suffix in ('-wal', '-shm', '-journal')), 'sealed_sidecar_present'
    db = sqlite3.connect('file:' + str(path) + '?mode=ro&immutable=1', uri=True, isolation_level=None)
    db.row_factory = sqlite3.Row
    return db


def inventory(directory):
    assert directory.resolve() == directory and directory.is_dir()
    result = {}
    for path in sorted(directory.rglob('*')):
        info = path.lstat()
        assert stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'unexpected_artifact_type'
        if stat.S_ISREG(info.st_mode):
            result[str(path.relative_to(directory))] = {'sha256': sha(path), 'bytes': info.st_size,
                                                       'mode': stat.S_IMODE(info.st_mode)}
    return result


def matching(db, table, witness):
    assert table in ('functions', 'schedule_generations', 'schedule_firings', 'invocations')
    assert 'id' in witness and all(re.fullmatch('[a-z_]+', key) for key in witness)
    found = db.execute('SELECT ' + ','.join(witness) + ' FROM ' + table + ' WHERE id=?', (witness['id'],)).fetchone()
    assert found and dict(found) == witness, 'captured_witness_changed:' + table
    return dict(found)


def verify_capture(identifier):
    assert identifier in EVIDENCE, 'canonical_retention_capture_required'
    folder = HISTORY / identifier
    info = folder.lstat()
    assert folder.resolve() == folder and stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700, 'private_capture_required'
    legacy = identifier == SOURCE_ID
    for name in ('capture.json', 'artifacts.json'):
        protected_file(folder / name, legacy_json=legacy)
    receipt = json.loads((folder / 'capture.json').read_text())
    public_path = ROOT / 'docs/evidence' / EVIDENCE[identifier]
    public = json.loads(public_path.read_text())
    if legacy:
        assert public['capture_qualified'] and public['checkpoint']['completed']
        expected = [v for v in public['checkpoint']['report']['events'] if v.get('event') == 'retention-captured']
        assert expected == [receipt], 'canonical_capture_receipt_required'
        preservation_path = folder / 'preservation.json'
        protected_file(preservation_path)
        preservation = json.loads(preservation_path.read_text())
        assert preservation == public['native_preservation'] and preservation['completed'], 'canonical_preservation_required'
        images = preservation['images']
        image_capture_id = identifier
        eligible_after = receipt['eligible_after']
        earliest_eligible = min(receipt['invocation']['completed_at'], receipt['http_witness']['completed_at']) + 604801
    else:
        assert public['completed'] and public['receipt'] == receipt and receipt['completed'], 'canonical_capture_receipt_required'
        images, image_capture_id = receipt['images'], receipt['image_capture_id']
        eligible_after = receipt['all_eligible_after']
        earliest_eligible = min(value for group in receipt['eligible_after'].values() for value in group.values())
    assert receipt['capture_id'] == identifier and receipt['source_read_only'] and receipt['dates_unchanged']
    assert sha(folder / 'control.sqlite3') == receipt['backup_sha256']
    assert sha(folder / 'registry.sqlite3') == receipt['registry_sha256']
    artifact_inventory = json.loads((folder / 'artifacts.json').read_text())
    assert inventory(folder / 'artifacts') == artifact_inventory
    assert len(artifact_inventory) == receipt['artifact_files']
    assert hashlib.sha256(json.dumps(artifact_inventory, sort_keys=True).encode()).hexdigest() == receipt['artifact_inventory_sha256']
    inspection_path = ROOT / 'docs/evidence/schedule-retention-source-inspection-dev-2026-11-11.json'
    inspection = json.loads(inspection_path.read_text())
    rows = [v for v in inspection['captures'] if v['capture_id'] == identifier]
    assert inspection['inspection_complete'] and len(rows) == 1
    measured = rows[0]
    with closing(immutable(folder / 'control.sqlite3')) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        installation = db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
        assert str(UUID(installation)) == installation == measured['installation_id']
        assert installation == inspection['original_installation'] and measured['same_as_original']
        for table, expected in measured['counts'].items():
            assert re.fullmatch('[a-z_]+', table)
            assert db.execute('SELECT count(*) FROM ' + table).fetchone()[0] == expected, 'captured_table_count_changed'
        namespaces = [dict(v) for v in db.execute('SELECT id,name FROM namespaces WHERE deleted_at IS NULL ORDER BY id')]
        functions = [dict(v) for v in db.execute('SELECT id,name FROM functions WHERE deleted_at IS NULL ORDER BY id')]
        assert namespaces == sorted(measured['live_namespaces'], key=lambda v: v['id'])
        assert functions == sorted(measured['live_functions'], key=lambda v: v['id'])
        assert db.execute('SELECT count(*) FROM invocations WHERE completed_at IS NULL').fetchone()[0] == 0
        assert db.execute('SELECT coalesce(sum(reserved_bytes),0) FROM deployments').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM function_operations').fetchone()[0] == 0
        cursor = db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
        assert cursor == measured['cursor']
        instances = [dict(v) for v in db.execute('SELECT id,function_id,state FROM execution_instances ORDER BY id')]
        assert instances == sorted(measured['instances'], key=lambda v: v['id'])
        if legacy:
            fire = matching(db, 'schedule_firings', receipt['firing'])
            call = matching(db, 'invocations', receipt['invocation'])
            http = matching(db, 'invocations', receipt['http_witness'])
            assert fire['state'] == 'dispatched' and fire['completed_at'] is None
            assert call['state'] == http['state'] == 'succeeded' and call['handler_started'] and http['handler_started']
            assert fire['invocation_id'] == call['id'] and call['schedule_firing_id'] == fire['id']
            assert call['resolved_code_hash'] == fire['code_hash'] and call['trigger'] == 'schedule'
            assert functions == [{'id': fire['function_id'], 'name': 'protected-source-and-expiring-http'}]
            assert {v['name'] for v in namespaces} == {'lelabs', 'scheduled-functions-e190a449'}
            generation = dict(db.execute('SELECT * FROM schedule_generations WHERE id=?', (fire['generation_id'],)).fetchone())
            assert generation['retired_at'] is None and generation['function_id'] == functions[0]['id']
            witnesses = {'firings': [fire], 'invocations': [call, http], 'generations': [generation]}
            revision = generation['revision_id']
        else:
            witnesses = {key: [matching(db, table, row) for row in receipt['witnesses'][key]] for key, table in
                         [('functions', 'functions'), ('generations', 'schedule_generations'),
                          ('firings', 'schedule_firings'), ('invocations', 'invocations')]}
            assert not functions and not instances and {v['name'] for v in namespaces} == {'lelabs'}
            assert len(witnesses['generations']) == 2 and all(v['retired_at'] for v in witnesses['generations'])
            assert len(witnesses['firings']) == len(witnesses['invocations']) == 1
            fire = witnesses['firings'][0]
            revision = next(v['revision_id'] for v in witnesses['generations'] if v['id'] == fire['generation_id'])
        assert db.execute('SELECT image_id FROM revisions WHERE id=?', (revision,)).fetchone()[0] == images['runtime']['image']
        call_ids = [v['id'] for v in witnesses['invocations']]
        target_calls = [dict(v) for v in db.execute('SELECT ' + CALL_FIELDS + ' FROM invocations WHERE id IN (' + ','.join('?' for _ in call_ids) + ') ORDER BY id', call_ids)]
        latest_call = db.execute('SELECT coalesce(max(created_at),0) FROM invocations').fetchone()[0]
        if legacy:
            config = json.loads(db.execute('SELECT config_json FROM functions WHERE id=?',(functions[0]['id'],)).fetchone()[0])
            assert config['min_instances'] == 0 and not config['storage']['data']['enabled'] and not config['storage']['cache']['enabled']
    with closing(immutable(folder / 'registry.sqlite3')) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        tables = [v[0] for v in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        assert set(tables) == set(measured['registry_counts'])
        for table in tables:
            assert re.fullmatch('[a-z_]+', table)
            assert db.execute('SELECT count(*) FROM ' + table).fetchone()[0] == measured['registry_counts'][table]
        for table in ('volumes', 'leases', 'probes'):
            assert db.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0, 'source_registry_not_quiet'
        assert db.execute('SELECT count(*) FROM functions WHERE pending_json IS NOT NULL').fetchone()[0] == 0
    assert image_capture_id == SOURCE_ID
    image_folder = HISTORY / image_capture_id
    image_info = image_folder.lstat()
    assert image_folder.resolve() == image_folder and image_info.st_uid == 0 and stat.S_IMODE(image_info.st_mode) == 0o700
    for role, image in images.items():
        assert role in ('control', 'runtime') and re.fullmatch('sha256:[a-f0-9]{64}', image['image'])
        archive = image_folder / (role + '-image.tar')
        protected_file(archive)
        assert archive.stat().st_size == image['bytes'] and sha(archive) == image['archive_sha256']
    return {'capture_id': identifier, 'kind': 'source' if legacy else 'terminal',
            'receipt_sha256': sha(folder / 'capture.json'), 'public_evidence_sha256': sha(public_path),
            'inspection_evidence_sha256': sha(inspection_path), 'control_sha256': receipt['backup_sha256'],
            'registry_sha256': receipt['registry_sha256'], 'artifact_inventory_sha256': receipt['artifact_inventory_sha256'],
            'artifact_files': len(artifact_inventory), 'images': images, 'image_capture_id': image_capture_id,
            'installation_id': installation, 'namespaces': namespaces, 'live_functions': functions,
            'instances': instances, 'cursor': cursor, 'witnesses': witnesses,
            'target_calls': target_calls, 'latest_invocation_created_at': latest_call,
            'earliest_eligible_after': earliest_eligible, 'eligible_after': eligible_after}


def timing(source, mode):
    now = time.time()
    if mode == 'age':
        assert now >= source['eligible_after'], 'age_replay_not_yet_eligible'
    elif mode == 'preflight':
        assert now < source['earliest_eligible_after'] - 60, 'young_preflight_no_longer_eligible'
    else:
        assert mode in ('seed-loss', 'observer-loss'), 'unknown_retention_observation'
    return int(now // 300) * 300


def atomic(path, value):
    pending = path.with_suffix('.pending')
    with open(pending, 'w', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


def window(campaign, fd):
    assert str(UUID(campaign)) == campaign
    work = HISTORY / ('instance-limit-' + campaign)
    info = work.lstat()
    assert work.resolve() == work and stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o750
    item = json.loads((work / 'restore.json').read_text())
    assert item['campaign'] == campaign and item['mode'] == 'instance-limit' and item.get('retention_replay') and not item.get('restored')
    assert info.st_gid == item['gid']
    lock = os.fstat(fd)
    assert [lock.st_dev,lock.st_ino] == item['lock_identity'] and lock.st_uid == 0 and stat.S_IMODE(lock.st_mode) == 0o600
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source = verify_capture(item['retention_replay']['source']['capture_id'])
    assert source == item['retention_replay']['source'], 'capture_changed_since_preflight'
    spec = importlib.util.spec_from_file_location('retention_window',ROOT/'e2e/storage-legacy-environment.py')
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.retention_clone_context(item,source['installation_id'])
    return work,item,source,helper


def kill_pair(item,path,receipt):
    receipt.update(fault_signal='SIGKILL',driver_killed=True)
    pid = item['driver_pid']
    status = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
    assert status[19] == item['driver_birth'] and status[0] != 'Z', 'driver_identity_changed'
    atomic(path,receipt)
    descriptor = os.pidfd_open(pid)
    try:
        current = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        assert current[19] == item['driver_birth'] and current[0] != 'Z', 'driver_identity_changed_after_pin'
        signal.pidfd_send_signal(descriptor,signal.SIGKILL)
    finally:os.close(descriptor)
    os.kill(os.getpid(),signal.SIGKILL)


def seed(campaign,fd):
    work,item,source,helper = window(campaign,fd)
    timing(source,item['retention_replay']['mode'])
    helper.no_cloned_consumers(item)
    folder = HISTORY/source['capture_id']
    state = Path(item['paths']['state'])
    assert not (state/'control.sqlite3').exists() and not (state/'artifacts').exists()
    artifacts = state/'artifacts'
    shutil.copytree(folder/'artifacts',artifacts,copy_function=shutil.copy2)
    for path in [artifacts,*artifacts.rglob('*')]:os.chown(path,item['uid'],item['gid'],follow_symlinks=False)
    assert inventory(artifacts) == json.loads((folder/'artifacts.json').read_text())
    def publish(name,target,expected):
        assert not target.exists()
        pending = target.with_suffix('.retention-pending')
        with (folder/name).open('rb') as original,pending.open('xb') as output:
            shutil.copyfileobj(original,output)
            output.flush();os.fsync(output.fileno())
            os.fchmod(output.fileno(),0o600);os.fchown(output.fileno(),item['uid'],item['gid'])
        assert sha(pending) == expected
        pending.replace(target)
        parent = os.open(target.parent,os.O_DIRECTORY)
        try:os.fsync(parent)
        finally:os.close(parent)
    registry = Path(item['paths']['storage'])/'registry.sqlite3'
    publish('registry.sqlite3',registry,source['registry_sha256'])
    receipt = {'completed':False,'capture_id':source['capture_id'],'inherited_guard_lock':True,
               'artifacts_verified':True,'registry_published':True,'control_published':False}
    target = work/'retention-replay-seed.json';atomic(target,receipt)
    if item['retention_replay']['mode'] == 'seed-loss':kill_pair(item,target,receipt)
    publish('control.sqlite3',state/'control.sqlite3',source['control_sha256'])
    receipt.update(completed=True,control_published=True)
    atomic(target,receipt)
    return receipt


def read_state(reader,source):
    ids = [v['id'] for v in source['target_calls']]
    calls = reader.rows('SELECT '+CALL_FIELDS+' FROM invocations WHERE id IN ('+','.join('?' for _ in ids)+') ORDER BY id',ids)
    fires = [reader.rows('SELECT * FROM schedule_firings WHERE id=?',(v['id'],)) for v in source['witnesses']['firings']]
    generations = [reader.rows('SELECT * FROM schedule_generations WHERE id=?',(v['id'],)) for v in source['witnesses']['generations']]
    unexpected = reader.rows('SELECT id,function_id,created_at FROM invocations WHERE created_at>?',(source['latest_invocation_created_at'],))
    assert not unexpected, 'new_invocation_during_retention_replay'
    return {'invocations':calls,'firings':[row for values in fires for row in values],
            'generations':[row for values in generations for row in values],
            'instances':reader.rows('SELECT id,function_id,state FROM execution_instances ORDER BY id'),
            'cursor':reader.rows('SELECT window_at FROM schedule_cursor WHERE singleton=1')[0]['window_at'],
            'new_invocations':0}


def observe(campaign,fd):
    from control_database import ControlObserver
    from schedule_firing_volume_replay import BlockingNativeObserver
    work,item,source,helper = window(campaign,fd)
    mode = item['retention_replay']['mode']
    boundary = timing(source,mode)
    assert boundary == item['retention_replay']['armed_boundary'], 'retention_boundary_changed_since_arm'
    assert 10 <= item['retention_replay']['armed_at']-boundary <= 60
    assert time.time() < boundary+90, 'retention_start_margin_expired'
    helper.no_cloned_consumers(item)
    reader = ControlObserver(Path(item['paths']['state'])/'control.sqlite3')
    observer = None
    receipt = {'completed':False,'mode':mode,'capture_id':source['capture_id'],
               'start_boundary':boundary,'inherited_guard_lock':True}
    target = work/'retention-replay-observation.json'
    try:
        reader.open()
        # This copy is committed before any application process starts.
        initial = read_state(reader,source)
        assert initial['invocations'] == source['target_calls']
        assert initial['firings'] == source['witnesses']['firings']
        assert initial['generations'] == source['witnesses']['generations']
        receipt['before_start'] = initial
        atomic(target,receipt)
        helper.docker(item,'compose','--env-file','/etc/spark/env','--env-file','/run/spark/secrets',
                      '-f',str(work/'compose.yml'),'up','-d','--no-build')
        row = json.loads(helper.docker(item,'inspect',helper.temporary_control_name(item)))[0]
        assert row['State']['Running'] and row['Image'] == source['images']['control']['image']
        assert row['Config']['Labels']['com.docker.compose.project'] == item['project']
        init = row['State']['Pid'];find_deadline = time.monotonic()+3
        while True:
            descendants = [init]
            try:
                for parent in descendants:
                    descendants.extend(int(v) for v in Path('/proc',str(parent),'task',str(parent),'children').read_text().split())
                processes = [p for p in descendants if Path(os.readlink(f'/proc/{p}/exe')).name.startswith('python') and
                             Path('/proc',str(p),'cmdline').read_bytes().startswith(b'python\0-B\0-m\0uvicorn\0app.main:app\0')]
            except (FileNotFoundError,ProcessLookupError):processes=[]
            assert len(processes)<=1,'unique_control_process_required'
            if processes:break
            assert time.monotonic()<find_deadline,'control_process_missing'
            time.sleep(.01)
        pid = processes[0]
        cgroup = Path('/proc',str(pid),'cgroup').read_text()
        assert cgroup == Path('/proc',str(init),'cgroup').read_text()
        birth = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
        observer = BlockingNativeObserver(pid);observer.start()
        assert Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19] == birth
        receipt.update(container_id=row['Id'],image=row['Image'],pid=pid,birth=birth,
                       cgroup_sha256=hashlib.sha256(cgroup.encode()).hexdigest(),observer_attached=True,native_stop=observer.stopped)
        atomic(target,receipt)
        if mode == 'observer-loss':kill_pair(item,target,receipt)
        deadline = time.monotonic()+25
        pending = None;protected = None
        def accepted(value):
            nonlocal protected
            if source['kind'] == 'terminal':
                if mode == 'preflight':
                    return (not value['instances'] and value['invocations']==source['target_calls'] and
                            value['firings']==source['witnesses']['firings'] and value['generations']==source['witnesses']['generations'])
                return not any(value[key] for key in ('invocations','firings','generations','instances'))
            fire = value['firings'][0] if len(value['firings'])==1 else None
            assert fire and fire['id']==source['witnesses']['firings'][0]['id'],'source_firing_missing'
            assert not value['instances'], 'captured_instance_not_recovered'
            original = source['witnesses']['firings'][0]
            call_id = original['invocation_id']
            if mode == 'preflight':
                assert value['invocations']==source['target_calls'],'young_target_invocations_changed'
                return fire['state']=='succeeded' and fire['completed_at'] is not None
            if protected is None:
                if fire['completed_at'] is not None:raise AssertionError('source_closed_before_protected_age_frontier')
                calls = value['invocations']
                if len(calls)==1 and calls[0]['id']==call_id:
                    assert calls[0]==next(v for v in source['target_calls'] if v['id']==call_id)
                    assert fire==original,'protected_firing_changed'
                    protected=value;receipt['protected']=value;atomic(target,receipt)
                return False
            return not value['invocations'] and fire['state']=='succeeded' and fire['completed_at'] is not None
        # Recovery may not have removed the ready line at the first native stop.
        first = read_state(reader,source);receipt['initial_stop']=first
        if not first['instances'] and accepted(first):
            final=first
        else:
            observer.resume()
            while True:
                stopped=observer.wait(deadline)
                if stopped != signal.SIGTRAP|0x80:
                    assert stopped not in (signal.SIGSTOP,signal.SIGTRAP)
                    observer.resume(stopped);continue
                phase,data=observer.info()
                if phase==1:pending=data[0]
                if pending in (3,72,75) and phase in (1,2):
                    value=read_state(reader,source)
                    if not value['instances'] and accepted(value):
                        final=value;break
                observer.resume()
        if source['kind']=='source':
            fire=final['firings'][0]
            assert boundary <= fire['completed_at'] <= time.time(), 'firing_close_date_not_real'
            assert {k:v for k,v in fire.items() if k not in ('state','error_code','completed_at')} == {k:v for k,v in source['witnesses']['firings'][0].items() if k not in ('state','error_code','completed_at')}
        assert time.time()<boundary+110 and time.monotonic()<deadline,'retention_observation_deadline'
        receipt.update(completed=True,final=final,age_retention_qualified=mode=='age',
                       observation_seconds=25-(deadline-time.monotonic()))
        atomic(target,receipt)
        return receipt
    finally:
        if observer:observer.detach()
        reader.close()


def inspect_replay(campaign,fd):
    from control_database import ControlObserver
    _,item,source,helper=window(campaign,fd)
    helper.retention_scope(item)
    reader=ControlObserver(Path(item['paths']['state'])/'control.sqlite3')
    try:
        reader.open();return read_state(reader,source)
    finally:reader.close()


def main():
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['verify','seed','observe','inspect'])
    parser.add_argument('identifier')
    parser.add_argument('--lock-fd',type=int)
    args = parser.parse_args()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('retention_replay_deadline')))
    signal.alarm(35)
    try:
        if args.operation=='verify':value=verify_capture(args.identifier)
        else:
            assert args.lock_fd is not None
            value={'seed':seed,'observe':observe,'inspect':inspect_replay}[args.operation](args.identifier,args.lock_fd)
        print(json.dumps(value))
    except BaseException as error:
        print(json.dumps({'completed': False, 'failure_type': type(error).__name__,
                          'reason': str(error) if isinstance(error, AssertionError) else None}))
        raise SystemExit(1)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
