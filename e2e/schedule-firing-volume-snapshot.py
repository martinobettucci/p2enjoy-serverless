# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation
# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_CAPTURE_INTERRUPTION.md
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_CAPTURE_INTERRUPTION.md#éprouver-lattente-réelle-de-la-garde
"""Native RO capture of the first real window, inside an existing DEV guard."""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import time
import traceback
from uuid import UUID

from control_database import control_owner, read_control

ROOT = Path('/srv/p2enjoy-serverless')
DOCKER = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host',
          'unix:///run/user/1001/docker.sock']


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(folder):
    found = {}
    for path in sorted(folder.rglob('*')):
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode), 'artifact_type'
        if stat.S_ISREG(info.st_mode):
            found[str(path.relative_to(folder))] = {
                'sha256': sha(path), 'bytes': info.st_size,
                'mode': stat.S_IMODE(info.st_mode)}
    return found


def docker(*args):
    return subprocess.check_output(DOCKER + list(args), text=True, timeout=20)


def services(item):
    names = [item['original']['id'], 'serverless-api-instance-limit',
             'serverless-runtime-reference']
    rows = json.loads(docker('inspect', *names))
    found = [{'id': v['Id'], 'image': v['Image'],
              'running': v['State']['Running'], 'started_at': v['State']['StartedAt'],
              'health': v['State'].get('Health', {}).get('Status')} for v in rows]
    assert not found[0]['running'], 'original_control_running'
    assert all(v['running'] and v['health'] == 'healthy' for v in found[1:])
    assert found[0]['image'] == found[1]['image'] == item['historical_image']
    running = set(docker('ps', '-q', '--no-trunc').split())
    assert running == {v['id'] for v in found[1:]}, 'unexpected_running_container'
    return found


def identity(path):
    info = path.lstat()
    assert stat.S_ISDIR(info.st_mode)
    return {'device': info.st_dev, 'inode': info.st_ino, 'uid': info.st_uid,
            'gid': info.st_gid, 'mode': stat.S_IMODE(info.st_mode)}


