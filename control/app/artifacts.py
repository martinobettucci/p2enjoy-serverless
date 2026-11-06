# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#artefact
"""Bounded classic ZIP reader and atomic, descriptor-relative extraction on Linux."""
import argparse
import ctypes
from dataclasses import dataclass
import hashlib
import json
import ntpath
import os
from pathlib import Path
import stat
import struct
import sys
import unicodedata
import uuid
import zlib

MAX_ZIP=64*1024**2
MAX_FILE=64*1024**2
MAX_TOTAL=256*1024**2
MAX_ENTRIES=20000
MAX_CENTRAL=16*1024**2
BLOCK=65536
END=struct.Struct('<4s4H2IH')
CENTRAL=struct.Struct('<4s6H3I5H2I')
LOCAL=struct.Struct('<4s5H3I2H')


class ArtifactError(Exception):pass


@dataclass(frozen=True)
class Entry:
    name:str
    raw:bytes
    flags:int
    method:int
    crc:int
    compressed:int
    expanded:int
    offset:int
    executable:bool
    directory:bool


def exact(source,size):
    data=source.read(size)
    if len(data)!=size:raise ArtifactError('zip_truncated')
    return data


def extra_fields(data,raw,decoded):
    seen=set();offset=0
    while offset<len(data):
        if offset+4>len(data):raise ArtifactError('zip_extra_invalid')
        tag,size=struct.unpack_from('<HH',data,offset);offset+=4
        if tag in seen or offset+size>len(data):raise ArtifactError('zip_extra_invalid')
        seen.add(tag);value=data[offset:offset+size];offset+=size
        if tag==1:raise ArtifactError('zip64_unsupported')
        if tag not in (0x5455,0x7875,0x000a,0x7075):raise ArtifactError('zip_extra_unsupported')
        if tag==0x7075:
            if len(value)<5 or value[0]!=1 or struct.unpack_from('<I',value,1)[0]!=zlib.crc32(raw):
                raise ArtifactError('zip_unicode_invalid')
            try:unicode_name=value[5:].decode('utf8')
            except UnicodeError:raise ArtifactError('zip_unicode_invalid') from None
            if unicode_name!=decoded:raise ArtifactError('zip_unicode_conflict')


def path_name(raw,flags):
    try:decoded=raw.decode('utf8' if flags&0x800 else 'cp437')
    except UnicodeError:raise ArtifactError('zip_path_encoding') from None
    if (not decoded or len(decoded.encode())>512 or '\\' in decoded or
        ntpath.splitdrive(decoded)[0] or any(unicodedata.category(c)=='Cc' for c in decoded)):
        raise ArtifactError('zip_path_invalid')
    directory=decoded.endswith('/')
    name=decoded[:-1] if directory else decoded
    if any(part in ('','.','..') or len(part.encode())>255 for part in name.split('/')):
        raise ArtifactError('zip_path_invalid')
    return name,directory,decoded


def common(version,flags,method):
    if flags&1:raise ArtifactError('zip_encrypted')
    if method not in (0,8):raise ArtifactError('zip_compression_unsupported')
    if version not in (10,20) or flags&~(0x808|(6 if method==8 else 0)):
        raise ArtifactError('zip_format_unsupported')


