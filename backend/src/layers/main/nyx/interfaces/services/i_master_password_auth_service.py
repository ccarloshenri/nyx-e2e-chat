from abc import ABC, abstractmethod

from src.layers.main.nyx.models.auth import LoginChallenge


class IMasterPasswordAuthService(ABC):
    @abstractmethod
    def issue_login_challenge(
        self,
        username: str,
        master_password_salt: str,
        master_password_kdf_params: dict,
    ) -> LoginChallenge:
        pass

    @abstractmethod
    def verify_login_proof(
        self,
        username: str,
        stored_verifier: str,
        challenge_token: str,
        login_proof: str,
    ) -> None:
        pass
