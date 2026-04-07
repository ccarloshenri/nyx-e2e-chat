from dataclasses import dataclass


@dataclass(slots=True)
class RequestContext:
    correlation_id: str
    request_id: str | None
    user_id: str | None = None
    connection_id: str | None = None
    message_id: str | None = None
