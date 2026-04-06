import json
from typing import Any

from src.layers.main.nyx.exceptions import ApplicationError


class AwsResponseFormatter:
    def build_response(self, status_code: int, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body),
        }

    def success_response(self, body: dict[str, Any], status_code: int = 200) -> dict[str, Any]:
        return self.build_response(status_code, {"success": True, "data": body})

    def error_response(
        self,
        error: ApplicationError,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
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
        return self.build_response(error.status_code, payload)
