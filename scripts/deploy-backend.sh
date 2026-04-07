#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="main"
STACK_NAME="nyx-main"

if ! command -v sam >/dev/null 2>&1; then
  echo "[deploy-backend] AWS SAM CLI is required"
  exit 1
fi

if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
  echo "[deploy-backend] Python 3.12+ is required"
  exit 1
fi

echo "[deploy-backend] Building and deploying backend"
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
