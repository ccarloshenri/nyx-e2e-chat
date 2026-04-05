from dataclasses import dataclass


@dataclass(slots=True)
class Conversation:
    conversation_id: str
    participants: list[str]
    created_at: str
