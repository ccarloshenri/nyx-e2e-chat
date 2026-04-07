import boto3

from src.layers.main.nyx.config.settings import settings


class BaseDynamoDbTable:
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.table = self.dynamodb.Table(table_name)
