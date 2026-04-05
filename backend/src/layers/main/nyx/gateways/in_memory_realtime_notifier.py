from copy import deepcopy

from src.layers.main.nyx.interfaces.realtime.i_websocket_notifier import IWebSocketNotifier
from src.layers.main.nyx.local.in_memory_store import InMemoryStore


class InMemoryRealtimeNotifier(IWebSocketNotifier):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def notify(self, connection_id: str, payload: dict) -> None:
        notifications = self.store.notifications_by_connection.setdefault(connection_id, [])
        notifications.append(deepcopy(payload))
