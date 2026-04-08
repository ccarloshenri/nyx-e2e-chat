# Nyx - End-to-End Encrypted Chat

Nyx is a secure real-time chat platform with a Python serverless backend and a React frontend. Message encryption and decryption happen only on the client. The backend only validates, stores, and forwards encrypted payloads.

## Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Frontend Local Testing](#frontend-local-testing)
- [Load Testing](#load-testing)
- [Deployment Workflow](#deployment-workflow)
- [Environment Variables](#environment-variables)
- [How Conversations Work](#how-conversations-work)
- [Master Password Model](#master-password-model)
- [Conversation Password Model](#conversation-password-model)
- [Detailed Encryption Flow](#detailed-encryption-flow)
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

## How Conversations Work

This is the current product behavior in practical terms.

### What each user must know

To start a conversation successfully, the creator must know:

- the exact username of the other participant as it exists in the system
- their own master password
- the conversation password they want to use for that chat

To open and read that conversation, the other participant must know:

- their own master password
- the same conversation password chosen for that chat

Important:

- the application does not currently negotiate or exchange the conversation password for users
- the conversation password must be shared outside the app, by some separate trusted channel
- if the username is typed incorrectly, the conversation creation request fails because the backend looks up the other participant by exact username
- both participants must use the same conversation password for the same chat, otherwise they will not be able to derive the same conversation key and messages will not decrypt

### What happens when a chat is created

When user `alice` creates a chat with user `bob`:

1. `alice` types `bob`'s exact username.
2. `alice` enters her master password.
3. `alice` defines a conversation password for that specific chat.
4. The browser verifies `alice`'s master password locally.
5. The browser derives a conversation key from the conversation password.
6. The browser sends the backend only encrypted conversation metadata and encrypted message payloads.
7. The backend stores a conversation record containing both participants, but not the plaintext conversation password.

At this moment, `bob` is recognized as a participant by the backend, but `bob` still cannot read messages until he opens the chat with the same conversation password.

### What happens when the other participant opens the chat

When `bob` later opens the same conversation:

1. `bob` logs in with his own account.
2. `bob` selects the conversation.
3. `bob` enters his own master password.
4. `bob` enters the same conversation password that `alice` used when creating the chat.
5. The browser derives the same conversation key locally.
6. If the derived key matches the stored unlock check, the browser can decrypt the messages.

If `bob` enters a different conversation password, the conversation remains locked because the derived key does not match the encrypted data for that chat.

### What the backend knows and does not know

The backend knows:

- who the participants are
- each participant's username and user id
- encrypted conversation metadata
- encrypted message payloads
- which authenticated user is allowed to access which conversation

The backend does not know:

- any user's plaintext master password
- the plaintext conversation password
- the decrypted message content
- the derived conversation key used to decrypt messages

### Current UX limitations to be aware of

The current implementation is intentionally simple and has a few important product constraints:

- conversation creation depends on knowing the exact username of the other person
- conversation access depends on both users sharing the same conversation password beforehand
- there is no in-app password handoff, invite acceptance flow, or automatic key exchange yet
- there is no password recovery flow for conversation passwords
- if the shared conversation password is lost, the encrypted messages for that conversation cannot be opened
- if a user chooses the wrong username when creating a chat, the conversation will target the wrong account or fail if the username does not exist
- this model works for an MVP, but it is more manual than consumer chat apps because the shared secret is part of the security design

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

## Detailed Encryption Flow

This section describes the current end-to-end flow more precisely.

### 1. Account registration

During signup:

1. The user chooses a username and a master password.
2. The browser derives a verifier from the master password using PBKDF2.
3. The browser generates and protects the user's local cryptographic material.
4. The browser sends the backend:
   - `username`
   - `master_password_verifier`
   - `master_password_salt`
   - `master_password_kdf_params`
   - encrypted private-key material and related wrapping metadata
5. The backend stores the verifier and encrypted blobs, but not the plaintext master password.

Result:

- the master password becomes the root secret for that user's protected local material
- the backend can later verify login proofs without ever receiving the plaintext password

### 2. Login and JWT issuance

During login:

1. The browser calls `/auth/challenge` with the username.
2. The backend returns a short-lived challenge token plus the stored KDF metadata needed to derive the verifier again in the browser.
3. The browser derives the verifier locally from the typed master password.
4. The browser computes a proof over the server challenge.
5. The browser sends `username`, `challenge_token`, and `login_proof` to `/auth/login`.
6. The backend validates that proof.
7. If validation succeeds, the backend returns a JWT and non-sensitive user crypto metadata.

Important consequence:

- authentication is separate from conversation decryption
- having a valid JWT means the user is authenticated to the backend
- having a valid JWT does not mean the browser can automatically decrypt any conversation

### 3. Conversation creation

When a user creates a conversation:

1. The creator types the other participant's exact username.
2. The backend resolves that username to a real account.
3. The creator enters their master password.
4. The creator chooses a conversation password for that chat.
5. The browser validates the creator's master password locally.
6. The browser derives a conversation message key from:
   - the conversation password
   - a per-conversation salt
   - per-conversation KDF parameters
7. The browser creates an `unlock_check` encrypted with that derived key.
8. The browser encrypts the conversation password with a key derived from the creator's master password.
9. The browser sends the backend:
   - the other participant username
   - the conversation salt
   - the conversation KDF metadata
   - the unlock check ciphertext and nonce
   - the creator's wrapped conversation-password blob
10. The backend stores the conversation and marks both users as participants.

Important consequence:

- the backend can authorize access to the conversation by participant id
- the backend still cannot decrypt the conversation because it never receives the plaintext conversation password

### 4. Conversation opening

When a participant opens a conversation:

1. The browser fetches the encrypted conversation metadata and encrypted messages for that conversation.
2. The user enters their master password.
3. The browser validates the master password locally.
4. The user enters the conversation password.
5. The browser derives the conversation key locally from the conversation password plus the stored salt/KDF metadata.
6. The browser validates the `unlock_check`.
7. If validation succeeds, the browser decrypts the messages locally.
8. If that participant does not yet have a saved wrapped conversation secret, the browser wraps the conversation password locally and uploads only the encrypted wrapper for future use.

If the conversation password is wrong:

- the derived key does not match the unlock check
- the conversation stays locked
- the backend still does not learn what the user typed

### 5. Message encryption and delivery

When a user sends a message:

1. The browser first derives or reuses the unlocked conversation key locally.
2. The browser encrypts the plaintext message locally.
3. The browser sends only encrypted payload fields to the backend.
4. The backend validates the JWT, validates the sender identity, and verifies that the sender belongs to that conversation.
5. The backend stores the encrypted message and forwards it through the realtime/queue pipeline.
6. The recipient browser receives encrypted message data.
7. The recipient browser can only read the message after deriving the same conversation key locally.

This means the backend is responsible for:

- authentication
- authorization
- persistence
- delivery

But the browser is responsible for:

- deriving keys
- encrypting plaintext
- decrypting ciphertext
- validating passwords locally

### 6. Why both participants need the same conversation password

This is the most important product rule in the current implementation.

The message encryption key for a conversation is derived from the conversation password and that conversation's salt/KDF settings. Because of that:

- if two users type the same conversation password for the same conversation, they derive the same key
- if they derive the same key, they can encrypt and decrypt the same message history
- if they type different conversation passwords, they derive different keys
- if they derive different keys, decryption fails

So, in the current system, the shared conversation password is effectively the shared secret that makes end-to-end decryption possible for that chat.

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

## Load Testing

The repository includes a dedicated bomber for backend load testing in [backend/bomber/](./backend/bomber).

What it can do:

- create or reuse synthetic users
- authenticate them against the real API
- create conversations between those users
- stress test the `POST /messages` endpoint with concurrent async requests

Quick example:

```powershell
backend\.venv\Scripts\python backend\bomber\main.py --base-url https://your-api-id.execute-api.us-east-1.amazonaws.com/main --users-file backend\bomber\users.seed.json --skip-register --requests 1000 --concurrency 100 --warmup 50
```

See [backend/bomber/README.md](./backend/bomber/README.md) for the available options and usage notes.

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
