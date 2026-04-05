import boto3

from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.bo.connection_bo import ConnectionBO
from src.layers.main.nyx.bo.conversation_bo import ConversationBO
from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.controllers.auth_controller import AuthController
from src.layers.main.nyx.controllers.conversation_controller import ConversationController
from src.layers.main.nyx.controllers.message_controller import MessageController
from src.layers.main.nyx.controllers.websocket_controller import WebSocketController
from src.layers.main.nyx.dao.connection_dynamodb_dao import ConnectionDynamoDbDao
from src.layers.main.nyx.dao.conversation_dynamodb_dao import ConversationDynamoDbDao
from src.layers.main.nyx.dao.message_dynamodb_dao import MessageDynamoDbDao
from src.layers.main.nyx.dao.user_dynamodb_dao import UserDynamoDbDao
from src.layers.main.nyx.gateways.apigateway_websocket_notifier import ApiGatewayWebSocketNotifier
from src.layers.main.nyx.gateways.sqs_queue_publisher import SqsQueuePublisher
from src.layers.main.nyx.services.jwt_token_service import JwtTokenService
from src.layers.main.nyx.services.password_hasher import PasswordHasher
from src.layers.main.nyx.services.system_clock import SystemClock
from src.layers.main.nyx.services.uuid_generator import UuidGenerator
from src.layers.main.nyx.validators.request_validator import RequestValidator


class NyxContainer:
    def __init__(self) -> None:
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        sqs = boto3.client("sqs", region_name=settings.aws_region)
        websocket_management_api = boto3.client(
            "apigatewaymanagementapi",
            region_name=settings.aws_region,
            endpoint_url=settings.websocket_management_endpoint,
        )

        self.clock = SystemClock()
        self.id_generator = UuidGenerator()
        self.validator = RequestValidator()
        self.password_hasher = PasswordHasher()
        self.jwt_service = JwtTokenService(self.clock, self.id_generator)

        self.user_dao = UserDynamoDbDao(dynamodb)
        self.connection_dao = ConnectionDynamoDbDao(dynamodb)
        self.conversation_dao = ConversationDynamoDbDao(dynamodb)
        self.message_dao = MessageDynamoDbDao(dynamodb)

        self.queue_publisher = SqsQueuePublisher(sqs)
        self.websocket_notifier = ApiGatewayWebSocketNotifier(websocket_management_api)

    def get_auth_controller(self) -> AuthController:
        return AuthController(
            AuthBO(
                user_dao=self.user_dao,
                password_hasher=self.password_hasher,
                jwt_service=self.jwt_service,
                id_generator=self.id_generator,
                clock=self.clock,
            ),
            validator=self.validator,
        )

    def get_websocket_controller(self) -> WebSocketController:
        return WebSocketController(
            connection_bo=ConnectionBO(connection_dao=self.connection_dao, clock=self.clock),
            validator=self.validator,
            jwt_service=self.jwt_service,
        )

    def get_message_controller(self) -> MessageController:
        return MessageController(
            message_bo=MessageBO(
                message_dao=self.message_dao,
                connection_dao=self.connection_dao,
                conversation_dao=self.conversation_dao,
                queue_publisher=self.queue_publisher,
                websocket_notifier=self.websocket_notifier,
            ),
            validator=self.validator,
            jwt_service=self.jwt_service,
        )

    def get_conversation_controller(self) -> ConversationController:
        return ConversationController(
            conversation_bo=ConversationBO(
                conversation_dao=self.conversation_dao,
                clock=self.clock,
            ),
            validator=self.validator,
        )

_container: NyxContainer | None = None


def get_container() -> NyxContainer:
    global _container
    if _container is None:
        _container = NyxContainer()
    return _container


def build_auth_controller() -> AuthController:
    return get_container().get_auth_controller()


def build_websocket_controller() -> WebSocketController:
    return get_container().get_websocket_controller()


def build_message_controller() -> MessageController:
    return get_container().get_message_controller()


def build_conversation_controller() -> ConversationController:
    return get_container().get_conversation_controller()

