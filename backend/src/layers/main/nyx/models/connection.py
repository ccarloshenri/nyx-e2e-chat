from dataclasses import dataclass


@dataclass(slots=True)
class Connection:
    user_id: str
    connection_id: str
    connected_at: str
    ttl: int

