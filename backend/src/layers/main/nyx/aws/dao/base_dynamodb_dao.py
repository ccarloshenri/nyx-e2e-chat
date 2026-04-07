from src.layers.main.nyx.utils.logger import create_logger


class BaseDynamoDbDao:
    def __init__(self, table_resource) -> None:
        self.table = table_resource.table
        self.table_name = getattr(self.table, "name", "unknown-table")
        self.logger = create_logger(self.__class__.__module__)

