import json

from src.layers.main.nyx.aws.aws_response_formatter import AwsResponseFormatter
from src.layers.main.nyx.exceptions import ValidationError


def test_success_response_wraps_payload():
    formatter = AwsResponseFormatter()

    response = formatter.success_response({"message_id": "msg-1"}, status_code=202)

    assert response["statusCode"] == 202
    assert json.loads(response["body"]) == {
        "success": True,
        "data": {"message_id": "msg-1"},
    }


def test_error_response_includes_error_metadata_and_correlation_id():
    formatter = AwsResponseFormatter()

    response = formatter.error_response(
        ValidationError("Invalid payload", details={"field": "root"}),
        correlation_id="corr-1",
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "success": False,
        "error": {
            "code": "validation_error",
            "message": "Invalid payload",
            "details": {"field": "root"},
        },
        "correlation_id": "corr-1",
    }
