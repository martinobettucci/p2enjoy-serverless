# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#suite-commune-de-qualification
# @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#suite-commune-de-qualification
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
    assert sys.argv[1] in ('.local/e2e/storage-console-focused.json', '.local/e2e/storage-console-regressions.json',
                           '.local/e2e/invocation-urls-regressions.json','.local/e2e/function-catalogue-regressions.json')
    catalogue = sys.argv[1] == '.local/e2e/function-catalogue-regressions.json'
    extended = catalogue or sys.argv[1] == '.local/e2e/invocation-urls-regressions.json'
    output = ROOT / '.local/e2e/function-catalogue-physical.json' if catalogue else ROOT / '.local/e2e/invocation-urls-physical.json' if extended else OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.write_text(json.dumps({'completed': False}) + '\n')
    suite = json.loads((ROOT / sys.argv[1]).read_text())
    assert suite['serial'] and not suite['completed'], 'live_suite_checkpoint_required'
    if extended: assert suite['scope'] == ('function-catalogue' if catalogue else 'invocation-urls')
    commands = {row['campaign']: row for row in suite['commands']}
    campaigns, reports, historical, temporary_ids = {}, {}, {}, []
    names = NAMES + (('invocation-urls', 'invocation-urls-ui', 'service-configuration', 'service-transport') if extended else ())
    for name in (*names, 'storage-legacy-partial', 'storage-legacy-recovery'):
        row = commands[name]
        assert row['exit_code'] == 0 and row['fresh_report_verified'] and row['report_content_verified']
        path = ROOT / row['report_path']
        assert path == ROOT / ('.local/e2e/' + name + '.json')
        raw = path.read_bytes();digest = hashlib.sha256(raw).hexdigest()
        assert digest == row['after']['report']['sha256'], 'campaign_report_changed'
        report = json.loads(raw)
        assert report['completed'] and report['cleanup'] and not report.get('cleanup_errors')
        reports[name] = {'path': row['report_path'], 'sha256': digest}
        if name not in names:
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
    counts = (10, 32) if extended else (6, 24)
    assert len(campaigns) == counts[0] and len(identifiers) == len(set(identifiers)) == counts[1]
    assert set(identifiers).isdisjoint(temporary_ids), 'historical_ids_in_original_installation'
    command = ['python3', '-B', '/srv/p2enjoy-serverless/e2e/storage-console-inspect.py', json.dumps(campaigns)]
    physical = json.loads(subprocess.check_output(SSH + [shlex.join(command)], timeout=240))
    assert physical['completed'] and not any(physical['global_control_reservations'].values())
    assert physical['global_storage_allocated_bytes'] == 0
    catalogue_results = {}
    if catalogue:
        for name, namespace_count, function_count, service_count in [
                ('function-catalogue-api',7,32,8),('function-catalogue-ui',6,27,7)]:
            row=commands[name];assert row['exit_code']==0 and row['fresh_report_verified'] and row['report_content_verified']
            path=ROOT/row['report_path'];assert path==ROOT/('.local/e2e/'+name+'.json')
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest==row['after']['report']['sha256']
            report=json.loads(raw);assert report['completed'] and report['cleanup'] and not report['cleanup_errors'] and report['skipped']==0
            mapping={n:sorted(a['function_id'] for a in report['storage_archives'] if a['namespace_id']==n) for n in report['namespaces']}
            ids=[i for values in mapping.values() for i in values]
            assert len(mapping)==namespace_count and len(ids)==len(set(ids))==function_count
            assert set(ids).isdisjoint(identifiers+temporary_ids) and set(mapping).isdisjoint(campaigns)
            for prior in catalogue_results.values():
                assert set(ids).isdisjoint(prior['physical']['functions']) and set(mapping).isdisjoint(prior['physical']['campaigns'])
            command=['python3','-B','/srv/p2enjoy-serverless/e2e/storage-console-inspect.py',json.dumps(mapping)]
            result=json.loads(subprocess.check_output(SSH+[shlex.join(command)],timeout=240));assert result['completed']
            services=report['service_ids'];assert len(services)==len(set(services))==service_count
            # Decryption stays inside the existing image; only a boolean is returned.
            program='import json;from app.main import database,vault;ids='+repr(services)+';namespaces='+repr(list(mapping))+';rows=[database.one("SELECT id,namespace_id,environment_json,secrets_cipher,deleted_at FROM services WHERE id=?",(i,)) for i in ids];assert all(r and r["namespace_id"] in namespaces and r["deleted_at"] and json.loads(r["environment_json"])=={} and vault.open(r["secrets_cipher"])=={} for r in rows);actual={r["id"] for n in namespaces for r in database.all("SELECT id FROM services WHERE namespace_id=?",(n,))};assert actual==set(ids);print(json.dumps({"services_cleared":True,"service_count":len(ids)}))'
            command=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','exec','serverless-api','python3','-B','-c',program]
            cleared=json.loads(subprocess.check_output(SSH+[shlex.join(command)],timeout=90));assert cleared['services_cleared']
            reports[name]={'path':row['report_path'],'sha256':digest}
            catalogue_results[name]={'physical':result,**cleared}
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
assert not run(docker+['ps','-aq','--filter','label=com.docker.compose.project=p2enjoy-adapter-dev','--filter','label=com.docker.compose.service=e2e'])
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
    adapter = None
    if extended:
        row = next(item for item in suite['prerequisites'] if item['campaign'] == 'invocation-url-adapter-build')
        raw = (ROOT / row['report_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['after']['report']['sha256']
        adapter = json.loads(raw)
        assert adapter['completed'] and adapter['current_image'] == installation['control']['image']
        expected_images = {name: item['image'] for name, item in adapter['images'].items()}
        assert all(item['before'].get('adapter_images') == expected_images and
                   item['after'].get('adapter_images') == expected_images for item in suite['commands'])
    value = {'completed': True, 'campaign_count': len(campaigns), 'function_count': len(identifiers),
             'reports': reports, 'physical': physical, 'installation': installation,
             'historical_restoration': historical, 'excluded_historical_function_ids': temporary_ids,
             'adapter_build': adapter}
    if catalogue:
        value.update(catalogue=catalogue_results,
                     total_namespaces=len(campaigns)+sum(len(r['physical']['campaigns']) for r in catalogue_results.values()),
                     total_functions=len(identifiers)+sum(len(r['physical']['functions']) for r in catalogue_results.values()))
        assert value['total_namespaces']==23 and value['total_functions']==91
    pending = output.with_suffix('.pending');pending.write_text(json.dumps(value, indent=2) + '\n');pending.replace(output)
    print(json.dumps({'completed': True, 'namespaces': len(campaigns), 'functions': len(identifiers),
                      'embedded_files': len(expected), 'historical_restorations': len(historical)}))


if __name__ == '__main__':
    main()
