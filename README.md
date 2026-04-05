# Nyx - End-to-End Encrypted Chat

Nyx is a secure real-time chat platform with a Python serverless backend and a React frontend. The project is designed around end-to-end encryption: the frontend encrypts and decrypts messages, while the backend only validates, stores, and forwards encrypted payloads.

## Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Local Testing Strategy](#local-testing-strategy)
- [Environment Variables](#environment-variables)
- [AWS Deployment](#aws-deployment)
- [Testing](#testing)
- [Useful Links](#useful-links)

## Overview

Nyx is built to support two infrastructure modes:

- `mock` mode for local development without AWS dependencies
- `aws` mode for real deployment with Lambda, DynamoDB, SQS, and WebSocket infrastructure

In local development, the backend runs with in-memory implementations for persistence, queueing, and realtime delivery. That means you can develop the main flows without DynamoDB, SQS, API Gateway, or AWS credentials.

Core references:

- Backend directory: [backend/](./backend)
- Frontend directory: [frontend/](./frontend)
- Architecture documentation: [docs/architecture.md](./docs/architecture.md)
- AWS SAM template: [backend/template.yaml](./backend/template.yaml)
- Commit guidelines: [.codex/git-flow/](./.codex/git-flow/)

## Project Structure

- Backend: [backend/](./backend) -> serverless backend with Lambda entrypoints, layered application code, AWS integrations, and local mock infrastructure
- Frontend: [frontend/](./frontend) -> React + TypeScript + Vite client
- Documentation: [docs/](./docs) -> architecture and supporting notes
- Utility scripts: [scripts/](./scripts) -> setup, local run, local test, and deploy helpers

Important backend paths:

- Lambda entrypoints: [backend/src/functions/lambda/](./backend/src/functions/lambda)
- Application layers: [backend/src/layers/main/nyx/](./backend/src/layers/main/nyx)
- Local in-memory infrastructure: [backend/src/layers/main/nyx/local/](./backend/src/layers/main/nyx/local)
- Infrastructure factory: [backend/src/layers/main/nyx/bootstrap/infrastructure_factory.py](./backend/src/layers/main/nyx/bootstrap/infrastructure_factory.py)
- Dependency container: [backend/src/layers/main/nyx/bootstrap/container.py](./backend/src/layers/main/nyx/bootstrap/container.py)

Important frontend paths:

- Pages: [frontend/src/pages/](./frontend/src/pages)
- Services: [frontend/src/services/](./frontend/src/services)
- Frontend crypto layer: [frontend/src/crypto/](./frontend/src/crypto)
- Auth context: [frontend/src/context/](./frontend/src/context)

## Local Development

The recommended local workflow is:

1. install dependencies
2. create local environment files
3. run the backend in `mock` mode
4. run the frontend against the local backend
5. validate login and conversation flows with seeded local data

### Quick setup

Setup script: [scripts/setup.sh](./scripts/setup.sh)

```bash
./scripts/setup.sh
```

This script:

- installs frontend dependencies
- creates `frontend/.env.local` from [frontend/.env.example](./frontend/.env.example) if needed
- creates a backend virtual environment
- installs backend runtime and dev dependencies
- creates `backend/env.local.json` from [backend/env.local.example.json](./backend/env.local.example.json) if needed

On Windows, run the shell scripts from Git Bash or WSL.

### Frontend local

From [frontend/](./frontend):

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Expected URL:

```text
http://localhost:5173
```

Default frontend environment:

- [frontend/.env.example](./frontend/.env.example)

The frontend is configured to call the local backend by default:

```bash
VITE_API_BASE_URL=http://127.0.0.1:3000
VITE_CONVERSATIONS_SOURCE=api
```

### Backend local

From [backend/](./backend):

```bash
cd backend
python -m venv .venv
```

PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .[dev]
```

Create the local SAM env file:

```bash
cp env.local.example.json env.local.json
```

Run the local backend:

```bash
sam build
sam local start-api --env-vars env.local.json
```

Expected URL:

```text
http://127.0.0.1:3000
```

The local backend uses:

- in-memory DAOs instead of DynamoDB
- an in-memory queue publisher instead of SQS
- an in-memory realtime notifier instead of API Gateway Management API

Relevant local infrastructure classes:

- [UserInMemoryDao](./backend/src/layers/main/nyx/dao/user_in_memory_dao.py)
- [ConversationInMemoryDao](./backend/src/layers/main/nyx/dao/conversation_in_memory_dao.py)
- [MessageInMemoryDao](./backend/src/layers/main/nyx/dao/message_in_memory_dao.py)
- [ConnectionInMemoryDao](./backend/src/layers/main/nyx/dao/connection_in_memory_dao.py)
- [InMemoryQueuePublisher](./backend/src/layers/main/nyx/gateways/in_memory_queue_publisher.py)
- [InMemoryRealtimeNotifier](./backend/src/layers/main/nyx/gateways/in_memory_realtime_notifier.py)

### Full local run

Run script: [scripts/run-local.sh](./scripts/run-local.sh)

```bash
./scripts/run-local.sh
```

This script:

- builds and starts the backend with SAM local
- forces the backend into local/mock infrastructure mode through [backend/env.local.example.json](./backend/env.local.example.json)
- starts the frontend dev server

### Local demo credentials

The local mock environment seeds demo data automatically through [local_data_seeder.py](./backend/src/layers/main/nyx/bootstrap/local_data_seeder.py).

Use these credentials for the local login flow:

```text
username: carlo@nyx.app
password: nyx-local-pass
```

What works locally without AWS:

- login
- conversation listing
- conversation creation
- message enqueue and in-memory processing
- pending message retrieval

## Local Testing Strategy

Nyx uses infrastructure swapping at the composition root. The business layer does not know whether it is using AWS resources or local in-memory implementations.

Selection is based on backend environment variables:

- `APP_ENV=local`
- `INFRA_MODE=mock`

The infrastructure decision is centralized in:

- [backend/src/layers/main/nyx/bootstrap/infrastructure_factory.py](./backend/src/layers/main/nyx/bootstrap/infrastructure_factory.py)
- [backend/src/layers/main/nyx/bootstrap/container.py](./backend/src/layers/main/nyx/bootstrap/container.py)

This gives the local workflow a few important properties:

- no DynamoDB dependency for basic local development
- no SQS dependency for basic local development
- no API Gateway realtime dependency for basic local development
- no AWS credentials required for the basic local backend flow
- the same BO and controller logic is exercised in both local and AWS modes

Honest limitation:

- local mode uses in-memory state, so data resets when the local backend process restarts
- `sam local start-api` covers the HTTP handlers, not a full local WebSocket server
- the frontend still does not include automated browser tests

## Environment Variables

### Backend

Backend configuration lives in:

- [backend/src/layers/main/nyx/config/settings.py](./backend/src/layers/main/nyx/config/settings.py)
- [backend/env.local.example.json](./backend/env.local.example.json)
- [backend/template.yaml](./backend/template.yaml)

Important backend variables:

```bash
APP_ENV=local
INFRA_MODE=mock
JWT_SECRET=change-me-local
JWT_EXP_MINUTES=60
LOG_LEVEL=DEBUG
AWS_REGION=us-east-1
```

Behavior:

- `APP_ENV=local` enables local development intent
- `INFRA_MODE=mock` selects in-memory infrastructure
- deployed AWS environments keep `APP_ENV=aws` and `INFRA_MODE=aws`

### Frontend

Frontend configuration lives in:

- [frontend/.env.example](./frontend/.env.example)
- [frontend/src/utils/env.ts](./frontend/src/utils/env.ts)

Important frontend variables:

```bash
VITE_API_BASE_URL=http://127.0.0.1:3000
VITE_CONVERSATIONS_SOURCE=api
```

## AWS Deployment

The AWS deployment path uses the real infrastructure defined in:

- [backend/template.yaml](./backend/template.yaml)

### AWS credentials

Configure credentials with:

```bash
aws configure
```

You will be asked for:

- AWS Access Key ID
- AWS Secret Access Key
- default region
- output format

If you use a profile:

```bash
aws configure --profile nyx
sam deploy --guided --profile nyx
```

### Backend deploy

```bash
cd backend
sam build
sam deploy --guided
```

After the first guided deploy:

```bash
cd backend
sam deploy
```

### Frontend deploy

```bash
cd frontend
npm install
npm run build
aws s3 sync dist/ s3://YOUR_BUCKET
```

### Deploy helper script

Deploy script: [scripts/deploy.sh](./scripts/deploy.sh)

```bash
./scripts/deploy.sh --guided
```

If `FRONTEND_BUCKET` is set, the script also uploads the frontend build to S3.

## Testing

### Local test script

Test script: [scripts/test-local.sh](./scripts/test-local.sh)

```bash
./scripts/test-local.sh
```

This script:

- runs backend tests in local/mock mode
- runs the frontend production build as the current validation step

### Manual test commands

Backend:

```bash
cd backend
APP_ENV=local INFRA_MODE=mock pytest
```

Frontend:

```bash
cd frontend
npm run build
```

There is currently no `npm test` script in [frontend/package.json](./frontend/package.json).

## Useful Links

- Backend directory: [backend/](./backend)
- Frontend directory: [frontend/](./frontend)
- Scripts directory: [scripts/](./scripts)
- Architecture documentation: [docs/architecture.md](./docs/architecture.md)
- Backend README: [backend/README.md](./backend/README.md)
- AWS SAM template: [backend/template.yaml](./backend/template.yaml)
- Commit rules: [.codex/git-flow/commit-rules.md](./.codex/git-flow/commit-rules.md)
