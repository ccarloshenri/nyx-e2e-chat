import json
from time import perf_counter
import boto3

from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.realtime.i_websocket_notifier import IWebSocketNotifier
from src.layers.main.nyx.utils.logger import create_logger

logger = create_logger(__name__)


class ApiGatewayWebSocketNotifier(IWebSocketNotifier):
    def __init__(self, management_client=None) -> None:
        self.management_client = management_client or boto3.client(
            "apigatewaymanagementapi",
            region_name=settings.aws_region,
            endpoint_url=settings.websocket_management_endpoint,
        )

    def notify(self, connection_id: str, payload: dict) -> None:
        started_at = perf_counter()
        logger.info(
            "sending_message_to_active_connection",
            {
                "connection_id": connection_id,
                "websocket_action": payload.get("action"),
            },
        )
        self.management_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(payload).encode(),
        )
        logger.info(
            "websocket_delivery_succeeded",
            {
                "connection_id": connection_id,
                "websocket_action": payload.get("action"),
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )

