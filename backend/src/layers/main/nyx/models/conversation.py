from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Conversation:
    conversation_id: str
    participants: list[str]
    conversation_password_salt: str
    conversation_password_kdf_params: dict[str, Any]
    unlock_check_ciphertext: str
    unlock_check_nonce: str
    created_at: str
    participant_access: dict[str, dict[str, Any]] = field(default_factory=dict)

