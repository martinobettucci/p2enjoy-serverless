# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#artefact
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md#format-v1
# Package selected real files; neither load a handler nor execute a build.
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import stat
import uuid
import zipfile

from .manifest import ManifestError,public_plan

MAX_ZIP=64*1024*1024
MAX_EXPANDED=256*1024*1024
MAX_FILE=64*1024*1024
MAX_FILES=20000
EXCLUDED_DIRS={'.git','.aws','.serverless','.serverless-p2','__pycache__','.venv','venv'}


def excluded(relative):
    parts=PurePosixPath(relative).parts
    return (any(part in EXCLUDED_DIRS for part in parts) or
            any(part.startswith('.env') for part in parts) or
            any(part.startswith('serverless') and part.endswith(('.yml','.yaml')) for part in parts) or
            'node_modules/.bin' in relative or parts[-1] in ('.scwrc','credentials'))


def selected(relative,patterns):
    keep=True
    for pattern in patterns:
        exclude=pattern.startswith('!')
        if PurePosixPath(relative).full_match(pattern[1:] if exclude else pattern):keep=not exclude
    return keep


def sources(root,patterns,manifest_path,manifest_identity,output_identity):
    result=[]
    for directory,dirs,files in os.walk(root,followlinks=False):
        folder=Path(directory)
        for name in list(dirs):
            path=folder/name;relative=path.relative_to(root).as_posix()
            identity=path.lstat()
            if excluded(relative) or (identity.st_dev,identity.st_ino)==output_identity:dirs.remove(name)
            elif path.is_symlink():
                dirs.remove(name)
                if selected(relative,patterns):raise ManifestError('Lien de répertoire interdit dans l’artefact : '+relative)
        for name in sorted(files):
            path=folder/name;relative=path.relative_to(root).as_posix()
            metadata=path.lstat()
            if path==manifest_path or (metadata.st_dev,metadata.st_ino)==manifest_identity or excluded(relative) or not selected(relative,patterns):continue
            mode=metadata.st_mode
            if not stat.S_ISREG(mode) or path.is_symlink():raise ManifestError('Fichier non ordinaire interdit : '+relative)
            if len(relative.encode())>512 or '\\' in relative or any(ord(c)<32 or ord(c)==127 for c in relative):
                raise ManifestError('Chemin de fichier hors limites.')
            result.append((relative,path))
            if len(result)>MAX_FILES:raise ManifestError('Artefact supérieur à 20 000 fichiers.')
    return sorted(result)


def entrypoint(function,files):
    module=function['config']['handler'].rsplit('.',1)[0]
    candidates=[module] if module.endswith(('.js','.cjs','.mjs')) else [module+suffix for suffix in ('.js','.cjs','.mjs')]
    found=[candidate for candidate in candidates if candidate in files]
    if len(found)!=1:raise ManifestError(function['name']+' : module absent ou ambigu dans la sélection de fichiers.')
    return found[0]


def open_source(root,relative):
    directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        parts=PurePosixPath(relative).parts
        for part in parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=child
        return os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
    finally:os.close(directory)


def package_function(root,function,destination,manifest_path,manifest_identity,output_identity):
    entries=sources(root,function['patterns'],manifest_path,manifest_identity,output_identity)
    if not entries:raise ManifestError('La sélection de fichiers est vide.')
    entry=entrypoint(function,{name for name,_ in entries})
    inventory=[];total=0
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as archive:
        for relative,path in entries:
            fd=open_source(root,relative)
            try:
                before=os.fstat(fd)
                if (before.st_dev,before.st_ino)==manifest_identity:continue
                if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_FILE:raise ManifestError('Fichier non ordinaire ou supérieur à 64 Mio : '+relative)
                info=zipfile.ZipInfo(relative,(1980,1,1,0,0,0));info.create_system=3
                info.external_attr=(stat.S_IFREG|(0o555 if before.st_mode&0o111 else 0o444))<<16
                info.compress_type=zipfile.ZIP_DEFLATED
                digest=hashlib.sha256();size=0
                with archive.open(info,'w') as output:
                    while chunk:=os.read(fd,64*1024):
                        size+=len(chunk);total+=len(chunk)
                        if size>MAX_FILE or total>MAX_EXPANDED:raise ManifestError('Limite de taille décompressée dépassée.')
                        digest.update(chunk);output.write(chunk)
                after=os.fstat(fd)
                if (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                    raise ManifestError('Un fichier a changé pendant le packaging : '+relative)
                inventory.append({'path':relative,'size':size,'sha256':digest.hexdigest(),
                                  'mode':oct(0o555 if before.st_mode&0o111 else 0o444)})
            finally:os.close(fd)
            if destination.tell()>MAX_ZIP:raise ManifestError('ZIP supérieur à 64 Mio.')
    size=destination.tell()
    if size>MAX_ZIP:raise ManifestError('ZIP supérieur à 64 Mio.')
    if entry not in {row['path'] for row in inventory}:raise ManifestError('Le module a changé pendant le packaging.')
    destination.flush();destination.seek(0);digest=hashlib.file_digest(destination,'sha256').hexdigest()
    return {'sha256':digest,'size':size,'expanded_size':total,'entry':entry,'inventory':inventory}


def package(plan,root,output,manifest_path):
    root=Path(root).resolve();output=Path(output).resolve()
    # A dedicated reserved directory prevents recursive inclusion of prior builds.
    if output!=root/'.serverless-p2':raise ManifestError('La sortie doit être .serverless-p2 à la racine du projet.')
    manifest_path=Path(manifest_path).resolve();metadata=manifest_path.stat()
    manifest_identity=(metadata.st_dev,metadata.st_ino)
    rootfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    outfd=None
    descriptor=public_plan(plan);descriptor.update({'format_version':1,'runtime_validation':'pending','artifacts':{}})
    created=[]
    try:
        try:os.mkdir('.serverless-p2',mode=0o700,dir_fd=rootfd)
        except FileExistsError:pass
        outfd=os.open('.serverless-p2',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd)
        identity=os.fstat(outfd);output_identity=(identity.st_dev,identity.st_ino)
        def stable_output():
            current=os.stat('.serverless-p2',dir_fd=rootfd,follow_symlinks=False)
            if not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino)!=output_identity:
                raise ManifestError('Le répertoire de sortie a changé pendant le packaging.')
        def temporary():
            name='.building-'+uuid.uuid4().hex
            fd=os.open(name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=outfd)
            created.append(name);return name,fd
        for function in plan['functions']:
            stable_output();name,fd=temporary()
            with os.fdopen(fd,'w+b') as destination:
                result=package_function(root,function,destination,manifest_path,manifest_identity,output_identity)
                os.fsync(destination.fileno())
            stable_output();final=function['name']+'-'+result['sha256']+'.zip'
            os.replace(name,final,src_dir_fd=outfd,dst_dir_fd=outfd);created.remove(name)
            result['file']=final;descriptor['artifacts'][function['name']]=result
        stable_output();name,fd=temporary()
        with os.fdopen(fd,'w') as destination:
            destination.write(json.dumps(descriptor,ensure_ascii=False,indent=2)+'\n');destination.flush();os.fsync(destination.fileno())
        stable_output();os.replace(name,'deployment.json',src_dir_fd=outfd,dst_dir_fd=outfd);created.remove(name)
        os.fsync(outfd);stable_output()
    finally:
        if outfd is not None:
            for name in created:
                try:os.unlink(name,dir_fd=outfd)
                except FileNotFoundError:pass
            os.close(outfd)
        os.close(rootfd)
    return descriptor
