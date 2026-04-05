from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.models.conversation import Conversation
from src.layers.main.nyx.utils.exceptions import NotFoundError
from src.layers.main.nyx.utils.serializers import serialize


class ConversationBO:
    def __init__(self, conversation_dao: IConversationDao, clock: IClock) -> None:
        self.conversation_dao = conversation_dao
        self.clock = clock

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

