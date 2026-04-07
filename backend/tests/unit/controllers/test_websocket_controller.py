from unittest.mock import MagicMock, patch

from src.layers.main.nyx.controllers.websocket_controller import WebSocketController
from src.layers.main.nyx.models.auth import AuthContext
from src.layers.main.nyx.models.request_context import RequestContext


def build_controller():
    return WebSocketController(
        connection_bo=MagicMock(),
        validator=MagicMock(),
        jwt_service=MagicMock(),
        logger=MagicMock(),
        response_formatter=MagicMock(),
    )


def test_connect_registers_connection_and_returns_ok():
    controller = build_controller()
    controller.jwt_service.decode_access_token.return_value = AuthContext("user-1", "alice", "t1")
    controller.response_formatter.build_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.websocket_controller.build_aws_request_context",
        return_value=RequestContext(
            correlation_id="corr-1",
            request_id="req-1",
            connection_id="conn-1",
        ),
    ), patch(
        "src.layers.main.nyx.controllers.websocket_controller.extract_aws_bearer_token",
        return_value="token",
    ):
        response = controller.connect(
            {"requestContext": {"connectedAt": 1234567890}, "headers": {}}
        )

    controller.validator.validate.assert_called_once()
    controller.connection_bo.register_connection.assert_called_once_with("user-1", "conn-1")
    assert response == {"statusCode": 200}


def test_disconnect_validates_and_removes_connection():
    controller = build_controller()
    controller.response_formatter.build_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.websocket_controller.build_aws_request_context",
        return_value=RequestContext(
            correlation_id="corr-1",
            request_id="req-1",
            connection_id="conn-1",
        ),
    ):
        response = controller.disconnect({"requestContext": {"connectionId": "conn-1"}})

    controller.validator.validate.assert_called_once()
    controller.connection_bo.disconnect.assert_called_once_with("conn-1")
    assert response == {"statusCode": 200}
