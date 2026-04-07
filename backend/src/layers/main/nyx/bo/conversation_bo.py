from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.interfaces.dao.i_user_dao import IUserDao
from src.layers.main.nyx.interfaces.services.i_clock import IClock
from src.layers.main.nyx.interfaces.services.i_id_generator import IIdGenerator
from src.layers.main.nyx.models.conversation import Conversation
from src.layers.main.nyx.exceptions import ConflictError, InfrastructureError, NotFoundError
from src.layers.main.nyx.utils.serializers import serialize


class ConversationBO:
    def __init__(
        self,
        conversation_dao: IConversationDao,
        clock: IClock,
        id_generator: IIdGenerator | None = None,
        message_dao: IMessageDao | None = None,
        user_dao: IUserDao | None = None,
    ) -> None:
        self.conversation_dao = conversation_dao
        self.clock = clock
        self.id_generator = id_generator
        self.message_dao = message_dao
        self.user_dao = user_dao

    def create_conversation(self, payload: dict, authenticated_user_id: str) -> dict:
        if self.user_dao is None:
            raise InfrastructureError("user_dao_not_configured")

        target_user = self.user_dao.get_user_by_username(payload["target_username"])
        if target_user is None:
            raise NotFoundError("user_not_found")
        if target_user.user_id == authenticated_user_id:
            raise ConflictError("conversation_with_self_not_allowed")

        existing_conversation = self._find_direct_conversation(
            authenticated_user_id,
            target_user.user_id,
        )
        if existing_conversation is not None:
            return serialize(existing_conversation)

        if self.id_generator is None:
            raise InfrastructureError("id_generator_not_configured")

        conversation = Conversation(
            conversation_id=self.id_generator.new_id(),
            participants=[authenticated_user_id, target_user.user_id],
            conversation_password_salt=payload["conversation_password_salt"],
            conversation_password_kdf_params=payload["conversation_password_kdf_params"],
            unlock_check_ciphertext=payload["unlock_check_ciphertext"],
            unlock_check_nonce=payload["unlock_check_nonce"],
            participant_access={authenticated_user_id: payload["creator_access"]},
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
                "hasStoredSecret": user_id in conversation.participant_access,
            }
            for conversation in conversations
        ]
        return {"conversations": serialized, "count": len(serialized)}

    def get_conversation_access_context(self, conversation_id: str, user_id: str) -> dict:
        conversation = self.ensure_participant(conversation_id, user_id)
        return {
            "conversation_id": conversation.conversation_id,
            "conversation_password_salt": conversation.conversation_password_salt,
            "conversation_password_kdf_params": conversation.conversation_password_kdf_params,
            "unlock_check_ciphertext": conversation.unlock_check_ciphertext,
            "unlock_check_nonce": conversation.unlock_check_nonce,
            "participant_access": conversation.participant_access.get(user_id),
            "has_stored_secret": user_id in conversation.participant_access,
        }

    def save_participant_access(self, conversation_id: str, user_id: str, access_payload: dict) -> dict:
        self.ensure_participant(conversation_id, user_id)
        self.conversation_dao.save_participant_access(conversation_id, user_id, access_payload)
        return {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "has_stored_secret": True,
        }

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

    def _find_direct_conversation(
        self,
        authenticated_user_id: str,
        target_user_id: str,
    ) -> Conversation | None:
        conversations = self.conversation_dao.list_conversations_for_user(authenticated_user_id)
        expected_participants = {authenticated_user_id, target_user_id}
        for conversation in conversations:
            if len(conversation.participants) == 2 and set(conversation.participants) == expected_participants:
                return conversation
        return None

