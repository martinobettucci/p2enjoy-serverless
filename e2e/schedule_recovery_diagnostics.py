# @spec docs/BACKLOG.md#sls-145 | docs/SCHEDULE_RECOVERY.md#diagnostic-de-la-barrière-non-reçue--sls-145
# @verifies docs/BACKLOG.md#sls-145 | docs/SCHEDULE_RECOVERY.md#diagnostic-de-la-barrière-non-reçue--sls-145
"""Owned DEV recovery diagnostics; no application buffers or environment reads."""
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import socket
import stat
import struct
import sys
import time
import traceback
from uuid import UUID

VERSION = 1
STATE_SIZE = 4096
MAGIC = 0x534C534449414731
FIELDS = (
    'phase', 'phase_started_ns', 'updated_ns', 'acquisition_started_ns',
    'acquisition_deadline_ns', 'wait_calls', 'wait_returns', 'last_wait_signal',
    'last_wait_finished_ns', 'info_calls', 'last_syscall_phase',
    'last_syscall_number', 'candidate_calls', 'checkpoint_calls',
    'checkpoint_revision', 'checkpoint_finished_ns', 'cursor_read_calls',
    'cursor_read_last_ns', 'cursor_read_total_ns', 'firings_read_calls',
    'firings_read_last_ns', 'firings_read_total_ns', 'invocations_read_calls',
    'invocations_read_last_ns', 'invocations_read_total_ns', 'durable_calls',
    'durable_last_ns', 'durable_total_ns', 'primary_recorded',
    'finalization_recorded', 'diagnostic_errors',
    'guard_arm_started_ns', 'guard_arm_finished_ns', 'guard_arm_started_wall_ns',
    'guard_arm_finished_wall_ns', 'waiting_window_started_ns',
    'waiting_window_started_wall_ns', 'attach_started_ns', 'attach_started_wall_ns',
    'attach_finished_ns', 'attach_finished_wall_ns',
)
PHASES = (
    'initializing', 'guard_armed', 'waiting_window', 'attach', 'attached',
    'watchdog_wait', 'watchdog_loss', 'acquisition', 'wait', 'info',
    'cursor_read', 'firings_read', 'invocations_read', 'predicate',
    'durable', 'emit', 'waiting_command', 'cut', 'detach', 'restore',
    'guard_finish', 'reader_close', 'lock_close', 'done',
)
VALUES = struct.Struct('<' + 'q' * len(FIELDS))
CHECKPOINT_DIGEST_OFFSET = 2048
NAMES = ('recovery-diagnostic-manifest.json', 'recovery-diagnostic-state.bin',
         'recovery-diagnostic-checkpoint.json', 'recovery-diagnostic-primary.json',
         'recovery-diagnostic-finalization.json', 'recovery-diagnostic-issues.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def process_identity(pid):
    root = Path('/proc', str(pid))
    parts = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'birth': parts[19], 'state': parts[0],
            'cgroup': (root / 'cgroup').read_text(),
            'cpu_user_ticks': int(parts[11]), 'cpu_system_ticks': int(parts[12])}


def host_identity():
    info = os.stat('/proc/self/ns/pid')
    return {'pid_namespace': {'device': info.st_dev, 'inode': info.st_ino},
            'boot_id_sha256': sha(Path('/proc/sys/kernel/random/boot_id').read_bytes())}


def exception_metadata(error):
    frames = traceback.extract_tb(error.__traceback__)[-16:]
    number = getattr(error, 'errno', None)
    return {'type': type(error).__name__, 'message_sha256': sha(str(error).encode()),
            'errno': number if isinstance(number, int) else None,
            'frames': [{'file': Path(f.filename).name[:256], 'line': f.lineno,
                        'function': f.name[:256]} for f in frames]}


def checked_folder(folder, function_id, namespace_id):
    folder = Path(folder)
    assert folder.parent == Path('/run')
    assert re.fullmatch('serverless-restore-schedule-[0-9a-f]{32}', folder.name)
    info = folder.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0
    assert stat.S_IMODE(info.st_mode) == 0o700
    identity = json.loads((folder / 'identity.json').read_bytes())
    assert identity['function_id'] == str(UUID(function_id))
    assert identity['namespace_id'] == str(UUID(namespace_id))
    return identity