def directory(source,size):
    source.seek(max(0,size-65557));tail=source.read(65557)
    position=tail.rfind(b'PK\x05\x06');end=None
    while position>=0:
        if len(tail)-position>=END.size:
            candidate=END.unpack_from(tail,position)
            if position+END.size+candidate[-1]==len(tail):end=candidate;break
        position=tail.rfind(b'PK\x05\x06',0,position)
    if end is None:raise ArtifactError('zip_end_missing')
    _,disk,central_disk,disk_count,count,length,offset,_=end
    end_offset=size-len(tail)+position
    if count==65535 or length==0xffffffff or offset==0xffffffff:raise ArtifactError('zip64_unsupported')
    if disk or central_disk or disk_count!=count:raise ArtifactError('zip_multivolume_unsupported')
    if not 1<=count<=MAX_ENTRIES:raise ArtifactError('zip_entry_limit')
    if length>MAX_CENTRAL:raise ArtifactError('zip_metadata_limit')
    if offset+length!=end_offset or offset<0:raise ArtifactError('zip_layout_invalid')
    source.seek(offset);entries=[];total=0
    while source.tell()<end_offset:
        if len(entries)>=MAX_ENTRIES:raise ArtifactError('zip_entry_limit')
        if source.tell()+CENTRAL.size>end_offset:raise ArtifactError('zip_central_invalid')
        fields=CENTRAL.unpack(exact(source,CENTRAL.size))
        magic,made,version,flags,method,_,_,crc,compressed,expanded,nlen,xlen,clen,start_disk,_,attrs,local_offset=fields
        if magic!=b'PK\x01\x02':raise ArtifactError('zip_central_invalid')
        common(version,flags,method)
        if compressed==0xffffffff or expanded==0xffffffff or local_offset==0xffffffff:raise ArtifactError('zip64_unsupported')
        if start_disk:raise ArtifactError('zip_multivolume_unsupported')
        if source.tell()+nlen+xlen+clen>end_offset:raise ArtifactError('zip_central_invalid')
        raw=exact(source,nlen);extra=exact(source,xlen);exact(source,clen)
        name,is_dir,decoded=path_name(raw,flags);extra_fields(extra,raw,decoded)
        mode=(attrs>>16)&0xffff;kind=stat.S_IFMT(mode)
        if kind not in (0,stat.S_IFREG,stat.S_IFDIR):raise ArtifactError('zip_special_file')
        if (kind==stat.S_IFDIR or attrs&0x10) and not is_dir:raise ArtifactError('zip_type_conflict')
        if kind==stat.S_IFREG and is_dir:raise ArtifactError('zip_type_conflict')
        if is_dir and expanded:raise ArtifactError('zip_directory_payload')
        if expanded>MAX_FILE or compressed>MAX_ZIP:raise ArtifactError('zip_file_limit')
        total+=expanded
        if total>MAX_TOTAL:raise ArtifactError('zip_total_limit')
        entries.append(Entry(name,raw,flags,method,crc,compressed,expanded,local_offset,bool(mode&0o111),is_dir))
    if source.tell()!=end_offset or len(entries)!=count:raise ArtifactError('zip_entry_count')
    seen=set();files=set();folders=set()
    for entry in entries:
        if entry.name in seen:raise ArtifactError('zip_duplicate')
        seen.add(entry.name)
        parts=entry.name.split('/')
        for index in range(1,len(parts)):
            parent='/'.join(parts[:index])
            if parent in files:raise ArtifactError('zip_path_collision')
            folders.add(parent)
        if entry.directory:
            if entry.name in files:raise ArtifactError('zip_path_collision')
            folders.add(entry.name)
        else:
            if entry.name in folders:raise ArtifactError('zip_path_collision')
            files.add(entry.name)
        if len(folders)>MAX_ENTRIES:raise ArtifactError('zip_directory_limit')
    if not files:raise ArtifactError('zip_empty')
    ordered=sorted(entries,key=lambda entry:entry.offset)
    if ordered[0].offset!=0:raise ArtifactError('zip_prefix_unsupported')
    locations={}
    for index,entry in enumerate(ordered):
        boundary=ordered[index+1].offset if index+1<len(ordered) else offset
        if entry.offset+LOCAL.size>boundary:raise ArtifactError('zip_overlap')
        source.seek(entry.offset)
        magic,version,flags,method,_,_,crc,compressed,expanded,nlen,xlen=LOCAL.unpack(exact(source,LOCAL.size))
        if magic!=b'PK\x03\x04':raise ArtifactError('zip_local_invalid')
        common(version,flags,method)
        if flags!=entry.flags or method!=entry.method:raise ArtifactError('zip_header_conflict')
        if source.tell()+nlen+xlen>boundary:raise ArtifactError('zip_overlap')
        raw=exact(source,nlen);extra=exact(source,xlen)
        if raw!=entry.raw:raise ArtifactError('zip_header_conflict')
        extra_fields(extra,raw,raw.decode('utf8' if flags&0x800 else 'cp437'))
        data_start=source.tell();data_end=data_start+entry.compressed
        if data_end>boundary:raise ArtifactError('zip_overlap')
        if flags&8:
            if any(value not in (0,wanted) for value,wanted in zip((crc,compressed,expanded),(entry.crc,entry.compressed,entry.expanded))):
                raise ArtifactError('zip_header_conflict')
            if boundary-data_end not in (12,16):raise ArtifactError('zip_descriptor_invalid')
            source.seek(data_end);descriptor=exact(source,boundary-data_end)
            if len(descriptor)==16 and descriptor[:4]==b'PK\x07\x08':descriptor=descriptor[4:]
            if len(descriptor)!=12 or struct.unpack('<III',descriptor)!=(entry.crc,entry.compressed,entry.expanded):
                raise ArtifactError('zip_descriptor_invalid')
        elif (crc,compressed,expanded)!=(entry.crc,entry.compressed,entry.expanded) or data_end!=boundary:
            raise ArtifactError('zip_header_conflict')
        locations[entry.name]=data_start
    return entries,folders,locations


