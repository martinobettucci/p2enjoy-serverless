# @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
# @verifies docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
"""Package original journal handlers without importing or executing them."""
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

root=Path(__file__).resolve().parents[1]
assert len(sys.argv)==3,'archive_and_marker_required'
target=Path(sys.argv[1]).resolve();marker=sys.argv[2]
assert target.is_relative_to(root/'.local/e2e') and target.parent.is_dir()
assert not target.exists() and not target.is_symlink()
assert re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',marker),'public_package_marker_required'
handler=(root/'qualification/artifacts/execution-journal.cjs').read_bytes()
descriptor=json.dumps({'value':marker},separators=(',',':')).encode()
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=False) as archive:
    for name,content in [('execution-journal.cjs',handler),('execution-journal-marker.json',descriptor)]:
        item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.create_system=3
        item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=(stat.S_IFREG|0o444)<<16
        archive.writestr(item,content)
with zipfile.ZipFile(target) as archive:
    assert len(archive.infolist())==2 and archive.testzip() is None
print(json.dumps({'path':str(target),'entries':2,'archive_bytes':target.stat().st_size,
    'archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'handler_sha256':hashlib.sha256(handler).hexdigest(),'marker_sha256':hashlib.sha256(descriptor).hexdigest(),
    'all_crc_valid':True}))
