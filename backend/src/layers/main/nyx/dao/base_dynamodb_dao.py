class BaseDynamoDbDao:
    def __init__(self, table_resource) -> None:
        self.table = table_resource.table

