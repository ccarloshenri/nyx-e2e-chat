from abc import ABC, abstractmethod
from typing import Any


class ILogger(ABC):
    @abstractmethod
    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        pass

    @abstractmethod
    def error(self, message: str, context: dict[str, Any] | None = None) -> None:
        pass

    @abstractmethod
    def exception(self, message: str, context: dict[str, Any] | None = None) -> None:
        pass
