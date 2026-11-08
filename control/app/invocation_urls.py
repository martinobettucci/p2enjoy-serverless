# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#source-officielle-et-limites | docs/INVOCATION_URLS.md#api-et-calcul-commun
"""Read the SPARK's official route projection; never infer domains from Host."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request

ROUTES = Path('/spark/routes')
MAX_BYTES = 64 * 1024
MAX_ROUTES = 512
DOMAIN = re.compile(r'(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', re.ASCII)
EMPTY_MARKER = '# Aucune route ne vise ce Spark.'


def read_routes(port):
    source = {'state': 'unavailable', 'observed_at': time.time()}
    try:
        # NONBLOCK also prevents a non-regular source from hanging before fstat.
        fd = os.open(ROUTES, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_BYTES:
                raise ValueError('invalid_source')
            raw = stream.read(MAX_BYTES + 1)
            after = os.fstat(stream.fileno())
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        named = os.stat(ROUTES, follow_symlinks=False)
        if identity(before) != identity(after) or identity(after) != identity(named) or len(raw) != before.st_size:
            raise ValueError('source_changed')
        if len(raw) > MAX_BYTES or not raw.endswith(b'\n'):
            raise ValueError('invalid_source')
        rows = {}; count = 0; empty = False
        for line in raw.decode('utf-8', errors='strict').splitlines():
            line = line.strip()
            if not line: continue
            if line.startswith('#'):
                empty |= line == EMPTY_MARKER
                continue
            count += 1
            if count > MAX_ROUTES: raise ValueError('source_limit')
            fields = line.split()
            if len(fields) not in (2, 3): raise ValueError('invalid_source')
            domain = fields[0].lower(); number = fields[1]; mode = fields[2] if len(fields) == 3 else 'tls'
            if (len(domain) > 253 or not DOMAIN.fullmatch(domain) or
                    not re.fullmatch(r'[0-9]{1,5}', number, re.ASCII) or not 1 <= int(number) <= 65535 or
                    mode not in ('tls', 'clair')):
                raise ValueError('invalid_source')
            route = (int(number), mode)
            if domain in rows and rows[domain] != route: raise ValueError('conflicting_source')
            rows[domain] = route
        if not rows and not empty: raise ValueError('incomplete_source')
        applicable = [{'domain': domain, 'origin': ('https://' if mode == 'tls' else 'http://') + domain,
                       'transport': 'https' if mode == 'tls' else 'http'}
                      for domain, (target, mode) in sorted(rows.items()) if target == port]
        source.update(state='available', mtime=before.st_mtime, sha256=hashlib.sha256(raw).hexdigest())
        return source, applicable
    except PermissionError: code = 'source_forbidden'
    except FileNotFoundError: code = 'source_missing'
    except UnicodeError: code = 'invalid_source'
    except ValueError as error: code = str(error)
    except OSError: code = 'source_unavailable'
    source['error_code'] = code
    return source, []


def routes(db, identity, settings):
    api = APIRouter()

    @api.get('/api/functions/{key}/invocation-urls')
    async def catalogue(request: Request, key: UUID, limit: int = Query(5, ge=1, le=20),
                        offset: int = Query(0, ge=0, le=10000)):
        function_id = str(key)
        initial = db.one('SELECT service_id FROM functions WHERE id=? AND deleted_at IS NULL', (function_id,))
        authorization = await identity.operation(request, initial['service_id'] if initial else '', 'read', function_id)
        if not initial: raise HTTPException(404, 'Fonction introuvable.')
        # One snapshot binds the active pointer to precisely that revision's events.
        with closing(db.connect()) as connection:
            connection.execute('BEGIN')
            row = connection.execute('''SELECT f.id, f.service_id, r.id AS revision_id, r.events_json
                FROM functions f JOIN services s ON s.id=f.service_id AND s.deleted_at IS NULL
                JOIN namespaces n ON n.id=s.namespace_id AND n.deleted_at IS NULL
                LEFT JOIN revisions r ON r.id=f.active_revision_id AND r.function_id=f.id AND r.deleted_at IS NULL
                WHERE f.id=? AND f.deleted_at IS NULL''', (function_id,)).fetchone()
            if not row: raise HTTPException(404, 'Fonction ou service introuvable.')
            identity.recheck(connection, authorization, row['service_id'], 'read', function_id)
        server = request.scope.get('server')
        if not server or not isinstance(server[1], int) or not 1 <= server[1] <= 65535:
            source = {'state': 'unavailable', 'observed_at': time.time(), 'error_code': 'gateway_port_unavailable'}
            domains = []
        else:
            source, domains = read_routes(server[1])
        wildcards = [item['domain'] for item in domains if item['domain'].startswith('*.')]
        concrete = [item for item in domains if not item['domain'].startswith('*.')]
        items = []
        for domain in concrete[offset:offset + limit]:
            urls = {}
            if row['revision_id']:
                for event in json.loads(row['events_json']).get('http', []):
                    path = '/invoke/' + function_id + ('' if event.get('implicit') else '/' + event['path'])
                    methods = urls.setdefault(path, set()); methods.update(event['methods'])
            items.append({**domain, 'urls': [{'url': domain['origin'] + path, 'methods': sorted(methods)}
                                            for path, methods in sorted(urls.items())]})
        return {'function_id': function_id, 'service_id': row['service_id'], 'revision_id': row['revision_id'],
                'function_state': 'published' if row['revision_id'] else 'draft',
                'console_url': settings.public_url + '/console/functions/' + function_id + '/invocation-urls',
                'source': source, 'items': items, 'total': len(concrete), 'limit': limit, 'offset': offset,
                'wildcards': wildcards}

    return api
