from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.aws.dao.tables.base_dynamodb_table import BaseDynamoDbTable


class ConversationsTable(BaseDynamoDbTable):
    def __init__(self) -> None:
        super().__init__(settings.conversations_table_name)
