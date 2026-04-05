from dataclasses import asdict

from src.layers.main.nyx.enums import MessageStatus
from src.layers.main.nyx.models.message import Message


class DynamoDbMessageConverter:
    @staticmethod
    def to_dict(message: Message) -> dict:
        item = asdict(message)
        item["status"] = message.status.value
        return item

    @staticmethod
    def from_dict(item: dict) -> Message:
        payload = dict(item)
        payload["status"] = MessageStatus(payload["status"])
        return Message(**payload)