def witnesses(db, ids, window, namespace_name, installation):
    def rows(sql, args=()):
        return [dict(v) for v in db.execute(sql, args)]
    namespace = rows('SELECT id,name FROM namespaces WHERE deleted_at IS NULL')
    assert len(namespace) == 1 and namespace[0]['name'] == namespace_name
    assert db.execute('SELECT count(*) FROM services WHERE deleted_at IS NULL').fetchone()[0] == 1
    functions = rows('SELECT id,name,active_revision_id,config_json FROM functions ORDER BY id')
    assert {v['id'] for v in functions} == set(ids) and len(functions) == 16
    assert db.execute('SELECT count(*) FROM functions WHERE deleted_at IS NOT NULL').fetchone()[0] == 0
    assert {v['name'] for v in functions} == {'firing-retention-%02d' % v for v in range(1, 17)}
    for fn in functions:
        config = json.loads(fn['config_json'])
        assert (config['cpu'], config['memory_mib'], config['min_instances'],
                config['max_instances'], config['concurrency'], config['idle_seconds'],
                config['timeout_seconds']) == (.05, 128, 0, 1, 1, 0, 60)
        assert config['storage']['concurrency'] == 'shared'
        assert not config['storage']['data']['enabled'] and not config['storage']['cache']['enabled']
    for query in ["SELECT count(*) FROM invocations WHERE completed_at IS NULL",
                  'SELECT count(*) FROM execution_instances',
                  'SELECT count(*) FROM function_operations',
                  'SELECT coalesce(sum(reserved_bytes),0) FROM deployments']:
        assert db.execute(query).fetchone()[0] == 0, 'installation_not_quiet'
    assert db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0] == installation
    cursor = db.execute('SELECT window_at FROM schedule_cursor WHERE singleton=1').fetchone()[0]
    assert cursor == window, 'capture_cursor_changed'
    generations = rows('SELECT * FROM schedule_generations ORDER BY id')
    assert len(generations) == 16 and {v['function_id'] for v in generations} == set(ids)
    by_function = {v['id']: v for v in functions}
    for gen in generations:
        assert gen['retired_at'] is None and window - 300 < gen['activated_at'] < window
        assert gen['revision_id'] == by_function[gen['function_id']]['active_revision_id']
        declarations = json.loads(gen['events_json'])['schedules']
        assert len(declarations) == 16
        assert all(v == {'cron': '*/5 * * * *', 'enabled': True, 'timezone': 'UTC'} for v in declarations)
    firings = rows('SELECT * FROM schedule_firings ORDER BY id')
    assert len(firings) == 256
    assert Counter(v['function_id'] for v in firings) == Counter({v: 16 for v in ids})
    assert Counter(v['state'] for v in firings) == Counter(succeeded=2, refused_capacity=254)
    generation_by_id = {v['id']: v for v in generations}
    for fn in functions:
        assert {v['schedule_index'] for v in firings if v['function_id'] == fn['id']} == set(range(16))
    for firing in firings:
        gen = generation_by_id[firing['generation_id']]
        assert (firing['function_id'], firing['code_hash']) == (gen['function_id'], gen['code_hash'])
        assert firing['origin'] == 'manifest' and firing['expression'] == '*/5 * * * *'
        assert firing['window_at'] == firing['nominal_at'] == window and firing['coalesced'] == 1
        assert firing['completed_at'] >= firing['claimed_at'] >= window
        if firing['state'] == 'refused_capacity':
            assert firing['error_code'] == 'schedule_capacity' and firing['invocation_id'] is None
        else:
            assert firing['error_code'] is None and firing['invocation_id']
    calls = rows('''SELECT id,function_id,revision_id,resolved_code_hash,state,error_code,
        http_status,handler_started,instance_id,completed_at,logs,trigger,
        schedule_firing_id,schedule_expression,schedule_origin,schedule_slot
        FROM invocations ORDER BY id''')
    assert len(calls) == 2 and len({v['function_id'] for v in calls}) == 2
    fires_by_call = {v['invocation_id']: v for v in firings if v['invocation_id']}
    for call in calls:
        firing = fires_by_call[call['id']]
        assert call['state'] == 'succeeded' and call['handler_started'] and call['http_status'] == 200
        assert call['error_code'] is None and call['instance_id'] and call['completed_at'] >= window
        assert call['function_id'] == firing['function_id'] and call['schedule_firing_id'] == firing['id']
        assert call['resolved_code_hash'] == firing['code_hash']
        assert call['trigger'] == 'schedule' and call['schedule_slot'] == window
        logged = [json.loads(line) for line in call['logs'].splitlines() if line]
        completed = [v for v in logged if v.get('event') == 'completed']
        assert len(completed) == 1
        value = completed[0]
        assert value['id'] == call['id'] and value['trigger'] == 'schedule'
        assert value['method'] == 'POST' and value['path'] == '/' and value['body'] == {}
        assert value['authorization_present'] is False
        assert datetime.fromisoformat(value['slot'].replace('Z', '+00:00')).timestamp() == window
    runtime_images = rows('SELECT DISTINCT image_id FROM revisions WHERE id IN (SELECT revision_id FROM schedule_generations)')
    assert len(runtime_images) == 1
    return {'namespace': namespace[0], 'installation_id': installation, 'cursor': cursor,
            'functions': functions, 'generations': generations, 'firings': firings,
            'invocations': calls, 'runtime_image': runtime_images[0]['image_id']}



def process_identity(pid):
    fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'birth': fields[19], 'state': fields[0],
            'parent': int(fields[1])}


def same_process(expected, stopped=False):
    current = process_identity(expected['pid'])
    assert current['birth'] == expected['birth'], 'process_birth_changed'
    assert current['state'] != 'Z', 'process_already_dead'
    if stopped:
        assert current['state'] == 'T', 'copier_not_stopped'
    return current


