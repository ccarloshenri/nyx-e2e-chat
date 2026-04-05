from abc import ABC, abstractmethod

from src.models.user import User


class IUserDao(ABC):
    @abstractmethod
    def create_user(self, user: User) -> None:
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> User | None:
        pass
