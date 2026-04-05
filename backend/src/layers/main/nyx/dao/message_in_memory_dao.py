from copy import deepcopy

from src.layers.main.nyx.enums import MessageStatus
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.local.in_memory_store import InMemoryStore
from src.layers.main.nyx.models.message import Message


class MessageInMemoryDao(IMessageDao):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def save_message(self, message: Message) -> None:
        self.store.messages_by_key[(message.conversation_id, message.message_id)] = deepcopy(message)

    def get_message(self, conversation_id: str, message_id: str) -> Message | None:
        return self.store.clone_message(self.store.messages_by_key.get((conversation_id, message_id)))

    def list_pending_messages_for_user(self, user_id: str) -> list[Message]:
        messages = [
            deepcopy(message)
            for message in self.store.messages_by_key.values()
            if message.recipient_id == user_id
            and message.status in {MessageStatus.PENDING, MessageStatus.DELIVERED}
        ]
        return sorted(messages, key=lambda message: message.created_at)

    def update_message_status(
        self,
        conversation_id: str,
        message_id: str,
        status: MessageStatus,
    ) -> None:
        message = self.store.messages_by_key.get((conversation_id, message_id))
        if message is None:
            return
        message.status = status
