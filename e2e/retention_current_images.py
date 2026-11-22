# @spec docs/BACKLOG.md#sls-132 | docs/RETENTION_SCHEMA_011.md#préservation-des-images-avant-la-capture-numérique
# @verifies docs/BACKLOG.md#sls-132 | docs/RETENTION_SCHEMA_011.md#préservation-des-images-avant-la-capture-numérique
"""Preserve immutable DEV retention images without stopping or modifying services."""
import argparse
import ctypes
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import time
import traceback

from control_database import control_owner, read_control

ROOT = Path('/srv/p2enjoy-serverless')
DOCKER = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host',
          'unix:///run/user/1001/docker.sock']
CURRENT_MIGRATIONS = ['001_control.sql', '002_login_limits.sql', '003_deployments.sql',
    '004_function_operations.sql', '005_execution.sql', '006_storage_commands.sql',
    '007_function_code_hash.sql', '008_function_versions.sql', '009_schedules.sql',
    '010_code_drafts.sql', '011_execution_logs.sql']


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            result.update(chunk)
    return result.hexdigest()


def docker(*args):
    return subprocess.check_output(DOCKER + list(args), text=True, timeout=20)


def sealed(path, directory=False):
    info = path.lstat()
    assert path.resolve() == path, 'canonical_image_path_required'
    assert (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    assert info.st_uid == 0 and stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o400)


def synced_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def verify(image, runtime=None):
    assert re.fullmatch('sha256:[a-f0-9]{64}', image), 'immutable_image_required'
    folder = ROOT / 'qualification-history' / ('retention-images-' + image[7:])
    sealed(folder, directory=True)
    path = folder / 'preservation.json'
    sealed(path)
    value = json.loads(path.read_text())
    assert value['completed'] and value['capture_id'] == folder.name
    assert value['images']['control']['image'] == image
    assert set(value['images']) == {'control', 'runtime'}
    if runtime is not None:
        assert value['images']['runtime']['image'] == runtime, 'runtime_image_mismatch'
    assert set(p.name for p in folder.iterdir()) == {'preservation.json', 'control-image.tar', 'runtime-image.tar'}
    for role, row in value['images'].items():
        archive = folder / (role + '-image.tar')
        sealed(archive)
        assert archive.stat().st_size == row['bytes'] and sha(archive) == row['archive_sha256']
        assert docker('image', 'inspect', '--format', '{{.Id}}', row['image']).strip() == row['image']
    return value


