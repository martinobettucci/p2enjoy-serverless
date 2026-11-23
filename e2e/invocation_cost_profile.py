# @spec docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#profilage-du-coût-dinvocation-courant--sls-1336
# @verifies docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#fermeture-et-statistiques-fraîches
# @verifies docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#propriété-et-retrait-du-parser
# @spec docs/BACKLOG.md#sls-136 | docs/INVOCATION_PRODUCTION_PROFILE.md#portée-réelle-du-profiler--sls-136
# @verifies docs/BACKLOG.md#sls-136 | docs/INVOCATION_PRODUCTION_PROFILE.md#portée-réelle-du-profiler--sls-136
"""Owned DEV cProfile lifecycle; real image, process, stats and isolated parser."""
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import time
from uuid import UUID

IMAGE = 'sha256:f016a1b71cb055c4f4c4e2fb2a2622c67c93f7a6ec26b39ec7e663cd9de4c0c7'
ROOT = Path('/srv/p2enjoy-serverless')
DESTINATION = '/qualification-profile'
LABEL = 'tech.p2enjoy.qualification.invocation-cost-profile'
APP_ARGS = ['python', '-B', '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0',
            '--port', '18090', '--workers', '1', '--no-access-log', '--no-proxy-headers']

RUNTIME_PROGRAM = r'''
import cProfile,_lsprof,pstats,sys,sqlite3,hashlib,json
from importlib.metadata import version
from pathlib import Path
backend={'control/app/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/app').glob('*.py')}
backend.update({'control/migrations/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/migrations').glob('*.sql')})
backend['function_code_hash.py']=hashlib.sha256(Path('/app/function_code_hash.py').read_bytes()).hexdigest()
web={str(p.relative_to('/app/web')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app/web').rglob('*') if p.is_file()}
print(json.dumps({'python':sys.version,'python_version':list(sys.version_info[:3]),'uvicorn':version('uvicorn'),'sqlite':sqlite3.sqlite_version,
 'modules':{m.__name__:{'path':m.__file__,'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()} for m in (cProfile,_lsprof,pstats)},
 'backend':backend,'web':web}))
'''

