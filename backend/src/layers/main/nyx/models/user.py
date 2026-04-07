from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class UserCredentials:
    username: str
    master_password_verifier: str


@dataclass(slots=True)
class UserKeyMaterial:
    public_key: str
    encrypted_private_key: str
    private_key_wrap_salt: str
    private_key_wrap_kdf_params: dict[str, Any]


@dataclass(slots=True)
class User:
    user_id: str
    username: str
    master_password_verifier: str
    master_password_salt: str
    master_password_kdf_params: dict[str, Any]
    secret_wrap_salt: str
    secret_wrap_kdf_params: dict[str, Any]
    public_key: str
    encrypted_private_key: str
    private_key_wrap_salt: str
    private_key_wrap_kdf_params: dict[str, Any]
    created_at: str

