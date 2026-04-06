from src.layers.main.nyx.aws.aws_event_parser import extract_aws_bearer_token
from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.bo.connection_bo import ConnectionBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.utils.response_utils import build_response
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.websocket_schemas import WEBSOCKET_CONNECT_SCHEMA, WEBSOCKET_DISCONNECT_SCHEMA


class WebSocketController:
    def __init__(
        self,
        connection_bo: ConnectionBO,
        validator: RequestValidator,
        jwt_service: IJwtService,
        logger: ILogger,
    ) -> None:
        self.connection_bo = connection_bo
        self.validator = validator
        self.jwt_service = jwt_service
        self.logger = logger

    def connect(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        token = extract_aws_bearer_token(
            headers=event.get("headers"),
            query=event.get("queryStringParameters"),
        )
        auth = self.jwt_service.decode_access_token(token)
        payload = {
            "connection_id": context.connection_id,
            "connected_at": str(event.get("requestContext", {}).get("connectedAt", "")),
        }
        self.validator.validate(WEBSOCKET_CONNECT_SCHEMA, payload)
        self.connection_bo.register_connection(auth.user_id, context.connection_id or "")
        self.logger.info(
            "websocket_connected",
            {"correlation_id": context.correlation_id, "user_id": auth.user_id},
        )
        return build_response(200, {"success": True})

    def disconnect(self, event: dict) -> dict:
        context = build_aws_request_context(event)
        payload = {"connection_id": context.connection_id}
        self.validator.validate(WEBSOCKET_DISCONNECT_SCHEMA, payload)
        self.connection_bo.disconnect(context.connection_id or "")
        self.logger.info(
            "websocket_disconnected",
            {"correlation_id": context.correlation_id, "connection_id": context.connection_id},
        )
        return build_response(200, {"success": True})

