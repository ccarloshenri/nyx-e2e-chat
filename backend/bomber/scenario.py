from __future__ import annotations

import asyncio
import json

from .api import ApiError, NyxApiClient
from .config import BomberConfig
from .crypto_sim import build_conversation_payload, build_registration_payload, create_login_proof
from .models import BombUser, ConversationPair, MessagePlan


class ScenarioBuilder:
    def __init__(self, config: BomberConfig, api_client: NyxApiClient) -> None:
        self.config = config
        self.api_client = api_client

    async def build(self) -> list[MessagePlan]:
        users = self._build_users()
        await self._register_users(users)
        await self._login_users(users)
        conversation_pairs = await self._ensure_conversations(users)
        return self._build_message_plans(conversation_pairs)

    def _build_users(self) -> list[BombUser]:
        if self.config.users_file is not None:
            raw_users = json.loads(self.config.users_file.read_text(encoding="utf-8"))
            return [
                BombUser(
                    username=str(item["username"]),
                    master_password=str(item["master_password"]),
                )
                for item in raw_users
            ]
        return [self._build_user(index) for index in range(self.config.user_count)]

    def _build_user(self, index: int) -> BombUser:
        return BombUser(
            username=f"{self.config.username_prefix}-{index:04d}",
            master_password=f"{self.config.master_password_prefix}-{index:04d}",
        )

    async def _register_users(self, users: list[BombUser]) -> None:
        if not self.config.register_missing_users:
            return
        semaphore = asyncio.Semaphore(min(self.config.concurrency, 100))
        await asyncio.gather(
            *(self._register_user(semaphore, user) for user in users)
        )

    async def _register_user(self, semaphore: asyncio.Semaphore, user: BombUser) -> None:
        async with semaphore:
            payload = build_registration_payload(user.username, user.master_password)
            try:
                response = await self.api_client.post(self.config.register_path, json_body=payload)
                user.user_id = str(response["data"]["user_id"])
            except ApiError as exc:
                if exc.status_code != 409:
                    raise

    async def _login_users(self, users: list[BombUser]) -> None:
        semaphore = asyncio.Semaphore(min(self.config.concurrency, 100))
        await asyncio.gather(*(self._login_user(semaphore, user) for user in users))

    async def _login_user(self, semaphore: asyncio.Semaphore, user: BombUser) -> None:
        async with semaphore:
            challenge_response = await self.api_client.post(
                self.config.challenge_path,
                json_body={"username": user.username},
            )
            challenge = challenge_response["data"]
            proof = create_login_proof(
                master_password=user.master_password,
                challenge_token=str(challenge["challenge_token"]),
                master_password_salt=str(challenge["master_password_salt"]),
                master_password_kdf_params=challenge["master_password_kdf_params"],
            )
            login_response = await self.api_client.post(
                self.config.login_path,
                json_body={
                    "username": user.username,
                    "challenge_token": challenge["challenge_token"],
                    "login_proof": proof,
                },
            )
            user_payload = login_response["data"]["user"]
            user.user_id = str(user_payload["user_id"])
            user.token = str(login_response["data"]["token"]["access_token"])

    async def _ensure_conversations(self, users: list[BombUser]) -> list[ConversationPair]:
        semaphore = asyncio.Semaphore(min(self.config.concurrency, 50))
        tasks = []
        for index, left_user in enumerate(users):
            right_user = users[(index + 1) % len(users)]
            tasks.append(self._create_conversation(semaphore, left_user, right_user))

        seen_conversation_ids: set[str] = set()
        conversation_pairs: list[ConversationPair] = []
        for pair in await asyncio.gather(*tasks):
            if pair.conversation_id in seen_conversation_ids:
                continue
            seen_conversation_ids.add(pair.conversation_id)
            conversation_pairs.append(pair)
        return conversation_pairs

    async def _create_conversation(
        self,
        semaphore: asyncio.Semaphore,
        left_user: BombUser,
        right_user: BombUser,
    ) -> ConversationPair:
        async with semaphore:
            payload = build_conversation_payload(right_user.username)
            response = await self.api_client.post(
                self.config.conversations_path,
                json_body=payload,
                token=left_user.token,
            )
            return ConversationPair(
                conversation_id=str(response["data"]["conversation_id"]),
                left_user=left_user,
                right_user=right_user,
            )

    def _build_message_plans(self, conversation_pairs: list[ConversationPair]) -> list[MessagePlan]:
        plans: list[MessagePlan] = []
        for pair in conversation_pairs:
            plans.append(
                MessagePlan(
                    conversation_id=pair.conversation_id,
                    sender=pair.left_user,
                    recipient=pair.right_user,
                )
            )
            plans.append(
                MessagePlan(
                    conversation_id=pair.conversation_id,
                    sender=pair.right_user,
                    recipient=pair.left_user,
                )
            )
        if not plans:
            raise ValueError("no message plans were created")
        return plans
