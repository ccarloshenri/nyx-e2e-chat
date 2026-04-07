#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="main"
STACK_NAME="nyx-main"

if ! command -v sam >/dev/null 2>&1; then
  echo "[deploy] AWS SAM CLI is required"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[deploy] npm is required"
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "[deploy] AWS CLI is required"
  exit 1
fi

AWS_REGION="$(aws configure get region)"
AWS_REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

if [ -n "${FRONTEND_BUCKET:-}" ]; then
  TARGET_BUCKET="${FRONTEND_BUCKET}"
else
  TARGET_BUCKET="nyx-frontend-${ACCOUNT_ID}-${AWS_REGION}"
fi

if aws s3api head-bucket --bucket "$TARGET_BUCKET" >/dev/null 2>&1; then
  echo "[deploy] Frontend bucket already exists: s3://$TARGET_BUCKET"
else
  echo "[deploy] Creating frontend bucket s3://$TARGET_BUCKET"
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$TARGET_BUCKET" >/dev/null
  else
    aws s3api create-bucket --bucket "$TARGET_BUCKET" --create-bucket-configuration "LocationConstraint=${AWS_REGION}" >/dev/null
  fi
fi

echo "[deploy] Building and deploying backend"
cd "$ROOT_DIR/backend"
sam build
sam deploy \
  --stack-name "$STACK_NAME" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    StageName="$STAGE" \
    UsersTableName="nyx-users-${STAGE}" \
    ConnectionsTableName="nyx-connections-${STAGE}" \
    ConversationsTableName="nyx-conversations-${STAGE}" \
    MessagesTableName="nyx-messages-${STAGE}" \
    MessageQueueName="nyx-message-delivery-${STAGE}.fifo" \
    MessageDlqName="nyx-message-delivery-dlq-${STAGE}.fifo" \
  "$@"

echo "[deploy] Building frontend"
cd "$ROOT_DIR/frontend"
npm install

API_BASE_URL="$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" --output text 2>/dev/null || true)"
if [ -n "$API_BASE_URL" ] && [ "$API_BASE_URL" != "None" ]; then
  echo "[deploy] Using deployed backend URL: $API_BASE_URL"
  VITE_API_BASE_URL="$API_BASE_URL" npm run build
else
  echo "[deploy] Could not resolve HttpApiUrl output, building frontend with existing environment"
  npm run build
fi

echo "[deploy] Uploading frontend dist/ to s3://$TARGET_BUCKET"
aws s3 sync dist/ "s3://$TARGET_BUCKET"