def open_directory(path):
    path=Path(path).absolute()
    if '..' in path.parts:raise ArtifactError('destination_invalid')
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=child
        return fd
    except BaseException:os.close(fd);raise


def parent_fd(root,parts):
    fd=os.dup(root)
    try:
        for part in parts:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=child
        return fd
    except BaseException:os.close(fd);raise


def identity(fd):
    value=os.fstat(fd)
    return value.st_dev,value.st_ino


def remove_tree(parent,name,expected):
    try:root=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
    except FileNotFoundError:return
    try:
        if identity(root)!=expected:raise ArtifactError('cleanup_identity')
        os.fchmod(root,0o700)
        with os.scandir(root) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    child=os.open(entry.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=root)
                    try:expected_child=identity(child)
                    finally:os.close(child)
                    remove_tree(root,entry.name,expected_child)
                else:os.unlink(entry.name,dir_fd=root)
    finally:os.close(root)
    current=os.stat(name,dir_fd=parent,follow_symlinks=False)
    if (current.st_dev,current.st_ino)!=expected:raise ArtifactError('cleanup_identity')
    os.rmdir(name,dir_fd=parent)


def publish(parent,temporary,destination):
    libc=ctypes.CDLL(None,use_errno=True)
    rename=getattr(libc,'renameat2',None)
    if rename is None:raise ArtifactError('atomic_publish_unavailable')
    rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
    rename.restype=ctypes.c_int
    if rename(parent,os.fsencode(temporary),parent,os.fsencode(destination),1)!=0:
        error=ctypes.get_errno()
        if error==17:raise ArtifactError('destination_exists')
        raise OSError(error,'Atomic archive publication failed')


