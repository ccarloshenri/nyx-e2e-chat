from abc import ABC, abstractmethod


class IIdGenerator(ABC):
    @abstractmethod
    def new_id(self) -> str:
        pass

