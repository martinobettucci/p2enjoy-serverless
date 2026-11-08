# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#lecture-et-périmètre
# All queries project existing public metadata; no configuration values or code are searched.
from contextlib import contextmanager
from typing import Literal
import unicodedata
from urllib.parse import parse_qsl, urlencode
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request


SORTS = ('name_asc', 'name_desc', 'updated_asc', 'updated_desc')
MAX_OFFSET = 2147483647
MAX_PAGE = MAX_OFFSET // 25 + 1


def search_text(value):
    return ''.join(character for character in unicodedata.normalize('NFKD', value or '')
                   if not unicodedata.combining(character)).casefold()


def search_query(value):
    if len(value) > 200 or any(unicodedata.category(c) in ('Cc', 'Cf', 'Cs') for c in value):
        raise ValueError('Recherche limitée à 200 caractères sans caractère de contrôle.')
    value = ' '.join(value.split())
    if len(value.split()) > 8:
        raise ValueError('La recherche accepte au plus huit mots.')
    return value, search_text(value).split()


# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#parcours-et-adresses
def catalogue_query(value):
    """Validate a return query, never a user-supplied path or origin."""
    if len(value) > 4096:
        raise ValueError('catalogue_context_limit')
    pairs = parse_qsl(value, keep_blank_values=True, max_num_fields=6)
    allowed = ('q', 'namespace_id', 'service_id', 'state', 'sort', 'page')
    if any(key not in allowed for key, _ in pairs) or len(dict(pairs)) != len(pairs):
        raise ValueError('catalogue_context_fields')
    params = dict(pairs)
    result = {}
    for key in allowed:
        item = params.get(key, '')
        if not item:
            continue
        if key == 'q':
            item, _ = search_query(item)
        elif key in ('namespace_id', 'service_id'):
            if str(UUID(item)) != item:
                raise ValueError('catalogue_context_uuid')
        elif key == 'state' and item not in ('draft', 'published'):
            raise ValueError('catalogue_context_state')
        elif key == 'sort':
            if item not in SORTS:
                raise ValueError('catalogue_context_sort')
            if item == 'name_asc':
                continue
        elif key == 'page':
            if not item.isascii() or not item.isdecimal() or not 1 <= int(item) <= MAX_PAGE:
                raise ValueError('catalogue_context_page')
            item = str(int(item))
            if item == '1':
                continue
        if item:
            result[key] = item
    return urlencode(result)


@contextmanager
def snapshot(database):
    db = database.connect()
    try:
        db.create_function('catalogue_text', 1, search_text, deterministic=True)
        db.execute('BEGIN')
        yield db
    finally:
        db.rollback()
        db.close()


def words(value):
    try:
        return search_query(value)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None


def text_predicates(fields, terms, where, args):
    blob = 'catalogue_text(' + " || char(10) || ".join(f'coalesce({field},\'\')' for field in fields) + ')'
    for term in terms:
        where.append(f'instr({blob},?)>0')
        args.append(term)


