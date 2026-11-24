# @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
# @spec docs/BACKLOG.md#sls-078 | docs/SCHEDULE_REGRESSIONS.md
# @verifies docs/BACKLOG.md#sls-078 | docs/SCHEDULE_REGRESSIONS.md#rapports-frais-et-conservation
"""DEV proof orchestration only: exact reports, owned archives and native reads."""
import hashlib
import gzip
import json
from pathlib import Path
import re
import shlex
import subprocess
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/e2e'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-J',
       'ubuntu@51.158.54.202', 'root@10.77.0.24']
COUNTS = dict(zip(('schedules', 'schedule-calendar', 'schedule-versions', 'schedule-recovery',
    'schedule-admission', 'schedule-memory-version', 'schedule-queues', 'schedule-unavailable',
    'schedule-instance-reuse', 'schedule-concurrency', 'adapter-schedules', 'schedule-console'),
    (6, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 3), strict=True))
FUNCTION_COUNTS = dict(zip(COUNTS, (3, 3, 3, 1, 5, 3, 9, 1, 2, 2, 2, 2), strict=True))
NO_CLEANUP_FIELD = {'schedules', 'schedule-calendar', 'schedule-versions'}


def report_candidates(name):
    pattern = r'storage-recovery-[0-9a-f]{8}-schedule\.json' if name == 'schedule-unavailable' else r'scheduled-functions-[0-9a-f]{8}\.json'
    return {p for p in OUTPUT.glob('*.json') if re.fullmatch(pattern, p.name)}


def discover_report(name, previous):
    added = report_candidates(name) - previous
    assert len(added) == 1, 'one_new_schedule_report_required:' + name
    path = added.pop()
    assert path.is_file() and not path.is_symlink()
    return str(path.relative_to(ROOT))


def function_ids(report, name):
    ids = report.get('function_ids') or [report['function_id']]
    assert len(ids) == len(set(ids)) == FUNCTION_COUNTS[name]
    assert all(str(UUID(v)) == v for v in ids)
    assert str(UUID(report['namespace_id'])) == report['namespace_id']
    return ids


def verify_report(name, value):
    assert value['completed'] is True and value['skipped'] == 0
    assert len(value['checks']) == COUNTS[name] and all(v['status'] == 'passed' for v in value['checks'])
    assert value['cleanup_errors'] == [] and not value.get('failure')
    function_ids(value, name)
    if name in NO_CLEANUP_FIELD:
        assert 'cleanup' not in value, 'unexpected_schedule_cleanup_contract'
        if name != 'schedules':
            native = value['native_after_purge']
            assert native['completed'] and native['physical']['completed'] and not any(native['counts'].values())
    else:
        assert value['cleanup'] is True
    return COUNTS[name]


