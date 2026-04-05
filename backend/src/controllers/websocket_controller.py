from src.bo.connection_bo import ConnectionBO
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.utils.event_parser import extract_bearer_token
from src.utils.logger import get_module_logger
from src.utils.request_context import build_request_context
from src.utils.response_utils import build_response
from src.validators.request_validator import RequestValidator
from src.validators.schemas.websocket_schemas import WEBSOCKET_CONNECT_SCHEMA, WEBSOCKET_DISCONNECT_SCHEMA

logger = get_module_logger(__name__)


class WebSocketController:
    def __init__(
        self,
        connection_bo: ConnectionBO,
        validator: RequestValidator,
        jwt_service: IJwtService,
    ) -> None:
        self.connection_bo = connection_bo
        self.validator = validator
        self.jwt_service = jwt_service

    def connect(self, event: dict) -> dict:
        context = build_request_context(event)
        token = extract_bearer_token(
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
        logger.info(
            "websocket_connected",
            extra={"context": {"correlation_id": context.correlation_id, "user_id": auth.user_id}},
        )
        return build_response(200, {"success": True})

    def disconnect(self, event: dict) -> dict:
        context = build_request_context(event)
        payload = {"connection_id": context.connection_id}
        self.validator.validate(WEBSOCKET_DISCONNECT_SCHEMA, payload)
        self.connection_bo.disconnect(context.connection_id or "")
        logger.info(
            "websocket_disconnected",
            extra={"context": {"correlation_id": context.correlation_id, "connection_id": context.connection_id}},
        )
        return build_response(200, {"success": True})
