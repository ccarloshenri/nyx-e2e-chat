from boto3.resources.base import ServiceResource


class BaseDynamoDbDao:
    def __init__(self, table_name: str, dynamodb: ServiceResource) -> None:
        self.table = dynamodb.Table(table_name)

