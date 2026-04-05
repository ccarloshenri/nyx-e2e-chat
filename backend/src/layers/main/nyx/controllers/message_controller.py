from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.utils.event_parser import extract_bearer_token, parse_json_body
from src.layers.main.nyx.utils.logger import get_module_logger
from src.layers.main.nyx.utils.request_context import build_request_context
from src.layers.main.nyx.utils.response_utils import success_response
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.message_schemas import ACK_MESSAGE_SCHEMA, FETCH_PENDING_MESSAGES_SCHEMA, SEND_MESSAGE_SCHEMA

logger = get_module_logger(__name__)


class MessageController:
    def __init__(
        self,
        message_bo: MessageBO,
        validator: RequestValidator,
        jwt_service: IJwtService,
    ) -> None:
        self.message_bo = message_bo
        self.validator = validator
        self.jwt_service = jwt_service

    def send_message(self, event: dict) -> dict:
        context = build_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_bearer_token(headers=event.get("headers"))
        )
        payload = parse_json_body(event)
        self.validator.validate(SEND_MESSAGE_SCHEMA, payload)
        result = self.message_bo.enqueue_message(payload, authenticated_user_id=auth.user_id)
        logger.info(
            "message_enqueued",
            extra={
                "context": {
                    "correlation_id": context.correlation_id,
                    "user_id": auth.user_id,
                    "message_id": payload["message_id"],
                }
            },
        )
        return success_response(result, status_code=202)

    def ack_message(self, event: dict) -> dict:
        context = build_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_bearer_token(headers=event.get("headers"))
        )
        payload = parse_json_body(event)
        self.validator.validate(ACK_MESSAGE_SCHEMA, payload)
        result = self.message_bo.ack_message(payload, user_id=auth.user_id)
        logger.info(
            "message_acknowledged",
            extra={
                "context": {
                    "correlation_id": context.correlation_id,
                    "user_id": auth.user_id,
                    "message_id": payload["message_id"],
                }
            },
        )
        return success_response(result)

    def fetch_pending_messages(self, event: dict) -> dict:
        auth = self.jwt_service.decode_access_token(
            extract_bearer_token(headers=event.get("headers"))
        )
        payload = {"user_id": auth.user_id}
        self.validator.validate(FETCH_PENDING_MESSAGES_SCHEMA, payload)
        result = self.message_bo.fetch_pending_messages(auth.user_id)
        return success_response(result)

    def process_sqs_record(self, record: dict) -> dict:
        payload = parse_json_body({"body": record["body"]})
        self.validator.validate(SEND_MESSAGE_SCHEMA, payload)
        result = self.message_bo.process_queued_message(payload)
        logger.info("message_processed", extra={"context": {"message_id": payload["message_id"]}})
        return result

    def process_sqs_event(self, event: dict) -> dict:
        results = []
        for record in event.get("Records", []):
            results.append(self.process_sqs_record(record))

        logger.info("sqs_batch_processed", extra={"context": {"records": len(results)}})
        return {"batchItemFailures": [], "results": results}

