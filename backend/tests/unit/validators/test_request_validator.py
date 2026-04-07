import pytest

from src.layers.main.nyx.exceptions import ValidationError
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.auth_schemas import REGISTER_USER_SCHEMA


def test_request_validator_accepts_valid_payload():
    validator = RequestValidator()
    payload = {
        "username": "alice",
        "master_password_verifier": "v" * 44,
        "master_password_salt": "salt-value-123456",
        "master_password_kdf_params": {
            "algorithm": "PBKDF2",
            "iterations": 310000,
            "hash": "SHA-256",
        },
        "secret_wrap_salt": "secret-salt-12345",
        "secret_wrap_kdf_params": {
            "algorithm": "PBKDF2",
            "iterations": 310000,
            "hash": "SHA-256",
        },
        "public_key": "a" * 64,
        "encrypted_private_key": "b" * 64,
        "private_key_wrap_salt": "wrap-salt-value1",
        "private_key_wrap_kdf_params": {
            "algorithm": "PBKDF2",
            "iterations": 310000,
            "hash": "SHA-256",
        },
    }

    validator.validate(REGISTER_USER_SCHEMA, payload)


def test_request_validator_raises_structured_error_for_invalid_payload():
    validator = RequestValidator()

    with pytest.raises(ValidationError) as exc:
        validator.validate(REGISTER_USER_SCHEMA, {"username": "ab"})

    assert exc.value.details["field"] == "root"

