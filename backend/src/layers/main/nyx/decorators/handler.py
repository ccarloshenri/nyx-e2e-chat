from collections.abc import Callable
from functools import wraps
from typing import Any

from src.layers.main.nyx.utils.exceptions import ApplicationError
from src.layers.main.nyx.utils.logger import logger
from src.layers.main.nyx.utils.request_context import build_request_context
from src.layers.main.nyx.utils.response_utils import error_response


def handler(function: Callable[[dict, Any], dict]) -> Callable[[dict, Any], dict]:
    @wraps(function)
    def wrapper(event: dict, context: Any) -> dict:
        request_context = build_request_context(event)
        try:
            return function(event, context)
        except ApplicationError as exc:
            logger.warning(
                "application_error",
                extra={
                    "context": {
                        "correlation_id": request_context.correlation_id,
                        "error_code": exc.error_code,
                    }
                },
            )
            return error_response(exc, correlation_id=request_context.correlation_id)
        except Exception:
            logger.exception(
                "unhandled_error",
                extra={"context": {"correlation_id": request_context.correlation_id}},
            )
            return error_response(
                ApplicationError("Internal server error"),
                correlation_id=request_context.correlation_id,
            )

    return wrapper

