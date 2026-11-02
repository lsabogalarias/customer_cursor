#!/usr/bin/env bash
# Start the gateway and the four services. Ctrl+C stops all of them.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/.run"
export JWT_SECRET="${JWT_SECRET:-dev-only-change-me}"
pids=()

start() {
  local name="$1"
  local dir="$2"
  local app="$3"
  local port="$4"
  (
    cd "$ROOT/$dir"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    exec uvicorn "$app" --host 127.0.0.1 --port "$port"
  ) >"$ROOT/.run/$name.log" 2>&1 &
  pids+=("$!")
  echo "$name listening on $port (pid $!)"
}

cleanup() {
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

start identity services/identity-service identity_service.main:app 8001
start policy services/policy-service policy_service.main:app 8002
start billing services/billing-service billing_service.main:app 8003
start contact services/contact-service contact_service.main:app 8004
start gateway services/api-gateway api_gateway.main:app 8000
echo "Logs: $ROOT/.run/*.log"
wait
