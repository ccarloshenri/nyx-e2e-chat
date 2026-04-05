from copy import deepcopy
from dataclasses import dataclass, field

from src.layers.main.nyx.models.connection import Connection
from src.layers.main.nyx.models.conversation import Conversation
from src.layers.main.nyx.models.message import Message
from src.layers.main.nyx.models.user import User


@dataclass
class InMemoryStore:
    users_by_id: dict[str, User] = field(default_factory=dict)
    usernames_to_user_id: dict[str, str] = field(default_factory=dict)
    conversations_by_id: dict[str, Conversation] = field(default_factory=dict)
    messages_by_key: dict[tuple[str, str], Message] = field(default_factory=dict)
    connections_by_user: dict[str, dict[str, Connection]] = field(default_factory=dict)
    notifications_by_connection: dict[str, list[dict]] = field(default_factory=dict)
    published_messages: list[dict] = field(default_factory=list)

    def clone_user(self, user: User | None) -> User | None:
        return deepcopy(user) if user is not None else None

    def clone_conversation(self, conversation: Conversation | None) -> Conversation | None:
        return deepcopy(conversation) if conversation is not None else None

    def clone_message(self, message: Message | None) -> Message | None:
        return deepcopy(message) if message is not None else None

    def clone_connection(self, connection: Connection | None) -> Connection | None:
        return deepcopy(connection) if connection is not None else None
