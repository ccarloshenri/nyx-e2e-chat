WEBSOCKET_CONNECT_SCHEMA = {
    "type": "object",
    "required": ["connection_id", "connected_at"],
    "additionalProperties": False,
    "properties": {
        "connection_id": {"type": "string", "minLength": 1},
        "connected_at": {"type": "string", "minLength": 1},
    },
}

WEBSOCKET_DISCONNECT_SCHEMA = {
    "type": "object",
    "required": ["connection_id"],
    "additionalProperties": False,
    "properties": {
        "connection_id": {"type": "string", "minLength": 1},
    },
}