class ProofArchive:
    """Retain exact report bytes before overwrite, then each new result and image."""
    # @spec docs/BACKLOG.md#sls-143 | docs/SCHEMA_011_REGRESSIONS.md#négatifs-des-finalisations-du-moniteur--sls-1435
    # @verifies docs/BACKLOG.md#sls-143 | docs/SCHEMA_011_REGRESSIONS.md#négatifs-des-finalisations-du-moniteur--sls-1435
    def __init__(self, purpose='schedules'):
        assert purpose in ('schedules', 'storage-console')
        OUTPUT.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.id = uuid4().hex
        self.path = OUTPUT / (purpose + '-run-' + self.id)
        self.path.mkdir(mode=0o700)
        self.sequence = 0

    def retain(self, name, path, remote, stage, expected_sha256=None):
        assert re.fullmatch('[a-z0-9-]+', name) and stage in ('previous', 'result')
        if remote:
            program = 'from pathlib import Path;import sys;p=Path(' + repr('/srv/p2enjoy-serverless/' + path) + ');sys.stdout.buffer.write(p.read_bytes()) if p.exists() else None'
            raw = subprocess.check_output(SSH + [shlex.join(['python3', '-B', '-c', program])], timeout=60)
            if not raw:
                assert expected_sha256 is None
                return None
        else:
            source = ROOT / path
            if not source.exists():
                assert expected_sha256 is None
                return None
            assert source.is_file() and not source.is_symlink()
            raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if expected_sha256 is not None:
            assert digest == expected_sha256, 'report_changed_before_archive'
        value = json.loads(raw)
        destination = self.path / (f'{self.sequence:03d}-' + name + '-' + stage)
        self.sequence += 1
        destination.mkdir(mode=0o700)
        report_path = destination / 'report.json'
        with report_path.open('xb') as stream:
            stream.write(raw)
        report_path.chmod(0o600)
        captures = {}
        declared_captures = value.get('captures', {})
        if name == 'login-ui':
            declared_captures = {n:None for n in ('login-desktop.png','login-tablette.png','login-mobile.png','login-error.png','login-limit.png','sso-entry.png')}
        for filename, declared in declared_captures.items():
            assert Path(filename).name == filename, 'capture_basename_required'
            source = OUTPUT / filename
            assert source.is_file() and not source.is_symlink(), 'declared_capture_missing'
            image = source.read_bytes()
            expected = declared['sha256'] if isinstance(declared, dict) else declared
            actual = hashlib.sha256(image).hexdigest()
            assert expected is None or actual == expected, 'declared_capture_changed'
            target = destination / filename
            with target.open('xb') as stream:
                stream.write(image)
            target.chmod(0o600)
            captures[filename] = {'path': str(target.relative_to(ROOT)), 'sha256': actual, 'declared_sha256': expected, 'source_mtime_ns': source.stat().st_mtime_ns}
        return {'path': str(report_path.relative_to(ROOT)), 'sha256': digest, 'captures': captures}


def native_state(mapping=None, *, additional_client=None, additional_namespace=None):
    """Check an idle original installation; optional campaign cleanup is read only."""
    assert (additional_client is None) == (additional_namespace is None)
    assert additional_client is None or mapping is not None
    program = 'mapping=' + repr(mapping) + '\nadditional_client=' + repr(additional_client) + '\nadditional_namespace=' + repr(additional_namespace) + '\n' + r'''
import hashlib,json,os,socket,sqlite3,subprocess,sys,time
from pathlib import Path
from contextlib import closing
assert socket.gethostname()=='infra-serverless' and os.geteuid()==0
root=Path('/srv/p2enjoy-serverless');sys.path.insert(0,str(root/'e2e'))
from control_database import read_control,control_owner
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def run(args):return subprocess.check_output(args,text=True,timeout=60)
services=json.loads(run(D+['inspect','serverless-api','serverless-runtime-reference']))
assert all(v['State']['Running'] and v['State']['Health']['Status']=='healthy' for v in services)
assert set(run(D+['ps','-a','--format','{{.Names}}']).splitlines())=={'serverless-api','serverless-runtime-reference'}
assert run(['systemctl','is-active','p2enjoy-storage-dev.service']).strip()=='active'
physical=None
if mapping:
 assert len(mapping)==1
 command=['python3','-B',str(root/'e2e/storage-console-inspect.py'),json.dumps(mapping)]
 if additional_client is not None:command += ['--additional-client',additional_client,'--namespace-name',additional_namespace]
 physical=json.loads(run(command))
 assert physical['completed']
with read_control(root/'state/control.sqlite3') as db:
 counts={n:db.execute(q).fetchone()[0] for n,q in {'live_functions':'SELECT count(*) FROM functions WHERE deleted_at IS NULL','instances':'SELECT count(*) FROM execution_instances','operations':'SELECT count(*) FROM function_operations','active_calls':'SELECT count(*) FROM invocations WHERE completed_at IS NULL','reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments','active_deployments':"SELECT count(*) FROM deployments WHERE state IN ('prepared','receiving','validating')"}.items()}
 integrity=db.execute('PRAGMA integrity_check').fetchone()[0];fk=[list(v) for v in db.execute('PRAGMA foreign_key_check')];migrations=[v[0] for v in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
 if mapping:
  ids=next(iter(mapping.values()));marks=','.join('?' for _ in ids)
  assert not db.execute('SELECT 1 FROM schedule_generations WHERE function_id IN ('+marks+') AND retired_at IS NULL',ids).fetchone()
with control_owner(root/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(root/'storage-state/registry.sqlite3')+'?mode=ro',uri=True)) as db:
 counts['leases']=db.execute('SELECT count(*) FROM leases').fetchone()[0]
 counts['pending_storage']=db.execute('SELECT count(*) FROM functions WHERE pending_json IS NOT NULL').fetchone()[0]
 registry_integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
assert not any(counts.values()) and integrity==registry_integrity=='ok' and not fk
units=run(['systemctl','list-units','--type=service','--type=timer','--state=activating,active','--no-legend','--no-pager'])
assert not any('serverless-restore-' in line for line in units.splitlines())
budgets=json.loads(run(D+['exec','serverless-api','python','-B','-c',"import json;from app.config import Settings;s=Settings.load();print(json.dumps({n:getattr(s,n) for n in ('function_cpu_nanos','function_memory_mib','function_instance_limit','waiting_call_limit','function_waiting_call_limit')}))"]))
assert budgets=={'function_cpu_nanos':1000000000,'function_memory_mib':8192,'function_instance_limit':32,'waiting_call_limit':128,'function_waiting_call_limit':16}
artifacts={str(p.relative_to(root/'state/artifacts')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'state/artifacts').rglob('*')) if p.is_file()}
original={'files':len(artifacts),'manifest_sha256':hashlib.sha256(json.dumps(artifacts,sort_keys=True).encode()).hexdigest()}
assert original=={'files':5982,'manifest_sha256':'846904e1437a034d7fd95488f246cd5b3dc935a4723d20abf9bb419673e5d482'}
print(json.dumps({'completed':True,'sampled_at_ns':time.time_ns(),'counts':counts,'budgets':budgets,'migrations':migrations,'integrity':integrity,'foreign_keys':fk,'registry_integrity':registry_integrity,'physical':physical,'original_artifacts':original,'services':[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt']} for v in services],'official_sha256':{n:hashlib.sha256(Path(n).read_bytes()).hexdigest() if Path(n).exists() else None for n in ['/etc/spark/env','/run/spark/secrets','/etc/spark/routes','/etc/spark/env.?']}}))
'''
    value = json.loads(subprocess.check_output(SSH + ['python3 -B -'], input=program.encode(), timeout=240))
    assert value['migrations'] == [p.name for p in sorted((ROOT / 'control/migrations').glob('*.sql'))]
    return value


