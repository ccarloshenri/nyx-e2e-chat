from uuid import uuid4

from src.layers.main.nyx.interfaces.services.i_id_generator import IIdGenerator


class UuidGenerator(IIdGenerator):
    def new_id(self) -> str:
        return str(uuid4())

