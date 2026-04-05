from abc import ABC, abstractmethod

from src.models.connection import Connection


class IConnectionDao(ABC):
    @abstractmethod
    def upsert_connection(self, connection: Connection) -> None:
        pass

    @abstractmethod
    def delete_connection(self, user_id: str, connection_id: str) -> None:
        pass

    @abstractmethod
    def get_connections_by_user(self, user_id: str) -> list[Connection]:
        pass

    @abstractmethod
    def get_connection_by_id(self, connection_id: str) -> Connection | None:
        pass
