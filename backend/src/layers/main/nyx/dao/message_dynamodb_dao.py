from boto3.dynamodb.conditions import Attr, Key

from src.layers.main.nyx.dao.base_dynamodb_dao import BaseDynamoDbDao
from src.layers.main.nyx.dao.converters.dynamodb_message_converter import DynamoDbMessageConverter
from src.layers.main.nyx.dao.tables.messages_table import MessagesTable
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.enums import MessageStatus
from src.layers.main.nyx.models.message import Message


class MessageDynamoDbDao(BaseDynamoDbDao, IMessageDao):
    def __init__(self, messages_table: MessagesTable | None = None) -> None:
        super().__init__(messages_table or MessagesTable())

    def save_message(self, message: Message) -> None:
        self.table.put_item(Item=DynamoDbMessageConverter.to_dict(message))

    def get_message(self, conversation_id: str, message_id: str) -> Message | None:
        response = self.table.get_item(
            Key={"conversation_id": conversation_id, "message_id": message_id}
        )
        item = response.get("Item")
        return DynamoDbMessageConverter.from_dict(item) if item else None

    def list_pending_messages_for_user(self, user_id: str) -> list[Message]:
        response = self.table.query(
            IndexName="recipient-status-index",
            KeyConditionExpression=Key("recipient_id").eq(user_id),
            FilterExpression=Attr("status").is_in(
                [MessageStatus.PENDING.value, MessageStatus.DELIVERED.value]
            ),
        )
        return [DynamoDbMessageConverter.from_dict(item) for item in response.get("Items", [])]

    def update_message_status(
        self,
        conversation_id: str,
        message_id: str,
        status: MessageStatus,
    ) -> None:
        self.table.update_item(
            Key={"conversation_id": conversation_id, "message_id": message_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status.value},
        )

