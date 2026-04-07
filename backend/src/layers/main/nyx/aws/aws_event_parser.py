import json
from typing import Any

from src.layers.main.nyx.exceptions import ValidationError


def parse_aws_json_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValidationError("Request body must be valid JSON") from exc


def extract_aws_bearer_token(
    headers: dict[str, Any] | None,
    query: dict[str, Any] | None = None,
) -> str:
    headers = headers or {}
    query = query or {}
    authorization = (
        headers.get("Authorization")
        or headers.get("authorization")
        or query.get("token")
        or query.get("authorization")
    )
    if not authorization:
        raise ValidationError("Authorization token is required")
    return authorization.removeprefix("Bearer ").strip()
