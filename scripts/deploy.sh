#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[deploy] Running backend deploy"
"$SCRIPT_DIR/deploy-backend.sh" "$@"

echo "[deploy] Running frontend deploy"
"$SCRIPT_DIR/deploy-frontend.sh"