class RecoveryDiagnostics:
    """A sequence-protected shared page and bounded, coarse JSON records."""
    def __init__(self, folder, identity):
        self.folder = Path(folder)
        assert checked_folder(folder, identity['function_id'], identity['namespace_id']) == identity
        assert identity['helper_pid'] == os.getpid()
        assert process_identity(os.getpid())['birth'] == identity['helper_birth']
        self.values = dict.fromkeys(FIELDS, 0)
        self.values.update(last_wait_signal=-1, last_syscall_phase=-1, last_syscall_number=-1)
        self.sequence = 0
        self.last_checkpoint = None
        self.finalization = []
        self.issues = []
        self.mapping = None
        self.fd = None
        assert all(not (self.folder / name).exists() for name in NAMES)
        try:
            self.fd = os.open(self.folder / NAMES[1], os.O_RDWR | os.O_CREAT |
                              os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.ftruncate(self.fd, STATE_SIZE)
            self.mapping = mmap.mmap(self.fd, STATE_SIZE, access=mmap.ACCESS_WRITE)
            struct.pack_into('<QQ', self.mapping, 0, MAGIC, 0)
            manifest = {'version': VERSION, 'state_bytes': STATE_SIZE,
                        'value_format': VALUES.format, 'fields': FIELDS, 'phases': PHASES,
                        'checkpoint_digest_offset': CHECKPOINT_DIGEST_OFFSET,
                        'function_id': identity['function_id'],
                        'namespace_id': identity['namespace_id'],
                        'writer': process_identity(os.getpid()),
                        'control': {'pid': identity['pid'], 'birth': identity['birth'],
                                    'cgroup': identity['cgroup']},
                        'operator_sha256': identity['operator_sha256'],
                        'diagnostic_program_sha256': sha(Path(__file__).read_bytes()),
                        'created_at_ns': time.time_ns(), 'created_monotonic_ns': time.monotonic_ns(),
                        **host_identity()}
            _, complete = self._atomic_json(NAMES[0], manifest, 16 * 1024)
            assert complete, 'diagnostic_manifest_capacity'
            self.phase('initializing')
        except BaseException:
            self.close()
            raise

    def _atomic_json(self, name, value, limit):
        raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
        complete = len(raw) <= limit
        if not complete:
            value = {'observation_complete': False, 'reason': 'diagnostic_capacity',
                     'original_bytes': len(raw), 'original_sha256': sha(raw),
                     'revision': value.get('revision') if isinstance(value, dict) else None}
            raw = (json.dumps(value, sort_keys=True) + '\n').encode()
        pending = self.folder / (name + '.pending')
        descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fchmod(stream.fileno(), 0o600)
        pending.replace(self.folder / name)
        if not complete:
            self.update(diagnostic_errors=self.values['diagnostic_errors'] + 1)
        return raw, complete

    def update(self, checkpoint_digest=None, **changes):
        assert self.mapping is not None, 'diagnostic_writer_closed'
        assert set(changes) <= set(FIELDS)
        self.values.update(changes)
        self.values['updated_ns'] = time.monotonic_ns()
        self.sequence += 1
        struct.pack_into('<Q', self.mapping, 8, self.sequence)
        VALUES.pack_into(self.mapping, 16, *(self.values[name] for name in FIELDS))
        if checkpoint_digest is not None:
            assert len(checkpoint_digest) == 32
            self.mapping[CHECKPOINT_DIGEST_OFFSET:CHECKPOINT_DIGEST_OFFSET + 32] = checkpoint_digest
        self.sequence += 1
        struct.pack_into('<Q', self.mapping, 8, self.sequence)

    def phase(self, name):
        assert name in PHASES, 'unknown_recovery_diagnostic_phase'
        instant = time.monotonic_ns()
        first_transition = {'waiting_window': 'waiting_window_started',
                            'attach': 'attach_started', 'attached': 'attach_finished'}.get(name)
        values = {'phase': PHASES.index(name), 'phase_started_ns': instant}
        if first_transition is not None and not self.values[first_transition + '_ns']:
            values.update({first_transition + '_ns': instant,
                           first_transition + '_wall_ns': time.time_ns()})
        self.update(**values)

    def count(self, name):
        self.update(**{name: self.values[name] + 1})

    def duration(self, name, started_ns):
        elapsed = time.monotonic_ns() - started_ns
        self.update(**{name + '_calls': self.values[name + '_calls'] + 1,
                       name + '_last_ns': elapsed,
                       name + '_total_ns': self.values[name + '_total_ns'] + elapsed})

    def checkpoint(self, value):
        self.count('checkpoint_calls')
        if value == self.last_checkpoint:
            return
        revision = self.values['checkpoint_revision'] + 1
        data = {'observation_complete': True, 'revision': revision,
                'observed_monotonic_ns': time.monotonic_ns(), 'checkpoint': value}
        try:
            raw, complete = self._atomic_json(NAMES[2], data, 64 * 1024)
            self.update(checkpoint_digest=hashlib.sha256(raw).digest(),
                        checkpoint_revision=revision,
                        checkpoint_finished_ns=data['observed_monotonic_ns'])
            if complete:
                self.last_checkpoint = value
        except BaseException as error:
            self.issue('checkpoint_write', error)

    def issue(self, stage, error):
        """Keep an observation failure separate from the original exception."""
        try:
            self.update(diagnostic_errors=self.values['diagnostic_errors'] + 1)
        except BaseException:
            pass  # The original exception must survive a broken diagnostic writer.
        entry = {'stage': stage, 'monotonic_ns': time.monotonic_ns(),
                 'error': exception_metadata(error)}
        self.issues.append(entry)
        self.issues = self.issues[-16:]
        try:
            self._atomic_json(NAMES[5], {'issues': self.issues[-16:]}, 16 * 1024)
        except BaseException:
            try:
                os.write(2, (json.dumps({'event': 'diagnostic_write_failed', **entry}) + '\n').encode())
            except OSError:
                pass  # No successful observation is claimed when both channels are lost.

    def primary(self, error):
        value = {'observation_complete': True, 'monotonic_ns': time.monotonic_ns(),
                 'phase': PHASES[self.values['phase']], 'error': exception_metadata(error)}
        try:
            _, complete = self._atomic_json(NAMES[3], value, 16 * 1024)
            self.update(primary_recorded=int(complete))
        except BaseException as failure:
            self.issue('primary_write', failure)

    def finalizing(self, stage, state, error=None):
        value = {'stage': stage, 'state': state, 'monotonic_ns': time.monotonic_ns()}
        if error is not None:
            value['error'] = exception_metadata(error)
        self.finalization.append(value)
        try:
            _, complete = self._atomic_json(NAMES[4], {'events': self.finalization[-16:]}, 16 * 1024)
            self.update(finalization_recorded=int(complete))
        except BaseException as failure:
            self.issue('finalization_write', failure)

    def close(self):
        if self.mapping is not None:
            mapping, self.mapping = self.mapping, None
            mapping.close()
        if self.fd is not None:
            descriptor, self.fd = self.fd, None
            os.close(descriptor)


def _bounded_json(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    info = os.fstat(descriptor)
    if not (stat.S_ISREG(info.st_mode) and info.st_uid == 0 and
            stat.S_IMODE(info.st_mode) == 0o600):
        os.close(descriptor)
        raise AssertionError('diagnostic_file_ownership')
    with os.fdopen(descriptor, 'rb') as stream:
        raw = stream.read(limit + 1)
    assert len(raw) <= limit, 'diagnostic_file_outside_limit'
    return {'sha256': sha(raw), 'bytes': len(raw), 'value': json.loads(raw)}


def _process_metadata(expected):
    try:
        current = process_identity(expected['pid'])
    except (FileNotFoundError, ProcessLookupError):
        return {'birth_ended': True, 'current': None}
    if current['birth'] != expected['birth']:
        return {'birth_ended': True, 'current': current}
    root = Path('/proc', str(expected['pid']))
    details = {}
    for name in ('wchan', 'syscall', 'status'):
        try:
            with (root / name).open('rb') as stream:
                raw = stream.read(8193)
            assert len(raw) <= 8192, 'process_metadata_outside_limit'
            value = raw.decode()
            if name == 'status':
                allowed = {'State', 'PPid', 'TracerPid', 'Uid', 'Gid', 'Threads', 'VmRSS',
                           'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches'}
                parsed = {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
                          for line in value.splitlines() if ':' in line}
                value = {key: parsed[key] for key in allowed if key in parsed}
            elif name == 'syscall':
                words = value.split()
                value = {'state': 'running'} if words == ['running'] else {'number': int(words[0])}
            details[name] = {'available': True, 'value': value, 'raw_sha256': sha(raw)}
        except (OSError, ValueError, IndexError, AssertionError) as error:
            details[name] = {'available': False, 'error': exception_metadata(error)}
    try:
        after = process_identity(expected['pid'])
        identity_still_equal = after['birth'] == expected['birth']
    except (FileNotFoundError, ProcessLookupError):
        identity_still_equal = False
    return {'birth_ended': current['state'] == 'Z', 'current': current,
            'identity_still_equal_after_read': identity_still_equal, 'metadata': details}


def read_guard_diagnostics(folder, function_id, namespace_id):
    assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
    folder = Path(folder)
    identity = checked_folder(folder, function_id, namespace_id)
    manifest = _bounded_json(folder / NAMES[0], 16 * 1024)
    value = manifest['value']
    assert value['version'] == VERSION and value['state_bytes'] == STATE_SIZE
    assert value['fields'] == list(FIELDS) and value['phases'] == list(PHASES)
    assert value['value_format'] == VALUES.format
    assert value['diagnostic_program_sha256'] == identity['recovery_diagnostics_sha256'] == sha(Path(__file__).read_bytes())
    assert value['operator_sha256'] == identity['operator_sha256']
    assert value['writer']['pid'] == identity['helper_pid'] and value['writer']['birth'] == identity['helper_birth']
    assert value['function_id'] == function_id and value['namespace_id'] == namespace_id
    assert {key: value[key] for key in ('pid_namespace', 'boot_id_sha256')} == host_identity()
    state_path = folder / NAMES[1]
    descriptor = os.open(state_path, os.O_RDONLY | os.O_NOFOLLOW)
    decoded = None
    try:
        info = os.fstat(descriptor)
        assert (info.st_size == STATE_SIZE and stat.S_ISREG(info.st_mode) and
                info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o600)
        with mmap.mmap(descriptor, STATE_SIZE, access=mmap.ACCESS_READ) as shared:
            for attempt in range(3):
                magic, before = struct.unpack_from('<QQ', shared, 0)
                payload = VALUES.unpack_from(shared, 16)
                digest = bytes(shared[CHECKPOINT_DIGEST_OFFSET:CHECKPOINT_DIGEST_OFFSET + 32])
                after = struct.unpack_from('<Q', shared, 8)[0]
                if magic == MAGIC and before == after and not before % 2:
                    decoded = dict(zip(FIELDS, payload, strict=True))
                    break
                if attempt < 2:
                    time.sleep(.001)
    finally:
        os.close(descriptor)
    result = {'version': VERSION, 'read_only': True, 'manifest': manifest,
              'sampled_at_ns': time.time_ns(), 'sampled_monotonic_ns': time.monotonic_ns(),
              'sequence_consistent': decoded is not None, 'state': decoded,
              'helper': _process_metadata(value['writer']),
              'control': _process_metadata(value['control']), 'files': {}}
    if decoded is not None:
        assert 0 <= decoded['phase'] < len(PHASES)
        result['phase'] = PHASES[decoded['phase']]
    for name, limit in ((NAMES[2], 64 * 1024), (NAMES[3], 16 * 1024),
                        (NAMES[4], 16 * 1024), (NAMES[5], 16 * 1024)):
        path = folder / name
        if path.exists():
            result['files'][name] = _bounded_json(path, limit)
    checkpoint_ok = decoded is not None
    if decoded is not None and decoded['checkpoint_revision']:
        item = result['files'].get(NAMES[2])
        checkpoint_ok = bool(item and item['sha256'] == digest.hex() and
                             item['value'].get('revision') == decoded['checkpoint_revision'] and
                             item['value'].get('observation_complete'))
    result['checkpoint_consistent'] = checkpoint_ok
    result['observation_complete'] = bool(decoded is not None and checkpoint_ok and
                                         decoded['diagnostic_errors'] == 0 and NAMES[5] not in result['files'])
    return result


def transport_nanoseconds(value):
    """Preserve native integer timestamps through JavaScript JSON consumers."""
    if isinstance(value, dict):
        return {key: str(item) if key.endswith('_ns') and isinstance(item, int)
                else transport_nanoseconds(item) for key, item in value.items()}
    if isinstance(value, list):
        return [transport_nanoseconds(item) for item in value]
    return value


if __name__ == '__main__':
    assert len(sys.argv) == 4, 'function_namespace_guard_arguments_required'
    function_id, namespace_id, unit = sys.argv[1:]
    assert re.fullmatch('serverless-restore-schedule-[0-9a-f]{32}', unit)
    result = read_guard_diagnostics(Path('/run') / unit, function_id, namespace_id)
    result['nanoseconds_encoding'] = 'decimal-string'
    print(json.dumps(transport_nanoseconds(result)))
