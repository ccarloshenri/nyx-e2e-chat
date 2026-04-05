from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.interfaces.services.i_password_hasher import IPasswordHasher
from src.layers.main.nyx.models.conversation import Conversation
from src.layers.main.nyx.models.user import User

LOCAL_PRIMARY_USER_ID = "local-user-1"
LOCAL_SECONDARY_USER_ID = "local-user-2"
LOCAL_PRIMARY_USERNAME = "carlo@nyx.app"
LOCAL_SECONDARY_USERNAME = "lena@nyx.app"
LOCAL_DEFAULT_PASSWORD = "nyx-local-pass"
LOCAL_CONVERSATION_ID = "local-conversation-1"


class LocalDataSeeder:
    def __init__(
        self,
        user_dao: IUserDao,
        conversation_dao: IConversationDao,
        password_hasher: IPasswordHasher,
        clock: IClock,
    ) -> None:
        self.user_dao = user_dao
        self.conversation_dao = conversation_dao
        self.password_hasher = password_hasher
        self.clock = clock

    def seed(self) -> None:
        if self.user_dao.get_user_by_username(LOCAL_PRIMARY_USERNAME) is None:
            self.user_dao.create_user(
                User(
                    user_id=LOCAL_PRIMARY_USER_ID,
                    username=LOCAL_PRIMARY_USERNAME,
                    password_hash=self.password_hasher.hash_password(LOCAL_DEFAULT_PASSWORD),
                    public_key="local-public-key-primary",
                    encrypted_private_key="local-encrypted-private-key-primary",
                    kdf_salt="local-salt-primary",
                    kdf_params={"algorithm": "argon2id", "iterations": 3},
                    created_at=self.clock.now_iso(),
                )
            )

        if self.user_dao.get_user_by_username(LOCAL_SECONDARY_USERNAME) is None:
            self.user_dao.create_user(
                User(
                    user_id=LOCAL_SECONDARY_USER_ID,
                    username=LOCAL_SECONDARY_USERNAME,
                    password_hash=self.password_hasher.hash_password(LOCAL_DEFAULT_PASSWORD),
                    public_key="local-public-key-secondary",
                    encrypted_private_key="local-encrypted-private-key-secondary",
                    kdf_salt="local-salt-secondary",
                    kdf_params={"algorithm": "argon2id", "iterations": 3},
                    created_at=self.clock.now_iso(),
                )
            )

        if self.conversation_dao.get_conversation(LOCAL_CONVERSATION_ID) is None:
            self.conversation_dao.create_conversation(
                Conversation(
                    conversation_id=LOCAL_CONVERSATION_ID,
                    participants=[LOCAL_PRIMARY_USER_ID, LOCAL_SECONDARY_USER_ID],
                    created_at=self.clock.now_iso(),
                )
            )