def same_installation(before, after):
    for key in ('official_sha256', 'budgets', 'original_artifacts'):
        assert before[key] == after[key], 'schedule_installation_changed:' + key
    assert before['services'][1] == after['services'][1], 'reference_service_changed'
    for key in ('id', 'image'):
        assert before['services'][0][key] == after['services'][0][key], 'original_control_changed'


def retained_retention_proofs():
    """Bind preserved epochs without claiming that their aged witnesses ran again."""
    sources = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in
               ('control/app/schedules.py', 'control/app/execution.py', 'control/app/schedule_calendar.py', 'control/app/execution_logs.py')}
    results = []
    for name in ('schedule-firing-retention-count-schema011-query-dev-2026-11-22.json',
                 'invocation-source-retention-volume-schema011-query-dev-2026-11-22.json',
                 'schedule-retention-age-schema011-query-dev-2026-11-22.json'):
        path = ROOT / 'docs/evidence' / name
        raw = path.read_bytes(); proof = json.loads(raw)
        assert proof['completed'] and proof['image']=='sha256:f016a1b71cb055c4f4c4e2fb2a2622c67c93f7a6ec26b39ec7e663cd9de4c0c7'
        assert all(proof['source_sha256'][n] == digest for n, digest in sources.items())
        compressed_name = proof['raw']['path']
        assert Path(compressed_name).name == compressed_name
        compressed = path.with_name(compressed_name).read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == proof['raw']['sha256']
        digest=hashlib.sha256()
        with gzip.open(path.with_name(compressed_name),'rb') as stream:
            while block:=stream.read(1024*1024):digest.update(block)
        assert digest.hexdigest()==proof['raw']['uncompressed_sha256'],'retention_raw_content_mismatch'
        results.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(),
                        'raw_sha256': proof['raw']['sha256'], 'same_core_sources': sources,
                        'replayed_in_this_scope': False, 'groups_added': 0})
    return results
