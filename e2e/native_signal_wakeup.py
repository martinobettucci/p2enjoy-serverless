# @spec docs/BACKLOG.md#sls-121 | docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
# @verifies docs/BACKLOG.md#sls-121 | docs/BACKLOG.md#sls-123 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
"""Shared real SIGCHLD notification; only the caller consumes waitpid statuses."""
import os
import select
import signal
import sys
import time


class NativeWakeup:
    """Wake on actual SIGCHLD; waitpid alone determines which tracee stopped."""
    def __init__(self):
        self.read_fd=None;self.write_fd=None;self.previous_handler=None
        self.previous_wakeup=None;self.handler_changed=False;self.wakeup_changed=False
        self.waits=0;self.bytes_drained=0

    @staticmethod
    def child_signal(signum,frame):pass

    def start(self):
        self.previous_handler=signal.getsignal(signal.SIGCHLD)
        assert self.previous_handler in (signal.SIG_DFL,signal.SIG_IGN) or callable(self.previous_handler),'unrestorable_child_handler'
        self.read_fd,self.write_fd=os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC)
        try:
            signal.signal(signal.SIGCHLD,self.child_signal);self.handler_changed=True
            self.previous_wakeup=signal.set_wakeup_fd(self.write_fd,warn_on_full_buffer=False);self.wakeup_changed=True
        except BaseException:
            self.close();raise

    def wait(self,deadline):
        remaining=deadline-time.monotonic()
        if remaining<=0:return
        self.waits+=1
        ready=select.select([self.read_fd,sys.stdin],[],[],min(.05,remaining))[0]
        if self.read_fd in ready:
            while True:
                try:
                    raw=os.read(self.read_fd,4096)
                    assert raw,'native_wakeup_pipe_closed'
                    self.bytes_drained+=len(raw)
                except BlockingIOError:break

    def close(self):
        try:
            if self.wakeup_changed:
                signal.set_wakeup_fd(self.previous_wakeup);self.wakeup_changed=False
        finally:
            try:
                if self.handler_changed:
                    signal.signal(signal.SIGCHLD,self.previous_handler);self.handler_changed=False
            finally:
                for name in ('read_fd','write_fd'):
                    fd=getattr(self,name)
                    if fd is not None:
                        os.close(fd);setattr(self,name,None)
