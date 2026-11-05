#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md | docs/PLATFORM_DEV.md
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -r /etc/spark/env || ! -r /run/spark/secrets ]]; then
  echo 'Cette commande DEV s’exécute dans le SPARK configuré.' >&2
  exit 1
fi
case "${1:-}" in
  build) docker compose -f compose.spark.yml build --pull ;;
  up) docker compose -f compose.spark.yml up -d --wait --wait-timeout 90 ;;
  status) docker compose -f compose.spark.yml ps ;;
  logs) docker compose -f compose.spark.yml logs --tail 100 control ;;
  stop) docker compose -f compose.spark.yml stop ;;
  *) echo 'Usage: bash dev.sh {build|up|status|logs|stop}' >&2; exit 2 ;;
esac
