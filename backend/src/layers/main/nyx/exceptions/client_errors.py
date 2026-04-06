from src.layers.main.nyx.exceptions.base import ApplicationError


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
