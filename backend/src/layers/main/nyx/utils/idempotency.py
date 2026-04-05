from src.layers.main.nyx.interfaces.dao.i_message_dao import IMessageDao


class IdempotencyService:
    def __init__(self, message_dao: IMessageDao) -> None:
        self.message_dao = message_dao

    def message_already_processed(self, conversation_id: str, message_id: str) -> bool:
        return self.message_dao.get_message(conversation_id=conversation_id, message_id=message_id) is not None

