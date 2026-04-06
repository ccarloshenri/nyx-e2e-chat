from src.layers.main.nyx.dao.connection_dynamodb_dao import ConnectionDynamoDbDao
from src.layers.main.nyx.dao.conversation_dynamodb_dao import ConversationDynamoDbDao
from src.layers.main.nyx.dao.message_dynamodb_dao import MessageDynamoDbDao
from src.layers.main.nyx.dao.user_dynamodb_dao import UserDynamoDbDao
from src.layers.main.nyx.gateways.apigateway_websocket_notifier import ApiGatewayWebSocketNotifier
from src.layers.main.nyx.gateways.sqs_queue_publisher import SqsQueuePublisher
from src.layers.main.nyx.interfaces.infrastructure.i_infrastructure import IInfrastructure


class AwsInfrastructure(IInfrastructure):
    def get_user_dao(self) -> UserDynamoDbDao:
        return UserDynamoDbDao()

    def get_connection_dao(self) -> ConnectionDynamoDbDao:
        return ConnectionDynamoDbDao()

    def get_conversation_dao(self) -> ConversationDynamoDbDao:
        return ConversationDynamoDbDao()

    def get_message_dao(self) -> MessageDynamoDbDao:
        return MessageDynamoDbDao()

    def get_queue_publisher(self) -> SqsQueuePublisher:
        return SqsQueuePublisher()

    def get_websocket_notifier(self) -> ApiGatewayWebSocketNotifier:
        return ApiGatewayWebSocketNotifier()
