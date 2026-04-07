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
- [Master Password Model](#master-password-model)
- [Conversation Password Model](#conversation-password-model)
- [Logging And Observability](#logging-and-observability)
- [Security Review](#security-review)
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

## Master Password Model

Nyx now separates authentication from conversation decryption.

- The user chooses a master password during signup.
- The plaintext master password is handled only in the browser for the current operation.
- The browser derives a verifier from the master password with PBKDF2 and sends only that verifier and KDF metadata to the backend.
- The backend stores only:
  - `master_password_verifier`
  - `master_password_salt`
  - `master_password_kdf_params`
  - encrypted private key material and non-sensitive metadata
- During login, the browser first requests `/auth/challenge`, derives the same verifier locally, and sends an HMAC proof over the server challenge.
- The backend validates the proof without receiving the plaintext master password.

What the frontend keeps:

- JWT and non-sensitive crypto metadata in `localStorage`
- decrypted conversation keys only in in-memory React state after a conversation is unlocked

What the frontend does not keep:

- plaintext master password in `localStorage`
- plaintext master password in `sessionStorage`
- plaintext master password in the backend

## Conversation Password Model

Each conversation has its own separate password and its own KDF metadata.

Creation flow:

- The creator enters:
  - recipient username
  - master password
  - conversation password
- The browser validates the master password locally by attempting to decrypt the user private key wrapper.
- The browser derives a conversation message key from the conversation password and a per-conversation salt.
- The browser creates an encrypted unlock check blob from that key.
- The browser encrypts the conversation password with a key derived from the master password.
- The backend stores only:
  - encrypted conversation password blob per participant
  - conversation salt / KDF metadata
  - unlock check ciphertext / nonce
  - encrypted message payloads

Open flow:

- The user enters the master password.
- The browser validates it locally.
- The user enters the conversation password.
- The browser derives the conversation key, validates the unlock check, and only then decrypts messages.
- If the participant has not saved their wrapped conversation secret yet, the browser wraps it locally and uploads only the encrypted blob.

Important consequence:

- The backend never knows the plaintext conversation password.
- Messages stay encrypted in transit, in storage, and in the client until the chat is explicitly unlocked.

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

### 3. Deploy the backend

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-backend.ps1
```

Bash:

```bash
bash scripts/deploy-backend.sh
```

### 4. Deploy the frontend

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-frontend.ps1
```

Bash:

```bash
bash scripts/deploy-frontend.sh
```

The frontend deploy script tries to resolve the backend URL from the `nyx-main` CloudFormation stack. You can also override it by setting `VITE_API_BASE_URL` before running the script.

### 5. Test the deployed environment

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

### Deploy scripts

The deployment flow is now split so backend and frontend can be released independently. There is also a convenience script for full deploys.

Backend only:

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-backend.ps1
```

Bash:

```bash
bash scripts/deploy-backend.sh
```

Frontend only:

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-frontend.ps1
```

Bash:

```bash
bash scripts/deploy-frontend.sh
```

Full deploy:

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

The frontend deploy scripts create or reuse a frontend bucket and upload the frontend build to it. If `FRONTEND_BUCKET` is set, that exact bucket name is used. Otherwise the default name is `s3://nyx-frontend-<account-id>-<region>`.

High-level deploy flow:

- `deploy-backend`: build and deploy the backend with AWS SAM
- `deploy-frontend`: resolve `VITE_API_BASE_URL` from the current environment or from the `HttpApiUrl` output of the `nyx-main` stack, then build and upload `frontend/dist/`
- `deploy`: run backend deploy first, then frontend deploy

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
VITE_WEBSOCKET_URL=wss://your-websocket-id.execute-api.your-region.amazonaws.com/main
```

## Logging And Observability

Nyx uses structured JSON logs designed for CloudWatch Logs Insights and distributed tracing across HTTP, SQS, Lambda, WebSocket, and DynamoDB flows.

Logging strategy:

- all backend logs are emitted through the centralized utility in [backend/src/layers/main/nyx/utils/logger.py](./backend/src/layers/main/nyx/utils/logger.py)
- every request starts with a bound request context using `correlation_id` and `request_id`
- the same `correlation_id` is propagated into queued message payloads so the async processor can continue the same trace
- infrastructure components such as SQS publishers, WebSocket notifiers, and DynamoDB DAOs emit logs in the same JSON shape

Common log fields:

- `timestamp`
- `level`
- `service`
- `component`
- `message`
- `correlation_id`
- `request_id`
- `user_id` when available
- `conversation_id` when available
- `message_id` when available
- latency fields such as `duration_ms` for timed operations

Examples of logged operations:

- request start / completion in Lambda handlers
- user authentication attempts and outcomes
- queue publish start / success
- queue processing start / result
- WebSocket connection lifecycle
- delivery attempts to active connections
- DynamoDB write attempts / successes / failures

What is intentionally not logged:

- plaintext messages
- decrypted message content
- master passwords
- conversation passwords
- raw encryption keys
- wrapped or decrypted secrets
- JWT access tokens

Sensitive fields are sanitized before serialization, and unexpected exceptions include stack traces plus safe operational context so production debugging remains useful without exposing secrets.

## Security Review

Threat model:

- The backend is treated as honest-but-curious storage and transport.
- TLS is assumed for client-to-backend transport.
- An attacker who steals backend database contents should see encrypted message payloads, salted verifiers, wrapped conversation secrets, and crypto metadata, but not plaintext secrets.

What the backend can see:

- usernames and user ids
- conversation membership metadata
- encrypted private keys
- encrypted conversation-password wrappers
- encrypted messages
- salts, IVs, KDF parameters, and unlock-check metadata

What the backend cannot see:

- plaintext master password
- plaintext conversation password
- decrypted message content
- conversation keys derived in the browser

Why the master password is not persisted:

- it is the root secret that protects wrapped conversation secrets
- persisting it in browser storage would turn an XSS or local compromise into account-wide chat compromise
- Nyx only uses it long enough to derive local keys or proofs, then clears the corresponding form state

Why each conversation has its own secret:

- compromise of one conversation password does not automatically expose every other chat
- users can rotate or share a conversation secret independently of account login state
- message decryption is gated per conversation instead of globally after login

Security limitations and assumptions:

- login proof is challenge-based, but it still assumes HTTPS and trusted client code delivery
- decrypted conversation keys live in browser memory while a chat is unlocked
- existing deployed users created under the older password model need re-registration or migration to adopt the new verifier-based flow cleanly
- the current DynamoDB conversation listing still uses `Scan`, which is acceptable for MVP correctness but not ideal for scale

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

Equivalent helper scripts:

- backend only: `.\scripts\deploy-backend.ps1` or `bash scripts/deploy-backend.sh`
- frontend only: `.\scripts\deploy-frontend.ps1` or `bash scripts/deploy-frontend.sh`
- full deploy: `.\scripts\deploy.ps1` or `bash scripts/deploy.sh`

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
