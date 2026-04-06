from src.layers.main.nyx.aws.aws_event_parser import extract_aws_bearer_token, parse_aws_json_body
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.conversation_bo import ConversationBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.message_schemas import CREATE_CONVERSATION_SCHEMA


class ConversationController:
    def __init__(
        self,
        conversation_bo: ConversationBO,
        validator: RequestValidator,
        jwt_service: IJwtService,
        response_formatter: AwsResponseFormatter,
    ) -> None:
        self.conversation_bo = conversation_bo
        self.validator = validator
        self.jwt_service = jwt_service
        self.response_formatter = response_formatter

    def create_conversation(self, event: dict) -> dict:
        payload = parse_aws_json_body(event)
        self.validator.validate(CREATE_CONVERSATION_SCHEMA, payload)
        result = self.conversation_bo.create_conversation(payload)
        return self.response_formatter.success_response(result, status_code=201)

    def list_conversations(self, event: dict) -> dict:
        auth = self.jwt_service.decode_access_token(
            extract_aws_bearer_token(headers=event.get("headers"))
        )
        result = self.conversation_bo.list_conversations_for_user(auth.user_id)
        return self.response_formatter.success_response(result)

