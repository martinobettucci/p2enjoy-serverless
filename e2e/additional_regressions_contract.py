# @spec docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#formats-explicites-des-rapports-supplémentaires
# @verifies docs/BACKLOG.md#sls-072 | docs/SCHEMA_011_REGRESSIONS.md#exécution-preuves-et-clôture
"""Exact namespace formats and function inventories of current API campaigns."""
import re
from uuid import UUID

# prefix, suffix source, complete nominal function count. These describe real
# existing clients; shared prefixes deliberately remain the clients' own names.
API_CASES = {
    'code-draft-capacity': ('code-draft-capacity-', 'campaign36', 33),
    'code-editor': ('edition-', 'campaign8', 2),
    'code-editor-ui': ('edition-console-', 'campaign8', 1),
    'code-editor-source-limits': ('code-editor-source-limits-', 'campaign36', 1),
    'code-editor-source-access': ('code-editor-source-access-', 'campaign8', 2),
    'code-editor-source-lifecycle': ('code-editor-read-concurrency-', 'campaign8', 1),
    'code-editor-read-concurrency': ('code-editor-read-concurrency-', 'campaign8', 1),
    'code-editor-build-capacity': ('code-editor-read-concurrency-', 'campaign8', 2),
    'code-editor-ui-concurrency': ('code-editor-read-concurrency-', 'campaign8', 1),
    'code-editor-publication-continuity': ('code-editor-read-concurrency-', 'campaign8', 1),
    'code-editor-control-interruption': ('code-editor-control-interruption-', 'campaign8', 1),
    'code-editor-archive-boundaries': ('code-editor-archive-limits-', 'campaign8', 5),
    'function-http-client': ('function-http-client-', 'campaign36', 2),
    'function-http-client-ui': ('function-http-client-ui-', 'campaign36', 2),
    'function-http-client-admission': ('function-http-client-admission-', 'campaign16', 2),
    'function-http-client-confidentiality': ('function-http-client-confidentiality-', 'campaign16', 2),
    'function-http-client-loading': ('function-http-client-recovery-loading-', 'campaign8', 1),
    'function-http-client-recovery': ('function-http-client-recovery-', 'campaign16', 2),
    'function-http-client-source-access': ('source-access-', 'campaign8', 1),
    'function-http-client-task-exception': ('function-http-client-task-exception-', 'campaign8', 1),
    'function-http-client-token-loss': ('function-http-client-token-loss-', 'campaign16', 1),
    'function-version-state-transport': ('version-state-transport-', 'prefix', 1),
    'function-version-validation': ('version-validation-', 'prefix', 1),
    'function-version-upload-capacity': ('version-upload-capacity-', 'prefix', 1),
    'function-version-duplicate-recovery': ('version-duplicate-recovery-', 'prefix', 1),
    'function-versions-api': ('function-versions-', 'prefix', 1),
    'function-versions-ui': ('version-execution-ui-', 'prefix', 1),
    'function-versions-cli': ('version-cli-', 'namespace_name', 1),
    'function-versions-cli-docker-cli': ('version-cli-', 'namespace_name', 1),
    'function-versions-cli-docker-qualification': ('version-cli-', 'namespace_name', 1),
}
assert len(API_CASES) == 30 and sum(v[2] for v in API_CASES.values()) == 74


def validate_namespace(client, name, functions):
    prefix, source, count = API_CASES[client]
    suffix = {'campaign36': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
              'campaign16': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{2}'}.get(source, r'[0-9a-f]{8}')
    assert isinstance(name, str) and re.fullmatch(re.escape(prefix) + suffix, name), 'additional_namespace_format'
    assert isinstance(functions, list) and len(functions) == len(set(functions)) == count, 'additional_function_inventory'
    assert all(isinstance(v, str) and str(UUID(v)) == v for v in functions), 'additional_function_uuid'


def namespace_from_report(client, report, functions):
    prefix, source, _ = API_CASES[client]
    if source.startswith('campaign'):
        identifier = report['campaign']
        assert isinstance(identifier, str) and str(UUID(identifier)) == identifier
        name = prefix + identifier[:int(source.removeprefix('campaign'))]
    else:
        name = report[source]
    validate_namespace(client, name, functions)
    return name
