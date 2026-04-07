import json
from time import perf_counter
import boto3

from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.messaging.i_queue_publisher import IQueuePublisher
from src.layers.main.nyx.utils.logger import create_logger

logger = create_logger(__name__)


class SqsQueuePublisher(IQueuePublisher):
    def __init__(self, sqs_client=None) -> None:
        self.sqs_client = sqs_client or boto3.client("sqs", region_name=settings.aws_region)

    def publish(self, payload: dict, deduplication_id: str, group_id: str) -> None:
        queue_name = settings.message_delivery_queue_url.rsplit("/", maxsplit=1)[-1]
        started_at = perf_counter()
        logger.info(
            "sending_message_to_queue",
            {
                "queue_name": queue_name,
                "message_id": payload.get("message_id"),
                "conversation_id": payload.get("conversation_id"),
                "user_id": payload.get("sender_id"),
            },
        )
        self.sqs_client.send_message(
            QueueUrl=settings.message_delivery_queue_url,
            MessageBody=json.dumps(payload),
            MessageDeduplicationId=deduplication_id,
            MessageGroupId=group_id,
        )
        logger.info(
            "message_enqueued_successfully",
            {
                "queue_name": queue_name,
                "message_id": payload.get("message_id"),
                "conversation_id": payload.get("conversation_id"),
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )

