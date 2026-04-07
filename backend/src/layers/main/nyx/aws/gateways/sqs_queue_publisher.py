import json
import boto3

from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.messaging.i_queue_publisher import IQueuePublisher


class SqsQueuePublisher(IQueuePublisher):
    def __init__(self, sqs_client=None) -> None:
        self.sqs_client = sqs_client or boto3.client("sqs", region_name=settings.aws_region)

    def publish(self, payload: dict, deduplication_id: str, group_id: str) -> None:
        self.sqs_client.send_message(
            QueueUrl=settings.message_delivery_queue_url,
            MessageBody=json.dumps(payload),
            MessageDeduplicationId=deduplication_id,
            MessageGroupId=group_id,
        )

