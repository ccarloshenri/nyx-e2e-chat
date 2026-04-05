from dataclasses import asdict

from src.models.conversation import Conversation


class DynamoDbConversationConverter:
    @staticmethod
    def to_dict(conversation: Conversation) -> dict:
        return asdict(conversation)

    @staticmethod
    def from_dict(item: dict) -> Conversation:
        return Conversation(**item)
