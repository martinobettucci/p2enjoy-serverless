# @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#garde-de-remise-en-service
# @verifies docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
"""Exact DEV upload observation and guarded control replacement; no fixture server.

All helpers share this contract. Only the principal invokes this operator.
"""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time
from uuid import UUID
from control_database import read_control

ROOT = Path('/srv/p2enjoy-serverless')
assert os.geteuid() == 0 and socket.gethostname() == 'infra-serverless'
mode, function, namespace = sys.argv[1:4]
assert all(str(UUID(value)) == value for value in (function, namespace))
settings = {}
for line in Path('/etc/spark/env').read_text().splitlines():
    fields = shlex.split(line, comments=True)
    if len(fields) == 1 and '=' in fields[0]:
        key, value = fields[0].split('=', 1)
        if key in ('SERVERLESS_STATE_HOST_PATH', 'SERVERLESS_DOCKER_SOCKET_HOST'):
            settings[key] = value
state = Path(settings['SERVERLESS_STATE_HOST_PATH'])
docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix://' + settings['SERVERLESS_DOCKER_SOCKET_HOST']]


def command(args, timeout=30):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    assert p.returncode == 0, 'operator_command_failed'
    return p.stdout.strip()


def rows(sql, args=()):
    with read_control(state / 'control.sqlite3') as db:
        return [dict(row) for row in db.execute(sql, args)]


owner = rows('''SELECT n.name FROM functions f JOIN services s ON s.id=f.service_id
    JOIN namespaces n ON n.id=s.namespace_id WHERE f.id=? AND n.id=?''', (function, namespace))
assert len(owner) == 1 and re.fullmatch(r'validator-names-[0-9a-f]{8}', owner[0]['name'])
assert not rows('SELECT 1 FROM functions WHERE deleted_at IS NULL AND id!=?', (function,)), 'foreign_active_function'
installation = rows("SELECT value FROM security_metadata WHERE name='installation-id'")[0]['value']


