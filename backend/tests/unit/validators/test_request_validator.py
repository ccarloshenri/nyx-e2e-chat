import pytest

from src.layers.main.nyx.utils.exceptions import ValidationError
from src.layers.main.nyx.validators.request_validator import RequestValidator
from src.layers.main.nyx.validators.schemas.auth_schemas import REGISTER_USER_SCHEMA


def test_request_validator_accepts_valid_payload():
    validator = RequestValidator()
    payload = {
        "username": "alice",
        "password": "super-secret-password",
        "public_key": "a" * 64,
        "encrypted_private_key": "b" * 64,
        "kdf_salt": "salt-value-123456",
        "kdf_params": {"algorithm": "argon2id", "iterations": 3},
    }

    validator.validate(REGISTER_USER_SCHEMA, payload)


def test_request_validator_raises_structured_error_for_invalid_payload():
    validator = RequestValidator()

    with pytest.raises(ValidationError) as exc:
        validator.validate(REGISTER_USER_SCHEMA, {"username": "ab"})

    assert exc.value.details["field"] == "root"

