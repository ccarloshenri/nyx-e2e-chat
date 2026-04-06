from src.layers.main.nyx.exceptions.base import ApplicationError


class InfrastructureError(ApplicationError):
    status_code = 502
    error_code = "infrastructure_error"
