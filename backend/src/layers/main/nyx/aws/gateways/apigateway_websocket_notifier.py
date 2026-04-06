import json
import boto3

from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.realtime.i_websocket_notifier import IWebSocketNotifier


class ApiGatewayWebSocketNotifier(IWebSocketNotifier):
    def __init__(self, management_client=None) -> None:
        self.management_client = management_client or boto3.client(
            "apigatewaymanagementapi",
            region_name=settings.aws_region,
            endpoint_url=settings.websocket_management_endpoint,
        )

    def notify(self, connection_id: str, payload: dict) -> None:
        self.management_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(payload).encode(),
        )

