# @spec docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
# @verifies docs/BACKLOG.md#sls-031 | docs/SERVICE_CONFIGURATION_URLS.md#preuve-de-transport
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#barrière-native-de-pause-et-libération
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#perte-native-du-catalogue-après-publication-cli
"""Shared read-only native syscall observer for the real DEV control.

The implementation is moved unchanged from service-transport-observer.py.
Callers own their request scope, process identity, independent recovery and
lifecycle; this class never replaces buffers, registers or syscall results.
"""
import ctypes
import os
import time


class NativeObserver:
    """Read syscall metadata and a bounded public request line, never credentials."""
    def __init__(self, pid):
        self.pid, self.attached, self.stopped = pid, False, False
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.libc.ptrace.restype = ctypes.c_long
        self.libc.ptrace.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        self.memory = None

    def ptrace(self, request, address=0, data=0):
        ctypes.set_errno(0)
        value = self.libc.ptrace(request, self.pid, address, data)
        if value == -1 and ctypes.get_errno():
            raise OSError(ctypes.get_errno(), 'native_observation_failed')
        return value

    def start(self):
        # SEIZE + INTERRUPT avoids sending SIGSTOP to the application group.
        self.ptrace(0x4206, 0, 1)  # PTRACE_SEIZE, TRACESYSGOOD; no EXITKILL.
        self.attached = True
        self.ptrace(0x4207)  # PTRACE_INTERRUPT
        self.wait(time.monotonic() + 5)
        self.memory = os.open(f'/proc/{self.pid}/mem', os.O_RDONLY)

    def wait(self, deadline):
        while True:
            value, status = os.waitpid(self.pid, os.WNOHANG)
            if value:
                assert os.WIFSTOPPED(status), 'control_exited_during_observation'
                self.stopped = True
                return os.WSTOPSIG(status)
            assert time.monotonic() < deadline, 'native_stop_not_observed'
            time.sleep(.001)

    def resume(self, delivered=0):
        self.ptrace(24, 0, delivered)  # PTRACE_SYSCALL
        self.stopped = False

    def info(self):
        buffer = ctypes.create_string_buffer(88)
        self.ptrace(0x420e, 88, ctypes.addressof(buffer))  # GET_SYSCALL_INFO
        raw = buffer.raw
        assert int.from_bytes(raw[4:8], 'little') == 0xc000003e, 'x86_64_syscall_required'
        op = raw[0]
        if op == 1:
            return op, [int.from_bytes(raw[i:i+8], 'little') for i in range(24, 80, 8)]
        if op == 2:
            return op, int.from_bytes(raw[24:32], 'little', signed=True)
        return op, None

    def match_line(self, pointer, count, expected, offset):
        # One byte at a time stops at CRLF, even when headers share this recv.
        while count and offset < len(expected):
            value = os.pread(self.memory, 1, pointer)
            if value != expected[offset:offset+1]:
                return None
            pointer, count, offset = pointer + 1, count - 1, offset + 1
        return offset

    def detach(self):
        if self.memory is not None:
            os.close(self.memory)
            self.memory = None
        if self.attached:
            try:
                if not self.stopped:
                    self.ptrace(0x4207)
                    self.wait(time.monotonic() + 5)
                self.ptrace(17)  # PTRACE_DETACH
            except (OSError, ProcessLookupError, ChildProcessError):
                pass  # Independent restorer still verifies the original owner.
            self.attached = False
