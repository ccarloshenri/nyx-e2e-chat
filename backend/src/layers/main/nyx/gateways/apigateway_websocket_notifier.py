import json

from src.layers.main.nyx.interfaces.realtime.i_websocket_notifier import IWebSocketNotifier


class ApiGatewayWebSocketNotifier(IWebSocketNotifier):
    def __init__(self, management_client) -> None:
        self.management_client = management_client

    def notify(self, connection_id: str, payload: dict) -> None:
        self.management_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(payload).encode(),
        )

