from dataclasses import dataclass, field
from typing import Any

from src.layers.main.nyx.enums import MessageStatus


@dataclass(slots=True)
class Message:
    conversation_id: str
    message_id: str
    sender_id: str
    recipient_id: str
    ciphertext: str
    encrypted_message_key: str
    nonce: str
    algorithm: str
    created_at: str
    status: MessageStatus
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PendingDelivery:
    user_id: str
    conversation_id: str
    message_id: str
    status: MessageStatus
    created_at: str


@dataclass(slots=True)
class MessageAck:
    message_id: str
    conversation_id: str
    recipient_id: str
    received_at: str

