from dataclasses import asdict

from src.models.connection import Connection


class DynamoDbConnectionConverter:
    @staticmethod
    def to_dict(connection: Connection) -> dict:
        return asdict(connection)

    @staticmethod
    def from_dict(item: dict) -> Connection:
        return Connection(**item)
