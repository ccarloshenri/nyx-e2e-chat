import json
from typing import Any

from src.layers.main.nyx.exceptions import ApplicationError
from src.layers.main.nyx.utils.serializers import serialize


def to_snake_case(value: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else "_" for character in value)
    compact = "_".join(segment for segment in normalized.split("_") if segment)
    return compact or "unknown_error"


class AwsResponseFormatter:
    def build_response(self, status_code: int, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(serialize(body)),
        }

    def success_response(self, body: dict[str, Any], status_code: int = 200) -> dict[str, Any]:
        return self.build_response(status_code, {"success": True, "data": body})

    def error_response(
        self,
        error: ApplicationError,
    ) -> dict[str, Any]:
        return self.build_response(
            error.status_code,
            {
                "error_code": to_snake_case(error.error_code),
                "error_message": to_snake_case(error.message),
            },
        )
