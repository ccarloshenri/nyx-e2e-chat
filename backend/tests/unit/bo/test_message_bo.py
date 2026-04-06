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


def test_enqueue_message_publishes_when_user_is_conversation_participant():
    message_dao = MagicMock()
    connection_dao = MagicMock()
    conversation_dao = MagicMock()
    conversation_dao.get_conversation.return_value = MagicMock(participants=["user-a", "user-b"])
    queue_publisher = MagicMock()
    infrastructure = FakeInfrastructure(
        message_dao=message_dao,
        connection_dao=connection_dao,
        conversation_dao=conversation_dao,
        queue_publisher=queue_publisher,
        websocket_notifier=MagicMock(),
    )
    bo = MessageBO(infrastructure=infrastructure)

    result = bo.enqueue_message(
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
        authenticated_user_id="user-a",
    )

    queue_publisher.publish.assert_called_once_with(
        payload={
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
        deduplication_id="msg-1",
        group_id="conv-1",
    )
    assert result["status"] == MessageStatus.QUEUED.value


def test_process_queued_message_marks_as_delivered_when_notified():
    message_dao = MagicMock()
    connection_dao = MagicMock()
    connection_dao.get_connections_by_user.return_value = [
        MagicMock(connection_id="conn-1"),
        MagicMock(connection_id="conn-2"),
    ]
    websocket_notifier = MagicMock()
    idempotency_service = MagicMock()
    idempotency_service.message_already_processed.return_value = False
    infrastructure = FakeInfrastructure(
        message_dao=message_dao,
        connection_dao=connection_dao,
        conversation_dao=MagicMock(),
        queue_publisher=MagicMock(),
        websocket_notifier=websocket_notifier,
    )
    bo = MessageBO(infrastructure=infrastructure, idempotency_service=idempotency_service)

    result = bo.process_queued_message(
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
            "metadata": {"version": 1},
        }
    )

    message_dao.save_message.assert_called_once()
    message_dao.update_message_status.assert_called_once_with(
        "conv-1",
        "msg-1",
        MessageStatus.DELIVERED,
    )
    assert websocket_notifier.notify.call_count == 2
    assert result == {"message_id": "msg-1", "status": MessageStatus.DELIVERED.value}


def test_process_queued_message_returns_duplicate_when_already_processed():
    infrastructure = FakeInfrastructure(
        message_dao=MagicMock(),
        connection_dao=MagicMock(),
    )
    idempotency_service = MagicMock()
    idempotency_service.message_already_processed.return_value = True
    bo = MessageBO(infrastructure=infrastructure, idempotency_service=idempotency_service)

    result = bo.process_queued_message(
        {
            "conversation_id": "conv-1",
            "message_id": "msg-1",
            "sender_id": "user-a",
            "recipient_id": "user-b",
            "encryption_type": "AES_GCM_V1",
            "ciphertext": "cipher",
            "encrypted_message_key": "key",
            "nonce": "nonce",
            "created_at": "2026-01-01T00:00:00+00:00",
        }
    )

    assert result == {"message_id": "msg-1", "status": "DUPLICATE"}


def test_fetch_pending_messages_returns_serialized_count():
    message = Message(
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
    message_dao = MagicMock()
    message_dao.list_pending_messages_for_user.return_value = [message]
    infrastructure = FakeInfrastructure(message_dao=message_dao, connection_dao=MagicMock())
    bo = MessageBO(infrastructure=infrastructure)

    result = bo.fetch_pending_messages("user-b")

    assert result["count"] == 1
    assert result["messages"][0]["message_id"] == "msg-1"


def test_push_pending_messages_notifies_each_connection():
    pending_messages = [
        Message(
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
    ]
    message_dao = MagicMock()
    message_dao.list_pending_messages_for_user.return_value = pending_messages
    connection_dao = MagicMock()
    connection_dao.get_connections_by_user.return_value = [
        MagicMock(connection_id="conn-1"),
        MagicMock(connection_id="conn-2"),
    ]
    websocket_notifier = MagicMock()
    infrastructure = FakeInfrastructure(
        message_dao=message_dao,
        connection_dao=connection_dao,
        websocket_notifier=websocket_notifier,
    )
    bo = MessageBO(infrastructure=infrastructure)

    result = bo.push_pending_messages("user-b")

    assert websocket_notifier.notify.call_count == 2
    assert result == {"delivered": 2}

