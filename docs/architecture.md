# Nyx Monorepo Architecture

## Root layout

```text
/backend
/frontend
/docs
README.md
```

## Backend

- Python backend for Lambda, API Gateway WebSocket, SQS and DynamoDB.
- Source code lives in `backend/src`.
- Lambda entrypoints live in `backend/src/functions/lambda`.
- Infrastructure contracts and concrete implementations live in `backend/src/layers/main/nyx`.

## Frontend

- React + TypeScript + Vite application.
- Source code lives in `frontend/src`.
- Authentication flow is handled by `AuthContext`.
- API communication is centralized in `frontend/src/services`.
- Conversations currently use an isolated mock service and are ready to switch to the backend endpoint later.

## Future direction

- Keep frontend cryptography client-side under `frontend/src/crypto`.
- Extend backend with conversation listing and richer realtime delivery.
- Add IaC and deployment docs under `docs`.
