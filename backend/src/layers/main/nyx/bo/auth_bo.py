from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.interfaces.services.i_id_generator import IIdGenerator
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.interfaces.services.i_master_password_auth_service import (
    IMasterPasswordAuthService,
)
from src.layers.main.nyx.models.user import User
from src.layers.main.nyx.exceptions import AuthenticationError, ConflictError, NotFoundError
from src.layers.main.nyx.utils.serializers import serialize


class AuthBO:
    """Coordinate registration, challenge issuance, and login token generation."""

    def __init__(
        self,
        user_dao: IUserDao,
        master_password_auth_service: IMasterPasswordAuthService,
        jwt_service: IJwtService,
        id_generator: IIdGenerator,
        clock: IClock,
    ) -> None:
        self.user_dao = user_dao
        self.master_password_auth_service = master_password_auth_service
        self.jwt_service = jwt_service
        self.id_generator = id_generator
        self.clock = clock

    def register_user(self, payload: dict) -> dict:
        """Persist a new user with verifier-based authentication and wrapped key material."""
        existing_user = self.user_dao.get_user_by_username(payload["username"])
        if existing_user is not None:
            raise ConflictError("User already exists")
        user = User(
            user_id=self.id_generator.new_id(),
            username=payload["username"],
            master_password_verifier=payload["master_password_verifier"],
            master_password_salt=payload["master_password_salt"],
            master_password_kdf_params=payload["master_password_kdf_params"],
            secret_wrap_salt=payload["secret_wrap_salt"],
            secret_wrap_kdf_params=payload["secret_wrap_kdf_params"],
            public_key=payload["public_key"],
            encrypted_private_key=payload["encrypted_private_key"],
            private_key_wrap_salt=payload["private_key_wrap_salt"],
            private_key_wrap_kdf_params=payload["private_key_wrap_kdf_params"],
            created_at=self.clock.now_iso(),
        )
        self.user_dao.create_user(user)
        return {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": user.created_at,
        }

    def create_login_challenge(self, username: str) -> dict:
        """Return the challenge payload the browser needs to prove master-password knowledge."""
        user = self.user_dao.get_user_by_username(username)
        if user is None:
            raise AuthenticationError("Invalid username or master password")
        challenge = self.master_password_auth_service.issue_login_challenge(
            username=user.username,
            master_password_salt=user.master_password_salt,
            master_password_kdf_params=user.master_password_kdf_params,
        )
        return serialize(challenge)

    def login(self, payload: dict) -> dict:
        """Verify the login proof and return the authenticated user bundle plus JWT."""
        user = self.user_dao.get_user_by_username(payload["username"])
        if user is None:
            raise AuthenticationError("Invalid username or master password")
        self.master_password_auth_service.verify_login_proof(
            username=user.username,
            stored_verifier=user.master_password_verifier,
            challenge_token=payload["challenge_token"],
            login_proof=payload["login_proof"],
        )
        token = self.jwt_service.generate_access_token(user.user_id, user.username)
        return {
            "token": serialize(token),
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "public_key": user.public_key,
                "encrypted_private_key": user.encrypted_private_key,
                "secret_wrap_salt": user.secret_wrap_salt,
                "secret_wrap_kdf_params": user.secret_wrap_kdf_params,
                "private_key_wrap_salt": user.private_key_wrap_salt,
                "private_key_wrap_kdf_params": user.private_key_wrap_kdf_params,
            },
        }

    def fetch_public_key(self, username: str) -> dict:
        """Fetch the public key needed to encrypt payloads for another user."""
        user = self.user_dao.get_user_by_username(username)
        if user is None:
            raise NotFoundError("User not found")
        return {"user_id": user.user_id, "username": user.username, "public_key": user.public_key}