def extract(archive,destination):
    destination=Path(destination).absolute()
    if destination.name in ('','..','.'):raise ArtifactError('destination_invalid')
    source_parent=open_directory(Path(archive).absolute().parent)
    try:source_fd=os.open(Path(archive).name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=source_parent)
    finally:os.close(source_parent)
    try:
        before=os.fstat(source_fd)
        if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=MAX_ZIP:raise ArtifactError('zip_size_limit')
        source_file=os.fdopen(source_fd,'rb')
    except BaseException:os.close(source_fd);raise
    parent=None;root=None;temporary=None;published=False;expected=None
    try:
        with source_file as source:
            digest=hashlib.sha256();remaining=before.st_size
            while remaining:
                block=exact(source,min(BLOCK,remaining));digest.update(block);remaining-=len(block)
            if source.read(1):raise ArtifactError('zip_source_changed')
            checksum=digest.hexdigest()
            entries,folders,locations=directory(source,before.st_size)
            parent=open_directory(destination.parent)
            try:os.stat(destination.name,dir_fd=parent,follow_symlinks=False)
            except FileNotFoundError:pass
            else:raise ArtifactError('destination_exists')
            temporary='.extract-'+uuid.uuid4().hex
            os.mkdir(temporary,mode=0o700,dir_fd=parent)
            created=os.stat(temporary,dir_fd=parent,follow_symlinks=False)
            expected=(created.st_dev,created.st_ino)
            root=os.open(temporary,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
            if identity(root)!=expected:raise ArtifactError('destination_changed')
            for folder in sorted(folders,key=lambda name:(name.count('/'),name)):
                parts=folder.split('/');fd=parent_fd(root,parts[:-1])
                try:os.mkdir(parts[-1],mode=0o700,dir_fd=fd)
                finally:os.close(fd)
            inventory=[];total=0
            for entry in entries:
                output=None;count=0;crc=0;sha=hashlib.sha256()
                if not entry.directory:
                    parts=entry.name.split('/');fd=parent_fd(root,parts[:-1])
                    try:output=os.open(parts[-1],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
                    finally:os.close(fd)
                try:
                    source.seek(locations[entry.name]);left=entry.compressed
                    decoder=zlib.decompressobj(-15) if entry.method==8 else None
                    def emit(data):
                        nonlocal count,total,crc
                        count+=len(data);total+=len(data)
                        if count>MAX_FILE or total>MAX_TOTAL:raise ArtifactError('zip_expansion_limit')
                        if count>entry.expanded:raise ArtifactError('zip_size_mismatch')
                        crc=zlib.crc32(data,crc);sha.update(data)
                        if output is not None:
                            view=memoryview(data)
                            while view:
                                written=os.write(output,view)
                                if not written:raise ArtifactError('storage_write_failed')
                                view=view[written:]
                    while left:
                        block=exact(source,min(BLOCK,left));left-=len(block)
                        if decoder:
                            while True:
                                decoded=decoder.decompress(block,BLOCK);emit(decoded);block=decoder.unconsumed_tail
                                if decoder.unused_data:raise ArtifactError('zip_deflate_trailing')
                                if not block and len(decoded)<BLOCK:break
                        else:emit(block)
                    if decoder:
                        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:raise ArtifactError('zip_deflate_incomplete')
                    if count!=entry.expanded:raise ArtifactError('zip_size_mismatch')
                    if crc!=entry.crc:raise ArtifactError('zip_crc_mismatch')
                    if output is not None:
                        mode=0o555 if entry.executable else 0o444
                        os.fchmod(output,mode);os.fsync(output)
                        inventory.append({'path':entry.name,'size':count,'sha256':sha.hexdigest(),'mode':oct(mode)})
                finally:
                    if output is not None:os.close(output)
            for folder in sorted(folders,key=lambda name:(-name.count('/'),name)):
                fd=parent_fd(root,folder.split('/'))
                try:os.fchmod(fd,0o555);os.fsync(fd)
                finally:os.close(fd)
            os.fchmod(root,0o555);os.fsync(root)
            after=os.fstat(source.fileno())
            if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                raise ArtifactError('zip_source_changed')
            current=open_directory(destination.parent)
            try:
                if identity(current)!=identity(parent):raise ArtifactError('destination_changed')
            finally:os.close(current)
            live=os.stat(temporary,dir_fd=parent,follow_symlinks=False)
            if (live.st_dev,live.st_ino)!=expected:raise ArtifactError('destination_changed')
            publish(parent,temporary,destination.name);temporary=destination.name
            os.fsync(parent)
            published=True
            charge=(len(folders)+1)*4096+((before.st_size+4095)//4096)*4096
            charge+=sum(max(1,(row['size']+4095)//4096)*4096 for row in inventory)
            return {'archive_sha256':checksum,'archive_bytes':before.st_size,'expanded_bytes':total,
                    'file_count':len(inventory),'directory_count':len(folders),'storage_charge_bytes':charge,
                    'inventory':sorted(inventory,key=lambda row:row['path'])}
    finally:
        if root is not None:os.close(root)
        try:
            if parent is not None and temporary and expected and not published:remove_tree(parent,temporary,expected)
        finally:
            if parent is not None:os.close(parent)


def main():
    parser=argparse.ArgumentParser(description='Extraction bornée d’un artefact ZIP de plateforme')
    parser.add_argument('--archive',required=True);parser.add_argument('--destination',required=True)
    args=parser.parse_args()
    try:result=extract(args.archive,args.destination)
    except ArtifactError as error:
        print(json.dumps({'ok':False,'error':str(error)}));return 1
    except (OSError,ValueError,UnicodeError,zlib.error,struct.error):
        print(json.dumps({'ok':False,'error':'artifact_invalid_or_storage_unavailable'}));return 1
    print(json.dumps({'ok':True,**result},ensure_ascii=False));return 0


if __name__=='__main__':sys.exit(main())