def durable_point(folder, value):
    path = folder / 'copy-interruption.json'
    pending = folder / 'copy-interruption.pending'
    with pending.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)
    fd = os.open(folder, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def stop_during_backup(folder, item, live, args, remaining, total):
    assert remaining > 0 and total > remaining, 'partial_backup_required'
    copier = process_identity(os.getpid())
    wrapper = process_identity(os.getppid())
    wrapper_argv = Path('/proc', str(wrapper['pid']), 'cmdline').read_bytes().split(b'\0')[:-1]
    assert wrapper_argv[:4] == [b'timeout', b'--foreground', b'--signal=KILL', b'40s'], 'bounded_wrapper_required'
    assert wrapper['parent'] == item['driver_pid'], 'wrapper_driver_mismatch'
    durable_point(folder, {'campaign': args.campaign, 'window': args.window,
        'point': 'control-backup', 'created_at': time.time(),
        'created_monotonic': time.monotonic(), 'remaining': remaining, 'total': total,
        'output_directory': identity(folder), 'copier': copier, 'wrapper': wrapper,
        'lock_fd': args.lock_fd, 'lock_identity': item['lock_identity'],
        'witnesses_sha256': hashlib.sha256(json.dumps(live, sort_keys=True).encode()).hexdigest(),
        'firings': len(live['firings']), 'invocations': len(live['invocations']),
        'generations': len(live['generations'])})
    os.kill(os.getpid(), signal.SIGSTOP)
    raise AssertionError('interrupted_copier_must_never_resume')



def sealed_capture_state(campaign):
    history = ROOT / 'qualification-history'
    evidence = json.loads((ROOT / 'docs/evidence/schedule-firing-volume-capture-dev-2026-11-11.json').read_text())
    canonical = evidence['receipt']['capture_id']
    assert re.fullmatch('schedule-firing-volume-[a-f0-9]{32}', canonical)
    result = {}
    for identifier in (canonical, 'schedule-firing-volume-' + campaign.replace('-', '')):
        folder = history / identifier
        info = identity(folder)
        assert info['uid'] == 0 and info['mode'] == 0o700
        receipt = json.loads((folder / 'capture.json').read_text())
        assert receipt['completed'] and receipt['capture_id'] == identifier
        if identifier == canonical:
            assert receipt == evidence['receipt'], 'canonical_receipt_changed'
        files = {}
        for name in ('capture.json', 'control.sqlite3', 'registry.sqlite3', 'artifacts.json'):
            path = folder / name
            meta = path.lstat()
            assert stat.S_ISREG(meta.st_mode) and meta.st_uid == 0 and stat.S_IMODE(meta.st_mode) == 0o400
            files[name] = {'sha256': sha(path), 'bytes': meta.st_size, 'inode': meta.st_ino}
        assert files['control.sqlite3']['sha256'] == receipt['backup_sha256']
        assert files['registry.sqlite3']['sha256'] == receipt['registry_sha256']
        artifacts = json.loads((folder / 'artifacts.json').read_text())
        assert inventory(folder / 'artifacts') == artifacts
        result[identifier] = {'directory': info, 'files': files,
            'artifact_inventory_sha256': hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest(),
            'eligible_after': receipt['eligible_after']}
    return result


def loss_action(args):
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
    assert str(UUID(args.campaign)) == args.campaign
    work = ROOT / 'qualification-history' / ('instance-limit-' + args.campaign)
    journal = work / 'restore.json'
    item = json.loads(journal.read_text())
    assert item['mode'] == 'instance-limit' and item['campaign'] == args.campaign
    assert item['work'] == str(work) and item['guard_seconds'] == 900
    folder = ROOT / 'qualification-history' / ('schedule-firing-capture-interrupted-' + args.campaign.replace('-', ''))
    point_path = folder / 'copy-interruption.json'
    if args.action == 'sealed-state':
        meta = identity(folder)
        assert meta['uid'] == 0 and meta['mode'] == 0o700 and folder.resolve() == folder
        assert not any((folder / name).exists() for name in ('capture.json', 'registry.sqlite3', 'artifacts'))
        files = {}
        for path in folder.iterdir():
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o400
            files[path.name] = {'sha256': sha(path), 'bytes': info.st_size,
                                'device': info.st_dev, 'inode': info.st_ino}
        return {'completed': True, 'sealed_captures': sealed_capture_state(args.campaign), 'partial_files': files}
    if args.action == 'loss-point':
        deadline = time.monotonic() + 10
        while not point_path.exists():
            assert time.monotonic() < deadline, 'copy_point_missing'
            time.sleep(.05)
    point = json.loads(point_path.read_text())
    assert point['campaign'] == args.campaign and point['point'] == 'control-backup'
    assert point['lock_identity'] == item['lock_identity']
    assert 0 < point['remaining'] < point['total'] and point['firings'] == 256
    assert point['invocations'] == 2 and point['generations'] == 16
    normal = ROOT / 'qualification-history' / ('schedule-firing-volume-' + args.campaign.replace('-', ''))
    normal_receipt = json.loads((normal / 'capture.json').read_text())
    assert point['window'] == normal_receipt['witnesses']['cursor']
    assert point['witnesses_sha256'] == hashlib.sha256(json.dumps(normal_receipt['witnesses'], sort_keys=True).encode()).hexdigest(), 'source_witnesses_changed'
    assert folder.resolve() == folder and point['output_directory']['uid'] == item['uid'] and point['output_directory']['mode'] == 0o700
    assert identity(folder) == point['output_directory'], 'copy_output_replaced'
    assert not any((folder / name).exists() for name in ('capture.json', 'registry.sqlite3', 'artifacts'))

    def driver_dead():
        try:
            row = process_identity(item['driver_pid'])
            return row['birth'] != item['driver_birth'] or row['state'] == 'Z'
        except FileNotFoundError:
            return True

    def sample():
        current = json.loads(journal.read_text())
        assert not current.get('restored') and driver_dead(), 'guard_already_restored_or_driver_alive'
        copier = same_process(point['copier'], stopped=True)
        wrapper = same_process(point['wrapper'])
        assert copier['parent'] == wrapper['pid'], 'copier_parent_changed'
        expected_command = [b'python3', b'-B', str(Path(__file__)).encode()]
        argv = Path('/proc', str(copier['pid']), 'cmdline').read_bytes().split(b'\0')[:-1]
        assert argv[:3] == expected_command and args.campaign.encode() in argv and b'--loss' in argv
        fd_info = Path('/proc', str(copier['pid']), 'fd', str(point['lock_fd'])).stat()
        assert [fd_info.st_dev, fd_info.st_ino] == item['lock_identity']
        lock = os.open('/run/serverless-archive-migration.lock', os.O_RDWR | os.O_NOFOLLOW)
        try:
            info = os.fstat(lock)
            assert [info.st_dev, info.st_ino] == item['lock_identity']
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise AssertionError('inherited_lock_not_held')
        finally:
            os.close(lock)
        assert all(identity(work / ('original-' + key)) == current['original_dirs'][key]
                   and identity(Path(path)) == current['replacement_dirs'][key]
                   for key, path in current['paths'].items()), 'directories_changed_before_join'
        return {'sampled_monotonic': time.monotonic(), 'copier': copier, 'wrapper': wrapper,
                'driver_dead': True, 'restored': False, 'lock_busy': True,
                'originals_preserved': True, 'replacements_preserved': True}

    if args.action == 'loss-point':
        deadline = time.monotonic() + 2
        while same_process(point['copier'])['state'] != 'T':
            assert time.monotonic() < deadline, 'copier_not_stopped'
            time.sleep(.01)
        same_process(point['wrapper'])
        assert not item.get('restored') and not driver_dead()
        return {'completed': True, 'point': point, 'stopped': True, 'sealed_captures': sealed_capture_state(args.campaign)}
    if args.action == 'block-guard':
        first = sample()
        subprocess.run(['systemctl', 'start', '--no-block', item['unit'] + '.service'], check=True, timeout=5)
        started = time.monotonic()
        samples = []
        while True:
            value = sample()
            properties = subprocess.check_output(['systemctl', 'show', item['unit'] + '.service',
                '--property=MainPID,ActiveState,SubState'], text=True, timeout=3)
            properties = dict(line.split('=', 1) for line in properties.splitlines())
            guard_pid = int(properties['MainPID'])
            if guard_pid:
                assert properties['ActiveState'] in ('active', 'activating')
                value['guard'] = process_identity(guard_pid)
                assert value['guard']['state'] != 'Z'
                if samples:
                    assert (value['guard']['pid'], value['guard']['birth']) == (samples[0]['guard']['pid'], samples[0]['guard']['birth']), 'guard_process_changed'
                samples.append(value)
                if value['sampled_monotonic'] - samples[0]['sampled_monotonic'] >= 2:
                    break
            assert time.monotonic() - started < 8, 'guard_not_observed_blocked'
            time.sleep(.1)
        original = json.loads(docker('inspect', item['original']['id']))[0]
        assert not original['State']['Running']
        return {'completed': True, 'trigger': 'explicit-service-start', 'timer_expiry_tested': False,
                'before_start': first, 'samples': samples, 'original_control_stopped': True,
                'blocked_seconds': samples[-1]['sampled_monotonic'] - samples[0]['sampled_monotonic']}
    assert args.action in ('join-copy', 'rescue-copy')
    if args.action == 'join-copy':
        sample()
        assert time.monotonic() - point['created_monotonic'] < 25, 'copy_deadline_margin_lost'
    fds = []
    try:
        for name in ('copier', 'wrapper'):
            expected = point[name]
            fd = os.pidfd_open(expected['pid'])
            fds.append(fd)
            same_process(expected, stopped=name == 'copier')
        wrapper_age = time.clock_gettime(time.CLOCK_BOOTTIME) - int(point['wrapper']['birth']) / os.sysconf('SC_CLK_TCK')
        if args.action == 'join-copy':
            assert 0 <= wrapper_age < 30, 'wrapper_deadline_margin_lost'
        signal.pidfd_send_signal(fds[0], signal.SIGKILL)
        assert select.select([fds[0]], [], [], 8)[0], 'copier_not_joined'
        assert select.select([fds[1]], [], [], 8)[0], 'wrapper_not_joined'
        files = {}
        for path in folder.iterdir():
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode), 'partial_output_type'
            files[path.name] = {'sha256': sha(path), 'bytes': info.st_size,
                                'device': info.st_dev, 'inode': info.st_ino}
            os.chown(path, 0, 0)
            os.chmod(path, 0o400)
        os.chown(folder, 0, 0)
        os.chmod(folder, 0o700)
        return {'completed': True, 'copier_sigkill': True, 'copier_joined': True,
                'wrapper_joined': True, 'wrapper_age_at_sigkill': wrapper_age,
                'wrapper_timeout_seconds': 40, 'partial_files': files, 'capture_complete': False,
                'root_private_directory': True, 'no_completed_capture': True,
                'joined_at_monotonic': time.monotonic(), 'sealed_captures': sealed_capture_state(args.campaign)}
    finally:
        for fd in fds:
            os.close(fd)


