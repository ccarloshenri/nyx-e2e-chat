from src.layers.main.nyx.aws.aws_event_parser import parse_aws_json_body
from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.auth_schemas import LOGIN_SCHEMA, PUBLIC_KEY_LOOKUP_SCHEMA, REGISTER_USER_SCHEMA


class AuthController:
    def __init__(
        self,
        auth_bo: AuthBO,
        validator: RequestValidator,
        logger: ILogger,
        response_formatter: AwsResponseFormatter,
    ) -> None:
        self.auth_bo = auth_bo
        self.validator = validator
        self.logger = logger
        self.response_formatter = response_formatter

    def register_user(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.validator.validate(REGISTER_USER_SCHEMA, payload)
        result = self.auth_bo.register_user(payload)
        self.logger.info("user_registered", {"correlation_id": context.correlation_id})
        return self.response_formatter.success_response(result, status_code=201)

    def login(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.validator.validate(LOGIN_SCHEMA, payload)
        result = self.auth_bo.login(payload)
        self.logger.info("user_logged_in", {"correlation_id": context.correlation_id})
        return self.response_formatter.success_response(result)

    def fetch_public_key(self, event: dict) -> dict:
        payload = parse_aws_json_body(event)
        self.validator.validate(PUBLIC_KEY_LOOKUP_SCHEMA, payload)
        result = self.auth_bo.fetch_public_key(payload["username"])
        return self.response_formatter.success_response(result)

