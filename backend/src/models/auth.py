from dataclasses import dataclass


@dataclass(slots=True)
class AuthToken:
    access_token: str
    expires_at: str


@dataclass(slots=True)
class AuthContext:
    user_id: str
    username: str
    token_id: str
