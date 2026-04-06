from unittest.mock import MagicMock

import pytest

from src.layers.main.nyx.bo.conversation_bo import ConversationBO
from src.layers.main.nyx.exceptions import NotFoundError
from src.layers.main.nyx.models.conversation import Conversation


def test_create_conversation_persists_and_serializes_result():
    conversation_dao = MagicMock()
    clock = MagicMock()
    clock.now_iso.return_value = "2026-01-01T00:00:00+00:00"
    bo = ConversationBO(conversation_dao=conversation_dao, clock=clock)

    result = bo.create_conversation(
        {
            "conversation_id": "conv-1",
            "participants": ["user-1", "user-2"],
        }
    )

    conversation_dao.create_conversation.assert_called_once()
    assert result["conversation_id"] == "conv-1"
    assert result["participants"] == ["user-1", "user-2"]


def test_ensure_participant_raises_when_conversation_missing():
    conversation_dao = MagicMock()
    conversation_dao.get_conversation.return_value = None
    bo = ConversationBO(conversation_dao=conversation_dao, clock=MagicMock())

    with pytest.raises(NotFoundError):
        bo.ensure_participant("conv-1", "user-1")


def test_ensure_participant_raises_when_user_not_in_conversation():
    conversation_dao = MagicMock()
    conversation_dao.get_conversation.return_value = Conversation(
        conversation_id="conv-1",
        participants=["user-2", "user-3"],
        created_at="2026-01-01T00:00:00+00:00",
    )
    bo = ConversationBO(conversation_dao=conversation_dao, clock=MagicMock())

    with pytest.raises(NotFoundError):
        bo.ensure_participant("conv-1", "user-1")


def test_list_conversations_for_user_resolves_other_participant_names():
    conversation_dao = MagicMock()
    conversation_dao.list_conversations_for_user.return_value = [
        Conversation(
            conversation_id="conv-1",
            participants=["user-1", "user-2"],
            created_at="2026-01-01T00:00:00+00:00",
        ),
        Conversation(
            conversation_id="conv-2",
            participants=["user-1", "user-2", "user-3"],
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    user_dao = MagicMock()
    user_dao.get_user_by_id.side_effect = [
        MagicMock(username="alice"),
        MagicMock(username="alice"),
        MagicMock(username="bob"),
    ]
    bo = ConversationBO(
        conversation_dao=conversation_dao,
        clock=MagicMock(),
        user_dao=user_dao,
    )

    result = bo.list_conversations_for_user("user-1")

    assert result["count"] == 2
    assert result["conversations"][0]["title"] == "alice"
    assert result["conversations"][0]["participantLabel"] == "Direct message"
    assert result["conversations"][1]["title"] == "alice, bob"
    assert result["conversations"][1]["participantLabel"] == "Group conversation"
