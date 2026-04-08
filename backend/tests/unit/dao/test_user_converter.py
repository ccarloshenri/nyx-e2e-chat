from src.layers.main.nyx.aws.dao.converters.dynamodb_user_converter import (
    DynamoDbUserConverter,
)


def test_from_dict_ignores_legacy_user_fields_not_present_in_model():
    user = DynamoDbUserConverter.from_dict(
        {
            "user_id": "user-1",
            "username": "alice",
            "master_password_verifier": "verifier",
            "master_password_salt": "master-salt",
            "master_password_kdf_params": {
                "algorithm": "PBKDF2",
                "iterations": 1,
                "hash": "SHA-256",
            },
            "secret_wrap_salt": "secret-salt",
            "secret_wrap_kdf_params": {
                "algorithm": "PBKDF2",
                "iterations": 1,
                "hash": "SHA-256",
            },
            "public_key": "public-key",
            "encrypted_private_key": "encrypted-private-key",
            "private_key_wrap_salt": "wrap-salt",
            "private_key_wrap_kdf_params": {
                "algorithm": "PBKDF2",
                "iterations": 1,
                "hash": "SHA-256",
            },
            "created_at": "2026-01-01T00:00:00+00:00",
            "kdf_salt": "legacy-salt",
            "kdf_params": {"algorithm": "PBKDF2"},
            "password_hash": "legacy-password-hash",
        }
    )

    assert user.user_id == "user-1"
    assert user.username == "alice"
    assert user.master_password_verifier == "verifier"
