from collections.abc import Callable
from copy import deepcopy

from src.layers.main.nyx.interfaces.messaging.i_queue_publisher import IQueuePublisher
from src.layers.main.nyx.local.in_memory_store import InMemoryStore


class InMemoryQueuePublisher(IQueuePublisher):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store
        self.consumer: Callable[[dict], None] | None = None

    def set_consumer(self, consumer: Callable[[dict], None]) -> None:
        self.consumer = consumer

    def publish(self, payload: dict, deduplication_id: str, group_id: str) -> None:
        envelope = {
            "payload": deepcopy(payload),
            "deduplication_id": deduplication_id,
            "group_id": group_id,
        }
        self.store.published_messages.append(envelope)
        if self.consumer is not None:
            self.consumer(deepcopy(payload))
