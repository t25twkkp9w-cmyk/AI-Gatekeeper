#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Run ./setup.sh first to create the Python environment.' >&2
  exit 1
fi
if [[ ! -d frontend/node_modules ]]; then
  echo 'Run ./setup.sh first to install frontend dependencies.' >&2
  exit 1
fi
for port in 8100 3100; do
  if lsof -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Port $port is already in use. Stop the existing Gatekeeper session or use its URL." >&2
    exit 1
  fi
done
if [[ ! -f frontend/.next/BUILD_ID ]]; then
  npm --prefix frontend run build
fi
mkdir -p runtime
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 &
API_PID=$!
(cd frontend && npm run start) &
WEB_PID=$!
trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null || true' EXIT INT TERM
echo 'AI Gatekeeper: http://127.0.0.1:3100'
wait "$WEB_PID"
