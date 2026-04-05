from abc import ABC, abstractmethod

from src.layers.main.nyx.enums import MessageStatus
from src.layers.main.nyx.models.message import Message


class IMessageDao(ABC):
    @abstractmethod
    def save_message(self, message: Message) -> None:
        pass

    @abstractmethod
    def get_message(self, conversation_id: str, message_id: str) -> Message | None:
        pass

    @abstractmethod
    def list_pending_messages_for_user(self, user_id: str) -> list[Message]:
        pass

    @abstractmethod
    def update_message_status(
        self,
        conversation_id: str,
        message_id: str,
        status: MessageStatus,
    ) -> None:
        pass

