from src.layers.main.nyx.enums import EncryptionType


SEND_MESSAGE_SCHEMA = {
    "type": "object",
    "required": [
        "conversation_id",
        "sender_id",
        "recipient_id",
        "encryption_type",
        "ciphertext",
        "encrypted_message_key",
        "nonce",
        "message_id",
        "created_at",
    ],
    "additionalProperties": False,
    "properties": {
        "conversation_id": {"type": "string", "minLength": 1},
        "sender_id": {"type": "string", "minLength": 1},
        "recipient_id": {"type": "string", "minLength": 1},
        "encryption_type": {
            "type": "string",
            "enum": [encryption_type.value for encryption_type in EncryptionType],
        },
        "ciphertext": {"type": "string", "minLength": 1},
        "encrypted_message_key": {"type": "string", "minLength": 1},
        "nonce": {"type": "string", "minLength": 1},
        "message_id": {"type": "string", "minLength": 1},
        "created_at": {"type": "string", "minLength": 1},
        "metadata": {"type": "object", "additionalProperties": True},
    },
}

ACK_MESSAGE_SCHEMA = {
    "type": "object",
    "required": ["conversation_id", "message_id", "received_at"],
    "additionalProperties": False,
    "properties": {
        "conversation_id": {"type": "string", "minLength": 1},
        "message_id": {"type": "string", "minLength": 1},
        "received_at": {"type": "string", "minLength": 1},
    },
}

FETCH_PENDING_MESSAGES_SCHEMA = {
    "type": "object",
    "required": ["user_id"],
    "additionalProperties": False,
    "properties": {
        "user_id": {"type": "string", "minLength": 1},
    },
}

CREATE_CONVERSATION_SCHEMA = {
    "type": "object",
    "required": ["target_username"],
    "additionalProperties": False,
    "properties": {
        "target_username": {"type": "string", "minLength": 3, "maxLength": 128},
    },
}

