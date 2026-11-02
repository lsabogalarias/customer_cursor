#!/usr/bin/env bash
# Run pytest, ruff, and mypy for every Python project.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check() {
  local dir="$1"
  echo "== $dir =="
  (
    cd "$ROOT/$dir"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    if [[ -d tests ]]; then
      pytest
    fi
    if [[ -d tests ]]; then
      ruff check src tests
    else
      ruff check src
    fi
    mypy src
  )
}

check libs/portal-common
for service in identity-service policy-service billing-service contact-service api-gateway; do
  check "services/$service"
done
