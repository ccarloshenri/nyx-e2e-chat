from datetime import datetime
from abc import ABC, abstractmethod


class IClock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass

    @abstractmethod
    def now_iso(self) -> str:
        pass
