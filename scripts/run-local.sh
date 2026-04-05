#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""

cleanup() {
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "[run-local] Stopping backend"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

if ! command -v sam >/dev/null 2>&1; then
  echo "[run-local] AWS SAM CLI is required"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[run-local] npm is required"
  exit 1
fi

cd "$ROOT_DIR/backend"

if [ ! -f env.local.json ]; then
  cp env.local.example.json env.local.json
fi

echo "[run-local] Starting backend with in-memory infrastructure"
sam build >/dev/null
sam local start-api --env-vars env.local.json > "$ROOT_DIR/backend/.sam-local.log" 2>&1 &
BACKEND_PID=$!

sleep 5

echo "[run-local] Backend URL: http://127.0.0.1:3000"
echo "[run-local] Starting frontend dev server"

cd "$ROOT_DIR/frontend"

if [ ! -f .env.local ]; then
  cp .env.example .env.local
fi

npm run dev
