import json
import logging
import traceback
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

from src.layers.main.nyx.config.settings import settings
from src.layers.main.nyx.interfaces.services.i_logger import ILogger

_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("nyx_log_context", default={})

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "master_password_verifier",
    "master_password_salt",
    "master_password_kdf_params",
    "secret_wrap_salt",
    "secret_wrap_kdf_params",
    "private_key_wrap_salt",
    "private_key_wrap_kdf_params",
    "encrypted_conversation_password",
    "conversation_password",
    "conversation_password_salt",
    "conversation_password_kdf_params",
    "unlock_check_ciphertext",
    "unlock_check_nonce",
    "challenge_token",
    "login_proof",
    "ciphertext",
    "encrypted_private_key",
    "encrypted_message_key",
    "public_key",
    "token",
    "access_token",
}

LEVEL_MAPPING = {
    "WARNING": "WARN",
}


def bind_log_context(context: dict[str, Any] | None = None) -> Token:
    """Merge request-scoped fields into the active logging context."""
    merged_context = {**_LOG_CONTEXT.get({}), **(context or {})}
    return _LOG_CONTEXT.set(merged_context)


def reset_log_context(token: Token) -> None:
    """Restore the previous logging context after the current scope finishes."""
    _LOG_CONTEXT.reset(token)


def get_log_context() -> dict[str, Any]:
    """Return a copy of the currently bound structured logging context."""
    return dict(_LOG_CONTEXT.get({}))


def _sanitize(value: Any) -> Any:
    """Redact sensitive values before they reach log serialization."""
    if isinstance(value, dict):
        return {
            key: ("***" if key in SENSITIVE_KEYS else _sanitize(inner))
            for key, inner in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    """Serialize application logs into a CloudWatch-friendly JSON document."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": LEVEL_MAPPING.get(record.levelname, record.levelname),
            "service": settings.service_name,
            "component": record.name,
            "message": record.getMessage(),
        }
        combined_context = {
            **get_log_context(),
            **(record.context if hasattr(record, "context") and isinstance(record.context, dict) else {}),
        }
        if combined_context:
            payload.update(_sanitize(combined_context))
        if record.exc_info:
            exception_type, exception, _ = record.exc_info
            payload["exception_type"] = getattr(exception_type, "__name__", "UnknownException")
            payload["exception_message"] = str(exception)
            payload["stack_trace"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, default=str)


def _configure_logger(name: str) -> logging.Logger:
    """Create or reuse a logger configured with the project JSON formatter."""
    configured_logger = logging.getLogger(name)
    if configured_logger.handlers:
        return configured_logger
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    configured_logger.addHandler(handler)
    configured_logger.setLevel(settings.log_level)
    configured_logger.propagate = False
    return configured_logger


class StructuredLogger(ILogger):
    """Thin adapter that exposes the project logging interface over stdlib logging."""

    def __init__(self, logger_name: str) -> None:
        self._logger = _configure_logger(logger_name)

    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        self._logger.info(message, extra={"context": context or {}})

    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        self._logger.warning(message, extra={"context": context or {}})

    def error(self, message: str, context: dict[str, Any] | None = None) -> None:
        self._logger.error(message, extra={"context": context or {}})

    def exception(self, message: str, context: dict[str, Any] | None = None) -> None:
        self._logger.exception(message, extra={"context": context or {}})


def create_logger(name: str | None = None) -> ILogger:
    """Build a structured logger for a component or fall back to the service name."""
    return StructuredLogger(name or settings.service_name)

