from src.layers.main.nyx.enums import EncryptionType, MessageStatus, WebSocketAction
from src.layers.main.nyx.interfaces.infrastructure.i_infrastructure import IInfrastructure
from src.layers.main.nyx.models.message import Message
from src.layers.main.nyx.exceptions import AuthorizationError, InfrastructureError, NotFoundError
from src.layers.main.nyx.utils.idempotency import IdempotencyService
from src.layers.main.nyx.utils.logger import create_logger
from src.layers.main.nyx.utils.serializers import serialize

logger = create_logger(__name__)


class MessageBO:
    """Handle message queueing, persistence, delivery, and acknowledgement flows."""

    def __init__(
        self,
        infrastructure: IInfrastructure,
        idempotency_service: IdempotencyService | None = None,
    ) -> None:
        self.infrastructure = infrastructure
        self.message_dao = infrastructure.get_message_dao()
        self.connection_dao = infrastructure.get_connection_dao()
        self.conversation_dao = infrastructure.get_conversation_dao()
        self.queue_publisher = infrastructure.get_queue_publisher()
        self.websocket_notifier = infrastructure.get_websocket_notifier()
        self.idempotency_service = idempotency_service or IdempotencyService(self.message_dao)

    def enqueue_message_for_async_validation(
        self,
        *,
        payload: dict,
        auth_token: str,
        deduplication_id: str,
        group_id: str,
    ) -> dict:
        """Push the raw request to the queue so validation can happen off the synchronous path."""
        if self.queue_publisher is None:
            raise InfrastructureError("Queue publisher not configured")
        queue_payload = {
            "auth_token": auth_token,
            "payload": payload,
        }
        logger.info(
            "sending_message_to_queue",
            {
                "queue_name": payload.get("queue_name"),
                "sender_id": payload["sender_id"],
                "receiver_id": payload["recipient_id"],
            },
        )
        self.queue_publisher.publish(
            payload=queue_payload,
            deduplication_id=deduplication_id,
            group_id=group_id,
        )
        logger.info(
            "message_enqueued_successfully",
            {
                "sender_id": payload["sender_id"],
                "receiver_id": payload["recipient_id"],
            },
        )
        return {
            "message_id": payload["message_id"],
            "conversation_id": payload["conversation_id"],
            "status": MessageStatus.QUEUED.value,
        }

    def authorize_message_payload(self, payload: dict, authenticated_user_id: str) -> None:
        """Validate sender ownership and conversation membership before processing the queued message."""
        if payload["sender_id"] != authenticated_user_id:
            raise AuthorizationError("Sender does not match authenticated user")
        self._ensure_conversation_access(payload["conversation_id"], authenticated_user_id)

    def process_queued_message(self, payload: dict) -> dict:
        """Persist an enqueued message and attempt immediate delivery to active connections."""
        if self.idempotency_service.message_already_processed(
            conversation_id=payload["conversation_id"],
            message_id=payload["message_id"],
        ):
            logger.warning("duplicate_message_detected", {"status": "DUPLICATE"})
            return {"message_id": payload["message_id"], "status": "DUPLICATE"}
        message = Message(
            conversation_id=payload["conversation_id"],
            message_id=payload["message_id"],
            sender_id=payload["sender_id"],
            recipient_id=payload["recipient_id"],
            encryption_type=EncryptionType(payload["encryption_type"]),
            ciphertext=payload["ciphertext"],
            encrypted_message_key=payload["encrypted_message_key"],
            nonce=payload["nonce"],
            created_at=payload["created_at"],
            status=MessageStatus.PENDING,
            metadata=payload.get("metadata", {}),
        )
        self.message_dao.save_message(message)
        delivered = self._deliver_to_active_connections(message)
        final_status = MessageStatus.DELIVERED if delivered else MessageStatus.PENDING
        self.message_dao.update_message_status(message.conversation_id, message.message_id, final_status)
        logger.info(
            "message_sent_from_user_to_user",
            {
                "sender_id": message.sender_id,
                "receiver_id": message.recipient_id,
                "status": final_status.value,
            },
        )
        return {"message_id": message.message_id, "status": final_status.value}

    def fetch_pending_messages(self, user_id: str) -> dict:
        """Return encrypted messages that still await delivery or acknowledgement."""
        messages = self.message_dao.list_pending_messages_for_user(user_id)
        serialized = serialize(messages)
        return {"messages": serialized, "count": len(serialized)}

    def list_messages_for_conversation(self, conversation_id: str, user_id: str) -> dict:
        """List stored encrypted messages for a conversation the user can access."""
        self._ensure_conversation_access(conversation_id, user_id)
        messages = self.message_dao.list_messages_for_conversation(conversation_id)
        serialized = serialize(messages)
        return {"messages": serialized, "count": len(serialized)}

    def ack_message(self, payload: dict, user_id: str) -> dict:
        """Mark a message as acknowledged by its intended recipient."""
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
        """Push pending encrypted messages to all active WebSocket sessions for a user."""
        connections = self.connection_dao.get_connections_by_user(user_id)
        if not connections:
            return {"delivered": 0}
        if self.websocket_notifier is None:
            return {"delivered": 0}
        pending = self.message_dao.list_pending_messages_for_user(user_id)
        delivered = 0
        for connection in connections:
            logger.info(
                "sending_message_to_active_connection",
                {
                    "user_id": user_id,
                    "connection_id": connection.connection_id,
                    "pending_count": len(pending),
                },
            )
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
        """Attempt realtime fan-out of one encrypted message to active recipient connections."""
        delivered = False
        if self.websocket_notifier is None:
            return delivered
        for connection in self.connection_dao.get_connections_by_user(message.recipient_id):
            try:
                logger.info(
                    "sending_message_to_active_connection",
                    {
                        "receiver_id": message.recipient_id,
                        "connection_id": connection.connection_id,
                    },
                )
                self.websocket_notifier.notify(
                    connection.connection_id,
                    {
                        "action": WebSocketAction.DELIVER_MESSAGE.value,
                        "message": serialize(message),
                    },
                )
                logger.info(
                    "message_delivered_to_user",
                    {
                        "receiver_id": message.recipient_id,
                        "connection_id": connection.connection_id,
                    },
                )
                delivered = True
            except Exception:
                logger.exception(
                    "websocket_delivery_failed",
                    {
                        "receiver_id": message.recipient_id,
                        "connection_id": connection.connection_id,
                    },
                )
                continue
        return delivered

    def _ensure_conversation_access(self, conversation_id: str, user_id: str) -> None:
        """Fail fast when a user tries to access a conversation they do not belong to."""
        if self.conversation_dao is None:
            return
        conversation = self.conversation_dao.get_conversation(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        if user_id not in conversation.participants:
            raise AuthorizationError("User is not a participant of this conversation")

