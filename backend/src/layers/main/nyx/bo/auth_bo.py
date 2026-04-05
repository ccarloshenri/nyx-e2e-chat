from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.interfaces.services.i_id_generator import IIdGenerator
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.interfaces.services.i_password_hasher import IPasswordHasher
from src.layers.main.nyx.models.user import User
from src.layers.main.nyx.utils.exceptions import AuthenticationError, ConflictError, NotFoundError
from src.layers.main.nyx.utils.serializers import serialize


class AuthBO:
    def __init__(
        self,
        user_dao: IUserDao,
        password_hasher: IPasswordHasher,
        jwt_service: IJwtService,
        id_generator: IIdGenerator,
        clock: IClock,
    ) -> None:
        self.user_dao = user_dao
        self.password_hasher = password_hasher
        self.jwt_service = jwt_service
        self.id_generator = id_generator
        self.clock = clock

    def register_user(self, payload: dict) -> dict:
        existing_user = self.user_dao.get_user_by_username(payload["username"])
        if existing_user is not None:
            raise ConflictError("User already exists")
        user = User(
            user_id=self.id_generator.new_id(),
            username=payload["username"],
            password_hash=self.password_hasher.hash_password(payload["password"]),
            public_key=payload["public_key"],
            encrypted_private_key=payload["encrypted_private_key"],
            kdf_salt=payload["kdf_salt"],
            kdf_params=payload["kdf_params"],
            created_at=self.clock.now_iso(),
        )
        self.user_dao.create_user(user)
        return {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at,
        }

    def login(self, payload: dict) -> dict:
        user = self.user_dao.get_user_by_username(payload["username"])
        if user is None:
            raise AuthenticationError("Invalid username or password")
        self.password_hasher.verify_password(payload["password"], user.password_hash)
        token = self.jwt_service.generate_access_token(user.user_id, user.username)
        return {
            "token": serialize(token),
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "public_key": user.public_key,
                "encrypted_private_key": user.encrypted_private_key,
                "kdf_salt": user.kdf_salt,
                "kdf_params": user.kdf_params,
            },
        }

    def fetch_public_key(self, username: str) -> dict:
        user = self.user_dao.get_user_by_username(username)
        if user is None:
            raise NotFoundError("User not found")
        return {"user_id": user.user_id, "username": user.username, "public_key": user.public_key}

