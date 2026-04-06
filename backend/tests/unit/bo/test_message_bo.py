from unittest.mock import MagicMock

import pytest

from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.enums import EncryptionType, MessageStatus
from src.layers.main.nyx.models.message import Message
from src.layers.main.nyx.exceptions import AuthorizationError
from src.layers.main.nyx.interfaces.infrastructure.i_infrastructure import IInfrastructure


class FakeInfrastructure(IInfrastructure):
    def __init__(
        self,
        message_dao,
        connection_dao,
        conversation_dao=None,
        queue_publisher=None,
        websocket_notifier=None,
    ) -> None:
        self._message_dao = message_dao
        self._connection_dao = connection_dao
        self._conversation_dao = conversation_dao or MagicMock()
        self._queue_publisher = queue_publisher or MagicMock()
        self._websocket_notifier = websocket_notifier or MagicMock()
        self._user_dao = MagicMock()

    def get_user_dao(self):
        return self._user_dao

    def get_connection_dao(self):
        return self._connection_dao

    def get_conversation_dao(self):
        return self._conversation_dao

    def get_message_dao(self):
        return self._message_dao

    def get_queue_publisher(self):
        return self._queue_publisher

    def get_websocket_notifier(self):
        return self._websocket_notifier


def test_enqueue_message_rejects_sender_mismatch():
    infrastructure = FakeInfrastructure(
        message_dao=MagicMock(),
        connection_dao=MagicMock(),
        conversation_dao=MagicMock(),
        queue_publisher=MagicMock(),
        websocket_notifier=MagicMock(),
    )
    bo = MessageBO(
        infrastructure=infrastructure,
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
    infrastructure = FakeInfrastructure(
        message_dao=message_dao,
        connection_dao=MagicMock(),
        queue_publisher=MagicMock(),
        websocket_notifier=MagicMock(),
    )
    bo = MessageBO(
        infrastructure=infrastructure,
    )

    with pytest.raises(AuthorizationError):
        bo.ack_message(
            {"conversation_id": "conv-1", "message_id": "msg-1", "received_at": "2026-01-01"},
            user_id="user-c",
        )

