#!/usr/bin/env bash
# Create one virtualenv per Python project and install it in editable mode.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

install_project() {
  local dir="$1"
  local with_lib="${2:-no}"
  python3.11 -m venv "$dir/.venv"
  # shellcheck disable=SC1091
  (
    source "$dir/.venv/bin/activate"
    python -m pip install --upgrade pip
    if [[ "$with_lib" == "yes" ]]; then
      python -m pip install -e "$ROOT/libs/portal-common"
    fi
    python -m pip install -e "$dir[dev]"
  )
}

install_project "$ROOT/libs/portal-common" no
for service in identity-service policy-service billing-service contact-service api-gateway; do
  install_project "$ROOT/services/$service" yes
done
echo "Python environments are ready."
