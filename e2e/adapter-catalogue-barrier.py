# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#révocation-avant-le-get-facultatif
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#révocation-avant-le-get-facultatif
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_DOMAINS_PAGINATION.md#cycle-borné-et-preuves-retenues
"""Pause the real adapter before its sixth or seventh HTTPS connect.

All helpers share this contract. Native ABI: Linux x86_64 ptrace(2),
https://man7.org/linux/man-pages/man2/ptrace.2.html.
"""
import ctypes
import json
import os
from pathlib import Path
import platform
import select
import signal
import sys
import time
from uuid import UUID


def emit(value):
    print(json.dumps(value), flush=True)


def main():
    assert platform.system() == 'Linux' and platform.machine() == 'x86_64', 'linux_x86_64_required'
    assert len(sys.argv) in (3, 4), 'manifest_service_and_optional_boundary_required'
    manifest, service = sys.argv[1:3]
    boundary = int(sys.argv[3]) if len(sys.argv) == 4 else 6
    assert boundary in (6, 7), 'authorized_boundary_required'
    assert str(UUID(service)) == service and Path(manifest).is_file()
    assert os.environ.get('P2_SERVERLESS_URL') == 'https://serverless.lelabs.tech'
    credential = os.environ.get('P2_SERVERLESS_TOKEN', '')
    assert credential and len(credential) <= 4096
    libc = ctypes.CDLL(None, use_errno=True)
    libc.ptrace.restype = ctypes.c_long
    libc.ptrace.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]

    def ptrace(request, pid, address=0, data=0):
        ctypes.set_errno(0)
        value = libc.ptrace(request, pid, address, data)
        if value == -1 and ctypes.get_errno():
            raise OSError(ctypes.get_errno(), 'adapter_native_observation_failed')
        return value

    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(stdout_read); os.close(stderr_read)
            os.dup2(stdout_write, 1); os.dup2(stderr_write, 2)
            os.close(stdout_write); os.close(stderr_write)
            null = os.open('/dev/null', os.O_RDONLY); os.dup2(null, 0); os.close(null)
            ptrace(0, 0)  # TRACEME: this exact child, before executing the adapter.
            os.kill(os.getpid(), signal.SIGSTOP)
            os.execvpe(sys.executable, [sys.executable, '-B', '-m', 'adapter', 'deploy',
                                      '--config', manifest, '--service', service], os.environ)
        except BaseException:
            os.write(2, b'adapter_exec_failed\n')
            os._exit(127)
    os.close(stdout_write); os.close(stderr_write)
    pipes = {stdout_read: bytearray(), stderr_read: bytearray()}
    open_pipes = set(pipes)
    for fd in pipes:
        os.set_blocking(fd, False)
    reaped, armed, gated, pending = False, False, False, False
    attempts, exits = 0, []
    deadline = time.monotonic() + (240 if boundary == 7 else 180)

    def drain():
        for fd in list(open_pipes):
            while True:
                try:
                    chunk = os.read(fd, 65536)
                except BlockingIOError:
                    break
                if not chunk:
                    open_pipes.remove(fd)
                    break
                pipes[fd].extend(chunk)
                assert sum(map(len, pipes.values())) <= 4*1024**2, 'adapter_output_limit'

    try:
        while True:
            drain()
            assert time.monotonic() < deadline, 'adapter_native_deadline'
            waited, status = os.waitpid(pid, os.WNOHANG)
            if not waited:
                time.sleep(.001)
                continue
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                reaped = True
                code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 128 + os.WTERMSIG(status)
                break
            assert os.WIFSTOPPED(status), 'adapter_stop_required'
            stopped = os.WSTOPSIG(status)
            if not armed:
                assert stopped == signal.SIGSTOP, 'adapter_initial_stop_required'
                # TRACESYSGOOD | EXITKILL: no surviving CLI if this tracer dies.
                ptrace(0x4200, pid, 0, 1 | 0x100000)
                armed = True
                emit({'event': 'armed', 'child_pid': pid, 'exitkill': True})
            elif stopped == signal.SIGTRAP | 0x80:
                buffer = ctypes.create_string_buffer(88)
                ptrace(0x420e, pid, 88, ctypes.addressof(buffer))
                raw = buffer.raw
                assert int.from_bytes(raw[4:8], 'little') == 0xc000003e, 'x86_64_syscall_required'
                if raw[0] == 1:
                    number, *args = [int.from_bytes(raw[i:i+8], 'little') for i in range(24, 80, 8)]
                    pending = False
                    if number == 42 and 4 <= args[2] <= 128:  # connect(fd, sockaddr, size)
                        fd = os.open(f'/proc/{pid}/mem', os.O_RDONLY)
                        try:
                            address = os.pread(fd, min(args[2], 28), args[1])
                        finally:
                            os.close(fd)
                        if int.from_bytes(address[:2], 'little') in (2, 10) and int.from_bytes(address[2:4], 'big') == 443:
                            attempts += 1; pending = True
                            assert attempts <= boundary, 'unexpected_extra_https_attempt'
                            if attempts == boundary:
                                assert len(exits) == boundary - 1 and all(value in (0, -115) for value in exits), 'prior_connects_required'
                                gated = True
                                emit({'event': 'gated', 'boundary': 'before-sixth-https-connect' if boundary == 6 else 'before-seventh-https-connect',
                                      'child_pid': pid, 'https_connect_attempts': attempts, 'prior_connect_results': exits})
                                release_end = min(deadline, time.monotonic() + (90 if boundary == 7 else 20))
                                release = bytearray()
                                while not release.endswith(b'\n'):
                                    remaining = release_end - time.monotonic()
                                    assert remaining > 0 and select.select([0], [], [], remaining)[0], 'adapter_release_deadline'
                                    byte = os.read(0, 1)
                                    assert byte, 'adapter_release_eof'
                                    release.extend(byte)
                                    assert len(release) <= 16, 'adapter_release_limit'
                                assert release == b'release\n', 'adapter_release_required'
                elif raw[0] == 2 and pending:
                    exits.append(int.from_bytes(raw[24:32], 'little', signed=True)); pending = False
            elif stopped != signal.SIGTRAP:
                ptrace(24, pid, 0, stopped)
                continue
            ptrace(24, pid)  # SYSCALL: original operation, unchanged arguments/result.
        drain()
        assert not open_pipes, 'adapter_output_still_open'
        stdout = pipes[stdout_read].decode('utf-8', errors='strict')
        stderr = pipes[stderr_read].decode('utf-8', errors='strict')
        assert credential not in stdout and credential not in stderr, 'adapter_credential_exposure'
        assert gated and attempts == len(exits) == boundary and all(value in (0, -115) for value in exits)
        emit({'event': 'finished', 'exit_code': code, 'stdout': stdout, 'stderr': stderr,
              'https_connect_attempts': attempts, 'connect_results': exits, 'child_reaped': True})
    finally:
        if not reaped:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            end = time.monotonic() + 10
            while True:
                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited and (os.WIFEXITED(status) or os.WIFSIGNALED(status)):
                    break
                assert time.monotonic() < end, 'adapter_child_stop_unknown'
                time.sleep(.01)
        for fd in pipes:
            os.close(fd)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        # Never print an exception containing argv, environment or client output.
        print('adapter_catalogue_barrier_failed', file=sys.stderr)
        sys.exit(1)
