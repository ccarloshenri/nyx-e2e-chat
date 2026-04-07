# Nyx E2EE Chat Backend

Python backend for a secure real-time chat application built on AWS Lambda, API Gateway WebSocket, SQS, DynamoDB, and JWT. The project follows a layered architecture and keeps one core security rule explicit: the server never decrypts messages. It only receives, stores, and routes end-to-end encrypted payloads.

## Architecture

```text
src/
  functions/lambda/ # Minimal Lambda entrypoints, one function per folder
  layers/main/nyx/
    controllers/ # Application entrypoints; translate Lambda/API Gateway events into use cases
    bo/          # Business rules and orchestration across contracts
    models/      # Entities and DTOs
    enums/       # Domain enums
    validators/  # jsonschema definitions and centralized validation
    aws/         # AWS-specific adapters and implementations
    utils/       # Logging, responses, parsing, serializers, and helpers
    config/      # Settings and constants
    interfaces/
      dao/       # Persistence contracts
      infrastructure/ # Central infrastructure contract
      messaging/ # Messaging contracts
      realtime/  # Realtime notification contracts
      services/  # Technical service contracts
    dao/         # Concrete DynamoDB implementations
    gateways/    # Concrete SQS and WebSocket implementations
    infrastructure/ # Concrete AWS infrastructure implementation
    services/    # JWT, hashing, clock, and ID generator services
tests/
  unit/          # Layered unit tests
```

Responsibilities:

- `controllers`: receive raw events, parse input, validate payloads, authenticate users, and invoke the business layer.
- `bo`: concentrate business rules for authentication, connections, conversations, and messages while depending only on abstractions.
- `layers/main/nyx/interfaces`: define explicit capability-based contracts without coupling to a concrete technology.
- `layers/main/nyx/interfaces/infrastructure`: defines the central `IInfrastructure` contract.
- `layers/main/nyx/aws/dao` and `layers/main/nyx/aws/gateways`: encapsulate DynamoDB, SQS, and the API Gateway Management API.
- `layers/main/nyx/aws/infrastructure`: contains `AwsInfrastructure`, responsible for providing concrete AWS DAOs and gateways without spreading imports across Lambda handlers.
- `validators`: centralize `jsonschema` validation and standardized errors.
- `functions/lambda`: contain only minimal Lambda entrypoints.
- `layers/main/nyx`: holds the reusable application logic, infrastructure adapters, and system rules.

Applied patterns:

- Domain categorical values use `Enum`, such as `MessageStatus` and `WebSocketAction`.
- Models are intentionally anemic: attributes only, without `to_dict`, `from_dict`, or infrastructure-specific behavior.
- DynamoDB conversion happens only inside concrete DAO converters.
- Lambda handlers use a decorator for standardized error handling and request context binding.
- Business rules depend on interfaces such as `IUserDao`, `IMessageDao`, `IQueuePublisher`, `IWebSocketNotifier`, `IJwtService`, `IClock`, and `IIdGenerator`.
- `boto3` appears only in concrete tables, DAOs, and gateways that actually need it.
- Interfaces use `ABC` and `@abstractmethod` with explicit and consistent contracts across the project.
- Handlers instantiate a single `AwsInfrastructure` typed as `IInfrastructure` and reuse it to obtain DAOs and gateways.
- `AwsInfrastructure` does not create shared AWS clients centrally; each DAO or gateway creates the AWS resource it needs.
- The project intentionally avoids `Protocol` and `from __future__ import annotations`.

## System Flow

### Registration and Login

1. The client sends `username`, `master_password_verifier`, salts/KDF params, and encrypted user crypto material.
2. The backend stores only the derived verifier, never the plaintext master password.
3. During login, the client requests a challenge at `/auth/challenge`.
4. The client derives the verifier locally and sends only `challenge_token` plus `login_proof`.
5. The backend validates the proof without seeing the master password and returns a JWT with the metadata required for the client to unlock local secrets.

### Per-Conversation Secret

