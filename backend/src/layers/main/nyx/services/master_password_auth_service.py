import base64
import hashlib
import hmac
import os
from datetime import timedelta

import jwt

from src.layers.main.nyx.config.constants import JWT_ALGORITHM
from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.exceptions import AuthenticationError
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.interfaces.services.i_master_password_auth_service import (
    IMasterPasswordAuthService,
)
from src.layers.main.nyx.models.auth import LoginChallenge

LOGIN_CHALLENGE_TTL_SECONDS = 300


class MasterPasswordAuthService(IMasterPasswordAuthService):
    def __init__(self, clock: IClock) -> None:
        self.clock = clock

    def issue_login_challenge(
        self,
        username: str,
        master_password_salt: str,
        master_password_kdf_params: dict,
    ) -> LoginChallenge:
        now = self.clock.now()
        expires_at = now + timedelta(seconds=LOGIN_CHALLENGE_TTL_SECONDS)
        nonce = base64.b64encode(os.urandom(32)).decode()
        challenge_token = jwt.encode(
            {
                "type": "login_challenge",
                "username": username,
                "nonce": nonce,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            settings.jwt_secret,
            algorithm=JWT_ALGORITHM,
        )
        return LoginChallenge(
            challenge_token=challenge_token,
            master_password_salt=master_password_salt,
            master_password_kdf_params=master_password_kdf_params,
            expires_at=expires_at.isoformat(),
        )

    def verify_login_proof(
        self,
        username: str,
        stored_verifier: str,
        challenge_token: str,
        login_proof: str,
    ) -> None:
        try:
            payload = jwt.decode(challenge_token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired login challenge") from exc

        if payload.get("type") != "login_challenge" or payload.get("username") != username:
            raise AuthenticationError("Invalid login challenge")

        expected_proof = hmac.new(
            stored_verifier.encode(),
            payload["nonce"].encode(),
            hashlib.sha256,
        ).digest()
        expected_proof_b64 = base64.b64encode(expected_proof).decode()
        if not hmac.compare_digest(expected_proof_b64, login_proof):
            raise AuthenticationError("Invalid username or master password")
