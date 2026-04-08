from dataclasses import asdict, fields

from src.layers.main.nyx.models.user import User

USER_FIELDS = {field.name for field in fields(User)}


class DynamoDbUserConverter:
    @staticmethod
    def to_dict(user: User) -> dict:
        return asdict(user)

    @staticmethod
    def from_dict(item: dict) -> User:
        sanitized_item = {key: value for key, value in item.items() if key in USER_FIELDS}
        return User(**sanitized_item)

