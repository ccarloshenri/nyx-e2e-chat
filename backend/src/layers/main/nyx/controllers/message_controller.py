from src.layers.main.nyx.aws.aws_event_parser import extract_aws_bearer_token, parse_aws_json_body
from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.utils.logger import bind_log_context, reset_log_context
from src.layers.main.nyx.validators.request_validator import RequestValidator
from time import perf_counter

from src.layers.main.nyx.validators.schemas.message_schemas import (
    ACK_MESSAGE_SCHEMA,
    FETCH_PENDING_MESSAGES_SCHEMA,
    QUEUED_SEND_MESSAGE_SCHEMA,
    SEND_MESSAGE_SCHEMA,
)


class MessageController:
    """Translate message-related events into validated business operations and queue processing."""

    def __init__(
        self,
        message_bo: MessageBO,
        validator: RequestValidator,
        jwt_service: IJwtService,
        logger: ILogger,
        response_formatter: AwsResponseFormatter,
    ) -> None:
        self.message_bo = message_bo
        self.validator = validator
        self.jwt_service = jwt_service
        self.logger = logger
        self.response_formatter = response_formatter

    def send_message(self, event: dict) -> dict:
        """Enqueue an outgoing message quickly and defer validation to the async processor."""
        context = build_aws_request_context(event)
        token = extract_aws_bearer_token(headers=event.get("headers"))
        payload = parse_aws_json_body(event)
        payload["correlation_id"] = context.correlation_id
        if context.request_id:
            payload["request_id"] = context.request_id
        log_token = bind_log_context(
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": None,
                "conversation_id": payload["conversation_id"],
                "message_id": payload["message_id"],
            }
        )
        self.logger.info(
            "message_send_requested",
            {
                "sender_id": payload.get("sender_id"),
                "receiver_id": payload["recipient_id"],
            },
        )
        try:
            result = self.message_bo.enqueue_message_for_async_validation(
                payload=payload,
                auth_token=token,
                deduplication_id=payload.get("message_id") or context.request_id or context.correlation_id,
                group_id=payload.get("conversation_id") or "unrouted",
            )
            self.logger.info(
                "message_sent_from_user_to_user",
                {
                    "sender_id": payload.get("sender_id"),
                    "receiver_id": payload["recipient_id"],
                    "status": result["status"],
                },
            )
            return self.response_formatter.success_response(result, status_code=202)
        finally:
            reset_log_context(log_token)

    def ack_message(self, event: dict) -> dict:
        """Acknowledge a delivered message on behalf of the authenticated recipient."""
        context = build_aws_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        payload = parse_aws_json_body(event)
        self.validator.validate(ACK_MESSAGE_SCHEMA, payload)
        log_token = bind_log_context(
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
                "conversation_id": payload["conversation_id"],
                "message_id": payload["message_id"],
            }
        )
        try:
            result = self.message_bo.ack_message(payload, user_id=auth.user_id)
            self.logger.info(
                "message_acknowledged",
                {
                    "recipient_id": auth.user_id,
                },
            )
            return self.response_formatter.success_response(result)
        finally:
            reset_log_context(log_token)

    def fetch_pending_messages(self, event: dict) -> dict:
        """Return pending encrypted messages for the authenticated user."""
        context = build_aws_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        payload = {"user_id": auth.user_id}
        self.validator.validate(FETCH_PENDING_MESSAGES_SCHEMA, payload)
        log_token = bind_log_context(
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
            }
        )
        try:
            result = self.message_bo.fetch_pending_messages(auth.user_id)
            self.logger.info("pending_messages_fetched", {"message_count": result["count"]})
            return self.response_formatter.success_response(result)
        finally:
            reset_log_context(log_token)

    def list_messages_for_conversation(self, event: dict) -> dict:
        """List encrypted conversation history after access checks pass."""
        context = build_aws_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        conversation_id = (event.get("pathParameters") or {}).get("conversation_id")
        log_token = bind_log_context(
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
                "conversation_id": conversation_id,
            }
        )
        try:
            result = self.message_bo.list_messages_for_conversation(conversation_id, auth.user_id)
            self.logger.info("conversation_messages_listed", {"message_count": result["count"]})
            return self.response_formatter.success_response(result)
        finally:
            reset_log_context(log_token)

    def process_sqs_record(self, record: dict) -> dict:
        """Process one queued message record under a propagated correlation context."""
        envelope = parse_aws_json_body({"body": record["body"]})
        self.validator.validate(QUEUED_SEND_MESSAGE_SCHEMA, envelope)
        payload = envelope["payload"]
        auth = self.jwt_service.decode_access_token(envelope["auth_token"])
        self.validator.validate(SEND_MESSAGE_SCHEMA, payload)
        self.message_bo.authorize_message_payload(payload, authenticated_user_id=auth.user_id)
        log_token = bind_log_context(
            {
                "correlation_id": payload.get("correlation_id"),
                "request_id": payload.get("request_id"),
                "user_id": auth.user_id,
                "conversation_id": payload.get("conversation_id"),
                "message_id": payload.get("message_id"),
                "queue_name": record.get("eventSourceARN", "").rsplit(":", maxsplit=1)[-1],
            }
        )
        self.logger.info(
            "processing_message_from_queue",
            {"queue_name": record.get("eventSourceARN", "").rsplit(":", maxsplit=1)[-1]},
        )
        try:
            result = self.message_bo.process_queued_message(payload)
            self.logger.info(
                "message_processed",
                {
                    "status": result["status"],
                    "receiver_id": payload["recipient_id"],
                },
            )
            return result
        finally:
            reset_log_context(log_token)

    def process_sqs_event(self, event: dict) -> dict:
        """Process a batch of queued messages and emit a single batch summary log."""
        started_at = perf_counter()
        results = []
        for record in event.get("Records", []):
            results.append(self.process_sqs_record(record))

        self.logger.info(
            "sqs_batch_processed",
            {"records": len(results), "duration_ms": round((perf_counter() - started_at) * 1000, 2)},
        )
        return {"batchItemFailures": [], "results": results}

