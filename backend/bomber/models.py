from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BombUser:
    username: str
    master_password: str
    user_id: str | None = None
    token: str | None = None


@dataclass(slots=True)
class ConversationPair:
    conversation_id: str
    left_user: BombUser
    right_user: BombUser


@dataclass(slots=True)
class MessagePlan:
    conversation_id: str
    sender: BombUser
    recipient: BombUser
