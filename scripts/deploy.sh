#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v sam >/dev/null 2>&1; then
  echo "[deploy] AWS SAM CLI is required"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[deploy] npm is required"
  exit 1
fi

echo "[deploy] Building and deploying backend"
cd "$ROOT_DIR/backend"
sam build
sam deploy "${@}"

echo "[deploy] Building frontend"
cd "$ROOT_DIR/frontend"
npm install
npm run build

if [ -n "${FRONTEND_BUCKET:-}" ]; then
  echo "[deploy] Uploading frontend dist/ to s3://$FRONTEND_BUCKET"
  aws s3 sync dist/ "s3://$FRONTEND_BUCKET"
else
  echo "[deploy] FRONTEND_BUCKET not set, skipping S3 sync"
fi
