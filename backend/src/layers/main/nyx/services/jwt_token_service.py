from datetime import timedelta

import jwt

from src.layers.main.nyx.config.constants import JWT_ALGORITHM
from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.interfaces.services.i_id_generator import IIdGenerator
from src.layers.main.nyx.interfaces.services.i_jwt_service import IJwtService
from src.layers.main.nyx.models.auth import AuthContext, AuthToken
from src.layers.main.nyx.exceptions import AuthenticationError


class JwtTokenService(IJwtService):
    def __init__(self, clock: IClock, id_generator: IIdGenerator) -> None:
        self.clock = clock
        self.id_generator = id_generator

    def generate_access_token(self, user_id: str, username: str) -> AuthToken:
        now = self.clock.now()
        expires_at = now + timedelta(minutes=settings.jwt_exp_minutes)
        token_id = self.id_generator.new_id()
        encoded = jwt.encode(
            {
                "sub": user_id,
                "username": username,
                "jti": token_id,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            settings.jwt_secret,
            algorithm=JWT_ALGORITHM,
        )
        return AuthToken(access_token=encoded, expires_at=expires_at.isoformat())

    def decode_access_token(self, token: str) -> AuthContext:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        return AuthContext(
            user_id=payload["sub"],
            username=payload["username"],
            token_id=payload["jti"],
        )

