// @spec docs/DESIGN_SYSTEM.md | docs/BACKLOG.md#sls-020 | docs/CONTROL.md#console-du-contrôle
let csrf = '';
export function sessionToken(value) { csrf = value || ''; }
export async function api(path, options = {}) {
  const method = options.method || 'GET';
  const response = await fetch(path, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? {'Content-Type': 'application/json'} : {}),
      ...(method !== 'GET' ? {'X-CSRF-Token': csrf} : {}),
      ...options.headers,
    },
    credentials: 'same-origin',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || `Le serveur a refusé la requête (${response.status}).`);
    error.status = response.status;
    error.details = data.details;
    throw error;
  }
  return data;
}
