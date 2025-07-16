from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TELEGRAM_BOT_TOKEN: str = Field(default=...)


class NotificationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    KAFKA_TOPIC: str = Field(default=...)
    KAFKA_SERVER: str = Field(default=...)
