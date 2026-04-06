from src.layers.main.nyx.dao.base_dynamodb_dao import BaseDynamoDbDao
from src.layers.main.nyx.dao.converters.dynamodb_conversation_converter import (
    DynamoDbConversationConverter,
)
from src.layers.main.nyx.dao.tables.conversations_table import ConversationsTable
from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.models.conversation import Conversation


class ConversationDynamoDbDao(BaseDynamoDbDao, IConversationDao):
    def __init__(self, conversations_table: ConversationsTable | None = None) -> None:
        super().__init__(conversations_table or ConversationsTable())

    def create_conversation(self, conversation: Conversation) -> None:
        self.table.put_item(
            Item=DynamoDbConversationConverter.to_dict(conversation),
            ConditionExpression="attribute_not_exists(conversation_id)",
        )

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        response = self.table.get_item(Key={"conversation_id": conversation_id})
        item = response.get("Item")
        return DynamoDbConversationConverter.from_dict(item) if item else None

    def list_conversations_for_user(self, user_id: str) -> list[Conversation]:
        response = self.table.scan()
        conversations = [
            DynamoDbConversationConverter.from_dict(item)
            for item in response.get("Items", [])
            if user_id in item.get("participants", [])
        ]
        return sorted(conversations, key=lambda conversation: conversation.created_at, reverse=True)

