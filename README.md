# Nyx - End-to-End Encrypted Chat

Backend and frontend for a secure real-time chat system built around end-to-end encryption, AWS serverless architecture, and a React client. The server transports and persists encrypted payloads, but it does not decrypt message content.

## Quick Start

### Backend local

#### Prerequisites

- Python 3.12+
- `pip`
- AWS CLI
- AWS credentials configured locally

#### Install

```bash
cd backend
pip install -r requirements.txt
```

#### Optional development dependencies

```bash
pip install -e .[dev]
```

#### Run locally

The backend is organized for AWS Lambda handlers, but this repository does not currently include a committed SAM template, CDK app, or Terraform stack for full local emulation with `sam local start-api`.

What you can do locally right now:

```bash
cd backend
pytest
```

If you want full local Lambda/API emulation, the next step is to add infrastructure-as-code for the deployed resources and bind the handlers under `backend/src/functions/lambda`.

### Frontend local

#### Prerequisites

- Node.js 18+
- `npm`

#### Install

```bash
cd frontend
npm install
```

#### Configure environment

Create a local env file:

```bash
cp .env.example .env.local
```

Set at least:

```bash
VITE_API_BASE_URL=http://localhost:3000
VITE_CONVERSATIONS_SOURCE=mock
```

#### Run locally

```bash
cd frontend
npm run dev
```

The frontend runs on:

```text
http://localhost:5173
```

## Frontend Build

Generate a production build with:

```bash
cd frontend
npm run build
```

This produces the static output in:

```text
frontend/dist/
```

## Frontend Deploy to S3

Build first:

```bash
cd frontend
npm run build
```

Then upload to your S3 bucket:

```bash
aws s3 sync dist/ s3://SEU_BUCKET
```

Recommended production setup:

- Host the static files in an S3 bucket
- Put CloudFront in front of the bucket
- Use HTTPS and custom domain configuration through CloudFront
- Keep the bucket private when using CloudFront with origin access control

If you are using S3 static website hosting directly, configure the bucket for static website hosting and ensure the correct read policy is applied.

## Backend Deploy

The backend code is ready for Lambda deployment, but this repository does not currently include a committed SAM template or other deployment manifest.

Current practical deployment options:

1. Deploy the handlers manually through your existing AWS infrastructure setup.
2. Add AWS SAM, CDK, or Terraform to provision Lambda, API Gateway WebSocket, SQS, and DynamoDB.

If you choose to add AWS SAM, the expected workflow will look like this:

```bash
cd backend
sam build
sam deploy --guided
```

Important:

- The commands above require a valid `template.yaml`, which is not currently present in the repository.
- Lambda handlers live under `backend/src/functions/lambda`.

## AWS Configuration

Configure your AWS credentials locally with:

```bash
aws configure
```

You will be asked for:

- AWS Access Key ID
- AWS Secret Access Key
- Default region name
- Default output format

Example:

```text
AWS Access Key ID [None]: AKIA...
AWS Secret Access Key [None]: ...
Default region name [None]: us-east-1
Default output format [None]: json
```

## Environment Variables

### Backend

Configure backend environment variables in your Lambda environment or local shell.

Main variables:

```bash
AWS_REGION=us-east-1
USERS_TABLE_NAME=nyx-users
CONNECTIONS_TABLE_NAME=nyx-connections
CONVERSATIONS_TABLE_NAME=nyx-conversations
MESSAGES_TABLE_NAME=nyx-messages
MESSAGE_DELIVERY_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/nyx.fifo
WEBSOCKET_MANAGEMENT_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
JWT_SECRET=change-this
JWT_EXP_MINUTES=60
LOG_LEVEL=INFO
```

Where to set them:

- Local shell session
- CI/CD secrets
- Lambda environment variables
- `.env` files for local development when needed

### Frontend

Configure frontend variables in:

- `frontend/.env`
- `frontend/.env.local`

Main variable:

```bash
VITE_API_BASE_URL=http://localhost:3000
```

Optional variable for conversations source:

```bash
VITE_CONVERSATIONS_SOURCE=mock
```

Use `mock` while the backend conversation listing endpoint is not available. Switch to `api` once that endpoint exists.

## Project Structure

```text
/backend   -> serverless backend in Python (Lambda, SQS, DynamoDB, JWT, WebSocket)
/frontend  -> React + TypeScript application
/docs      -> supporting documentation
```

Backend structure highlights:

```text
backend/src/functions/lambda  -> Lambda entrypoints
backend/src/controllers       -> request orchestration
backend/src/bo                -> business rules
backend/src/layers/main/nyx   -> interfaces, concrete infra, bootstrap
backend/src/models            -> domain models
backend/src/validators        -> jsonschema validation
```

Frontend structure highlights:

```text
frontend/src/pages           -> route-level pages
frontend/src/components      -> reusable UI and layout
frontend/src/services        -> API, auth, conversations, crypto
frontend/src/context         -> auth state
frontend/src/router          -> routes and protection
```

## System Flow

### Login

1. The frontend sends username and password to the backend login endpoint.
2. The backend validates credentials and returns a JWT plus encrypted key material metadata.
3. The frontend stores the token and opens the protected area.

### Send message

1. The client prepares encrypted message payloads.
2. The backend validates the request and publishes the encrypted payload to the queue.
3. A background processor persists the encrypted message and attempts real-time delivery.

### Queue processing

1. The message processor consumes queued payloads.
2. The backend applies idempotency checks.
3. The encrypted message is stored and marked with delivery state.

### WebSocket delivery

1. Active recipient connections are resolved.
2. Encrypted payloads are pushed over WebSocket when possible.
3. Offline messages remain pending until the user reconnects.

## Important Notes

- The backend never decrypts message content.
- End-to-end encryption is intended to happen on the client side.
- The frontend already includes a dedicated crypto service area for future client-side key generation and local encryption logic.
- This project emphasizes architecture, security boundaries, clean layering, and testability.
- Conversation listing on the frontend is currently backed by an isolated mock service unless `VITE_CONVERSATIONS_SOURCE=api`.

## Testing

### Backend

```bash
cd backend
pytest
```

### Frontend

The frontend project is scaffolded and ready for additional test tooling, but automated frontend tests are not configured yet in this repository.

## Documentation

Additional notes:

- `docs/architecture.md`
- `backend/README.md`
