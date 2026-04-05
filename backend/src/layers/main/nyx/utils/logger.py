import json
import logging
from typing import Any

from src.layers.main.nyx.config.settings import settings

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "ciphertext",
    "encrypted_private_key",
    "encrypted_message_key",
    "public_key",
    "token",
    "access_token",
}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("***" if key in SENSITIVE_KEYS else _sanitize(inner))
            for key, inner in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context") and isinstance(record.context, dict):
            payload.update(_sanitize(record.context))
        return json.dumps(payload, default=str)

def _configure_logger(name: str) -> logging.Logger:
    configured_logger = logging.getLogger(name)
    if configured_logger.handlers:
        return configured_logger
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    configured_logger.addHandler(handler)
    configured_logger.setLevel(settings.log_level)
    configured_logger.propagate = False
    return configured_logger


logger = _configure_logger(settings.service_name)


def get_module_logger(name: str) -> logging.Logger:
    return _configure_logger(name)