def write(path, value):
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('w') as handle:
        json.dump(value, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    temporary.replace(path)


def validators():
    ids = command(docker + ['ps', '-aq', '--filter', 'label=tech.p2enjoy.serverless.installation=' + installation,
                           '--filter', 'label=tech.p2enjoy.serverless.kind=validation']).split()
    return json.loads(command(docker + ['inspect', *ids])) if ids else []


def snapshot(candidate):
    candidate = str(UUID(candidate))
    found = rows('''SELECT id,state,error_code,reserved_bytes,revision_id,configuration_cipher IS NULL AS configuration_empty,
        validation_json FROM deployments WHERE id=? AND function_id=?''', (candidate, function))
    assert len(found) == 1, 'owned_candidate_required'
    row = found[0]; row['validation'] = json.loads(row.pop('validation_json') or 'null')
    code = state / 'artifacts' / candidate / 'code'
    matched = []
    for item in validators():
        mounts = {m['Destination']: m['Source'] for m in item['Mounts']}
        if mounts.get('/code') != str(code):
            continue
        labels = item['Config']['Labels']
        assert labels['tech.p2enjoy.serverless.installation'] == installation and labels['tech.p2enjoy.serverless.kind'] == 'validation'
        channel = Path(mounts['/protocol']); assert channel.parent == state / 'validation' and channel.name.startswith('v-')
        marker = None
        if item['State']['Running']:
            program = 'const fs=require("node:fs"),p="/tmp/validator-name-import.json";process.stdout.write(fs.existsSync(p)?fs.readFileSync(p,"utf8"):"null")'
            marker = json.loads(command(docker + ['exec', item['Id'], 'node', '-e', program]))
            if marker:
                assert marker['mode'] == json.loads((code / 'validation-mode.json').read_text())['mode'] and marker['pid'] > 0
        host = item['HostConfig']
        matched.append({'id': item['Id'], 'name': item['Name'].lstrip('/'), 'image': item['Image'], 'running': item['State']['Running'],
                        'labels': labels, 'marker': marker, 'channel': channel.name, 'channel_present': channel.is_dir(),
                        'isolation': {k: host[k] for k in ('NetworkMode', 'ReadonlyRootfs', 'CapDrop', 'SecurityOpt', 'Memory', 'MemorySwap', 'NanoCpus', 'PidsLimit', 'Init')},
                        'mounts': [{k: m[k] for k in ('Source', 'Destination', 'RW')} for m in item['Mounts']]})
    fn = rows('SELECT active_revision_id,updated_at,config_json,environment_json,secrets_cipher FROM functions WHERE id=?', (function,))[0]
    configuration = hashlib.sha256(json.dumps([fn.pop(k) for k in ('config_json', 'environment_json', 'secrets_cipher')]).encode()).hexdigest()
    return {'candidate': row, 'validators': matched, 'global_validators': [v['Id'] for v in validators()],
            'channels': [p.name for p in (state / 'validation').iterdir()], 'code_present': code.is_dir(),
            'archive_present': (code.parent / 'archive.zip').is_file(),
            'function': {**fn, 'configuration_sha256': configuration},
            'revisions': rows('SELECT id,code_hash,stored_bytes,deleted_at FROM revisions WHERE function_id=? ORDER BY id', (function,)),
            'versions': rows('SELECT code_hash,state FROM function_versions WHERE function_id=? ORDER BY code_hash', (function,))}


def observe(candidate):
    deadline = time.monotonic() + 10
    while True:
        value = snapshot(candidate)
        if value['candidate']['state'] == 'validating' and len(value['validators']) == 1 and value['validators'][0]['marker']:
            assert value['validators'][0]['running']; return value
        assert value['candidate']['state'] in ('prepared', 'receiving', 'validating'), 'live_validation_window_missed'
        assert time.monotonic() < deadline, 'live_validation_not_observed'
        time.sleep(.05)


RECOVER = '''import fcntl,hashlib,json,os,re,socket,subprocess,sys,time,urllib.request
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
folder=Path(sys.argv[1]);assert folder.parent==Path('/run') and re.fullmatch(r'serverless-validator-names-[a-f0-9]{32}',folder.name)
identity=json.loads((folder/'identity.json').read_text());d=identity['docker']
fd=os.open(folder/'lock',os.O_RDWR|os.O_NOFOLLOW)
try:
 deadline=time.monotonic()+60
 while True:
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   assert time.monotonic()<deadline,'recovery_lock_deadline';time.sleep(.1)
 def cmd(args,timeout=30):return subprocess.check_output(args,text=True,timeout=timeout,cwd=Path(identity['compose']).parent)
 for name,digest in identity['official_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,'official_configuration_changed'
 assert hashlib.sha256(Path(identity['compose']).read_bytes()).hexdigest()==identity['compose_sha256']
 assert hashlib.sha256((folder/'recover.py').read_bytes()).hexdigest()==identity['recover_sha256']
 assert cmd(d+['image','inspect','p2enjoy-control:dev','--format','{{.Id}}']).strip()==identity['new_image']
 reference=json.loads(cmd(d+['inspect','serverless-runtime-reference']))[0];assert [reference['Id'],reference['Image'],reference['State']['StartedAt']]==identity['reference']
 def configuration(row):
  return {'mounts':sorted([{k:m.get(k) for k in ('Type','Source','Destination','RW','Propagation')} for m in row['Mounts']],key=lambda m:m['Destination']),
   'host':{k:row['HostConfig'].get(k) for k in ('NetworkMode','ReadonlyRootfs','Memory','MemorySwap','NanoCpus','PidsLimit','CapDrop','SecurityOpt','Tmpfs')},
   'environment_sha256':hashlib.sha256(json.dumps(sorted(row['Config']['Env'])).encode()).hexdigest(),
   'command':row['Config']['Cmd'],'entrypoint':row['Config']['Entrypoint']}
 def inspect():
  row=json.loads(cmd(d+['inspect','serverless-api']))[0]
  assert row['Image'] in (identity['old_image'],identity['new_image'])
  labels=row['Config']['Labels'];assert labels['com.docker.compose.project']=='p2enjoy-serverless-dev' and labels['com.docker.compose.service']=='control'
  assert configuration(row)==identity['control_configuration'],'effective_control_configuration_changed'
  return row
 current=inspect();intent=folder/'replacement-intent.json'
 if current['Image']==identity['old_image']:
  assert current['Id']==identity['old_id'] and current['State']['StartedAt']==identity['old_started_at']
  assert not current['State']['Running'] and current['State']['ExitCode']==137,'original_control_not_interrupted'
  assert not intent.exists(),'replacement_already_attempted_requires_review'
  with intent.open('x') as handle:
   json.dump({'old_stopped_id':current['Id'],'old_started_at':current['State']['StartedAt'],'new_image':identity['new_image'],'response_known':False},handle);handle.flush();os.fsync(handle.fileno())
  cmd(d+['compose','--env-file','/etc/spark/env','--env-file','/run/spark/secrets','-f',identity['compose'],'up','-d','--force-recreate','--no-build','--wait','--wait-timeout','60'],timeout=90)
  current=inspect()
 else:
  assert intent.exists(),'new_control_not_owned_by_this_replacement'
  prior=json.loads(intent.read_text());assert prior['old_stopped_id']==identity['old_id'] and prior['new_image']==identity['new_image']
 expected_id=current['Id'];deadline=time.monotonic()+70
 while True:
  current=inspect();assert current['Id']==expected_id and current['Image']==identity['new_image']
  if current['State'].get('Health',{}).get('Status')=='healthy':break
  assert current['State']['Running'] and time.monotonic()<deadline,'new_control_health_not_confirmed'
  time.sleep(.2)
 with urllib.request.urlopen('http://127.0.0.1:18090/healthz',timeout=5) as response:assert response.status==200 and json.load(response)['status']=='ok'
 for name,digest in identity['official_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
 result={'completed':True,'trigger':sys.argv[2],'control_id':current['Id'],'image':current['Image'],'started_at':current['State']['StartedAt'],'healthy':True,'old_control_restarted':False,'reference_unchanged':True,'official_unchanged':True}
 path=folder/'restored.json'
 if path.exists():
  previous=json.loads(path.read_text());assert previous['completed'] and previous['control_id']==current['Id'];result=previous
 else:
  temporary=folder/'restored.pending';temporary.write_text(json.dumps(result));temporary.replace(path)
 print(json.dumps(result))
finally:os.close(fd)
'''


def folder_path(unit):
    assert re.fullmatch(r'serverless-validator-names-[a-f0-9]{32}', unit)
    folder = Path('/run') / unit; info = folder.lstat()
    assert info.st_uid == 0 and info.st_mode & 0o777 == 0o700 and not folder.is_symlink()
    identity = json.loads((folder / 'identity.json').read_text())
    assert identity['function_id'] == function and identity['namespace_id'] == namespace
    return folder, identity


if mode in ('inspect', 'observe'):
    result = snapshot(sys.argv[4]) if mode == 'inspect' else observe(sys.argv[4])
elif mode == 'interrupt':
    candidate, new_image, unit = sys.argv[4:7]
    assert re.fullmatch(r'sha256:[a-f0-9]{64}', new_image)
    assert re.fullmatch(r'serverless-validator-names-[a-f0-9]{32}', unit)
    assert not rows('SELECT 1 FROM execution_instances') and not rows("SELECT 1 FROM invocations WHERE state IN ('receiving','queued','admitted','running')")
    initial = observe(candidate); assert len(initial['global_validators']) == 1
    assert re.fullmatch(r'p2-v-[a-f0-9]{32}', initial['validators'][0]['name'])
    services = json.loads(command(docker + ['inspect', 'serverless-api', 'serverless-runtime-reference']))
    assert services[0]['Image'] != new_image and services[0]['State']['Health']['Status'] == 'healthy'
    assert services[0]['Image'] == command(docker + ['image', 'inspect', 'p2enjoy-control:before-validator-names', '--format', '{{.Id}}'])
    assert command(docker + ['image', 'inspect', 'p2enjoy-control:dev', '--format', '{{.Id}}']) == new_image
    folder = Path('/run') / unit; folder.mkdir(mode=0o700)
    (folder / 'lock').touch(mode=0o600); (folder / 'recover.py').write_text(RECOVER)
    identity = {'function_id': function, 'namespace_id': namespace, 'candidate_id': candidate,
                'old_id': services[0]['Id'], 'old_image': services[0]['Image'], 'old_started_at': services[0]['State']['StartedAt'], 'new_image': new_image, 'docker': docker,
                'control_configuration': {
                    'mounts': sorted([{k: m.get(k) for k in ('Type', 'Source', 'Destination', 'RW', 'Propagation')} for m in services[0]['Mounts']], key=lambda m: m['Destination']),
                    'host': {k: services[0]['HostConfig'].get(k) for k in ('NetworkMode', 'ReadonlyRootfs', 'Memory', 'MemorySwap', 'NanoCpus', 'PidsLimit', 'CapDrop', 'SecurityOpt', 'Tmpfs')},
                    'environment_sha256': hashlib.sha256(json.dumps(sorted(services[0]['Config']['Env'])).encode()).hexdigest(),
                    'command': services[0]['Config']['Cmd'], 'entrypoint': services[0]['Config']['Entrypoint']},
                'reference': [services[1]['Id'], services[1]['Image'], services[1]['State']['StartedAt']],
                'compose': str(ROOT / 'control/compose.spark.yml'), 'compose_sha256': hashlib.sha256((ROOT / 'control/compose.spark.yml').read_bytes()).hexdigest(),
                'official_sha256': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ['/etc/spark/env', '/run/spark/secrets', '/etc/spark/routes']},
                'recover_sha256': hashlib.sha256((folder / 'recover.py').read_bytes()).hexdigest()}
    write(folder / 'identity.json', identity); write(folder / 'before.json', initial)
    labels = services[0]['Config']['Labels']
    assert labels['com.docker.compose.project'] == 'p2enjoy-serverless-dev' and labels['com.docker.compose.service'] == 'control'
    command(['systemd-run', '--quiet', '--collect', '--unit=' + unit, '--on-active=90s', '--timer-property=AccuracySec=100ms',
             '/usr/bin/python3', '-I', str(folder / 'recover.py'), str(folder), 'guard'])
    assert command(['systemctl', 'is-active', unit + '.timer']) == 'active'
    print(json.dumps({'event': 'guard-armed', 'unit': unit}), flush=True)
    # Recheck the exact live import immediately before the single authorized kill.
    with (folder / 'lock').open('r+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before_kill = snapshot(candidate); assert before_kill['validators'][0]['id'] == initial['validators'][0]['id'] and before_kill['validators'][0]['running']
        stopped = json.loads(command(docker + ['inspect', 'serverless-api']))[0]
        assert stopped['Id'] == identity['old_id'] and stopped['Image'] == identity['old_image']
        command(docker + ['kill', '--signal', 'KILL', identity['old_id']])
        stopped = json.loads(command(docker + ['inspect', identity['old_id']]))[0]
        assert not stopped['State']['Running'] and stopped['State']['ExitCode'] == 137
        after = snapshot(candidate); assert after['validators'][0]['id'] == initial['validators'][0]['id']
        result = {'completed': True, 'unit': unit, 'before': before_kill, 'orphan': after, 'control_exit_code': 137, 'old_control_id': identity['old_id']}
        write(folder / 'interrupted.json', result)
elif mode == 'restore':
    folder, identity = folder_path(sys.argv[4])
    result = json.loads(command(['/usr/bin/python3', '-I', str(folder / 'recover.py'), str(folder), 'explicit'], timeout=120))
    stopped = subprocess.run(['systemctl', 'stop', folder.name + '.timer'], capture_output=True, text=True, timeout=10)
    if stopped.returncode:
        observed = command(['systemctl', 'show', folder.name + '.timer', '--property=LoadState', '--property=ActiveState'])
        assert stopped.returncode == 5 and dict(line.split('=', 1) for line in observed.splitlines()) == {'LoadState': 'not-found', 'ActiveState': 'inactive'}
    statuses = {}
    for suffix in ('timer', 'service'):
        deadline = time.monotonic() + 15
        while True:
            p = subprocess.run(['systemctl', 'is-active', folder.name + '.' + suffix], capture_output=True, text=True, timeout=10)
            statuses[suffix] = p.stdout.strip()
            if statuses[suffix] in ('inactive', 'unknown'):
                break
            assert time.monotonic() < deadline, 'recovery_unit_not_finished'
            time.sleep(.1)
    result = {**result, 'guard_states': statuses, 'recovery_identity': identity}
else:
    raise RuntimeError('unknown_operator_mode')
print(json.dumps(result), flush=True)