PARSER_PROGRAM = r'''
import hashlib,io,json,math,pstats,signal,sqlite3,sys
from pathlib import Path
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('invocation_cost_parser_deadline')))
signal.alarm(20)
path=Path('/qualification-profile/control.pstats')
raw=path.read_bytes();assert 0<len(raw)<=32*1024**2
profile=pstats.Stats(str(path),stream=io.StringIO());assert 0<len(profile.stats)<=20000
functions=[];links=0
for (filename,line,name),(cc,nc,tt,ct,callers) in sorted(profile.stats.items()):
 assert isinstance(filename,str) and isinstance(line,int) and isinstance(name,str)
 assert isinstance(cc,int) and isinstance(nc,int) and 0<=cc<=nc
 assert all(math.isfinite(t) and t>=0 for t in (tt,ct))
 incoming=[]
 for (caller_file,caller_line,caller_name),data in sorted(callers.items()):
  assert isinstance(data,tuple) and len(data)==4
  total,primitive,own,cumulative=data
  assert isinstance(total,int) and isinstance(primitive,int) and 0<=primitive<=total
  assert all(math.isfinite(t) and t>=0 for t in (own,cumulative))
  incoming.append({'file':caller_file,'line':caller_line,'name':caller_name,'total_calls':total,'primitive_calls':primitive,
                   'self_seconds':own,'cumulative_seconds':cumulative})
 links+=len(incoming);assert links<=100000
 functions.append({'file':filename,'line':line,'name':name,'primitive_calls':cc,'total_calls':nc,
                   'self_seconds':tt,'cumulative_seconds':ct,'callers':incoming})
# @verifies docs/BACKLOG.md#sls-136 | docs/INVOCATION_PRODUCTION_PROFILE.md#portée-réelle-du-profiler--sls-136
scope={'clock':'real','collection':'interpreter-global callbacks','thread_attribution':False,
       'task_attribution':False,'call_path_timing_attribution':False}
consistency={'functions_self_gt_cumulative':sum(f['self_seconds']>f['cumulative_seconds'] for f in functions),
 'caller_links_self_gt_cumulative':sum(c['self_seconds']>c['cumulative_seconds'] for f in functions for c in f['callers'])}
value={'completed':True,'python':sys.version,'python_version':list(sys.version_info[:3]),'sqlite':sqlite3.sqlite_version,
 'pstats_module_sha256':hashlib.sha256(Path(pstats.__file__).read_bytes()).hexdigest(),
 'file_bytes':len(raw),'file_sha256':hashlib.sha256(raw).hexdigest(),'function_count':len(functions),'caller_links':links,
 'total_calls':profile.total_calls,'primitive_calls':profile.prim_calls,'total_self_seconds':profile.total_tt,
 'timer':'cProfile default real time','measurement_scope':scope,'timing_consistency':consistency,'functions':functions}
output=json.dumps(value,allow_nan=False,separators=(',',':')).encode();assert len(output)<=16*1024**2
signal.alarm(0);sys.stdout.buffer.write(output+b'\n')
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def context(item, helper, *, allow_restored=False):
    cost = item['invocation_cost_profile']
    assert cost['mode'] in ('smoke', 'full', 'parser-loss') and item['mode'] == 'instance-limit' and item['guard_seconds'] == 2700
    assert str(UUID(item['campaign'])) == item['campaign'] and item['original']['image'] == IMAGE
    assert not item.get('retention_replay') and not item.get('firing_replay') and (allow_restored or not item.get('restored'))
    work = Path(item['work']); assert work == ROOT / 'qualification-history' / ('instance-limit-' + item['campaign'])
    assert sha((work / 'invocation_cost_profile.py').read_bytes()) == cost['source_sha256']
    assert helper.hashes() == item['configuration']
    return cost, work


def definition(item, helper, identifier):
    values = json.loads(helper.docker(item, 'inspect', identifier))
    assert len(values) == 1
    return values[0]


def runtime(item, helper, identifier):
    value = json.loads(helper.docker(item, 'exec', identifier, 'python', '-B', '-c', RUNTIME_PROGRAM))
    assert value['python_version'][:2] == [3, 14] and value['uvicorn'] == '0.54.0'
    expected = {'control/' + str(p.relative_to(ROOT / 'control')): sha(p.read_bytes())
                for directory, pattern in (('app', '*.py'), ('migrations', '*.sql'))
                for p in (ROOT / 'control' / directory).glob(pattern)}
    expected['function_code_hash.py'] = sha((ROOT / 'function_code_hash.py').read_bytes())
    assert len(expected) == 42 and value['backend'] == expected and len(value['web']) == 4
    return value


def capture_original(item, journal, helper):
    cost, _ = context(item, helper)
    current = definition(item, helper, item['original']['id'])
    assert current['Id'] == item['original']['id'] and current['Image'] == IMAGE and current['State']['Running']
    assert current['Config']['Cmd'] == APP_ARGS
    cost['baseline'] = runtime(item, helper, current['Id'])
    helper.atomic(journal, item)


def configure(item, journal, helper, source):
    cost, work = context(item, helper)
    assert 'baseline' in cost and '    command:' not in source and source.count('    volumes:\n') == 1
    folder = work / 'invocation-cost-profile'
    assert not folder.exists() and not folder.is_symlink()
    cost['output_intent'] = str(folder); helper.atomic(journal, item)
    folder.mkdir(mode=0o700); os.chown(folder, item['uid'], item['gid'])
    cost['output_identity'] = helper.identity(folder)
    assert cost['output_identity']['uid'] == 1001 and cost['output_identity']['mode'] == 0o700
    command = APP_ARGS[:3] + ['cProfile', '-o', DESTINATION + '/control.pstats', '-m'] + APP_ARGS[3:]
    cost['command'] = command
    source = source.replace('    network_mode: host\n', '    command: ' + json.dumps(command) + '\n    network_mode: host\n', 1)
    source = source.replace('    volumes:\n', '    volumes:\n      - ' + str(folder) + ':' + DESTINATION + '\n', 1)
    helper.atomic(journal, item)
    return source


def process(pid):
    path = Path('/proc', str(pid)); fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    status = dict(line.split(':', 1) for line in (path / 'status').read_text().splitlines() if ':' in line)
    raw = (path / 'cmdline').read_bytes()
    value = {'pid': pid, 'birth': fields[19], 'state': fields[0], 'parent': int(fields[1]),
             'uid': int(status['Uid'].split()[0]), 'cgroup': (path / 'cgroup').read_text(),
             'namespace_pids': [int(v) for v in status['NSpid'].split()], 'argv_sha256': sha(raw)}
    assert (path / 'stat').read_text().rsplit(')', 1)[1].split()[19] == value['birth']
    return value, raw


def app_identity(item, helper):
    cost, _ = context(item, helper)
    current = definition(item, helper, helper.temporary_control_name(item))
    assert current['Image'] == IMAGE and current['State']['Running'] and current['Id'] != item['original']['id']
    assert current['Config']['Labels']['com.docker.compose.project'] == item['project']
    assert current['Config']['Cmd'] == cost['command']
    mounts = [v for v in current['Mounts'] if v['Destination'] == DESTINATION]
    assert len(mounts) == 1 and mounts[0]['Source'] == cost['output_intent'] and mounts[0]['RW']
    assert helper.same(cost['output_intent'], cost['output_identity'])
    init = current['State']['Pid']; init_identity, _ = process(init)
    assert init_identity.pop('state') not in ('Z', 'X')
    pending = [init]; seen = set(); found = []
    expected = b'\0'.join(os.fsencode(v) for v in cost['command']) + b'\0'
    while pending:
        pid = pending.pop()
        if pid in seen: continue
        seen.add(pid); assert len(seen) <= 64, 'profile_process_bound'
        try:
            for task in Path('/proc', str(pid), 'task').iterdir():
                try: pending.extend(int(v) for v in (task / 'children').read_text().split())
                except (FileNotFoundError, ProcessLookupError): continue
            identity, raw = process(pid)
        except (FileNotFoundError, ProcessLookupError): continue
        if raw == expected:
            assert identity.pop('state') not in ('Z', 'X')
            assert identity['cgroup'] == init_identity['cgroup'] and identity['uid'] == item['uid']
            assert identity['namespace_pids'][0] == pid and len(identity['namespace_pids']) >= 2
            assert Path('/proc', str(pid), 'exe').resolve().name.startswith('python')
            found.append(identity)
    assert len(found) == 1, 'unique_profiled_api_required'
    return {'container_id': current['Id'], 'image': current['Image'], 'init': init_identity, 'api': found[0]}


def ready(item, journal, helper):
    cost, _ = context(item, helper)
    value = app_identity(item, helper)
    cost['runtime'] = runtime(item, helper, value['container_id'])
    assert cost['runtime'] == cost['baseline'], 'profile_runtime_or_manifest_changed'
    assert not os.path.lexists(Path(cost['output_intent']) / 'control.pstats')
    cost['initial_process'] = value; helper.atomic(journal, item)
    return {'mode': cost['mode'], 'process': value, 'runtime': cost['runtime'],
            'command_sha256': sha(json.dumps(cost['command']).encode()), 'output_absent': True}


def parser_owned(item, helper):
    cost, _ = context(item, helper); intent = cost.get('parser')
    if intent is None: return None
    ids = helper.docker(item, 'ps', '-aq', '--filter', 'name=^/' + intent['name'] + '$').split()
    if not ids: return None
    assert len(ids) == 1
    value = definition(item, helper, ids[0])
    assert value['Image'] == IMAGE and value['Name'] == '/' + intent['name']
    assert value['Config']['Labels'].get(LABEL) == item['campaign']
    assert 'tech.p2enjoy.serverless.installation' not in value['Config']['Labels']
    assert value['Config']['Cmd'] == ['-I', '-B', '-c', PARSER_PROGRAM]
    assert value['Config']['Entrypoint'] == ['python']
    assert value['HostConfig']['NetworkMode'] == 'none' and value['HostConfig']['ReadonlyRootfs']
    assert value['HostConfig']['Memory'] == 256 * 1024**2 and value['HostConfig']['NanoCpus'] == 500000000
    assert value['HostConfig']['PidsLimit'] == 32 and value['HostConfig']['CapDrop'] == ['ALL']
    assert value['HostConfig']['SecurityOpt'] in (['no-new-privileges'], ['no-new-privileges:true'])
    assert not any(v.startswith(('OIDC_', 'SERVERLESS_')) for v in value['Config']['Env'])
    mounts = value['Mounts']; assert len(mounts) == 1
    assert mounts[0]['Source'] == cost['output_intent'] and mounts[0]['Destination'] == DESTINATION and not mounts[0]['RW']
    assert intent.get('id') in (None, value['Id']) and value['Id'] not in (item['original']['id'], cost['initial_process']['container_id'])
    return value


def seal_stats(item, journal, helper):
    cost, _ = context(item, helper)
    if 'file' not in cost: return
    folder = Path(cost['output_intent']); output = folder / 'control.pstats'
    expected = cost.get('sealed_identity', cost['output_identity'])
    assert helper.same(folder, expected), 'profile_output_identity_changed'
    info = output.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    assert (info.st_dev, info.st_ino, info.st_size) == (cost['file']['device'], cost['file']['inode'], cost['file']['bytes'])
    assert sha(output.read_bytes()) == cost['file']['sha256'] and list(folder.iterdir()) == [output]
    os.chown(output, 0, 0); os.chmod(output, 0o400)
    os.chown(folder, 0, 0); os.chmod(folder, 0o700)
    with output.open('rb') as stream: os.fsync(stream.fileno())
    descriptor = os.open(folder, os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)
    cost['sealed_identity'] = helper.identity(folder); helper.atomic(journal, item)


def cleanup_parser(item, journal, helper):
    cost, _ = context(item, helper)
    value = parser_owned(item, helper)
    if value is not None:
        helper.docker(item, 'rm', '-f', value['Id'])
        assert parser_owned(item, helper) is None, 'profile_parser_retained'
    if 'parser' in cost:
        cost['parser']['absent'] = True; helper.atomic(journal, item)
    try:
        seal_stats(item, journal, helper)
    except (OSError, AssertionError) as error:
        cost['seal_failure']={'type':type(error).__name__,'reason_sha256':sha(str(error).encode())}
        helper.atomic(journal,item)


def parse_stats(item, journal, helper):
    cost, _ = context(item, helper)
    assert 'parser' not in cost
    name = 'serverless-invocation-cost-parser-' + item['campaign']
    cost['parser'] = {'name': name, 'image': IMAGE, 'id': None,
                      'program_sha256': sha(PARSER_PROGRAM.encode()), 'folder_identity': cost['output_identity']}
    helper.atomic(journal, item)
    assert parser_owned(item, helper) is None, 'profile_parser_already_exists'
    try:
        identifier = helper.docker(item, 'create', '--name', name, '--label', LABEL + '=' + item['campaign'],
            '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--memory', '256m', '--cpus', '0.5', '--pids-limit', '32', '--mount',
            'type=bind,src=' + cost['output_intent'] + ',dst=' + DESTINATION + ',readonly',
            '--entrypoint', 'python', IMAGE, '-I', '-B', '-c', PARSER_PROGRAM)
        assert re.fullmatch('[a-f0-9]{64}', identifier)
        value = parser_owned(item, helper); assert value is not None and value['Id'] == identifier
        cost['parser']['id'] = identifier; helper.atomic(journal, item)
        if cost['mode']=='parser-loss':
            assert value['State']['Status']=='created' and not value['State']['Running']
            cost['parser']['loss_point']='created-before-start';helper.atomic(journal,item)
            helper.emit({'event':'invocation-cost-parser-created','campaign':item['campaign'],'id':identifier,'name':name,'image':IMAGE,'state':'created','driver_pid':item['driver_pid'],'driver_birth':item['driver_birth']})
            os.kill(os.getpid(),signal.SIGSTOP)
            raise AssertionError('profile_loss_driver_resumed_unexpectedly')
        output = helper.docker(item, 'start', '-a', identifier)
        state = parser_owned(item, helper)
        assert state and state['State']['Status'] == 'exited' and state['State']['ExitCode'] == 0
        result = json.loads(output); assert result['completed'] and result['python'] == cost['runtime']['python']
        assert result['pstats_module_sha256'] == cost['runtime']['modules']['pstats']['sha256']
        assert result['file_sha256'] == cost['file']['sha256'] and result['file_bytes'] == cost['file']['bytes']
        cost['parser']['exit_code'] = state['State']['ExitCode']; helper.atomic(journal, item)
        return result
    finally:
        cleanup_parser(item, journal, helper)


def complete(item, journal, helper, request):
    cost, work = context(item, helper)
    assert set(request) == {'op', 'functions', 'window'} and 'completed' not in cost
    functions = request['functions']; assert len(functions) == len(set(functions)) == 2
    assert all(isinstance(v, str) and str(UUID(v)) == v for v in functions)
    window = request['window']; assert type(window) is int and window % 300 == 0 and time.time() < window - 60
    current = helper.instance_limit_observation(item)
    expected = 6000 if cost['mode'] == 'full' else 2
    assert not current['instances'] and not current['containers'] and not current['firings']
    assert all(v['deleted_at'] for v in current['functions'])
    calls = current['invocations']; assert len(calls) == expected
    assert sorted({v['function_id'] for v in calls}) == sorted(functions)
    assert all(v['trigger'] == 'http' and v['state'] == 'succeeded' and v['handler_started'] and v['completed_at'] for v in calls)
    assert not helper.rows(item, Path(item['paths']['storage']) / 'registry.sqlite3', 'SELECT 1 FROM leases')
    identity = app_identity(item, helper)
    assert identity == cost['initial_process'], 'profile_process_identity_changed'
    assert runtime(item, helper, identity['container_id']) == cost['baseline']
    output = Path(cost['output_intent']) / 'control.pstats'
    assert not os.path.lexists(output), 'profile_must_be_fresh'
    descriptor = os.pidfd_open(identity['api']['pid'])
    cost['signal'] = {'number': signal.SIGINT, 'sent': False, 'intent_at_ns': str(time.time_ns())}
    try:
        assert app_identity(item, helper) == identity
        helper.atomic(journal, item)
        started = time.monotonic(); sent_ns = time.time_ns()
        signal.pidfd_send_signal(descriptor, signal.SIGINT)
        cost['signal'].update(sent=True, before_send_at_ns=str(sent_ns), sent_monotonic=started,
                              after_send_at_ns=str(time.time_ns()))
        deadline = started + 15
        assert select.select([descriptor], [], [], max(0, deadline - time.monotonic()))[0], 'profile_api_shutdown_deadline'
        finished = time.monotonic()
        assert finished <= deadline, 'profile_api_shutdown_deadline'
        cost['signal']['api_termination_seconds'] = finished - started
    finally:
        os.close(descriptor)
        cost['signal']['pidfd_closed'] = True; helper.atomic(journal, item)
    def exited():
        value = definition(item, helper, identity['container_id'])
        return value if value['State']['Status'] == 'exited' else None
    current_definition = helper.until(exited, 'profile_container_not_exited', 5)
    assert current_definition['State']['ExitCode'] == 0, 'profile_process_nonzero'
    logs = helper.command(item['docker'] + ['logs', identity['container_id']], combined_output=True)
    data = logs.encode(); private_logs = work / 'invocation-cost-control.log'
    with private_logs.open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600); stream.write(data); stream.flush(); os.fsync(stream.fileno())
    namespace_pid = identity['api']['namespace_pids'][-1]
    markers = ['Started server process [' + str(namespace_pid) + ']', 'Application startup complete.',
               'Application shutdown complete.', 'Finished server process [' + str(namespace_pid) + ']']
    positions = [logs.find(marker) for marker in markers]
    assert all(v >= 0 for v in positions) and positions == sorted(positions), 'profile_application_shutdown_unproven'
    bad = ('traceback', 'application startup failed', 'application shutdown failed', 'lifespan failure',
           'graceful shutdown timeout', 'timeout graceful shutdown exceeded', 'exceeded timeout',
           'error during shutdown', 'error closing')
    assert not any(marker in logs.lower() for marker in bad), 'profile_application_shutdown_failed'
    info = output.lstat()
    assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == item['uid'] and 0 < info.st_size <= 32 * 1024**2
    assert info.st_mtime_ns >= sent_ns, 'profile_file_not_fresh'
    raw = output.read_bytes()
    cost['file'] = {'bytes': len(raw), 'sha256': sha(raw), 'device': info.st_dev, 'inode': info.st_ino,
                    'mtime_ns': str(info.st_mtime_ns), 'ctime_ns': str(info.st_ctime_ns)}
    helper.atomic(journal, item)
    projection = parse_stats(item, journal, helper)
    assert cost.get('seal_failure') is None, 'profile_stats_seal_failed'
    again = output.lstat()
    assert (again.st_dev, again.st_ino, again.st_size, again.st_mtime_ns) == (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    assert sha(output.read_bytes()) == cost['file']['sha256']
    seal_stats(item,journal,helper)
    assert time.time() < window - 60, 'profile_collection_margin_exhausted'
    cost['completed'] = True
    result = {'completed': True, 'qualified_groups': 0, 'mode': cost['mode'], 'image': IMAGE,
              'process': identity, 'runtime': cost['runtime'], 'signal': cost['signal'], 'file': cost['file'],
              'profiler_exit_code': current_definition['State']['ExitCode'],
              'application_shutdown': {'markers': markers, 'positions': positions, 'verified': True,
                                       'logs_bytes': len(data), 'logs_sha256': sha(data)},
              'parser': cost['parser'], 'projection': projection, 'sealed_directory': cost['sealed_identity'],
              'http_invocations': expected, 'invocation_ids_sha256': sha(json.dumps(sorted(v['id'] for v in calls), separators=(',', ':')).encode()),
              'limitations': ['Interpreter-global callbacks, real time, whole lifecycle, explicit profiling overhead; no TID/task attribution.',
                             'Raw callers timings do not provide a reliable cost decomposition; inconsistencies remain unaltered.',
                             'Overlapping cumulative values are not summed as CPU; coroutine resumptions are not invocations.',
                             'No COMMIT-body, fsync or pure network duration is inferred from SQL RO or client intervals.']}
    helper.atomic(work / 'invocation-cost-profile.json', result)
    helper.atomic(journal, item)
    return result


# @verifies docs/BACKLOG.md#sls-133 | docs/INVOCATION_PRODUCTION_PROFILE.md#perte-réelle-après-création-du-parser--sls-1336
def status(item, helper):
    cost, _ = context(item, helper, allow_restored=True)
    driver_state = None
    try:
        identity, _ = process(item['driver_pid'])
        if identity['birth'] == item['driver_birth']: driver_state = identity['state']
    except (FileNotFoundError, ProcessLookupError): pass
    intent = cost.get('parser'); parser = None
    if intent is not None:
        ids = helper.docker(item,'ps','-aq','--filter','name=^/'+intent['name']+'$').split()
        if ids:
            assert not item.get('restored'), 'profile_parser_retained_after_restore'
            native = parser_owned(item, helper)
            parser = {'id':native['Id'],'image':native['Image'],'state':native['State']['Status'],
                      'running':native['State']['Running'],'loss_point':intent.get('loss_point')}
    return {'mode':cost['mode'],'completed':bool(cost.get('completed')),'driver_state':driver_state,
            'parser':parser,'parser_absent':parser is None,'stats_sealed':bool(cost.get('sealed_identity')),
            'seal_failure':cost.get('seal_failure')}
