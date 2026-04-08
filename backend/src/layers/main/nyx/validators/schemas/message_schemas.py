from src.layers.main.nyx.enums import EncryptionType


SEND_MESSAGE_SCHEMA = {
    "type": "object",
    "required": [
        "conversation_id",
        "sender_id",
        "recipient_id",
        "encryption_type",
        "ciphertext",
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
        "encrypted_message_key": {"type": "string"},
        "nonce": {"type": "string", "minLength": 1},
        "message_id": {"type": "string", "minLength": 1},
        "created_at": {"type": "string", "minLength": 1},
        "correlation_id": {"type": "string", "minLength": 1},
        "request_id": {"type": "string", "minLength": 1},
        "metadata": {"type": "object", "additionalProperties": True},
    },
}

QUEUED_SEND_MESSAGE_SCHEMA = {
    "type": "object",
    "required": ["auth_token", "payload"],
    "additionalProperties": False,
    "properties": {
        "auth_token": {"type": "string", "minLength": 1},
        "payload": {
            "type": "object",
        },
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
    "required": [
        "target_username",
        "conversation_password_salt",
        "conversation_password_kdf_params",
        "unlock_check_ciphertext",
        "unlock_check_nonce",
        "creator_access",
    ],
    "additionalProperties": False,
    "properties": {
        "target_username": {"type": "string", "minLength": 3, "maxLength": 128},
        "conversation_password_salt": {"type": "string", "minLength": 16},
        "conversation_password_kdf_params": {
            "type": "object",
            "required": ["algorithm", "iterations", "hash"],
            "additionalProperties": True,
            "properties": {
                "algorithm": {"type": "string", "minLength": 1},
                "iterations": {"type": "integer", "minimum": 1},
                "hash": {"type": "string", "minLength": 1},
            },
        },
        "unlock_check_ciphertext": {"type": "string", "minLength": 16},
        "unlock_check_nonce": {"type": "string", "minLength": 16},
        "creator_access": {
            "type": "object",
            "required": ["encrypted_conversation_password", "nonce"],
            "additionalProperties": False,
            "properties": {
                "encrypted_conversation_password": {"type": "string", "minLength": 16},
                "nonce": {"type": "string", "minLength": 16},
            },
        },
    },
}

SAVE_CONVERSATION_ACCESS_SCHEMA = {
    "type": "object",
    "required": ["encrypted_conversation_password", "nonce"],
    "additionalProperties": False,
    "properties": {
        "encrypted_conversation_password": {"type": "string", "minLength": 16},
        "nonce": {"type": "string", "minLength": 16},
    },
}

