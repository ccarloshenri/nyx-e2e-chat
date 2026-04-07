from src.layers.main.nyx.aws.aws_event_parser import extract_aws_bearer_token, parse_aws_json_body
from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.conversation_bo import ConversationBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.message_schemas import (
    CREATE_CONVERSATION_SCHEMA,
    SAVE_CONVERSATION_ACCESS_SCHEMA,
)


class ConversationController:
    def __init__(
        self,
        conversation_bo: ConversationBO,
        validator: RequestValidator,
        jwt_service: IJwtService,
        logger: ILogger,
        response_formatter: AwsResponseFormatter,
    ) -> None:
        self.conversation_bo = conversation_bo
        self.validator = validator
        self.jwt_service = jwt_service
        self.logger = logger
        self.response_formatter = response_formatter

    def create_conversation(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.logger.info(
            "create_conversation_requested",
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "target_username": payload.get("target_username"),
            },
        )
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        self.logger.info(
            "create_conversation_authenticated",
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
                "target_username": payload.get("target_username"),
            },
        )
        self.validator.validate(CREATE_CONVERSATION_SCHEMA, payload)
        self.logger.info(
            "create_conversation_validated",
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
                "target_username": payload["target_username"],
            },
        )
        result = self.conversation_bo.create_conversation(payload, auth.user_id)
        self.logger.info(
            "conversation_created",
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
                "target_username": payload["target_username"],
                "conversation_id": result.get("conversation_id"),
            },
        )
        return self.response_formatter.success_response(result, status_code=201)

    def list_conversations(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        self.logger.info(
            "list_conversations_requested",
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
            },
        )
        result = self.conversation_bo.list_conversations_for_user(auth.user_id)
        self.logger.info(
            "conversations_listed",
            {
                "correlation_id": context.correlation_id,
                "request_id": context.request_id,
                "user_id": auth.user_id,
                "conversation_count": result.get("count"),
            },
        )
        return self.response_formatter.success_response(result)

    def get_conversation_access_context(self, event: dict) -> dict:
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        conversation_id = (event.get("pathParameters") or {}).get("conversation_id")
        result = self.conversation_bo.get_conversation_access_context(conversation_id, auth.user_id)
        return self.response_formatter.success_response(result)

    def save_conversation_access(self, event: dict) -> dict:
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        conversation_id = (event.get("pathParameters") or {}).get("conversation_id")
        payload = parse_aws_json_body(event)
        self.validator.validate(SAVE_CONVERSATION_ACCESS_SCHEMA, payload)
        result = self.conversation_bo.save_participant_access(
            conversation_id=conversation_id,
            user_id=auth.user_id,
            access_payload=payload,
        )
        return self.response_formatter.success_response(result, status_code=201)

