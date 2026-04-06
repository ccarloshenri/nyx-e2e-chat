from boto3.dynamodb.conditions import Key

from src.layers.main.nyx.dao.base_dynamodb_dao import BaseDynamoDbDao
from src.layers.main.nyx.dao.converters.dynamodb_connection_converter import (
    DynamoDbConnectionConverter,
)
from src.layers.main.nyx.dao.tables.connections_table import ConnectionsTable
from src.layers.main.nyx.interfaces.dao.i_connection_dao import IConnectionDao
from src.layers.main.nyx.models.connection import Connection


class ConnectionDynamoDbDao(BaseDynamoDbDao, IConnectionDao):
    def __init__(self, connections_table: ConnectionsTable | None = None) -> None:
        super().__init__(connections_table or ConnectionsTable())

    def upsert_connection(self, connection: Connection) -> None:
        self.table.put_item(Item=DynamoDbConnectionConverter.to_dict(connection))

    def delete_connection(self, user_id: str, connection_id: str) -> None:
        self.table.delete_item(Key={"user_id": user_id, "connection_id": connection_id})

    def get_connections_by_user(self, user_id: str) -> list[Connection]:
        response = self.table.query(KeyConditionExpression=Key("user_id").eq(user_id))
        return [DynamoDbConnectionConverter.from_dict(item) for item in response.get("Items", [])]

    def get_connection_by_id(self, connection_id: str) -> Connection | None:
        response = self.table.query(
            IndexName="connection-id-index",
            KeyConditionExpression=Key("connection_id").eq(connection_id),
            Limit=1,
        )
        items = response.get("Items", [])
        return DynamoDbConnectionConverter.from_dict(items[0]) if items else None

