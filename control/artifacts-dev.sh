#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#artefact
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $(cat /etc/hostname) == infra-serverless ]] || { echo 'SPARK DEV infra-serverless requis.' >&2; exit 1; }
case "${1:-}" in
  build) docker compose -f compose.artifacts.spark.yml --profile dev build --pull ;;
  test) python3 ../e2e/artifacts.py ;;
  *) echo 'Usage: bash artifacts-dev.sh {build|test}' >&2; exit 2 ;;
esac
