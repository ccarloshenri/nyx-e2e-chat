from abc import ABC, abstractmethod


class IQueuePublisher(ABC):
    @abstractmethod
    def publish(self, payload: dict, deduplication_id: str, group_id: str) -> None:
        pass
