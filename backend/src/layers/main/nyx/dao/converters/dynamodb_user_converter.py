from dataclasses import asdict

from src.layers.main.nyx.models.user import User


class DynamoDbUserConverter:
    @staticmethod
    def to_dict(user: User) -> dict:
        return asdict(user)

    @staticmethod
    def from_dict(item: dict) -> User:
        return User(**item)

