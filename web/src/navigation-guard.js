// @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#détail-de-la-facette-console--12novembre2026-avant-code | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md#modifier-le-code-dans-la-console
// Registered only while an editor is mounted; no content or preference is persisted.
const guards = new Set();
export function registerNavigationGuard(check) {
  guards.add(check);
  return () => guards.delete(check);
}
export async function confirmNavigation() {
  for (const check of [...guards]) if (!await check()) return false;
  return true;
}
