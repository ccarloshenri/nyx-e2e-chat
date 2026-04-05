import json
from typing import Any

from src.utils.exceptions import ApplicationError


def build_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def success_response(body: dict[str, Any], status_code: int = 200) -> dict[str, Any]:
    return build_response(status_code, {"success": True, "data": body})


def error_response(error: ApplicationError, correlation_id: str | None = None) -> dict[str, Any]:
    payload = {
        "success": False,
        "error": {
            "code": error.error_code,
            "message": error.message,
            "details": error.details,
        },
    }
    if correlation_id:
        payload["correlation_id"] = correlation_id
    return build_response(error.status_code, payload)
