from dataclasses import dataclass


@dataclass(slots=True)
class AuthToken:
    access_token: str
    expires_at: str


@dataclass(slots=True)
class LoginChallenge:
    challenge_token: str
    master_password_salt: str
    master_password_kdf_params: dict
    expires_at: str


@dataclass(slots=True)
class AuthContext:
    user_id: str
    username: str
    token_id: str

