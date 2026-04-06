import json
from unittest.mock import MagicMock, patch

from src.layers.main.nyx.controllers.auth_controller import AuthController
from src.layers.main.nyx.models.request_context import RequestContext


def build_auth_controller():
    return AuthController(
        auth_bo=MagicMock(),
        validator=MagicMock(),
        logger=MagicMock(),
        response_formatter=MagicMock(),
    )


def test_register_user_validates_payload_and_returns_created_response():
    controller = build_auth_controller()
    controller.auth_bo.register_user.return_value = {"user_id": "user-1"}
    controller.response_formatter.success_response.return_value = {"statusCode": 201}

    with patch(
        "src.layers.main.nyx.controllers.auth_controller.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ), patch(
        "src.layers.main.nyx.controllers.auth_controller.parse_aws_json_body",
        return_value={"username": "alice", "password": "secret"},
    ):
        response = controller.register_user({"body": json.dumps({})})

    controller.validator.validate.assert_called_once()
    controller.auth_bo.register_user.assert_called_once_with(
        {"username": "alice", "password": "secret"}
    )
    controller.logger.info.assert_called_once()
    controller.response_formatter.success_response.assert_called_once_with(
        {"user_id": "user-1"},
        status_code=201,
    )
    assert response == {"statusCode": 201}


def test_login_returns_formatted_success_response():
    controller = build_auth_controller()
    controller.auth_bo.login.return_value = {"token": {"access_token": "token"}}
    controller.response_formatter.success_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.auth_controller.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ), patch(
        "src.layers.main.nyx.controllers.auth_controller.parse_aws_json_body",
        return_value={"username": "alice", "password": "secret"},
    ):
        response = controller.login({"body": json.dumps({})})

    controller.validator.validate.assert_called_once()
    controller.auth_bo.login.assert_called_once_with(
        {"username": "alice", "password": "secret"}
    )
    assert response == {"statusCode": 200}


def test_fetch_public_key_uses_username_from_request_payload():
    controller = build_auth_controller()
    controller.auth_bo.fetch_public_key.return_value = {"public_key": "pk"}
    controller.response_formatter.success_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.auth_controller.parse_aws_json_body",
        return_value={"username": "alice"},
    ):
        response = controller.fetch_public_key({"body": json.dumps({})})

    controller.validator.validate.assert_called_once()
    controller.auth_bo.fetch_public_key.assert_called_once_with("alice")
    assert response == {"statusCode": 200}
