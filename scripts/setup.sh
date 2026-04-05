#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[setup] Preparing Nyx local development environment"

if ! command -v npm >/dev/null 2>&1; then
  echo "[setup] npm is required but was not found"
  exit 1
fi

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "[setup] Python 3.12+ is required but was not found"
  exit 1
fi

echo "[setup] Installing frontend dependencies"
cd "$ROOT_DIR/frontend"
npm install

if [ ! -f .env.local ]; then
  cp .env.example .env.local
  echo "[setup] Created frontend/.env.local from .env.example"
fi

echo "[setup] Installing backend dependencies"
cd "$ROOT_DIR/backend"
"$PYTHON_BIN" -m venv .venv

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/Scripts/activate
fi

pip install -r requirements.txt
pip install -e .[dev]

if [ ! -f env.local.json ]; then
  cp env.local.example.json env.local.json
  echo "[setup] Created backend/env.local.json from env.local.example.json"
fi

echo "[setup] Local setup complete"
echo "[setup] Demo local credentials"
echo "  username: carlo@nyx.app"
echo "  password: nyx-local-pass"
