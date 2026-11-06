// @spec docs/BACKLOG.md#sls-010 | docs/PLATFORM.md#stockage
// @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#registre-et-chemins
// All declarations implement the exclusive, bounded, native-file FUSE volume.
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"regexp"
	"sync"
	"syscall"
	"time"

	fusefs "github.com/hanwen/go-fuse/v2/fs"
	"github.com/hanwen/go-fuse/v2/fuse"
)

const block = uint64(4096)

type item struct {
	size   uint64
	refs   int
	linked bool
}
type volume struct {
	sync.Mutex
	limit, used uint64
	items       map[uint64]*item
}

// A per-entry charge bounds empty entries; rounded length charges sparse files.
func charge(size uint64) uint64 { return block + ((size+block-1)/block)*block }
func (v *volume) fits(old, size uint64) bool {
	return size <= v.limit && charge(size) <= v.limit && v.used-charge(old) <= v.limit-charge(size)
}
func (v *volume) resize(ino, size uint64) {
	i := v.items[ino]
	v.used = v.used - charge(i.size) + charge(size)
	i.size = size
}
func (v *volume) add(ino, size uint64) {
	if _, exists := v.items[ino]; exists {
		v.resize(ino, size)
		return
	}
	v.items[ino] = &item{size: size, linked: true}
	v.used += charge(size)
}
func (v *volume) collect(ino uint64) {
	i := v.items[ino]
	if i != nil && !i.linked && i.refs == 0 {
		v.used -= charge(i.size)
		delete(v.items, ino)
	}
}
func (v *volume) unlink(ino uint64) {
	if i := v.items[ino]; i != nil {
		i.linked = false
		v.collect(ino)
	}
}

type node struct {
	fusefs.LoopbackNode
	v *volume
}

func (n *node) path() string {
	return filepath.Join(n.RootData.Path, n.Path(n.RootData.RootNode.EmbeddedInode()))
}
func stat(path string) (syscall.Stat_t, syscall.Errno) {
	var s syscall.Stat_t
	err := syscall.Lstat(path, &s)
	return s, fusefs.ToErrno(err)
}

// The handle is deliberately not embedded: kernel passthrough and ioctl must
// never inherit a way around the quota. Safe operations are delegated below.
type handle struct {
	raw    *fusefs.LoopbackFile
	v      *volume
	ino    uint64
	closed bool
}

// Directory handles keep an unlinked inode charged until released, too.
type directoryOps interface {
	fusefs.FileReaddirenter
	fusefs.FileSeekdirer
	fusefs.FileReleasedirer
	fusefs.FileFsyncdirer
}
type directory struct {
	directoryOps
	v       *volume
	ino     uint64
	counted bool
}

func (d *directory) Releasedir(ctx context.Context, flags uint32) {
	d.v.Lock()
	defer d.v.Unlock()
	d.directoryOps.Releasedir(ctx, flags)
	if d.counted {
		d.v.items[d.ino].refs--
		d.v.collect(d.ino)
	}
}
func (n *node) OpendirHandle(ctx context.Context, flags uint32) (fusefs.FileHandle, uint32, syscall.Errno) {
	n.v.Lock()
	defer n.v.Unlock()
	s, e := stat(n.path())
	if e != 0 {
		return nil, 0, e
	}
	f, opts, e := n.LoopbackNode.OpendirHandle(ctx, flags)
	if e != 0 {
		return nil, 0, e
	}
	i, counted := n.v.items[s.Ino]
	if counted {
		i.refs++
	}
	return &directory{directoryOps: f.(directoryOps), v: n.v, ino: s.Ino, counted: counted}, opts, 0
}

