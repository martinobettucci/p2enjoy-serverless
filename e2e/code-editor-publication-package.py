# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_PUBLICATION_CONTINUITY.md#découpage-et-autorité
# @verifies docs/CODE_EDITOR_PUBLICATION_CONTINUITY.md#sept-groupes-ciblés-puis25communs-frais
"""Original ZIP with repository handlers and real bytes for partial uploads."""
import hashlib,json,secrets,stat,sys,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
target=Path(sys.argv[1]).resolve()
assert target.is_relative_to(root/'.local/e2e') and target.parent.is_dir() and not target.exists()
files={name:(root/'qualification/artifacts'/name).read_bytes() for name in
       ('editor-reader-lifecycle.cjs','publication-recovery.cjs')}
files.update({'reader-gate.txt':'Lecteurs réels, capacité conservée et restitution vérifiée.\n'.encode(),
              'publication-marker.json':json.dumps({'value':'original-package','validation_delay_ms':0}).encode(),
              'upload-payload.bin':secrets.token_bytes(256*1024)})
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=False) as archive:
    for name,data in sorted(files.items()):
        item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.create_system=3
        item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=(stat.S_IFREG|0o444)<<16
        archive.writestr(item,data)
assert target.stat().st_size>192*1024
print(json.dumps({'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
                 'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':'0o444'} for name,data in files.items()}}))
