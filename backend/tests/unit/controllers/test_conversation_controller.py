from unittest.mock import MagicMock, patch

from src.layers.main.nyx.controllers.conversation_controller import ConversationController
from src.layers.main.nyx.models.auth import AuthContext


def build_controller():
    return ConversationController(
        conversation_bo=MagicMock(),
        validator=MagicMock(),
        jwt_service=MagicMock(),
        response_formatter=MagicMock(),
    )


def test_create_conversation_returns_created_response():
    controller = build_controller()
    controller.conversation_bo.create_conversation.return_value = {"conversation_id": "conv-1"}
    controller.jwt_service.decode_access_token.return_value = AuthContext(
        user_id="user-1",
        username="alice",
        token_id="token-1",
    )
    controller.response_formatter.success_response.return_value = {"statusCode": 201}

    with patch(
        "src.layers.main.nyx.controllers.conversation_controller.parse_aws_json_body",
        return_value={"target_username": "bob"},
    ), patch(
        "src.layers.main.nyx.controllers.conversation_controller.extract_aws_bearer_token",
        return_value="token",
    ):
        response = controller.create_conversation({"body": "{}", "headers": {"Authorization": "Bearer token"}})

    controller.validator.validate.assert_called_once()
    controller.conversation_bo.create_conversation.assert_called_once_with(
        {"target_username": "bob"},
        "user-1",
    )
    controller.response_formatter.success_response.assert_called_once_with(
        {"conversation_id": "conv-1"},
        status_code=201,
    )
    assert response == {"statusCode": 201}


def test_list_conversations_uses_authenticated_user():
    controller = build_controller()
    controller.jwt_service.decode_access_token.return_value = AuthContext(
        user_id="user-1",
        username="alice",
        token_id="token-1",
    )
    controller.conversation_bo.list_conversations_for_user.return_value = {
        "conversations": [],
        "count": 0,
    }
    controller.response_formatter.success_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.conversation_controller.extract_aws_bearer_token",
        return_value="token",
    ):
        response = controller.list_conversations({"headers": {"Authorization": "Bearer token"}})

    controller.conversation_bo.list_conversations_for_user.assert_called_once_with("user-1")
    assert response == {"statusCode": 200}
