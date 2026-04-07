from boto3.dynamodb.conditions import Key

from src.layers.main.nyx.aws.dao.base_dynamodb_dao import BaseDynamoDbDao
from src.layers.main.nyx.aws.dao.converters.dynamodb_user_converter import DynamoDbUserConverter
from src.layers.main.nyx.aws.dao.tables.users_table import UsersTable
from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.models.user import User


class UserDynamoDbDao(BaseDynamoDbDao, IUserDao):
    def __init__(self, users_table: UsersTable | None = None) -> None:
        super().__init__(users_table or UsersTable())

    def create_user(self, user: User) -> None:
        self.logger.info(
            "writing_item_to_dynamodb",
            {"table_name": self.table_name, "operation": "create_user", "user_id": user.user_id},
        )
        try:
            self.table.put_item(
                Item=DynamoDbUserConverter.to_dict(user),
                ConditionExpression="attribute_not_exists(user_id)",
            )
        except Exception:
            self.logger.exception(
                "failed_to_write_item_to_dynamodb",
                {"table_name": self.table_name, "operation": "create_user", "user_id": user.user_id},
            )
            raise
        self.logger.info(
            "item_stored_successfully",
            {"table_name": self.table_name, "operation": "create_user", "user_id": user.user_id},
        )

    def get_user_by_username(self, username: str) -> User | None:
        response = self.table.query(
            IndexName="username-index",
            KeyConditionExpression=Key("username").eq(username),
            Limit=1,
        )
        items = response.get("Items", [])
        return DynamoDbUserConverter.from_dict(items[0]) if items else None

    def get_user_by_id(self, user_id: str) -> User | None:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item")
        return DynamoDbUserConverter.from_dict(item) if item else None

