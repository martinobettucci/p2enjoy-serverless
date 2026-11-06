#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#preuves
# @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#réalisation-et-preuves
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $(cat /etc/hostname) == infra-serverless ]] || { echo 'SPARK DEV infra-serverless requis.' >&2; exit 1; }
compose=(docker compose -f compose.spark.yml --profile dev)
case "${1:-}" in
  build) "${compose[@]}" build --pull runtime; "${compose[@]}" build qualification ;;
  test) python3 ../e2e/runtime-validation.py ;;
  instances-test) python3 -B ../e2e/runtime-instances.py ;;
  lifecycle-test) python3 -B ../e2e/instance-lifecycle.py ;;
  *) echo 'Usage: bash dev.sh {build|test|instances-test|lifecycle-test}' >&2; exit 2 ;;
esac
