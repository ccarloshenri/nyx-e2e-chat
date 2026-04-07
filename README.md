# Nyx - End-to-End Encrypted Chat

Nyx is a secure real-time chat platform with a Python serverless backend and a React frontend. Message encryption and decryption happen only on the client. The backend only validates, stores, and forwards encrypted payloads.

## Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Frontend Local Testing](#frontend-local-testing)
- [Deployment Workflow](#deployment-workflow)
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

The frontend is responsible for end-to-end encryption. The backend never decrypts message content.

## Tech Stack

- Frontend: React + TypeScript + Vite
- Backend: Python 3.12+ with AWS SAM
- Infrastructure: API Gateway, Lambda, DynamoDB, SQS
- Tooling: npm, pytest, AWS CLI, AWS SAM CLI

## Project Structure

- [backend/](./backend) -> serverless backend with Lambda entrypoints, layered application code, and AWS integrations
- [frontend/](./frontend) -> React + TypeScript + Vite client
- [docs/](./docs) -> architecture and supporting notes
- [scripts/](./scripts) -> setup and deploy helpers

Important backend paths:

- [backend/src/functions/lambda/](./backend/src/functions/lambda) -> Lambda entrypoints
- [backend/src/layers/main/nyx/](./backend/src/layers/main/nyx) -> application layers
- [backend/src/functions/lambda/login/app.py](./backend/src/functions/lambda/login/app.py) -> example handler wiring

Important frontend paths:

- [frontend/src/pages/](./frontend/src/pages) -> pages
- [frontend/src/services/](./frontend/src/services) -> service layer
- [frontend/src/crypto/](./frontend/src/crypto) -> encryption and decryption logic
- [frontend/src/context/](./frontend/src/context) -> auth and app state context

## Prerequisites

Install these tools before running setup or deployment scripts:

- Node.js 20+ with `npm`
- Python 3.12+
- AWS CLI
- AWS SAM CLI

### Windows

Using `winget`:

```powershell
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.12
winget install Amazon.AWSCLI
winget install Amazon.SAM-CLI
```

Verify the installation:

```powershell
node --version
npm --version
python --version
aws --version
sam --version
```

If `python` still opens the Microsoft Store alias, close the terminal and open a new PowerShell window.

### macOS

Using Homebrew:

```bash
brew install node@20 python@3.12 awscli aws-sam-cli
```

Verify the installation:

```bash
node --version
npm --version
python3 --version
aws --version
sam --version
```

### Linux

Install Node.js, Python, AWS CLI, and AWS SAM CLI with your distro package manager or the official installers.

Ubuntu/Debian example:

```bash
sudo apt update
sudo apt install -y nodejs npm python3 python3-venv python3-pip awscli
sam --version
```

If your distro does not provide Python 3.12+ or a recent enough Node.js version, use the official installers:

- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/
- AWS CLI: https://docs.aws.amazon.com/cli/
- AWS SAM CLI: https://docs.aws.amazon.com/serverless-application-model/

## Quick Start

### 1. Install project dependencies

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Bash:

```bash
./scripts/setup.sh
```

What this does:

- installs frontend dependencies
- creates `frontend/.env.local` from `frontend/.env.example` if needed
- creates `backend/.venv`
- installs backend runtime and development dependencies

### 2. Configure AWS credentials

```powershell
aws configure
```

You will be asked for:

- AWS Access Key ID
- AWS Secret Access Key
- default region
- output format

### 3. Deploy the main stack

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
```

Bash:

```bash
bash scripts/deploy.sh
```

### 4. Test the deployed environment

After deployment:

- use the `HttpApiUrl` output from [backend/template.yaml](./backend/template.yaml) to test backend endpoints
- open the deployed frontend in the S3 bucket or hosting target used by the deploy script
- if you want to test the UI locally against the deployed backend, set `VITE_API_BASE_URL` to the deployed `/main` API URL and run the frontend locally

## Frontend Local Testing

Use this flow when you only want to run and validate the frontend locally.

### 1. Install frontend dependencies

```powershell
cd frontend
npm install
```

### 2. Point the frontend to the backend you want to use

For local UI work without backend integration, keep the default values from [frontend/.env.example](./frontend/.env.example).

To test the frontend against the deployed backend, create or update `frontend/.env.local` with:

```text
VITE_API_BASE_URL=https://your-api-id.execute-api.your-region.amazonaws.com/main
VITE_CONVERSATIONS_SOURCE=api
```

### 3. Start the frontend locally

```powershell
cd frontend
npm run dev
```

Then open the local URL shown by Vite, usually `http://localhost:5173`.

### 4. Optional production-like check

```powershell
cd frontend
npm run build
npm run preview
```

Use `npm run preview` when you want to validate the generated production build locally before deploying.

## Deployment Workflow

### Setup script

Use the setup script when cloning the repository for the first time or when dependencies change.

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Bash:

```bash
./scripts/setup.sh
```

### Deploy script

The deploy script always deploys the single main stack, then builds and uploads the frontend with the deployed backend URL when available.

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
```

Bash:

```bash
bash scripts/deploy.sh
```

The fixed deployment targets are:

- stack name: `nyx-main`
- API stage: `main`
- default tables and queues: `nyx-users`, `nyx-connections`, `nyx-conversations`, `nyx-messages`, `nyx-message-delivery.fifo`, `nyx-message-delivery-dlq.fifo`

The deploy scripts create or reuse a frontend bucket and upload the frontend build to it. If `FRONTEND_BUCKET` is set, that exact bucket name is used. Otherwise the default name is `s3://nyx-frontend-<account-id>-<region>`.

High-level deploy flow:

- build and deploy the backend with AWS SAM
- resolve the `HttpApiUrl` output from the `nyx-main` stack
- build the frontend with `VITE_API_BASE_URL` pointing to that deployed API
- upload `frontend/dist/` to the configured S3 bucket

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
VITE_API_BASE_URL=https://your-api-id.execute-api.your-region.amazonaws.com/main
```

## AWS Deployment

The AWS infrastructure is defined in [backend/template.yaml](./backend/template.yaml).

### Using an AWS profile

```powershell
aws configure --profile nyx
sam deploy --guided --profile nyx
```

### Manual deploy

Backend:

```powershell
cd backend
sam build
sam deploy --stack-name nyx-main --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides StageName=main UsersTableName=nyx-users ConnectionsTableName=nyx-connections ConversationsTableName=nyx-conversations MessagesTableName=nyx-messages MessageQueueName=nyx-message-delivery.fifo MessageDlqName=nyx-message-delivery-dlq.fifo
```

Frontend:

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL="https://your-api-id.execute-api.your-region.amazonaws.com/main"
npm run build
aws s3 sync dist/ s3://YOUR_BUCKET
```

### How to validate after deploy

- confirm the CloudFormation stack `nyx-main` finished successfully
- verify the `HttpApiUrl` output answers requests under the `/main` stage
- open the deployed frontend and test login, registration, conversations, and message flows
- if needed, run the frontend locally with `npm run dev` against the deployed `VITE_API_BASE_URL`

## Useful Links

- [backend/](./backend)
- [frontend/](./frontend)
- [docs/architecture.md](./docs/architecture.md)
- [backend/README.md](./backend/README.md)
- [backend/template.yaml](./backend/template.yaml)
