from unittest.mock import MagicMock

from src.layers.main.nyx.dao.converters.dynamodb_message_converter import DynamoDbMessageConverter
from src.layers.main.nyx.dao.message_dynamodb_dao import MessageDynamoDbDao
from src.layers.main.nyx.enums import EncryptionType, MessageStatus
from src.layers.main.nyx.models.message import Message


def test_get_message_returns_none_when_missing():
    dynamodb = MagicMock()
    table = MagicMock()
    table.get_item.return_value = {}
    dynamodb.Table.return_value = table
    dao = MessageDynamoDbDao(dynamodb=dynamodb)

    result = dao.get_message("conv", "msg")

    assert result is None


def test_save_message_persists_serialized_model():
    dynamodb = MagicMock()
    table = MagicMock()
    dynamodb.Table.return_value = table
    dao = MessageDynamoDbDao(dynamodb=dynamodb)
    message = Message(
        conversation_id="conv",
        message_id="msg",
        sender_id="u1",
        recipient_id="u2",
        encryption_type=EncryptionType.AES_GCM_V1,
        ciphertext="abc",
        encrypted_message_key="def",
        nonce="ghi",
        created_at="2026-01-01T00:00:00+00:00",
        status=MessageStatus.PENDING,
    )

    dao.save_message(message)

    table.put_item.assert_called_once_with(Item=DynamoDbMessageConverter.to_dict(message))

