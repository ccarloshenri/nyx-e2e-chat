REGISTER_USER_SCHEMA = {
    "type": "object",
    "required": [
        "username",
        "master_password_verifier",
        "master_password_salt",
        "master_password_kdf_params",
        "secret_wrap_salt",
        "secret_wrap_kdf_params",
        "public_key",
        "encrypted_private_key",
        "private_key_wrap_salt",
        "private_key_wrap_kdf_params",
    ],
    "additionalProperties": False,
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 128},
        "master_password_verifier": {"type": "string", "minLength": 32},
        "master_password_salt": {"type": "string", "minLength": 16},
        "master_password_kdf_params": {
            "type": "object",
            "required": ["algorithm", "iterations", "hash"],
            "additionalProperties": True,
            "properties": {
                "algorithm": {"type": "string", "minLength": 1},
                "iterations": {"type": "integer", "minimum": 1},
                "hash": {"type": "string", "minLength": 1},
            },
        },
        "secret_wrap_salt": {"type": "string", "minLength": 16},
        "secret_wrap_kdf_params": {
            "type": "object",
            "required": ["algorithm", "iterations", "hash"],
            "additionalProperties": True,
            "properties": {
                "algorithm": {"type": "string", "minLength": 1},
                "iterations": {"type": "integer", "minimum": 1},
                "hash": {"type": "string", "minLength": 1},
            },
        },
        "public_key": {"type": "string", "minLength": 32},
        "encrypted_private_key": {"type": "string", "minLength": 32},
        "private_key_wrap_salt": {"type": "string", "minLength": 16},
        "private_key_wrap_kdf_params": {
            "type": "object",
            "required": ["algorithm", "iterations", "hash"],
            "additionalProperties": True,
            "properties": {
                "algorithm": {"type": "string", "minLength": 1},
                "iterations": {"type": "integer", "minimum": 1},
                "hash": {"type": "string", "minLength": 1},
            },
        },
    },
}

LOGIN_SCHEMA = {
    "type": "object",
    "required": ["username", "challenge_token", "login_proof"],
    "additionalProperties": False,
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 128},
        "challenge_token": {"type": "string", "minLength": 16},
        "login_proof": {"type": "string", "minLength": 16},
    },
}

LOGIN_CHALLENGE_SCHEMA = {
    "type": "object",
    "required": ["username"],
    "additionalProperties": False,
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 128},
    },
}

PUBLIC_KEY_LOOKUP_SCHEMA = {
    "type": "object",
    "required": ["username"],
    "additionalProperties": False,
    "properties": {"username": {"type": "string", "minLength": 3, "maxLength": 128}},
}

