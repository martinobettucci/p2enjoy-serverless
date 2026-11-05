# @spec docs/BACKLOG.md#sls-010 | docs/PLATFORM.md#stockage
# @verifies docs/BACKLOG.md#sls-010 | docs/PLATFORM.md#stockage
# Real filesystem client: all operations cross the mounted FUSE filesystem.
import concurrent.futures
import ctypes
import errno
import fcntl
import json
import mmap
import os
from pathlib import Path
import shutil
import sys
import threading
import time

A, B = Path('/data-a'), Path('/data-b')
BLOCK, LIMIT = 4096, 1024 * 1024
RESULTS = []


def usage(path=A):
    v = os.statvfs(path)
    assert v.f_blocks * v.f_frsize == LIMIT
    return (v.f_blocks - v.f_bavail) * v.f_frsize


def eventually(expected, path=A):
    deadline = time.monotonic() + 5
    while usage(path) != expected and time.monotonic() < deadline:
        time.sleep(.01)
    assert usage(path) == expected, (usage(path), expected)


def clean():
    for root in (A, B):
        for p in root.iterdir():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        eventually(0, root)


def refused(action, *codes):
    try:
        result = action()
    except OSError as exc:
        assert exc.errno in codes, (exc.errno, codes)
    else:
        if hasattr(result,'close'): result.close()
        raise AssertionError('operation unexpectedly allowed')


def case(name, action):
    try:
        clean()
        action()
        clean()
        RESULTS.append({'name': name, 'status': 'passed'})
    except Exception as exc:
        RESULTS.append({'name': name, 'status': 'failed', 'error': str(exc)})


def basic():
    with (A/'value').open('wb') as f:
        f.write(b'persisted'); f.flush(); os.fsync(f.fileno())
    assert (A/'value').read_bytes() == b'persisted'
    eventually(2 * BLOCK)
    os.chmod(A/'value', 0o600)
    assert (A/'value').stat().st_mode & 0o777 == 0o600


