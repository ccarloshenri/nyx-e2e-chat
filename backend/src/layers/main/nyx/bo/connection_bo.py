from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.dao.i_connection_dao import IConnectionDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.models.connection import Connection
from src.layers.main.nyx.utils.serializers import serialize


class ConnectionBO:
    def __init__(self, connection_dao: IConnectionDao, clock: IClock) -> None:
        self.connection_dao = connection_dao
        self.clock = clock

    def register_connection(self, user_id: str, connection_id: str) -> dict:
        now = self.clock.now()
        connection = Connection(
            user_id=user_id,
            connection_id=connection_id,
            connected_at=self.clock.now_iso(),
            ttl=int(now.timestamp()) + settings.connection_ttl_seconds,
        )
        self.connection_dao.upsert_connection(connection)
        return serialize(connection)

    def disconnect(self, connection_id: str) -> None:
        connection = self.connection_dao.get_connection_by_id(connection_id)
        if connection is None:
            return
        self.connection_dao.delete_connection(connection.user_id, connection.connection_id)

    def list_user_connections(self, user_id: str) -> list[Connection]:
        return self.connection_dao.get_connections_by_user(user_id)

