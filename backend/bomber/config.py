from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_KDF_PARAMS = {
    "algorithm": "PBKDF2",
    "iterations": 310000,
    "hash": "SHA-256",
}


@dataclass(slots=True, frozen=True)
class BomberConfig:
    base_url: str
    total_requests: int = 100_000
    concurrency: int = 1_000
    timeout_seconds: float = 10.0
    warmup_requests: int = 0
    progress_interval_seconds: float = 1.0
    user_count: int = 100
    username_prefix: str = "bomber-user"
    master_password_prefix: str = "bomber-master"
    register_missing_users: bool = True
    message_size_bytes: int = 96
    message_path: str = "/messages"
    register_path: str = "/auth/register"
    challenge_path: str = "/auth/challenge"
    login_path: str = "/auth/login"
    conversations_path: str = "/conversations"
    headers: dict[str, str] = field(default_factory=dict)
    users_file: Path | None = None
    export_json_path: Path | None = None
    failure_log_path: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))
        if self.total_requests <= 0:
            raise ValueError("total_requests must be greater than zero")
        if self.concurrency <= 0:
            raise ValueError("concurrency must be greater than zero")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if self.warmup_requests < 0:
            raise ValueError("warmup_requests cannot be negative")
        if self.progress_interval_seconds <= 0:
            raise ValueError("progress_interval_seconds must be greater than zero")
        if self.user_count < 2:
            raise ValueError("user_count must be at least 2")
        if self.message_size_bytes <= 0:
            raise ValueError("message_size_bytes must be greater than zero")

    @classmethod
    def from_cli(
        cls,
        *,
        base_url: str,
        total_requests: int,
        concurrency: int,
        timeout_seconds: float,
        warmup_requests: int,
        progress_interval_seconds: float,
        user_count: int,
        username_prefix: str,
        master_password_prefix: str,
        register_missing_users: bool,
        message_size_bytes: int,
        headers: list[str] | None,
        users_file: str | None,
        export_json_path: str | None,
        failure_log_path: str | None,
    ) -> "BomberConfig":
        return cls(
            base_url=base_url,
            total_requests=total_requests,
            concurrency=concurrency,
            timeout_seconds=timeout_seconds,
            warmup_requests=warmup_requests,
            progress_interval_seconds=progress_interval_seconds,
            user_count=user_count,
            username_prefix=username_prefix,
            master_password_prefix=master_password_prefix,
            register_missing_users=register_missing_users,
            message_size_bytes=message_size_bytes,
            headers=parse_headers(headers or []),
            users_file=Path(users_file) if users_file else None,
            export_json_path=Path(export_json_path) if export_json_path else None,
            failure_log_path=Path(failure_log_path) if failure_log_path else None,
        )


def parse_headers(header_entries: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for entry in header_entries:
        key, separator, value = entry.partition(":")
        if not separator:
            raise ValueError(f"invalid header format: {entry!r}. Expected 'Key: Value'.")
        normalized_key = key.strip()
        if not normalized_key:
            raise ValueError(f"invalid header key in entry: {entry!r}")
        headers[normalized_key] = value.strip()
    return headers


def dump_config(config: BomberConfig) -> dict:
    return json.loads(
        json.dumps(
            {
                "base_url": config.base_url,
                "total_requests": config.total_requests,
                "concurrency": config.concurrency,
                "timeout_seconds": config.timeout_seconds,
                "warmup_requests": config.warmup_requests,
                "progress_interval_seconds": config.progress_interval_seconds,
                "user_count": config.user_count,
                "username_prefix": config.username_prefix,
                "master_password_prefix": config.master_password_prefix,
                "register_missing_users": config.register_missing_users,
                "message_size_bytes": config.message_size_bytes,
                "users_file": str(config.users_file) if config.users_file else None,
                "message_path": config.message_path,
                "register_path": config.register_path,
                "challenge_path": config.challenge_path,
                "login_path": config.login_path,
                "conversations_path": config.conversations_path,
                "headers": config.headers,
            }
        )
    )
