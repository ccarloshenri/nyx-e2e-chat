from abc import ABC, abstractmethod

from src.layers.main.nyx.models.auth import AuthContext, AuthToken


class IJwtService(ABC):
    @abstractmethod
    def generate_access_token(self, user_id: str, username: str) -> AuthToken:
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> AuthContext:
        pass

