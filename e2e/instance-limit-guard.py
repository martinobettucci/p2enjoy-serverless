# @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#refus-avant-toute-mutation
# @verifies docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#preuve-ciblée-du-refus
# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md#budgets-et-attente
"""Inspect the real DEV limit and refuse an unconditionally restored mutation.

The normal console has no active-entry write precondition. A client-side GET
cannot close that race. Until an authoritative conditional protocol is supplied
and qualified, this helper performs no writes, proposals or Compose commands.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import urllib.request
from uuid import UUID

KEY = 'SERVERLESS_FUNCTION_INSTANCE_LIMIT'
CONSOLE = 'http://127.0.0.1:5175/api/v1/sparks/infra-serverless'
QUERY = '?server=spark-experiment'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-J',
       'ubuntu@51.158.54.202', 'root@10.77.0.24']

# Only read selected public budgets and hashes. No configuration body or secret
# leaves the SPARK. SQLite reads run under the actual rootless owner.
READER = r'''
import hashlib,json,os,re,shlex,socket,subprocess,sys
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');values={}
for line in Path('/etc/spark/env').read_text().splitlines():
 parts=shlex.split(line,comments=True)
 if len(parts)==1 and '=' in parts[0]:
  name,value=parts[0].split('=',1)
  if name in ('SERVERLESS_FUNCTION_INSTANCE_LIMIT','SERVERLESS_FUNCTION_CPU_BUDGET','SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB','SERVERLESS_STATE_HOST_PATH'):values[name]=value
sys.path.insert(0,str(root/'e2e'))
from control_database import read_control
with read_control(Path(values['SERVERLESS_STATE_HOST_PATH'])/'control.sqlite3') as db:
 row=db.execute('SELECT name FROM namespaces WHERE id=? AND deleted_at IS NULL',(namespace,)).fetchone()
 assert row and re.fullmatch('invocation-[0-9a-f]{8}',row[0]),'campaign_namespace_required'
 assert db.execute('SELECT count(*) FROM functions f JOIN services s ON s.id=f.service_id WHERE f.deleted_at IS NULL AND s.namespace_id!=?',(namespace,)).fetchone()[0]==0,'foreign_function_present'
 counts={name:db.execute(query).fetchone()[0] for name,query in {
 'instances':'SELECT count(*) FROM execution_instances',
 'active_calls':"SELECT count(*) FROM invocations WHERE state IN ('receiving','queued','admitted','running')",
 'operations':'SELECT count(*) FROM function_operations',
 'reserved_bytes':'SELECT coalesce(sum(reserved_bytes),0) FROM deployments'}.items()}
 assert not any(counts.values()),'active_consumers_required_to_finish'
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
services=json.loads(subprocess.check_output(D+['inspect','serverless-api','serverless-runtime-reference'],text=True,timeout=15))
assert all(v['State']['Running'] and v['State']['Health']['Status']=='healthy' for v in services)
keys=('SERVERLESS_FUNCTION_INSTANCE_LIMIT','SERVERLESS_FUNCTION_CPU_BUDGET','SERVERLESS_FUNCTION_MEMORY_BUDGET_MIB')
source='import os,json;print(json.dumps({key:os.environ[key] for key in '+repr(keys)+'}))'
consumed=json.loads(subprocess.check_output(D+['exec','serverless-api','python','-B','-c',source],text=True,timeout=15))
assert consumed=={k:values[k] for k in keys},'official_consumed_mismatch'
assert consumed[keys[0]]=='32' and consumed[keys[1]]=='1' and consumed[keys[2]]=='8192','baseline_budgets_required'
files={}
for name in ('/etc/spark/env','/etc/spark/env.?','/run/spark/secrets','/etc/spark/routes'):
 p=Path(name);assert not p.is_symlink()
 files[name]=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
proposal=Path('/etc/spark/env.?')
assert not proposal.exists() or not any(re.match(r'\s*(?:export\s+)?SERVERLESS_FUNCTION_INSTANCE_LIMIT\s*=',line) for line in proposal.read_text().splitlines()),'existing_limit_proposal_required_to_remain'
print(json.dumps({'counts':counts,'budgets':consumed,'files':files,'services':{v['Name'].lstrip('/'):{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'healthy':True} for v in services}}))
'''


def inspect(namespace):
    assert str(UUID(namespace)) == namespace, 'canonical_namespace_uuid_required'
    # Existing normal console, one resolved entry only; never retain the full
    # environment response, which can include unrelated confidential settings.
    with urllib.request.urlopen(CONSOLE + '/env' + QUERY, timeout=30) as response:
        assert response.status == 200
        value = json.load(response)
    rows = [v for v in value['env'] if v['name'] == KEY]
    assert len(rows) == 1
    entry = rows[0]
    assert entry['value'] == '32' and entry['origin'] == entry['scope'] == 'spark'
    assert not entry['is_secret']
    program = 'namespace=' + repr(namespace) + '\n' + READER
    result = subprocess.run(SSH + ['python3 -B -c ' + shlex.quote(program)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError('cell_guard_read_only_preflight_failed')
    snapshot = json.loads(result.stdout)
    snapshot['console_entry'] = {k: entry.get(k) for k in
                                 ('name', 'value', 'origin', 'scope', 'updated_at')}
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('namespace')
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    snapshot = inspect(args.namespace)
    if args.inspect:
        print(json.dumps({'completed': True, 'inspection': snapshot}), flush=True)
        return 0
    print(json.dumps({'event': 'instance-limit-blocked', 'completed': False,
                      'code': 'active_environment_precondition_unavailable',
                      'mutation_count': 0, 'inspection': snapshot}), flush=True)
    return 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # Do not print remote stderr, console response bodies or transport URLs.
        print(json.dumps({'event': 'instance-limit-blocked', 'completed': False,
                          'code': 'read_only_preflight_failed',
                          'failure_type': type(error).__name__, 'mutation_count': 0}), flush=True)
        raise SystemExit(2) from None
