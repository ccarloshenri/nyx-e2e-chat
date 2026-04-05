import json

from src.config.settings import settings
from src.layers.main.nyx.interfaces.messaging.i_queue_publisher import IQueuePublisher


class SqsQueuePublisher(IQueuePublisher):
    def __init__(self, sqs_client) -> None:
        self.sqs_client = sqs_client

    def publish(self, payload: dict, deduplication_id: str, group_id: str) -> None:
        self.sqs_client.send_message(
            QueueUrl=settings.message_delivery_queue_url,
            MessageBody=json.dumps(payload),
            MessageDeduplicationId=deduplication_id,
            MessageGroupId=group_id,
        )
