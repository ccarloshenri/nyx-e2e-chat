import json
from unittest.mock import MagicMock

from src.layers.main.nyx.controllers.message_controller import MessageController
from src.layers.main.nyx.models.auth import AuthContext


def test_send_message_returns_accepted(mocker):
    message_bo = MagicMock()
    message_bo.enqueue_message.return_value = {
        "message_id": "msg-1",
        "conversation_id": "conv-1",
        "status": "QUEUED",
    }
    validator = MagicMock()
    jwt_service = MagicMock()
    jwt_service.decode_access_token.return_value = AuthContext("u1", "alice", "t1")
    controller = MessageController(message_bo, validator, jwt_service)
    mocker.patch(
        "src.layers.main.nyx.controllers.message_controller.extract_bearer_token",
        return_value="token",
    )

    response = controller.send_message(
        {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps(
                {
                    "conversation_id": "conv-1",
                    "sender_id": "u1",
                    "recipient_id": "u2",
                    "encryption_type": "AES_GCM_V1",
                    "ciphertext": "abc",
                    "encrypted_message_key": "def",
                    "nonce": "ghi",
                    "message_id": "msg-1",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ),
        }
    )

    assert response["statusCode"] == 202
    validator.validate.assert_called_once()
    message_bo.enqueue_message.assert_called_once()

