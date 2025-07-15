from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TELEGRAM_BOT_TOKEN: str = Field(default=...)
    DB_PATH: str = Field(default=":memory:")

    CANTEEN_SVC_URL: str = Field(default=...)
    EXAMS_SVC_URL: str = Field(default=...)
    LECTURES_SVC_URL: str = Field(default=...)
    MAPS_SVC_URL: str = Field(default=...)
    ROOMS_SVC_URL: str = Field(default=...)
    TT_SVC_URL: str = Field(default=...)


settings = Settings()
