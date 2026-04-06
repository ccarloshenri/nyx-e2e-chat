from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.aws.dao.tables.base_dynamodb_table import BaseDynamoDbTable


class MessagesTable(BaseDynamoDbTable):
    def __init__(self) -> None:
        super().__init__(settings.messages_table_name)
