from src.layers.main.nyx.interfaces.dao.i_connection_dao import IConnectionDao
from src.layers.main.nyx.interfaces.dao.i_conversation_dao import IConversationDao
from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao
from src.layers.main.nyx.interfaces.messaging.i_queue_publisher import IQueuePublisher
from src.layers.main.nyx.interfaces.realtime.i_websocket_notifier import IWebSocketNotifier
from src.models.enums import MessageStatus, WebSocketAction
from src.models.message import Message
from src.utils.exceptions import AuthorizationError, InfrastructureError, NotFoundError
from src.utils.idempotency import IdempotencyService
from src.utils.serializers import serialize


class MessageBO:
    def __init__(
        self,
        message_dao: IMessageDao,
        connection_dao: IConnectionDao,
        conversation_dao: IConversationDao | None = None,
        queue_publisher: IQueuePublisher | None = None,
        websocket_notifier: IWebSocketNotifier | None = None,
        idempotency_service: IdempotencyService | None = None,
    ) -> None:
        self.message_dao = message_dao
        self.connection_dao = connection_dao
        self.conversation_dao = conversation_dao
        self.queue_publisher = queue_publisher
        self.websocket_notifier = websocket_notifier
        self.idempotency_service = idempotency_service or IdempotencyService(message_dao)

    def enqueue_message(self, payload: dict, authenticated_user_id: str) -> dict:
        if payload["sender_id"] != authenticated_user_id:
            raise AuthorizationError("Sender does not match authenticated user")
        self._ensure_conversation_access(payload["conversation_id"], authenticated_user_id)
        if self.queue_publisher is None:
            raise InfrastructureError("Queue publisher not configured")
        self.queue_publisher.publish(
            payload=payload,
            deduplication_id=payload["message_id"],
            group_id=payload["conversation_id"],
        )
        return {
            "message_id": payload["message_id"],
            "conversation_id": payload["conversation_id"],
            "status": MessageStatus.QUEUED.value,
        }

    def process_queued_message(self, payload: dict) -> dict:
        if self.idempotency_service.message_already_processed(
            conversation_id=payload["conversation_id"],
            message_id=payload["message_id"],
        ):
            return {"message_id": payload["message_id"], "status": "DUPLICATE"}
        message = Message(
            conversation_id=payload["conversation_id"],
            message_id=payload["message_id"],
            sender_id=payload["sender_id"],
            recipient_id=payload["recipient_id"],
            ciphertext=payload["ciphertext"],
            encrypted_message_key=payload["encrypted_message_key"],
            nonce=payload["nonce"],
            algorithm=payload["algorithm"],
            created_at=payload["created_at"],
            status=MessageStatus.PENDING,
            metadata=payload.get("metadata", {}),
        )
        self.message_dao.save_message(message)
        delivered = self._deliver_to_active_connections(message)
        final_status = MessageStatus.DELIVERED if delivered else MessageStatus.PENDING
        self.message_dao.update_message_status(message.conversation_id, message.message_id, final_status)
        return {"message_id": message.message_id, "status": final_status.value}

    def fetch_pending_messages(self, user_id: str) -> dict:
        messages = self.message_dao.list_pending_messages_for_user(user_id)
        serialized = serialize(messages)
        return {"messages": serialized, "count": len(serialized)}

    def ack_message(self, payload: dict, user_id: str) -> dict:
        message = self.message_dao.get_message(
            conversation_id=payload["conversation_id"],
            message_id=payload["message_id"],
        )
        if message is None:
            raise NotFoundError("Message not found")
        if message.recipient_id != user_id:
            raise AuthorizationError("Authenticated user cannot acknowledge this message")
        self.message_dao.update_message_status(
            conversation_id=payload["conversation_id"],
            message_id=payload["message_id"],
            status=MessageStatus.ACKNOWLEDGED,
        )
        return {
            "message_id": payload["message_id"],
            "conversation_id": payload["conversation_id"],
            "recipient_id": user_id,
            "status": MessageStatus.ACKNOWLEDGED.value,
        }

    def push_pending_messages(self, user_id: str) -> dict:
        connections = self.connection_dao.get_connections_by_user(user_id)
        if not connections:
            return {"delivered": 0}
        if self.websocket_notifier is None:
            return {"delivered": 0}
        pending = self.message_dao.list_pending_messages_for_user(user_id)
        delivered = 0
        for connection in connections:
            self.websocket_notifier.notify(
                connection.connection_id,
                {
                    "action": WebSocketAction.PENDING_MESSAGES.value,
                    "messages": serialize(pending),
                },
            )
            delivered += len(pending)
        return {"delivered": delivered}

    def _deliver_to_active_connections(self, message: Message) -> bool:
        delivered = False
        if self.websocket_notifier is None:
            return delivered
        for connection in self.connection_dao.get_connections_by_user(message.recipient_id):
            try:
                self.websocket_notifier.notify(
                    connection.connection_id,
                    {
                        "action": WebSocketAction.DELIVER_MESSAGE.value,
                        "message": serialize(message),
                    },
                )
                delivered = True
            except Exception:
                continue
        return delivered

    def _ensure_conversation_access(self, conversation_id: str, user_id: str) -> None:
        if self.conversation_dao is None:
            return
        conversation = self.conversation_dao.get_conversation(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        if user_id not in conversation.participants:
            raise AuthorizationError("User is not a participant of this conversation")
