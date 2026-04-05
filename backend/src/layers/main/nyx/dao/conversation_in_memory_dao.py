from copy import deepcopy

from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.local.in_memory_store import InMemoryStore
from src.layers.main.nyx.models.conversation import Conversation


class ConversationInMemoryDao(IConversationDao):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def create_conversation(self, conversation: Conversation) -> None:
        self.store.conversations_by_id[conversation.conversation_id] = deepcopy(conversation)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.store.clone_conversation(self.store.conversations_by_id.get(conversation_id))

    def list_conversations_for_user(self, user_id: str) -> list[Conversation]:
        conversations = [
            deepcopy(conversation)
            for conversation in self.store.conversations_by_id.values()
            if user_id in conversation.participants
        ]
        return sorted(conversations, key=lambda conversation: conversation.created_at, reverse=True)
