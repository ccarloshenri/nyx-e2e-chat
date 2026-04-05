#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[test-local] Running backend tests in local/mock mode"
cd "$ROOT_DIR/backend"
APP_ENV=local INFRA_MODE=mock pytest

echo "[test-local] Running frontend build validation"
cd "$ROOT_DIR/frontend"
npm run build

echo "[test-local] Local validation completed"
