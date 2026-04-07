import base64
import hashlib
import hmac
import os

from src.layers.main.nyx.interfaces.services.i_password_hasher import IPasswordHasher
from src.layers.main.nyx.exceptions import AuthenticationError

PBKDF2_ITERATIONS = 210_000


class PasswordHasher(IPasswordHasher):
    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
        return (
            f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
            f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
        )

    def verify_password(self, password: str, encoded_hash: str) -> None:
        try:
            algorithm, iterations, salt_b64, digest_b64 = encoded_hash.split("$", maxsplit=3)
            if algorithm != "pbkdf2_sha256":
                raise ValueError("unsupported hash")
        except ValueError as exc:
            raise AuthenticationError("Invalid stored credentials format") from exc
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            base64.b64decode(salt_b64),
            int(iterations),
        )
        if not hmac.compare_digest(candidate, base64.b64decode(digest_b64)):
            raise AuthenticationError("Invalid username or password")

