from jsonschema import Draft202012Validator

from src.layers.main.nyx.exceptions import ValidationError


class RequestValidator:
    def validate(self, schema: dict, payload: dict) -> None:
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: error.path)
        if errors:
            error = errors[0]
            field = ".".join(str(part) for part in error.absolute_path) or "root"
            raise ValidationError(
                "Payload validation failed",
                details={"field": field, "reason": error.message},
            )

