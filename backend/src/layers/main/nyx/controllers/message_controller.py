from src.layers.main.nyx.aws.aws_event_parser import extract_aws_bearer_token, parse_aws_json_body
from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.message_schemas import ACK_MESSAGE_SCHEMA, FETCH_PENDING_MESSAGES_SCHEMA, SEND_MESSAGE_SCHEMA


class MessageController:
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
        context = build_aws_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        payload = parse_aws_json_body(event)
        self.validator.validate(SEND_MESSAGE_SCHEMA, payload)
        result = self.message_bo.enqueue_message(payload, authenticated_user_id=auth.user_id)
        self.logger.info(
            "message_enqueued",
            {
                "correlation_id": context.correlation_id,
                "user_id": auth.user_id,
                "message_id": payload["message_id"],
            },
        )
        return self.response_formatter.success_response(result, status_code=202)

    def ack_message(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        payload = parse_aws_json_body(event)
        self.validator.validate(ACK_MESSAGE_SCHEMA, payload)
        result = self.message_bo.ack_message(payload, user_id=auth.user_id)
        self.logger.info(
            "message_acknowledged",
            {
                "correlation_id": context.correlation_id,
                "user_id": auth.user_id,
                "message_id": payload["message_id"],
            },
        )
        return self.response_formatter.success_response(result)

    def fetch_pending_messages(self, event: dict) -> dict:
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        payload = {"user_id": auth.user_id}
        self.validator.validate(FETCH_PENDING_MESSAGES_SCHEMA, payload)
        result = self.message_bo.fetch_pending_messages(auth.user_id)
        return self.response_formatter.success_response(result)

    def process_sqs_record(self, record: dict) -> dict:
        payload = parse_aws_json_body({"body": record["body"]})
        self.validator.validate(SEND_MESSAGE_SCHEMA, payload)
        result = self.message_bo.process_queued_message(payload)
        self.logger.info("message_processed", {"message_id": payload["message_id"]})
        return result

    def process_sqs_event(self, event: dict) -> dict:
        results = []
        for record in event.get("Records", []):
            results.append(self.process_sqs_record(record))

        self.logger.info("sqs_batch_processed", {"records": len(results)})
        return {"batchItemFailures": [], "results": results}

