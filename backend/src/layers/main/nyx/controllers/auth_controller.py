from src.layers.main.nyx.aws.aws_event_parser import parse_aws_json_body
from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.exceptions import AuthenticationError
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.utils.logger import bind_log_context, reset_log_context
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.auth_schemas import (
    LOGIN_CHALLENGE_SCHEMA,
    LOGIN_SCHEMA,
    PUBLIC_KEY_LOOKUP_SCHEMA,
    REGISTER_USER_SCHEMA,
)


class AuthController:
    """Translate HTTP auth requests into validated business operations and structured logs."""

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
        """Validate the signup payload and create a verifier-based user account."""
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.validator.validate(REGISTER_USER_SCHEMA, payload)
        log_token = bind_log_context(
            {"correlation_id": context.correlation_id, "request_id": context.request_id}
        )
        try:
            result = self.auth_bo.register_user(payload)
            self.logger.info(
                "user_registered",
                {"username": payload["username"], "user_id": result["user_id"]},
            )
            return self.response_formatter.success_response(result, status_code=201)
        finally:
            reset_log_context(log_token)

    def login(self, event: dict) -> dict:
        """Validate a login proof exchange and return the authenticated session bundle."""
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.validator.validate(LOGIN_SCHEMA, payload)
        log_token = bind_log_context(
            {"correlation_id": context.correlation_id, "request_id": context.request_id}
        )
        self.logger.info("user_authentication_attempt", {"username": payload["username"]})
        try:
            result = self.auth_bo.login(payload)
            user_id = None
            if isinstance(result, dict):
                user = result.get("user")
                if isinstance(user, dict):
                    user_id = user.get("user_id")
            self.logger.info(
                "user_authenticated_successfully",
                {"username": payload["username"], "user_id": user_id},
            )
            return self.response_formatter.success_response(result)
        except AuthenticationError:
            self.logger.warning("authentication_failed", {"username": payload["username"]})
            raise
        finally:
            reset_log_context(log_token)

    def create_login_challenge(self, event: dict) -> dict:
        """Issue a short-lived login challenge for the provided username."""
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.validator.validate(LOGIN_CHALLENGE_SCHEMA, payload)
        log_token = bind_log_context(
            {"correlation_id": context.correlation_id, "request_id": context.request_id}
        )
        try:
            result = self.auth_bo.create_login_challenge(payload["username"])
            self.logger.info("login_challenge_issued", {"username": payload["username"]})
            return self.response_formatter.success_response(result)
        finally:
            reset_log_context(log_token)

    def fetch_public_key(self, event: dict) -> dict:
        """Return the target user's public key used for end-to-end encryption flows."""
        context = build_aws_request_context(event)
        payload = parse_aws_json_body(event)
        self.validator.validate(PUBLIC_KEY_LOOKUP_SCHEMA, payload)
        log_token = bind_log_context(
            {"correlation_id": context.correlation_id, "request_id": context.request_id}
        )
        try:
            result = self.auth_bo.fetch_public_key(payload["username"])
            self.logger.info("public_key_lookup_succeeded", {"username": payload["username"]})
            return self.response_formatter.success_response(result)
        finally:
            reset_log_context(log_token)

