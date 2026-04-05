from unittest.mock import MagicMock

import pytest

from src.bo.auth_bo import AuthBO
from src.models.auth import AuthToken
from src.models.user import User
from src.utils.exceptions import AuthenticationError


def test_register_user_returns_public_metadata():
    user_dao = MagicMock()
    password_hasher = MagicMock()
    password_hasher.hash_password.return_value = "hashed-password"
    jwt_service = MagicMock()
    id_generator = MagicMock()
    id_generator.new_id.return_value = "user-1"
    clock = MagicMock()
    clock.now_iso.return_value = "2026-01-01T00:00:00+00:00"
    bo = AuthBO(user_dao, password_hasher, jwt_service, id_generator, clock)

    result = bo.register_user(
        {
            "username": "alice",
            "password": "super-secret-password",
            "public_key": "a" * 64,
            "encrypted_private_key": "b" * 64,
            "kdf_salt": "salt-value-123456",
            "kdf_params": {"algorithm": "argon2id", "iterations": 3},
        }
    )

    assert result["username"] == "alice"
    user_dao.create_user.assert_called_once()


def test_login_rejects_invalid_password():
    user_dao = MagicMock()
    password_hasher = MagicMock()
    password_hasher.verify_password.side_effect = AuthenticationError("Invalid username or password")
    jwt_service = MagicMock()
    jwt_service.generate_access_token.return_value = AuthToken("token", "2026-01-02T00:00:00+00:00")
    id_generator = MagicMock()
    clock = MagicMock()
    user_dao.get_user_by_username.return_value = User(
        user_id="user-1",
        username="alice",
        password_hash="pbkdf2_sha256$210000$c2FsdHZhbHVlMTIzNDU2Nw==$ZGlnZXN0dmFsdWUxMjM0NTY3ODkwMTIzNDU2Nw==",
        public_key="pk",
        encrypted_private_key="enc",
        kdf_salt="salt",
        kdf_params={"algorithm": "argon2id", "iterations": 3},
        created_at="2026-01-01T00:00:00+00:00",
    )
    bo = AuthBO(user_dao, password_hasher, jwt_service, id_generator, clock)

    with pytest.raises(AuthenticationError):
        bo.login({"username": "alice", "password": "wrong-password"})
