# @spec docs/BACKLOG.md#sls-112 | docs/MANAGED_INVOCATION_WATCH.md
# @verifies docs/BACKLOG.md#sls-112 | docs/MANAGED_INVOCATION_WATCH.md#expérience-bornée-avant-correction
"""Observe genuine invocation/watcher tasks around real Docker/FUSE deadlines."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from uuid import UUID, uuid4

ROOT = Path('/srv/p2enjoy-serverless')
CONFIGURATION = {kind: {'enabled': True, 'quota_mib': 1} for kind in ('data', 'cache')}
DEADLINES = tuple(value / 100 for value in range(175, 221, 5))


def emit(value):
    print(json.dumps(value), flush=True)


def diagnostic(error):
    frames = []
    trace = error.__traceback__
    while trace:
        frames.append({'file': Path(trace.tb_frame.f_code.co_filename).name,
                       'function': trace.tb_frame.f_code.co_name, 'line': trace.tb_lineno})
        trace = trace.tb_next
    return {'type': type(error).__name__, 'frames': frames,
            'message_sha256': hashlib.sha256(str(error).encode(errors='replace')).hexdigest()}


def result_projection(result):
    return {key: result.get(key) for key in ('invocation_id', 'instance_id', 'state',
            'handler_started', 'instance_available', 'container_removed', 'elapsed_seconds')} | {
        'error': result.get('error') if isinstance(result.get('error'), str)
        and re.fullmatch('[a-z_]{1,64}', result['error']) else None}


async def worker(installation):
    sys.path.insert(0, '/app')
    from app.managed_instances import ManagedInstance
    from app.storage_client import StorageClient
    owner = asyncio.current_task()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, owner.cancel)
    storage = StorageClient('/storage-agent/agent.sock', os.environ['SERVERLESS_STORAGE_ROOT_HOST'])
    work = Path(tempfile.mkdtemp(prefix='invocation-watch-proof-', dir='/state'))
    function_id = str(uuid4())
    instances = []
    checks = []
    observations = []
    cleanup_errors = []
    completed = False
    failure = None
    observer = None
    observer_stop = None

    def instance():
        item = ManagedInstance(docker_socket='/docker.sock',
            image=os.environ['SERVERLESS_RUNTIME_IMAGE'], code=str(ROOT / 'qualification/artifacts'),
            work=work, host_work=Path(os.environ['SERVERLESS_STATE_HOST_PATH']) / work.name,
            installation=installation, function_id=function_id, revision_id=str(uuid4()),
            handler='volume-operations.cjs.handler', function_name='storage-deadline-observation',
            environment={}, secrets={}, storage=storage, storage_configuration=CONFIGURATION)
        instances.append(item)
        return item

    async def close(item):
        async with asyncio.timeout(40):
            while not await item.close():
                await asyncio.sleep(.2)
        assert item.removed and not item.lease_possible and not item.cleanup_error, 'watch_close_state'
        assert await item.call('GET', '/containers/' + item.name + '/json', allowed=(404,)), 'watch_close_container'
        assert await item.call('GET', '/networks/' + item.name, allowed=(404,)), 'watch_close_network'
        assert item.channel is None or not item.channel.exists(), 'watch_close_channel'
        assert not any(row['consumer_id'] == item.id for row in await storage.leases(installation)), 'watch_close_lease'

    async def observe_tasks(item, stop, record):
        seen = set()

        def terminal(task, role):
            value = {'role': role, 'observed_monotonic_ns': time.monotonic_ns(),
                     'instance_id': item.id, 'closing': item.closing,
                     'lease_possible': item.lease_possible, 'cancelled': task.cancelled()}
            if not task.cancelled():
                error = task.exception()
                if error is not None:
                    text = str(error)
                    value['error'] = text if re.fullmatch('[a-z_]{1,64}', text) else 'other_error'
                    value['error_type'] = type(error).__name__
                elif role == 'internal-invocation':
                    value['result'] = result_projection(task.result())
                else:
                    value['returned'] = True
            record['task_terminals'].append(value)

        while not stop.is_set():
            for task in asyncio.all_tasks():
                coroutine = task.get_coro()
                role = {'Instance.invoke': 'internal-invocation',
                        'ManagedInstance.watch_storage': 'storage-watcher'}.get(
                            getattr(coroutine, '__qualname__', ''))
                frame = getattr(coroutine, 'cr_frame', None)
                # Read only self identity; never retain the frame or any locals.
                if not role or frame is None or frame.f_locals.get('self') is not item or task in seen:
                    continue
                seen.add(task)
                record['tasks_observed'].append(role)
                task.add_done_callback(lambda finished, role=role: terminal(finished, role))
            try:
                await asyncio.wait_for(stop.wait(), .01)
            except TimeoutError:
                pass

    try:
        await storage.call('configure', function_id=function_id, configuration=CONFIGURATION)
        for index, deadline in enumerate(DEADLINES):
            item = await instance().start()
            record = {'case': index + 1, 'deadline_seconds': deadline, 'instance_id': item.id,
                      'tasks_observed': [], 'task_terminals': []}
            observations.append(record)
            observer_stop = asyncio.Event()
            observer = asyncio.create_task(observe_tasks(item, observer_stop, record))
            name = 'deadline-' + str(index + 1)
            expected = 'persisted-' + str(index + 1)
            result = await item.invoke({'operation': 'write-sleep', 'name': name,
                                        'value': expected, 'ms': 30000}, deadline)
            record['final_result'] = result_projection(result)
            observer_stop.set()
            await observer
            observer = None
            # All genuine product tasks have been joined by ManagedInstance.invoke.
            await asyncio.sleep(0)
            await close(item)
            record['consumer_bail_absent'] = not any(
                row['consumer_id'] == item.id for row in await storage.leases(installation))
            reader = await instance().start()
            read = await reader.invoke({'operation': 'read', 'name': name}, 5)
            record['read_result'] = result_projection(read)
            body = json.loads(read['response']['body']) if read.get('response') else {}
            value = body.get('value')
            record['read_matches_expected'] = value == expected
            record['read_sha256'] = hashlib.sha256(value.encode()).hexdigest() if isinstance(value, str) else None
            await close(reader)
            assert sorted(record['tasks_observed']) == ['internal-invocation', 'storage-watcher'], 'watch_tasks_missing'
            assert len(record['task_terminals']) == 2, 'watch_terminals_missing'
            assert result['state'] == 'failed' and result.get('error') == 'invocation_timeout', 'watch_timeout_overwritten'
            assert result['handler_started'] is True and not result['instance_available'] and result['container_removed'], 'watch_timeout_lifecycle'
            assert read['state'] == 'succeeded' and read['response']['statusCode'] == 200 and record['read_matches_expected'], 'watch_write_not_observed'
            checks.append({'name': f'Deadline réelle {deadline:.2f}s et surveillance jointe', 'status': 'passed'})
            emit({'passed': checks[-1]['name']})
        record = {'case': 11, 'scenario': 'external-close', 'deadline_seconds': 5,
                  'tasks_observed': [], 'task_terminals': [], 'prior_write_acknowledged': False}
        observations.append(record)
        writer = instance()
        record['writer_instance_id'] = writer.id
        await writer.start()
        written = await writer.invoke({'operation': 'write', 'name': 'drained-record',
                                       'value': 'acknowledged-before-drain'}, 5)
        record['write_result'] = result_projection(written)
        assert written['state'] == 'succeeded' and written['response']['statusCode'] == 200, 'watch_drain_write_ack'
        record['prior_write_acknowledged'] = True
        await close(writer)
        item = await instance().start()
        record['instance_id'] = item.id
        observer_stop = asyncio.Event()
        observer = asyncio.create_task(observe_tasks(item, observer_stop, record))
        record['invocation_requested_monotonic_ns'] = time.monotonic_ns()
        invoking = asyncio.create_task(item.invoke({'operation': 'write-sleep',
            'name': 'drained-record', 'value': 'acknowledged-before-drain', 'ms': 30000}, 5))
        try:
            async with asyncio.timeout(5):
                while not item.started_observed:
                    assert not invoking.done(), 'watch_drain_handler_not_started'
                    await asyncio.sleep(.01)
            record['close_requested_monotonic_ns'] = time.monotonic_ns()
            assert (record['close_requested_monotonic_ns'] - record['invocation_requested_monotonic_ns']
                    < 5_000_000_000), 'watch_drain_requested_after_deadline'
            await close(item)
            result = await invoking
        finally:
            if not invoking.done():
                invoking.cancel()
                await asyncio.gather(invoking, return_exceptions=True)
        record['final_result'] = result_projection(result)
        observer_stop.set()
        await observer
        observer = None
        await asyncio.sleep(0)
        reader = await instance().start()
        read = await reader.invoke({'operation': 'read', 'name': 'drained-record'}, 5)
        record['read_result'] = result_projection(read)
        body = json.loads(read['response']['body']) if read.get('response') else {}
        record['read_matches_expected'] = body.get('value') == 'acknowledged-before-drain'
        await close(reader)
        assert result['state'] == 'failed' and result.get('error') == 'instance_stopped', 'watch_drain_result'
        assert result['handler_started'] is True and result['instance_available'] is False, 'watch_drain_lifecycle'
        assert sorted(record['tasks_observed']) == ['internal-invocation', 'storage-watcher'], 'watch_drain_tasks_missing'
        assert len(record['task_terminals']) == 2, 'watch_drain_terminals_missing'
        assert read['state'] == 'succeeded' and read['response']['statusCode'] == 200 and record['read_matches_expected'], 'watch_drain_persistence'
        checks.append({'name': 'Fermeture extérieure, invocation active et écriture acquittée conservée', 'status': 'passed'})
        emit({'passed': checks[-1]['name']})
        assert any(terminal.get('error_type') == 'LeaseMissingDuringClose'
                   and terminal.get('error') == 'lease_unknown' and terminal['closing']
                   for record in observations for terminal in record['task_terminals']), 'watch_closing_lease_branch_unobserved'
        completed = True
    except BaseException as error:
        failure = diagnostic(error)
    finally:
        if observer is not None:
            observer_stop.set()
            try:
                await observer
            except BaseException as error:
                cleanup_errors.append(type(error).__name__)
        for item in instances:
            try:
                await close(item)
            except BaseException as error:
                cleanup_errors.append(type(error).__name__)
        for operation in ('archive', 'purge'):
            try:
                await storage.call(operation, function_id=function_id)
            except BaseException as error:
                cleanup_errors.append(type(error).__name__)
        try:
            assert not await storage.leases(installation)
            assert not list(work.iterdir())
            work.rmdir()
        except BaseException as error:
            cleanup_errors.append(type(error).__name__)
        emit({'report': {'completed': completed and not cleanup_errors, 'cleanup': not cleanup_errors,
            'skipped': 0, 'checks': checks, 'failure': failure, 'observations': observations,
            'cleanup_errors': cleanup_errors, 'installation_id': installation, 'functions': [function_id]}})


def parent():
    assert os.geteuid() == 0 and Path('/etc/hostname').read_text().strip() == 'infra-serverless'
    report = ROOT / 'runtime/managed-invocation-watch-proof.json'
    report.write_text(json.dumps({'completed': False, 'cleanup': False}) + '\n')
    installation = str(uuid4())
    script = '/tmp/managed-invocation-watch-' + UUID(installation).hex + '.py'
    docker = ['runuser', '-u', 'spark-docker', '--', 'docker', '--host', 'unix:///run/user/1001/docker.sock']

    def run(args, **kwargs):
        return subprocess.run(args, check=True, text=True, capture_output=True, timeout=90, **kwargs)

    run(docker + ['exec', '-i', 'serverless-api', 'python', '-B', '-c',
        'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text(sys.stdin.read())', script], input=Path(__file__).read_text())
    transport = ROOT / 'runtime' / ('invocation-watch-transport-' + UUID(installation).hex)
    transport.mkdir(mode=0o700)
    process = None
    script_removed = False
    parent_failure = None
    join_failure = None
    output = errors = b''
    joined = False
    try:
        process = subprocess.Popen(docker + ['exec', 'serverless-api', 'python', '-B', script, '--worker', installation],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, errors = process.communicate(timeout=240)
            joined = True
        except BaseException as error:
            parent_failure = diagnostic(error)
            stop = "import os,pathlib,signal,sys\nfor p in pathlib.Path('/proc').iterdir():\n if p.name.isdigit() and int(p.name)!=os.getpid():\n  try:args=p.joinpath('cmdline').read_bytes().split(b'\\0')\n  except OSError:continue\n  if sys.argv[1].encode() in args:os.kill(int(p.name),signal.SIGTERM)"
            try:
                run(docker + ['exec', 'serverless-api', 'python', '-B', '-c', stop, script])
            except BaseException as stop_error:
                join_failure = diagnostic(stop_error)
            try:
                output, errors = process.communicate(timeout=60)
                joined = True
            except subprocess.TimeoutExpired as join_error:
                output, errors = join_error.output or b'', join_error.stderr or b''
                join_failure = diagnostic(join_error)
        streams = {}
        for name, raw in (('stdout', output), ('stderr', errors)):
            path = transport / name
            with path.open('xb') as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            streams[name] = {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        final = None
        try:
            for line in output.splitlines():
                frame = json.loads(line)
                if 'report' in frame:
                    assert final is None, 'watch_duplicate_report'
                    final = frame['report']
                elif 'passed' in frame:
                    print('PASS ' + frame['passed'], flush=True)
        except BaseException as parse_error:
            parent_failure = parent_failure or diagnostic(parse_error)
        if final is None:
            final = {'completed': False, 'cleanup': False, 'skipped': 0,
                     'checks': [], 'observations': [], 'cleanup_errors': ['worker_report_missing']}
        if joined:
            try:
                run(docker + ['exec', 'serverless-api', 'rm', '-f', script])
                script_removed = True
            except BaseException as remove_error:
                parent_failure = parent_failure or diagnostic(remove_error)
        final['worker_exit_code'] = process.returncode
        final.update(worker_joined=joined, script_removed=script_removed,
                     script_retained_for_reconciliation=not script_removed,
                     parent_failure=parent_failure, join_failure=join_failure, transport=streams)
        final['completed'] = bool(final['completed'] and joined and script_removed
                                  and parent_failure is None and join_failure is None
                                  and process.returncode == 0 and not errors)
        report.write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n')
        assert final['completed'], 'watch_campaign_failed'
    finally:
        # Keep the owned script as an identity for reconciliation if joining failed.
        if not script_removed and process is None:
            run(docker + ['exec', 'serverless-api', 'rm', '-f', script])


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        asyncio.run(worker(str(UUID(sys.argv[2]))))
    else:
        parent()
