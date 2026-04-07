from boto3.dynamodb.conditions import Attr, Key

from src.layers.main.nyx.enums import MessageStatus
from src.layers.main.nyx.aws.dao.base_dynamodb_dao import BaseDynamoDbDao
from src.layers.main.nyx.aws.dao.converters.dynamodb_message_converter import DynamoDbMessageConverter
from src.layers.main.nyx.aws.dao.tables.messages_table import MessagesTable
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.models.message import Message


class MessageDynamoDbDao(BaseDynamoDbDao, IMessageDao):
    def __init__(self, messages_table: MessagesTable | None = None) -> None:
        super().__init__(messages_table or MessagesTable())

    def save_message(self, message: Message) -> None:
        self.logger.info(
            "writing_item_to_dynamodb",
            {
                "table_name": self.table_name,
                "operation": "save_message",
                "conversation_id": message.conversation_id,
                "message_id": message.message_id,
                "user_id": message.sender_id,
            },
        )
        try:
            self.table.put_item(Item=DynamoDbMessageConverter.to_dict(message))
        except Exception:
            self.logger.exception(
                "failed_to_write_item_to_dynamodb",
                {
                    "table_name": self.table_name,
                    "operation": "save_message",
                    "conversation_id": message.conversation_id,
                    "message_id": message.message_id,
                    "user_id": message.sender_id,
                },
            )
            raise
        self.logger.info(
            "item_stored_successfully",
            {
                "table_name": self.table_name,
                "operation": "save_message",
                "conversation_id": message.conversation_id,
                "message_id": message.message_id,
                "user_id": message.sender_id,
            },
        )

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

    def list_messages_for_conversation(self, conversation_id: str) -> list[Message]:
        response = self.table.query(
            KeyConditionExpression=Key("conversation_id").eq(conversation_id),
        )
        return [DynamoDbMessageConverter.from_dict(item) for item in response.get("Items", [])]

    def update_message_status(
        self,
        conversation_id: str,
        message_id: str,
        status: MessageStatus,
    ) -> None:
        self.logger.info(
            "writing_item_to_dynamodb",
            {
                "table_name": self.table_name,
                "operation": "update_message_status",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "status": status.value,
            },
        )
        try:
            self.table.update_item(
                Key={"conversation_id": conversation_id, "message_id": message_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": status.value},
            )
        except Exception:
            self.logger.exception(
                "failed_to_write_item_to_dynamodb",
                {
                    "table_name": self.table_name,
                    "operation": "update_message_status",
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "status": status.value,
                },
            )
            raise
        self.logger.info(
            "item_stored_successfully",
            {
                "table_name": self.table_name,
                "operation": "update_message_status",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "status": status.value,
            },
        )

