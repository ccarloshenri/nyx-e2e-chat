import pytest

from src.layers.main.nyx.aws.aws_event_parser import extract_aws_bearer_token, parse_aws_json_body
from src.layers.main.nyx.exceptions import ValidationError


def test_parse_aws_json_body_accepts_dict_body():
    assert parse_aws_json_body({"body": {"value": 1}}) == {"value": 1}


def test_parse_aws_json_body_returns_empty_dict_when_body_missing():
    assert parse_aws_json_body({}) == {}


def test_parse_aws_json_body_raises_for_invalid_json():
    with pytest.raises(ValidationError):
        parse_aws_json_body({"body": "{invalid"})


def test_extract_aws_bearer_token_reads_authorization_header():
    token = extract_aws_bearer_token({"Authorization": "Bearer token-123"})

    assert token == "token-123"


def test_extract_aws_bearer_token_falls_back_to_query_string():
    token = extract_aws_bearer_token(headers=None, query={"token": "query-token"})

    assert token == "query-token"


def test_extract_aws_bearer_token_requires_token():
    with pytest.raises(ValidationError):
        extract_aws_bearer_token(headers=None, query=None)