def directory_sync():
    (A/'dir').mkdir()
    with (A/'dir'/'value').open('wb') as f:
        f.write(b'renamed'); f.flush(); os.fsync(f.fileno())
    os.rename(A/'dir'/'value', A/'dir'/'durable')
    fd = os.open(A/'dir', os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    assert (A/'dir'/'durable').read_bytes() == b'renamed'
    eventually(3 * BLOCK)


def saturation():
    with (A/'full').open('wb', buffering=0) as f:
        assert f.write(b'x'*(LIMIT-BLOCK)) == LIMIT-BLOCK
        refused(lambda: f.write(b'x'), errno.EDQUOT)
        refused(lambda: (A/'another').touch(), errno.EDQUOT)
    eventually(LIMIT)
    assert (A/'full').stat().st_size == LIMIT-BLOCK
    (B/'independent').write_bytes(b'ok')
    assert (B/'independent').read_bytes() == b'ok'


def truncate():
    (A/'size').write_bytes(b'x'*5000)
    eventually(3*BLOCK)
    os.truncate(A/'size', 1)
    eventually(2*BLOCK)
    refused(lambda: os.truncate(A/'size', LIMIT), errno.EDQUOT)
    assert (A/'size').stat().st_size == 1
    with (A/'size').open('r+b') as f:
        os.ftruncate(f.fileno(), 9000)
        eventually(4*BLOCK)
        refused(lambda: os.ftruncate(f.fileno(), LIMIT), errno.EDQUOT)
    (A/'size').write_bytes(b'')
    eventually(BLOCK)


def sparse():
    fd = os.open(A/'sparse', os.O_CREAT|os.O_RDWR, 0o600)
    try:
        refused(lambda: os.pwrite(fd, b'x', LIMIT), errno.EDQUOT)
        assert os.pwrite(fd,b'x',LIMIT-BLOCK-1) == 1
        assert os.fstat(fd).st_size == LIMIT-BLOCK
    finally:
        os.close(fd)
    eventually(LIMIT)


def open_unlink():
    fd = os.open(A/'held', os.O_CREAT|os.O_RDWR, 0o600)
    try:
        os.write(fd,b'x'*(LIMIT-BLOCK))
        os.unlink(A/'held')
        eventually(LIMIT)
        refused(lambda: (A/'other').touch(), errno.EDQUOT)
        assert os.pread(fd, 1, 0) == b'x'
        os.ftruncate(fd, 0)
        eventually(BLOCK)
        os.pwrite(fd,b'y',0)
        eventually(2*BLOCK)
    finally:
        os.close(fd)
    eventually(0)


def multi_open():
    (A/'shared').write_bytes(b'x')
    one = os.open(A/'shared',os.O_RDWR)
    two = os.open(A/'shared',os.O_RDWR)
    try:
        (A/'shared').unlink()
        eventually(2*BLOCK)
        os.close(one); one = None
        eventually(2*BLOCK)
        assert os.pwrite(two,b'z',BLOCK) == 1
        eventually(3*BLOCK)
    finally:
        if one is not None: os.close(one)
        os.close(two)
    eventually(0)


def open_rmdir():
    (A/'held-dir').mkdir()
    fd=os.open(A/'held-dir',os.O_DIRECTORY)
    try:
        (A/'held-dir').rmdir()
        eventually(BLOCK)
    finally:
        os.close(fd)
    eventually(0)


def replace_open():
    (A/'old').write_bytes(b'old')
    (A/'new').write_bytes(b'new')
    fd = os.open(A/'old',os.O_RDWR)
    try:
        os.replace(A/'new',A/'old')
        eventually(4*BLOCK)
        assert os.pread(fd,3,0) == b'old'
        assert (A/'old').read_bytes() == b'new'
        os.pwrite(fd,b'old-tail',2*BLOCK)
        eventually(6*BLOCK)
    finally:
        os.close(fd)
    eventually(2*BLOCK)


def concurrency():
    # One bounded contention scenario; the campaign itself remains serial.
    barrier = threading.Barrier(2, timeout=5)
    def writer(index):
        total = 0
        with (A/f'writer-{index}').open('wb',buffering=0) as f:
            barrier.wait()
            while True:
                try: total += f.write(b'x'*BLOCK)
                except OSError as exc:
                    assert exc.errno == errno.EDQUOT
                    return total
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        totals = list(pool.map(writer, (1,2)))
    assert sum(totals) <= LIMIT-2*BLOCK
    assert usage() <= LIMIT


def empty_entries():
    for index in range(LIMIT//BLOCK):
        (A/f'empty-{index}').touch()
    eventually(LIMIT)
    refused(lambda: (A/'extra-dir').mkdir(), errno.EDQUOT)
    (A/'empty-0').unlink()
    eventually(LIMIT-BLOCK)
    (A/'extra-dir').mkdir()
    eventually(LIMIT)


def prohibited():
    (A/'source').write_bytes(b'x')
    for action in (
        lambda: os.link(A/'source',A/'hard'),
        lambda: os.symlink('/etc/passwd',A/'symbolic'),
        lambda: os.mkfifo(A/'pipe'),
        lambda: os.setxattr(A/'source',b'user.example',b'value'),
    ):
        refused(action,errno.EOPNOTSUPP,errno.ENOSYS)
    fd=os.open(A/'source',os.O_RDWR)
    try:
        libc=ctypes.CDLL(None,use_errno=True)
        libc.fallocate.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_longlong]
        assert libc.fallocate(fd,0,0,LIMIT) == -1
        assert ctypes.get_errno() == errno.EOPNOTSUPP
        refused(lambda: os.open(A,os.O_TMPFILE|os.O_RDWR,0o600),errno.EOPNOTSUPP)
        refused(lambda: fcntl.ioctl(fd,0x40049409,fd),errno.EOPNOTSUPP,errno.ENOTTY)
    finally:
        os.close(fd)
    eventually(2*BLOCK)


def directory_ioctl():
    fd=os.open(A,os.O_DIRECTORY)
    try:
        refused(lambda: fcntl.ioctl(fd,0x80086601,bytearray(8),True),errno.EOPNOTSUPP)
    finally:
        os.close(fd)


def copy_range():
    (A/'source').write_bytes(b'x'*BLOCK)
    source=os.open(A/'source',os.O_RDWR)
    target=os.open(A/'target',os.O_CREAT|os.O_RDWR,0o600)
    try:
        # Linux may fall back to read/write after FUSE rejects acceleration.
        assert os.copy_file_range(source,target,BLOCK) == BLOCK
        assert os.pread(target,BLOCK,0) == b'x'*BLOCK
        refused(lambda: os.copy_file_range(source,target,BLOCK,offset_src=0,offset_dst=LIMIT),errno.EDQUOT)
    finally:
        os.close(source);os.close(target)


def shared_mmap():
    (A/'source').write_bytes(b'x'*BLOCK)
    source=os.open(A/'source',os.O_RDWR)
    try:
        refused(lambda: mmap.mmap(source,BLOCK,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ|mmap.PROT_WRITE),errno.ENODEV)
    finally:
        os.close(source)


def copy_and_append():
    (A/'source').write_bytes(b'original')
    shutil.copyfile(A/'source',A/'copy')
    assert (A/'copy').read_bytes() == b'original'
    with (A/'copy').open('ab') as f: f.write(b' tail')
    assert (A/'copy').read_bytes() == b'original tail'
    os.rename(A/'copy',A/'copy')
    eventually(4*BLOCK)


if sys.argv[1:] == ['persist-write']:
    clean()
    with (A/'persistent').open('wb') as f:
        f.write(b'p2enjoy-native-files-survive'); f.flush(); os.fsync(f.fileno())
    print(json.dumps({'name':'persist-write','status':'passed'}))
elif sys.argv[1:] == ['persist-read']:
    assert (A/'persistent').read_bytes() == b'p2enjoy-native-files-survive'
    eventually(2*BLOCK)
    clean()
    print(json.dumps({'name':'persist-read','status':'passed'}))
elif sys.argv[1:] == ['unavailable']:
    assert (A/'persistent').read_bytes() == b'p2enjoy-native-files-survive'
    print('READY',flush=True)
    assert input() == 'CHECK'
    refused(lambda: (A/'must-fail').write_bytes(b'x'), errno.ENOTCONN,errno.EIO)
    print(json.dumps({'name':'disconnected-mount-refuses-write','status':'passed'}))
else:
    for name,action in (
        ('read-write-fsync-chmod',basic),('directory-fsync-rename',directory_sync),
        ('saturation-isolation',saturation),('truncate-both-paths',truncate),
        ('sparse-charged',sparse),('open-unlink',open_unlink),
        ('multiple-open-handles',multi_open),('rename-open-destination',replace_open),
        ('open-removed-directory',open_rmdir),
        ('concurrent-growth',concurrency),('empty-entry-bound',empty_entries),
        ('alternate-mutations-refused',prohibited),('copy-append-self-rename',copy_and_append),
        ('directory-ioctl-refused',directory_ioctl),('copy-range-quota',copy_range),('shared-mmap-refused',shared_mmap),
    ):
        case(name,action)
    print(json.dumps(RESULTS))
    if any(r['status']!='passed' for r in RESULTS): sys.exit(1)
