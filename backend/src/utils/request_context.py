from dataclasses import dataclass
from uuid import uuid4


@dataclass(slots=True)
class RequestContext:
    correlation_id: str
    request_id: str | None
    user_id: str | None = None
    connection_id: str | None = None
    message_id: str | None = None


def build_request_context(event: dict) -> RequestContext:
    request_context = event.get("requestContext", {}) if isinstance(event, dict) else {}
    headers = event.get("headers", {}) if isinstance(event, dict) else {}
    correlation_id = (
        headers.get("x-correlation-id")
        or headers.get("X-Correlation-Id")
        or request_context.get("requestId")
        or str(uuid4())
    )
    return RequestContext(
        correlation_id=correlation_id,
        request_id=request_context.get("requestId"),
        connection_id=request_context.get("connectionId"),
    )
