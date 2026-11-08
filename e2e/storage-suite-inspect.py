# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
"""Read-only recoup of the exact public storage campaigns and historical recovery.

All declarations implement this scope. The operator never deletes resources.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/e2e/storage-console-physical.json'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-J', 'ubuntu@51.158.54.202', 'root@10.77.0.24']
NAMES = ('storage-console-api', 'storage-console-ui', 'storage-command-recovery',
         'storage-validation-recovery', 'storage-decision-recovery')


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    OUTPUT.write_text(json.dumps({'completed': False}) + '\n')
    assert sys.argv[1] in ('.local/e2e/storage-console-focused.json', '.local/e2e/storage-console-regressions.json')
    suite = json.loads((ROOT / sys.argv[1]).read_text())
    assert suite['serial'] and not suite['completed'], 'live_suite_checkpoint_required'
    commands = {row['campaign']: row for row in suite['commands']}
    campaigns, reports, historical, temporary_ids = {}, {}, {}, []
    for name in (*NAMES, 'storage-legacy-partial', 'storage-legacy-recovery'):
        row = commands[name]
        assert row['exit_code'] == 0 and row['fresh_report_verified'] and row['report_content_verified']
        path = ROOT / row['report_path']
        assert path == ROOT / ('.local/e2e/' + name + '.json')
        raw = path.read_bytes();digest = hashlib.sha256(raw).hexdigest()
        assert digest == row['after']['report']['sha256'], 'campaign_report_changed'
        report = json.loads(raw)
        assert report['completed'] and report['cleanup'] and not report.get('cleanup_errors')
        reports[name] = {'path': row['report_path'], 'sha256': digest}
        if name not in NAMES:
            restored = [item for item in report['evidence'] if item.get('restored')]
            assert restored and all(item['restoration']['databases_identical'] and item['restoration']['artifacts_identical']
                                    and item['driver_alive'] is False for item in restored), 'historical_restore_unproven'
            historical[name] = {'report_sha256': digest, 'restorations': restored}
            temporary_ids.extend(report['function_ids'])
            continue
        mapping = report.get('campaigns') or {report['namespace_id']: report.get('function_ids') or [report['function_id']]}
        for namespace, functions in mapping.items():
            assert namespace not in campaigns and functions, 'ambiguous_campaign_mapping'
            campaigns[namespace] = functions
    identifiers = [value for values in campaigns.values() for value in values]
    assert len(campaigns) == 6 and len(identifiers) == len(set(identifiers)) == 24
    assert set(identifiers).isdisjoint(temporary_ids), 'historical_ids_in_original_installation'
    command = ['python3', '-B', '/srv/p2enjoy-serverless/e2e/storage-console-inspect.py', json.dumps(campaigns)]
    physical = json.loads(subprocess.check_output(SSH + [shlex.join(command)], timeout=240))
    assert physical['completed'] and not any(physical['global_control_reservations'].values())
    assert physical['global_storage_allocated_bytes'] == 0
    expected = {str(path.relative_to(ROOT / 'control')): hashlib.sha256(path.read_bytes()).hexdigest()
                for directory, pattern in [('app', '*.py'), ('migrations', '*.sql')]
                for path in (ROOT / 'control' / directory).glob(pattern)}
    program = '''import hashlib,json,shlex,socket,subprocess,sys
from pathlib import Path
assert socket.gethostname()=='infra-serverless'
sys.path.insert(0,'/srv/p2enjoy-serverless/e2e')
from control_database import read_control
values={}
for line in Path('/etc/spark/env').read_text().splitlines():
 fields=shlex.split(line,comments=True)
 if len(fields)==1 and '=' in fields[0]:
  key,value=fields[0].split('=',1);values[key]=value
with read_control(Path(values['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3') as db:
 installation=db.execute("SELECT value FROM security_metadata WHERE name='installation-id'").fetchone()[0]
 assert not db.execute('SELECT 1 FROM functions WHERE deleted_at IS NULL').fetchone()
 assert not db.execute('SELECT 1 FROM function_operations').fetchone()
 assert not db.execute("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')").fetchone()
docker=['runuser','-u','spark-docker','--','docker','--host','unix://'+values['SERVERLESS_DOCKER_SOCKET_HOST']]
def run(args):return subprocess.check_output(args,text=True,timeout=45).strip()
assert not run(docker+['ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation])
assert run(['systemctl','is-active','p2enjoy-storage-dev.service'])=='active'
result={'global_active_functions':0,'global_owned_containers_absent':True,'agent_active':True}
for name,key in [('serverless-api','control'),('serverless-runtime-reference','reference')]:
 row=json.loads(run(docker+['inspect',name]))[0]
 assert row['State']['Running'] and row['State']['Health']['Status']=='healthy'
 result[key]={'id':row['Id'],'image':row['Image'],'started_at':row['State']['StartedAt'],'health':'healthy'}
source="from pathlib import Path;import hashlib,json;files=[p for d,e in [('app','*.py'),('migrations','*.sql')] for p in (Path('/app')/d).glob(e)];print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))"
result['embedded_sources']=json.loads(run(docker+['exec','serverless-api','python','-B','-c',source]))
print(json.dumps(result))
'''
    installation = json.loads(subprocess.check_output(SSH + ['python3 -B -'], input=program.encode(), timeout=180))
    assert installation['embedded_sources'] == expected, 'deployed_control_sources_differ'
    assert installation['control']['image'] == physical['control_image']
    value = {'completed': True, 'campaign_count': len(campaigns), 'function_count': len(identifiers),
             'reports': reports, 'physical': physical, 'installation': installation,
             'historical_restoration': historical, 'excluded_historical_function_ids': temporary_ids}
    pending = OUTPUT.with_suffix('.pending');pending.write_text(json.dumps(value, indent=2) + '\n');pending.replace(OUTPUT)
    print(json.dumps({'completed': True, 'namespaces': len(campaigns), 'functions': len(identifiers),
                      'embedded_files': len(expected), 'historical_restorations': len(historical)}))


if __name__ == '__main__':
    main()
