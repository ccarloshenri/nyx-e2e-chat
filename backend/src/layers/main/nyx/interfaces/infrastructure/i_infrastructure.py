from abc import ABC, abstractmethod

from src.layers.main.nyx.interfaces.dao.i_connection_dao import IConnectionDao
from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.interfaces.messaging.i_queue_publisher import IQueuePublisher
from src.layers.main.nyx.interfaces.realtime.i_websocket_notifier import IWebSocketNotifier


class IInfrastructure(ABC):
    @abstractmethod
    def get_user_dao(self) -> IUserDao:
        pass

    @abstractmethod
    def get_connection_dao(self) -> IConnectionDao:
        pass

    @abstractmethod
    def get_conversation_dao(self) -> IConversationDao:
        pass

    @abstractmethod
    def get_message_dao(self) -> IMessageDao:
        pass

    @abstractmethod
    def get_queue_publisher(self) -> IQueuePublisher:
        pass

    @abstractmethod
    def get_websocket_notifier(self) -> IWebSocketNotifier:
        pass
