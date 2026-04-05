REGISTER_USER_SCHEMA = {
    "type": "object",
    "required": [
        "username",
        "password",
        "public_key",
        "encrypted_private_key",
        "kdf_salt",
        "kdf_params",
    ],
    "additionalProperties": False,
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 128},
        "password": {"type": "string", "minLength": 8, "maxLength": 256},
        "public_key": {"type": "string", "minLength": 32},
        "encrypted_private_key": {"type": "string", "minLength": 32},
        "kdf_salt": {"type": "string", "minLength": 16},
        "kdf_params": {
            "type": "object",
            "required": ["algorithm", "iterations"],
            "additionalProperties": True,
            "properties": {
                "algorithm": {"type": "string", "minLength": 1},
                "iterations": {"type": "integer", "minimum": 1},
            },
        },
    },
}

LOGIN_SCHEMA = {
    "type": "object",
    "required": ["username", "password"],
    "additionalProperties": False,
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 128},
        "password": {"type": "string", "minLength": 8, "maxLength": 256},
    },
}

PUBLIC_KEY_LOOKUP_SCHEMA = {
    "type": "object",
    "required": ["username"],
    "additionalProperties": False,
    "properties": {"username": {"type": "string", "minLength": 3, "maxLength": 128}},
}
