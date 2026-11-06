#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md | docs/PLATFORM_DEV.md
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -r /etc/spark/env || ! -r /run/spark/secrets ]]; then
  echo 'Cette commande DEV s’exécute dans le SPARK configuré.' >&2
  exit 1
fi
compose=(docker compose --env-file /etc/spark/env --env-file /run/spark/secrets -f compose.spark.yml)
case "${1:-}" in
  build) "${compose[@]}" build --pull ;;
  up) "${compose[@]}" up -d --wait --wait-timeout 90 ;;
  status) "${compose[@]}" ps ;;
  logs) "${compose[@]}" logs --tail 100 control ;;
  stop) "${compose[@]}" stop ;;
  *) echo 'Usage: bash dev.sh {build|up|status|logs|stop}' >&2; exit 2 ;;
esac
