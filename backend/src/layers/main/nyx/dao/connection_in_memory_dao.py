from copy import deepcopy

from src.layers.main.nyx.interfaces.dao.i_connection_dao import IConnectionDao
from src.layers.main.nyx.local.in_memory_store import InMemoryStore
from src.layers.main.nyx.models.connection import Connection


class ConnectionInMemoryDao(IConnectionDao):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def upsert_connection(self, connection: Connection) -> None:
        user_connections = self.store.connections_by_user.setdefault(connection.user_id, {})
        user_connections[connection.connection_id] = deepcopy(connection)

    def delete_connection(self, user_id: str, connection_id: str) -> None:
        user_connections = self.store.connections_by_user.get(user_id, {})
        user_connections.pop(connection_id, None)
        if not user_connections:
            self.store.connections_by_user.pop(user_id, None)

    def get_connections_by_user(self, user_id: str) -> list[Connection]:
        connections = self.store.connections_by_user.get(user_id, {})
        return [deepcopy(connection) for connection in connections.values()]

    def get_connection_by_id(self, connection_id: str) -> Connection | None:
        for connections in self.store.connections_by_user.values():
            connection = connections.get(connection_id)
            if connection is not None:
                return deepcopy(connection)
        return None
