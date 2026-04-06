from unittest.mock import MagicMock, patch

from src.layers.main.nyx.aws.aws_handler import aws_handler
from src.layers.main.nyx.exceptions import ApplicationError, ValidationError
from src.layers.main.nyx.models.request_context import RequestContext


def test_aws_handler_returns_function_result_on_success():
    logger = MagicMock()
    response_formatter = MagicMock()

    @aws_handler(logger, response_formatter)
    def wrapped(event, context):
        return {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.aws.aws_handler.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ):
        result = wrapped({}, None)

    assert result == {"statusCode": 200}
    logger.warning.assert_not_called()
    logger.exception.assert_not_called()


def test_aws_handler_formats_application_error():
    logger = MagicMock()
    response_formatter = MagicMock()
    response_formatter.error_response.return_value = {"statusCode": 400}

    @aws_handler(logger, response_formatter)
    def wrapped(event, context):
        raise ValidationError("Invalid payload")

    with patch(
        "src.layers.main.nyx.aws.aws_handler.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ):
        result = wrapped({}, None)

    logger.warning.assert_called_once()
    response_formatter.error_response.assert_called_once()
    assert result == {"statusCode": 400}


def test_aws_handler_converts_unexpected_error_to_internal_error():
    logger = MagicMock()
    response_formatter = MagicMock()
    response_formatter.error_response.return_value = {"statusCode": 500}

    @aws_handler(logger, response_formatter)
    def wrapped(event, context):
        raise RuntimeError("boom")

    with patch(
        "src.layers.main.nyx.aws.aws_handler.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ):
        result = wrapped({}, None)

    logger.exception.assert_called_once()
    error = response_formatter.error_response.call_args.args[0]
    assert isinstance(error, ApplicationError)
    assert error.message == "Internal server error"
    assert result == {"statusCode": 500}
