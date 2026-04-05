from src.config.settings import settings
from src.layers.main.nyx.dao.base_dynamodb_dao import BaseDynamoDbDao
from src.layers.main.nyx.dao.converters.dynamodb_conversation_converter import (
    DynamoDbConversationConverter,
)
from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.models.conversation import Conversation


class ConversationDynamoDbDao(BaseDynamoDbDao, IConversationDao):
    def __init__(self, dynamodb) -> None:
        super().__init__(settings.conversations_table_name, dynamodb)

    def create_conversation(self, conversation: Conversation) -> None:
        self.table.put_item(
            Item=DynamoDbConversationConverter.to_dict(conversation),
            ConditionExpression="attribute_not_exists(conversation_id)",
        )

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        response = self.table.get_item(Key={"conversation_id": conversation_id})
        item = response.get("Item")
        return DynamoDbConversationConverter.from_dict(item) if item else None
