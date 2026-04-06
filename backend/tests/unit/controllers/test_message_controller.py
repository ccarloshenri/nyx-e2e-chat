from unittest.mock import MagicMock, patch

from src.layers.main.nyx.controllers.message_controller import MessageController
from src.layers.main.nyx.models.auth import AuthContext
from src.layers.main.nyx.models.request_context import RequestContext


def build_controller():
    return MessageController(
        message_bo=MagicMock(),
        validator=MagicMock(),
        jwt_service=MagicMock(),
        logger=MagicMock(),
        response_formatter=MagicMock(),
    )


def test_send_message_returns_accepted_response():
    controller = build_controller()
    controller.jwt_service.decode_access_token.return_value = AuthContext("u1", "alice", "t1")
    controller.message_bo.enqueue_message.return_value = {
        "message_id": "msg-1",
        "conversation_id": "conv-1",
        "status": "QUEUED",
    }
    controller.response_formatter.success_response.return_value = {"statusCode": 202}

    with patch(
        "src.layers.main.nyx.controllers.message_controller.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ), patch(
        "src.layers.main.nyx.controllers.message_controller.extract_aws_bearer_token",
        return_value="token",
    ), patch(
        "src.layers.main.nyx.controllers.message_controller.parse_aws_json_body",
        return_value={
            "conversation_id": "conv-1",
            "sender_id": "u1",
            "recipient_id": "u2",
            "encryption_type": "AES_GCM_V1",
            "ciphertext": "abc",
            "encrypted_message_key": "def",
            "nonce": "ghi",
            "message_id": "msg-1",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    ):
        response = controller.send_message({"headers": {"Authorization": "Bearer token"}})

    controller.validator.validate.assert_called_once()
    controller.message_bo.enqueue_message.assert_called_once()
    controller.response_formatter.success_response.assert_called_once_with(
        {
            "message_id": "msg-1",
            "conversation_id": "conv-1",
            "status": "QUEUED",
        },
        status_code=202,
    )
    assert response == {"statusCode": 202}


def test_ack_message_returns_success_response():
    controller = build_controller()
    controller.jwt_service.decode_access_token.return_value = AuthContext("u2", "bob", "t1")
    controller.message_bo.ack_message.return_value = {
        "message_id": "msg-1",
        "status": "ACKNOWLEDGED",
    }
    controller.response_formatter.success_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.message_controller.build_aws_request_context",
        return_value=RequestContext(correlation_id="corr-1", request_id="req-1"),
    ), patch(
        "src.layers.main.nyx.controllers.message_controller.extract_aws_bearer_token",
        return_value="token",
    ), patch(
        "src.layers.main.nyx.controllers.message_controller.parse_aws_json_body",
        return_value={"conversation_id": "conv-1", "message_id": "msg-1", "received_at": "2026-01-01"},
    ):
        response = controller.ack_message({"headers": {"Authorization": "Bearer token"}})

    controller.message_bo.ack_message.assert_called_once_with(
        {"conversation_id": "conv-1", "message_id": "msg-1", "received_at": "2026-01-01"},
        user_id="u2",
    )
    assert response == {"statusCode": 200}


def test_fetch_pending_messages_uses_authenticated_user():
    controller = build_controller()
    controller.jwt_service.decode_access_token.return_value = AuthContext("u2", "bob", "t1")
    controller.message_bo.fetch_pending_messages.return_value = {"messages": [], "count": 0}
    controller.response_formatter.success_response.return_value = {"statusCode": 200}

    with patch(
        "src.layers.main.nyx.controllers.message_controller.extract_aws_bearer_token",
        return_value="token",
    ):
        response = controller.fetch_pending_messages(
            {"headers": {"Authorization": "Bearer token"}}
        )

    controller.validator.validate.assert_called_once()
    controller.message_bo.fetch_pending_messages.assert_called_once_with("u2")
    assert response == {"statusCode": 200}


def test_process_sqs_event_returns_batch_results():
    controller = build_controller()

    with patch.object(controller, "process_sqs_record", side_effect=[{"id": 1}, {"id": 2}]):
        result = controller.process_sqs_event({"Records": [{"body": "1"}, {"body": "2"}]})

    assert result == {"batchItemFailures": [], "results": [{"id": 1}, {"id": 2}]}
    controller.logger.info.assert_called_once_with("sqs_batch_processed", {"records": 2})
