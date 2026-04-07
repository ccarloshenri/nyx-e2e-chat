# Nyx E2EE Chat Backend

Backend em Python para chat seguro em tempo real usando AWS Lambda, API Gateway WebSocket, SQS, DynamoDB e JWT. O projeto segue arquitetura em camadas e deixa explicito um principio central: o servidor nunca descriptografa mensagens, apenas recebe, persiste e encaminha payloads criptografados ponta a ponta.

## Arquitetura

```text
src/
  functions/lambda/ # Entrypoints Lambda minimos, uma funcao por pasta
  layers/main/nyx/
    controllers/ # Entrada da aplicacao; traduz eventos Lambda/API Gateway para casos de uso
    bo/          # Regras de negocio e orquestracao entre contratos
    models/      # Entidades e DTOs
    enums/       # Enumeracoes de dominio
    validators/  # Schemas jsonschema e validador centralizado
    aws/         # Adaptadores e implementacoes especificas da AWS
    utils/       # logging, responses, parsing, serializers e helpers
    config/      # Settings e constantes
    interfaces/
      dao/       # Contratos de persistencia
      infrastructure/ # Contrato central de infraestrutura
      messaging/ # Contratos de mensageria
      realtime/  # Contratos de notificacao em tempo real
      services/  # Contratos de servicos tecnicos
    dao/         # Implementacoes concretas DynamoDB
    gateways/    # Implementacoes concretas SQS e WebSocket
    infrastructure/ # Implementacao concreta de infraestrutura AWS
    services/    # JWT, hash, clock, id generator
tests/
  unit/          # Testes por camada
```

Responsabilidades:

- `controllers`: recebem evento bruto, fazem parsing, validam payload, autenticam e chamam BO.
- `bo`: concentram regra de negocio de autenticacao, conexoes, conversas e mensagens e dependem apenas de abstracoes.
- `layers/main/nyx/interfaces`: definem contratos explicitos por capacidade de dominio, sem citar tecnologia.
- `layers/main/nyx/interfaces/infrastructure`: define o contrato central `IInfrastructure`.
- `layers/main/nyx/aws/dao` e `layers/main/nyx/aws/gateways`: encapsulam DynamoDB, SQS e API Gateway Management API.
- `layers/main/nyx/aws/infrastructure`: concentra `AwsInfrastructure`, responsavel por entregar DAOs e gateways AWS concretos sem espalhar imports pela Lambda.
- `validators`: centralizam `jsonschema` e erros padronizados.
- `functions/lambda`: contem apenas entrypoints minimos por Lambda.
- `layers/main/nyx`: contem toda a logica reutilizavel, infraestrutura e regras do sistema.

Padroes aplicados:

- Valores categoricos de dominio usam `Enum`, como `MessageStatus` e `WebSocketAction`.
- Models sao anemicos: apenas atributos, sem `to_dict`, `from_dict` ou qualquer logica de infraestrutura.
- Conversao para DynamoDB acontece somente nos converters da camada DAO concreta.
- Handlers Lambda usam decorator `@handler` para tratamento padronizado de erros e contexto.
- Regras de negocio dependem de interfaces como `IUserDao`, `IMessageDao`, `IQueuePublisher`, `IWebSocketNotifier`, `IJwtService`, `IClock` e `IIdGenerator`.
- `boto3` existe somente nas tables, DAOs e gateways concretos que realmente precisam dele.
- Interfaces usam `ABC` e `@abstractmethod`, com contratos explicitos e consistentes em todo o projeto.
- Os handlers instanciam uma unica infraestrutura `AwsInfrastructure` tipada como `IInfrastructure` e reutilizam essa instancia para obter DAOs e gateways.
- `AwsInfrastructure` nao cria clients AWS; ele apenas entrega implementacoes concretas, e cada DAO/gateway instancia o recurso AWS que precisa.
- O projeto nao usa `Protocol` nem `from __future__ import annotations`.

## Fluxo do sistema

### Cadastro e login

1. O cliente envia `username`, `master_password_verifier`, salts/KDF params e o material criptografico do usuario.
2. O backend persiste apenas o verificador derivado, nunca a master password em plaintext.
3. No login, o cliente pede um challenge em `/auth/challenge`.
4. O cliente deriva o verificador localmente e envia apenas `challenge_token` + `login_proof`.
5. O backend valida a prova sem ver a master password e retorna JWT com o metadata necessario para o cliente destravar segredos locais.

### Segredo por conversa

1. Cada conversa possui sua propria password, seu proprio salt/KDF e um `unlock_check` cifrado.
2. O cliente cifra a conversation password com uma chave derivada da master password.
3. O backend armazena apenas:
   - `participant_access` com `encrypted_conversation_password`
   - salt e KDF da conversa
   - `unlock_check`
   - mensagens cifradas
4. A conversa so e aberta no frontend depois que:
   - a master password e validada localmente
   - a conversation password e validada localmente
   - o frontend deriva a chave da conversa e consegue descriptografar o `unlock_check`

### WebSocket

1. O handler `connect/app.py` valida JWT durante o handshake.
2. O backend associa `connectionId` ao usuario e salva a conexao ativa com TTL.
3. O handler `src/functions/lambda/disconnect/app.py` remove a conexao ativa.

### Mensagens

1. O cliente envia payload ja criptografado.
2. O handler `send_message/app.py` valida o schema, verifica o emissor autenticado e publica no SQS.
3. O handler `process_message/app.py` aplica idempotencia por `message_id`, persiste a mensagem cifrada e tenta fan-out via API Gateway Management API.
4. Se o destinatario estiver offline, a mensagem fica pendente.
5. O cliente pode buscar mensagens pendentes e depois enviar ACK.

## Seguranca

- O backend nunca le plaintext.
- `ciphertext`, `encrypted_message_key`, `encrypted_private_key` e `encrypted_conversation_password` sao tratados apenas como dados opacos.
- A autenticacao usa verifier derivado com `PBKDF2-HMAC-SHA256` e challenge-based proof.
- JWT possui expiracao.
- Logs estruturados sanitizam senha, token, chaves e ciphertext.
- Responses de erro sao padronizadas e nao expoem material sensivel.

## Modelagem DynamoDB sugerida

- `users`
  - PK: `user_id`
  - GSI: `username-index` com PK `username`
- `connections`
  - PK: `user_id`
  - SK: `connection_id`
  - GSI: `connection-id-index` com PK `connection_id`
- `conversations`
  - PK: `conversation_id`
- `messages`
  - PK: `conversation_id`
  - SK: `message_id`
  - GSI: `recipient-status-index` com PK `recipient_id`

Para producao, vale evoluir o indice de mensagens com chave composta por status e data para buscas offline mais seletivas.

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

Cada `app.py` instancia explicitamente as dependencias que usa, sem container central.

## Como rodar

1. Crie um ambiente virtual com Python 3.12+.
2. Instale dependencias:

```bash
pip install -e .[dev]
```

3. Configure variaveis de ambiente:

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

4. Rode os testes:

```bash
pytest
```

## Limitacoes do MVP

- Ainda nao inclui IaC.
- Ainda nao ha refresh token, rotacao de chaves ou revogacao de JWT.
- A autorizacao por conversa pode ser expandida com politicas mais finas.
- O tratamento de conexoes expiradas pode ser enriquecido com limpeza reativa e DLQ.

## Evolucoes futuras

- Adicionar AWS CDK ou Terraform.
- Expandir testes com `moto` para integracao de DynamoDB e SQS.
- Adicionar metricas, tracing e dashboards.
- Implementar leitura por conversa com paginacao.
- Incluir politicas de retencao e arquivamento.