def capture(args):
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    assert str(UUID(args.campaign)) == args.campaign
    ids = args.functions.split(',')
    assert len(ids) == len(set(ids)) == 16 and all(str(UUID(v)) == v for v in ids)
    assert args.window > 0 and args.window % 300 == 0
    history = ROOT / 'qualification-history'
    journal = history / ('instance-limit-' + args.campaign) / 'restore.json'
    item = json.loads(journal.read_text())
    assert item['mode'] == 'instance-limit' and item['campaign'] == args.campaign and not item.get('restored')
    assert item['namespace_name'] == 'instance-limit-' + args.campaign[:8]
    lock = os.fstat(args.lock_fd)
    assert [lock.st_dev, lock.st_ino] == item['lock_identity']
    assert stat.S_ISREG(lock.st_mode) and lock.st_uid == 0 and stat.S_IMODE(lock.st_mode) == 0o600
    fcntl.flock(args.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert all(identity(Path(path)) == item['replacement_dirs'][name] for name, path in item['paths'].items())
    assert subprocess.check_output(['systemctl', 'is-active', item['unit'] + '.timer'], text=True).strip() == 'active'
    before_services = services(item)
    official = {name: sha(Path(name)) for name in item['configuration']}
    assert official == item['configuration'], 'official_configuration_changed'
    control = Path(item['paths']['state']) / 'control.sqlite3'
    registry = Path(item['paths']['storage']) / 'registry.sqlite3'
    with read_control(control) as db:
        db.execute('BEGIN')
        live = witnesses(db, ids, args.window, item['namespace_name'], item['temporary_installation'])
    source_proof = ROOT / 'docs/evidence/schedule-retention-capture-dev-2026-11-11.json'
    preservation = json.loads(source_proof.read_text())['native_preservation']
    assert preservation['completed']
    image_capture = history / preservation['capture_id']
    assert re.fullmatch(r'schedule-retention-[a-f0-9]{32}', image_capture.name)
    assert image_capture.is_dir() and not image_capture.is_symlink()
    assert json.loads((image_capture / 'preservation.json').read_text())['images'] == preservation['images']
    assert preservation['images']['control']['image'] == before_services[1]['image']
    assert preservation['images']['runtime']['image'] == live['runtime_image']
    for role, row in preservation['images'].items():
        archive = image_capture / (role + '-image.tar')
        info = archive.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o400
        assert info.st_size == row['bytes'] and sha(archive) == row['archive_sha256']
    prefix = 'schedule-firing-capture-interrupted-' if args.loss else 'schedule-firing-volume-'
    folder = history / (prefix + args.campaign.replace('-', ''))
    folder.mkdir(mode=0o700)
    owner = control.stat()
    os.chown(folder, owner.st_uid, owner.st_gid)
    with read_control(control) as db, closing(sqlite3.connect(folder / 'control.sqlite3')) as target:
        if args.loss:
            db.backup(target, pages=1, progress=lambda status, remaining, total:
                      stop_during_backup(folder, item, live, args, remaining, total) if remaining else None)
            raise AssertionError('partial_backup_not_interrupted')
        db.backup(target)
        target.row_factory = sqlite3.Row
        assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert witnesses(target, ids, args.window, item['namespace_name'], item['temporary_installation']) == live
    with control_owner(control), closing(sqlite3.connect('file:' + str(registry) + '?mode=ro', uri=True)) as db, closing(sqlite3.connect(folder / 'registry.sqlite3')) as target:
        assert db.execute('SELECT count(*) FROM leases').fetchone()[0] == 0
        db.backup(target)
        assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert target.execute('SELECT count(*) FROM leases').fetchone()[0] == 0
    artifacts = Path(item['paths']['state']) / 'artifacts'
    before = inventory(artifacts)
    assert before and shutil.disk_usage(folder).free > 2 * sum(v['bytes'] for v in before.values()) + 1024**3
    shutil.copytree(artifacts, folder / 'artifacts', copy_function=shutil.copy2)
    assert inventory(artifacts) == before == inventory(folder / 'artifacts')
    (folder / 'artifacts.json').write_text(json.dumps(before, sort_keys=True) + '\n')
    with read_control(control) as db:
        db.execute('BEGIN')
        assert witnesses(db, ids, args.window, item['namespace_name'], item['temporary_installation']) == live
    with control_owner(control), closing(sqlite3.connect('file:' + str(registry) + '?mode=ro', uri=True)) as db:
        assert db.execute('SELECT count(*) FROM leases').fetchone()[0] == 0
    assert services(item) == before_services and {name: sha(Path(name)) for name in official} == official
    for name in ['control.sqlite3', 'registry.sqlite3', 'artifacts.json']:
        os.chown(folder / name, 0, 0)
        os.chmod(folder / name, 0o400)
    os.chown(folder, 0, 0)
    os.chmod(folder, 0o700)
    windows = (10000 - len(live['firings'])) // 256 + 1
    receipt = {'completed': True, 'capture_id': folder.name, 'campaign': args.campaign,
               'captured_at': time.time(), 'witnesses': live, 'services': before_services,
               'official_sha256': official, 'source_read_only': True, 'dates_unchanged': True,
               'inherited_guard_lock': True, 'lock_identity': item['lock_identity'],
               'operator_sha256': sha(Path(__file__)),
               'backup_sha256': sha(folder / 'control.sqlite3'),
               'registry_sha256': sha(folder / 'registry.sqlite3'),
               'artifact_inventory_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
               'artifact_files': len(before), 'image_capture_id': image_capture.name,
               'images': preservation['images'], 'image_evidence_sha256': sha(source_proof),
               'initial_firings': len(live['firings']), 'declarations_per_window': 256,
               'required_missed_windows': windows, 'eligible_after': args.window + windows * 300,
               'root_private_directory': True, 'sqlite_read_only': True,
               'count_retention_qualified': False, 'seven_day_retention_qualified': False}
    (folder / 'capture.json').write_text(json.dumps(receipt) + '\n')
    os.chmod(folder / 'capture.json', 0o400)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--action', choices=['capture', 'loss-point', 'block-guard', 'join-copy', 'rescue-copy', 'sealed-state'], default='capture')
    parser.add_argument('--loss', choices=['control-backup'])
    parser.add_argument('--functions')
    parser.add_argument('--window', type=int)
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('native_capture_deadline')))
    signal.alarm(30)
    try:
        assert args.action == 'capture' or not any(v is not None for v in (args.loss, args.functions, args.window, args.lock_fd))
        if args.action == 'capture':
            assert args.functions and args.window and args.lock_fd is not None
        print(json.dumps(capture(args) if args.action == 'capture' else loss_action(args)))
        signal.alarm(0)
    except BaseException as error:
        print(json.dumps({'completed': False, 'failure_type': type(error).__name__,
                          'failure_reason': str(error) if isinstance(error, AssertionError) else None,
                          'errno': getattr(error, 'errno', None),
                          'source_line': traceback.extract_tb(error.__traceback__)[-1].lineno}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