func (n *node) wrap(ctx context.Context, f fusefs.FileHandle) (*handle, syscall.Errno) {
	raw := f.(*fusefs.LoopbackFile)
	var out fuse.AttrOut
	if e := raw.Getattr(ctx, &out); e != 0 {
		raw.Release(ctx)
		return nil, e
	}
	n.v.add(out.Ino, out.Size)
	n.v.items[out.Ino].refs++
	return &handle{raw: raw, v: n.v, ino: out.Ino}, 0
}
func (h *handle) refresh(ctx context.Context) syscall.Errno {
	var a fuse.AttrOut
	if e := h.raw.Getattr(ctx, &a); e != 0 {
		return e
	}
	h.v.resize(h.ino, a.Size)
	return 0
}
func (h *handle) Read(ctx context.Context, data []byte, off int64) (fuse.ReadResult, syscall.Errno) {
	return h.raw.Read(ctx, data, off)
}
func (h *handle) Getattr(ctx context.Context, out *fuse.AttrOut) syscall.Errno {
	return h.raw.Getattr(ctx, out)
}
func (h *handle) Flush(ctx context.Context) syscall.Errno { return h.raw.Flush(ctx) }
func (h *handle) Fsync(ctx context.Context, flags uint32) syscall.Errno {
	return h.raw.Fsync(ctx, flags)
}
func (h *handle) Write(ctx context.Context, data []byte, off int64) (uint32, syscall.Errno) {
	h.v.Lock()
	defer h.v.Unlock()
	i := h.v.items[h.ino]
	if h.closed || i == nil {
		return 0, syscall.EBADF
	}
	if off < 0 || uint64(off) > h.v.limit || uint64(len(data)) > h.v.limit-uint64(off) {
		return 0, syscall.EDQUOT
	}
	size := max(i.size, uint64(off)+uint64(len(data)))
	if !h.v.fits(i.size, size) {
		return 0, syscall.EDQUOT
	}
	// Keep the full reservation if the post-write stat ever fails.
	h.v.resize(h.ino, size)
	written, e := h.raw.Write(ctx, data, off)
	if refresh := h.refresh(ctx); refresh != 0 {
		return written, refresh
	}
	return written, e
}
func (h *handle) Setattr(ctx context.Context, in *fuse.SetAttrIn, out *fuse.AttrOut) syscall.Errno {
	h.v.Lock()
	defer h.v.Unlock()
	if h.closed {
		return syscall.EBADF
	}
	if size, ok := in.GetSize(); ok {
		old := h.v.items[h.ino].size
		if !h.v.fits(old, size) {
			return syscall.EDQUOT
		}
		if size > old {
			h.v.resize(h.ino, size)
		}
	}
	e := h.raw.Setattr(ctx, in, out)
	if refresh := h.refresh(ctx); refresh != 0 {
		return refresh
	}
	return e
}
func (h *handle) Release(ctx context.Context) syscall.Errno {
	h.v.Lock()
	defer h.v.Unlock()
	if h.closed {
		return syscall.EBADF
	}
	h.closed = true
	e := h.raw.Release(ctx)
	h.v.items[h.ino].refs--
	h.v.collect(h.ino)
	return e
}
func (h *handle) Allocate(context.Context, uint64, uint64, uint32) syscall.Errno {
	return syscall.EOPNOTSUPP
}
func (h *handle) PassthroughFd() (int, bool) { return -1, false }
func (h *handle) Ioctl(context.Context, uint32, uint64, []byte, []byte) (int32, syscall.Errno) {
	return -1, syscall.EOPNOTSUPP
}
func (h *handle) Getlk(ctx context.Context, o uint64, l *fuse.FileLock, f uint32, out *fuse.FileLock) syscall.Errno {
	return h.raw.Getlk(ctx, o, l, f, out)
}
func (h *handle) Setlk(ctx context.Context, o uint64, l *fuse.FileLock, f uint32) syscall.Errno {
	return h.raw.Setlk(ctx, o, l, f)
}
func (h *handle) Setlkw(ctx context.Context, o uint64, l *fuse.FileLock, f uint32) syscall.Errno {
	return h.raw.Setlkw(ctx, o, l, f)
}
func (h *handle) Lseek(ctx context.Context, off uint64, whence uint32) (uint64, syscall.Errno) {
	return h.raw.Lseek(ctx, off, whence)
}

