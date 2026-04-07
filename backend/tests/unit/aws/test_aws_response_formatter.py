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


def test_error_response_returns_snake_case_error_payload():
    formatter = AwsResponseFormatter()

    response = formatter.error_response(ValidationError("Invalid payload", details={"field": "root"}))

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "error_code": "validation_error",
        "error_message": "invalid_payload",
    }
