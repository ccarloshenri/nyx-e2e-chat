from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.models.conversation import Conversation
from src.layers.main.nyx.utils.exceptions import NotFoundError
from src.layers.main.nyx.utils.serializers import serialize


class ConversationBO:
    def __init__(
        self,
        conversation_dao: IConversationDao,
        clock: IClock,
        message_dao: IMessageDao | None = None,
        user_dao: IUserDao | None = None,
    ) -> None:
        self.conversation_dao = conversation_dao
        self.clock = clock
        self.message_dao = message_dao
        self.user_dao = user_dao

    def create_conversation(self, payload: dict) -> dict:
        conversation = Conversation(
            conversation_id=payload["conversation_id"],
            participants=payload["participants"],
            created_at=self.clock.now_iso(),
        )
        self.conversation_dao.create_conversation(conversation)
        return serialize(conversation)

    def ensure_participant(self, conversation_id: str, user_id: str) -> Conversation:
        conversation = self.conversation_dao.get_conversation(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        if user_id not in conversation.participants:
            raise NotFoundError("Conversation not found for user")
        return conversation

    def list_conversations_for_user(self, user_id: str) -> dict:
        conversations = self.conversation_dao.list_conversations_for_user(user_id)
        serialized = [
            {
                "id": conversation.conversation_id,
                "title": self._build_title(conversation, user_id),
                "preview": "Encrypted conversation ready",
                "updatedAt": conversation.created_at,
                "unreadCount": 0,
                "participantLabel": self._build_participant_label(conversation),
            }
            for conversation in conversations
        ]
        return {"conversations": serialized, "count": len(serialized)}

    def _build_title(self, conversation: Conversation, user_id: str) -> str:
        other_participants = [
            participant for participant in conversation.participants if participant != user_id
        ]
        if not other_participants:
            return conversation.conversation_id
        if self.user_dao is not None:
            resolved_participants = []
            for participant in other_participants:
                user = self.user_dao.get_user_by_id(participant)
                resolved_participants.append(user.username if user is not None else participant)
            other_participants = resolved_participants
        if len(other_participants) == 1:
            return other_participants[0]
        return ", ".join(other_participants)

    def _build_participant_label(self, conversation: Conversation) -> str:
        if len(conversation.participants) > 2:
            return "Group conversation"
        return "Direct message"

