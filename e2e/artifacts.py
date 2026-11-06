# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#artefact
# @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#artefact
"""Real ZIP CLI, filesystem failures, adapter and Node/Docker validation on DEV."""
import hashlib
import ctypes
import json
import os
from pathlib import Path
import shutil
import select
import stat
import struct
import subprocess
import tempfile
import time
import uuid
import zipfile
import zlib

ROOT=Path('/srv/p2enjoy-serverless')
REPORT=ROOT/'control'/'artifacts-proof.json'
REPORT.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
assert Path('/etc/hostname').read_text().strip()=='infra-serverless','SPARK DEV requis'
checks=[];completed=False;work=None;process=None
installation=str(uuid.uuid4());counter=0


def run(args,*,timeout=120,input=None,check=True):
    result=subprocess.run(args,cwd=ROOT,text=True,input=input,capture_output=True,timeout=timeout)
    if check and result.returncode:raise RuntimeError('Commande échouée : '+args[0]+' ('+str(result.returncode)+')')
    return result


def passed(name):
    checks.append({'name':name,'status':'passed'});print('PASS',name,flush=True)


class FixtureZip(bytes):
    def __new__(cls,payload,expected):
        value=super().__new__(cls,payload);value.expected=expected;return value


def archive(entries,comment=b''):
    """Construct actual classic ZIP records, including intentionally invalid fields."""
    local=bytearray();central=bytearray();expected=[]
    for item in entries:
        raw=item.get('raw',item.get('name','handler.cjs').encode())
        data=item.get('data',b'exports.handler = async () => ({statusCode:200,body:"ok"});\n')
        method=item.get('method',8);flags=item.get('flags',0x800)
        compressed=zlib.compress(data,wbits=-15) if method==8 else data
        compressed=item.get('compressed',compressed)
        crc=item.get('crc',zlib.crc32(data));expanded=item.get('expanded',len(data))
        version=item.get('version',20);extra=item.get('extra',b'');local_extra=item.get('local_extra',extra)
        attrs=item.get('attrs',(stat.S_IFREG|0o644)<<16)
        if not raw.endswith(b'/'):
            expected.append({'path':raw.decode('utf8' if flags&0x800 else 'cp437',errors='replace'),
                'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                'mode':oct(0o555 if (attrs>>16)&0o111 else 0o444)})
        descriptor=item.get('descriptor',False)
        if descriptor:flags|=8
        local_crc=0 if descriptor else crc;local_size=0 if descriptor else len(compressed);local_exp=0 if descriptor else expanded
        local_raw=item.get('local_raw',raw)
        start=len(local)
        local.extend(struct.pack('<4s5H3I2H',b'PK\x03\x04',version,item.get('local_flags',flags),item.get('local_method',method),0,0,
            item.get('local_crc',local_crc),item.get('local_size',local_size),item.get('local_expanded',local_exp),len(local_raw),len(local_extra)))
        local.extend(local_raw+local_extra+compressed)
        if descriptor:local.extend((b'PK\x07\x08' if descriptor=='signed' else b'')+struct.pack('<III',crc,len(compressed),expanded))
        local.extend(item.get('gap',b''))
        central.extend(struct.pack('<4s6H3I5H2I',b'PK\x01\x02',0x314,version,flags,method,0,0,crc,
            item.get('central_size',len(compressed)),expanded,len(raw),len(extra),len(item.get('comment',b'')),item.get('disk',0),0,attrs,item.get('offset',start)))
        central.extend(raw+extra+item.get('comment',b''))
    return FixtureZip(local+central+struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,len(entries),len(entries),len(central),len(local),len(comment))+comment,expected)


def extra(tag,value):return struct.pack('<HH',tag,len(value))+value


def erase(path):
    if not path.exists() or path.is_symlink():
        if path.is_symlink():path.unlink()
        return
    if not path.is_dir():path.unlink();return
    for parent,dirs,_ in os.walk(path):
        os.chmod(parent,0o700)
        for name in dirs:
            child=Path(parent)/name
            if not child.is_symlink():os.chmod(child,0o700)
    shutil.rmtree(path)


def command(source,destination,*,name=None):
    return ['docker','run','--rm','--name',name or 'p2-artifact-'+uuid.uuid4().hex,
        '--label','tech.p2enjoy.serverless.installation='+installation,
        '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--memory','256m','--cpus','1','--pids-limit','32','--tmpfs','/tmp:size=16m,mode=1777,noexec,nosuid',
        '--env-file','/etc/spark/env','--env-file','/run/spark/secrets',
        '--mount','type=bind,src='+str(work)+',dst='+str(work),image,'--archive',str(source),'--destination',str(destination)]


def result_of(result,error=None):
    assert result.returncode==(1 if error else 0),(result.returncode,result.stderr[:200],result.stdout[:300])
    assert not result.stderr,'Diagnostic brut inattendu'
    output=json.loads(result.stdout)
    assert output['ok']==(error is None),output
    if error:assert output.get('error')==error,(output,error)
    return output


def inspect(output,destination,source,expected=None):
    assert stat.S_IMODE(destination.stat().st_mode)==0o555
    actual=[];directories=0
    for parent,dirs,files in os.walk(destination):
        for name in dirs:
            child=Path(parent)/name;assert not child.is_symlink()
            assert stat.S_IMODE(child.stat().st_mode)==0o555;directories+=1
        for name in files:
            child=Path(parent)/name;assert child.is_file() and not child.is_symlink()
            actual.append({'path':child.relative_to(destination).as_posix(),'size':child.stat().st_size,
                'sha256':hashlib.file_digest(child.open('rb'),'sha256').hexdigest(),
                'mode':oct(stat.S_IMODE(child.stat().st_mode))})
    assert output['inventory']==sorted(actual,key=lambda row:row['path'])
    if expected is None:
        expected=[]
        with zipfile.ZipFile(source) as zipped:
            for item in zipped.infolist():
                if item.is_dir():continue
                with zipped.open(item) as stream:checksum=hashlib.file_digest(stream,'sha256').hexdigest()
                expected.append({'path':item.filename,'size':item.file_size,'sha256':checksum,
                    'mode':oct(0o555 if (item.external_attr>>16)&0o111 else 0o444)})
    assert sorted(actual,key=lambda row:row['path'])==sorted(expected,key=lambda row:row['path']), 'Contenu différent de l’archive originale'
    assert output['file_count']==len(actual) and output['directory_count']==directories
    assert output['expanded_bytes']==sum(row['size'] for row in actual)
    charge=(directories+1)*4096+((output['archive_bytes']+4095)//4096)*4096
    charge+=sum(max(1,(row['size']+4095)//4096)*4096 for row in actual)
    assert output['storage_charge_bytes']==charge


def case(name,data,error=None):
    global counter
    counter+=1;source=work/'input.zip';destination=work/'output'
    source.write_bytes(data)
    output=result_of(run(command(source,destination),check=False),error)
    assert not list(work.glob('.extract-*')),'Candidat conservé après réponse'
    if error:assert not destination.exists(),'Destination publiée après échec'
    else:
        assert output['archive_sha256']==hashlib.sha256(data).hexdigest()
        assert output['archive_bytes']==len(data)
        inspect(output,destination,source,data.expected);erase(destination)
    source.unlink();passed(name);return output


try:
    image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-artifacts:dev']).stdout.strip()
    adapter_image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-adapter:dev']).stdout.strip()
    runtime_image=run(['docker','image','inspect','--format','{{.Id}}','p2enjoy-runtime:dev']).stdout.strip()
    work=Path(tempfile.mkdtemp(prefix='artifact-proof-',dir=ROOT/'state'))
    case('STORED, DEFLATE, dossiers explicites/implicites et fichier vide',archive([
        {'name':'explicit/','data':b'','attrs':(stat.S_IFDIR|0o755)<<16|0x10},
        {'name':'explicit/a.cjs','method':0},{'name':'implicit/deep/b.cjs'},{'name':'empty','data':b''}]))
    output=case('Permissions readonly et retrait des bits privilégiés',archive([
        {'name':'a','attrs':(stat.S_IFREG|0o6755)<<16},{'name':'b','attrs':(stat.S_IFREG|0o666)<<16}]))
    assert [row['mode'] for row in output['inventory']]==['0o555','0o444']
    output=case('Noms UTF-8 et CP437 conservés',archive([
        {'name':'été.cjs'},{'raw':b'caf\x82.cjs','flags':0}]))
    assert [row['path'] for row in output['inventory']]==['café.cjs','été.cjs']
    for descriptor in ('signed','unsigned'):
        for method in (0,8):case('Data descriptor '+descriptor+' méthode '+str(method),archive([{'descriptor':descriptor,'method':method}]))
    raw=b'caf\x82.cjs';unicode=extra(0x7075,b'\x01'+struct.pack('<I',zlib.crc32(raw))+'café.cjs'.encode())
    case('Extra Unicode confirmant le nom et métadonnées admises',archive([{'raw':raw,'flags':0,
        'extra':unicode+extra(0x5455,b'\x01\0\0\0\0')+extra(0x7875,b'\x01\x01\x01\x01\x01')+extra(0x000a,b'\0'*4)}]))
    case('Commentaire ZIP maximal avec signatures internes',archive([{}],b'PK\x05\x06'+b'x'*65531))
    path='a'*255+'/'+'b'*255
    case('Composant 256 refusé dans un chemin de 512 octets',archive([{'name':path+'c'}]),'zip_path_invalid')
    case('Chemin 512 octets accepté',archive([{'name':'a'*254+'/'+'b'*255+'/c'}]))
    bad_paths=['/absolute','../parent','a/../parent','./a','a//b','a\\b','C:drive','a\0b','a\nb','a'*256,'a'*254+'/'+'b'*255+'/cc']
    for index,name in enumerate(bad_paths):case('Chemin interdit '+str(index+1),archive([{'name':name}]),'zip_path_invalid')
    case('Nom UTF-8 invalide',archive([{'raw':b'\xff'}]),'zip_path_encoding')
    case('Extra Unicode contradictoire',archive([{'raw':raw,'flags':0,'extra':extra(0x7075,b'\x01'+struct.pack('<I',zlib.crc32(raw))+b'../outside')}]),'zip_unicode_conflict')
    case('Extra Unicode CRC invalide',archive([{'extra':extra(0x7075,b'\x01\0\0\0\0handler.cjs')}]),'zip_unicode_invalid')
    for tag,data,error in [(1,b'\0'*16,'zip64_unsupported'),(0x9999,b'','zip_extra_unsupported')]:
        case('Extra refusé '+str(tag),archive([{'extra':extra(tag,data)}]),error)
    case('Extra tronqué',archive([{'extra':b'\x55\x54\x05\0x'}]),'zip_extra_invalid')
    case('Extra répété',archive([{'extra':extra(0x5455,b'')*2}]),'zip_extra_invalid')
    for kind in (stat.S_IFLNK,stat.S_IFIFO,stat.S_IFSOCK,stat.S_IFCHR,stat.S_IFBLK):
        case('Type spécial refusé '+str(kind),archive([{'attrs':(kind|0o777)<<16}]),'zip_special_file')
    case('Type répertoire sans slash',archive([{'attrs':stat.S_IFDIR<<16}]),'zip_type_conflict')
    case('Type fichier avec slash',archive([{'name':'folder/','data':b''}]),'zip_type_conflict')
    case('Répertoire avec données',archive([{'name':'folder/','attrs':stat.S_IFDIR<<16}]),'zip_directory_payload')
    case('Archive vide',archive([]),'zip_entry_limit')
    case('Archive contenant seulement des dossiers',archive([{'name':'dir/','data':b'','attrs':stat.S_IFDIR<<16}]),'zip_empty')
    for entries in ([{'name':'a'},{'name':'a'}],[{'name':'a/' ,'data':b'','attrs':stat.S_IFDIR<<16},{'name':'a'}]):
        case('Doublon de chemin complet',archive(entries),'zip_duplicate')
    for entries in ([{'name':'a'},{'name':'a/b'}],[{'name':'a/b'},{'name':'a'}]):
        case('Collision fichier et parent dans les deux ordres',archive(entries),'zip_path_collision')
    for item,error,name in [({'flags':1},'zip_encrypted','ZIP chiffré'),({'method':12},'zip_compression_unsupported','Compression non prise en charge'),
        ({'version':45},'zip_format_unsupported','Version ZIP64'),({'flags':0x40},'zip_format_unsupported','Flags non admis'),
        ({'disk':1},'zip_multivolume_unsupported','Volume distinct'),({'offset':1},'zip_prefix_unsupported','Préfixe non décrit'),
        ({'local_raw':b'other'},'zip_header_conflict','Nom local divergent'),({'local_method':0},'zip_header_conflict','Méthode locale divergente'),
        ({'local_crc':1},'zip_header_conflict','CRC local divergent'),({'gap':b'x'},'zip_header_conflict','Octet entre données et répertoire'),
        ({'descriptor':'signed','gap':b'x'*65536},'zip_descriptor_invalid','Descripteur surdimensionné'),
        ({'descriptor':'signed','local_expanded':999},'zip_header_conflict','Taille locale de descripteur contradictoire')]:
        case(name,archive([item]),error)
    nominal=archive([{}]);end=len(nominal)-22
    for relative,fmt,value,error,name in [(8,'H',2,'zip_multivolume_unsupported','Comptes par disque incohérents'),
        (8,'HH', (2,2),'zip_entry_count','Nombre central mensonger'),(8,'HH',(65535,65535),'zip64_unsupported','Sentinelle ZIP64'),
        (12,'I',16*1024**2+1,'zip_metadata_limit','Répertoire central hors limite'),(16,'I',0,'zip_layout_invalid','Offset central incohérent')]:
        mutated=bytearray(nominal);struct.pack_into('<'+fmt,mutated,end+relative,*(value if isinstance(value,tuple) else (value,)))
        case(name,mutated,error)
    case('Fin ZIP tronquée',nominal[:-3],'zip_end_missing')
    case('Contenu après la fin ZIP',nominal+b'junk','zip_end_missing')
    case('Zones locales superposées',archive([{'name':'a'},{'name':'b','offset':0}]),'zip_overlap')
    for method in (0,8):
        case('Taille réelle supérieure à la taille annoncée méthode '+str(method),archive([{'data':b'ab','method':method,'expanded':1,'crc':zlib.crc32(b'a')}]),'zip_size_mismatch')
        case('Taille réelle inférieure à la taille annoncée méthode '+str(method),archive([{'data':b'a','method':method,'expanded':2}]),'zip_size_mismatch')
    case('CRC erroné après écriture effective',archive([{'name':'first'},{'name':'second','crc':0}]),'zip_crc_mismatch')
    compressed=zlib.compress(b'actual payload',wbits=-15)
    case('Flux DEFLATE tronqué',archive([{'data':b'actual payload','compressed':compressed[:-1]}]),'zip_deflate_incomplete')
    case('Octets après fin DEFLATE',archive([{'data':b'actual payload','compressed':compressed+b'junk'}]),'zip_deflate_trailing')
    for size in (65535,65536,65537,131071,131072,131073):
        case('Drainage DEFLATE à '+str(size)+' octets',archive([{'data':b'x'*size}]))
    case('Limite réelle fichier 64 Mio',archive([{'data':b'x'*(64*1024**2)}]))
    overhead=len(archive([{'data':b'','method':0}]))
    case('Limite réelle ZIP 64 Mio',archive([{'data':b'x'*(64*1024**2-overhead),'method':0}]))
    case('Fichier au-dessus de 64 Mio annoncé',archive([{'expanded':64*1024**2+1}]),'zip_file_limit')
    case('Expansion cachée au-dessus de 64 Mio',archive([{'data':b'x'*(64*1024**2+1),'expanded':64*1024**2}]),'zip_expansion_limit')
    case('Limite totale réelle 256 Mio',archive([{'name':str(i),'data':b'x'*(64*1024**2)} for i in range(4)]))
    case('Total déclaré supérieur à 256 Mio',archive([{'name':str(i),'expanded':64*1024**2} for i in range(5)]),'zip_total_limit')
    many=[{'name':str(i),'data':b''} for i in range(20000)]
    case('Limite réelle 20 000 fichiers',archive(many))
    case('Entrées au-dessus de 20 000',archive(many+[{'name':'too-many'}]),'zip_entry_limit')
    directories=[{'name':str(i)+'/', 'data':b'', 'attrs':stat.S_IFDIR<<16} for i in range(20000)]
    case('Répertoires explicites comptés parmi les entrées',archive(directories+[{}]),'zip_entry_limit')
    case('Limite 20 000 répertoires implicites',archive([{'name':str(i)+'/a/x'} for i in range(10001)]),'zip_directory_limit')
    central=[];remaining=16*1024**2-257*(46+5)
    for i in range(257):
        size=min(remaining,65535);remaining-=size
        central.append({'name':f'f{i:04d}','data':b'','comment':b'x'*size})
    assert remaining==0
    case('Répertoire central réel à 16 Mio',archive(central))
    central[-1]['comment']+=b'x'
    case('Répertoire central réel au-dessus de 16 Mio',archive(central),'zip_metadata_limit')
    source=work/'input.zip';destination=work/'output'
    with source.open('wb') as stream:stream.truncate(64*1024**2+1)
    result_of(run(command(source,destination),check=False),'zip_size_limit');source.unlink();passed('ZIP réel de plus de 64 Mio refusé')
    source.write_bytes(nominal)
    destination.mkdir();(destination/'sentinel').write_text('preserved')
    result_of(run(command(source,destination),check=False),'destination_exists')
    assert (destination/'sentinel').read_text()=='preserved';erase(destination);passed('Destination existante préservée')
    outside=work/'outside';outside.mkdir();(outside/'sentinel').write_text('preserved')
    destination.symlink_to(outside,target_is_directory=True)
    result_of(run(command(source,destination),check=False),'destination_exists');destination.unlink();passed('Destination lien symbolique refusée')
    link=work/'link';link.symlink_to(outside,target_is_directory=True)
    result_of(run(command(source,link/'output'),check=False),'artifact_invalid_or_storage_unavailable');link.unlink()
    assert list(outside.iterdir())==[outside/'sentinel'];passed('Parent destination lié refusé sans écriture externe')
    source.unlink();source.symlink_to(outside/'sentinel')
    result_of(run(command(source,destination),check=False),'artifact_invalid_or_storage_unavailable');source.unlink();passed('Archive liée refusée')
    os.mkfifo(source)
    result_of(run(command(source,destination),check=False),'zip_size_limit');source.unlink();passed('Archive FIFO refusée sans blocage')
    source.mkdir();result_of(run(command(source,destination),check=False),'zip_size_limit');source.rmdir();passed('Archive répertoire refusée')
    # Real disk exhaustion; a second process only inspects the directory after the CLI exits.
    source.write_bytes(archive([{'data':b'x'*(2*1024**2)}]))
    args=command(source,destination);index=args.index(image)
    args=args[:index]+['--tmpfs','/capacity:size=1m,mode=0700','--entrypoint','python',image,'-B','-c',
        'import subprocess,json,os; r=subprocess.run(["python","-B","-m","control.app.artifacts","--archive",'+repr(str(source))+',"--destination","/capacity/output"],capture_output=True,text=True); print(json.dumps({"code":r.returncode,"out":json.loads(r.stdout),"stderr":r.stderr,"remaining":os.listdir("/capacity")}))']
    disk=json.loads(run(args).stdout)
    assert disk=={'code':1,'out':{'ok':False,'error':'artifact_invalid_or_storage_unavailable'},'stderr':'','remaining':[]},disk
    source.unlink();passed('Disque réellement saturé : erreur et candidat supprimé')
    # Collision is produced during actual extraction, without replacing syscalls.
    source.write_bytes(archive(many))
    process=subprocess.Popen(command(source,destination),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    deadline=time.monotonic()+15
    while not list(work.glob('.extract-*')) and process.poll() is None and time.monotonic()<deadline:time.sleep(.005)
    assert list(work.glob('.extract-*')),'Extraction non observée avant la course'
    destination.mkdir();(destination/'sentinel').write_text('concurrent')
    out,err=process.communicate(timeout=120)
    result_of(subprocess.CompletedProcess([],process.returncode,out,err),'destination_exists');process=None
    assert (destination/'sentinel').read_text()=='concurrent' and not list(work.glob('.extract-*'))
    erase(destination);passed('Création concurrente de destination préservée par NOREPLACE')
    parent=work/'parent';parent.mkdir()
    process=subprocess.Popen(command(source,parent/'output'),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    deadline=time.monotonic()+15
    while not list(parent.glob('.extract-*')) and process.poll() is None and time.monotonic()<deadline:time.sleep(.005)
    assert list(parent.glob('.extract-*')),'Extraction non observée avant échange du parent'
    parent.rename(work/'retired');parent.symlink_to(outside,target_is_directory=True)
    out,err=process.communicate(timeout=120)
    result_of(subprocess.CompletedProcess([],process.returncode,out,err),'artifact_invalid_or_storage_unavailable');process=None
    assert not list((work/'retired').iterdir()) and list(outside.iterdir())==[outside/'sentinel']
    parent.unlink();(work/'retired').rmdir();source.unlink();passed('Échange du parent en cours : aucune écriture via le lien et nettoyage par FD')
    source.write_bytes(archive([{'method':0,'data':b'x'*(60*1024**2)}]))
    libc=ctypes.CDLL(None,use_errno=True)
    watch=libc.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC);assert watch>=0
    assert libc.inotify_add_watch(watch,os.fsencode(source),1)>=0
    args=command(source,destination);args[args.index('--cpus')+1]='0.05'
    try:
        process=subprocess.Popen(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        assert select.select([watch],[],[],20)[0],'Lecture source non observée'
        os.read(watch,4096)
        with source.open('ab') as stream:stream.write(b'x'*(5*1024**2))
        out,err=process.communicate(timeout=120)
        result_of(subprocess.CompletedProcess([],process.returncode,out,err),'zip_source_changed');process=None
    finally:os.close(watch)
    assert not destination.exists() and not list(work.glob('.extract-*'))
    source.unlink();passed('Source réellement augmentée pendant sa lecture : refus sans publication')
    project=work/'project';project.mkdir()
    for name in ('package.json','serverless.platform.yml'):shutil.copyfile(ROOT/'qualification'/name,project/name)
    shutil.copytree(ROOT/'qualification'/'src',project/'src')
    package=run(['docker','run','--rm','--name','p2-artifact-package-'+uuid.uuid4().hex,
        '--label','tech.p2enjoy.serverless.installation='+installation,
        '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--memory','256m','--cpus','1','--pids-limit','32',
        '--env-file','/etc/spark/env','--env-file','/run/spark/secrets',
        '--mount','type=bind,src='+str(project)+',dst=/project',adapter_image,'package','--config','/project/serverless.platform.yml'])
    assert json.loads(package.stdout)['functions']==12
    zipfiles=sorted((project/'.serverless-p2').glob('*.zip'));assert len(zipfiles)==12
    handlers=['echo','binary','callback','business','configuration','state','cache','worker','failure','sleep','spin','relay']
    descriptor=json.loads((project/'.serverless-p2'/'deployment.json').read_text())
    assert len(descriptor['artifacts'])==12
    for name in handlers:
        source=project/'.serverless-p2'/descriptor['artifacts'][name]['file']
        output=result_of(run(command(source,destination)));inspect(output,destination,source)
        validator=run(['python3','-B','-m','control.app.validator','--image',runtime_image,'--code',str(destination),
            '--work',str(work),'--handler','src/handlers.'+name,'--installation',installation],input='{"environment":{},"secrets":{}}',check=False)
        validated=json.loads(validator.stdout)
        assert validator.returncode==0 and not validator.stderr and validated['valid'] and validated['container_removed'],validated
        erase(destination);passed('Packaging → extraction → chargement Node réel : '+name)
    assert not run(['docker','ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation]).stdout.strip()
    for container in ('serverless-api','serverless-runtime-reference'):
        assert run(['docker','inspect','--format','{{.State.Health.Status}}',container]).stdout.strip()=='healthy'
    passed('Aucun conteneur de preuve restant et services DEV sains')
    completed=True
finally:
    if process is not None:
        process.kill();process.communicate(timeout=10)
    remaining=run(['docker','ps','-aq','--filter','label=tech.p2enjoy.serverless.installation='+installation]).stdout.split()
    if remaining:run(['docker','rm','-f',*remaining]);completed=False
    if work is not None:erase(work)
    REPORT.write_text(json.dumps({'completed':completed,'passed':len(checks),'skipped':0,'checks':checks,
        'image':globals().get('image'),'adapter_image':globals().get('adapter_image'),'runtime_image':globals().get('runtime_image'),
        'cleanup':not remaining},ensure_ascii=False,indent=2)+'\n')
if not completed:raise SystemExit(1)
