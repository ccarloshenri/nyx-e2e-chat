import os
from dataclasses import dataclass

from dotenv import load_dotenv

from src.layers.main.nyx.config.constants import DEFAULT_CONNECTION_TTL_SECONDS, DEFAULT_JWT_EXP_MINUTES

load_dotenv()


@dataclass(frozen=True)
class Settings:
    service_name: str = os.getenv("SERVICE_NAME", "nyx-e2e-chat-backend")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    users_table_name: str = os.getenv("USERS_TABLE_NAME", "nyx-users")
    connections_table_name: str = os.getenv("CONNECTIONS_TABLE_NAME", "nyx-connections")
    conversations_table_name: str = os.getenv("CONVERSATIONS_TABLE_NAME", "nyx-conversations")
    messages_table_name: str = os.getenv("MESSAGES_TABLE_NAME", "nyx-messages")
    message_delivery_queue_url: str = os.getenv("MESSAGE_DELIVERY_QUEUE_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_exp_minutes: int = int(os.getenv("JWT_EXP_MINUTES", str(DEFAULT_JWT_EXP_MINUTES)))
    websocket_management_endpoint: str = os.getenv("WEBSOCKET_MANAGEMENT_ENDPOINT", "")
    connection_ttl_seconds: int = int(
        os.getenv("CONNECTION_TTL_SECONDS", str(DEFAULT_CONNECTION_TTL_SECONDS))
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

