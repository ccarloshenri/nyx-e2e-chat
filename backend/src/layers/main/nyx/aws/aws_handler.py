from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any

from src.layers.main.nyx.aws.aws_request_context_builder import build_aws_request_context
from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.exceptions import ApplicationError
from src.layers.main.nyx.interfaces.services.i_logger import ILogger
from src.layers.main.nyx.utils.logger import bind_log_context, reset_log_context


def aws_handler(
    logger: ILogger,
    response_formatter: AwsResponseFormatter,
) -> Callable[[Callable[[dict, Any], dict]], Callable[[dict, Any], dict]]:
    def build_log_context(event: dict, context: Any, request_context: Any) -> dict[str, Any]:
        request_data = event.get("requestContext", {}) if isinstance(event, dict) else {}
        http_data = request_data.get("http", {}) if isinstance(request_data, dict) else {}
        return {
            "correlation_id": request_context.correlation_id,
            "request_id": request_context.request_id or getattr(context, "aws_request_id", None),
            "route": event.get("routeKey") or request_data.get("routeKey") or event.get("rawPath"),
            "path": event.get("rawPath") or event.get("path"),
            "http_method": http_data.get("method") or event.get("httpMethod"),
            "function_name": getattr(context, "function_name", None),
        }

    def decorator(function: Callable[[dict, Any], dict]) -> Callable[[dict, Any], dict]:
        @wraps(function)
        def wrapper(event: dict, context: Any) -> dict:
            request_context = build_aws_request_context(event)
            log_context = build_log_context(event, context, request_context)
            context_token = bind_log_context(log_context)
            started_at = perf_counter()
            logger.info("request_started", log_context)
            try:
                response = function(event, context)
                logger.info(
                    "request_completed",
                    {
                        **log_context,
                        "status_code": response.get("statusCode") if isinstance(response, dict) else None,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    },
                )
                return response
            except ApplicationError as exc:
                logger.warning(
                    "application_error",
                    {
                        **log_context,
                        "error_code": exc.error_code,
                        "error_message": exc.message,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    },
                )
                return response_formatter.error_response(exc)
            except Exception as exc:
                logger.exception(
                    "unhandled_error",
                    {
                        **log_context,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    },
                )
                return response_formatter.error_response(ApplicationError("Internal server error"))
            finally:
                reset_log_context(context_token)

        return wrapper

    return decorator
