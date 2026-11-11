# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_FIRING_VOLUME.md#préparation-authentique-et-conservation
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
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import time
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
    folder = history / ('schedule-firing-volume-' + args.campaign.replace('-', ''))
    folder.mkdir(mode=0o700)
    owner = control.stat()
    os.chown(folder, owner.st_uid, owner.st_gid)
    with read_control(control) as db, closing(sqlite3.connect(folder / 'control.sqlite3')) as target:
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
    parser.add_argument('--functions', required=True)
    parser.add_argument('--window', type=int, required=True)
    parser.add_argument('--lock-fd', type=int, required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('native_capture_deadline')))
    signal.alarm(30)
    try:
        print(json.dumps(capture(args)))
        signal.alarm(0)
    except BaseException as error:
        print(json.dumps({'completed': False, 'failure_type': type(error).__name__,
                          'failure_reason': str(error) if isinstance(error, AssertionError) else None}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
