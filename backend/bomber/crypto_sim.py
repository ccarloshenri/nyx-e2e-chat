from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

from .config import DEFAULT_KDF_PARAMS


def random_b64(size_bytes: int) -> str:
    return base64.b64encode(os.urandom(size_bytes)).decode("ascii")


def derive_verifier(master_password: str, salt_b64: str, iterations: int) -> str:
    salt = base64.b64decode(salt_b64)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        iterations,
        dklen=32,
    )
    return base64.b64encode(hashlib.sha256(derived).digest()).decode("ascii")


def decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("invalid JWT challenge token")
    payload = parts[1]
    normalized = payload.replace("-", "+").replace("_", "/")
    padded = normalized + "=" * (-len(normalized) % 4)
    return json.loads(base64.b64decode(padded).decode("utf-8"))


def create_login_proof(
    *,
    master_password: str,
    challenge_token: str,
    master_password_salt: str,
    master_password_kdf_params: dict[str, Any],
) -> str:
    payload = decode_jwt_payload(challenge_token)
    nonce = str(payload.get("nonce", ""))
    if not nonce:
        raise ValueError("challenge token nonce is missing")
    verifier = derive_verifier(
        master_password,
        master_password_salt,
        int(master_password_kdf_params.get("iterations", DEFAULT_KDF_PARAMS["iterations"])),
    )
    digest = hmac.new(
        verifier.encode("utf-8"),
        nonce.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def build_registration_payload(username: str, master_password: str) -> dict[str, Any]:
    auth_salt = random_b64(16)
    verifier = derive_verifier(master_password, auth_salt, DEFAULT_KDF_PARAMS["iterations"])
    return {
        "username": username,
        "master_password_verifier": verifier,
        "master_password_salt": auth_salt,
        "master_password_kdf_params": DEFAULT_KDF_PARAMS,
        "secret_wrap_salt": random_b64(16),
        "secret_wrap_kdf_params": {
            **DEFAULT_KDF_PARAMS,
            "encryption": "AES-GCM",
            "key_length": 256,
        },
        "public_key": random_b64(256),
        "encrypted_private_key": json.dumps(
            {
                "algorithm": "AES-GCM",
                "iv": random_b64(12),
                "ciphertext": random_b64(256),
            }
        ),
        "private_key_wrap_salt": random_b64(16),
        "private_key_wrap_kdf_params": {
            **DEFAULT_KDF_PARAMS,
            "encryption": "AES-GCM",
            "key_length": 256,
        },
    }


def build_conversation_payload(target_username: str) -> dict[str, Any]:
    return {
        "target_username": target_username,
        "conversation_password_salt": random_b64(16),
        "conversation_password_kdf_params": DEFAULT_KDF_PARAMS,
        "unlock_check_ciphertext": random_b64(48),
        "unlock_check_nonce": random_b64(12),
        "creator_access": {
            "encrypted_conversation_password": random_b64(48),
            "nonce": random_b64(12),
        },
    }


def build_message_payload(
    *,
    conversation_id: str,
    sender_id: str,
    recipient_id: str,
    request_id: int,
    message_size_bytes: int,
) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "encryption_type": "AES_GCM_CONVERSATION_V1",
        "ciphertext": random_b64(message_size_bytes),
        "encrypted_message_key": "",
        "nonce": random_b64(12),
        "message_id": f"bomber-msg-{request_id}",
        "created_at": iso_now(),
        "metadata": {
            "source": "backend-bomber",
            "request_id": request_id,
        },
    }


def iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
