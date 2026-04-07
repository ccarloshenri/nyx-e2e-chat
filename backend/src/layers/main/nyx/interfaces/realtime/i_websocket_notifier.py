from abc import ABC, abstractmethod


class IWebSocketNotifier(ABC):
    @abstractmethod
    def notify(self, connection_id: str, payload: dict) -> None:
        pass