func (n *node) Open(ctx context.Context, flags uint32) (fusefs.FileHandle, uint32, syscall.Errno) {
	n.v.Lock()
	defer n.v.Unlock()
	f, _, e := n.LoopbackNode.Open(ctx, flags)
	if e != 0 {
		return nil, 0, e
	}
	h, e := n.wrap(ctx, f)
	return h, fuse.FOPEN_DIRECT_IO, e
}
func (n *node) Create(ctx context.Context, name string, flags, mode uint32, out *fuse.EntryOut) (*fusefs.Inode, fusefs.FileHandle, uint32, syscall.Errno) {
	n.v.Lock()
	defer n.v.Unlock()
	_, exists := stat(filepath.Join(n.path(), name))
	if exists == syscall.ENOENT && n.v.used+block > n.v.limit {
		return nil, nil, 0, syscall.EDQUOT
	}
	child, f, _, e := n.LoopbackNode.Create(ctx, name, flags, mode, out)
	if e != 0 {
		return nil, nil, 0, e
	}
	n.v.add(out.Ino, out.Size)
	h, e := n.wrap(ctx, f)
	return child, h, fuse.FOPEN_DIRECT_IO, e
}
func (n *node) Mkdir(ctx context.Context, name string, mode uint32, out *fuse.EntryOut) (*fusefs.Inode, syscall.Errno) {
	n.v.Lock()
	defer n.v.Unlock()
	if n.v.used+block > n.v.limit {
		return nil, syscall.EDQUOT
	}
	child, e := n.LoopbackNode.Mkdir(ctx, name, mode, out)
	if e == 0 {
		n.v.add(out.Ino, 0)
	}
	return child, e
}
func (n *node) Unlink(ctx context.Context, name string) syscall.Errno {
	n.v.Lock()
	defer n.v.Unlock()
	s, e := stat(filepath.Join(n.path(), name))
	if e != 0 {
		return e
	}
	e = n.LoopbackNode.Unlink(ctx, name)
	if e == 0 {
		n.v.unlink(s.Ino)
	}
	return e
}
func (n *node) Rmdir(ctx context.Context, name string) syscall.Errno {
	n.v.Lock()
	defer n.v.Unlock()
	s, e := stat(filepath.Join(n.path(), name))
	if e != 0 {
		return e
	}
	e = n.LoopbackNode.Rmdir(ctx, name)
	if e == 0 {
		n.v.unlink(s.Ino)
	}
	return e
}
func (n *node) Rename(ctx context.Context, name string, parent fusefs.InodeEmbedder, newName string, flags uint32) syscall.Errno {
	p, ok := parent.(*node)
	if !ok || p.v != n.v {
		return syscall.EXDEV
	}
	// NOREPLACE is safe; EXCHANGE and WHITEOUT require another accounting model.
	if flags > 1 {
		return syscall.EOPNOTSUPP
	}
	n.v.Lock()
	defer n.v.Unlock()
	source, e := stat(filepath.Join(n.path(), name))
	if e != 0 {
		return e
	}
	dest, de := stat(filepath.Join(p.path(), newName))
	e = n.LoopbackNode.Rename(ctx, name, parent, newName, flags)
	if e == 0 && de == 0 && dest.Ino != source.Ino {
		n.v.unlink(dest.Ino)
	}
	return e
}
func (n *node) Setattr(ctx context.Context, f fusefs.FileHandle, in *fuse.SetAttrIn, out *fuse.AttrOut) syscall.Errno {
	if h, ok := f.(*handle); ok {
		return h.Setattr(ctx, in, out)
	}
	n.v.Lock()
	defer n.v.Unlock()
	s, e := stat(n.path())
	if e != 0 {
		return e
	}
	if size, ok := in.GetSize(); ok {
		if s.Mode&syscall.S_IFMT != syscall.S_IFREG {
			return syscall.EISDIR
		}
		if !n.v.fits(n.v.items[s.Ino].size, size) {
			return syscall.EDQUOT
		}
		if size > n.v.items[s.Ino].size {
			n.v.resize(s.Ino, size)
		}
	}
	e = n.LoopbackNode.Setattr(ctx, nil, in, out)
	// Recount even after an error: truncate can succeed before a timestamp fails.
	after, se := stat(n.path())
	if se != 0 {
		return se
	}
	if s.Mode&syscall.S_IFMT == syscall.S_IFREG {
		n.v.resize(s.Ino, uint64(after.Size))
	}
	return e
}
func (n *node) Statfs(ctx context.Context, out *fuse.StatfsOut) syscall.Errno {
	n.v.Lock()
	defer n.v.Unlock()
	out.Bsize = uint32(block)
	out.Frsize = uint32(block)
	out.Blocks = n.v.limit / block
	out.Bfree = (n.v.limit - n.v.used) / block
	out.Bavail = out.Bfree
	out.Files = n.v.limit / block
	out.Ffree = out.Bfree
	out.NameLen = 255
	return 0
}
func (n *node) Symlink(context.Context, string, string, *fuse.EntryOut) (*fusefs.Inode, syscall.Errno) {
	return nil, syscall.EOPNOTSUPP
}
func (n *node) Link(context.Context, fusefs.InodeEmbedder, string, *fuse.EntryOut) (*fusefs.Inode, syscall.Errno) {
	return nil, syscall.EOPNOTSUPP
}
func (n *node) Mknod(context.Context, string, uint32, uint32, *fuse.EntryOut) (*fusefs.Inode, syscall.Errno) {
	return nil, syscall.EOPNOTSUPP
}
func (n *node) Tmpfile(context.Context, uint32, uint32, *fuse.EntryOut) (*fusefs.Inode, fusefs.FileHandle, uint32, syscall.Errno) {
	return nil, nil, 0, syscall.EOPNOTSUPP
}
func (n *node) Setxattr(context.Context, string, []byte, uint32) syscall.Errno {
	return syscall.EOPNOTSUPP
}
func (n *node) Ioctl(context.Context, fusefs.FileHandle, uint32, uint64, []byte, []byte) (int32, syscall.Errno) {
	return -1, syscall.EOPNOTSUPP
}
func (n *node) CopyFileRange(context.Context, fusefs.FileHandle, uint64, *fusefs.Inode, fusefs.FileHandle, uint64, uint64, uint64) (uint32, syscall.Errno) {
	return 0, syscall.EOPNOTSUPP
}
func (n *node) Fsync(ctx context.Context, f fusefs.FileHandle, flags uint32) syscall.Errno {
	if h, ok := f.(*handle); ok {
		return h.Fsync(ctx, flags)
	}
	file, err := os.Open(n.path())
	if err != nil {
		return fusefs.ToErrno(err)
	}
	defer file.Close()
	return fusefs.ToErrno(file.Sync())
}

