class ApplicationError(Exception):
    status_code = 500
    error_code = "internal_error"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ApplicationError):
    status_code = 400
    error_code = "validation_error"


class AuthenticationError(ApplicationError):
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(ApplicationError):
    status_code = 403
    error_code = "authorization_error"


class NotFoundError(ApplicationError):
    status_code = 404
    error_code = "not_found"


class ConflictError(ApplicationError):
    status_code = 409
    error_code = "conflict_error"


class InfrastructureError(ApplicationError):
    status_code = 502
    error_code = "infrastructure_error"
