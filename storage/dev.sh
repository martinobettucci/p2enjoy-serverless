#!/usr/bin/env bash
# @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#réalisation-et-preuves
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $(cat /etc/hostname) == infra-serverless ]] || { echo 'SPARK DEV infra-serverless requis.' >&2; exit 1; }
case "${1:-}" in
  build)
    docker build -t p2enjoy-quota-build:dev .
    container=$(docker create p2enjoy-quota-build:dev)
    trap 'docker rm "$container" >/dev/null' EXIT
    docker cp "$container:/p2-quota" p2-quota
    ;;
  install) python3 -I -B install-dev.py ;;
  agent-test) python3 -I -B agent-proof.py ;;
  limits-test) python3 -I -B agent-proof.py --limits ;;
  status) systemctl status --no-pager p2enjoy-storage-dev.service ;;
  *) echo 'Usage: bash dev.sh {build|install|agent-test|limits-test|status}' >&2; exit 2 ;;
esac