def baseline(image):
    settings = {}
    for line in Path('/etc/spark/env').read_text().splitlines():
        fields = shlex.split(line, comments=True)
        if len(fields) == 1 and '=' in fields[0]:
            key, value = fields[0].split('=', 1)
            if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_STORAGE_ROOT_HOST', 'SERVERLESS_RUNTIME_IMAGE'):
                settings[key] = value
    assert len(settings) == 3
    rows = json.loads(docker('inspect', 'serverless-api', 'serverless-runtime-reference'))
    assert all(row['State']['Running'] and row['State']['Health']['Status'] == 'healthy' for row in rows)
    assert rows[0]['Image'] == image
    assert set(docker('ps', '-q', '--no-trunc').split()) == {row['Id'] for row in rows}
    state = Path(settings['SERVERLESS_STATE_HOST_PATH']) / 'control.sqlite3'
    registry = Path(settings['SERVERLESS_STORAGE_ROOT_HOST']) / 'registry.sqlite3'
    with read_control(state) as db:
        versions = [row[0] for row in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
        assert versions == CURRENT_MIGRATIONS, 'current_schema011_required'
        counts = {key: db.execute(sql).fetchone()[0] for key, sql in {
            'live_functions': 'SELECT count(*) FROM functions WHERE deleted_at IS NULL',
            'instances': 'SELECT count(*) FROM execution_instances',
            'active_calls': 'SELECT count(*) FROM invocations WHERE completed_at IS NULL',
            'operations': 'SELECT count(*) FROM function_operations'}.items()}
        assert not any(counts.values()), 'quiet_original_required'
        collection = db.execute('SELECT collection_id FROM execution_log_state WHERE singleton=1').fetchone()[0]
    with control_owner(state), closing(sqlite3.connect('file:' + str(registry) + '?mode=ro', uri=True)) as db:
        assert db.execute('SELECT count(*) FROM leases').fetchone()[0] == 0
    official = {str(path): sha(path) for path in map(Path, ('/etc/spark/env', '/run/spark/secrets', '/etc/spark/routes'))}
    return {'services': [{'id': row['Id'], 'image': row['Image'], 'started_at': row['State']['StartedAt']}
                         for row in rows], 'schema_migrations': versions, 'counts': counts,
            'collection_id': collection, 'official_sha256': official,
            'runtime_image': settings['SERVERLESS_RUNTIME_IMAGE']}


def group_members(group):
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group:
                found.append({'pid': int(path.name), 'birth': fields[19], 'state': fields[0]})
        except (FileNotFoundError, ProcessLookupError):
            continue
    return found


def export_image(identity, stream):
    # Mask the real global alarm before a child can exist. communicate uses its
    # remaining deadline; pending SIGALRM is delivered only after group join.
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
    process = None
    primary = None
    cleanup_error = None
    try:
        remaining_alarm = signal.getitimer(signal.ITIMER_REAL)[0]
        assert remaining_alarm > 0, 'image_preservation_deadline_expired'
        process = subprocess.Popen(['timeout', '--foreground', '--signal=KILL', '40s',
            *DOCKER, 'image', 'save', identity], stdout=stream, stderr=subprocess.PIPE,
            start_new_session=True)
        process.communicate(timeout=min(45, remaining_alarm))
        assert process.returncode == 0, 'image_export_failed'
    except BaseException as error:
        primary = error
    finally:
        try:
            if process is not None:
                deadline = time.monotonic() + 5
                remaining = group_members(process.pid)
                if remaining:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process.poll() is None:
                    process.wait(timeout=max(.001, deadline - time.monotonic()))
                while True:
                    try:
                        waited, _ = os.waitpid(-process.pid, os.WNOHANG)
                        if waited:
                            continue
                    except ChildProcessError:
                        pass
                    if not group_members(process.pid):
                        break
                    assert time.monotonic() < deadline, 'image_export_group_not_joined'
                    time.sleep(.02)
        except BaseException as error:
            cleanup_error = error
        finally:
            if process is not None:
                process.stderr.close()
            try:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            except BaseException as error:
                if primary is None:
                    primary = error
    if cleanup_error is not None:
        raise cleanup_error from primary
    if primary is not None:
        raise primary
    return {'wrapper_exit_code': process.returncode, 'group_joined': True,
            'process_group': process.pid}


def preserve(image):
    assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0, 'export_subreaper_required'
    before = baseline(image)
    folder = ROOT / 'qualification-history' / ('retention-images-' + image[7:])
    if folder.exists():
        result = verify(image, before['runtime_image'])
        assert baseline(image) == before
        return result
    images = {'control': image, 'runtime': before['runtime_image']}
    sizes = []
    for identity in images.values():
        row = json.loads(docker('image', 'inspect', identity))[0]
        assert row['Id'] == identity
        sizes.append(row['Size'])
    assert shutil.disk_usage(folder.parent).free > sum(sizes) * 2 + 1024 ** 3
    folder.mkdir(mode=0o700)
    assert folder.resolve() == folder
    exports = {}
    for role, identity in images.items():
        path = folder / (role + '-image.tar')
        with path.open('xb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            command = export_image(identity, stream)
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(0o400)
        exports[role] = {'image': identity, 'bytes': path.stat().st_size, 'archive_sha256': sha(path),
                         'command': command}
    assert baseline(image) == before, 'original_changed_during_image_preservation'
    receipt = {'completed': True, 'capture_id': folder.name, 'images': exports,
               'operator_sha256': sha(Path(__file__)), 'preserved_at_ns': time.time_ns(),
               'baseline': before, 'no_service_or_configuration_change': True}
    pending = folder / 'preservation.pending'
    with pending.open('x') as stream:
        os.fchmod(stream.fileno(), 0o400)
        json.dump(receipt, stream)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(folder / 'preservation.json')
    synced_directory(folder)
    return verify(image, before['runtime_image'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['preserve', 'verify'])
    parser.add_argument('image')
    args = parser.parse_args()
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless', 'dev_spark_required'
    assert re.fullmatch('sha256:[a-f0-9]{64}', args.image), 'immutable_image_required'
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('image_preservation_deadline')))
    signal.alarm(90)
    try:
        if args.operation == 'preserve':
            result = preserve(args.image)
        else:
            before = baseline(args.image)
            result = verify(args.image, before['runtime_image'])
            assert baseline(args.image) == before, 'original_changed_during_image_verification'
        print(json.dumps(result))
    except BaseException as error:
        print(json.dumps({'completed': False, 'failure_type': type(error).__name__,
                          'reason': str(error) if isinstance(error, AssertionError) else None,
                          'source_line': traceback.extract_tb(error.__traceback__)[-1].lineno}))
        raise SystemExit(1)
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    main()
