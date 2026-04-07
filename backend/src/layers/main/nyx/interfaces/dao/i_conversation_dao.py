from abc import ABC, abstractmethod

from src.layers.main.nyx.models.conversation import Conversation


class IConversationDao(ABC):
    @abstractmethod
    def create_conversation(self, conversation: Conversation) -> None:
        pass

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Conversation | None:
        pass

    @abstractmethod
    def list_conversations_for_user(self, user_id: str) -> list[Conversation]:
        pass

    @abstractmethod
    def save_participant_access(self, conversation_id: str, user_id: str, access_payload: dict) -> None:
        pass

