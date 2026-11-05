#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#preuves
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -r /etc/spark/env && -r /run/spark/secrets ]] || { echo 'Exécuter dans le SPARK DEV configuré.' >&2; exit 1; }
compose=(docker compose -f compose.spark.yml --profile dev)
case "${1:-}" in
  build) "${compose[@]}" build --pull adapter; "${compose[@]}" build --pull e2e ;;
  plan) "${compose[@]}" run --rm adapter plan --config /project/serverless.platform.yml ;;
  package) "${compose[@]}" run --rm adapter package --config /project/serverless.platform.yml ;;
  test) "${compose[@]}" run --rm e2e ;;
  *) echo 'Usage: bash dev.sh {build|plan|package|test}' >&2; exit 2 ;;
esac
