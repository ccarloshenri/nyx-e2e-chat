from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.bo.connection_bo import ConnectionBO
from src.layers.main.nyx.bo.conversation_bo import ConversationBO
from src.layers.main.nyx.bo.message_bo import MessageBO
from src.layers.main.nyx.bootstrap.infrastructure_factory import InfrastructureFactory
from src.layers.main.nyx.bootstrap.local_data_seeder import LocalDataSeeder
from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.controllers.auth_controller import AuthController
from src.layers.main.nyx.controllers.conversation_controller import ConversationController
from src.layers.main.nyx.controllers.message_controller import MessageController
from src.layers.main.nyx.controllers.websocket_controller import WebSocketController
from src.layers.main.nyx.gateways.in_memory_queue_publisher import InMemoryQueuePublisher
from src.layers.main.nyx.services.jwt_token_service import JwtTokenService
from src.layers.main.nyx.services.password_hasher import PasswordHasher
from src.layers.main.nyx.services.system_clock import SystemClock
from src.layers.main.nyx.services.uuid_generator import UuidGenerator
from src.layers.main.nyx.validators.request_validator import RequestValidator


class NyxContainer:
    def __init__(self) -> None:
        infrastructure_factory = InfrastructureFactory()

        self.clock = SystemClock()
        self.id_generator = UuidGenerator()
        self.validator = RequestValidator()
        self.password_hasher = PasswordHasher()
        self.jwt_service = JwtTokenService(self.clock, self.id_generator)

        self.user_dao = infrastructure_factory.build_user_dao()
        self.connection_dao = infrastructure_factory.build_connection_dao()
        self.conversation_dao = infrastructure_factory.build_conversation_dao()
        self.message_dao = infrastructure_factory.build_message_dao()

        self.queue_publisher = infrastructure_factory.build_queue_publisher()
        self.websocket_notifier = infrastructure_factory.build_websocket_notifier()

        if settings.is_local or settings.uses_mock_infra:
            LocalDataSeeder(
                user_dao=self.user_dao,
                conversation_dao=self.conversation_dao,
                password_hasher=self.password_hasher,
                clock=self.clock,
            ).seed()

        if isinstance(self.queue_publisher, InMemoryQueuePublisher):
            self.queue_publisher.set_consumer(self._consume_local_message)

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
                message_dao=self.message_dao,
                user_dao=self.user_dao,
            ),
            validator=self.validator,
            jwt_service=self.jwt_service,
        )

    def _consume_local_message(self, payload: dict) -> None:
        message_bo = MessageBO(
            message_dao=self.message_dao,
            connection_dao=self.connection_dao,
            conversation_dao=self.conversation_dao,
            websocket_notifier=self.websocket_notifier,
        )
        message_bo.process_queued_message(payload)

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

