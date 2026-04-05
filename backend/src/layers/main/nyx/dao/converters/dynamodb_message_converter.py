from dataclasses import asdict

from src.layers.main.nyx.enums import EncryptionType, MessageStatus
from src.layers.main.nyx.models.message import Message


class DynamoDbMessageConverter:
    @staticmethod
    def to_dict(message: Message) -> dict:
        item = asdict(message)
        item["encryption_type"] = message.encryption_type.value
        item["status"] = message.status.value
        return item

    @staticmethod
    def from_dict(item: dict) -> Message:
        payload = dict(item)
        payload["status"] = MessageStatus(payload["status"])
        payload["encryption_type"] = EncryptionType(
            payload.get("encryption_type", EncryptionType.AES_GCM_V1.value)
        )
        return Message(**payload)

