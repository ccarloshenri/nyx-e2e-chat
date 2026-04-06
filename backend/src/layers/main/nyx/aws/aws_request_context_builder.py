from uuid import uuid4

from src.layers.main.nyx.models.request_context import RequestContext


def build_aws_request_context(event: dict) -> RequestContext:
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
