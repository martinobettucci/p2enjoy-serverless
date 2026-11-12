# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_LIMITS.md#campagne-https-de-sources-et-bornes
# @verifies docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#source-limites-et-modifications
"""Original boundary data added to the real packaged YAML and repository handlers."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

root=Path(__file__).resolve().parent.parent
target=Path(sys.argv[1]).resolve()
assert target.parent.is_dir() and target.is_relative_to(root/'.local/e2e') and not target.exists()
result=json.loads(subprocess.check_output([sys.executable,'-B',str(root/'e2e/code-editor-package.py'),str(target)],text=True,timeout=90))
files={
    'editor-source-limits.cjs':(root/'qualification/artifacts/editor-source-limits.cjs').read_bytes(),
    'large-source.txt':b'x'*(1024**2+1),
    'source-marker.txt':b'source-A\n',
    'diff-lines.txt':b'A\n'*2000,
    'diff-before-limit.txt':b'A\n'*2001,
    'diff-output.txt':b'A'*65500+b'\n',
}
with zipfile.ZipFile(target,'a',compression=zipfile.ZIP_DEFLATED,allowZip64=False) as archive:
    assert not set(files)&set(archive.namelist())
    for name,data in sorted(files.items()):
        entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.create_system=3;entry.compress_type=zipfile.ZIP_DEFLATED
        entry.external_attr=(stat.S_IFREG|(0o555 if name.endswith('.cjs') else 0o444))<<16
        archive.writestr(entry,data)
result.update(sha256=hashlib.sha256(target.read_bytes()).hexdigest(),files=result['files']+len(files),
              boundary_files={name:{'size':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()})
result.pop('file',None)
print(json.dumps(result))
