import boto3

from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.dao.connection_dynamodb_dao import ConnectionDynamoDbDao
from src.layers.main.nyx.dao.connection_in_memory_dao import ConnectionInMemoryDao
from src.layers.main.nyx.dao.conversation_dynamodb_dao import ConversationDynamoDbDao
from src.layers.main.nyx.dao.conversation_in_memory_dao import ConversationInMemoryDao
from src.layers.main.nyx.dao.message_dynamodb_dao import MessageDynamoDbDao
from src.layers.main.nyx.dao.message_in_memory_dao import MessageInMemoryDao
from src.layers.main.nyx.dao.user_dynamodb_dao import UserDynamoDbDao
from src.layers.main.nyx.dao.user_in_memory_dao import UserInMemoryDao
from src.layers.main.nyx.gateways.apigateway_websocket_notifier import ApiGatewayWebSocketNotifier
from src.layers.main.nyx.gateways.in_memory_queue_publisher import InMemoryQueuePublisher
from src.layers.main.nyx.gateways.in_memory_realtime_notifier import InMemoryRealtimeNotifier
from src.layers.main.nyx.gateways.sqs_queue_publisher import SqsQueuePublisher
from src.layers.main.nyx.local.in_memory_store import InMemoryStore


class InfrastructureFactory:
    def __init__(self) -> None:
        self.store = InMemoryStore() if self._uses_mock_infrastructure() else None

    def build_user_dao(self):
        if self._uses_mock_infrastructure():
            return UserInMemoryDao(self.store)

        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        return UserDynamoDbDao(dynamodb)

    def build_connection_dao(self):
        if self._uses_mock_infrastructure():
            return ConnectionInMemoryDao(self.store)

        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        return ConnectionDynamoDbDao(dynamodb)

    def build_conversation_dao(self):
        if self._uses_mock_infrastructure():
            return ConversationInMemoryDao(self.store)

        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        return ConversationDynamoDbDao(dynamodb)

    def build_message_dao(self):
        if self._uses_mock_infrastructure():
            return MessageInMemoryDao(self.store)

        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        return MessageDynamoDbDao(dynamodb)

    def build_queue_publisher(self):
        if self._uses_mock_infrastructure():
            return InMemoryQueuePublisher(self.store)

        sqs = boto3.client("sqs", region_name=settings.aws_region)
        return SqsQueuePublisher(sqs)

    def build_websocket_notifier(self):
        if self._uses_mock_infrastructure():
            return InMemoryRealtimeNotifier(self.store)

        websocket_management_api = boto3.client(
            "apigatewaymanagementapi",
            region_name=settings.aws_region,
            endpoint_url=settings.websocket_management_endpoint,
        )
        return ApiGatewayWebSocketNotifier(websocket_management_api)

    def _uses_mock_infrastructure(self) -> bool:
        return settings.is_local or settings.uses_mock_infra
