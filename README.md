# Nyx - End-to-End Encrypted Chat

Nyx is a secure real-time chat platform with a Python serverless backend and a React frontend. Message encryption and decryption happen only on the client. The backend only validates, stores, and forwards encrypted payloads.

## How To Test

Testing now happens through AWS deployment. The recommended flow is:

1. install dependencies
2. configure AWS credentials
3. deploy to a target stage
4. test the deployed environment

### First-time setup

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Bash:

```bash
./scripts/setup.sh
```

### Deploy and test the `develop` environment

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1 develop
```

Bash:

```bash
bash scripts/deploy.sh develop
```

This command:

- builds and deploys the backend with AWS SAM
- creates or updates a stage-specific stack
- builds the frontend against the deployed backend URL when the stack output is available
- optionally uploads `frontend/dist/` to S3 when `FRONTEND_BUCKET` is configured

After deployment:

- use the `HttpApiUrl` output from [backend/template.yaml](./backend/template.yaml) to test backend endpoints
- if you uploaded the frontend to S3, open the deployed frontend and test the full flow there
- if you did not upload the frontend, point your local frontend to the deployed API URL through [frontend/.env.example](./frontend/.env.example)

## Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Scripts](#scripts)
- [Environment Variables](#environment-variables)
- [AWS Deployment](#aws-deployment)
- [Useful Links](#useful-links)

## Overview

Nyx is designed for AWS deployment with:

- AWS Lambda
- API Gateway HTTP + WebSocket
- SQS
- DynamoDB
- JWT-based authentication

Core references:

- Backend directory: [backend/](./backend)
- Frontend directory: [frontend/](./frontend)
- Architecture documentation: [docs/architecture.md](./docs/architecture.md)
- AWS SAM template: [backend/template.yaml](./backend/template.yaml)
- Commit guidelines: [.codex/git-flow/](./.codex/git-flow/)

## Project Structure

- Backend: [backend/](./backend) -> serverless backend with Lambda entrypoints, layered application code, and AWS integrations
- Frontend: [frontend/](./frontend) -> React + TypeScript + Vite client
- Documentation: [docs/](./docs) -> architecture and supporting notes
- Scripts: [scripts/](./scripts) -> setup and deploy helpers

Important backend paths:

- Lambda entrypoints: [backend/src/functions/lambda/](./backend/src/functions/lambda)
- Application layers: [backend/src/layers/main/nyx/](./backend/src/layers/main/nyx)
- Example handler wiring: [backend/src/functions/lambda/login/app.py](./backend/src/functions/lambda/login/app.py)

Important frontend paths:

- Pages: [frontend/src/pages/](./frontend/src/pages)
- Services: [frontend/src/services/](./frontend/src/services)
- Crypto layer: [frontend/src/crypto/](./frontend/src/crypto)
- Auth context: [frontend/src/context/](./frontend/src/context)

## Scripts

### Setup

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Bash:

```bash
./scripts/setup.sh
```

This script installs frontend and backend dependencies and prepares the repository for deployment work.

### Deploy

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1 develop
```

Bash:

```bash
bash scripts/deploy.sh develop
```

The first argument is the target stage name. Example stages:

- `develop`
- `staging`
- `prod`

The deploy scripts create stage-specific resource names such as:

- `nyx-users-develop`
- `nyx-messages-develop`
- `nyx-message-delivery-develop.fifo`

If `FRONTEND_BUCKET` is set, the deploy scripts upload the frontend build to `s3://<bucket>-<stage>`.

## Environment Variables

### Backend

Backend configuration lives in:

- [backend/src/layers/main/nyx/config/settings.py](./backend/src/layers/main/nyx/config/settings.py)
- [backend/template.yaml](./backend/template.yaml)

Important backend variables in AWS:

```text
AWS_REGION=us-east-1
JWT_SECRET=change-me
JWT_EXP_MINUTES=60
LOG_LEVEL=INFO
```

### Frontend

Frontend configuration lives in:

- [frontend/.env.example](./frontend/.env.example)
- [frontend/src/utils/env.ts](./frontend/src/utils/env.ts)

Important frontend variable:

```text
VITE_API_BASE_URL=https://your-api-id.execute-api.your-region.amazonaws.com/develop
```

## AWS Deployment

The AWS infrastructure is defined in [backend/template.yaml](./backend/template.yaml).

### Configure AWS credentials

```powershell
aws configure
```

You will be asked for:

- AWS Access Key ID
- AWS Secret Access Key
- default region
- output format

If you use a profile:

```powershell
aws configure --profile nyx
sam deploy --guided --profile nyx
```

### Deploy manually

Backend:

```powershell
cd backend
sam build
sam deploy --stack-name nyx-e2e-chat-develop --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides StageName=develop UsersTableName=nyx-users-develop ConnectionsTableName=nyx-connections-develop ConversationsTableName=nyx-conversations-develop MessagesTableName=nyx-messages-develop MessageQueueName=nyx-message-delivery-develop.fifo MessageDlqName=nyx-message-delivery-dlq-develop.fifo
```

Frontend:

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL="https://your-api-id.execute-api.your-region.amazonaws.com/develop"
npm run build
aws s3 sync dist/ s3://YOUR_BUCKET-develop
```

## Useful Links

- Backend directory: [backend/](./backend)
- Frontend directory: [frontend/](./frontend)
- Scripts directory: [scripts/](./scripts)
- Architecture documentation: [docs/architecture.md](./docs/architecture.md)
- Backend README: [backend/README.md](./backend/README.md)
- AWS SAM template: [backend/template.yaml](./backend/template.yaml)
- Commit rules: [.codex/git-flow/commit-rules.md](./.codex/git-flow/commit-rules.md)
