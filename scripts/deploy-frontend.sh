#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK_NAME="nyx-main"

if ! command -v npm >/dev/null 2>&1; then
  echo "[deploy-frontend] npm is required"
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "[deploy-frontend] AWS CLI is required"
  exit 1
fi

AWS_REGION="$(aws configure get region)"
AWS_REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

if [ -z "$ACCOUNT_ID" ] || [ "$ACCOUNT_ID" = "None" ]; then
  echo "[deploy-frontend] Could not resolve AWS account id"
  exit 1
fi

if [ -n "${FRONTEND_BUCKET:-}" ]; then
  TARGET_BUCKET="${FRONTEND_BUCKET}"
else
  TARGET_BUCKET="nyx-frontend-${ACCOUNT_ID}-${AWS_REGION}"
fi

if aws s3api head-bucket --bucket "$TARGET_BUCKET" >/dev/null 2>&1; then
  echo "[deploy-frontend] Frontend bucket already exists: s3://$TARGET_BUCKET"
else
  echo "[deploy-frontend] Creating frontend bucket s3://$TARGET_BUCKET"
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$TARGET_BUCKET" >/dev/null
  else
    aws s3api create-bucket --bucket "$TARGET_BUCKET" --create-bucket-configuration "LocationConstraint=${AWS_REGION}" >/dev/null
  fi
fi

echo "[deploy-frontend] Building frontend"
cd "$ROOT_DIR/frontend"
npm install

API_BASE_URL="${VITE_API_BASE_URL:-}"
if [ -z "$API_BASE_URL" ]; then
  API_BASE_URL="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" --output text 2>/dev/null || true)"
fi

if [ -n "$API_BASE_URL" ] && [ "$API_BASE_URL" != "None" ]; then
  echo "[deploy-frontend] Using backend URL: $API_BASE_URL"
  VITE_API_BASE_URL="$API_BASE_URL" npm run build
else
  echo "[deploy-frontend] Could not resolve backend URL, building frontend with existing environment"
  npm run build
fi

echo "[deploy-frontend] Uploading frontend dist/ to s3://$TARGET_BUCKET"
aws s3 sync dist/ "s3://$TARGET_BUCKET"
