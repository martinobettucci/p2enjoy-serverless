# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_READ_CONCURRENCY.md#barrière-native-retenue
# @verifies docs/CODE_EDITOR_READ_CONCURRENCY.md#qualification-propre-à-linstrumentation
"""Package repository original handler and deterministic reader data as a real ZIP."""
import hashlib,json,stat,sys,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
target=Path(sys.argv[1]).resolve()
assert target.is_relative_to(root/'.local/e2e') and target.parent.is_dir() and not target.exists()
files={'editor-reader-lifecycle.cjs':(root/'qualification/artifacts/editor-reader-lifecycle.cjs').read_bytes(),
       'reader-gate.txt':'Lecteurs réels, capacité conservée et restitution vérifiée.\n'.encode()}
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=False) as z:
    for name,data in sorted(files.items()):
        item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.create_system=3;item.compress_type=zipfile.ZIP_DEFLATED
        item.external_attr=(stat.S_IFREG|0o444)<<16;z.writestr(item,data)
print(json.dumps({'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()}}))
