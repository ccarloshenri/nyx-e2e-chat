from src.layers.main.nyx.bo.conversation_bo import ConversationBO
from src.layers.main.nyx.utils.event_parser import parse_json_body
from src.layers.main.nyx.utils.response_utils import success_response
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.message_schemas import CREATE_CONVERSATION_SCHEMA


class ConversationController:
    def __init__(self, conversation_bo: ConversationBO, validator: RequestValidator) -> None:
        self.conversation_bo = conversation_bo
        self.validator = validator

    def create_conversation(self, event: dict) -> dict:
        payload = parse_json_body(event)
        self.validator.validate(CREATE_CONVERSATION_SCHEMA, payload)
        result = self.conversation_bo.create_conversation(payload)
        return success_response(result, status_code=201)

