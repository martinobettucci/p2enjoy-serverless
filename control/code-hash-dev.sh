#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md#calcul-opérateur-et-preuve-réelle
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $(cat /etc/hostname) == infra-serverless && $(id -u) == 1001 ]] || { echo 'SPARK DEV et compte spark-docker requis.' >&2; exit 1; }
case "${1:-}" in
  build) docker compose -f compose.code-hash.spark.yml --profile dev build ;;
  test) python3 -B ../e2e/function-code-hash.py ;;
  *) echo 'Usage: bash code-hash-dev.sh {build|test}' >&2; exit 2 ;;
esac
