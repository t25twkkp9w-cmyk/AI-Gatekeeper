#!/usr/bin/env bash
set -euo pipefail
cd /app
: "${DEMO_USERNAME:?Set DEMO_USERNAME in Render}"
: "${DEMO_PASSWORD:?Set DEMO_PASSWORD in Render}"
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY in Render}"
: "${LANGSMITH_API_KEY:?Set LANGSMITH_API_KEY in Render}"
[[ "$DEMO_USERNAME" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'Invalid demo username'; exit 1; }
[[ ${#DEMO_PASSWORD} -ge 16 ]] || { echo 'Demo password must contain at least 16 characters'; exit 1; }
[[ "${PORT:-10000}" =~ ^[0-9]+$ ]] || exit 1
export GATEKEEPER_MODE=live LANGSMITH_TRACING=true
export LANGSMITH_PROJECT="${LANGSMITH_PROJECT:-ai-gatekeeper-hosted}"
umask 077
hashed=$(printf '%s\n' "$DEMO_PASSWORD" | openssl passwd -apr1 -stdin)
printf '%s:%s\n' "$DEMO_USERNAME" "$hashed" > /etc/nginx/gatekeeper.htpasswd
chown root:www-data /etc/nginx/gatekeeper.htpasswd
chmod 640 /etc/nginx/gatekeeper.htpasswd
unset hashed
sed "s/__PORT__/${PORT:-10000}/g" /app/deploy/nginx.conf > /etc/nginx/nginx.conf
mkdir -p "$GATEKEEPER_DATA_DIR"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100 &
api=$!
(cd frontend && node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3100) &
web=$!
nginx -g 'daemon off;' &
gateway=$!
trap 'kill "$api" "$web" "$gateway" 2>/dev/null || true; wait || true' EXIT
trap 'exit 0' TERM INT
wait -n "$api" "$web" "$gateway"