func run() error {
	backing := flag.String("backing", "", "private native directory")
	mount := flag.String("mount", "", "empty mount directory")
	limit := flag.Uint64("bytes", 0, "logical quota including 4KiB per entry")
	direct := flag.Bool("direct", false, "mount directly with CAP_SYS_ADMIN in the cell")
	name := flag.String("name", "p2quota", "mount generation identity")
	flag.Parse()
	if !regexp.MustCompile(`^[A-Za-z0-9_-]{1,128}$`).MatchString(*name) {
		return errors.New("invalid mount name")
	}
	if *backing == "" || *mount == "" || *limit < block || *limit > 1<<50 {
		return errors.New("backing, mount and bytes (4KiB..1PiB) required")
	}
	var err error
	*backing, err = filepath.EvalSymlinks(*backing)
	if err != nil {
		return err
	}
	*mount, err = filepath.EvalSymlinks(*mount)
	if err != nil {
		return err
	}
	*backing, err = filepath.Abs(*backing)
	if err != nil {
		return err
	}
	*mount, err = filepath.Abs(*mount)
	if err != nil {
		return err
	}
	rel, err := filepath.Rel(*backing, *mount)
	if err != nil {
		return err
	}
	reverse, err := filepath.Rel(*mount, *backing)
	if err != nil {
		return err
	}
	if filepath.IsLocal(rel) || filepath.IsLocal(reverse) {
		return errors.New("backing and mount must be separate trees")
	}
	dir, err := os.Open(*backing)
	if err != nil {
		return err
	}
	defer dir.Close()
	if err = syscall.Flock(int(dir.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		return fmt.Errorf("volume already owned: %w", err)
	}
	entries, err := os.ReadDir(*mount)
	if err != nil {
		return err
	}
	if len(entries) != 0 {
		return errors.New("mount must be empty")
	}
	v := &volume{limit: *limit, items: map[uint64]*item{}}
	rootStat, e := stat(*backing)
	if e != 0 {
		return e
	}
	err = filepath.WalkDir(*backing, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if path == *backing {
			return nil
		}
		s, e := stat(path)
		if e != 0 {
			return e
		}
		kind := s.Mode & syscall.S_IFMT
		if s.Dev != rootStat.Dev || (kind != syscall.S_IFREG && kind != syscall.S_IFDIR) || (kind == syscall.S_IFREG && s.Nlink != 1) {
			return errors.New("unsupported link, type or nested filesystem in backing")
		}
		size := uint64(0)
		if kind == syscall.S_IFREG {
			size = uint64(s.Size)
		}
		if size > v.limit || charge(size) > v.limit || v.used > v.limit-charge(size) {
			return errors.New("quota smaller than existing usage")
		}
		v.add(s.Ino, size)
		return nil
	})
	if err != nil {
		return err
	}
	rd := &fusefs.LoopbackRoot{Path: *backing, Dev: uint64(rootStat.Dev)}
	rd.NewNode = func(r *fusefs.LoopbackRoot, _ *fusefs.Inode, _ string, _ *syscall.Stat_t) fusefs.InodeEmbedder {
		return &node{LoopbackNode: fusefs.LoopbackNode{RootData: r}, v: v}
	}
	root := &node{LoopbackNode: fusefs.LoopbackNode{RootData: rd}, v: v}
	rd.RootNode = root
	zero := time.Duration(0)
	server, err := fusefs.Mount(*mount, root, &fusefs.Options{MountOptions: fuse.MountOptions{
		Name: "p2quota", FsName: *name, Options: []string{"default_permissions", "nosuid", "nodev", "noexec"}, DisableXAttrs: true, EnableLocks: true, DirectMountStrict: *direct,
	}, AttrTimeout: &zero, EntryTimeout: &zero, NegativeTimeout: &zero})
	if err != nil {
		return err
	}
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		for range signals {
			if err := server.Unmount(); err != nil {
				log.Printf("unmount refused: %v", err)
			}
		}
	}()
	log.Printf("mounted quota=%d used=%d", v.limit, v.used)
	server.Wait()
	signal.Stop(signals)
	return nil
}
func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}
