from unittest.mock import MagicMock

import pytest

from src.layers.main.nyx.bo.auth_bo import AuthBO
from src.layers.main.nyx.exceptions import AuthenticationError, ConflictError, NotFoundError
from src.layers.main.nyx.models.auth import AuthToken
from src.layers.main.nyx.models.user import User


def build_user() -> User:
    return User(
        user_id="user-1",
        username="alice",
        master_password_verifier="verifier",
        master_password_salt="salt",
        master_password_kdf_params={"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
        secret_wrap_salt="secret-salt",
        secret_wrap_kdf_params={"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
        public_key="pk",
        encrypted_private_key="enc",
        private_key_wrap_salt="wrap-salt",
        private_key_wrap_kdf_params={"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_register_user_returns_public_metadata():
    user_dao = MagicMock()
    user_dao.get_user_by_username.return_value = None
    master_password_auth_service = MagicMock()
    jwt_service = MagicMock()
    id_generator = MagicMock()
    id_generator.new_id.return_value = "user-1"
    clock = MagicMock()
    clock.now_iso.return_value = "2026-01-01T00:00:00+00:00"
    bo = AuthBO(user_dao, master_password_auth_service, jwt_service, id_generator, clock)

    result = bo.register_user(
        {
            "username": "alice",
            "master_password_verifier": "verifier",
            "master_password_salt": "salt",
            "master_password_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
            "secret_wrap_salt": "secret-salt",
            "secret_wrap_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
            "public_key": "a" * 64,
            "encrypted_private_key": "b" * 64,
            "private_key_wrap_salt": "wrap-salt",
            "private_key_wrap_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
        }
    )

    assert result["username"] == "alice"
    user_dao.create_user.assert_called_once()


def test_create_login_challenge_uses_stored_master_password_metadata():
    user_dao = MagicMock()
    user_dao.get_user_by_username.return_value = build_user()
    master_password_auth_service = MagicMock()
    master_password_auth_service.issue_login_challenge.return_value = {
        "challenge_token": "token",
        "master_password_salt": "salt",
        "master_password_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
        "expires_at": "2026-01-01T01:00:00+00:00",
    }
    bo = AuthBO(user_dao, master_password_auth_service, MagicMock(), MagicMock(), MagicMock())

    result = bo.create_login_challenge("alice")

    assert result["challenge_token"] == "token"


def test_login_rejects_invalid_master_password_proof():
    user_dao = MagicMock()
    user_dao.get_user_by_username.return_value = build_user()
    master_password_auth_service = MagicMock()
    master_password_auth_service.verify_login_proof.side_effect = AuthenticationError(
        "Invalid username or master password"
    )
    jwt_service = MagicMock()
    jwt_service.generate_access_token.return_value = AuthToken("token", "2026-01-02T00:00:00+00:00")
    bo = AuthBO(user_dao, master_password_auth_service, jwt_service, MagicMock(), MagicMock())

    with pytest.raises(AuthenticationError):
        bo.login({"username": "alice", "challenge_token": "token", "login_proof": "proof"})


def test_register_user_rejects_existing_username():
    user_dao = MagicMock()
    user_dao.get_user_by_username.return_value = MagicMock()
    bo = AuthBO(user_dao, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(ConflictError):
        bo.register_user(
            {
                "username": "alice",
                "master_password_verifier": "verifier",
                "master_password_salt": "salt",
                "master_password_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
                "secret_wrap_salt": "secret-salt",
                "secret_wrap_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
                "public_key": "a" * 64,
                "encrypted_private_key": "b" * 64,
                "private_key_wrap_salt": "wrap-salt",
                "private_key_wrap_kdf_params": {"algorithm": "PBKDF2", "iterations": 1, "hash": "SHA-256"},
            }
        )


def test_login_returns_token_and_user_crypto_material():
    user_dao = MagicMock()
    master_password_auth_service = MagicMock()
    jwt_service = MagicMock()
    jwt_service.generate_access_token.return_value = AuthToken(
        access_token="token-123",
        expires_at="2026-01-02T00:00:00+00:00",
    )
    user_dao.get_user_by_username.return_value = build_user()
    bo = AuthBO(user_dao, master_password_auth_service, jwt_service, MagicMock(), MagicMock())

    result = bo.login({"username": "alice", "challenge_token": "token", "login_proof": "proof"})

    master_password_auth_service.verify_login_proof.assert_called_once_with(
        username="alice",
        stored_verifier="verifier",
        challenge_token="token",
        login_proof="proof",
    )
    jwt_service.generate_access_token.assert_called_once_with("user-1", "alice")
    assert result["token"]["access_token"] == "token-123"
    assert result["user"]["encrypted_private_key"] == "enc"
    assert result["user"]["secret_wrap_salt"] == "secret-salt"


def test_fetch_public_key_returns_expected_payload():
    user_dao = MagicMock()
    user_dao.get_user_by_username.return_value = build_user()
    bo = AuthBO(user_dao, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    result = bo.fetch_public_key("alice")

    assert result == {"user_id": "user-1", "username": "alice", "public_key": "pk"}


def test_fetch_public_key_raises_when_user_missing():
    user_dao = MagicMock()
    user_dao.get_user_by_username.return_value = None
    bo = AuthBO(user_dao, MagicMock(), MagicMock(), MagicMock(), MagicMock())

    with pytest.raises(NotFoundError):
        bo.fetch_public_key("alice")
