// @spec docs/DESIGN_SYSTEM.md | docs/BACKLOG.md#sls-020 | docs/CONTROL.md#console-du-contrôle
let csrf = '';
export function sessionToken(value) { csrf = value || ''; }
export async function api(path, options = {}) {
  const method = options.method || 'GET';
  const archive = options.body instanceof Blob;
  const response = await fetch(path, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? {'Content-Type': archive ? 'application/zip' : 'application/json'} : {}),
      ...(method !== 'GET' ? {'X-CSRF-Token': csrf} : {}),
      ...options.headers,
    },
    credentials: 'same-origin',
    body: options.body === undefined ? undefined : archive ? options.body : JSON.stringify(options.body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    // @spec docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#attente-de-droits
    if (response.status === 403 && ['verification','administration'].includes(data.access_requirement)) {
      const destination = '/auth/attente?reason=' + data.access_requirement;
      if (location.pathname + location.search !== destination) location.assign(destination);
    }
    const error = new Error(data.error || `Le serveur a refusé la requête (${response.status}).`);
    error.status = response.status;
    // @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER_FAILURES.md#défaut-reproduit-après-admission--correction0718
    error.fromControl = response.headers.get('X-Serverless-Control-Response') === '1' && typeof data.error === 'string';
    error.details = data.details;
    throw error;
  }
  return data;
}
