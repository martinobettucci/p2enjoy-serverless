#!/usr/bin/env bash
# @spec docs/BACKLOG.md#qlf-001 | docs/DAT.md#qualification
set -euo pipefail
cd -- "$(dirname -- "$0")"
compose=(docker compose -f compose.dev.yml)
if [[ "${1:-}" == "--spark" ]]; then
  compose+=(-f compose.spark.yml)
  shift
fi
compose+=(--profile dev)
case "${1:-}" in
  build) "${compose[@]}" build qualification ;;
  up) "${compose[@]}" up -d --wait --wait-timeout 60 qualification ;;
  test) "${compose[@]}" run --rm -T --no-deps e2e npm test ;;
  test-absent) "${compose[@]}" run --rm -T --no-deps e2e node tests/configuration-absent.cjs ;;
  operations)
    [[ "${compose[*]}" == *compose.spark.yml* ]] || { printf '%s\n' 'operations requires the authorized DEV Spark' >&2; exit 2; }
    python3 tests/operations.py
    ;;
  check) "${compose[@]}" exec -T qualification npm run check ;;
  probe) "${compose[@]}" run --rm -T --no-deps e2e npm run probe ;;
  recreate-proof)
    "${compose[@]}" run --rm -T --no-deps e2e node tests/probe.cjs before-recreate
    "${compose[@]}" up -d --force-recreate --wait --wait-timeout 60 qualification
    "${compose[@]}" run --rm -T --no-deps e2e node tests/probe.cjs after-recreate
    ;;
  logs) "${compose[@]}" logs --tail 30 qualification ;;
  status) "${compose[@]}" ps qualification ;;
  stop) "${compose[@]}" stop qualification ;;
  *) printf '%s\n' 'Usage: bash dev.sh [--spark] build|up|check|test|test-absent|probe|recreate-proof|operations|logs|status|stop' >&2; exit 2 ;;
esac