def routes(database, identity):
    api = APIRouter(prefix='/api')

    @api.get('/functions')
    async def functions(request: Request, q: str = Query('', max_length=200),
                        namespace_id: UUID | None = None, service_id: UUID | None = None,
                        state: Literal['draft', 'published'] | None = None,
                        sort: Literal['name_asc', 'name_desc', 'updated_asc', 'updated_desc'] = 'name_asc',
                        limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0, le=MAX_OFFSET)):
        await identity.admin(request)
        query, terms = words(q)
        join = '''FROM functions f JOIN services s ON s.id=f.service_id
                  JOIN namespaces n ON n.id=s.namespace_id
                  LEFT JOIN revisions r ON r.id=f.active_revision_id AND r.function_id=f.id AND r.deleted_at IS NULL'''
        where = ['f.deleted_at IS NULL', 's.deleted_at IS NULL', 'n.deleted_at IS NULL']
        args = []
        for key, value in (('n.id', namespace_id), ('s.id', service_id)):
            if value is not None:
                where.append(key + '=?'); args.append(str(value))
        if state:
            where.append('r.id IS ' + ('NULL' if state == 'draft' else 'NOT NULL'))
        text_predicates(('f.name', 'f.id', 's.name', 's.id', 'n.name', 'n.id',
                         "json_extract(f.config_json,'$.handler')", 's.description', 'n.description'), terms, where, args)
        predicate = ' WHERE ' + ' AND '.join(where)
        order = {'name_asc': 'catalogue_text(f.name) ASC', 'name_desc': 'catalogue_text(f.name) DESC',
                 'updated_asc': 'f.updated_at ASC', 'updated_desc': 'f.updated_at DESC'}[sort]
        order += ',catalogue_text(n.name),catalogue_text(s.name),f.id'
        with snapshot(database) as db:
            total = db.execute('SELECT count(*) ' + join + predicate, args).fetchone()[0]
            rows = db.execute('''SELECT f.id,f.name,f.updated_at,s.id service_id,s.name service_name,
                                 n.id namespace_id,n.name namespace_name,
                                 json_extract(f.config_json,'$.handler') handler,r.id revision_id ''' +
                              join + predicate + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?', [*args, limit, offset]).fetchall()
            items = [{'id': row['id'], 'name': row['name'], 'handler': row['handler'],
                      'updated_at': row['updated_at'], 'revision_id': row['revision_id'],
                      'state': 'published' if row['revision_id'] else 'draft',
                      'service': {'id': row['service_id'], 'name': row['service_name']},
                      'namespace': {'id': row['namespace_id'], 'name': row['namespace_name']}} for row in rows]
            selected = {}
            if namespace_id:
                row = db.execute('SELECT id,name FROM namespaces WHERE id=? AND deleted_at IS NULL', (str(namespace_id),)).fetchone()
                selected['namespace'] = {**dict(row), 'available': True} if row else {'id': str(namespace_id), 'available': False}
            if service_id:
                row = db.execute('''SELECT s.id,s.name,n.name namespace_name,n.id namespace_id FROM services s
                                    JOIN namespaces n ON n.id=s.namespace_id WHERE s.id=? AND s.deleted_at IS NULL AND n.deleted_at IS NULL''',
                                 (str(service_id),)).fetchone()
                selected['service'] = {**dict(row), 'available': True} if row else {'id': str(service_id), 'available': False}
        return {'items': items, 'total': total, 'limit': limit, 'offset': offset, 'selected': selected,
                'criteria': {'q': query, 'namespace_id': str(namespace_id) if namespace_id else None,
                             'service_id': str(service_id) if service_id else None, 'state': state, 'sort': sort}}

    # @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#choisir-les-filtres
    def parents(kind, q, limit, offset, namespace_id=None):
        query, terms = words(q)
        if kind == 'namespaces':
            join = 'FROM namespaces n'; where = ['n.deleted_at IS NULL']; args = []
            projection = 'n.id,n.name,n.description'
            fields = ('n.id', 'n.name', 'n.description'); order = 'catalogue_text(n.name),n.id'
        else:
            join = 'FROM services s JOIN namespaces n ON n.id=s.namespace_id'
            where = ['s.deleted_at IS NULL', 'n.deleted_at IS NULL']; args = []
            projection = 's.id,s.name,s.description,n.id namespace_id,n.name namespace_name'
            fields = ('s.id', 's.name', 's.description', 'n.id', 'n.name', 'n.description')
            order = 'catalogue_text(s.name),catalogue_text(n.name),s.id'
            if namespace_id is not None:
                where.append('n.id=?'); args.append(str(namespace_id))
        text_predicates(fields, terms, where, args)
        predicate = ' WHERE ' + ' AND '.join(where)
        with snapshot(database) as db:
            total = db.execute('SELECT count(*) ' + join + predicate, args).fetchone()[0]
            rows = db.execute('SELECT ' + projection + ' ' + join + predicate + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?',
                              [*args, limit, offset]).fetchall()
        return {'items': [dict(row) for row in rows], 'total': total, 'limit': limit, 'offset': offset, 'q': query}

    @api.get('/catalogue/namespaces')
    async def namespaces(request: Request, q: str = Query('', max_length=200),
                         limit: int = Query(5, ge=1, le=50), offset: int = Query(0, ge=0, le=MAX_OFFSET)):
        await identity.admin(request)
        return parents('namespaces', q, limit, offset)

    @api.get('/catalogue/services')
    async def services(request: Request, q: str = Query('', max_length=200), namespace_id: UUID | None = None,
                       limit: int = Query(5, ge=1, le=50), offset: int = Query(0, ge=0, le=MAX_OFFSET)):
        await identity.admin(request)
        return parents('services', q, limit, offset, namespace_id)

    return api