1. Each conversation has its own password, its own salt/KDF metadata, and an encrypted `unlock_check`.
2. The client encrypts the conversation password with a key derived from the master password.
3. The backend stores only:
   - `participant_access` entries with `encrypted_conversation_password`
   - conversation salt and KDF metadata
   - `unlock_check`
   - encrypted messages
4. A conversation is only opened in the frontend after:
   - the master password is validated locally
   - the conversation password is validated locally
   - the frontend derives the conversation key and successfully decrypts the `unlock_check`

### WebSocket

1. The `connect/app.py` handler validates the JWT during the handshake.
2. The backend associates the `connectionId` with the user and stores the active connection with a TTL.
3. The `src/functions/lambda/disconnect/app.py` handler removes the active connection.

### Messages

1. The client sends an already encrypted payload.
2. The `send_message/app.py` handler validates the schema, verifies the authenticated sender, and publishes the message to SQS.
3. The `process_message/app.py` handler applies `message_id` idempotency, stores the encrypted message, and attempts fan-out through the API Gateway Management API.
4. If the recipient is offline, the message remains pending.
5. The client can fetch pending messages and later send an ACK.

## Security

- The backend never reads plaintext content.
- `ciphertext`, `encrypted_message_key`, `encrypted_private_key`, and `encrypted_conversation_password` are treated only as opaque blobs.
- Authentication uses a derived verifier with `PBKDF2-HMAC-SHA256` plus a challenge-based proof.
- JWT tokens expire.
- Structured logs sanitize passwords, tokens, keys, and ciphertext.
- Error responses are standardized and do not expose sensitive material.

## Suggested DynamoDB Modeling

- `users`
  - PK: `user_id`
  - GSI: `username-index` with PK `username`
- `connections`
  - PK: `user_id`
  - SK: `connection_id`
  - GSI: `connection-id-index` with PK `connection_id`
- `conversations`
  - PK: `conversation_id`
- `messages`
  - PK: `conversation_id`
  - SK: `message_id`
  - GSI: `recipient-status-index` with PK `recipient_id`

For production, the message index should evolve toward a composite key that includes status and time to support more selective offline fetches.

## Handlers

- `src/functions/lambda/register_user/app.py`
- `src/functions/lambda/login/app.py`
- `src/functions/lambda/create_login_challenge/app.py`
- `src/functions/lambda/fetch_public_key/app.py`
- `src/functions/lambda/create_conversation/app.py`
- `src/functions/lambda/get_conversation_access/app.py`
- `src/functions/lambda/save_conversation_access/app.py`
- `src/functions/lambda/list_conversation_messages/app.py`
- `src/functions/lambda/connect/app.py`
- `src/functions/lambda/disconnect/app.py`
- `src/functions/lambda/send_message/app.py`
- `src/functions/lambda/ack_message/app.py`
- `src/functions/lambda/fetch_pending_messages/app.py`
- `src/functions/lambda/process_message/app.py`

Each `app.py` wires the concrete dependencies it needs explicitly, without a central container.

## How to Run

1. Create a virtual environment with Python 3.12+.
2. Install dependencies:

```bash
pip install -e .[dev]
```

3. Configure environment variables:

```bash
JWT_SECRET=change-this
AWS_REGION=us-east-1
USERS_TABLE_NAME=nyx-users
CONNECTIONS_TABLE_NAME=nyx-connections
CONVERSATIONS_TABLE_NAME=nyx-conversations
MESSAGES_TABLE_NAME=nyx-messages
MESSAGE_DELIVERY_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/nyx.fifo
WEBSOCKET_MANAGEMENT_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

4. Run the tests:

```bash
pytest
```

## MVP Limitations

- It does not yet include a separate infrastructure-as-code alternative beyond the current SAM template.
- There is still no refresh token flow, key rotation, or JWT revocation.
- Conversation authorization can be expanded with finer-grained policies.
- Expired connection handling can be improved with reactive cleanup and stronger DLQ workflows.

## Future Work

- Add AWS CDK or Terraform support.
- Expand tests with `moto` for DynamoDB and SQS integration scenarios.
- Add metrics, tracing, and dashboards.
- Implement paginated conversation reads.
- Introduce retention and archival policies.
