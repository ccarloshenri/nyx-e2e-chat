from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.layers.main.nyx.bo.connection_bo import ConnectionBO
from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.models.connection import Connection


def test_register_connection_persists_connection_with_ttl():
    connection_dao = MagicMock()
    clock = MagicMock()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock.now.return_value = now
    clock.now_iso.return_value = "2026-01-01T00:00:00+00:00"
    bo = ConnectionBO(connection_dao=connection_dao, clock=clock)

    result = bo.register_connection("user-1", "conn-1")

    saved_connection = connection_dao.upsert_connection.call_args.args[0]
    assert saved_connection.user_id == "user-1"
    assert saved_connection.connection_id == "conn-1"
    assert saved_connection.ttl == int(now.timestamp()) + settings.connection_ttl_seconds
    assert result["connection_id"] == "conn-1"


def test_disconnect_ignores_missing_connection():
    connection_dao = MagicMock()
    connection_dao.get_connection_by_id.return_value = None
    bo = ConnectionBO(connection_dao=connection_dao, clock=MagicMock())

    bo.disconnect("conn-1")

    connection_dao.delete_connection.assert_not_called()


def test_disconnect_deletes_existing_connection():
    connection_dao = MagicMock()
    connection_dao.get_connection_by_id.return_value = Connection(
        user_id="user-1",
        connection_id="conn-1",
        connected_at="2026-01-01T00:00:00+00:00",
        ttl=123,
    )
    bo = ConnectionBO(connection_dao=connection_dao, clock=MagicMock())

    bo.disconnect("conn-1")

    connection_dao.delete_connection.assert_called_once_with("user-1", "conn-1")
