from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.utils.event_parser import parse_json_body
from src.layers.main.nyx.utils.logger import get_module_logger
from src.layers.main.nyx.utils.request_context import build_request_context
from src.layers.main.nyx.utils.response_utils import success_response
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.auth_schemas import LOGIN_SCHEMA, PUBLIC_KEY_LOOKUP_SCHEMA, REGISTER_USER_SCHEMA

logger = get_module_logger(__name__)


class AuthController:
    def __init__(self, auth_bo: AuthBO, validator: RequestValidator) -> None:
        self.auth_bo = auth_bo
        self.validator = validator

    def register_user(self, event: dict) -> dict:
        context = build_request_context(event)
        payload = parse_json_body(event)
        self.validator.validate(REGISTER_USER_SCHEMA, payload)
        result = self.auth_bo.register_user(payload)
        logger.info("user_registered", extra={"context": {"correlation_id": context.correlation_id}})
        return success_response(result, status_code=201)

    def login(self, event: dict) -> dict:
        context = build_request_context(event)
        payload = parse_json_body(event)
        self.validator.validate(LOGIN_SCHEMA, payload)
        result = self.auth_bo.login(payload)
        logger.info("user_logged_in", extra={"context": {"correlation_id": context.correlation_id}})
        return success_response(result)

    def fetch_public_key(self, event: dict) -> dict:
        payload = parse_json_body(event)
        self.validator.validate(PUBLIC_KEY_LOOKUP_SCHEMA, payload)
        result = self.auth_bo.fetch_public_key(payload["username"])
        return success_response(result)

