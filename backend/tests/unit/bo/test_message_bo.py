from unittest.mock import MagicMock

import pytest

from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.enums import EncryptionType, MessageStatus
from src.layers.main.nyx.models.message import Message
from src.layers.main.nyx.utils.exceptions import AuthorizationError


def test_enqueue_message_rejects_sender_mismatch():
    bo = MessageBO(
        message_dao=MagicMock(),
        connection_dao=MagicMock(),
        conversation_dao=MagicMock(),
        queue_publisher=MagicMock(),
        websocket_notifier=MagicMock(),
    )

    with pytest.raises(AuthorizationError):
        bo.enqueue_message(
            {
                "conversation_id": "conv-1",
                "sender_id": "user-a",
                "recipient_id": "user-b",
                "encryption_type": "AES_GCM_V1",
                "ciphertext": "cipher",
                "encrypted_message_key": "key",
                "nonce": "nonce",
                "message_id": "msg-1",
                "created_at": "2026-01-01T00:00:00+00:00",
            },
            authenticated_user_id="user-b",
        )


def test_ack_message_checks_recipient():
    message_dao = MagicMock()
    message_dao.get_message.return_value = Message(
        conversation_id="conv-1",
        message_id="msg-1",
        sender_id="user-a",
        recipient_id="user-b",
        encryption_type=EncryptionType.AES_GCM_V1,
        ciphertext="cipher",
        encrypted_message_key="key",
        nonce="nonce",
        created_at="2026-01-01T00:00:00+00:00",
        status=MessageStatus.PENDING,
    )
    bo = MessageBO(
        message_dao=message_dao,
        connection_dao=MagicMock(),
        queue_publisher=MagicMock(),
        websocket_notifier=MagicMock(),
    )

    with pytest.raises(AuthorizationError):
        bo.ack_message(
            {"conversation_id": "conv-1", "message_id": "msg-1", "received_at": "2026-01-01"},
            user_id="user-c",
        )

