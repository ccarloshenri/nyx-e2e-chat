from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class UserCredentials:
    username: str
    password_hash: str


@dataclass(slots=True)
class UserKeyMaterial:
    public_key: str
    encrypted_private_key: str
    kdf_salt: str
    kdf_params: dict[str, Any]


@dataclass(slots=True)
class User:
    user_id: str
    username: str
    password_hash: str
    public_key: str
    encrypted_private_key: str
    kdf_salt: str
    kdf_params: dict[str, Any]
    created_at: str

