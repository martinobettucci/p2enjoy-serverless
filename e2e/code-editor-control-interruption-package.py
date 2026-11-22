# @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_CONTROL_INTERRUPTION.md#décision-et-frontières-observables
# @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_CONTROL_INTERRUPTION.md#quatre-groupes-ciblés-puis-25-communs-frais
"""Original complete ZIP for a real receiving/extraction observation window."""
import hashlib
import json
from pathlib import Path
import stat
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
target = Path(sys.argv[1]).resolve()
assert target.is_relative_to(root / '.local/e2e') and target.parent.is_dir()
assert not target.exists() and not target.is_symlink()
handler = (root / 'qualification/artifacts/publication-recovery.cjs').read_bytes()
marker = json.dumps({'value': 'stable-A', 'validation_delay_ms': 0}).encode()
total = 0
inventory = hashlib.sha256()
with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, allowZip64=False) as archive:
    for name, content in [('publication-recovery.cjs', handler), ('publication-marker.json', marker),
                          *((f'extraction-inputs/file-{index:05d}.txt',
                             f'Entrée originale {index:05d} : extraction réelle, intégrité et conservation après redémarrage.\n'.encode())
                            for index in range(18000))]:
        item = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
        item.create_system = 3
        item.compress_type = zipfile.ZIP_DEFLATED
        item.external_attr = (stat.S_IFREG | 0o444) << 16
        archive.writestr(item, content)
        total += len(content)
        inventory.update(json.dumps({'path': name, 'bytes': len(content),
                                     'sha256': hashlib.sha256(content).hexdigest()}, sort_keys=True).encode() + b'\n')
with zipfile.ZipFile(target) as archive:
    assert len(archive.infolist()) == 18002 and archive.testzip() is None
assert total < 256 * 1024**2 and target.stat().st_size < 64 * 1024**2
print(json.dumps({'entries': 18002, 'original_text_files': 18000, 'expanded_bytes': total,
                  'archive_bytes': target.stat().st_size, 'archive_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'inventory_sha256': inventory.hexdigest(), 'all_crc_valid': True,
                  'handler_sha256': hashlib.sha256(handler).hexdigest(), 'marker_sha256': hashlib.sha256(marker).hexdigest()}))
