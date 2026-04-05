from copy import deepcopy

from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.local.in_memory_store import InMemoryStore
from src.layers.main.nyx.models.user import User


class UserInMemoryDao(IUserDao):
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def create_user(self, user: User) -> None:
        self.store.users_by_id[user.user_id] = deepcopy(user)
        self.store.usernames_to_user_id[user.username] = user.user_id

    def get_user_by_username(self, username: str) -> User | None:
        user_id = self.store.usernames_to_user_id.get(username)
        if user_id is None:
            return None
        return self.get_user_by_id(user_id)

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.store.clone_user(self.store.users_by_id.get(user_id))
