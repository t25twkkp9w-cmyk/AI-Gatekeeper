#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then
  export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.setup-cache}"
  export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$PWD/.python}"
  uv python install 3.12 --no-bin
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -r backend/requirements.lock.txt
else
  PYTHON_BIN="${PYTHON_BIN:-python3.12}"
  "$PYTHON_BIN" -m venv .venv
  .venv/bin/python -m pip install -r backend/requirements.lock.txt
fi
npm --prefix frontend ci --cache "$PWD/.npm-cache"
echo 'Setup complete. Run ./run-local.sh'
