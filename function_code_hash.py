# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md#format-v1 | docs/FUNCTION_CODE_HASH.md#calcul-opérateur-et-preuve-réelle
"""Canonical executable-package identity; every declaration shares this contract."""
import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata

SHA = re.compile(r'[0-9a-f]{64}')
METHODS = frozenset(('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'))


class PackageIdentityError(ValueError):
    """Fixed, non-sensitive diagnostics for a rejected package description."""


def require(condition, code):
    if not condition: raise PackageIdentityError(code)


def fields(value, names, code):
    require(isinstance(value, dict) and set(value) == set(names), code)


def safe_path(value):
    require(isinstance(value, str) and value and len(value.encode('utf8')) <= 512, 'invalid_file_path')
    require('\\' not in value and not ntpath.splitdrive(value)[0] and not any(unicodedata.category(c) == 'Cc' for c in value), 'invalid_file_path')
    require(all(p not in ('', '.', '..') and len(p.encode('utf8')) <= 255 for p in value.split('/')), 'invalid_file_path')
    return value


def cron(value):
    require(isinstance(value, str) and len(value) <= 256 and len(value.split()) == 5, 'invalid_schedule')
    for part, (low, high) in zip(value.split(), ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))):
        for item in part.split(','):
            matched = re.fullmatch(r'(\*|\d+(?:-\d+)?)(?:/(\d+))?', item)
            require(matched is not None, 'invalid_schedule')
            base, step = matched.groups()
            require(step is None or 1 <= int(step) <= high - low + 1, 'invalid_schedule')
            if base != '*':
                values = [int(n) for n in base.split('-')]
                require(all(low <= n <= high for n in values) and values[0] <= values[-1], 'invalid_schedule')
    return ' '.join(value.split())


def canonical_events(value):
    fields(value, ('http', 'schedules'), 'invalid_events')
    require(all(isinstance(value[k], list) and len(value[k]) <= 16 for k in value), 'invalid_events')
    endpoints = {}
    for row in value['http']:
        fields(row, ('path', 'methods', 'implicit'), 'invalid_http_event')
        require(type(row['implicit']) is bool, 'invalid_http_event')
        path = row['path']
        require(isinstance(path, str) and len(path) <= 256 and re.fullmatch(r'[A-Za-z0-9_/-]+', path) is not None, 'invalid_http_event')
        safe_path(path)
        methods = row['methods']
        require(isinstance(methods, list) and 1 <= len(methods) <= 7 and all(isinstance(m, str) and m in METHODS for m in methods), 'invalid_http_event')
        key = (row['implicit'], '' if row['implicit'] else path)
        endpoints.setdefault(key, set()).update(methods)
    http = []
    for (implicit, path), methods in sorted(endpoints.items()):
        row = {'implicit': implicit, 'methods': sorted(methods)}
        if not implicit: row['path'] = path
        http.append(row)
    schedules = {}
    for row in value['schedules']:
        fields(row, ('cron', 'enabled', 'timezone'), 'invalid_schedule')
        require(type(row['enabled']) is bool and row['timezone'] == 'UTC', 'invalid_schedule')
        item = {'cron': cron(row['cron']), 'enabled': row['enabled'], 'timezone': 'UTC'}
        schedules[(item['cron'], item['enabled'])] = item
    return {'http': http, 'schedules': [schedules[key] for key in sorted(schedules)]}


def canonical_execution(execution):
    fields(execution, ('handler', 'runtime', 'architecture', 'image_id', 'events'), 'invalid_execution')
    handler = execution['handler']
    require(isinstance(handler, str) and 3 <= len(handler) <= 256 and
            re.fullmatch(r'[A-Za-z0-9_./-]+\.[A-Za-z_$][A-Za-z0-9_$]*', handler) is not None, 'invalid_handler')
    module = handler.rsplit('.', 1)[0]
    require(not module.startswith('/') and all(part not in ('', '.', '..') for part in module.split('/')), 'invalid_handler')
    require(execution['runtime'] == 'node24' and execution['architecture'] == 'linux-x64', 'unsupported_execution')
    require(isinstance(execution['image_id'], str) and re.fullmatch(r'sha256:[0-9a-f]{64}', execution['image_id']) is not None, 'invalid_image')
    descriptor = {k: execution[k] for k in ('handler', 'runtime', 'architecture', 'image_id')}
    descriptor['events'] = canonical_events(execution['events'])
    return descriptor


def canonical_package(inventory, execution):
    descriptor = canonical_execution(execution)
    require(isinstance(inventory, list) and 1 <= len(inventory) <= 20000, 'invalid_inventory')
    files, seen, total = [], set(), 0
    for row in inventory:
        fields(row, ('path', 'size', 'sha256', 'mode'), 'invalid_inventory_entry')
        name = safe_path(row['path'])
        require(name not in seen, 'duplicate_file_path'); seen.add(name)
        require(type(row['size']) is int and 0 <= row['size'] <= 64 * 1024**2, 'invalid_file_size')
        total += row['size']; require(total <= 256 * 1024**2, 'package_size_limit')
        require(isinstance(row['sha256'], str) and SHA.fullmatch(row['sha256']) is not None, 'invalid_file_digest')
        require(row['mode'] in ('0o444', '0o555'), 'invalid_file_mode')
        files.append({'path': name, 'size': row['size'], 'sha256': row['sha256'], 'executable': row['mode'] == '0o555'})
    # A file cannot also be an ancestor of a different file.
    for name in seen:
        parts = name.split('/')
        require(not any('/'.join(parts[:i]) in seen for i in range(1, len(parts))), 'file_path_conflict')
    return {'format': 'p2enjoy.function-code/1', 'files': sorted(files, key=lambda f: f['path'].encode('utf8')), 'execution': descriptor}


def code_hash(inventory, execution):
    canonical = canonical_package(inventory, execution)
    raw = json.dumps(canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf8')
    return {'code_hash': hashlib.sha256(raw).hexdigest(), 'canonical': canonical}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key'); result[key] = value
    return result


def read_execution(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= 65536, 'invalid_execution_file')
        raw = stream.read(65537); after = os.fstat(stream.fileno())
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and len(raw) == before.st_size, 'execution_file_changed')
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(PackageIdentityError('invalid_json_number')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True); parser.add_argument('--destination', required=True)
    parser.add_argument('--execution', required=True); args = parser.parse_args()
    try:
        from control.app.artifacts import ArtifactError, extract
        execution = read_execution(args.execution)
        # Validate the public descriptor before publishing an extracted directory.
        canonical_execution(execution)
        extracted = extract(Path(args.archive), Path(args.destination))
        result = code_hash(extracted['inventory'], execution)
        result['extraction'] = extracted
        print(json.dumps(result, ensure_ascii=False)); return 0
    except (PackageIdentityError, ArtifactError, OSError, ValueError, TypeError, RecursionError):
        print(json.dumps({'error': 'package_identity_rejected'})); return 1


if __name__ == '__main__': raise SystemExit(main())
