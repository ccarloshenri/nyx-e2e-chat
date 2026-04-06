from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.dao.tables.base_dynamodb_table import BaseDynamoDbTable


class ConnectionsTable(BaseDynamoDbTable):
    def __init__(self) -> None:
        super().__init__(settings.connections_table_name)
