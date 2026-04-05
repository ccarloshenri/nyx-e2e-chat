from enum import Enum


class MessageStatus(str, Enum):
    QUEUED = "QUEUED"
    DELIVERED = "DELIVERED"
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"


class WebSocketAction(str, Enum):
    DELIVER_MESSAGE = "deliver_message"
    PENDING_MESSAGES = "pending_messages"
